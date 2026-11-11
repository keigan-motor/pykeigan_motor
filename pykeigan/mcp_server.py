# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) server for KeiganMotor.

Lets an AI assistant (Claude Code, Claude Desktop, etc.) control a KeiganMotor over USB or BLE.

Install:  pip install pykeigan_motor[mcp]          (Python >= 3.10)
Run:      pykeigan-mcp --usb COM3                   (or /dev/ttyUSB0)
          pykeigan-mcp --ble XX:XX:XX:XX:XX:XX
          pykeigan-mcp                              (connect later with the 'connect' tool)
Register: claude mcp add keigan -- pykeigan-mcp --usb COM3

Units of the tools are degrees and rpm (the library itself uses rad and rad/sec).
Safety: speeds and torques above --max-rpm / --max-torque are rejected. The connection is opened
on the first tool call (not at startup), so the server starts even if the Motor is not connected.
"""
import argparse
import math
import sys
import threading
import time
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from pykeigan import utils

DEFAULT_MAX_RPM = 60.0
DEFAULT_MAX_TORQUE = 0.3  # N.m
POLL_INTERVAL = 0.05  # sec. polling interval while waiting for arrival
ARRIVAL_TOLERANCE_DEG = 1.0
ARRIVAL_VELOCITY_RPM = 1.0
LED_STATES = {'off': 0, 'solid': 1, 'flash': 2, 'dim': 3}

INSTRUCTIONS = """\
Controls a KeiganMotor (smart servo motor).
- Units: position/distance in degrees, speed in rpm, torque in N.m. Positive = counter clockwise.
- Call enable_motor before moving. stop_motor decelerates to zero and holds; free_motor removes the excitation.
- Moving the real motor is a physical action: only move it when the user asked for it.
- Speeds above {max_rpm} rpm and torques above {max_torque} N.m are rejected (server limits).
"""

_READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)
_ACTION = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)
_SAFE_ACTION = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True,
                               open_world_hint=False)


class MotorSession(object):
    """Holds one connection to a KeiganMotor, shared by all tool calls."""

    def __init__(self, transport=None, target=None, max_rpm=DEFAULT_MAX_RPM, max_torque=DEFAULT_MAX_TORQUE,
                 timeout=10.0):
        self.default_transport = transport
        self.default_target = target
        self.max_rpm = max_rpm
        self.max_torque = max_torque
        self.timeout = timeout
        self.transport = None
        self.target = None
        self.dev = None
        self._lock = threading.RLock()  # held only for short operations (never while waiting for arrival)
        self._abort = threading.Event()  # set by stop / free / disable to end waiting moves

    # -------------------- connection --------------------
    def connect(self, transport, target):
        with self._lock:
            self._close()
            if transport == 'usb':
                from pykeigan import usbcontroller
                dev = usbcontroller.USBController(target, open_timeout=self.timeout)
            elif transport == 'ble':
                from pykeigan import blecontroller
                dev = blecontroller.BLEController(target, timeout=self.timeout)
            else:
                raise ToolError("transport must be 'usb' or 'ble'")
            dev.enable_continual_motor_measurement()
            self.dev, self.transport, self.target = dev, transport, target
            return dev

    def disconnect(self):
        with self._lock:
            self._close()

    def _close(self):
        dev, self.dev = self.dev, None
        if dev is None:
            return
        try:
            if dev.__class__.__name__ == 'USBController':
                dev.disconnect(reconnect=False)  # do not reopen the port in the background
            else:
                dev.disconnect()
        except Exception:
            pass

    def device(self):
        """The connected controller. Connects with the command line settings on the first call."""
        with self._lock:
            if self.dev is not None and self.dev.is_connected():
                return self.dev
            transport = self.transport or self.default_transport
            target = self.target or self.default_target
            if not transport:
                raise ToolError("Not connected. Call the 'connect' tool (use list_serial_ports / scan_ble "
                                "to find the Motor), or start the server with --usb PORT / --ble ADDRESS.")
            try:
                return self.connect(transport, target)
            except ToolError:
                raise
            except Exception as e:
                raise ToolError('Connecting to {} ({}) failed: {}'.format(target, transport, e)) from e

    def call(self, name, *args):
        """Call a controller method with the I/O lock held, converting errors into ToolError."""
        with self._lock:
            dev = self.device()
            try:
                return getattr(dev, name)(*args)
            except ToolError:
                raise
            except Exception as e:
                raise ToolError('{} failed: {}'.format(name, e)) from e

    # -------------------- limits --------------------
    def check_rpm(self, rpm):
        if not math.isfinite(rpm) or abs(rpm) > self.max_rpm:
            raise ToolError('{} rpm exceeds the server limit {} rpm (--max-rpm).'.format(rpm, self.max_rpm))

    def check_torque(self, torque):
        if not math.isfinite(torque) or abs(torque) > self.max_torque:
            raise ToolError('{} N.m exceeds the server limit {} N.m (--max-torque).'.format(torque, self.max_torque))

    # -------------------- measurement --------------------
    def measurement(self):
        m = self.call('read_motor_measurement')
        return {'position_deg': round(utils.rad2deg(m['position']), 3),
                'velocity_rpm': round(utils.rad_per_sec2rpm(m['velocity']), 3),
                'torque_nm': round(m['torque'], 4)}

    def require_enabled(self):
        status = self.call('read_status')
        if not status.get('motorEnabled'):
            raise ToolError('The motor is disabled. Call enable_motor first.')

    def wait_arrival(self, target_deg, timeout_s):
        """Poll the measurement until the Motor settles at 'target_deg'. Ends early on stop / free / disable."""
        deadline = time.time() + timeout_s
        m = self.measurement()
        while time.time() < deadline:
            if self._abort.wait(POLL_INTERVAL):
                return dict(m, arrived=False, aborted=True)
            m = self.measurement()
            if (abs(m['position_deg'] - target_deg) <= ARRIVAL_TOLERANCE_DEG
                    and abs(m['velocity_rpm']) <= ARRIVAL_VELOCITY_RPM):
                return dict(m, arrived=True)
        return dict(m, arrived=False, timed_out=True,
                    note='Not arrived within {} s. The motor may still be moving.'.format(timeout_s))


def create_server(session):
    """Create the MCP server whose tools operate 'session' (a MotorSession)."""
    server = MCPServer(name='pykeigan', title='KeiganMotor',
                       instructions=INSTRUCTIONS.format(max_rpm=session.max_rpm, max_torque=session.max_torque))

    # -------------------- connection --------------------
    @server.tool(annotations=_READ_ONLY)
    def list_serial_ports() -> list[dict]:
        """List serial ports (USB connection candidates). KeiganMotor appears as a USB-serial (FTDI) device."""
        from serial.tools import list_ports
        return [{'port': p.device, 'description': p.description, 'hwid': p.hwid} for p in list_ports.comports()]

    @server.tool(annotations=_READ_ONLY)
    def scan_ble(timeout_s: float = 5.0) -> list[dict]:
        """Scan KeiganMotors nearby over BLE. Returns name, address and rssi (dBm), strongest first."""
        try:
            from pykeigan import blecontroller
        except ImportError as e:
            raise ToolError('BLE is not installed: pip install pykeigan_motor[ble]') from e
        return blecontroller.scan(timeout=timeout_s)

    @server.tool(annotations=_SAFE_ACTION)
    def connect(transport: Literal['usb', 'ble'], target: str) -> dict:
        """Connect to a KeiganMotor. 'target' is the serial port (e.g. COM3, /dev/ttyUSB0) for usb,
        or the address from scan_ble for ble. Replaces the current connection."""
        session.transport, session.target = transport, target
        session.disconnect()
        session.device()  # connects to transport / target
        return dict(_info(), transport=transport, target=target)

    @server.tool(annotations=_SAFE_ACTION)
    def disconnect() -> str:
        """Close the connection to the motor."""
        session.disconnect()
        return 'disconnected'

    def _info():
        info = {}
        for key, name in (('device_name', 'read_device_name'), ('device_info', 'read_device_info'),
                          ('status', 'read_status')):
            try:
                info[key] = session.call(name)
            except ToolError as e:
                info[key] = 'unavailable ({})'.format(e)
        return info

    @server.tool(annotations=_READ_ONLY)
    def get_motor_info() -> dict:
        """Device name, firmware info and status (motorEnabled, control mode, queue, ...) of the connected motor."""
        session.device()
        return dict(_info(), transport=session.transport, target=session.target,
                    limits={'max_rpm': session.max_rpm, 'max_torque_nm': session.max_torque})

    @server.tool(annotations=_READ_ONLY)
    def read_measurement() -> dict:
        """Current position (deg), velocity (rpm) and torque (N.m)."""
        return session.measurement()

    # -------------------- enable / stop --------------------
    @server.tool(annotations=_SAFE_ACTION)
    def enable_motor() -> str:
        """Enable the motor so that it accepts motion commands."""
        session.call('enable_action')
        return 'enabled'

    @server.tool(annotations=_SAFE_ACTION)
    def disable_motor() -> str:
        """Disable the motor (motion commands are ignored until enable_motor)."""
        session._abort.set()
        session.call('disable_action')
        return 'disabled'

    @server.tool(annotations=_SAFE_ACTION)
    def stop_motor() -> dict:
        """Decelerate to zero speed and hold the position. Use this to stop any motion."""
        session._abort.set()
        session.call('stop_motor')
        return session.measurement()

    @server.tool(annotations=_SAFE_ACTION)
    def free_motor() -> dict:
        """Remove the excitation: the shaft can be turned by hand (no holding torque)."""
        session._abort.set()
        session.call('free_motor')
        return session.measurement()

    # -------------------- motion --------------------
    def _start_motion():
        session.require_enabled()
        session._abort.clear()

    @server.tool(annotations=_ACTION)
    def run_at_velocity(rpm: float) -> dict:
        """Keep rotating at 'rpm' (negative = clockwise) until stop_motor / free_motor is called."""
        session.check_rpm(rpm)
        _start_motion()
        session.call('run_at_velocity', utils.rpm2rad_per_sec(rpm))
        return {'running_at_rpm': rpm}

    @server.tool(annotations=_ACTION)
    def move_to_position(degrees: float, rpm: float = 10.0, wait: bool = True, timeout_s: float = 30.0) -> dict:
        """Move to the absolute position 'degrees' at 'rpm'.
        With wait=True, returns after arrival (or timeout) with the final measurement."""
        session.check_rpm(rpm)
        _start_motion()
        session.call('move_to_pos', utils.deg2rad(degrees), utils.rpm2rad_per_sec(abs(rpm)))
        if not wait:
            return {'target_deg': degrees}
        return dict(session.wait_arrival(degrees, timeout_s), target_deg=degrees)

    @server.tool(annotations=_ACTION)
    def move_by_distance(degrees: float, rpm: float = 10.0, wait: bool = True, timeout_s: float = 30.0) -> dict:
        """Move by 'degrees' relative to the current position (negative = clockwise) at 'rpm'.
        With wait=True, returns after arrival (or timeout) with the final measurement."""
        session.check_rpm(rpm)
        _start_motion()
        start = session.measurement()['position_deg']
        session.call('move_by_dist', utils.deg2rad(degrees), utils.rpm2rad_per_sec(abs(rpm)))
        target = start + degrees
        if not wait:
            return {'target_deg': round(target, 3)}
        return dict(session.wait_arrival(target, timeout_s), target_deg=round(target, 3))

    @server.tool(annotations=_ACTION)
    def hold_torque(torque_nm: float) -> dict:
        """Output a constant torque (N.m, negative = clockwise) until stop_motor / free_motor is called."""
        session.check_torque(torque_nm)
        _start_motion()
        session.call('hold_torque', torque_nm)
        return {'holding_torque_nm': torque_nm}

    @server.tool(annotations=_SAFE_ACTION)
    def preset_position(degrees: float = 0.0) -> dict:
        """Redefine the current position as 'degrees' (0 = set the origin here). The motor does not move.
        Not saved to flash: lost when the motor reboots."""
        session.call('preset_position', utils.deg2rad(degrees))
        time.sleep(0.1)
        return session.measurement()

    # -------------------- LED --------------------
    @server.tool(annotations=_SAFE_ACTION)
    def set_led(state: Literal['off', 'solid', 'flash', 'dim'] = 'solid',
                red: int = 255, green: int = 255, blue: int = 255) -> str:
        """Set the LED of the motor. Colors are 0-255."""
        for c in (red, green, blue):
            if not 0 <= c <= 255:
                raise ToolError('LED colors must be 0-255')
        session.call('set_led', LED_STATES[state], red, green, blue)
        return 'ok'

    return server


def _parse_http(value):
    host, _, port = value.rpartition(':')
    return (host or '127.0.0.1'), int(port)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pykeigan-mcp', description='MCP server for KeiganMotor')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--usb', metavar='PORT', help='serial port of the motor, e.g. COM3 or /dev/ttyUSB0')
    target.add_argument('--ble', metavar='ADDRESS', help='BLE address of the motor (see scan_ble)')
    parser.add_argument('--max-rpm', type=float, default=DEFAULT_MAX_RPM,
                        help='reject speeds above this [rpm] (default: %(default)s)')
    parser.add_argument('--max-torque', type=float, default=DEFAULT_MAX_TORQUE,
                        help='reject torques above this [N.m] (default: %(default)s)')
    parser.add_argument('--timeout', type=float, default=10.0, help='connection timeout [sec] (default: %(default)s)')
    parser.add_argument('--http', metavar='[HOST:]PORT',
                        help='serve over Streamable HTTP instead of stdio (e.g. 8000 or 0.0.0.0:8000). '
                             'No authentication: expose it only on a trusted network.')
    args = parser.parse_args(argv)

    transport = 'usb' if args.usb else 'ble' if args.ble else None
    session = MotorSession(transport, args.usb or args.ble, args.max_rpm, args.max_torque, args.timeout)
    server = create_server(session)
    try:
        if args.http:
            host, port = _parse_http(args.http)
            if host not in ('127.0.0.1', 'localhost', '::1'):
                print('WARNING: serving without authentication on {}:{}'.format(host, port), file=sys.stderr)
            server.run('streamable-http', host=host, port=port)
        else:
            server.run('stdio')
    finally:
        session.disconnect()


if __name__ == '__main__':
    main()
