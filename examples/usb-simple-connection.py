# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""

import sys
import pathlib
import time
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append( str(current_dir) + '/../' )

from pykeigan import usbcontroller
from pykeigan import utils

"""
----------------------
モーターへの接続
----------------------
    モーターのデバイスファイル指定について
        "/dev/ttyUSB0"で表示されるデバイス名での接続は、複数のモーターを接続した場合に変わる可能性がある。
        複数のモーターがある場合で、モーターを特定して接続する場合は "$ls /dev/serial/by-id/" で表示されるデバイスを使用する。
            ex)/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DM00LSSA-if00-port0

"""

dev=usbcontroller.USBController('/dev/ttyUSB0',False)
dev.set_led(2,255,255,0)# (LEDflash:2,R:255,G:255,B:0) https://document.keigan-motor.com/software_dev/lowapis/led
dev.enable_action()#安全装置。初めてモーターを動作させる場合に必ず必要。
dev.set_speed(utils.rpm2rad_per_sec(5))#rpm -> radian/sec
dev.run_forward()

"""
Exit with key input
"""
while True:
    print("---------------------------------------")
    inp = input('Exit:[key input] >>')
    if inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()#USB接続は切断してもモーター動作は停止しない為、明示的に停止する必要がある
        dev.disconnect()
        break