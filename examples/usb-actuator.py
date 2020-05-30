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
from pykeigan import utils

parser = argparse.ArgumentParser(description='モーター動作 絶対位置往復運動')
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

os.system('clear')
for i in range(10):
    print("　　　　　　　")
print("\033[9;2H","---------------------------------------", "\033[2;2H\033[2K", end="",flush=True)

"""
----------------------
モーター接続、各種情報の取得
----------------------
"""
##モーター回転情報callback
def on_motor_measurement_cb(measurement):
    print("\033[2;2H\033[2K", end="")
    print('measurement {} '.format(measurement), end="", flush=True)

##ログ情報callback
def on_motor_log_cb(log):
    print("\033[5;2H\033[2K", end="", flush=True)
    print('log {} '.format(log), end="", flush=True)

#接続
dev=usbcontroller.USBController(args.port,False)
dev.on_motor_measurement_value_cb=on_motor_measurement_cb
dev.on_motor_log_cb=on_motor_log_cb


"""
----------------------
モーター動作 絶対位置往復運動
----------------------
"""
is_forward=False
cnt=0
#位置を監視して反転
def direction_measurement_cb(measurement):
    on_motor_measurement_cb(measurement)
    global is_forward,cnt

    if is_forward and measurement['position'] > (utils.deg2rad(720) - 0.02):
        is_forward=False
        cnt += 1
        if cnt > 4:
            dev.disable_action()
        else:
            dev.set_led(2, 255, 0, 255)
            dev.move_to_pos(utils.deg2rad(0))

    if not is_forward and measurement['position']<(0+0.02):
        is_forward=True
        dev.set_led(2, 0, 255, 255)
        dev.move_to_pos(utils.deg2rad(720))  # 2回転



dev.set_speed(utils.rpm2rad_per_sec(20))
dev.preset_position(0)#現在位置の座標を0に設定
dev.enable_action()
dev.on_motor_measurement_value_cb=direction_measurement_cb


"""
Exit with key input
"""

sleep(0.5)
while True:
    print("\033[10;2H", end="",flush=True)
    print("---------------------------------------")
    inp = input('Exit:[key input] >>')
    if inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.disconnect()
        break
