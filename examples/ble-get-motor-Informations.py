# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""


import argparse
import sys
import os
import pathlib
from time import sleep
from concurrent.futures import ThreadPoolExecutor

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller
from ble_select import select_motor, connect_motor

"""
----------------------
モーターに接続し、各種情報の取得
----------------------
    $python3 ble-get-motor-Informations.py [MACアドレス]   (省略時はスキャン。参照 ble-simple-connection.py)
"""
parser = argparse.ArgumentParser(description="BLE モーター情報の取得")
parser.add_argument('address', metavar='ADDRESS', nargs='?', help='モーターのMACアドレス (省略時はスキャン)')
args = parser.parse_args()

if os.name == 'nt':
    os.system('')  # Windows のコンソールでエスケープシーケンスを有効にする

running = True

def show(row, label, read):
    # 読み出しに失敗しても (一時的な電波の悪化など) 表示を止めずに次の周期で再試行する
    try:
        text = '{} {} '.format(label, read())
    except Exception as e:
        text = '{} (read failed: {!r}) '.format(label, e)
    print("\033[{};2H\033[2K".format(row))
    sys.stdout.flush()
    print(text)
    sys.stdout.flush()

def get_motor_informations():
    while running:
        if dev:
            show(3, 'status', dev.read_status)
            show(8, 'measurement', dev.read_motor_measurement)
            show(12, 'imu_measurement', dev.read_imu_measurement)
        sleep(0.5)

#接続
address = args.address or select_motor()  # 省略時はスキャンして選択 (1台なら自動)
if address is None:
    sys.exit()

dev=connect_motor(address)
dev.set_led(2,255,255,0)
dev.enable_continual_motor_measurement()
dev.enable_continual_imu_measurement()#IMUは通知をOnにする必要がある
sleep(0.5)

#一定間隔で取得
executor = ThreadPoolExecutor(max_workers=2)
res = executor.submit(get_motor_informations)


"""
Exit with key input
"""
os.system('cls' if os.name == 'nt' else 'clear')
for i in range(20):
    print("　　　　　　　")
print("\033[17;2H")
print("---------------------------------------")
print("\033[3;2H\033[2K")
sys.stdout.flush()
sleep(0.5)
print("\033[18;2H")
sys.stdout.flush()
print("---------------------------------------")
input('Exit:[key input] >>')
running = False
res.result()
dev.set_led(1, 100, 100, 100)
dev.disable_continual_motor_measurement()
dev.disable_continual_imu_measurement()
dev.disconnect()
