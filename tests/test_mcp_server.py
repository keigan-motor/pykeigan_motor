# -*- coding: utf-8 -*-
"""Tests of the MCP server tools with a fake controller (no motor needed). Requires: pip install mcp"""
import math

import pytest

pytest.importorskip('mcp')
import anyio
from mcp.server.mcpserver.exceptions import ToolError

from pykeigan import mcp_server


class FakeMotor(object):
    """Minimal stand-in for USBController / BLEController. Moves arrive instantly."""

    def __init__(self):
        self.calls = []
        self.enabled = False
        self.position = 0.0  # rad
        self.velocity = 0.0  # rad/sec

    def is_connected(self):
        return True

    def disconnect(self, reconnect=False):
        self.calls.append(('disconnect',))

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        registers = self.__dict__.setdefault('registers', {})

        def record(*args):
            self.calls.append((name,) + args)
            if name.startswith('set_') and args:
                registers[name[4:]] = args[0]
            elif name.startswith('read_'):
                return registers.get(name[5:], 0.0)
        return record

    def read_imu_measurement(self):
        return {'accel_x': 0.0, 'accel_y': 0.0, 'accel_z': 1.0, 'temp': 30.0,
                'gyro_x': math.radians(10), 'gyro_y': 0.0, 'gyro_z': 0.0, 'received_unix_time': 0}

    def enable_action(self):
        self.calls.append(('enable_action',))
        self.enabled = True

    def disable_action(self):
        self.calls.append(('disable_action',))
        self.enabled = False

    def read_status(self):
        return {'motorEnabled': int(self.enabled)}

    def read_device_name(self):
        return 'KM-1S fake'

    def read_device_info(self):
        return 'fw 3.00'

    def read_motor_measurement(self):
        return {'position': self.position, 'velocity': self.velocity, 'torque': 0.01, 'received_unix_time': 0}

    def move_to_pos(self, position, speed):
        self.calls.append(('move_to_pos', position, speed))
        self.position = position

    def move_by_dist(self, distance, speed):
        self.calls.append(('move_by_dist', distance, speed))
        self.position += distance


@pytest.fixture
def env():
    session = mcp_server.MotorSession('usb', 'FAKE', max_rpm=60, max_torque=0.3)
    motor = FakeMotor()
    session.connect = lambda transport, target: setattr(session, 'dev', motor) or motor
    return mcp_server.create_server(session), motor


def call(server, name, **args):
    result = anyio.run(lambda: server.call_tool(name, args))
    return result


def structured(result):
    return result.structured_content if hasattr(result, 'structured_content') else result


def test_tools_registered(env):
    server, _ = env
    names = {t.name for t in anyio.run(server.list_tools)}
    for n in ('connect', 'move_to_position', 'move_by_distance', 'run_at_velocity', 'stop_motor',
              'free_motor', 'enable_motor', 'read_measurement', 'get_motor_info', 'set_led'):
        assert n in names


def test_move_requires_enable(env):
    server, motor = env
    with pytest.raises(ToolError, match='enable_motor'):
        call(server, 'move_to_position', degrees=90)
    assert not any(c[0] == 'move_to_pos' for c in motor.calls)


def test_move_to_position_units_and_wait(env):
    server, motor = env
    call(server, 'enable_motor')
    call(server, 'move_to_position', degrees=90, rpm=30)
    name, pos, speed = [c for c in motor.calls if c[0] == 'move_to_pos'][0]
    assert pos == pytest.approx(math.pi / 2)
    assert speed == pytest.approx(30 * 2 * math.pi / 60)
    m = call(server, 'read_measurement')
    assert '90.0' in str(m)


def test_move_by_distance_target(env):
    server, motor = env
    motor.position = math.radians(10)
    call(server, 'enable_motor')
    result = str(call(server, 'move_by_distance', degrees=-30, rpm=10))
    assert "'arrived': True" in result or '"arrived": true' in result
    assert motor.position == pytest.approx(math.radians(-20))


