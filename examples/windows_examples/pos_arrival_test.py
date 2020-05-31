# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: Takashi Tokuda
Keigan Inc.
"""

import argparse
import sys
import pathlib
import serial
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


# isGo means on the way, !isGo means on the way back.
isGo = True

def go_round():
    global isGo
    if isGo:
        print('Go to the target')
        dev.move_to_pos(utils.deg2rad(1080))
    else:           
        print('Go back to Zero')
        dev.move_to_pos(utils.deg2rad(0))

# ログ情報callback
def on_motor_log_cb(log):
    global isGo
    print('log {} '.format(log))

    if log['error_codes'] == 'KM_SUCCESS':
        print('Command Success')
    elif log['error_codes'] == 'KM_SUCCESS_ARRIVAL':
        print('Position Arrival Success')
        isGo = not isGo
        go_round()


# モーター再接続 callback
def on_motor_reconnection_cb(cnt):
    go_round()

# モーター回転情報callback
def on_motor_measurement_cb(measurement):
    #print("\033[2;2H\033[2K", end="")
    # , end="", flush=True)
    print("\r"+'measurement {} '.format(measurement), end="")
    #print("\033[20;2H", end="",flush=True)


dev = usbcontroller.USBController(select_port())
dev.on_motor_log_cb = on_motor_log_cb
#dev.on_motor_connection_error_cb = on_motor_connection_error_cb
dev.on_motor_reconnection_cb = on_motor_reconnection_cb
dev.on_motor_measurement_value_cb = on_motor_measurement_cb
dev.enable_action()
dev.set_pos_control_threshold(utils.deg2rad(2)) # 位置のPID制御有効区間を大きくしておく 0.8[deg] -> 2.0[deg]
dev.set_notify_pos_arrival_settings(True, 0.00872665, 200) # 0.00872665[rad] = 0.5[deg] に 到達して 200[ms] 経過で モーターから位置到達通知
dev.set_speed(utils.rpm2rad_per_sec(200))
go_round()

"""
Exit with key input
"""

while True:
    sleep(0.1)
