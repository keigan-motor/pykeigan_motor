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
from ble_select import select_motor, connect_motor

scan_sec=5.0
target_dev=None

"""
----------------------
モーターを検出し、選択して接続する
----------------------
    Windows / Linux(Raspberry Pi 含む) ともに sudo は不要です。
    見つかったモーターが一覧表示されるので、番号を入力して接続します。

    Bluetoohでモーターが検出されない場合は、モーターの"インターフェイスのリセット"を実行して下さい。
    https://document.keigan-motor.com/basic/reset
"""

"""
----------------------
モーターに接続し、LEDを黄色で点滅させる
----------------------
"""
def release():
    # 接続中のモーターはアドバタイズを停止するためスキャンに出てこない。再スキャン前に切断する
    global target_dev
    if target_dev:
        target_dev.set_led(1, 100, 100, 100)
        target_dev.disconnect()
        target_dev = None
        print('disconnected')

def connection(macdress):
    global target_dev
    target_dev = connect_motor(macdress)
    target_dev.set_led(2,255,255,0)# (LEDflash:2,R:255,G:255,B:0)　https://document.keigan-motor.com/software_dev/lowapis/led
    print('connected:', target_dev.read_device_name())


"""
Exit with key input
"""
while True:
    print("---------------------------------------")
    inp = input('Scan & connect:[s] Exit:[Other key] >>')
    if inp == 's':
        release()
        address = select_motor(scan_sec, auto_select_single=False)
        if address:
            connection(address)
    else:
        release()
        break
