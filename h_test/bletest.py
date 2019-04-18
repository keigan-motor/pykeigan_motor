# -*- coding: utf-8 -*-
import time
from pykeigan import blecontroller
#BLEController
dev=blecontroller.BLEController("ee:f4:36:61:81:3f")
dev.enable_action()
dev.set_speed(2.0)
dev.run_reverse()

#---------------------------
#    テスト
#---------------------------

print('#######テスト開始######')
print('##回転情報')
start=time.time()
while time.time()-start<3.0:
    print(dev.read_motor_measurement())

#---------------------------
#   トルク設定
#---------------------------
defTorque=dev.read_max_torque()
dev.set_max_torque(0.1)
chTorque=dev.read_max_torque()
print('##トルク設定 dev.read_maxTorque:{} --> {}'.format(defTorque,chTorque))
time.sleep(3)
print('##トルク復帰>3.0')
dev.set_max_torque(10.0)
time.sleep(3)


while True:
    inp=input('Command: t, d, or c >>')
    if inp == 't':
        dev.set_max_torque(0.2)
    elif inp == 'd':#情報の取得
        print('measurement {} '.format(dev.read_motor_measurement()))
        print('read_device_info : {} '.format(dev.read_device_info()))
        print('read_device_name : {} '.format(dev.read_device_name()))
        print('read_maxTorque : {} '.format(dev.read_max_torque()))
    elif inp == 'c':#初期状態に戻す
        dev.set_max_torque(10.0)
    elif inp !=None:
        dev.disconnect()
        break
