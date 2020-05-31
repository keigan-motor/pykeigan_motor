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
dev.set_curve_type(10) # 10: ダイレクト位置制御（速度制限、カーブなしで位置制御を行う。振動対策）
dev.set_speed_i(0)
#dev.set_pos_control_threshold(utils.deg2rad(2))
#dev.set_position_p(10)
#dev.set_position_i(2)
#dev.set_speed(utils.rpm2rad_per_sec(20))
# 連続で動作命令を送る場合、位置到達時の通知設定をOFFとする必要がある
# dev.set_notify_pos_arrival_settings(False, 0.00872665, 200) # 第1引数 False で無効化
dev.set_safe_run_settings(True, 100, 3) # 第1引数が True の場合、5000[ms]以内に次の動作命令が来ないと、停止する 0:free,1:disable,2:stop, 3:position固定

# 最初 0[deg] へ移動
targetPos = 0
inc = 0
"""
Exit with key input
"""
try:
    while True:
        dev.move_to_pos(utils.deg2rad(targetPos+inc))
        inc += 0.1 # 少しずつ目標位置をずらしていく。位置固定の場合はこの行をコメントアウト
        sleep(0.01)
        if msvcrt.kbhit():
            c = msvcrt.getwch()
            print(c)
            if c == 'f': # 1080[deg] へ移動
                targetPos = 1080
            elif c == 'b': # 0[deg] へ移動
                targetPos = 0



except KeyboardInterrupt:
    if dev:
        dev.disable_action()
    print('Ctrl-C')