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
sys.path.insert(0, str(current_dir) + '/../../') # give priority to the directory where pykeigan is

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


def read_pid_settings(motor):
    print('\rread_pid_settings')
    qCurrentP = motor.read_qcurrent_p()
    qCurrentI = motor.read_qcurrent_i()
    qCurrentD = motor.read_qcurrent_d()
    speedP = motor.read_speed_p()
    speedI = motor.read_speed_i()
    speedD = motor.read_speed_d()
    positionP = motor.read_position_p()
    positionI = motor.read_position_i()
    positionD = motor.read_position_d()
    threshold = motor.read_pos_control_threshold()
    print('-------')
    print('qCurrent gain P: ',qCurrentP)
    print('qCurrent gain I: ',qCurrentI)
    print('qCurrent gain D: ',qCurrentD)
    print('speed    gain P: ',speedP)
    print('speed    gain I: ',speedI)
    print('speed    gain D: ',speedD)
    print('position gain P: ',positionP)
    print('position gain I: ',positionI)
    print('position gain D: ',positionD)
    print('position PID threshold [rad]: ', threshold)
    print('position PID threshold [deg]: ', utils.rad2deg(threshold))
    print('-------')

def read_device_name(motor):
    name = motor.read_device_name()
    print('Device Name: ', name)


if __name__ == '__main__':
    dev = usbcontroller.USBController(select_port())
    read_device_name(dev)
    read_pid_settings(dev)
    try:
        while True:
            sleep(0.01)
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                print(c)

                if c == 'r':
                    read_pid_settings(dev)
                elif c == 'n':
                    read_device_name(dev)
                elif c == 's':
                    dev.stop_motor()

    except KeyboardInterrupt:
        if dev:
            dev.disable_action()
        print('Ctrl-C')