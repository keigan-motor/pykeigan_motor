# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) server for KeiganMotor.

Lets an AI assistant (Claude Code, Claude Desktop, etc.) control a KeiganMotor over USB or BLE.

Install:  pip install pykeigan_motor[mcp]          (Python >= 3.10)
Run:      pykeigan-mcp --usb COM3                   (or /dev/ttyUSB0)
          pykeigan-mcp --ble XX:XX:XX:XX:XX:XX
          pykeigan-mcp                              (connect later with the 'connect' tool)
Register: claude mcp add keiganmotor -- pykeigan-mcp --usb COM3

Units of the tools are degrees and rpm (the library itself uses rad and rad/sec).
Safety: speeds and torques above --max-rpm / --max-torque are rejected. The connection is opened
on the first tool call (not at startup), so the server starts even if the Motor is not connected.
"""
import argparse
import collections
import math
import sys
import threading
import time
from typing import Literal

from pykeigan._deps import MissingDependencyError, require_mcp, require_pyserial
require_mcp()
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from pykeigan import errors, utils

DEFAULT_MAX_RPM = 60.0
DEFAULT_MAX_TORQUE = 0.3  # N.m
POLL_INTERVAL = 0.05  # sec. polling interval while waiting for arrival
ARRIVAL_TOLERANCE_DEG = 1.0
ARRIVAL_VELOCITY_RPM = 1.0
LED_STATES = {'off': 0, 'solid': 1, 'flash': 2, 'dim': 3}
CURVE_TYPES = {'none': 0, 'trapezoid': 1, 'direct': 10}
SAFE_RUN_ACTIONS = {'free': 0, 'disable': 1, 'stop': 2, 'hold_position': 3}
PID_SETTERS = {'q_current': ('set_qcurrent_p', 'set_qcurrent_i', 'set_qcurrent_d'),
               'speed': ('set_speed_p', 'set_speed_i', 'set_speed_d'),
               'position': ('set_position_p', 'set_position_i', 'set_position_d')}

INSTRUCTIONS = """\
Controls a KeiganMotor (smart servo motor).
- Units: position/distance in degrees, speed in rpm, acceleration in rpm/s, torque in N.m. Positive = counter clockwise.
- Call enable_motor before moving. free_motor removes the excitation.
- stop_motor decelerates to zero and keeps 0 rpm (velocity control). It does NOT hold the position: if the shaft
  is turned by an external force, it does not come back.
- To fix / hold the motor at its current position (e.g. "その場で固定して"), use hold_position (position control).
  The holding force is limited by the max torque setting (read_settings): a stronger external force overcomes it.
- Moving the real motor is a physical action: only move it when the user asked for it.
- Speeds above {max_rpm} rpm and torques above {max_torque} N.m are rejected (server limits).
- update_settings / set_pid_gains change the RAM only (lost on reboot). save_settings_to_flash makes them
  permanent: call it only when the user asked to save.
