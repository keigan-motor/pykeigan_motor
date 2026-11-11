# -*- coding: utf-8 -*-
# Hardware-free tests for USBController register reading.
import struct
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


# ------------------------------------------------------------
# framing / parsing
# ------------------------------------------------------------
from pykeigan.utils import calc_crc16_bytes


def wire(frame):
    """Serial frame: preamble + [length..payload] + CRC + postamble."""
    return USBController.PREAMBLE + frame + calc_crc16_bytes(frame) + USBController.POSTAMBLE


def measurement_frame(position, velocity=0.0, torque=0.0):
    body = b'\xB4' + float2bytes(position) + float2bytes(velocity) + float2bytes(torque)
    return bytes([len(body) + 1]) + body


def make_parser():
    c = make_controller()
    c.is_check_sum_enabled = False
    c.DebugMode = False
    c.on_motor_measurement_value_cb = False
    c.on_motor_log_cb = False
    got = []
    c.on_motor_measurement_value_cb = got.append
    return c, got


def test_frame_with_crlf_in_payload():
    # bytes 0D 0A inside the float data must not end the frame
    pos = struct.unpack('!f', b'\x0d\x0a\x0d\x0a')[0]
    c, got = make_parser()
    rest = c._parse_frames(wire(measurement_frame(pos)) + wire(measurement_frame(1.0)))
    assert [v['position'] for v in got] == [pos, 1.0]
    assert rest == b''


def test_frame_split_across_reads():
    c, got = make_parser()
    data = wire(measurement_frame(1.5)) + wire(measurement_frame(2.5))
    buf = b''
    for k in range(0, len(data), 5):  # 5 bytes per read
        buf = c._parse_frames(buf + data[k:k + 5])
    assert [v['position'] for v in got] == [1.5, 2.5]
    assert buf == b''


def test_garbage_and_false_preamble_are_skipped():
    c, got = make_parser()
    junk = b'\x01\x02' + USBController.PREAMBLE + b'\x02\xff\xff'  # preamble pattern with a bad length
    rest = c._parse_frames(junk + wire(measurement_frame(3.0)))
    assert [v['position'] for v in got] == [3.0]
    assert rest == b''


def test_crc_checked_when_enabled():
    c, got = make_parser()
    c.is_check_sum_enabled = True
    bad = bytearray(wire(measurement_frame(1.0)))
    bad[-3] ^= 0xFF  # break the CRC
    c._parse_frames(bytes(bad) + wire(measurement_frame(2.0)))
    assert [v['position'] for v in got] == [2.0]


def test_device_name_not_truncated():
    c = make_controller()
    assert parse(c, register_frame(0x46, b'KM-1S NEI7#4A0'))
    assert c.setting_values[0x46][0] == 'KM-1S NEI7#4A0'
    info = b'0:Keigan Inc.,1:KM-1S,2:1,3:2.79B\x00\x00'
    assert parse(c, register_frame(0x47, info))
    assert c.setting_values[0x47][0] == '0:Keigan Inc.,1:KM-1S,2:1,3:2.79B'


def test_log_callback_gets_unknown_codes():
    c, _ = make_parser()
    logs = []
    c.on_motor_log_cb = logs.append
    body = b'\xBE\x00\x00\xFE' + b'\x00\x00\x12\x34'  # unknown command 0xFE, unknown error code
    assert parse(c, bytes([len(body) + 1]) + body)
    assert len(logs) == 1 and logs[0]['command_names'] == 0xFE and logs[0]['error_codes'] == 0x1234
    assert logs[0]['info'] is None  # short frame without info
    assert c.last_error == logs[0]


def test_measurement_too_old_message():
    c = make_controller()
    c._USBController__motor_measurement_value = {'position': 0.0, 'received_unix_time': time.time() - 5}
    c._USBController__imu_measurement_value = None
    with pytest.raises(ValueError, match=r'^No data within 1.0 sec.$'):
        c.read_motor_measurement()
    assert c.read_motor_measurement(validation_threshold=10)['position'] == 0.0


def test_open_timeout_raises():
    t = time.time()
    with pytest.raises(ConnectionError):
        USBController('NO_SUCH_PORT_FOR_TEST', open_timeout=0)
    assert time.time() - t < 2


class _Port:
    def __init__(self, device, vid=0x0403, sn='DM00TEST'):
        self.device, self.vid, self.serial_number = device, vid, sn
        self.pid, self.description = None, 'test port'


def _fake_ports(monkeypatch, ports):
    from serial.tools import list_ports
    monkeypatch.setattr(list_ports, 'comports', lambda: ports)


def test_diagnose_no_device_visible(monkeypatch):
    from pykeigan.usbcontroller import diagnose_port
    _fake_ports(monkeypatch, [_Port('COM1', vid=None)])  # only a non-FTDI port
    msg = diagnose_port('COM3', OSError('not found'))
    assert 'No KeiganMotor USB device' in msg and 'USB hub' in msg


def test_diagnose_wrong_port_lists_candidates(monkeypatch):
    from pykeigan.usbcontroller import diagnose_port
    _fake_ports(monkeypatch, [_Port('COM5')])
    msg = diagnose_port('COM3', OSError('not found'))
    assert 'not a KeiganMotor' in msg and 'COM5' in msg and 'DM00TEST' in msg


def test_diagnose_port_in_use(monkeypatch):
    from pykeigan.usbcontroller import diagnose_port
    _fake_ports(monkeypatch, [_Port('COM5')])
    msg = diagnose_port('com5', serial_exc('Access is denied.'))
    assert 'another program' in msg


def serial_exc(text):
    import serial
    return serial.SerialException(text)


def test_open_timeout_message_has_diagnosis(monkeypatch):
    _fake_ports(monkeypatch, [])
    with pytest.raises(ConnectionError, match='No KeiganMotor USB device'):
        USBController('NO_SUCH_PORT_FOR_TEST', open_timeout=0)


def test_unstable_connection_warning(monkeypatch, capsys):
    _fake_ports(monkeypatch, [])
    c = USBController.__new__(USBController)
    c.port = 'COM5'
    for _ in range(2):
        c._on_usb_lost()
    assert 'disappeared from the OS' in capsys.readouterr().out
    c._on_usb_lost()
    assert 'unstable' in capsys.readouterr().out


def test_usbcheck_no_device(monkeypatch):
    from pykeigan import usbcheck
    _fake_ports(monkeypatch, [_Port('COM1', vid=None)])
    lines = []
    assert usbcheck.check(out=lines.append) is False
    assert any('No KeiganMotor USB device' in l for l in lines)


def test_usbcheck_open_failure(monkeypatch):
    from pykeigan import usbcheck
    _fake_ports(monkeypatch, [])
    lines = []
    assert usbcheck.check('NO_SUCH_PORT_FOR_TEST', out=lines.append) is False
    assert any('[2/3]' in l and 'NG' in l for l in lines)
