# -*- coding: utf-8 -*-
"""
Created on Apr 24 2021

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

from pykeigan import utils
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


dev = usbcontroller.USBController(select_port())
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