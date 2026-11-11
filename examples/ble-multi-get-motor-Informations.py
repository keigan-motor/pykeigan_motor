# -*- coding: utf-8 -*-
"""
----------------------
複数のモーターの回転情報を一覧表示
----------------------
    接続したすべてのモーターの 位置[deg] / 速度[rpm] / トルク[N.m] と、
    回転情報の受信頻度[Hz] (notify の間隔。台数を増やしたときの通信状況の目安) を 0.2秒ごとに表示する。
    モーターは動かさないので、手で回して確認して下さい。キー入力で終了。

        $python3 ble-multi-get-motor-Informations.py
        $python3 ble-multi-get-motor-Informations.py xx:xx:xx:xx:xx:xx yy:yy:yy:yy:yy:yy
"""
import argparse
import os
import sys
import pathlib
import threading
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from ble_multi import get_addresses, connect_motors, run_all, disconnect_all
from pykeigan import utils

parser = argparse.ArgumentParser(description="BLE 複数台の回転情報を一覧表示")
parser.add_argument('addresses', metavar='ADDRESS', nargs='*', help='モーターのMACアドレス (複数可。省略時はスキャン)')
args = parser.parse_args()

if os.name == 'nt':
    os.system('')  # Windows のコンソールでエスケープシーケンスを有効にする

motors = connect_motors(get_addresses(args.addresses))
if not motors:
    sys.exit("接続できたモーターがありません")

# モーターごとの最新値と受信時刻 (コールバックはバックグラウンドのスレッドから呼ばれる)
latest = [None] * len(motors)
stamps = [[] for _ in motors]
lock = threading.Lock()


def make_callback(i):
    # i=i ではなく関数で包んで、モーターごとに番号を固定する
    def on_measurement(v):
        now = time.time()
        with lock:
            latest[i] = v
            stamps[i].append(now)
            while stamps[i] and now - stamps[i][0] > 2.0:  # 直近2秒分
                stamps[i].pop(0)
    return on_measurement


for i, m in enumerate(motors):
    m.on_motor_measurement_value_cb = make_callback(i)
run_all(motors, lambda m: m.enable_continual_motor_measurement())

running = True


def show():
    os.system('cls' if os.name == 'nt' else 'clear')
    while running:
        now = time.time()
        lines = ["{:<3} {:<18} {:<20} {:>10} {:>8} {:>8} {:>6}".format(
            'No', 'name', 'address', 'pos[deg]', 'vel[rpm]', 'torque', 'Hz')]
        with lock:
            for i, m in enumerate(motors):
                v = latest[i]
                hz = len(stamps[i]) / 2.0
                if v is None or now - v['received_unix_time'] > 1.0:
                    values = "{:>10} {:>8} {:>8}".format('-', '-', '-')
                else:
                    values = "{:>10.2f} {:>8.2f} {:>8.3f}".format(
                        utils.rad2deg(v['position']), utils.rad_per_sec2rpm(v['velocity']), v['torque'])
                state = '' if m.is_connected() else '  (disconnected)'
                lines.append("{:<3} {:<18} {:<20} {} {:>6.1f}{}".format(i, m.name, m.address, values, hz, state))
        # 1行目から上書きして表示 (カーソルは入力行の手前に戻す)
        sys.stdout.write("\0337\033[1;1H" + "".join("\033[2K" + l + "\n" for l in lines) + "\0338")
        sys.stdout.flush()
        time.sleep(0.2)


t = threading.Thread(target=show, daemon=True)
t.start()

time.sleep(0.3)
sys.stdout.write("\033[{};1H---------------------------------------\n".format(len(motors) + 3))
input('Exit:[key input] >>')
running = False
t.join()
run_all(motors, lambda m: m.disable_continual_motor_measurement())
disconnect_all(motors)
