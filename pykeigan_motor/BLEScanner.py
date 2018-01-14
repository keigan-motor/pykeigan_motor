#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 10:46:12 2018

@author: takata@innovotion.co.jp
"""

from bluepy.btle import Scanner, DefaultDelegate

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        
class KM1Scanner:
    def __init__(self):
        self.scanner=Scanner().withDelegate(ScanDelegate())
        self.devices=[]
        self.KM1_list=[]
        
    def scan(self,scan_sec=10):
        self.devices=self.scanner.scan(scan_sec)
        self.KM1_list=[]
        for dev in self.devices:
            for (adtype, desc, value) in dev.getScanData():
                if desc=="Complete Local Name" and "KM-1" in value:
                    self.KM1_list.append((value,dev.addr))
        return self.KM1_list