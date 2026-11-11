#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 14 10:46:12 2018

@author: takata@innovotion.co.jp

KeiganMotor の BLE スキャン（Windows / Linux。sudo 不要）
    $python3 KM1Scan.py [スキャン秒数]     (省略時 10秒)

    見つけたモーターをその場で表示し、残り時間と見つかった台数を表示する。
    Ctrl+C で途中で終了 (それまでに見つかったモーターを表示)。
    周囲に BLE 機器が多いと、モーターは数秒に1回しか受信できないことがあるため、
    見つからない場合はスキャン秒数を長くして下さい。
"""
import sys
import pathlib
import threading
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller

scan_sec = float(sys.argv[1]) if len(sys.argv) >= 2 else 10.0

print_lock = threading.Lock()
found = []
result = None


def status(remaining):
    return "\r  scanning... {:4.1f} sec left, {} found ".format(max(remaining, 0.0), len(found))


def on_found(km):
    # バックグラウンドのスレッドから呼ばれる。進捗の行を消してから表示する
    with print_lock:
        found.append(km)
        sys.stdout.write("\r\033[2K  [{:4.1f}s] found {} : {} (RSSI {})\n".format(
            km['elapsed'], km['name'], km['address'], km['rssi']))
        sys.stdout.write(status(scan_sec - km['elapsed']))
        sys.stdout.flush()


def run_scan():
    global result
    result = blecontroller.scan(scan_sec, on_found=on_found)


if sys.platform == 'win32':
    import os
    os.system('')  # Windows のコンソールでエスケープシーケンスを有効にする

print("Scanning KeiganMotors for {:.0f} sec (Ctrl+C to stop)".format(scan_sec))
t0 = time.time()
th = threading.Thread(target=run_scan, daemon=True)
th.start()
try:
    while th.is_alive():
        with print_lock:
            sys.stdout.write(status(scan_sec - (time.time() - t0)))
            sys.stdout.flush()
        th.join(0.2)
    interrupted = False
except KeyboardInterrupt:
    interrupted = True

with print_lock:
    sys.stdout.write("\r\033[2K")
    motors = result if result is not None else sorted(found, key=lambda x: -x['rssi'])
    print("{} {} KeiganMotor(s) found{}".format("Stopped." if interrupted else "Done.", len(motors),
                                               "" if motors else " (try a longer scan: KM1Scan.py 20)"))
    for km in motors:
        print("  {} : {} (RSSI {})".format(km['name'], km['address'], km['rssi']))
