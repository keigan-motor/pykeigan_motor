# -*- coding: utf-8 -*-
"""
Error codes of the log notifications (on_motor_log_cb / on_motor_error_cb), and how to deal with them.

The Motor sends a log notification [identifier, command, error_code, info] for each command it
receives (while the response setting is on, which is the default). The controllers pass it to the
callbacks as a dict::

    {'identifier': 0x0000, 'command_names': 0x58, 'error_codes': 6, 'info': 0x7fc00000,
     'command_name': 'set_speed', 'error_name': 'KM_ERROR_INVALID_PARAM'}

('command_names' and 'error_codes' are the numbers, kept with these names for compatibility.)

Use describe(log) to get a readable message with the cause and the remedy, e.g.::

    from pykeigan import errors
    dev.on_motor_error_cb = lambda log: print(errors.describe(log))

Notifications that are not replies to a command (over heat, watchdog, BLE stack error) have
the identifier 0xFFFF and the command 0xFF. On an error the LED of the Motor flashes red and blue for a moment.

The table is based on km_error.h of the KeiganMotor firmware (KM-1).
"""
from collections import namedtuple
import struct

ErrorInfo = namedtuple('ErrorInfo', ['code', 'name', 'summary', 'causes', 'remedy', 'info'])
ErrorInfo.__doc__ = """
Description of an error code.

- code: the number (int)
- name: the firmware name, e.g. 'KM_ERROR_INVALID_PARAM'
- summary: one line description
- causes: tuple of typical causes
- remedy: what to do
- info: meaning of the 'info' value of the log notification ('' if not used)
"""

SYSTEM_IDENTIFIER = 0xFFFF
"""Identifier of the notifications that are not replies to a command."""
SYSTEM_COMMAND = 0xFF
"""Command number of the notifications that are not replies to a command."""

SUCCESS = 0x00
SUCCESS_ARRIVAL = 0x64

FLASH_STATE_NAMES = {
    0: 'READY', 1: 'TEACHING_PREPARE', 2: 'TEACHING_DOING', 3: 'PLAYBACK_PREPARE', 4: 'PLAYBACK_DOING',
    5: 'PLAYBACK_PAUSING', 6: 'TASKSET_RECORDING', 7: 'TASKSET_DOING', 8: 'TASKSET_PAUSING',
    10: 'ERASING', 20: 'IMU', 30: 'READING',
}

_RESERVED = ('Not sent by the current firmware (reserved).',)
_RESERVED_REMEDY = ('Turn the Motor off and on. If it continues, update the firmware and contact Keigan '
                    'with the command, the error code and the info value.')


def _e(code, name, summary, causes, remedy, info=''):
    return code, ErrorInfo(code, name, summary, tuple(causes), remedy, info)


