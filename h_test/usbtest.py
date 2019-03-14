# -*- coding: utf-8 -*-
import time
from pykeigan_motor import usbcontroller

##info::モーター回転情報受信callback
def on_motor_measurement_value_cb(measurement):
    print('measurement {} '.format(measurement))

##モーター接続処理
dev=usbcontroller.USBController('/dev/ttyUSB0')


#USB接続でモーター回転情報(on_motor_measurement_value_cb)を受信する場合予めdev.set_interfaceでUSBに経路を指定する必要がある
#dev.set_interface(dev.interface_type['USB'] + dev.interface_type['BTN'])#info:USB通知モードはインスタンス生成時に自動実行するようにコンストラクタに設定済み
#dev.on_motor_measurement_value_cb=on_motor_measurement_value_cb
#dev.start_auto_serial_reading()#回転受信の開始
#motor.saveAllRegisters() #info: USBモードは使用前に都度設定(保存をしない場合、再起動でbleに戻る)

#info::2.0よりコマンドは全て新コマンドに刷新
dev.enable_action()
dev.set_speed(1.0)
dev.run_forward()

#---------------------------
#    テスト
#---------------------------

print('#######テスト開始######')
print('##回転情報')

#info::USB接続でモーター回転情報(on_motor_measurement_value_cb)を受信する場合予めdev.set_interfaceでUSBに経路を指定する必要がある
#info::そして、dev.set_interfaceはインスタンス生成時に自動実行するようにコンストラクタに設定(変更)済み
dev.on_motor_measurement_value_cb=on_motor_measurement_value_cb
dev.start_auto_serial_reading()#回転受信の開始
time.sleep(3)
dev.finish_auto_serial_reading()
time.sleep(0.5)

#---------------------------
#   トルク設定
#---------------------------
defTorque=dev.read_maxTorque()
dev.set_max_torque(0.1)
chTorque=dev.read_maxTorque()
print('##トルク設定 dev.read_maxTorque:{} --> {}'.format(defTorque,chTorque))
time.sleep(3)
print('##トルク復帰>3.0')
dev.set_max_torque(10.0)
time.sleep(3)


############
# import threading
# ##############遅延実行関数用#####################
# def delay(delay=0.):
#     """
#     Decorator delaying the execution of a function for a while.
#     """
#     def wrap(f):
#         @wraps(f)
#         def delayed(*args, **kwargs):
#             timer = threading.Timer(delay, f, args=args, kwargs=kwargs)
#             timer.start()
#         return delayed
#     return wrap
# class Timer():
#     toClearTimer = False
#     def setTimeout(self, fn, time):
#         isInvokationCancelled = False
#         @delay(time)
#         def some_fn():
#                 if (self.toClearTimer is False):
#                         fn()
#                 else:
#                     print('Invokation is cleared!')
#         some_fn()
#         return isInvokationCancelled
#     def setClearTimer(self):
#         self.toClearTimer = True
# ########################################
# timer = Timer()

# print('#######テスト開始######')
#
# def test1():
#     print('##回転情報')
#     dev.on_motor_measurement_value_cb=on_motor_measurement_value_cb
#     dev.start_auto_serial_reading()
#     timer.setTimeout(test2, 3.0)
#
# def test2():
#     print('##トルク設定> 0.1')
#     dev.set_max_torque(0.1)
#     timer.setTimeout(test3, 3.0)
#
# def test3():
#     print('##トルク復帰>3.0')
#     dev.set_max_torque(3.0)
#     timer.setTimeout(test4, 3.0)
#
# def test4():
#     print('##トルク情報')
#     print('read_maxTorque :'.format(dev.read_maxTorque()))  # info:エラー
#     timer.setTimeout(test5, 3.0)
#
# def test5():
#     print('##END')
#
# ##
# #test1()

#
#
#
# while True:
#     inp=input('Stop with Any key >>')
#     if inp=='r':#回転情報の手動取得
#         vv=dev.read_motor_measurement()
#         print('measurement {} '.format(vv))
#     elif inp == 't':
#         dev.set_max_torque(0.2)
#     elif inp == 'd':#情報の取得
#         print('read_device_info :'.format(dev.read_device_info(1)))
#         print('read_device_name :'.format(dev.read_device_name()))
#         print('read_maxTorque :'.format(dev.read_maxTorque()))
#     elif inp == 'c':#初期状態に戻す
#         dev.set_max_torque(3)
#     elif inp !=None:
#         dev.stop_motor()
