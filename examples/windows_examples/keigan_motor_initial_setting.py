#!/usr/bin/env python3
# coding:utf-8
import argparse
import sys
import pathlib
import msvcrt
import serial.tools.list_ports
from time import sleep
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../../') # give 1st priority to the directory where pykeigan exists

from pykeigan import utils
from pykeigan import usbcontroller

#  '0: 115200'
#  '1: 230400'
#  '2: 250000'
#  '3: 460800'
#  '4: 921600'
#  '5: 1000000 (1M)'

baud_list = [115200, 230400, 250000, 460800, 921600, 1000000]

def current_baud_rate():
    print('Select current baud rate (bps) of KeiganMotor side')
    print("0: 115200, 1: 230400, 2: 250000, 3: 460800, 4: 921600, 5: 1000000 (1M)")
    print("Default is 0: 115200")
    print('- Enter the port number (0~5)')

    baud_num = int(input())
    
    if baud_num > 5 or baud_num < 0:
        baud_num = 0

    baud_rate = baud_list[baud_num]
    
    return baud_rate


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

dev = usbcontroller.USBController(select_port(), baud=current_baud_rate())

#  '0: 115200'
#  '1: 230400'
#  '2: 250000'
#  '3: 460800'
#  '4: 921600'
#  '5: 1000000 (1M)'

#  '0: 115200'
#  '1: 230400'
#  '2: 250000'
#  '3: 460800'
#  '4: 921600'
#  '5: 1000000 (1M)'
# 設定したいボーレートに対応する整数を入れてください
dev.set_baud_rate(5) #5: 1Mbps

# 0:      2 [ms]
# 1:      5 [ms]
# 2:     10 [ms]
# 3:     20 [ms]
# 4:     50 [ms]
# 5:    100 [ms]
# 6:    200 [ms]
# 7:    500 [ms]
# 8:   1000 [ms]
# 9:   2000 [ms]
# 10:  5000 [ms]
# 11: 10000 [ms]
# 設定したい測定値送信間隔に対応する整数を入れてください
dev.set_motor_measurement_interval(0)
dev.set_led(1, 255, 0, 0)
dev.save_all_registers()
print("dev.save_all_registers()")
time.sleep(2)
dev.set_led(1, 255, 255, 0)
dev.reboot()