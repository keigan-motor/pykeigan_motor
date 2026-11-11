# -*- coding: utf-8 -*-
import re
from pykeigan import errors, controller
from pykeigan.utils import uint32_t2bytes, float2bytes, bytes2uint32_t


def test_all_firmware_codes_are_described():
    # all the codes of km_error.h (KM-1 firmware)
    for code in (0, 100, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 15, 16, 17, 18, 20, 60, 61, 62, 63, 70, 80, 81):
        e = errors.ERRORS[code]
        assert e.code == code and e.name.startswith('KM_') and e.summary and e.remedy


def test_error_codes_property_keeps_old_names():
    names = controller.Controller().error_codes
    assert names[0x64] == 'KM_SUCCESS_ARRIVAL' and names[0x14] == 'KM_ERROR_MOTOR_DISABLED'


def test_flash_states_include_erasing_and_reading():
    s = controller.Controller().flash_memory_states
    assert s[10] == 'FLASH_STATE_ERASING' and s[30] == 'FLASH_STATE_READING'


def test_parse_log():
    payload = b'\x00\x05\x58' + uint32_t2bytes(6) + float2bytes(-1.5)
    log = errors.parse_log(payload, controller.Controller().command_names)
    assert log['identifier'] == 5 and log['command_names'] == 0x58 and log['command_name'] == 'set_speed'
    assert log['error_name'] == 'KM_ERROR_INVALID_PARAM' and log['info'] == bytes2uint32_t(float2bytes(-1.5))


def test_describe():
    log = {'identifier': 0, 'command_names': 0x60, 'command_name': 'run_forward', 'error_codes': 8, 'info': 4}
    text = errors.describe(log)
    assert 'run_forward (0x60): KM_ERROR_INVALID_FLASH_STATE' in text
    assert 'PLAYBACK_DOING' in text and 'remedy:' in text
    over = errors.describe({'identifier': 0xFFFF, 'command_names': 0xFF, 'error_codes': 0x51, 'info': 63})
    assert over.startswith('system notification (0xFF)') and 'temperature=63 deg C' in over
    arrival = errors.describe({'command_names': 0x66, 'error_codes': 100, 'info': bytes2uint32_t(float2bytes(1.0))})
    assert 'position=1.0000 rad' in arrival and 'remedy' not in arrival
    assert 'UNKNOWN_ERROR_0x1234' in errors.describe(0x1234)


def test_is_error():
    assert not errors.is_error(0) and not errors.is_error(100) and errors.is_error(6)
