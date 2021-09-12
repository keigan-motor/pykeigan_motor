# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: Takashi Tokuda
Keigan Inc.
"""

import argparse
import sys
import pathlib
import msvcrt
import serial.tools.list_ports
from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller


def select_port():
    print('Available COM ports list')

    portlist = serial.tools.list_ports.comports()

    if not portlist:
        print('No available port')
        sys.exit()

    print('i : name')
    print('--------')
    for i, port in enumerate(portlist):
        print(i, ':', port.device)

    print('- Enter the port number (0~)')
    portnum = input()
    portnum = int(portnum)

    portdev = None
    if portnum in range(len(portlist)):
        portdev = portlist[portnum].device

    print('Conncted to', portdev)

    return portdev


for i in range(24):
    print("　　　　　　　")

print("\033[19;2H","---------------------------------------", "\033[2;2H\033[2K", end="",flush=True)

"""
----------------------
モーターに接続し、各種情報の取得
----------------------
"""
##モーター回転情報callback
def on_motor_measurement_cb(measurement):
    print("\033[2;2H\033[2K", end="")
    print('measurement {} '.format(measurement), end="", flush=True)

##IMU情報callback
def on_motor_imu_measurement_cb(measurement):
    print("\033[6;2H\033[2K", end="")
    print('imu_measurement {} '.format(measurement), end="", flush=True)

##ログ情報callback
def on_motor_log_cb(log):
    print("\033[12;2H\033[2K", end="", flush=True)
    print('log {} '.format(log), end="", flush=True)

##エラー情報callback
def on_motor_connection_error_cb(e):
    print("\033[16;2H\033[2K", end="", flush=True)
    print('error {} '.format(e), end="", flush=True)


#接続
#dev=usbcontroller.USBController('/dev/ttyUSB0',False)#モーターのアドレス 参照 usb-simple-connection.py
dev=usbcontroller.USBController(select_port()) #モーターのアドレス 参照 usb-simple-connection.py
dev.on_motor_measurement_value_cb=on_motor_measurement_cb
dev.on_motor_imu_measurement_cb=on_motor_imu_measurement_cb
dev.on_motor_log_cb=on_motor_log_cb
dev.on_motor_connection_error_cb=on_motor_connection_error_cb

dev.enable_continual_imu_measurement()#IMUはデフォルトでOFFの為、取得する場合Onにする

# ビットフラグ 0x40 でモーターの時刻送信を有効化 ※ モーターFW ver 2.62以降対応、ver2.61以下は無効
dev.set_motor_measurement_settings(5) 

#モーター動作
dev.set_led(2,255,255,0)
sleep(3)
dev.enable_action()
dev.set_speed(1.0)
dev.run_forward()
sleep(10)
dev.disable_action()


"""
Exit with key input
"""

sleep(0.5)

try:
    while True:
        print("\033[20;2H", end="",flush=True)
        print("---------------------------------------")
        inp = input('Exit:[key input] >>')
        if inp !=None:
            dev.set_led(1, 100, 100, 100)
            dev.disable_action()
            dev.disconnect()
            break


except KeyboardInterrupt:
    if dev:
        dev.disable_action()
        dev.disconnect()
    print('Ctrl-C')