def test_limits(env):
    server, motor = env
    call(server, 'enable_motor')
    with pytest.raises(ToolError, match='max-rpm'):
        call(server, 'run_at_velocity', rpm=61)
    with pytest.raises(ToolError, match='max-rpm'):
        call(server, 'move_to_position', degrees=10, rpm=-100)
    with pytest.raises(ToolError, match='max-torque'):
        call(server, 'hold_torque', torque_nm=0.5)
    assert not any(c[0] in ('run_at_velocity', 'move_to_pos', 'hold_torque') for c in motor.calls)


def test_stop_and_led(env):
    server, motor = env
    call(server, 'stop_motor')
    call(server, 'set_led', state='flash', red=255, green=0, blue=0)
    assert ('stop_motor',) in motor.calls
    assert ('set_led', 2, 255, 0, 0) in motor.calls


def test_not_connected_message():
    server = mcp_server.create_server(mcp_server.MotorSession())
    with pytest.raises(ToolError, match="connect"):
        call(server, 'read_measurement')


def test_update_settings_units_and_limits(env):
    server, motor = env
    result = str(call(server, 'update_settings', max_torque_nm=0.1, max_speed_rpm=20, acc_rpm_per_s=60,
                      curve='trapezoid'))
    assert ('set_max_torque', 0.1) in motor.calls
    assert motor.registers['max_speed'] == pytest.approx(20 * 2 * math.pi / 60)
    assert motor.registers['curve_type'] == 1
    assert '20.0' in result  # read back in rpm
    with pytest.raises(ToolError, match='max-torque'):
        call(server, 'update_settings', max_torque_nm=0.5)
    with pytest.raises(ToolError, match='max-rpm'):
        call(server, 'update_settings', max_speed_rpm=100)
    with pytest.raises(ToolError, match='No setting'):
        call(server, 'update_settings')


def test_read_settings_and_pid(env):
    server, motor = env
    call(server, 'set_pid_gains', loop='speed', p=12.5)
    assert ('set_speed_p', 12.5) in motor.calls
    result = str(call(server, 'read_settings'))
    assert 'max_torque_nm' in result and '12.5' in result


def test_imu_taskset_queue_errors(env):
    server, motor = env
    assert '10.0' in str(call(server, 'read_imu'))
    assert ('disable_continual_imu_measurement',) in motor.calls
    call(server, 'taskset', action='start_recording', index=3)
    call(server, 'queue', action='wait', wait_ms=500)
    assert ('start_recording_taskset', 3) in motor.calls
    assert ('wait_queue', 500) in motor.calls
    with pytest.raises(ToolError, match='enable_motor'):
        call(server, 'taskset', action='run', index=3)


def test_get_errors():
    session = mcp_server.MotorSession()
    server = mcp_server.create_server(session)
    session._on_error({'identifier': 0, 'command_names': 0x58, 'error_codes': 6, 'info': 0,
                       'command_name': 'set_speed', 'error_name': 'KM_ERROR_INVALID_PARAM'})
    result = str(call(server, 'get_errors', clear=True))
    assert 'KM_ERROR_INVALID_PARAM' in result and 'set_speed' in result
    assert not session.errors


def test_hold_position_uses_relative_zero_move(env):
    server, motor = env
    motor.position = math.radians(-42)
    with pytest.raises(ToolError, match='enable_motor'):
        call(server, 'hold_position')
    call(server, 'enable_motor')
    call(server, 'update_settings', max_torque_nm=0.1)
    result = str(call(server, 'hold_position'))
    name, distance, speed = [c for c in motor.calls if c[0] == 'move_by_dist'][0]
    assert distance == 0.0
    assert '-42.0' in result and '0.1' in result
    assert not any(c[0] == 'move_to_pos' for c in motor.calls)


def test_preset_and_read_position_offset(env):
    server, motor = env

    def preset(position):  # the motor adds the change to the offset (register 0x5B)
        motor.calls.append(('preset_position', position))
        offset = motor.registers.get('position_offset', 0.0)
        motor.registers['position_offset'] = offset + position - motor.position
        motor.position = position
    motor.preset_position = preset
    motor.position = math.radians(30)
    assert '0.0' in str(call(server, 'read_position_offset'))
    result = str(call(server, 'preset_position', degrees=0))
    assert "'position_offset_deg': -30.0" in result or '"position_offset_deg": -30.0' in result
    assert '-30.0' in str(call(server, 'read_position_offset'))
