#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KeiganMotor シンプル位置制御サンプル（preset_position を使わない版）

モーターの原点は書き換えず、プログラム側のオフセット（OFFSET_DEG）で
「機械の 0°」を決める。

使い方:
    1. 軸を機械の 0° にしたい位置に合わせて、--measure を付けて実行する
       （現在位置を表示するだけで、モーターは動かない）
    2. 表示された「モーターの現在位置」の値を OFFSET_DEG に書き込む
    3. 以降は --measure なしで実行すると、TARGETS_DEG（機械基準の角度）へ順に移動する

    $python3 usb-offset-position-control.py /dev/ttyUSB0 --measure
    $python3 usb-offset-position-control.py /dev/ttyUSB0
    > python usb-offset-position-control.py COM3   (Windows)
"""

import argparse
import pathlib
import sys
from time import sleep

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../')  # give 1st priority to the directory where pykeigan exists

from pykeigan.usbcontroller import USBController
from pykeigan.utils import deg2rad, rad2deg, rpm2rad_per_sec

# ============================================================
# 設定（ここを書き換える）
# ============================================================
BAUD = 115200

OFFSET_DEG = 0.0            # 機械の 0° におけるモーターの位置 [deg]
SPEED_RPM = 30.0            # 移動速度 [rpm]
TARGETS_DEG = [0.0, 90.0, 180.0, 0.0]   # 移動先（機械基準の角度）[deg]
WAIT_SEC = 3.0              # 各移動の待ち時間 [秒]

# ============================================================
# 現在位置の取得（計測値コールバック）
# ============================================================
motor_position_rad = None


def on_measurement(data):
    global motor_position_rad
    motor_position_rad = data.get('position', 0.0)


# ============================================================
# 位置制御
# ============================================================
def move_to(dev, target_deg):
    """機械基準の角度 [deg] へ移動する（オフセットを加算して指令）"""
    dev.move_to_pos(deg2rad(target_deg + OFFSET_DEG))


def main():
    parser = argparse.ArgumentParser(description="オフセットを使った絶対位置移動")
    parser.add_argument('port', metavar='PORT', default='/dev/ttyUSB0', nargs='?',
                        help='モーターのデバイスファイル指定 (default:/dev/ttyUSB0, Windows の場合は COM3 など)')
    parser.add_argument('--measure', action='store_true',
                        help='現在位置を表示するだけで終了する（モーターは動かない）')
    args = parser.parse_args()

    dev = USBController(port=args.port, baud=BAUD)
    dev.on_motor_measurement_value_cb = on_measurement
    dev.enable_continual_motor_measurement()
    sleep(1.0)  # 計測値が届くまで待つ

    if motor_position_rad is None:
        dev.disconnect()
        sys.exit('モーターの計測値を取得できませんでした')

    motor_deg = rad2deg(motor_position_rad)
    print('モーターの現在位置: {:.2f} deg（この値を OFFSET_DEG に設定）'.format(motor_deg))
    print('機械基準の現在位置: {:.2f} deg'.format(motor_deg - OFFSET_DEG))

    if args.measure:
        dev.disconnect()
        return

    dev.enable_action()
    dev.set_speed(rpm2rad_per_sec(SPEED_RPM))

    for target_deg in TARGETS_DEG:
        print('移動: {:.2f} deg'.format(target_deg))
        move_to(dev, target_deg)
        sleep(WAIT_SEC)

    dev.disable_action()
    dev.disconnect()


if __name__ == '__main__':
    main()
