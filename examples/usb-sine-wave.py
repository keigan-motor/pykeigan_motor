# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: Takashi Tokuda
Keigan Inc.
"""

import argparse
from argparse import RawTextHelpFormatter
import sys
import pathlib
from time import sleep
import signal # タイマーで定期実行するためのシグナルライブラリ（高精度に定期実行できる）
import math
import numpy as np

import matplotlib.pyplot as plt # グラフ作成のため

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import utils
from pykeigan import usbcontroller






# ログ情報callback
def on_motor_log_cb(log):
    print('log {} '.format(log))

    if log['error_codes'] == 'KM_SUCCESS':
        print('Command Success')
    elif log['error_codes'] == 'KM_SUCCESS_ARRIVAL':
        print('Position Arrival Success')


data = []
maxNum = 500

# モーター回転情報callback
def on_motor_measurement_cb(measurement):
    global data, maxNum
    print("\r"+'measurement {} '.format(measurement), end="")

    

# 正弦波
f = 0.5 # 周波数 [s]
ampDegree = 80 # 振幅 [degree]
t = 0 
res = 0.01 # 時間分解能 [s]
oneRound = f/res # 1周分


# シグナルライブラリ（schedular関数を定期的に呼ぶ）のタイマースタート
def timer_start():
    signal.setitimer(signal.ITIMER_REAL, 1, res) # 第2引数の1は、1秒後にスタート、第3引数は、タイマー間隔

# シグナルライブラリ（schedular関数を定期的に呼ぶ）のタイマーストップ
def timer_stop():
    signal.setitimer(signal.ITIMER_REAL, 0, res) # 第2引数を0にすると、タイマーは停止する決まり




# シグナルライブラリで定期実行される関数。
def scheduler(arg1, args2):
    global ampDegree, t, res, oneRound    
    target = utils.deg2rad(ampDegree * math.sin(t * 2 * math.pi / oneRound))
    dev.move_to_pos(target)
    t += 1


description=""
parser = argparse.ArgumentParser(description=description,formatter_class=RawTextHelpFormatter)
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

dev=usbcontroller.USBController(args.port)
#dev.on_motor_log_cb = on_motor_log_cb
dev.on_motor_measurement_value_cb = on_motor_measurement_cb
dev.enable_action()
dev.set_speed(utils.rpm2rad_per_sec(10))
dev.reset_all_pid()
dev.move_to_pos(0)

sleep(2)

print("sine wave start !")
# 目標位置からの偏差には以下のゲインを調整するか、振幅自体を変える
# 振幅自体変えた方がベター??

# 新設 curveType:10 ダイレクト位置制御（速度制限、カーブなしでマスター側が時間管理して位置制御を行う。）
dev.set_curve_type(10) 
dev.set_speed_p(3) # デフォルト 14 振動対策
dev.set_speed_i(0)
dev.set_pos_control_threshold(utils.deg2rad(1000))
dev.set_position_i(80)

# # シグナルライブラリ（schedular関数を定期的に呼ぶ, timer_start(), timer_stop()も参照）で定期実行することの宣言
signal.signal(signal.SIGALRM, scheduler) 
timer_start()

try:
    while True:
        continue


except KeyboardInterrupt:
    if dev:
        dev.disable_action()
    print('Ctrl-C')