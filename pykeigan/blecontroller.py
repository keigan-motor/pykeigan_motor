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
import sys
import threading
import time

from bleak import BleakClient, BleakScanner

from pykeigan import controller as base
from pykeigan.utils import *

SERVICE_UUID = 'f140ea35-8936-4d35-a0ed-dfcd795baa8c'


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

    def _on_detect(d, adv):
        name = adv.local_name or d.name or ''
        uuids = [u.lower() for u in adv.service_uuids]
        if not (SERVICE_UUID in uuids or name.startswith('KM-1')):
            return
        _scanned_devices[d.address.upper()] = d
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
        return sorted(found.values(), key=lambda x: -x['rssi'])

    t0 = time.time()
    return _get_loop().call(_scan(), timeout + 10.0)


class BLEController(base.Controller):
    def __init__(self, addr, debug_mode=False, timeout=10.0):
        """
        Connect to the KeiganMotor at 'addr'.
        'addr' is the MAC address (Windows / Linux) or the device UUID (macOS).
        """
        self.address = addr
        self.timeout = timeout
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
        self._worker.call(self._connect(), self.timeout + 10.0)

    async def _connect(self):
        self._write_lock = asyncio.Lock()
        self._closing = False
        # 1. device found by scan() just before: fastest
        cached = _scanned_devices.pop(self.address.upper(), None)
        if cached is not None:
            try:
                await self.__connect_device(cached)
                return
            except Exception:
                pass  # stale (e.g. the motor was rebooted)
        # 2. Windows: connect by address without scanning. Advertisements are received only every few
        #    seconds in a crowded environment, so scanning first often takes 5-10 sec or more.
        #    Fails immediately if Windows has never seen the device.
        if sys.platform == 'win32':
            try:
                await self.__connect_device(self.address, direct=True)
                return
            except Exception:
                pass
        # 3. scan for the device, then connect
        device = await BleakScanner.find_device_by_address(self.address, timeout=self.timeout)
        if device is None:
            raise ConnectionError('KeiganMotor not found: {}'.format(self.address))
        await self.__connect_device(device)

    async def __connect_device(self, device, direct=False):
        self._client = BleakClient(device, disconnected_callback=self._on_disconnected)
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
        if not self._closing and callable(self.on_motor_connection_error_cb):
            self.on_motor_connection_error_cb(ConnectionError('BLE disconnected'))

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
        self._worker.call(self._write(CHAR_UUIDS[characteristics], tx_buf), self.timeout)

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
    def _read_char(self, name):
        return bytes(self._worker.call(self._client.read_gatt_char(CHAR_UUIDS[name]), self.timeout))

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
