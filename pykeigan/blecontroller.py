#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp

BLE controller for KeiganMotor, based on bleak (Windows / Linux incl. Raspberry Pi / macOS).

bleak is asyncio based. This controller runs its own event loop in a background
thread so that the public API stays synchronous (same as USBController).
Notification callbacks (on_motor_measurement_value_cb etc.) are called from that
background thread; keep them short and do not call blocking BLEController
methods from inside them.
"""
import asyncio
import atexit
import collections
import glob
import re
import statistics
import subprocess
import sys
import threading
import time

from bleak import BleakClient, BleakScanner

from pykeigan import controller as base
from pykeigan.utils import *

SERVICE_UUID = 'f140ea35-8936-4d35-a0ed-dfcd795baa8c'


class DeviceNotFoundError(ConnectionError):
    """The KeiganMotor was not found by scanning (not advertising, out of range, or connected to another device)."""


def _uuid(n):
    return 'f14000{:02x}-8936-4d35-a0ed-dfcd795baa8c'.format(n)


CHAR_UUIDS = {
    'motor_tx': _uuid(0x01),
    'motor_led': _uuid(0x03),
    'motor_measurement': _uuid(0x04),
    'motor_imu_measurement': _uuid(0x05),
    'motor_rx': _uuid(0x06),
}

FLOAT_VALUE_COMMS = [0x02, 0x03, 0x07, 0x08, 0x0E, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21, 0x5B]
VALID_COMMS = [0x05, 0x2C, 0x3A, 0x46, 0x47, 0x9A] + FLOAT_VALUE_COMMS


class _LoopThread(object):
    """asyncio event loop running in a daemon thread."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, name='pykeigan-ble', daemon=True)
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def call(self, coro, timeout=None):
        if threading.current_thread() is self.thread:
            # called from a callback (on_motor_*_cb): waiting here would block the loop itself
            coro.close()
            raise RuntimeError('BLEController commands cannot be called from callbacks. '
                               'Store the value in the callback and send commands from another thread.')
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)


_shared_loop = None
_shared_loop_lock = threading.Lock()
_scanned_devices = {}  # address(upper) -> BLEDevice found by scan(); lets connect() skip rescanning
_scanned_rssi = {}  # address(upper) -> (rssi, unix time) of the latest advertisement received
_last_scan = {}  # {'advertisers': number of BLE devices (of any kind) seen, 'time': unix time} of the latest scan()

# link quality thresholds used by BLEController.diagnose_link()
RSSI_GOOD = -70  # dBm. weaker than this: 'fair'
RSSI_POOR = -85  # dBm. weaker than this: 'poor'
LATENCY_FAIR = 0.15  # sec (95th percentile of round trip time). longer than this: 'fair'
LATENCY_POOR = 0.5  # sec. longer than this: 'poor'
FAILURE_FAIR = 0.0  # ratio of failed requests. more than this: 'fair'
FAILURE_POOR = 0.05  # more than this: 'poor'
CROWDED_ADVERTISERS = 30  # number of BLE devices nearby regarded as a crowded 2.4GHz environment
_LEVELS = ('good', 'fair', 'poor')


def _get_loop():
    """All BLE operations (scan and every controller) share one event loop thread."""
    global _shared_loop
    with _shared_loop_lock:
        if _shared_loop is None:
            _shared_loop = _LoopThread()
        return _shared_loop


