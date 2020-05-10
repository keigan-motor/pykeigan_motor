# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: Takashi Tokuda
Keigan Inc.
"""

from pykeigan import utils
from pykeigan import usbcontroller
import argparse
import sys
import pathlib
import serial
import msvcrt
import serial.tools.list_ports
from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append(str(current_dir) + '/../')


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

    print('Conncted to', portdev)

    return portdev


# isGo means on the way, !isGo means on the way back.
isGo = False

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



# エラー情報callback


def on_motor_connection_error_cb(e):
    print("\033[16;2H\033[2K", end="", flush=True)
    print('error {} '.format(e), end="", flush=True)
    com_err_cnt = 0
    while True:  # 接続できるまで接続試行を指定回数繰り返す
        com_state = False
        print("3")
        #print('Serial connection lost. Retrying {} times'.format(com_err_cnt+1))
        dev.disconnect()  # 接続断
        try:  # 接続の再構築
            dev.connect()  # 接続を再構築
            #dev = usbcontroller.USBController(args.port,False)
            print('Serial connection established.')
            sleep(2)
            dev.recover()
            go_round()
            break  # 接続に成功したのでwhileを抜ける
        except serial.serialutil.SerialException:  # 接続の再構築に失敗した場合はこちらに遷移
            com_err_cnt += 1  # 試行済回数を上げる
            print('Serial connection Failed. count: ', com_err_cnt)
            sleep(1.5)
            continue  # エラー停止にしないでwhileループの頭に戻る

# モーター回転情報callback


def on_motor_measurement_cb(measurement):
    #print("\033[2;2H\033[2K", end="")
    # , end="", flush=True)
    print("\r"+'measurement {} '.format(measurement), end="")
    #print("\033[20;2H", end="",flush=True)


dev = usbcontroller.USBController(select_port())
dev.on_motor_log_cb = on_motor_log_cb
dev.on_motor_connection_error_cb = on_motor_connection_error_cb
dev.on_motor_measurement_value_cb = on_motor_measurement_cb
dev.enable_action()
dev.set_speed(utils.rpm2rad_per_sec(200))
dev.move_to_pos(utils.deg2rad(1080))
isGo = True

"""
Exit with key input
"""
while True:
    sleep(0.1)
