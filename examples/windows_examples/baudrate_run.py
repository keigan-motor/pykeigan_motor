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
sys.path.append( str(current_dir) + '/../../' )

from pykeigan import usbcontroller
from pykeigan import utils

"""
----------------------
Run after Change of Baud Rate 
You need to execute "baudrate_change.py" before executing this sample 
Choose COM port connected to KeiganMotor, and
Choose baud rate that you set by "baudrate_change.py".

ボーレート変更後の動作確認
本サンプル実行前に、"baudrate_change.py" を実行してボーレートを変更すること
COMポートと、"baudrate_change.py" で設定したボーレートを選択する
----------------------

"""
# This sample requires KM-1 firmware version more than 2.37

baud_rates = {0:"115200",1:"230400",2:"250000",3:"460800",4:"921600",5:"1000000"}

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


def baud_rate_setting():
    print('Select baud rate')
    print('--------')
    print('0: 115200')
    print('1: 230400')
    print('2: 250000')
    print('3: 460800')
    print('4: 921600')
    print('5: 1000000 (1M)')
    print('--------')
    num = int(input())
    while num < 0 or num > 5:
        print('Invalid value!')
        num = int(input())
    return num

port = select_port()
baud_rate = baud_rates[baud_rate_setting()]
dev=usbcontroller.USBController(port,baud=baud_rate)
dev.enable_action() #5: 1Mbps
dev.run_at_velocity(utils.rpm2rad_per_sec(100))

