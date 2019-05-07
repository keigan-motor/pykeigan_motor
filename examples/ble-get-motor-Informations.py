# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""


import sys
import os
import pathlib
from time import sleep
from concurrent.futures import ThreadPoolExecutor
current_dir = pathlib.Path(__file__).resolve().parent
sys.path.append( str(current_dir) + '/../' )
from pykeigan import blecontroller

"""
----------------------
モーターに接続し、各種情報の取得
----------------------
"""

def get_motor_informations():
    while True:
        if dev:
            print("\033[3;2H\033[2K", end="",flush=True)
            print('status {} '.format(dev.read_status()),end="",flush=True)

            print("\033[8;2H\033[2K", end="",flush=True)
            print('measurement {} '.format(dev.read_motor_measurement()), end="",flush=True)

            print("\033[12;2H\033[2K", end="",flush=True)
            print('imu_measurement {} '.format(dev.read_imu_measurement()),end="",flush=True)
        sleep(0.5)

#接続
dev=blecontroller.BLEController("FB:78:30:D3:7C:2F")#モーターのMACアドレス 参照 ble-simple-connection.py
dev.set_led(2,255,255,0)
dev.enable_continual_imu_measurement()#IMUは通知をOnにする必要がある
sleep(0.5)

#一定間隔で取得
executor = ThreadPoolExecutor(max_workers=2)
res = executor.submit(get_motor_informations)


"""
Exit with key input
"""
os.system('clear')
for i in range(20):
    print("　　　　　　　")
print("\033[17;2H", end="")
print("---------------------------------------")
print("\033[3;2H\033[2K", end="",flush=True)
sleep(0.5)
while True:
    print("\033[18;2H", end="",flush=True)
    print("---------------------------------------")
    inp = input('Exit:[key input] >>')
    if inp !=None:
        dev.set_led(1, 100, 100, 100)
        dev.disable_continual_imu_measurement()
        dev.disconnect()
        break
