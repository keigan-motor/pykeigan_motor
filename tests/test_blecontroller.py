# -*- coding: utf-8 -*-
"""Tests of blecontroller that do not need a Motor or a BLE adapter."""
import asyncio
import collections
import threading
import time

import pytest

pytest.importorskip('bleak')

from pykeigan import blecontroller as ble
from pykeigan.utils import float2bytes, uint8_t2bytes, uint32_t2bytes


def make_controller():
    """BLEController without connecting (only the attributes used by the tested methods)."""
    c = object.__new__(ble.BLEController)
    c.address = 'AA:BB:CC:DD:EE:FF'
    c.timeout = 1.0
    c.retries = 0
    c.DebugMode = False
    c.setting_values = {}
    c._setting_events = {}
    c._setting_locks = {}
    c._motor_measurement_value = None
    c._imu_measurement_value = None
    c.on_motor_measurement_value_cb = False
    c.on_motor_imu_measurement_cb = False
    c.on_motor_connection_error_cb = False
    c.on_motor_log_cb = False
    c.on_motor_event_cb = False
    c._link = {'connect_attempts': 1, 'disconnects': 0, 'connected_time': time.time()}
    c._requests = collections.deque(maxlen=200)
    c._client = None
    c._closing = False
    return c


CRC = b'\x00\x00'  # the parser does not check the CRC


# ------------------------------------------------------------
# event loop thread
# ------------------------------------------------------------
def test_call_timeout_cancels_coroutine():
    worker = ble._get_loop()
    state = {}

    async def slow():
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            state['cancelled'] = True
            raise

    with pytest.raises(TimeoutError):
        worker.call(slow(), 0.1)
    for _ in range(50):
        if state.get('cancelled'):
            break
        time.sleep(0.01)
    assert state.get('cancelled')


def test_call_from_loop_thread_raises():
    worker = ble._get_loop()
    result = {}

    async def inner():
        return 1

    def in_loop():
        try:
            worker.call(inner(), 1)
        except RuntimeError as e:
            result['error'] = e

    async def run():
        in_loop()

    worker.call(run(), 1)
    assert isinstance(result.get('error'), RuntimeError)


def test_not_connected_raises_connection_error():
    c = make_controller()
    with pytest.raises(ConnectionError):
        c.enable_action()
    with pytest.raises(ConnectionError):
        c._read_char('motor_measurement')
    assert len(c._requests) == 0  # not counted as a failed request


def test_connect_time_limit_covers_all_steps():
    c = make_controller()
    c.timeout, c.retries = 10.0, 2
    # 3 attempts x (scan + connect + discard) at least
    assert c._connect_time_limit() >= 3 * 3 * 10.0


# ------------------------------------------------------------
# notifications
# ------------------------------------------------------------
def test_motor_measurement_notification():
    c = make_controller()
    got = []
    c.on_motor_measurement_value_cb = got.append
    c._on_motor_measurement(None, float2bytes(1.0) + float2bytes(2.0) + float2bytes(0.5))
    assert got and got[0]['position'] == 1.0 and got[0]['velocity'] == 2.0 and got[0]['torque'] == 0.5
    assert c.read_motor_measurement() is got[0]  # recent notification is returned without reading


def test_register_float():
    c = make_controller()
    c._on_rx(None, b'\x40\x00\x00\x02' + float2bytes(3.5) + CRC)
    assert c.setting_values[0x02][0] == 3.5


@pytest.mark.parametrize('comm', [0x05, 0x2C, 0x3C, 0xC3])
def test_register_uint8(comm):
    c = make_controller()
    c._on_rx(None, b'\x40\x00\x00' + uint8_t2bytes(comm) + b'\x04' + CRC)
    assert c.setting_values[comm][0] == 4


def test_register_color_and_name():
    c = make_controller()
    c._on_rx(None, b'\x40\x00\x00\x3A\x01\x02\x03' + CRC)
    assert c.setting_values[0x3A][0] == (1, 2, 3)
    c._on_rx(None, b'\x40\x00\x00\x46' + b'KM-1S ABCD#12\x00' + CRC)
    assert c.setting_values[0x46][0] == 'KM-1S ABCD#12'


def test_command_log_and_event():
    c = make_controller()
    logs, events = [], []
    c.on_motor_log_cb = logs.append
    c.on_motor_event_cb = events.append
    c._on_rx(None, b'\xBE\x00\x00\x51' + uint32_t2bytes(0) + CRC)
    assert logs == [{'command_names': 0x51, 'error_codes': 0}]
    c._on_rx(None, b'\xCE\x01\x02\x03' + CRC)
    assert events and events[0]['number'] == 2 and events[0]['state'] == 3


