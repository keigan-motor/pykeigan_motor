# -*- coding: utf-8 -*-
from pykeigan_motor import usbcontroller
dev=usbcontroller.USBController('/dev/ttyUSB0')
#info::2.0よりコマンドは全て新コマンドに刷新
dev.enable_action()
dev.set_speed(1.0)
dev.run_forward()


while True:
    inp=input('Stop with Any key >>')
    if inp !=None:
        dev.stop_motor()
