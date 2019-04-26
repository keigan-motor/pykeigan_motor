# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
import signal
import sys
import os
import pathlib
from time import sleep
from concurrent.futures import ThreadPoolExecutor
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append( str(current_dir) + '/../' )
from pykeigan import usbcontroller


os.system('clear')
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
dev=usbcontroller.USBController('/dev/ttyUSB0',False)#モーターのアドレス 参照 usb-simple-connection.py
dev.on_motor_measurement_value_cb=on_motor_measurement_cb
dev.on_motor_imu_measurement_cb=on_motor_imu_measurement_cb
dev.on_motor_log_cb=on_motor_log_cb
dev.on_motor_connection_error_cb=on_motor_connection_error_cb

dev.enable_continual_imu_measurement()#IMUはデフォルトでOFFの為、取得する場合Onにする

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
while True:
    print("\033[20;2H", end="",flush=True)
    print("---------------------------------------")
    inp = input('Exit:[key input] >>')
    if inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.disconnect()
        break