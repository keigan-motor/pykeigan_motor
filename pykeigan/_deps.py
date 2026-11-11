# -*- coding: utf-8 -*-
"""
Import the optional / third-party dependencies with a clear message when they are missing.

The messages show the pip command for the Python that is running (sys.executable), because
"installed but not found" usually means it was installed into another Python.
"""
import sys


class MissingDependencyError(ImportError):
    """A dependency of pykeigan is not installed (or is the wrong package / too old)."""


def _exe():
    exe = sys.executable or 'python'
    return '"{}"'.format(exe) if ' ' in exe else exe


def pip_command(*packages, action='install'):
    """pip command for the running Python, e.g. 'C:\\...\\python.exe -m pip install "bleak>=0.22"'."""
    return '{} -m pip {} {}'.format(_exe(), action, ' '.join('"{}"'.format(p) for p in packages))


def _python():
    return 'Python {}.{} ({})'.format(sys.version_info[0], sys.version_info[1], sys.executable)


def require_pyserial():
    """Import and return the pyserial module 'serial' (USB)."""
    try:
        import serial
    except ImportError as e:
        raise MissingDependencyError(
            'USB needs pyserial, which is not installed in {}.\n'
            'Install it with:\n\n    {}\n'.format(_python(), pip_command('pyserial'))) from None
    if not hasattr(serial, 'Serial'):
        raise MissingDependencyError(
            'The module "serial" found at {} is not pyserial (another package named "serial" is installed).\n'
            'Replace it with:\n\n    {}\n    {}\n'.format(
                getattr(serial, '__file__', '?'), pip_command('serial', action='uninstall'), pip_command('pyserial')))
    return serial


def require_bleak():
    """Import and return the bleak module (BLE)."""
    if sys.version_info < (3, 8):
        raise MissingDependencyError('BLE (bleak) needs Python 3.8 or later. This is {}.'.format(_python()))
    try:
        import bleak
    except ImportError as e:
        raise MissingDependencyError(
            'BLE needs bleak, which is not installed in {}.\n'
            'Install it with:\n\n    {}\n\n'
            '(or pip install "pykeigan-motor[ble]")'.format(_python(), pip_command('bleak>=0.22'))) from None
    if not hasattr(bleak, 'BleakScanner'):
        raise MissingDependencyError(
            'The bleak found at {} is too old or broken. Update it with:\n\n    {} --upgrade\n'.format(
                getattr(bleak, '__file__', '?'), pip_command('bleak>=0.22')))
    return bleak


def require_mcp():
    """Check the MCP SDK (mcp >= 2, Python >= 3.10) for the MCP server."""
    if sys.version_info < (3, 10):
        raise MissingDependencyError('The MCP server (pykeigan-mcp) needs Python 3.10 or later. '
                                     'This is {}.'.format(_python()))
    try:
        import mcp.server.mcpserver  # noqa: F401  (mcp >= 2)
    except ImportError as e:
        try:
            from importlib.metadata import version
            installed = version('mcp')
        except Exception:
            installed = None
        if installed and installed.split('.')[0].isdigit() and int(installed.split('.')[0]) < 2:
            raise MissingDependencyError(
                'The MCP server needs the MCP SDK version 2 (mcp >= 2), but mcp {} is installed in {}.\n'
                'Update it with:\n\n    {}\n'.format(installed, _python(), pip_command('mcp>=2,<3'))) from None
        if installed:
            raise MissingDependencyError(
                'mcp {} is installed in {}, but it cannot be imported ({}).\n'
                'Reinstall it with:\n\n    {} --force-reinstall\n'.format(
                    installed, _python(), e, pip_command('mcp>=2,<3'))) from None
        raise MissingDependencyError(
            'The MCP server (pykeigan-mcp) needs the MCP SDK (mcp >= 2), which is not installed in {}.\n'
            'Install it with:\n\n    {}\n\n'
            '(or pip install "pykeigan-motor[mcp]", with BLE: "pykeigan-motor[mcp,ble]")'.format(
                _python(), pip_command('mcp>=2,<3'))) from None
