# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
import argparse
import sys
import os
import pathlib
from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller
from pykeigan import utils

parser = argparse.ArgumentParser(description='モーター動作　トルク制御')
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

os.system('clear')
for i in range(6):
    print("　　　　　　　")
print("\033[5;1H","---------------------------------------",  end="",flush=True)

"""
----------------------
モーター接続し、各種情報の取得
----------------------
"""
torque=0
position=0

##ログ情報callback
def on_motor_log_cb(log):
    if log['error_codes']!='KM_SUCCESS':
        print('log {} '.format(log))

#接続
dev=usbcontroller.USBController(args.port,False)
dev.on_motor_log_cb=on_motor_log_cb

"""
----------------------
モーター動作　トルク制御
----------------------
モーターを手で回して行くとトルクが加算され、重くなる。45度毎で0.025N*m増加
"""
torque_level=0

##トルクを監視し45度毎にトルクを増加
def on_motor_measurement_cb(measurement):
    global torque_level
    torque=measurement['torque']
    position=measurement['position']
    now_torque_level=round(utils.rad2deg(position)/45)*0.025
    if torque_level!=now_torque_level:
        torque_level=now_torque_level
        dev.set_max_torque(abs(torque_level))

    print('\033[4;1H\033[2K','torque/max_torque:{0:.2f}/{1:.2f}'.format(torque,torque_level), end="", flush=True)

def stop_torque_control_like_closing_cap():
    if dev:
        dev.on_motor_measurement_value_cb=None
        dev.disable_action()
        dev.set_max_torque(10.0)

def start_torque_control_like_closing_cap():
    global torque_level
    print('\033[2;1H\033[2K', 'Please try to turn the motor by hand.', end="", flush=True)
    dev.disable_action()
    dev.preset_position(0)
    sleep(0.2)
    dev.enable_action()
    dev.move_to_pos(0,utils.rpm2rad_per_sec(10))
    torque_level=10
    dev.on_motor_measurement_value_cb = on_motor_measurement_cb

"""
Exit with key input
"""

sleep(0.5)
while True:
    print('\033[6;1H\033[2K', end="", flush=True)
    inp = input('Command input > Start:[s] Reset:[r] Exit:[Other key] >>')
    if inp == 's':
        start_torque_control_like_closing_cap()
    elif inp == 'r':
        stop_torque_control_like_closing_cap()
    elif inp !=None:
        print()
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.set_max_torque(10.0)
        sleep(0.2)
        dev.disconnect()
        break
