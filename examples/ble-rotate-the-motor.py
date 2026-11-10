# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""

import argparse
import sys
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from time import sleep
from pykeigan import blecontroller
from ble_select import select_motor
from pykeigan import utils

"""
----------------------
モーターを5rpmで 正転(10秒) -> 逆転(10秒) -> 停止(トルクあり) -> 停止(トルク無し)
----------------------
    $python3 ble-rotate-the-motor.py [MACアドレス]   (省略時はスキャン。参照 ble-simple-connection.py)
"""
parser = argparse.ArgumentParser(description="BLE 正転 -> 逆転 -> 停止")
parser.add_argument('address', metavar='ADDRESS', nargs='?', help='モーターのMACアドレス (省略時はスキャン)')
args = parser.parse_args()

address = args.address or select_motor()  # 省略時はスキャンして選択 (1台なら自動)
if address is None:
    sys.exit()

dev=blecontroller.BLEController(address)
dev.enable_action()#安全装置。初めてモーターを動作させる場合に必ず必要。
dev.set_speed(utils.rpm2rad_per_sec(5))#rpm -> radian/sec

print('run forward (10s)')
dev.set_led(1, 0, 200, 0)
dev.run_forward()

sleep(10)

print('run reverse (10s)')
dev.set_led(1, 0, 0, 200)
dev.run_reverse()

sleep(10)

print('stop (with torque, 10s)')
dev.set_led(1, 200, 0, 0)
dev.stop_motor()

sleep(10)

print('free')
dev.set_led(1, 100, 100, 100)
dev.free_motor()


"""
Exit with key input
"""
print("---------------------------------------")
input('Exit:[key input] >>')
dev.set_led(1, 100, 100, 100)
dev.disconnect()
