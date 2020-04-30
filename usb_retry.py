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
sys.path.append( str(current_dir) + '/../' )

print(sys.path)


from pykeigan import usbcontroller
from pykeigan import utils


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




"""
----------------------
モーターを5rpmで 正転(10秒) -> 逆転(10秒) -> 停止(トルクあり) -> 停止(トルク無し)
----------------------

"""
dev=usbcontroller.USBController(select_port(),baud=115200)#モーターのアドレス 参照 usb-simple-connection.py
dev.enable_action()#安全装置。初めてモーターを動作させる場合に必ず必要。
dev.set_speed(utils.rpm2rad_per_sec(5))#rpm -> radian/sec

dev.set_led(1, 0, 200, 0)
dev.run_forward()

# sleep(10)

# dev.set_led(1, 0, 0, 200)
# dev.run_reverse()

# sleep(10)

# dev.set_led(1, 200, 0, 0)
# dev.stop_motor()

# sleep(10)

# dev.set_led(1, 100, 100, 100)
# dev.free_motor()


"""
Exit with key input
"""
while True:
    
    sleep(0.1)
    print("1")
    com_err_cnt = 0
    try:
        print("2")
        name = dev.read_device_name()  # モータ1から値を読み込む
        print('Device name: ', name)
    except ValueError:  # 値の読み込みに失敗したとき、即ち通信不良時はこちらへ遷移する
        print('COM DEAD')
        while True:  # 接続できるまで接続試行を指定回数繰り返す
            com_state = False
            print("3")
            #print('Serial connection lost. Retrying {} times'.format(com_err_cnt+1))
            dev.disconnect()  # 接続断
            try:  # 接続の再構築
                dev.connect()  # 接続を再構築
                #dev = usbcontroller.USBController(args.port,False) 
                print('Serial connection established.')
                break  # 接続に成功したのでwhileを抜ける
            except serial.serialutil.SerialException:  # 接続の再構築に失敗した場合はこちらに遷移
                com_err_cnt += 1  # 試行済回数を上げる
                print('Serial connection Failed. count: ', com_err_cnt)
                sleep(1.5)
                continue  # エラー停止にしないでwhileループの頭に戻る
        else:
            raise('SerialConnectionFailure')  # 指定回数の試行で全て失敗した場合はエラーを投げる

