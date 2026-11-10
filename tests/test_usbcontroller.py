# -*- coding: utf-8 -*-
# Hardware-free tests for USBController register reading.
import time
import pytest
from pykeigan.usbcontroller import USBController
from pykeigan.utils import float2bytes


def make_controller(responder=None):
    """Build a USBController without opening a serial port."""
    c = USBController.__new__(USBController)
    c.setting_values = {}
    c.auto_serial_reading = True
    c._sent = []

    def read_register(register, identifier=b'\x00\x00'):
        c._sent.append(register)
        if responder:
            responder(c, register)
    c.read_register = read_register
    return c


def register_frame(comm, value_bytes):
    body = b'\x40' + b'\x00\x00' + bytes([comm]) + value_bytes
    return bytes([len(body) + 1]) + body


def parse(c, frame):
    return c._USBController__serialdataParse(frame)


@pytest.mark.parametrize('comm', [0x2C, 0x3C, 0xC3])
def test_parse_uint8_registers(comm):
    c = make_controller()
    assert parse(c, register_frame(comm, b'\x03'))
    assert c.setting_values[comm][0] == 3


def test_read_returns_fresh_value():
    def responder(c, register):
        parse(c, register_frame(register, float2bytes(2.5)))
    c = make_controller(responder)
    assert c._read_setting_value(0x02) == 2.5


def test_read_ignores_stale_value():
    c = make_controller()  # motor never answers
    c.setting_values[0x02] = (1.0, time.time() - 10)
    with pytest.raises(ValueError, match='No data received'):
        c._read_setting_value(0x02, validation_threshold=0.05)


@pytest.mark.parametrize('method', ['read_baud_rate', 'read_motor_measurement_interval',
                                    'read_imu_measurement_interval'])
def test_public_readers_are_accepted(method):
    def responder(c, register):
        parse(c, register_frame(register, b'\x01'))
    c = make_controller(responder)
    assert getattr(c, method)() == 1
