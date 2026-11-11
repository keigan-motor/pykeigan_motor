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

from pykeigan import blecontroller
from ble_select import select_motor, connect_motor
from pykeigan import utils

"""
----------------------
モーターへの接続
----------------------
    モーターのMACアドレスについて
        MACアドレスは KM1Scan.py で調べる事が可能です。省略した場合はスキャンして一覧から選択します(1台のみなら自動で接続)。
            $python3 ble-simple-connection.py xx:xx:xx:xx:xx:xx

        Bluetoohでモーターが検出されない場合は、モーターの"インターフェイスのリセット"を実行して下さい。
        https://document.keigan-motor.com/basic/reset
"""
parser = argparse.ArgumentParser(description="BLE 基本的な接続 (5rpm で正転)")
parser.add_argument('address', metavar='ADDRESS', nargs='?', help='モーターのMACアドレス (省略時はスキャン)')
args = parser.parse_args()

address = args.address or select_motor()  # 省略時はスキャンして選択 (1台なら自動)
if address is None:
    sys.exit()

dev=connect_motor(address)#モーターのMACアドレス
dev.set_led(2,255,255,0)# (LEDflash:2,R:255,G:255,B:0) https://document.keigan-motor.com/software_dev/lowapis/led
dev.enable_action()#安全装置。初めてモーターを動作させる場合に必ず必要。
dev.set_speed(utils.rpm2rad_per_sec(5))#rpm -> radian/sec
dev.run_forward()

"""
Exit with key input
"""
print("---------------------------------------")
input('Exit:[key input] >>')
dev.set_led(1, 100, 100, 100)
dev.disable_action()
dev.disconnect()