def scan(timeout=5.0, on_found=None):
    """
    Scan KeiganMotors nearby.
    Returns a list of dict {'name', 'address', 'rssi'} sorted by signal strength.
    On Windows / Linux no administrator (sudo) privileges are required.
    'on_found' (optional) is called with the dict (plus 'elapsed' in sec) when each Motor is found for the first time.
    It is called from a background thread.
    """
    found = {}  # address -> dict
    advertisers = set()

    def _on_detect(d, adv):
        advertisers.add(d.address)
        name = adv.local_name or d.name or ''
        uuids = [u.lower() for u in adv.service_uuids]
        if not (SERVICE_UUID in uuids or name.startswith('KM-1')):
            return
        _scanned_devices[d.address.upper()] = d
        _record_rssi(d.address, adv.rssi)
        km = found.get(d.address)
        if km is None:
            km = found[d.address] = {'name': name, 'address': d.address, 'rssi': adv.rssi}
            if callable(on_found):
                try:
                    on_found(dict(km, elapsed=time.time() - t0))
                except Exception:
                    pass  # errors in the user's callback must not stop the scan
        else:
            km['rssi'] = adv.rssi
            km['name'] = name or km['name']

    async def _scan():
        async with BleakScanner(detection_callback=_on_detect):
            await asyncio.sleep(timeout)
        _last_scan.update(advertisers=len(advertisers), time=time.time())
        return sorted(found.values(), key=lambda x: -x['rssi'])

    t0 = time.time()
    return _get_loop().call(_scan(), timeout + 10.0)


def _record_rssi(address, rssi):
    if rssi is not None and rssi > -127:  # BlueZ reports -127 when the RSSI is unknown
        _scanned_rssi[address.upper()] = rssi, time.time()


async def _find_device(address, timeout):
    """Scan for 'address' and record the RSSI of its advertisement. Returns BLEDevice or None."""
    key = address.upper()

    def _match(d, adv):
        if d.address.upper() != key:
            return False
        _record_rssi(key, adv.rssi)
        return True

    return await BleakScanner.find_device_by_filter(_match, timeout=timeout)


def _run(cmd, timeout=3.0):
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout, check=False).stdout.decode('utf-8', 'replace')
    except Exception:
        return ''


def _band(freq=None, channel=None):
    if freq:
        return '2.4GHz' if freq < 3000 else '5GHz' if freq < 5925 else '6GHz'
    if channel:
        return '2.4GHz' if channel <= 14 else '5GHz'
    return None


def check_wifi():
    """
    Check the Wi-Fi of this PC. 2.4GHz Wi-Fi interferes with BLE: both use the 2.4GHz band, and most PCs and
    Raspberry Pi share one radio chip and antenna for Wi-Fi and Bluetooth.
    Returns a list of dict {'interface', 'channel', 'band'} of the Wi-Fi interfaces in use
    ('channel' / 'band' ('2.4GHz', '5GHz', '6GHz') are None if unknown).
    Returns an empty list if Wi-Fi is not used (turned off / not connected). Linux and Windows only.
    """
    result = []
    if sys.platform.startswith('linux'):
        for path in sorted(glob.glob('/sys/class/net/*/wireless')):
            iface = path.split('/')[-2]
            try:
                with open('/sys/class/net/{}/operstate'.format(iface)) as f:
                    if f.read().strip() != 'up':
                        continue  # turned off (nmcli radio wifi off / rfkill) or not connected
            except OSError:
                continue
            ch = freq = None
            m = re.search(r'^\*:(\d+):(\d+)', _run(['nmcli', '-t', '-f', 'IN-USE,CHAN,FREQ', 'dev', 'wifi', 'list',
                                                    'ifname', iface, '--rescan', 'no']), re.M)
            if m:
                ch, freq = int(m.group(1)), float(m.group(2))
            else:
                m = re.search(r'freq:\s*([\d.]+)', _run(['iw', 'dev', iface, 'link']))
                freq = float(m.group(1)) if m else None
            result.append({'interface': iface, 'channel': ch, 'band': _band(freq=freq)})
    elif sys.platform == 'win32':
        # the output of netsh is localized (English / Japanese supported). 'Channel' appears only while connected.
        out = _run(['netsh', 'wlan', 'show', 'interfaces'])
        for block in re.split(r'^\s*(?=(?:Name|名前)\s*:)', out, flags=re.M)[1:]:
            name = re.match(r'(?:Name|名前)\s*:\s*(.+)', block)
            m = re.search(r'(?:Channel|チャネル)\s*:\s*(\d+)', block)
            if m:
                ch = int(m.group(1))
                result.append({'interface': name.group(1).strip(), 'channel': ch, 'band': _band(channel=ch)})
    return result