ERRORS = dict([
    _e(0x00, 'KM_SUCCESS', 'The command was accepted.', (), 'Nothing to do.',
       'Usually 0. write_motion_position(): number of recorded positions. enable_check_sum(): the set value.'),
    _e(0x64, 'KM_SUCCESS_ARRIVAL', 'The Motor arrived at the target position (position arrival notification).',
       ('Enabled with set_notify_pos_arrival_settings().',),
       'Nothing to do. It is sent once per position command after it settles within the tolerance.',
       'Arrival position [rad] (float). describe() decodes it.'),

    _e(0x01, 'KM_ERROR_INTERNAL', 'Internal error.', _RESERVED, _RESERVED_REMEDY),
    _e(0x02, 'KM_ERROR_NO_MEM', 'No memory for the operation.', _RESERVED, _RESERVED_REMEDY),
    _e(0x03, 'KM_ERROR_NOT_FOUND', 'Nothing is recorded at the index.',
       ('prepare_playback_motion() / read_motion() with an index where no motion is recorded.',
        'start_doing_taskset() with an index where no taskset is recorded.'),
       'Check the index. Record it first (prepare_teaching_motion() / start_recording_taskset()). '
       'Motion indexes are 0-19, taskset indexes are 0-49.',
       'The index (0 if not given).'),
    _e(0x04, 'KM_ERROR_NOT_SUPPORTED', 'The operation is not supported in the current settings.',
       ('Not notified by the current firmware. enable_continual_imu_measurement() is ignored silently while BLE '
        'is disabled and the Linkage / micro:bit mode is on (the IMU values cannot be notified).',),
       'If no IMU values arrive, enable BLE with set_interface(), or turn off the Linkage / micro:bit mode.'),
    _e(0x05, 'KM_ERROR_INVALID_COMMAND', 'Invalid command.',
       ('Defined, but the current firmware ignores unknown commands without a notification.',),
       'If a command has no effect and no log is notified, the firmware may be too old for the command. '
       'Update the firmware (read_device_info() shows the version).'),
    _e(0x06, 'KM_ERROR_INVALID_PARAM', 'An argument is out of range or malformed. The command was not executed.',
       ('Too short command (the argument is missing).',
        'set_curve_type(): not 0 (none), 1 (trapezoid) or 10 (none, direct).',
        'set_teaching_interval() / set_playback_interval(): not 2-1000 [ms].',
        'set_motor_measurement_interval() / set_imu_measurement_interval(): too large setting number.',
        'set_max_torque(): negative value.',
        'set_notify_pos_arrival_settings(): isEnabled not 0/1, or tolerance <= 0.',
        'set_safe_run_settings(): isEnabled not 0/1.',
        'set_baud_rate(): not 0-5.',
        'set_autostart_setting(): mode not 0, 1, 2, 0x11 or 0x12.',
        'enable_check_sum(): not 0/1.',
        'prepare_playback_motion(): option not 0-3.'),
       'Check the argument and its unit (rad, rad/sec, N.m, ms). Note that set_acc() / set_dec() with 0 or a '
       'negative value is ignored without a notification. The firmware reports the errors of set_dec() as '
       'set_acc (0x07) and of set_position_d() as set_position_i (0x1F).',
       'The received argument as 4 raw bytes (big endian). For float arguments describe() decodes it as a float.'),
    _e(0x07, 'KM_ERROR_STORAGE_FULL', 'The storage area is not empty or is full.',
       ('prepare_teaching_motion() / start_teaching_motion() with an index where a motion is already recorded.',
        'start_recording_taskset() with an index where a taskset is already recorded.',
        'write_motion_position(): the motion area is full.'),
       'Erase it first with erase_motion(index) / erase_taskset(index) (or use another index). '
       'Erasing takes some time: prepare_teaching_motion() of the same index waits for it, '
       'but other flash operations fail with KM_ERROR_INVALID_FLASH_STATE (info=10) until it finishes.'),
    _e(0x08, 'KM_ERROR_INVALID_FLASH_STATE', 'Not allowed in the current flash memory state '
       '(teaching, playback, taskset, erasing, IMU measurement, ...).',
       ('Run / move commands during playback of a motion (or while preparing it, or erasing).',
        'Teaching / playback / taskset / erase / read commands while another one of them is running.',
        'start_teaching_motion_from_prep() without prepare_teaching_motion().',
        'enable / disable_continual_imu_measurement() while teaching, playback or taskset is running.',
        'read_motion() through BLE (it is supported only through USB).'),
       'Check the state with read_status()[\'flash_memory_state\']. Stop the running operation '
       '(stop_playback_motion(), stop_teaching_motion(), stop_recording_taskset(), stop_doing_taskset()) or wait '
       'for it to finish (erasing), then send the command again.',
       'The current flash memory state. describe() shows its name.'),
    _e(0x09, 'KM_ERROR_INVALID_LENGTH', 'Invalid data length.',
       ('Too long name (e.g. the motor model name).',),
       'Shorten the data.'),
    _e(0x0A, 'KM_ERROR_INVALID_CHECKSUM', 'CRC16 of the command is wrong. The command was not executed.',
       ('The checksum is enabled (enable_check_sum(1)) and a frame was corrupted on the line.',
        'enable_check_sum() (always checked) received a corrupted frame.'),
       'Send the command again. If it happens often, check the cable / radio environment and the baud rate. '
       'Disable the checksum with enable_check_sum(0) if it is not needed.'),
    _e(0x0D, 'KM_ERROR_TIMEOUT', 'The operation timed out.', _RESERVED, _RESERVED_REMEDY),
    _e(0x0F, 'KM_ERROR_FORBIDDEN', 'Forbidden operation.',
       ('set_interface() that disables BLE, USB (UART) and I2C at the same time '
        '(the Motor could not be controlled any more).',
        'Factory-only commands.'),
       'Keep at least one of BLE, USB or I2C enabled in set_interface().'),
    _e(0x10, 'KM_ERROR_INVALID_ADDR', 'The index (address) is out of range.',
       ('Motion index >= 20 (prepare_teaching_motion(), prepare_playback_motion(), read_motion(), ...).',
        'Taskset index >= 50 (start_recording_taskset(), start_doing_taskset(), erase_taskset(), ...).'),
       'Use motion index 0-19 and taskset index 0-49.',
       'The index (0 for some commands).'),
    _e(0x11, 'KM_ERROR_BUSY', 'Busy.', _RESERVED, 'Wait a moment and send the command again.'),
    _e(0x12, 'KM_ERROR_RESOURCE', 'Not enough resources for the operation.', _RESERVED, _RESERVED_REMEDY),
    _e(0x14, 'KM_ERROR_MOTOR_DISABLED', 'The motor action is disabled. The command was not executed.',
       ('enable_action() has not been called after power on (the action is disabled at power on, '
        'unless set by the autostart setting).',
        'disable_action() was called.',
        'The Motor disabled itself: over heat / over current (KM_ERROR_OVER_HEAT), '
        'safe run timeout with the "disable" option (set_safe_run_settings()), '
        'end of a playback started by the button, or end of teaching.'),
       'Call enable_action() and send the command again. If it was disabled by KM_ERROR_OVER_HEAT, '
       'remove the cause first. read_status()[\'motorEnabled\'] shows the state.'),
    _e(0x3C, 'KM_ERROR_DEVICE_DRIVER', 'Error of the motor driver.', _RESERVED, _RESERVED_REMEDY),
    _e(0x3D, 'KM_ERROR_DEVICE_FLASH', 'Error of the flash memory.', _RESERVED, _RESERVED_REMEDY),
    _e(0x3E, 'KM_ERROR_DEVICE_LED', 'Error of the LED.', _RESERVED, _RESERVED_REMEDY),
    _e(0x3F, 'KM_ERROR_DEVICE_IMU', 'Error of the IMU (no response from the sensor).',
       ('Not notified by the current firmware (the IMU check at startup is only logged internally).',),
       'If no IMU values arrive although enable_continual_imu_measurement() was called, turn the Motor off and on. '
       'If it continues, the IMU may be broken: contact Keigan.'),
    _e(0x46, 'KM_ERROR_NRF_DEVICE', 'Error of the BLE stack (nRF SoftDevice) when sending a notification.',
       ('Too many notifications for the connection (e.g. a short measurement interval with a weak signal).',),
       'Make the measurement interval longer, improve the radio environment (see the BLE radio page), '
       'and reconnect. If it continues, turn the Motor off and on.',
       'The nRF SDK error code.'),
    _e(0x50, 'KM_ERROR_WDT_EVENT', 'Watchdog timer: the firmware stopped responding and the Motor restarts now.',
       ('The main loop of the firmware stopped for about 60 ms (the notification may not arrive before the restart).',),
       'The Motor restarts: the connection is lost and the settings not saved by save_all_registers() are lost. '
       'Reconnect and set them again. If it happens repeatedly, note what the Motor was doing, update the '
       'firmware and contact Keigan.'),
    _e(0x51, 'KM_ERROR_OVER_HEAT', 'Over heat or over current. The Motor disabled the action '
       '(the LED blinks red and orange).',
       ('The temperature inside the Motor exceeded 60 deg C for more than 2 minutes '
        '(or already at power on: then it is notified but not disabled).',
        'The q-axis current exceeded 5 A for about 3 minutes in total (continuous overload).'),
       'Stop and let the Motor cool down. Reduce the load, the duty or the torque (set_max_torque(), '
       'set_limit_current()), and check that nothing blocks the rotation. Then call enable_action() again.',
       'The temperature [deg C] at the time of the notification.'),
])
"""Descriptions of the error codes, keyed by the code number (ErrorInfo)."""

