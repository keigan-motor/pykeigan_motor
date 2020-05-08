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

# isGo means on the way, !isGo means on the way back.
isGo = False

##ログ情報callback
def on_motor_log_cb(log):
    global isGo
    print('log {} '.format(log))

    if log['error_codes']=='KM_SUCCESS':   
        print('Command Success') 
    elif log['error_codes']=='KM_SUCCESS_ARRIVAL':
        print('Position Arrival Success') 
        if isGo:
            print('Go back to Zero') 
            dev.move_to_pos(utils.deg2rad(0))
            isGo = False
        else:
            print('Go to the target') 
            dev.move_to_pos(utils.deg2rad(1080))
            isGo = True


##モーター回転情報callback
def on_motor_measurement_cb(measurement):
    #print("\033[2;2H\033[2K", end="")
    print("\r"+'measurement {} '.format(measurement), end="") #, end="", flush=True)
    #print("\033[20;2H", end="",flush=True)

dev=usbcontroller.USBController(select_port())
dev.on_motor_log_cb = on_motor_log_cb
#dev.on_motor_measurement_value_cb = on_motor_measurement_cb
dev.enable_action() 
dev.set_speed(utils.rpm2rad_per_sec(200))
dev.move_to_pos(utils.deg2rad(1080))
isGo = True

"""
Exit with key input
"""
while True:
    sleep(0.1)