def _percentile(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p * (len(values) - 1))))]


def _worse(a, b):
    return a if _LEVELS.index(a) >= _LEVELS.index(b) else b


class BLEController(base.Controller):
    def __init__(self, addr, debug_mode=False, timeout=10.0, retries=2):
        """
        Connect to the KeiganMotor at 'addr'.
        'addr' is the MAC address (Windows / Linux) or the device UUID (macOS).
        'timeout' is the time limit [sec] of each scan / connection attempt.
        'retries' is the number of additional connection attempts when connecting fails
        (BLE connections sometimes fail to be established, e.g. Raspberry Pi with 2.4GHz Wi-Fi).
        Raises DeviceNotFoundError if the Motor is not found, ConnectionError if connecting fails.
        """
        self.address = addr
        self.timeout = timeout
        self.retries = max(0, int(retries))
        self.DebugMode = debug_mode
        self.setting_values = {}
        self._setting_events = {}
        self._motor_measurement_value = None
        self._imu_measurement_value = None

        self.on_motor_measurement_value_cb = False
        self.on_motor_imu_measurement_cb = False
        self.on_motor_connection_error_cb = False
        self.on_motor_log_cb = False
        self.on_motor_event_cb = False

        self._link = {'connect_attempts': None, 'disconnects': 0, 'connected_time': None}
        self._requests = collections.deque(maxlen=200)  # (unix time, round trip time [sec] or None if failed)
        self._client = None
        self._write_lock = None
        self._closing = False
        self._worker = _get_loop()
        atexit.register(self._cleanup)
        self.connect()
        self.set_interface(self.interface_type['BLE'] + self.interface_type['BTN'])

    # ------------------------------------------------------------
    # connection
    # ------------------------------------------------------------
    def connect(self):
        """
        Establish the BLE connection.
        """
        # each attempt may take up to 'timeout' for scanning and 'timeout' for connecting
        attempts = self.retries + 1
        self._worker.call(self._connect(), attempts * (2 * self.timeout + 5.0) + 10.0)

    async def _connect(self):
        self._write_lock = asyncio.Lock()
        self._closing = False
        attempts = self.retries + 1
        last_error = None
        # device found by scan() just before: fastest (no scanning needed)
        device = _scanned_devices.pop(self.address.upper(), None)
        for attempt in range(attempts):
            if attempt:
                await asyncio.sleep(0.5)
            if device is None and sys.platform == 'win32':
                # Windows: connect by address without scanning. Advertisements are received only every few
                # seconds in a crowded environment, so scanning first often takes 5-10 sec or more.
                # Fails immediately if Windows has never seen the device.
                try:
                    await self.__connect_device(self.address, direct=True)
                    self._link['connect_attempts'] = attempt + 1
                    return
                except Exception:
                    pass
            if device is None or attempt:
                # scan for the device. On a retry, the previous device may be stale (e.g. the Motor was
                # rebooted): use the newly found one, or keep the previous one if not found this time.
                found = await _find_device(self.address, self.timeout)
                if found is not None:
                    device = found
                elif device is None:
                    raise DeviceNotFoundError('KeiganMotor not found: {}'.format(self.address))
            try:
                await self.__connect_device(device)
                self._link['connect_attempts'] = attempt + 1
                return
            except Exception as e:
                last_error = e
                if self.DebugMode:
                    print('connect attempt {}/{} failed: {!r}'.format(attempt + 1, attempts, e))
        raise ConnectionError('Failed to connect to KeiganMotor {} ({} attempts): {!r}'.format(
            self.address, attempts, last_error)) from last_error

    async def __connect_device(self, device, direct=False):
        self._client = BleakClient(device, disconnected_callback=self._on_disconnected)
        try:
            if direct:
                # bleak (WinRT) scans only to get the 48-bit Bluetooth address; give it directly.
                backend = getattr(self._client, '_backend', None)
                if backend is None or not hasattr(backend, '_device_info'):
                    raise LookupError('direct connection is not supported by this bleak version')
                backend._device_info = int(self.address.replace(':', ''), 16)
            await self._client.connect(timeout=self.timeout)
            await self._client.start_notify(CHAR_UUIDS['motor_measurement'], self._on_motor_measurement)
            await self._client.start_notify(CHAR_UUIDS['motor_imu_measurement'], self._on_imu_measurement)
            await self._client.start_notify(CHAR_UUIDS['motor_rx'], self._on_rx)
            self._link.update(client=self._client, connected_time=time.time())
        except BaseException:
            await self.__discard_client()
            raise

    async def __discard_client(self):
        """Disconnect and forget a client whose connection attempt failed (so it does not block the next attempt)."""
        client, self._client = self._client, None
        if client is None:
            return
        try:
            await asyncio.wait_for(client.disconnect(), self.timeout)
        except Exception:
            pass

    def is_connected(self):
        return self._client is not None and self._client.is_connected

    def disconnect(self):
        """
        Close the BLE connection.
        """
        self._closing = True
        if self.is_connected():
            self._worker.call(self._client.disconnect(), self.timeout)

    def _cleanup(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def _on_disconnected(self, client):
        if client is not self._client:
            return  # a client discarded after a failed connection attempt
        if not self._closing and self._link.get('client') is client:
            self._link['disconnects'] += 1  # only after the connection was established (not failed attempts)
        if not self._closing and callable(self.on_motor_connection_error_cb):
            self.on_motor_connection_error_cb(ConnectionError('BLE disconnected'))

    # ------------------------------------------------------------
    # link quality
    # ------------------------------------------------------------
    def link_stats(self, period=None):
        """
        Statistics of the requests (commands and reads) sent in normal use, to monitor the link quality
        without extra communication. 'period' [sec]: only the requests in the last 'period' sec (default: last 200).
        Returns dict {'requests', 'failures', 'failure_rate', 'latency_median', 'latency_p95', 'latency_max'
        (round trip time [sec]; None if no successful request), 'connect_attempts', 'disconnects', 'rssi'}.
        'rssi' [dBm] is that of the advertisement received before connecting (None if unknown).
        BLE retransmits lost packets automatically, so interference usually appears as longer / irregular
        latency rather than failures. Failures mean the link is very poor.
        """
        samples = list(self._requests)
        if period is not None:
            since = time.time() - period
            samples = [x for x in samples if x[0] >= since]
        latencies = [rtt for _, rtt in samples if rtt is not None]
        failures = len(samples) - len(latencies)
        rssi = _scanned_rssi.get(self.address.upper())
        return {'requests': len(samples), 'failures': failures,
                'failure_rate': failures / len(samples) if samples else 0.0,
                'latency_median': statistics.median(latencies) if latencies else None,
                'latency_p95': _percentile(latencies, 0.95) if latencies else None,
                'latency_max': max(latencies) if latencies else None,
                'connect_attempts': self._link['connect_attempts'], 'disconnects': self._link['disconnects'],
                'rssi': rssi[0] if rssi else None}

    def diagnose_link(self, count=30, scan_time=3.0):
        """
        Measure the BLE link quality and the radio environment, and judge whether BLE is usable.
        Reads the measurement characteristic 'count' times (no effect on the Motor) to measure the response time,
        and scans 'scan_time' [sec] to count BLE devices nearby (0: skip). Takes about 'scan_time' + 1-3 sec.
        Returns dict: link_stats() of the probe requests, plus the following keys.

        - 'level': 'good' / 'fair' (usable but unstable; improvement recommended) / 'poor' (hard to use)
        - 'advertisers': number of BLE devices seen nearby (None if not scanned)
        - 'wifi': check_wifi()
        - 'advice': list of dict {'code', 'message'}. code: 'weak_signal', 'interference', 'wifi_2.4ghz',
          'crowded', 'reconnected', 'disconnected'

        Thresholds are the module constants RSSI_GOOD, RSSI_POOR, LATENCY_FAIR, LATENCY_POOR, FAILURE_FAIR,
        FAILURE_POOR and CROWDED_ADVERTISERS.
        """
        advertisers = self._worker.call(self._count_advertisers(scan_time), scan_time + 10.0) if scan_time else None
        probe = []  # round trip time [sec] or None if failed
        for _ in range(count):
            if not self.is_connected():
                probe.append(None)
                break
            try:
                self._read_char('motor_measurement', timeout=1.0)
                probe.append(self._requests[-1][1])
            except Exception:
                probe.append(None)
            time.sleep(0.02)
        stats = self.link_stats()
        # statistics of the probe requests only
        latencies = [rtt for rtt in probe if rtt is not None]
        stats.update(requests=len(probe), failures=len(probe) - len(latencies),
                     failure_rate=(len(probe) - len(latencies)) / len(probe) if probe else 0.0,
                     latency_median=statistics.median(latencies) if latencies else None,
                     latency_p95=_percentile(latencies, 0.95) if latencies else None,
                     latency_max=max(latencies) if latencies else None)
        wifi = check_wifi()
        stats.update(advertisers=advertisers, wifi=wifi)

        level, advice = 'good', []

        def add(lv, code, message):
            nonlocal level
            level = _worse(level, lv)
            advice.append({'code': code, 'message': message})

        if not self.is_connected():
            add('poor', 'disconnected', 'The connection was lost during the measurement. '
                                        'Move the PC closer to the Motor and connect again.')
        rssi = stats['rssi']
        signal_level = 'good'
        if rssi is not None and rssi < RSSI_GOOD:
            signal_level = 'poor' if rssi < RSSI_POOR else 'fair'
            add(signal_level, 'weak_signal',
                'The signal is weak (RSSI {} dBm). Move the PC closer to the Motor, and keep metal objects, '
                'walls and people out of the line between them.'.format(rssi))
        link_level = 'good'
        p95 = stats['latency_p95']
        if stats['failure_rate'] > FAILURE_POOR or (p95 is not None and p95 > LATENCY_POOR) or (probe and not latencies):
            link_level = 'poor'
        elif stats['failure_rate'] > FAILURE_FAIR or (p95 is not None and p95 > LATENCY_FAIR):
            link_level = 'fair'
        if link_level != 'good' and signal_level == 'good':
            add(link_level, 'interference',
                'Responses are delayed or lost (failures {}/{}, 95% latency {}) although the signal is not weak: '
                'radio interference is likely. Keep away from 2.4GHz devices (Wi-Fi routers, microwave ovens, '
                'wireless cameras, other Bluetooth devices) or change the place.'.format(
                    stats['failures'], stats['requests'], '{:.0f} ms'.format(p95 * 1000) if p95 else '-'))
        elif link_level != 'good':
            level = _worse(level, link_level)  # explained by the weak signal
        for w in wifi:
            if w['band'] in ('2.4GHz', None):
                # Raspberry Pi (Linux): on-board Wi-Fi and Bluetooth share one chip and 2.4GHz Wi-Fi makes BLE fail
                # very often, so this alone makes the level 'fair'. Other PCs: advice only.
                add('fair' if sys.platform.startswith('linux') else 'good', 'wifi_2.4ghz',
                    'This PC is using {} Wi-Fi ({}{}), which interferes with BLE. Use wired LAN and turn Wi-Fi off, '
                    'or use 5GHz Wi-Fi.'.format(w['band'] or 'probably 2.4GHz', w['interface'],
                                                 ', ch {}'.format(w['channel']) if w['channel'] else ''))
        if advertisers is not None and advertisers >= CROWDED_ADVERTISERS:
            advice.append({'code': 'crowded', 'message':
                           'Many BLE devices ({}) are nearby: the 2.4GHz band is crowded and the link may become '
                           'unstable.'.format(advertisers)})
        if (stats['connect_attempts'] or 1) > 1 or stats['disconnects']:
            add('fair', 'reconnected', 'The connection was unstable: {} attempts to connect, {} disconnections.'.format(
                stats['connect_attempts'], stats['disconnects']))
        stats.update(level=level, advice=advice)
        return stats

    async def _count_advertisers(self, scan_time):
        seen = set()

        def _on_detect(d, adv):
            seen.add(d.address)
            if d.address.upper() == self.address.upper():
                _record_rssi(d.address, adv.rssi)

        async with BleakScanner(detection_callback=_on_detect):
            await asyncio.sleep(scan_time)
        _last_scan.update(advertisers=len(seen), time=time.time())
        return len(seen)

    # ------------------------------------------------------------
    # debug
    # ------------------------------------------------------------
    def start_debug(self):
        """
        Start to print command logs
        """
        self.DebugMode = True

    def finish_debug(self):
        """
        Finish to print command logs
        """
        self.DebugMode = False

    # ------------------------------------------------------------
    # write
    # ------------------------------------------------------------
    def _run_command(self, val, characteristics=None):
        if characteristics not in ('motor_tx', 'motor_led', 'motor_rx'):
            raise ValueError('Invalid Characteristics')
        tx_buf = val + calc_crc16_bytes(val)
        self._timed(lambda: self._worker.call(self._write(CHAR_UUIDS[characteristics], tx_buf), self.timeout))

    def _timed(self, func):
        """Run a request (write with response / read) and record its round trip time for link_stats()."""
        t = time.perf_counter()
        try:
            result = func()
        except BaseException:
            self._requests.append((time.time(), None))
            raise
        self._requests.append((time.time(), time.perf_counter() - t))
        return result

    async def _write(self, uuid, data):
        async with self._write_lock:
            await self._client.write_gatt_char(uuid, data, response=True)

    # ------------------------------------------------------------
    # notifications (called in the event loop thread)
    # ------------------------------------------------------------
    def _on_motor_measurement(self, _, data):
        if len(data) < 12:
            return
        self._motor_measurement_value = {'position': bytes2float(data[0:4]), 'velocity': bytes2float(data[4:8]),
                                         'torque': bytes2float(data[8:12]), 'received_unix_time': time.time()}
        if callable(self.on_motor_measurement_value_cb):
            self.on_motor_measurement_value_cb(self._motor_measurement_value)

    def _on_imu_measurement(self, _, data):
        if len(data) < 14:
            return
        self._imu_measurement_value = self.__parse_imu(data)
        if callable(self.on_motor_imu_measurement_cb):
            self.on_motor_imu_measurement_cb(self._imu_measurement_value)

    def _on_rx(self, _, data):
        # [datatype][identifier(2)][payload...][crc(2)]  (same layout as USB after the length byte)
        data = bytes(data)
        if len(data) < 4:
            return
        datatype = data[0]
        payload = data[1:]
        try:
            if datatype == 0x40:  # register value
                self.__parse_register(payload)
            elif datatype == 0xBE:  # command log
                cmd = bytes2uint8_t(payload[2:3])
                err_code = bytes2uint32_t(payload[3:7])
                log = {'command_names': cmd, 'error_codes': err_code}
                if callable(self.on_motor_log_cb):
                    self.on_motor_log_cb(log)
                if self.DebugMode:
                    print(self.command_names.get(cmd, hex(cmd)), self.error_codes.get(err_code, err_code))
            elif datatype == 0xCE:  # event (button etc.)
                event = {'event_type': self.event_types[bytes2uint8_t(payload[0:1])],
                         'number': bytes2uint8_t(payload[1:2]), 'state': bytes2uint8_t(payload[2:3])}
                if callable(self.on_motor_event_cb):
                    self.on_motor_event_cb(event)
        except Exception as e:
            if self.DebugMode:
                print('BLE rx parse error:', e, data.hex())

    def __parse_register(self, payload):
        comm = bytes2uint8_t(payload[2:3])
        value = payload[3:]
        if comm in FLOAT_VALUE_COMMS:
            val = bytes2float(value[0:4])
        elif comm in (0x05, 0x2C):  # curve type / motor measurement interval (uint8)
            val = bytes2uint8_t(value[0:1])
        elif comm == 0x3A:
            val = bytes2uint8_t(value[0:1]), bytes2uint8_t(value[1:2]), bytes2uint8_t(value[2:3])
        elif comm in (0x46, 0x47):  # device name / device info (variable length, last 2 bytes are CRC)
            val = value[:-2].decode('utf-8', 'replace').rstrip('\x00')
        elif comm == 0x9A:
            bits_list = [int(n) for n in bin(bytes2uint8_t(value[0:1]))[2:].zfill(8)]
            val = {"isCheckSumEnabled": bits_list[0], "iMUMeasurement": bits_list[4], "motorMeasurement": bits_list[5],
                   "queue": bits_list[6], "motorEnabled": bits_list[7],
                   "flash_memory_state": self.flash_memory_states[bytes2uint8_t(value[1:2])],
                   "motor_control_mode": self.motor_control_modes[bytes2uint8_t(value[2:3])]}
        else:
            return
        self.setting_values[comm] = val, time.time()
        event = self._setting_events.get(comm)
        if event is not None:
            event.set()

    @staticmethod
    def __parse_imu(ba):
        return {'accel_x': bytes2int16_t(ba[0:2]) * 2.0 / 32767,
                'accel_y': bytes2int16_t(ba[2:4]) * 2.0 / 32767,
                'accel_z': bytes2int16_t(ba[4:6]) * 2.0 / 32767,
                'temp': bytes2int16_t(ba[6:8]) / 333.87 + 21.00,
                'gyro_x': bytes2int16_t(ba[8:10]) * 0.00013316211,
                'gyro_y': bytes2int16_t(ba[10:12]) * 0.00013316211,
                'gyro_z': bytes2int16_t(ba[12:14]) * 0.00013316211,
                'received_unix_time': time.time()}

    # ------------------------------------------------------------
    # read
    # ------------------------------------------------------------
    def _read_char(self, name, timeout=None):
        timeout = self.timeout if timeout is None else timeout
        return bytes(self._timed(lambda: self._worker.call(
            asyncio.wait_for(self._client.read_gatt_char(CHAR_UUIDS[name]), timeout), timeout + 1.0)))

    def read_motor_measurement(self, validation_threshold=0.5):
        """
        Get the position, velocity, and torque and store them to the properties 'position' in rad, 'velocity' in rad/sec, and 'torque' in N.m.
        Returns the latest notified value, or reads the characteristic directly if no recent notification.
        """
        v = self._motor_measurement_value
        if v is not None and time.time() - v['received_unix_time'] < validation_threshold:
            return v
        ba = self._read_char('motor_measurement')
        if len(ba) < 12:
            raise ValueError("Unknown Error. Reading motor measurement values failed.")
        return {'position': bytes2float(ba[0:4]), 'velocity': bytes2float(ba[4:8]), 'torque': bytes2float(ba[8:12]),
                'received_unix_time': time.time()}

    def read_imu_measurement(self, validation_threshold=0.5):
        """
        Get the x,y,z axis acceleration, temperature, and anguler velocities around x,y,z axis
        and store them to 'accel_x', 'accel_y', 'accel_z' in g(9.80665 m/s^2), 'temp' in degree Celsius, 'gyro_x', 'gyro_y', and 'gyro_z' in rad/sec. Need to call enable_continual_imu_measurement() before calling this function.
        """
        v = self._imu_measurement_value
        if v is not None and time.time() - v['received_unix_time'] < validation_threshold:
            return v
        ba = self._read_char('motor_imu_measurement')
        if len(ba) < 14:
            raise ValueError("Reading imu values failed. Did you call enable_continual_imu_measurement() beforehand?")
        return self.__parse_imu(ba)

    def _read_setting_value(self, comm, timeout=1.0):
        if comm not in VALID_COMMS:
            raise ValueError("Unknown Command")
        event = threading.Event()
        self._setting_events[comm] = event
        try:
            self.read_register(comm)
            if not event.wait(timeout):
                raise ValueError("No data received")
            return self.setting_values[comm][0]
        finally:
            self._setting_events.pop(comm, None)
