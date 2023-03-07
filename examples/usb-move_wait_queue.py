# -*- coding: utf-8 -*-
"""
Created on Apr 2021

@author: Keigan Inc.
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

parser = argparse.ArgumentParser(description="モーター動作 相対移動と絶対位置移動")
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

os.system('clear')
for i in range(10):
    print("　　　　　　　")
print("\033[9;2H","---------------------------------------", "\033[2;2H\033[2K")
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

##ログ情報callback
def on_motor_log_cb(log):
    print("\033[5;2H\033[2K")
    sys.stdout.flush()
    print('log {} '.format(log))
    sys.stdout.flush()

#接続
dev = usbcontroller.USBController(args.port)
#dev.on_motor_log_cb = on_motor_log_cb
dev.on_motor_measurement_value_cb = on_motor_measurement_cb

dev.enable_action()
dev.set_speed(utils.rpm2rad_per_sec(100))

# 位置到達の判定条件を決める
# def set_notify_pos_arrival_settings
#   引数1: python側に通知するかどうか 
#   引数2: 到達しているとみなす許容誤差 ±θ [rad]
#   引数3: 到達している状態が t[ms] 継続したら到達完了とみなす
# （例）誤差 ± 1.0[deg] で到達判定OK 到着判定が 1ms 継続で、モーターから位置到達通知
dev.set_notify_pos_arrival_settings(True, utils.deg2rad(1), 1) 

dev.set_curve_type(0)

# move_to_pos_wait / move_by_dist_wait コマンドはファームウェア ver 2.66以降対応

## 絶対位置へ移動（到着まで命令を保持）
dev.move_to_pos_wait(utils.deg2rad(0))
dev.move_to_pos_wait(utils.deg2rad(90))
dev.move_to_pos_wait(utils.deg2rad(0))
dev.move_to_pos_wait(utils.deg2rad(-90))
dev.move_to_pos_wait(utils.deg2rad(0))

## 相対位置へ移動（到着まで命令を保持）
# dev.move_by_dist_wait(utils.deg2rad(90))
# dev.move_by_dist_wait(utils.deg2rad(-90))
# dev.move_by_dist_wait(utils.deg2rad(90))
# dev.move_by_dist_wait(utils.deg2rad(-90))

try:
    while True:  
        pass  # ここに、Ctrl-C で止めたい処理を書く

except KeyboardInterrupt:
    if dev:
        dev.disable_action()
    print('Ctrl-C')