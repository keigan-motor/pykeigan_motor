# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
import signal
import sys
import os
import pathlib
from time import sleep

from concurrent.futures import ThreadPoolExecutor
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append( str(current_dir) + '/../' )

from pykeigan import usbcontroller
from pykeigan import utils


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
dev=usbcontroller.USBController('/dev/ttyUSB0',False)
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
        print("\033[1G\033[2K","モーターを動かして下さい。 残り:",5-i," sec", end="", flush=True)
        sleep(1)
    dev.stop_teaching_motion()
    print("")
    dev.set_led(1, 100, 100, 100)
    sleep(2)
    play_teaching(0)
    return True

def play_teaching(index):
    print("\033[1G\033[2K","ティーチング再生中",end="", flush=True)
    dev.set_led(2, 0, 255, 255)
    dev.stop_playback_motion()
    dev.enable_action()
    dev.start_playback_motion(index,1,1)
    sleep(5)
    print("\033[1G\033[2K", "ティーチング完了")
    dev.set_led(1, 100, 100, 100)
    return True

"""
Exit with key input
"""

sleep(0.5)
while True:
    print("---------------------------------------")
    inp = input('Command input > Rec:[r] Replay:[p] Exit:[Other key] >>')
    if inp == 'r':
        rec_and_play_teaching(0)
    elif inp == 'p':
        play_teaching(0)
    elif inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_action()
        dev.disconnect()
        break