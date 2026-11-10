#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 10:46:12 2018

@author: takata@innovotion.co.jp

KeiganMotor の BLE スキャン（Windows / Linux。sudo 不要）
    $python3 KM1Scan.py [スキャン秒数]
"""
import sys
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller

if len(sys.argv) >= 2:
    scan_sec = float(sys.argv[1])
else:
    scan_sec = 5.0

for km in blecontroller.scan(scan_sec):
    print(km['name'], ":", km['address'], "(RSSI", km['rssi'], ")")
