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
from pykeigan import utils

os.system('clear')
for i in range(10):
    print("　　　　　　　")
print("\033[9;2H","---------------------------------------", "\033[2;2H\033[2K", end="",flush=True)

"""
----------------------
モーターに接続し、各種情報の取得
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
dev=usbcontroller.USBController('/dev/ttyUSB0',False)
dev.on_motor_measurement_value_cb=on_motor_measurement_cb
dev.on_motor_log_cb=on_motor_log_cb

"""
----------------------
モーター動作 相対移動
----------------------
"""
dev.set_led(2,255,255,0)
sleep(3)
dev.enable_action()
dev.set_speed(utils.rpm2rad_per_sec(10))#rpm-> rad/sec

dev.move_by_dist(utils.deg2rad(180),None)#Degree-> rad
sleep(5)
dev.move_by_dist(utils.deg2rad(-180),None)
sleep(5)
dev.move_by_dist(utils.deg2rad(360),utils.rpm2rad_per_sec(15))#rpm-> rad/sec
sleep(6)

"""
----------------------
モーター動作 絶対位置移動
----------------------
"""
dev.set_curve_type(1)
dev.set_led(2,0,255,255)
dev.set_speed(utils.rpm2rad_per_sec(30))
dev.preset_position(0)#現在位置の座標を0に設定
dev.move_to_pos(utils.deg2rad(90),(utils.deg2rad(90)/3))
sleep(4)
dev.move_to_pos(utils.deg2rad(180),(utils.deg2rad(90)/3))
sleep(4)
dev.move_to_pos(utils.deg2rad(360),(utils.deg2rad(180)/3))
sleep(4)
dev.move_to_pos(utils.deg2rad(720),(utils.deg2rad(360)/3))
sleep(4)
dev.move_to_pos(utils.deg2rad(0),(utils.deg2rad(720)/4))
sleep(5)
dev.set_led(2, 255, 50, 255)
dev.set_curve_type(0)#Turn off Motion control
dev.move_to_pos(utils.deg2rad(90),(utils.deg2rad(90)/0.5))
sleep(2)
dev.move_to_pos(utils.deg2rad(180),(utils.deg2rad(90)/0.5))
sleep(2)
dev.move_to_pos(utils.deg2rad(90),(utils.deg2rad(90)/0.5))
sleep(2)
dev.move_to_pos(utils.deg2rad(360),(utils.deg2rad(270)/1))
sleep(2)

dev.set_led(1,255,255,0)
dev.disable_action()

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
        dev.set_curve_type(1)
        dev.disable_action()
        dev.disconnect()
        break