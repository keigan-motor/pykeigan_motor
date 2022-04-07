# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
import argparse
import signal
import sys
import os
import math
import pathlib
from time import sleep

from concurrent.futures import ThreadPoolExecutor

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller
from pykeigan import utils

parser = argparse.ArgumentParser(description='モーター動作　ティーチング記録・再生')
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

REC_NUMBER=1

"""
----------------------
モーター接続し、各種情報の取得
----------------------
"""

##ログ情報callback
def on_motor_log_cb(log):
    if log['error_codes']!='KM_SUCCESS':
        print('log {} '.format(log))

#接続
dev=usbcontroller.USBController(args.port,False)
dev.on_motor_log_cb=on_motor_log_cb

"""
----------------------
モーター動作　ティーチング記録・再生
----------------------
"""
def rec_and_play_teaching(index):
    dev.disable_action()
    dev.stop_teaching_motion()
    dev.erase_motion(index)#消してないとエラー無しで録画出来ない
    sleep(1)#erase_motionの実行完了までのインターバルが必要。約500ms
    dev.set_led(2, 255, 255, 0)
    dev.start_teaching_motion(index,5000) # インデックス,記録時間
    print("")
    for i in range(5):
        print("\033[1G\033[2K","モーターを動かして下さい。 残り:",5-i," sec")
        sys.stdout.flush()
        sleep(1)
    dev.stop_teaching_motion()
    print("")
    dev.set_led(1, 100, 100, 100)
    sleep(2)
    play_teaching(index)
    return True

def play_teaching(index):
    print("\033[1G\033[2K","ティーチング再生中")
    sys.stdout.flush()
    dev.set_led(2, 0, 255, 255)
    dev.stop_playback_motion()
    dev.enable_action()
    dev.start_playback_motion(index,1,1)
    sleep(5)
    print("\033[1G\033[2K", "ティーチング完了")
    dev.set_led(1, 100, 100, 100)
    return True

def read_comp_cb(index,motion_value):
    print("read motion data "+str(index)+" >>>>>>>>>>>>>>")
    print(motion_value)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

def read_motion_exec(index):
    dev.read_motion(index,read_comp_cb)

def write_motion_position_exec(index):
    print("Write Test motion>>>>" )
    dev.enable_action()
    dev.erase_motion(index)
    sleep(2)
    dev.prepare_teaching_motion(index,0)
    sleep(1)
    amp = math.pi/2 #deg
    len=500
    for i in range(len):
        pos=amp*math.cos(2*math.pi*i/500)
        dev.write_motion_position(pos)
        sleep(0.02)
        print('\r Write Test motion>>>>{0}  {1}/{2}'.format(pos,i,len))
    pass
    sleep(0.5)
    dev.stop_teaching_motion()
    sleep(1)
    print("")
    print("Write Test motion>>>>comp")
    play_teaching(REC_NUMBER)

"""
Exit with key input
"""


sleep(0.5)
while True:
    print("---------------------------------------")
    if sys.version_info<(3,0):
        inp = raw_input('Command input > Rec:[r] Replay:[p]  Write Test motion:[w] Read motion:[m] Exit:[Other key] >>')
    else:
        inp = input('Command input > Rec:[r] Replay:[p]  Write Test motion:[w] Read motion:[m] Exit:[Other key] >>')
    if inp == 'r':
        rec_and_play_teaching(REC_NUMBER)
    elif inp == 'p':
        play_teaching(REC_NUMBER)
    elif inp == 'w':
        write_motion_position_exec(REC_NUMBER)
    elif inp == 'm':
        read_motion_exec(REC_NUMBER)
    elif inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.disconnect()
        break
