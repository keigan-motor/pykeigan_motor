# -*- coding: utf-8 -*-
"""
----------------------
複数のモーターへの接続
----------------------
    BLE で複数のモーターに接続し、モーターごとに違う色で LED を点滅させて、5rpm で同時に正転させる。
    キー入力で停止・切断。

        $python3 ble-multi-simple-connection.py                                 (スキャンして選択)
        $python3 ble-multi-simple-connection.py xx:xx:xx:xx:xx:xx yy:yy:yy:yy:yy:yy

    スキャン時は 0,1 のように番号をカンマ区切りで入力します (a ですべて)。
"""
import argparse
import sys
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from ble_multi import get_addresses, connect_motors, run_all, disconnect_all, led_color
from pykeigan import utils

parser = argparse.ArgumentParser(description="BLE 複数台の接続 (5rpm で同時に正転)")
parser.add_argument('addresses', metavar='ADDRESS', nargs='*', help='モーターのMACアドレス (複数可。省略時はスキャン)')
args = parser.parse_args()

motors = connect_motors(get_addresses(args.addresses))
if not motors:
    sys.exit("接続できたモーターがありません")


def start(m):
    r, g, b = led_color(motors.index(m))
    m.set_led(2, r, g, b)  # (LEDflash:2, R, G, B) https://document.keigan-motor.com/software_dev/lowapis/led
    m.enable_action()  # 安全装置。初めてモーターを動作させる場合に必ず必要。
    m.set_speed(utils.rpm2rad_per_sec(5))  # rpm -> radian/sec
    m.run_forward()


run_all(motors, start)  # 全モーターに並列に送信 (同時に動き出す)
print(len(motors), "motors are running")

"""
Exit with key input
"""
print("---------------------------------------")
input('Exit:[key input] >>')
run_all(motors, lambda m: m.disable_action())
disconnect_all(motors)
