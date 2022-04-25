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



class KeiganMotor():
    def __init__(self):
        # measurement_method: コールバック関数を設定する場合の観測方法 
        measurement_method = "callback"

        # measurement_method: read_motor_measurement関数を使用する場合の観測方法 
        # measurement_method = "read"

        self.dev=usbcontroller.USBController(select_port(), baud=current_baud_rate())
        self.motor_measurement_start = time.perf_counter()

        self.dev.preset_position(0)        
        self.motor_measurement_count = 0
        self.before_motor_angle = 0
        
        # ビットフラグ 0x40 でモーターの時刻送信を有効化 ※ モーターFW ver 2.62以降対応
        self.dev.set_motor_measurement_settings(5)   

        self.dev.set_curve_type(0)
        self.dev.set_speed_i(0)
        self.dev.enable_action()
        self.dev.run_at_velocity(1)

        # コールバックを使う（自動通知：有効）
        if measurement_method == "callback":
            print("callback registered")
            self.dev.on_motor_measurement_value_cb = self.on_motor_measurement_cb
        # コールバックを使わず、プログラムから読み出す（自動通知：無効）
        elif measurement_method == "read":
            self.dev.disable_continual_motor_measurement()
            while True:
                try:
                    if measurement_method == "read":
                        self.motor_measurement()
                    time.sleep(0.002)
                except KeyboardInterrupt:
                    print("Break")
                    break

        time.sleep(100) # 100秒待つ



    def motor_measurement(self):
        # 観測値が更新されるまでの時間を計測
        measurement = self.dev.read_motor_measurement()
        self.angle = measurement["position"]
        print(self.motor_measurement_count, time.perf_counter(), measurement["motor_time"], self.angle)
        if self.angle != self.before_motor_angle:
            measurement_time = time.perf_counter() - self.motor_measurement_start
            print('measurement_time: {}'.format(measurement_time))
            print("angle: {}".format(self.angle))
            self.motor_measurement_start = time.perf_counter()
            self.before_motor_angle = self.angle
    
    def on_motor_measurement_cb(self, measurement):
        # 100回分の観測周期の平均値の計測
        self.angle = measurement["position"]
        # print(measurement)
        print(self.motor_measurement_count, time.perf_counter(), measurement["motor_time"], self.angle)
        # if self.motor_measurement_count == 100:
        #     measure_time = time.time() - self.motor_measurement_start
        #     print("measurement_time: {}".format(measure_time/100))
        #     self.motor_measurement_start = time.time()
        #     self.motor_measurement_count=0
        self.motor_measurement_count=self.motor_measurement_count+1

if __name__ == '__main__':
    km = KeiganMotor()
    