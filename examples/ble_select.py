# -*- coding: utf-8 -*-
"""
BLE サンプル共通: KeiganMotor をスキャンして、接続するモーターを選択する
"""
import sys
import pathlib

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../') # give 1st priority to the directory where pykeigan exists

from pykeigan import blecontroller



def _print_found(km):
    # スキャン中に見つけたモーターをその場で表示する (バックグラウンドのスレッドから呼ばれる)
    print("  ({:4.1f}s) found {}".format(km['elapsed'], km['name']), flush=True)

def select_motor(scan_sec=5.0, auto_select_single=True):
    """
    スキャンして見つかったモーターを一覧表示し、番号で選択させる。
    1台だけ見つかった場合は auto_select_single=True ならそのまま選ぶ。
    選択したモーターの MAC アドレスを返す (中止した場合は None)。
        番号: 接続   r: 再スキャン   q: 中止
    """
    while True:
        print("During scanning at", scan_sec, "sec ...")
        found = blecontroller.scan(scan_sec, on_found=_print_found)
        if found and len(found) == 1 and auto_select_single:
            km = found[0]
            print("connect to", km['name'], ":", km['address'])
            return km['address']
        if not found:
            print("KeiganMotor が見つかりませんでした")
        for i, km in enumerate(found):
            print("  [{}] {} : {} (RSSI {})".format(i, km['name'], km['address'], km['rssi']))
        inp = input('Connect:[number] Rescan:[r] Quit:[q] >>').strip()
        if inp == 'q':
            return None
        if inp.isdigit() and int(inp) < len(found):
            km = found[int(inp)]
            print("connect to", km['name'], ":", km['address'])
            return km['address']
