# -*- coding: utf-8 -*-
"""
BLE 通信品質の診断

接続したモーターとの通信品質 (電波強度 RSSI・応答時間・失敗率) と周囲の電波環境
(近くの BLE 機器の数・この PC の Wi-Fi) を測定し、使用可能かどうかと改善方法を表示します。
モーターは動作しません (測定値の読み出しのみ)。

    $python3 ble-link-check.py [xx:xx:xx:xx:xx:xx] [--monitor]

--monitor を付けると、診断後に通常の通信 (測定値の読み出し) を続けながら 5 秒ごとに品質を表示します。
"""

import argparse
import sys
import pathlib
import time

current_dir = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir) + '/../')  # give 1st priority to the directory where pykeigan exists

from ble_select import select_motor, connect_motor

LEVEL_JA = {'good': '良好', 'fair': '注意 (使用できますが不安定になる可能性があります)',
            'poor': '不良 (使用は困難です)'}

ADVICE_JA = {
    'weak_signal': '電波が弱いです。PC とモーターを近づけ、間に金属・壁・人が入らないようにして下さい。',
    'interference': '電波は弱くないのに応答が遅い/失われています。電波干渉の可能性が高いです。'
                    'Wi-Fi ルーター・電子レンジ・ワイヤレスカメラ・他の Bluetooth 機器から離すか、場所を変えて下さい。',
    'wifi_2.4ghz': 'この PC は 2.4GHz の Wi-Fi を使用しており、BLE と干渉します。'
                   '有線 LAN を使って Wi-Fi をオフにするか、5GHz の Wi-Fi を使用して下さい。'
                   '(Raspberry Pi: sudo nmcli radio wifi off)',
    'crowded': '周囲に BLE 機器が多く、2.4GHz 帯が混雑しています。通信が不安定になる場合があります。',
    'reconnected': '接続のリトライまたは切断が発生しました。通信が不安定です。',
    'disconnected': '測定中に切断されました。PC とモーターを近づけて再接続して下さい。',
}


def ms(v):
    return '-' if v is None else '{:.0f} ms'.format(v * 1000)


def print_result(r):
    print('---------------------------------------')
    print('判定      :', LEVEL_JA[r['level']])
    print('RSSI      :', '-' if r['rssi'] is None else '{} dBm'.format(r['rssi']), '(接続前のアドバタイズ)')
    print('応答時間  : 中央値 {}  95% {}  最大 {}'.format(ms(r['latency_median']), ms(r['latency_p95']),
                                                     ms(r['latency_max'])))
    print('失敗      : {}/{}'.format(r['failures'], r['requests']))
    print('接続      : {} 回目で接続, 切断 {} 回'.format(r['connect_attempts'], r['disconnects']))
    print('周囲の BLE:', '-' if r['advertisers'] is None else '{} 台'.format(r['advertisers']))
    print('Wi-Fi     :', ', '.join('{} {}'.format(w['interface'], w['band'] or '(帯域不明)') for w in r['wifi'])
          or '未使用')
    for a in r['advice']:
        print('  * ' + ADVICE_JA.get(a['code'], a['message']))
    print('---------------------------------------')


parser = argparse.ArgumentParser(description="BLE 通信品質の診断")
parser.add_argument('address', metavar='ADDRESS', nargs='?', help='モーターのMACアドレス (省略時はスキャン)')
parser.add_argument('--monitor', action='store_true', help='診断後、通信を続けながら 5 秒ごとに品質を表示')
args = parser.parse_args()

address = args.address or select_motor()
if address is None:
    sys.exit()

dev = connect_motor(address)
print('診断中 ...')
print_result(dev.diagnose_link())

if args.monitor:
    print('モニター中 (Ctrl+C で終了)')
    try:
        last = time.time()
        while True:
            dev.read_motor_measurement(validation_threshold=0)  # 通常の通信の代わり
            time.sleep(0.1)
            if time.time() - last >= 5.0:
                last = time.time()
                s = dev.link_stats(period=5.0)
                print('  応答 中央値 {} / 95% {} / 失敗 {}/{} / 切断 {} 回'.format(
                    ms(s['latency_median']), ms(s['latency_p95']), s['failures'], s['requests'], s['disconnects']))
    except KeyboardInterrupt:
        pass
dev.disconnect()
