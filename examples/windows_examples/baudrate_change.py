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

from pykeigan import usbcontroller
from pykeigan import utils

"""
----------------------
Change Baud Rate 
You can check new baud rate by "baudrate_run.py" after executing this sample 
Set the current baud rate to current_baud
ボーレートの変更
本サンプル実行後、"baudrate_run.py" で動作確認が可能
以下の current_baud に現在のボーレートを入れること
----------------------

"""
current_baud = 115200

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
    print('Select baud rate to set')
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


dev=usbcontroller.USBController(select_port(),baud=current_baud) # Set the current baudrate to communicate
dev.set_baud_rate(baud_rate_setting()) #5: 1Mbps
dev.save_all_registers()
sleep(1)
dev.reboot()



