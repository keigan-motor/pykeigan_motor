# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""

import sys
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller
from pykeigan import utils

"""
----------------------
モーターへの接続
----------------------
    モーターのMACアドレスについて
        MACアドレスは"nRF Connect"を使用して調べる事が可能です。 
        https://play.google.com/store/apps/details?id=no.nordicsemi.android.mcp
        
        Bluetoohでモーターが検出されない場合は、モーターの"インターフェイスのリセット"を実行して下さい。
        https://document.keigan-motor.com/basic/reset
"""

dev=blecontroller.BLEController("d1:5a:fa:a7:d9:5d")#モーターのMACアドレス
dev.set_led(2,255,255,0)# (LEDflash:2,R:255,G:255,B:0) https://document.keigan-motor.com/software_dev/lowapis/led
dev.enable_action()#安全装置。初めてモーターを動作させる場合に必ず必要。
dev.set_speed(utils.rpm2rad_per_sec(5))#rpm -> radian/sec
dev.run_forward()

"""
Exit with key input
"""
while True:
    print("---------------------------------------")
    if sys.version_info<(3,0):
        inp = raw_input('Exit:[key input] >>')
    else:
        inp = input('Exit:[key input] >>')
    if inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.disconnect()
        break