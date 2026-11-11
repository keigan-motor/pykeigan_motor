# -*- coding: utf-8 -*-
"""
USB connection check for KeiganMotor (pykeigan-usb-check / python -m pykeigan.usbcheck).

Checks step by step where the USB connection fails:
  1. the Motor is visible to the OS (FTDI USB-serial chip, VID 0403)
  2. the serial port can be opened
  3. the Motor answers (device name / device info)

Usage::

    pykeigan-usb-check            # check all KeiganMotors visible to the OS
    pykeigan-usb-check COM3       # check one port
"""
import argparse
import contextlib
import io
import sys

import serial

from pykeigan.usbcontroller import (KEIGAN_USB_VID, HARDWARE_HINT, USBController, _same_port,
                                    diagnose_port, find_keigan_ports)


def _hex(v):
    return '{:04X}'.format(v) if v is not None else '----'


def list_ports_report(out=print):
    """Print all serial ports, KeiganMotor candidates marked with '*'. Returns the KeiganMotor ports."""
    from serial.tools import list_ports
    ports = sorted(list_ports.comports(), key=lambda p: p.device)
    out('Serial ports visible to the OS:')
    if not ports:
        out('  (none)')
    for p in ports:
        mark = '*' if p.vid == KEIGAN_USB_VID else ' '
        out('  {} {:<14} VID:PID={}:{}  SN={}  {}'.format(mark, p.device, _hex(p.vid), _hex(p.pid),
                                                          p.serial_number or '-', p.description or ''))
    out('  (* = KeiganMotor candidate: FTDI chip, VID 0403)')
    return [p for p in ports if p.vid == KEIGAN_USB_VID]


def check_port(port, baud=115200, out=print):
    """Check one port: open it, then read the device name / info. Returns True if the Motor answers."""
    out('')
    out('== {} =='.format(port))
    visible = any(_same_port(port, p.device) for p in find_keigan_ports())
    out('[1/3] visible to the OS as a KeiganMotor : {}'.format('OK' if visible else 'NO'))

    try:
        serial.Serial(port, baud, timeout=0, write_timeout=0.1).close()
    except Exception as e:
        out('[2/3] open the port                     : NG')
        out(diagnose_port(port, e))
        return False
    out('[2/3] open the port                     : OK')

    dev = None
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # hide the controller's own precheck messages
            dev = USBController(port, baud=baud, reconnect=False, open_timeout=0)
            name = dev.read_device_name()
            info = dev.read_device_info()
    except Exception as e:
        out('[3/3] response from the Motor           : NG ({})'.format(e))
        out('  -> The port opens but the Motor does not answer. Check:\n'
            '     * the baud rate (default 115200, --baud)\n'
            '     * the Motor power (the LED is on?)\n'
            '     * the port really is a KeiganMotor (not another USB-serial device)\n'
            '     * if it fails only sometimes: USB hub / cable (see below)\n' + HARDWARE_HINT)
        return False
    finally:
        if dev is not None:
            with contextlib.redirect_stdout(io.StringIO()):
                dev.disconnect()
    out('[3/3] response from the Motor           : OK')
    out('      device name : {}'.format(name))
    out('      device info : {}'.format(info))
    return True


def check(port=None, baud=115200, out=print):
    """Run the USB check (all KeiganMotors, or only 'port'). Returns True if every checked Motor answers."""
    keigan = list_ports_report(out)
    if port:
        targets = [port]
    elif keigan:
        targets = [p.device for p in keigan]
    else:
        out('')
        out('No KeiganMotor USB device (FTDI, VID 0403) is visible to the OS.')
        out(HARDWARE_HINT)
        return False
    results = [check_port(t, baud, out) for t in targets]
    out('')
    out('Result: {}/{} Motor(s) OK'.format(sum(results), len(results)))
    return all(results)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pykeigan-usb-check',
                                     description='Check the USB connection to KeiganMotor(s).')
    parser.add_argument('port', nargs='?', help='serial port to check (default: all KeiganMotors found)')
    parser.add_argument('--baud', type=int, default=115200, help='baud rate (default: 115200)')
    args = parser.parse_args(argv)
    sys.exit(0 if check(args.port, args.baud) else 1)


if __name__ == '__main__':
    main()