- If a command seems to have no effect, check get_errors.
"""

_READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)
_DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=False)
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
        self.errors = collections.deque(maxlen=50)  # recent error logs from the Motor

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
            dev.on_motor_error_cb = self._on_error
            dev.enable_continual_motor_measurement()
            self.dev, self.transport, self.target = dev, transport, target
            return dev

    def _on_error(self, log):
        """Error log notifications from the Motor (called from the receiving thread)."""
        try:
            text = errors.describe(log)
        except Exception:
            text = repr(log)
        self.errors.append({'time': time.strftime('%H:%M:%S'), 'command': log.get('command_name'),
                            'error': log.get('error_name'), 'message': text})

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
    server = MCPServer(name='keiganmotor', title='KeiganMotor',
                       instructions=INSTRUCTIONS.format(max_rpm=session.max_rpm, max_torque=session.max_torque))

    # -------------------- connection --------------------
    @server.tool(annotations=_READ_ONLY)
    def list_serial_ports() -> list[dict]:
        """List serial ports (USB connection candidates).
        KeiganMotor uses an FTDI USB-serial chip: vid 0403 ('likely_keigan_motor': true). Bluetooth ports are not motors.
        If no port is a likely KeiganMotor, the Motor is not visible to the OS: this is usually a USB hardware
        problem (USB hub, charge-only or damaged cable, Motor power), tell the user to connect directly with another cable."""
        try:
            require_pyserial()
        except MissingDependencyError as e:
            raise ToolError(str(e)) from None
        from serial.tools import list_ports
        ports = []
        for p in list_ports.comports():
            vid = '{:04X}'.format(p.vid) if p.vid is not None else None
            pid = '{:04X}'.format(p.pid) if p.pid is not None else None
            ports.append({'port': p.device, 'description': p.description, 'vid': vid, 'pid': pid,
                          'likely_keigan_motor': vid == '0403'})
        return ports

    @server.tool(annotations=_READ_ONLY)
    def scan_ble(timeout_s: float = 5.0) -> list[dict]:
        """Scan KeiganMotors nearby over BLE. Returns name, address and rssi (dBm), strongest first."""
        try:
            from pykeigan import blecontroller
        except MissingDependencyError as e:
            raise ToolError(str(e)) from None
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
        """Decelerate to zero speed and keep 0 rpm (velocity control). Use this to stop any motion.
        It does NOT hold the position: if the shaft is turned by an external force, it does not come back.
        Use hold_position to fix the motor at its position."""
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
    def hold_position() -> dict:
        """Fix the motor at its current position (position control): if the shaft is turned by an external
        force, it comes back. Use this for "hold / fix it here". The holding force is limited by the max torque
        setting (max_torque_nm in the result); a stronger force overcomes it."""
        _start_motion()
        before = session.measurement()
        # a relative move of 0 targets the current position without reading it first (no error from a delay)
        session.call('move_by_dist', 0.0, utils.rpm2rad_per_sec(min(10.0, session.max_rpm)))
        time.sleep(0.3)
        after = session.measurement()
        result = {'holding_at_deg': after['position_deg'], 'position_before_deg': before['position_deg'],
                  'max_torque_nm': _read('read_max_torque', lambda v: round(v, 4))}
        if abs(after['position_deg'] - before['position_deg']) > 2.0:
            result['warning'] = ('The motor moved {:.1f} deg after the hold command: it may be moving to the previous '
                                 'target instead of holding here. Call stop_motor if this is not intended.'
                                 ).format(after['position_deg'] - before['position_deg'])
        return result

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
        The motor adds the change to its position offset (see read_position_offset).
        The offset is kept in RAM: lost when the motor reboots (saved to flash only from motor firmware 3.00)."""
        offset_before = _offset_deg()
        session.call('preset_position', utils.deg2rad(degrees))
        time.sleep(0.1)
        return dict(session.measurement(), position_offset_deg=_offset_deg(),
                    position_offset_before_deg=offset_before)

    def _offset_deg():
        return _read('read_position_offset', lambda v: round(utils.rad2deg(v), 3))

    @server.tool(annotations=_READ_ONLY)
    def read_position_offset() -> dict:
        """Where the origin is: the position offset (register 0x5B) accumulated by preset_position, in degrees.
        0 means no preset since power-on (the position is the motor's own coordinate). Use this for
        "what is the current origin?". Returns the current position too."""
        return dict(session.measurement(), position_offset_deg=_offset_deg())

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

    # -------------------- settings --------------------
    def _read(name, convert=None):
        try:
            value = session.call(name)
        except ToolError as e:
            return 'unavailable ({})'.format(e)
        return convert(value) if convert else value

    def _rpm(v):
        return round(utils.rad_per_sec2rpm(v), 3)

    def _curve_name(v):
        return {n: k for k, n in CURVE_TYPES.items()}.get(v, v)

    @server.tool(annotations=_READ_ONLY)
    def read_settings() -> dict:
        """Read the motion settings, PID gains, LED color and measurement intervals of the motor."""
        session.device()
        return {
            'max_speed_rpm': _read('read_max_speed', _rpm),
            'min_speed_rpm': _read('read_min_speed', _rpm),
            'acc_rpm_per_s': _read('read_acc', _rpm),
            'dec_rpm_per_s': _read('read_dec', _rpm),
            'curve': _read('read_curve_type', _curve_name),
            'max_torque_nm': _read('read_max_torque', lambda v: round(v, 4)),
            'pid': {loop: {'p': _read('read_{}_p'.format(r)), 'i': _read('read_{}_i'.format(r)),
                           'd': _read('read_{}_d'.format(r))}
                    for loop, r in (('q_current', 'qcurrent'), ('speed', 'speed'), ('position', 'position'))},
            'pos_control_threshold': _read('read_pos_control_threshold'),
            'position_offset_deg': _offset_deg(),
            'own_color_rgb': _read('read_own_color'),
            'motor_measurement_interval_code': _read('read_motor_measurement_interval'),
            'imu_measurement_interval_code': _read('read_imu_measurement_interval'),
            'server_limits': {'max_rpm': session.max_rpm, 'max_torque_nm': session.max_torque},
        }

    @server.tool(annotations=_SAFE_ACTION)
    def update_settings(max_torque_nm: float | None = None, max_speed_rpm: float | None = None,
                        min_speed_rpm: float | None = None, acc_rpm_per_s: float | None = None,
                        dec_rpm_per_s: float | None = None,
                        curve: Literal['trapezoid', 'none', 'direct'] | None = None) -> dict:
        """Change motion settings of the motor (only the given ones). RAM only: lost on reboot unless
        save_settings_to_flash is called. max_torque_nm limits the torque of every motion.
        curve: 'trapezoid' = accelerate / decelerate with acc / dec, 'none' = no motion control,
        'direct' = direct position control. Returns the values read back."""
        values = {'max_torque_nm': max_torque_nm, 'max_speed_rpm': max_speed_rpm, 'min_speed_rpm': min_speed_rpm,
                  'acc_rpm_per_s': acc_rpm_per_s, 'dec_rpm_per_s': dec_rpm_per_s}
        for key, v in values.items():
            if v is not None and (not math.isfinite(v) or v < 0):
                raise ToolError('{} must be a positive number'.format(key))
        if max_torque_nm is not None:
            session.check_torque(max_torque_nm)
        for v in (max_speed_rpm, min_speed_rpm):
            if v is not None:
                session.check_rpm(v)
        result = {}
        if max_torque_nm is not None:
            session.call('set_max_torque', max_torque_nm)
            result['max_torque_nm'] = _read('read_max_torque', lambda v: round(v, 4))
        for key, setter, reader in (('max_speed_rpm', 'set_max_speed', 'read_max_speed'),
                                    ('min_speed_rpm', 'set_min_speed', 'read_min_speed'),
                                    ('acc_rpm_per_s', 'set_acc', 'read_acc'),
                                    ('dec_rpm_per_s', 'set_dec', 'read_dec')):
            if values[key] is not None:
                session.call(setter, utils.rpm2rad_per_sec(values[key]))
                result[key] = _read(reader, _rpm)
        if curve is not None:
            session.call('set_curve_type', CURVE_TYPES[curve])
            result['curve'] = _read('read_curve_type', _curve_name)
        if not result:
            raise ToolError('No setting given')
        return result

    @server.tool(annotations=_SAFE_ACTION)
    def set_pid_gains(loop: Literal['q_current', 'speed', 'position'], p: float | None = None,
                      i: float | None = None, d: float | None = None) -> dict:
        """Change the PID gains of a control loop (only the given ones; RAM only).
        Wrong gains can make the motor oscillate: change them in small steps. reset_all_pid restores the defaults."""
        given = [(name, v) for name, v in zip(PID_SETTERS[loop], (p, i, d)) if v is not None]
        if not given:
            raise ToolError('Give at least one of p, i, d')
        for name, v in given:
            if not math.isfinite(v) or v < 0:
                raise ToolError('Gains must be positive numbers')
            session.call(name, v)
        r = 'qcurrent' if loop == 'q_current' else loop
        return {'loop': loop, 'p': _read('read_{}_p'.format(r)), 'i': _read('read_{}_i'.format(r)),
                'd': _read('read_{}_d'.format(r))}

    @server.tool(annotations=_SAFE_ACTION)
    def reset_all_pid() -> str:
        """Restore all the PID gains to the firmware defaults (RAM)."""
        session.call('reset_all_pid')
        return 'PID gains reset to the defaults'

    @server.tool(annotations=_SAFE_ACTION)
    def set_own_color(red: int, green: int, blue: int) -> str:
        """Set the motor's own LED color (shown while idle). Colors are 0-255. RAM only unless saved."""
        for c in (red, green, blue):
            if not 0 <= c <= 255:
                raise ToolError('Colors must be 0-255')
        session.call('set_own_color', red, green, blue)
        return 'ok'

    @server.tool(annotations=_SAFE_ACTION)
    def set_safe_run(enabled: bool, timeout_ms: int = 1000,
                     stop_action: Literal['free', 'disable', 'stop', 'hold_position'] = 'stop') -> str:
        """Watchdog: if the motor receives no command for 'timeout_ms', it does 'stop_action'
        (useful when the controlling PC may hang or the link may drop)."""
        if timeout_ms < 0:
            raise ToolError('timeout_ms must be >= 0')
        session.call('set_safe_run_settings', int(enabled), timeout_ms, SAFE_RUN_ACTIONS[stop_action])
        return 'safe run {}'.format('enabled ({} ms, {})'.format(timeout_ms, stop_action) if enabled else 'disabled')

    @server.tool(annotations=_DESTRUCTIVE)
    def save_settings_to_flash() -> str:
        """Save all the current settings (registers) to the flash memory so that they survive a reboot.
        Overwrites the saved settings: call it only when the user asked to save. Takes about 3 s."""
        session.call('save_all_registers')
        return 'saved to flash'

    @server.tool(annotations=_DESTRUCTIVE)
    def reset_settings_to_default() -> str:
        """Reset all the settings (registers) to the firmware defaults (RAM). The saved settings in flash are
        kept unless save_settings_to_flash is called afterwards."""
        session.call('reset_all_registers')
        return 'settings reset to the firmware defaults (not saved to flash)'

    # -------------------- IMU --------------------
    @server.tool(annotations=_READ_ONLY)
    def read_imu() -> dict:
        """Acceleration (g), angular velocity (deg/s) and temperature (deg C) of the motor's IMU."""
        session.call('enable_continual_imu_measurement')
        try:
            deadline = time.time() + 2.0
            while True:
                try:
                    v = session.call('read_imu_measurement')
                    break
                except ToolError:
                    if time.time() > deadline:
                        raise
                    time.sleep(0.1)
        finally:
            try:
                session.call('disable_continual_imu_measurement')  # keep the link free for motor measurement
            except ToolError:
                pass
        return {'accel_g': [round(v['accel_x'], 4), round(v['accel_y'], 4), round(v['accel_z'], 4)],
                'gyro_dps': [round(utils.rad2deg(v[k]), 3) for k in ('gyro_x', 'gyro_y', 'gyro_z')],
                'temperature_c': round(v['temp'], 2)}

    # -------------------- taskset / teaching / queue --------------------
    @server.tool(annotations=_DESTRUCTIVE)
    def taskset(action: Literal['start_recording', 'stop_recording', 'run', 'stop', 'erase', 'erase_all'],
                index: int = 0, repeat: int = 1) -> str:
        """Tasksets: sequences of commands stored in the motor's flash (index 0-49 on KM-1).
        start_recording -> send commands (use move tools with wait=False, and queue 'wait' for pauses)
        -> stop_recording. run plays it 'repeat' times. erase / erase_all delete stored tasksets."""
        if action in ('run',):
            _start_motion()
        calls = {'start_recording': ('start_recording_taskset', index),
                 'stop_recording': ('stop_recording_taskset',),
                 'run': ('start_doing_taskset', index, repeat),
                 'stop': ('stop_doing_taskset',),
                 'erase': ('erase_taskset', index),
                 'erase_all': ('erase_all_tasksets',)}
        session.call(*calls[action])
        return 'taskset {} (index {})'.format(action, index)

    @server.tool(annotations=_DESTRUCTIVE)
    def teaching_motion(action: Literal['start_teaching', 'stop_teaching', 'play', 'stop_playing',
                                        'erase', 'erase_all'],
                        index: int = 0, time_ms: int = 10000, repeat: int = 1) -> str:
        """Direct teaching: record the motion of the shaft turned by hand, then play it back
        (index 0-19, recording up to 65408 ms). start_teaching records for 'time_ms' while the user turns
        the shaft by hand. play plays it 'repeat' times."""
        if action == 'start_teaching' and not 0 < time_ms <= 65408:
            raise ToolError('time_ms must be 1-65408')
        if action == 'play':
            _start_motion()
        calls = {'start_teaching': ('start_teaching_motion', index, time_ms),
                 'stop_teaching': ('stop_teaching_motion',),
                 'play': ('start_playback_motion', index, repeat, 0),
                 'stop_playing': ('stop_playback_motion',),
                 'erase': ('erase_motion', index),
                 'erase_all': ('erase_all_motions',)}
        session.call(*calls[action])
        return 'motion {} (index {})'.format(action, index)

    @server.tool(annotations=_ACTION)
    def queue(action: Literal['pause', 'resume', 'clear', 'wait'], wait_ms: int = 1000) -> str:
        """The motor executes motion commands from a queue. pause / resume it, clear the pending commands
        (while paused), or 'wait' to insert a pause of 'wait_ms' (e.g. between moves of a taskset)."""
        calls = {'pause': ('pause_queue',), 'resume': ('resume_queue',), 'clear': ('clear_queue',),
                 'wait': ('wait_queue', wait_ms)}
        session.call(*calls[action])
        return 'queue {}'.format(action)

    # -------------------- diagnostics --------------------
    @server.tool(annotations=_READ_ONLY)
    def get_errors(clear: bool = False) -> list[dict]:
        """Recent error logs reported by the motor (newest last), with the cause and the remedy.
        Check this when a command seems to have no effect."""
        items = list(session.errors)
        if clear:
            session.errors.clear()
        return items

    @server.tool(annotations=_READ_ONLY)
    def ble_link_quality(diagnose: bool = False) -> dict:
        """BLE only. Statistics of the link (latency, failures, RSSI). diagnose=True also measures the response
        time and scans the radio environment (takes a few seconds) and gives a level and advice."""
        dev = session.device()
        if session.transport != 'ble':
            raise ToolError('Connected over {}, not BLE'.format(session.transport))
        with session._lock:
            try:
                return dev.diagnose_link() if diagnose else dev.link_stats()
            except Exception as e:
                raise ToolError('BLE diagnosis failed: {}'.format(e)) from e

    @server.tool(annotations=_DESTRUCTIVE)
    def reboot_motor() -> str:
        """Reboot the motor. Settings not saved to flash are lost. The server reconnects on the next tool call."""
        session.call('reboot')
        session.disconnect()
        time.sleep(1.0)
        return 'rebooting; the next tool call reconnects'

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
