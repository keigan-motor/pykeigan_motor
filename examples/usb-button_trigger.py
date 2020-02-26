# -*- coding: utf-8 -*-
"""
Created on Jan 23 2020
@author: tokuda@keigan.co.jp
"""

import sys
import pathlib

from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append( str(current_dir) + '/../' )

from pykeigan import usbcontroller
from pykeigan import utils

port1='/dev/ttyUSB0'

"""
----------------------
モーター側のイベントを受信したときに呼ばれるコールバック
----------------------
    event_type: 'button' はボタン押下を意味する
    その場合、number: は押したボタンの番号（左から1/2/3）
"""
def on_motor_event_cb(event):
    print("\033[3;2H\033[2K", end="")
    print('event {} '.format(event), end="", flush=True)
    if event['event_type'] == 'button':
        print('button!!')
        if event['number'] == 2:
            print('2!!')
            motor1.disable_action()
        elif event['number'] == 3:
            print('3!!')
            motor1.enable_action()
            motor1.run_at_velocity(utils.rpm2rad_per_sec(5)) 
        else:
            print(event['number'])



print("---------------------------------------")
print("Button Trigger Test Start!")

# KeiganMotor のデバイスアドレス（ポート）を指定し、初期化を行う
motor1=usbcontroller.USBController(port1,False)
motor1.on_motor_event_cb = on_motor_event_cb
motor1.set_button_setting(30) # Set buttons as Parent mode
motor1.enable_action()
motor1.run_at_velocity(utils.rpm2rad_per_sec(5))


"""
Exit with key input
"""
try:
    while True:
        sleep(0.1)

except KeyboardInterrupt:
    motor1.set_led(1, 255, 0, 0)
    motor1.disconnect()
