# -*- coding: utf-8 -*-
"""
BLE 複数台サンプル共通: 複数の KeiganMotor をスキャンして選択・接続する

    from ble_multi import get_addresses, connect_motors, run_all, disconnect_all

    addresses = get_addresses(args.addresses)   # 引数が無ければスキャンして選択
    motors = connect_motors(addresses)          # 1台ずつ順番に接続 (失敗したモーターは除く)
    run_all(motors, lambda m: m.enable_action())  # 全モーターに同時に送信
    disconnect_all(motors)

注意
    + 同時に接続できる台数は BLE アダプターに依存します (目安 5〜7台。Raspberry Pi 内蔵はより少ないことがある)
    + 接続中のモーターはスキャンに出てこないため、使うモーターをすべて選んでから接続します
    + コールバック (on_motor_*_cb) の中からモーターへコマンドを送ることはできません。
      コールバックでは値を保存するだけにして、コマンドはメインスレッドなどから送って下さい
"""
import sys
import pathlib
from concurrent.futures import ThreadPoolExecutor

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller

# モーターごとの LED 色 (R, G, B)。選択した順に割り当てる
LED_COLORS = [(255, 255, 0), (0, 255, 255), (255, 0, 255), (0, 255, 0), (255, 128, 0), (0, 0, 255), (255, 0, 0)]


def led_color(i):
    return LED_COLORS[i % len(LED_COLORS)]


SCAN_SEC = 10.0  # モーターのアドバタイズは数秒に1回しか受信できないことがあるため、単体用より長めにする


def select_motors(scan_sec=SCAN_SEC):
    """
    スキャンして見つかったモーターを一覧表示し、接続するモーターを番号で選択させる。
        0,1   : 番号をカンマ(またはスペース)区切りで指定 (指定した順に並ぶ)
        a     : 見つかったすべて
        r     : 再スキャン (前回までに見つかったモーターも一覧に残る)
        q     : 中止
    選択したモーターの MAC アドレスのリストを返す (中止した場合は空のリスト)。
    """
    known = {}  # address -> {'name', 'address', 'rssi'}。再スキャンしても消さずに追加していく
    while True:
        print("During scanning at", scan_sec, "sec")
        for km in blecontroller.scan(scan_sec):
            known[km['address']] = km  # 見つかったものは RSSI を更新
        found = list(known.values())  # 番号が変わらないよう、見つかった順に並べる
        if not found:
            print("KeiganMotor が見つかりませんでした")
        else:
            print("{} motors found (r で再スキャンすると、見つかっていないモーターが追加されることがあります)".format(len(found)))
        for i, km in enumerate(found):
            print("  [{}] {} : {} (RSSI {})".format(i, km['name'], km['address'], km['rssi']))
        inp = input('Connect:[numbers e.g. 0,1 / a=all] Rescan:[r] Quit:[q] >>').strip().lower()
        if inp == 'q':
            return []
        if inp == 'a' and found:
            return [km['address'] for km in found]
        nums = inp.replace(',', ' ').split()
        if nums and all(n.isdigit() and int(n) < len(found) for n in nums):
            selected = []
            for n in nums:
                address = found[int(n)]['address']
                if address not in selected:
                    selected.append(address)
            return selected
        if inp != 'r':
            print("番号を 0,1 のように入力して下さい")


def get_addresses(addresses=None, scan_sec=SCAN_SEC):
    """引数で MAC アドレスが指定されていればそれを、無ければスキャンして選択したものを返す"""
    return list(addresses) if addresses else select_motors(scan_sec)


def connect_motors(addresses):
    """
    1台ずつ順番に接続し、接続できた BLEController のリストを返す。
    各モーターの LED を選択順の色で点灯し、m.name にデバイス名を入れる。
    """
    motors = []
    for address in addresses:
        print("connecting to", address, "...")
        try:
            m = blecontroller.BLEController(address)
        except Exception as e:
            print("  failed:", address, e)
            continue
        try:
            m.name = m.read_device_name()
        except Exception:
            m.name = address
        r, g, b = led_color(len(motors))
        m.set_led(1, r, g, b)  # 点灯 (どのモーターが何番目か分かるように)
        print("  [{}] connected: {} ({})".format(len(motors), m.name, address))
        motors.append(m)
    return motors


def run_all(motors, func):
    """
    func(motor) を全モーターに対して並列に実行し、結果のリストを返す。
    順番に送るより各モーターの動き出しのずれが小さくなる。
    """
    if not motors:
        return []
    with ThreadPoolExecutor(max_workers=len(motors)) as ex:
        return list(ex.map(func, motors))


def disconnect_all(motors):
    """LED を白に戻して、すべて切断する (エラーは無視)"""
    def _release(m):
        try:
            m.set_led(1, 100, 100, 100)
            m.disconnect()
        except Exception as e:
            print("disconnect failed:", getattr(m, 'name', m.address), e)
    run_all(motors, _release)
