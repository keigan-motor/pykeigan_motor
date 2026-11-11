# -*- coding: utf-8 -*-
# Clear messages when pyserial / bleak / mcp are missing or wrong.
import subprocess
import sys
import types

import pytest

from pykeigan import _deps


def hide(monkeypatch, *names):
    for name in names:
        monkeypatch.setitem(sys.modules, name, None)  # 'import name' raises ImportError


def test_pyserial_missing(monkeypatch):
    hide(monkeypatch, 'serial')
    with pytest.raises(_deps.MissingDependencyError, match='pyserial') as e:
        _deps.require_pyserial()
    assert '-m pip install "pyserial"' in str(e.value)
    assert isinstance(e.value, ImportError)


def test_wrong_serial_package(monkeypatch):
    monkeypatch.setitem(sys.modules, 'serial', types.ModuleType('serial'))  # no serial.Serial
    with pytest.raises(_deps.MissingDependencyError, match='not pyserial') as e:
        _deps.require_pyserial()
    assert 'pip uninstall "serial"' in str(e.value)


def test_bleak_missing(monkeypatch):
    hide(monkeypatch, 'bleak')
    with pytest.raises(_deps.MissingDependencyError, match='BLE needs bleak') as e:
        _deps.require_bleak()
    assert '"bleak>=0.22"' in str(e.value)


def test_mcp_missing(monkeypatch):
    if sys.version_info < (3, 10):
        with pytest.raises(_deps.MissingDependencyError, match='3.10'):
            _deps.require_mcp()
        return
    hide(monkeypatch, 'mcp', 'mcp.server', 'mcp.server.mcpserver')
    with pytest.raises(_deps.MissingDependencyError, match='mcp'):
        _deps.require_mcp()


def test_pip_command_quotes_path_with_spaces(monkeypatch):
    monkeypatch.setattr(sys, 'executable', r'C:\Program Files\Python\python.exe')
    assert _deps.pip_command('bleak>=0.22') == r'"C:\Program Files\Python\python.exe" -m pip install "bleak>=0.22"'


def test_usb_works_without_bleak():
    # USB / errors / utils must not need bleak
    code = ("import sys; sys.modules['bleak'] = None; "
            "from pykeigan import usbcontroller, usbcheck, errors, utils; print('ok')")
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert r.stdout.strip() == 'ok', r.stderr


def test_ble_import_message_without_bleak():
    code = "import sys; sys.modules['bleak'] = None; from pykeigan import blecontroller"
    r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert 'MissingDependencyError: BLE needs bleak' in r.stderr
    assert 'During handling' not in r.stderr  # a single, short traceback