def test_rx_parse_error_is_ignored():
    c = make_controller()
    c._on_rx(None, b'\xCE\xFF\x00\x00' + CRC)  # unknown event type: ignored


def test_read_setting_value_waits_for_notification():
    c = make_controller()

    def fake_read_register(comm, identifier=b'\x00\x00'):
        # the Motor answers by a notification from another thread
        threading.Timer(0.05, c._on_rx, (None, b'\x40\x00\x00' + uint8_t2bytes(comm) + b'\x05' + CRC)).start()

    c.read_register = fake_read_register
    assert c.read_imu_measurement_interval() == 5
    with pytest.raises(ValueError):
        c._read_setting_value(0xFF)  # unknown register


# ------------------------------------------------------------
# link quality
# ------------------------------------------------------------
def test_rssi_is_ignored_when_stale():
    c = make_controller()
    key = c.address.upper()
    ble._scanned_rssi[key] = (-60, time.time())
    assert c._rssi() == -60
    ble._scanned_rssi[key] = (-60, c._link['connected_time'] - ble.RSSI_MAX_AGE - 1)
    assert c._rssi() is None
    del ble._scanned_rssi[key]
    assert c._rssi() is None


def test_diagnose_link_slow_response_without_rssi(monkeypatch):
    c = make_controller()
    ble._scanned_rssi.pop(c.address.upper(), None)
    monkeypatch.setattr(ble, 'check_wifi', lambda: [])
    c.is_connected = lambda: True
    c._read_char = lambda *a, **k: (b'', 0.6)  # 600 ms: poor
    r = c.diagnose_link(count=5, scan_time=0)
    assert r['level'] == 'poor'
    assert [a['code'] for a in r['advice']] == ['slow_response']


def test_diagnose_link_interference_with_good_rssi(monkeypatch):
    c = make_controller()
    ble._scanned_rssi[c.address.upper()] = (-50, time.time())
    monkeypatch.setattr(ble, 'check_wifi', lambda: [])
    c.is_connected = lambda: True
    c._read_char = lambda *a, **k: (b'', 0.2)  # 200 ms: fair
    r = c.diagnose_link(count=5, scan_time=0)
    assert r['level'] == 'fair'
    assert [a['code'] for a in r['advice']] == ['interference']
    del ble._scanned_rssi[c.address.upper()]


def test_diagnose_link_good(monkeypatch):
    c = make_controller()
    monkeypatch.setattr(ble, 'check_wifi', lambda: [])
    c.is_connected = lambda: True
    c._read_char = lambda *a, **k: (b'', 0.05)
    r = c.diagnose_link(count=5, scan_time=0)
    assert r['level'] == 'good' and r['advice'] == [] and r['latency_median'] == 0.05


# ------------------------------------------------------------
# Wi-Fi
# ------------------------------------------------------------
NETSH_JA = u"""
システムに 2 のインターフェイスがあります:

    名前                   : Wi-Fi
    説明                   : Intel(R) Wi-Fi 7 BE200 320MHz
    状態                   : 接続されました
    SSID                   : test
    バンド                 : 6 GHz
    チャネル               : 5

    名前                   : Wi-Fi 2
    説明                   : USB Adapter
    状態                   : 切断されました
"""

NETSH_EN = u"""
There is 1 interface on the system:

    Name                   : Wi-Fi
    Description            : Some adapter
    State                  : connected
    SSID                   : test
    Channel                : 6
"""


def test_netsh_japanese_6ghz():
    # 6GHz channel 5 must not be regarded as 2.4GHz; disconnected interfaces are skipped
    assert ble._parse_netsh_interfaces(NETSH_JA) == [{'interface': 'Wi-Fi', 'channel': 5, 'band': '6GHz'}]


def test_netsh_english_without_band():
    assert ble._parse_netsh_interfaces(NETSH_EN) == [{'interface': 'Wi-Fi', 'channel': 6, 'band': '2.4GHz'}]


def test_band():
    assert ble._band(freq=2437) == '2.4GHz'
    assert ble._band(freq=5180) == '5GHz'
    assert ble._band(freq=5955) == '6GHz'
    assert ble._band(ghz=2.4) == '2.4GHz'
    assert ble._band(ghz=5) == '5GHz'
    assert ble._band(ghz=6) == '6GHz'
    assert ble._band(channel=36) == '5GHz'
    assert ble._band() is None


def test_decode():
    text = u'チャネル : 6'
    assert ble._decode(text.encode('utf-8')) == text
    assert isinstance(ble._decode(text.encode('cp932')), str)  # never raises
