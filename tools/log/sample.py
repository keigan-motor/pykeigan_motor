# -*- coding: utf-8 -*-
import time

import log

import argparse
import sys
import pathlib
from time import sleep


current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import usbcontroller

parser = argparse.ArgumentParser(description='モーターに接続し、各種情報の取得')
parser.add_argument('port',metavar='PORT',default='/dev/ttyUSB0',nargs='?',help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0)')
args = parser.parse_args()

# ----------------------------------------------- User callback / ユーザーコールバック ------------------------------------------------------------------------------
# In case any of the below callback is used in main program, ALL needed callback log has to be added manually (please call additionalLog(msg) function)
# メインプログラムが以下のいずれかのコールバック使う場合、コールバックからの必要なログを全てのマニュアルで追加必要  （additionalLog(msg)関数使ってください）
def on_motor_log_cb(log):
    print('on_motor_log_cb used in main program')
    print('\33[34m', '[Main] log {} '.format(log), '\33[0m')
    # >>>>>> add additional message to logging / ログに追加メーセージ書き出し >>>>>>
    motor_log.additionalLog("log: "+str(log))

def on_motor_connection_error_cb(log):
    print('on_motor_connection_error_cb used in main program')
    print('\33[34m', '[Main] connection error {} '.format(log), '\33[0m')
    # >>>>>> add additional message to logging / ログに追加メーセージ書き出し >>>>>>
    motor_log.additionalLog("connection error: "+str(log))

def on_motor_reconnection_cb(log):
    print('on_motor_reconnection_cb used in main program')
    print('\33[34m', '[Main] reconnection {} '.format(log), '\33[0m')
    # >>>>>> add additional message to logging / ログに追加メーセージ書き出し >>>>>>
    motor_log.additionalLog("reconnection: "+str(log))

# -----------------------------------------------------------------------------------------------------------------------------

#接続
dev=usbcontroller.USBController(args.port,False)

# >>>>>> motor log >>>>>>
# Please initiate MotorLog after setting all initiate parameter of motor (dev).
# モーター（dev）の最初設定の後に MotorLogを作成してください
motor_log = log.MotorLog(dev)

# >>>>>> motor log (callback is used in main program / メインプログラムがコールバック使う) >>>>>>
# User callback / ユーザーコールバック
#dev.on_motor_log_cb=on_motor_log_cb
#dev.on_motor_connection_error_cb=on_motor_connection_error_cb
#dev.on_motor_reconnection_cb=on_motor_reconnection_cb
# Please initiate MotorLog after setting all initiate parameter of motor (dev).
# モーター（dev）の最初設定の後に MotorLogを作成してください
#motor_log = log.MotorLog(dev, 'Not_overwrite_cb', 1, False)

# ---------------------------------------------- User function / ユーザー関数 -------------------------------------------------------------------------------
def motorMove():
    try:
        print('\33[34m', "[Motor] move call", '\33[0m')
        dev.set_led(2, 255, 255, 0)
        sleep(3)
        # >>>>>> pause logging / ログ一時停止 >>>>>>
        motor_log.pauseLogging()
        sleep(2)
        # >>>>>> resume logging / ログ再開 >>>>>>
        motor_log.resumeLogging()

        # >>>>>> add additional message to logging / ログに追加メーセージ書き出し >>>>>>
        motor_log.additionalLog("Forward")
        print('\33[34m', "[Motor] start moving forward", '\33[0m')
        dev.enable_action()
        dev.set_speed(1.0)
        dev.run_forward()
        sleep(10)

        # >>>>>> add additional message to logging / ログに追加メーセージ書き出し >>>>>>
        motor_log.additionalLog("Backward")
        print('\33[34m', "[Motor] moving backward", '\33[0m')
        dev.run_reverse()
        sleep(10)

        dev.disable_action()
        print('\33[34m', "[Motor] end", '\33[0m')
        time.sleep(2)

    except Exception:
        print('\33[34m', "[Motor] end by interrupt", '\33[0m')
        sys.exit(-1)
    finally:
        # >>>>>> stop logging / ログ終了 >>>>>>
        motor_log.stopLogging()
# ----------------------------------------------------------------------------------------------------------------------------- #

# >>>>>> start logging motor data / モーターデータログ開始 >>>>>>
motor_log.startLogging()

# start motor control (User function) / モーターデータ操作開始（ユーザーの関数）
motorMove()








