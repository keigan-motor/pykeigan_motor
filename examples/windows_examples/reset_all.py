import msvcrt
from time import sleep
import argparse
import sys
import pathlib

import serial
import serial.tools.list_ports

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../../') # give 1st priority to the directory where pykeigan exists

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

# Select port connecting to KeiganMotor
port = select_port()
dev = usbcontroller.USBController(port)


if __name__ == '__main__':
    try:
        while True:
            sleep(0.01)
            if msvcrt.kbhit():
                c = msvcrt.getwch()
                print(c)

                if c == 'r':
                    # rpm -> radian/sec
                    dev.reset_all_registers()
                    dev.save_all_registers()

    except KeyboardInterrupt:
        if dev:
            dev.disable_action()
        print('Ctrl-C')
