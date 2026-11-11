# -*- coding: utf-8 -*-
"""
----------------------
複数のモーターの追従 (リーダー / フォロワー)
----------------------
    選択した 1台目をリーダー (脱力。手で回す)、2台目以降をフォロワーにする。
    リーダーを手で回すと、フォロワーが同じ角度だけ回って追従する。
    起動時の各モーターの位置を基準にするので、モーターの原点は書き換えない。

        $python3 ble-multi-follow.py                       (スキャンして選択。最初に選んだモーターがリーダー)
        $python3 ble-multi-follow.py LEADER_ADDRESS FOLLOWER_ADDRESS [FOLLOWER_ADDRESS ...]
        $python3 ble-multi-follow.py --reverse ...          (フォロワーを逆向きに回す)

    注意
        + フォロワーは最大 MAX_SPEED_RPM で動きます。周囲に物が無いことを確認して下さい。
        + リーダーの位置は BLE の notify (約10Hz) で受け取るため、少し遅れて追従します。
        + コールバックの中からはコマンドを送れないため、メインスレッドから一定周期で指令を送っています。
"""
import argparse
import sys
import pathlib
import threading
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from ble_multi import get_addresses, connect_motors, run_all, disconnect_all
from pykeigan.utils import deg2rad, rad2deg, rpm2rad_per_sec

MAX_SPEED_RPM = 60.0     # フォロワーの最高速度 [rpm]
PERIOD_SEC = 0.1         # フォロワーへ指令を送る周期 [秒]
DEADBAND_DEG = 0.5       # この角度未満の変化では指令を送らない [deg]

parser = argparse.ArgumentParser(description="BLE 複数台の追従 (1台目を手で回すと 2台目以降が追従)")
parser.add_argument('addresses', metavar='ADDRESS', nargs='*', help='MACアドレス (1つ目がリーダー。省略時はスキャン)')
parser.add_argument('--reverse', action='store_true', help='フォロワーを逆向きに回す')
args = parser.parse_args()

print("最初に選んだモーターがリーダー (手で回す側) になります")
motors = connect_motors(get_addresses(args.addresses))
if len(motors) < 2:
    disconnect_all(motors)
    sys.exit("2台以上のモーターが必要です")
leader, followers = motors[0], motors[1:]

# リーダーの最新位置 (コールバックでは保存するだけ)
leader_pos = None
pos_lock = threading.Lock()


def on_leader_measurement(v):
    global leader_pos
    with pos_lock:
        leader_pos = v['position']


leader.on_motor_measurement_value_cb = on_leader_measurement
run_all(motors, lambda m: m.enable_continual_motor_measurement())
time.sleep(0.5)

origins = run_all(motors, lambda m: m.read_motor_measurement()['position'])
leader_origin, follower_origins = origins[0], origins[1:]
sign = -1 if args.reverse else 1


def prepare_follower(m):
    m.enable_action()
    m.set_speed(rpm2rad_per_sec(MAX_SPEED_RPM))
    m.set_curve_type(1)  # 台形加減速 (目標が変わるたびに MAX_SPEED_RPM 以下で滑らかに追う)


leader.free_motor()  # リーダーは脱力して手で回せるようにする
run_all(followers, prepare_follower)
print("leader: {} / followers: {}".format(leader.name, ", ".join(m.name for m in followers)))
print("リーダーを手で回して下さい。Ctrl-C で終了")

last_sent = None
try:
    while True:
        time.sleep(PERIOD_SEC)
        with pos_lock:
            p = leader_pos
        if p is None:
            continue
        delta = p - leader_origin
        if last_sent is not None and abs(delta - last_sent) < deg2rad(DEADBAND_DEG):
            continue
        run_all(followers, lambda m: m.move_to_pos(follower_origins[followers.index(m)] + sign * delta))
        last_sent = delta
        sys.stdout.write("\rleader {:8.1f} deg ".format(rad2deg(delta)))
        sys.stdout.flush()
except KeyboardInterrupt:
    print()
finally:
    run_all(followers, lambda m: m.disable_action())
    run_all(motors, lambda m: m.disable_continual_motor_measurement())
    disconnect_all(motors)
