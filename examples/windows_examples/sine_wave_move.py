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
import signal # タイマーで定期実行するためのシグナルライブラリ（高精度に定期実行できる）
import math

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../../') # give 1st priority to the directory where pykeigan exists

from pykeigan import utils
from pykeigan import usbcontroller

RUN_CMD_INTERVAL = 0.01

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

    print('Connected to', portdev)

    return portdev



# ログ情報callback
def on_motor_log_cb(log):
    print('log {} '.format(log))

    if log['error_codes'] == 'KM_SUCCESS':
        print('Command Success')
    elif log['error_codes'] == 'KM_SUCCESS_ARRIVAL':
        print('Position Arrival Success')




# モーター回転情報callback
def on_motor_measurement_cb(measurement):
    print("\r"+'measurement {} '.format(measurement), end="")


# 正弦波諸元
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
    t += res


dev = usbcontroller.USBController(select_port())
#dev.on_motor_log_cb = on_motor_log_cb
dev.on_motor_measurement_value_cb = on_motor_measurement_cb
dev.enable_action()

#dev.set_pos_control_threshold(utils.deg2rad(2))
#dev.set_position_p(10)
#dev.set_position_i(2)
#dev.set_speed(utils.rpm2rad_per_sec(20))
# 連続で動作命令を送る場合、位置到達時の通知設定をOFFとする必要がある
# dev.set_notify_pos_arrival_settings(False, 0.00872665, 200) # 第1引数 False で無効化
dev.set_safe_run_settings(True, 100, 3) # 第1引数が True の場合、5000[ms]以内に次の動作命令が来ないと、停止する 0:free,1:disable,2:stop, 3:position固定
dev.move_to_pos(0)

sleep(3)
dev.set_curve_type(10) # 10: ダイレクト位置制御（速度制限、カーブなしで位置制御を行う。振動対策）

# シグナルライブラリ（schedular関数を定期的に呼ぶ, timer_start(), timer_stop()も参照）で定期実行することの宣言
signal.signal(signal.SIGALRM, scheduler) 
timer_start()

try:
    while True:
        continue


except KeyboardInterrupt:
    if dev:
        dev.disable_action()
    print('Ctrl-C')