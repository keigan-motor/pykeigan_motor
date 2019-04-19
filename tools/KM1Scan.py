#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 10:46:12 2018

@author: takata@innovotion.co.jp
"""
from __future__ import print_function
from bluepy.btle import Scanner
import sys
if len(sys.argv)>=2:
    scan_sec=float(sys.argv[1])
else:
    scan_sec=5.0
scanner=Scanner()
devices=scanner.scan(scan_sec)
KM1_list=[]
for dev in devices:
    for (adtype, desc, value) in dev.getScanData():
        if desc=="Complete Local Name" and "KM-1" in value:
            print(value,":",dev.addr)
