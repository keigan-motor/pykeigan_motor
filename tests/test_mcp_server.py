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
        def record(*args):
            self.calls.append((name,) + args)
        return record

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
