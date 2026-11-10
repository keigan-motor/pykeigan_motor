# -*- coding: utf-8 -*-
"""
----------------------
複数のモーターの同期位置制御
----------------------
    接続したすべてのモーターを、同じ角度の列 (TARGETS_DEG) へ順番に移動させる。
    全モーターが目標に到着してから、次の目標へ同時に動き出す。

    モーターの原点は書き換えず、起動時の各モーターの位置を 0° とする (プログラム側のオフセット)。
    REVERSE_ODD=True にすると、奇数番目のモーターは逆向きに動く。

        $python3 ble-multi-position-control.py
        $python3 ble-multi-position-control.py xx:xx:xx:xx:xx:xx yy:yy:yy:yy:yy:yy
"""
import argparse
import sys
import pathlib
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from ble_multi import get_addresses, connect_motors, run_all, disconnect_all
from pykeigan.utils import deg2rad, rad2deg, rpm2rad_per_sec

# ============================================================
# 設定
# ============================================================
SPEED_RPM = 30.0                                  # 移動速度 [rpm]
TARGETS_DEG = [90.0, 0.0, -90.0, 0.0, 360.0, 0.0]   # 移動先 (起動時の位置からの角度) [deg]
REVERSE_ODD = False                               # True: 奇数番目のモーターを逆向きに動かす
TOLERANCE_DEG = 1.0                               # 到着とみなす誤差 [deg]
ARRIVAL_TIMEOUT_SEC = 20.0                        # これ以上かかったら到着待ちをあきらめる [秒]

parser = argparse.ArgumentParser(description="BLE 複数台の同期位置制御")
parser.add_argument('addresses', metavar='ADDRESS', nargs='*', help='モーターのMACアドレス (複数可。省略時はスキャン)')
args = parser.parse_args()

motors = connect_motors(get_addresses(args.addresses))
if not motors:
    sys.exit("接続できたモーターがありません")

run_all(motors, lambda m: m.enable_continual_motor_measurement())
time.sleep(0.5)

# 起動時の位置を各モーターの 0° とする
origins = run_all(motors, lambda m: m.read_motor_measurement()['position'])
directions = [-1 if (REVERSE_ODD and i % 2 == 1) else 1 for i in range(len(motors))]
for i, m in enumerate(motors):
    print("[{}] {} start position {:.2f} deg".format(i, m.name, rad2deg(origins[i])))


def prepare(m):
    m.enable_action()  # 安全装置。初めてモーターを動作させる場合に必ず必要。
    m.set_speed(rpm2rad_per_sec(SPEED_RPM))
    m.set_curve_type(1)  # 台形加減速


def wait_arrival(targets_rad):
    """全モーターが目標位置に到着するまで待つ。到着したら True、タイムアウトしたら False"""
    deadline = time.time() + ARRIVAL_TIMEOUT_SEC
    tol = deg2rad(TOLERANCE_DEG)
    while time.time() < deadline:
        positions = [m.read_motor_measurement()['position'] for m in motors]
        if all(abs(p - t) < tol for p, t in zip(positions, targets_rad)):
            return True
        time.sleep(0.1)
    for i, (p, t) in enumerate(zip(positions, targets_rad)):
        if abs(p - t) >= tol:
            print("  [{}] {} not arrived: {:.2f} deg (target {:.2f})".format(
                i, motors[i].name, rad2deg(p - origins[i]) * directions[i], rad2deg(t - origins[i]) * directions[i]))
    return False


try:
    run_all(motors, prepare)
    for target_deg in TARGETS_DEG:
        targets_rad = [origins[i] + directions[i] * deg2rad(target_deg) for i in range(len(motors))]
        print("move to {:.1f} deg".format(target_deg))
        t0 = time.time()
        run_all(motors, lambda m: m.move_to_pos(targets_rad[motors.index(m)]))  # 全モーター同時に指令
        if wait_arrival(targets_rad):
            print("  all arrived ({:.1f} sec)".format(time.time() - t0))
        time.sleep(0.5)
except KeyboardInterrupt:
    print("interrupted")
finally:
    run_all(motors, lambda m: m.disable_action())
    run_all(motors, lambda m: m.disable_continual_motor_measurement())
    disconnect_all(motors)
