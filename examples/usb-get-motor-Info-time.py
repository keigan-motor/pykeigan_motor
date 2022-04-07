# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
import argparse
import signal
import sys
import os
import pathlib
from time import sleep
from concurrent.futures import ThreadPoolExecutor

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller

parser = argparse.ArgumentParser(description='モーターに接続し、各種情報の取得')
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

os.system('clear')
for i in range(24):
    print("　　　　　　　")

print("\033[19;2H","---------------------------------------", "\033[2;2H\033[2K")
sys.stdout.flush()

"""
----------------------
モーターに接続し、各種情報の取得
----------------------
"""
##モーター回転情報callback
def on_motor_measurement_cb(measurement):
    print("\033[2;2H\033[2K")
    print('measurement {} '.format(measurement))
    sys.stdout.flush()

##IMU情報callback
def on_motor_imu_measurement_cb(measurement):
    print("\033[6;2H\033[2K")
    print('imu_measurement {} '.format(measurement))
    sys.stdout.flush()

##ログ情報callback
def on_motor_log_cb(log):
    print("\033[12;2H\033[2K")
    sys.stdout.flush()
    print('log {} '.format(log))
    sys.stdout.flush()

##エラー情報callback
def on_motor_connection_error_cb(e):
    print("\033[16;2H\033[2K")
    sys.stdout.flush()
    print('error {} '.format(e))
    sys.stdout.flush()


#接続
#dev=usbcontroller.USBController('/dev/ttyUSB0',False)#モーターのアドレス 参照 usb-simple-connection.py
dev=usbcontroller.USBController(args.port,False)#モーターのアドレス 参照 usb-simple-connection.py
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
    print("\033[20;2H")
    sys.stdout.flush()
    print("---------------------------------------")
    if sys.version_info <(3,0):
        inp = raw_input('Exit:[key input] >>')
    else:
        inp = input('Exit:[key input] >>')
    if inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.disconnect()
        break