_FLOAT_INFO = {0x06, 0x64}


def lookup(code):
    """Return the ErrorInfo of 'code'. Unknown codes (e.g. newer firmware) get a generic description."""
    try:
        return ERRORS[code]
    except KeyError:
        return ErrorInfo(code, 'UNKNOWN_ERROR_0x{:X}'.format(code), 'Unknown error code {}.'.format(code), (),
                         'The firmware may be newer than this library. Update pykeigan_motor.', '')


def is_error(code):
    """True if 'code' is an error (not KM_SUCCESS or the position arrival notification)."""
    return code not in (SUCCESS, SUCCESS_ARRIVAL)


def _as_float(info):
    return struct.unpack('>f', struct.pack('>I', info & 0xFFFFFFFF))[0]


def info_text(code, info):
    """Readable meaning of the 'info' value of a log notification, or None."""
    if info is None:
        return None
    if code == SUCCESS:
        return None if info == 0 else 'info={}'.format(info)
    if code in _FLOAT_INFO:
        f = _as_float(info)
        if code == SUCCESS_ARRIVAL:
            return 'position={:.4f} rad'.format(f)
        return 'received value=0x{:08X} (as float: {!r})'.format(info, f)
    if code == 0x08:
        return 'flash memory state={} ({})'.format(info, FLASH_STATE_NAMES.get(info, 'unknown'))
    if code in (0x03, 0x10):
        return 'index={}'.format(info)
    if code == 0x51:
        return 'temperature={} deg C'.format(info if info < 0x80000000 else info - 0x100000000)
    if code == 0x46:
        return 'nRF error code=0x{:X}'.format(info)
    return None if info == 0 else 'info={}'.format(info)


