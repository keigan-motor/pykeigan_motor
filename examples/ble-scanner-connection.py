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
from bluepy.btle import Scanner

scan_sec=10.0
target_dev=None

"""
----------------------
モーターを検出する
----------------------
    raspberryPi等のOSではBluetoohのScanner実行時にルート権限が必要な為、sudoで実行するか以下の権限を付加する必要があります
    ex) sudo setcap 'cap_net_raw,cap_net_admin+eip' bluepy-helper
    
    Bluetoohでモーターが検出されない場合は、モーターの"インターフェイスのリセット"を実行して下さい。
    https://document.keigan-motor.com/basic/reset
"""
def scan(scan_sec):
    print("During scanning at ", scan_sec, "sec")
    scanner = Scanner()
    devices = scanner.scan(scan_sec)

    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and "KM-1" in value:
                print(value, ":", dev.addr)
                connection(dev,dev.addr)
                break

"""
----------------------
モーターに接続し、LEDを黄色で点滅させる
----------------------
"""
def connection(dev,macdress):
    target_dev = blecontroller.BLEController(macdress)
    target_dev.set_led(2,255,255,0)# (LEDflash:2,R:255,G:255,B:0)　https://document.keigan-motor.com/software_dev/lowapis/led


"""
Exit with key input
"""
while True:
    print("---------------------------------------")
    if sys.version_info<(3,0):
        inp = raw_input('Rescan:[s] Exit:[Other key] >>')
    else:
        inp = input('Rescan:[s] Exit:[Other key] >>')
    if inp == 's':
        scan(10)
    elif inp !=None:
        if target_dev:
            target_dev.set_led(1, 100, 100, 100)
            target_dev.disconnect()
        break