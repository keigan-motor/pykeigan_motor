# -*- coding: utf-8 -*-
import time
from pykeigan_motor import blecontroller
#BLEController
dev=blecontroller.BLEController("FB:78:30:D3:7C:2F")
dev.enable_action()
dev.set_speed(1.0)
dev.run_forward()

while True:
    inp=input('Stop with Any key >>')
    if inp !=None:break