def describe(log, command_names=None, verbose=True):
    """
    Readable message of a log notification 'log' (the dict passed to on_motor_log_cb), or of an error code (int).

    With verbose=True (default) the causes and the remedy are included.
    'command_names' (e.g. dev.command_names) is used if the log has no 'command_name'.
    """
    if isinstance(log, int):
        log = {'error_codes': log}
    code = log.get('error_codes', 0)
    e = lookup(code)
    cmd = log.get('command_names')
    if cmd is None:
        head = e.name
    else:
        name = log.get('command_name') or (command_names or {}).get(cmd)
        if cmd == SYSTEM_COMMAND and log.get('identifier') in (None, SYSTEM_IDENTIFIER):
            name = 'system notification'
        head = '{} (0x{:02X}): {}'.format(name or 'command', cmd, e.name)
    lines = [head + ' - ' + e.summary]
    it = info_text(code, log.get('info'))
    if it:
        lines[0] += ' [' + it + ']'
    if verbose and is_error(code):
        for c in e.causes:
            lines.append('  cause: ' + c)
        lines.append('  remedy: ' + e.remedy)
    return '\n'.join(lines)


def parse_log(payload, command_names=None):
    """
    Make the log dict from the payload of a log notification (datatype 0xBE):
    identifier (2 bytes), command (1 byte), error code (4 bytes), info (4 bytes), all big endian.
    """
    identifier = struct.unpack('>H', bytes(payload[0:2]))[0]
    cmd = payload[2]
    code = struct.unpack('>I', bytes(payload[3:7]))[0]
    info = struct.unpack('>I', bytes(payload[7:11]))[0] if len(payload) >= 11 else None
    return {'identifier': identifier, 'command_names': cmd, 'error_codes': code, 'info': info,
            'command_name': (command_names or {}).get(cmd), 'error_name': lookup(code).name}

