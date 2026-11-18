# -*- coding: utf-8 -*-
"""
BLE: 安全設定 (safety settings, レジスタ 0x32) の使い方と、切断時の自動再接続

    $python3 ble-safety-settings-reconnect.py [MACアドレス] [--no-reboot] [--save]

----------------------
安全設定 (set_safety_settings / read_safety_settings)
----------------------
    bit0 (BIT_SAFETY_BLE_DISCONNECT_RESET): BLE が切断されたときにモーターを再起動する (1:ON, 0:OFF)
        デフォルトは 1 (ON)。切断されると再起動し、動作も止まります。
        0 (OFF) にすると再起動せず、そのまま次の接続を待ちます。
    設定は RAM のみです。再起動後も残すには save_all_registers() で flash に保存します (--save)。

----------------------
このサンプルの動作
----------------------
    1. 現在の安全設定を読み出して表示し、--no-reboot なら bit0 を OFF にする
    2. モーターを 5rpm で回し、1秒ごとに位置を表示する
    3. BLE が切断されたら (PC の Bluetooth を OFF にする、モーターを離す など)、つながるまで再接続を続ける
    4. 再接続したら、モーターが再起動したか (motorEnabled が 0 になったか) を表示し、動作を再開する
    Ctrl+C で終了します。--save を付けなかった場合、終了時に安全設定を元の値に戻します。
"""

import argparse
import sys
import pathlib
import threading
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller
from ble_select import select_motor, connect_motor
from pykeigan import utils

BIT = blecontroller.BLEController.BIT_SAFETY_BLE_DISCONNECT_RESET
SPEED_RPM = 5
RECONNECT_INTERVAL = 2.0  # 再接続に失敗したときの待ち時間 [sec]

parser = argparse.ArgumentParser(description="BLE 安全設定 (切断時の再起動) と自動再接続")
parser.add_argument('address', metavar='ADDRESS', nargs='?', help='モーターのMACアドレス (省略時はスキャン)')
parser.add_argument('--no-reboot', action='store_true', help='切断時に再起動しない (bit0 = 0)')
parser.add_argument('--save', action='store_true', help='安全設定を flash に保存する (save_all_registers)')
args = parser.parse_args()

address = args.address or select_motor()  # 省略時はスキャンして選択 (1台なら自動)
if address is None:
    sys.exit()

dev = connect_motor(address)

"""
----------------------
安全設定の読み出しと変更
----------------------
"""
try:
    original = dev.read_safety_settings()
except ValueError:
    print("Cannot read the safety settings: the motor firmware may not support it.")
    dev.disconnect()
    sys.exit(1)
print("safety settings: 0x{:02X} (reboot on BLE disconnect: {})".format(original, bool(original & BIT)))

settings = original & ~BIT if args.no_reboot else original | BIT  # bit0 以外はそのまま
dev.set_safety_settings(settings)
settings = dev.read_safety_settings()
print("set to         : 0x{:02X} (reboot on BLE disconnect: {})".format(settings, bool(settings & BIT)))
if args.save:
    dev.save_all_registers()  # flash への保存は数秒かかります
    time.sleep(3)
    print("saved to flash")

"""
----------------------
切断の検出
----------------------
    on_motor_connection_error_cb は BLE のスレッドから呼ばれます。
    この中で connect() を呼ぶと止まってしまうので、イベントで知らせてメインのループで再接続します。
"""
disconnected = threading.Event()


def on_connection_error(e):
    print("\n!! {} ({})".format(e, time.strftime('%H:%M:%S')), flush=True)
    disconnected.set()


dev.on_motor_connection_error_cb = on_connection_error


def start_motion():
    dev.set_led(2, 0, 255, 0)  # 緑の点滅: 動作中
    dev.enable_action()
    dev.set_speed(utils.rpm2rad_per_sec(SPEED_RPM))
    dev.run_forward()


def reconnect():
    """つながるまで再接続を続ける。再接続後の設定のやり直しもここで行う。"""
    t0 = time.time()
    n = 0
    while True:
        n += 1
        try:
            dev.connect()
            break
        except (blecontroller.DeviceNotFoundError, ConnectionError) as e:
            # 再起動中のモーターは数秒間見つからないことがあります
            print("  reconnect attempt {} failed: {}".format(n, e), flush=True)
            time.sleep(RECONNECT_INTERVAL)
    print("reconnected ({:.1f}s, {} attempts)".format(time.time() - t0, n))
    disconnected.clear()

    try:
        # 接続時に BLEController が行う設定 (再起動すると RAM の設定は flash の値に戻ります)
        dev.set_interface(dev.interface_type['BLE'] + dev.interface_type['BTN'])
        status = dev.read_status()
        now = dev.read_safety_settings()
        rebooted = not status['motorEnabled']  # 再起動すると motorEnabled は 0 になる
        print("motor {} (safety settings: 0x{:02X})".format('was rebooted' if rebooted else 'kept running', now))
        if now != settings:
            # 保存していない設定は再起動でデフォルト (bit0 = 1) に戻る
            print("safety settings were reset by the reboot: set again")
            dev.set_safety_settings(settings)
        start_motion()
    except (ConnectionError, TimeoutError, ValueError) as e:
        # 再接続の直後にまた切れた / 応答がなかった: 次のループでもう一度再接続する
        print("  setup after reconnection failed: {!r}".format(e), flush=True)
        disconnected.set()


start_motion()
print("---------------------------------------")
print("running at {} rpm. Turn off Bluetooth of the PC etc. to test the reconnection. Exit: Ctrl+C".format(SPEED_RPM))

try:
    while True:
        if disconnected.is_set() or not dev.is_connected():
            reconnect()
            continue
        try:
            m = dev.read_motor_measurement()
            print("position {:9.1f} deg".format(utils.rad2deg(m['position'])), flush=True)
        except (ConnectionError, TimeoutError, ValueError):
            pass  # 切断直後 / 応答なし: 切れていれば次のループで再接続する
        disconnected.wait(1.0)
except KeyboardInterrupt:
    print()

"""
----------------------
終了
----------------------
"""
try:
    dev.on_motor_connection_error_cb = False
    dev.set_led(1, 100, 100, 100)
    dev.disable_action()
    if not args.save and settings != original:
        dev.set_safety_settings(original)  # 保存しなかった場合は元に戻す
        print("safety settings restored: 0x{:02X}".format(original))
except (ConnectionError, TimeoutError, ValueError) as e:
    print("could not send the last commands:", e)
dev.disconnect()
