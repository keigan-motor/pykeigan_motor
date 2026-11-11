Python Library for Keigan Motor (v3)
==============================================

Introduction
---------------
You can control your Keigan Motor through USB Serial and BLE.

https://www.keigan-motor.com/

**v3: BLE now uses bleak (Windows / Linux / Raspberry Pi, no sudo), detailed error information, and an MCP server for AI assistants.**

**The method names are the same as v2. BLE has some incompatible changes (see Release 3.0.0).**

**The method names of v1 are not compatible. Just in case you can get v1 from: https://github.com/keigan-motor/pykeigan_motor/tree/v1**

The BLE functions of this library depend on bleak (cross-platform Bluetooth Low Energy client), and work on Windows and Linux (including Raspberry Pi 4/5):

https://github.com/hbldh/bleak

The USB serial functions should work on Windows and Mac too.

Requirements
------------------

- python >= 3.5 (USB only)
- python >= 3.8 for BLE (python >= 3.10 recommended). The minimum version is required by bleak:
  pip installs the latest bleak that supports your python (3.8: bleak 0.22, 3.9: bleak 1.x, 3.10 or later: bleak 2.x / 3.x).
  Raspberry Pi OS Bookworm (python 3.11) and Bullseye (python 3.9) are supported. Buster (python 3.7) is not supported for BLE.
- pyserial >= 3.4
- bleak >= 0.22 (BLE support. Windows 10+ / Linux with BlueZ >= 5.55)
- mcp >= 2 (MCP server, optional. python >= 3.10): ``pip install pykeigan_motor[mcp]``

**NOTE) This library runs on python 3.5 or later (BLE: python 3.8 or later).**  

**If you want to use it with python 2.7 in ROS, etc., please use 2.2.0.**  

**https://github.com/keigan-motor/pykeigan_motor/tree/2.2.0**  

**We recommend to update your KeiganMotor firmware to the latest as python script can cause error if it use new API commands.**  
  

  *Update 2.4.0*

  - support both python2.7 and 3



Installation
-------------------------------

Install from source::

    sudo apt install git
    git clone https://github.com/keigan-motor/pykeigan_motor
    cd pykeigan_motor
    python setup.py install
    # and to install BLE Support
    pip install .[ble]

Install from PyPI::

    pip3 install pykeigan-motor
    # or to install BLE Support
    pip3 install pykeigan-motor[ble]

- NOTE) Use pip instead of pip3 in case of Python2.x or Windows OS.

USB Serial
-----------------
To connect your Keigan Motor through USB serial, you need to know the mounted path.
You can get the unique path of your Keigan Motor by::

    ls /dev/serial/by-id/

Your Keigan Motor's ID should be like 'usb-FTDI_FT230X_Basic_UART_DM00XXXX-if00-port0'.
To use your Keigan Motor through USB serial, you need to add R/W permission to it.::

    sudo chmod 666 /dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DM00XXXX-if00-port0

- Simplest Sample Code
    Rotate counter-clockwise with 1.0 rad/sec.

.. code-block:: python

  from pykeigan import usbcontroller
  dev=usbcontroller.USBController('/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DM00xxxx-if00-port0')
  dev.enable_action()
  dev.set_speed(1.0)
  dev.run_forward()

USB examples take the port as the first argument (default: /dev/ttyUSB0). On Windows use ``COM3`` etc.::

    python3 examples/usb-simple-connection.py /dev/ttyUSB0
    python examples\usb-simple-connection.py COM3

- examples/usb-simple-connection.py
    Basic connection to the Motor. Blink the LED and rotate at 5 rpm.
- examples/usb-rotate-the-motor.py
    Rotate the Motor forward (10 s), reverse (10 s), stop with torque and free.
- examples/usb-position-control.py
    Rotate the Motor to the relative and absolute position.
- examples/usb-offset-position-control.py
    Absolute positioning with a program-side offset (OFFSET_DEG) as the machine zero, without overwriting the Motor's origin.
    Run with ``--measure`` first to print the current position without moving the Motor.
- examples/usb-move_wait_queue.py
    Move to the next position after the arrival (move_to_pos_wait): 0 -> 90 -> 0 -> -90 -> 0 deg.
- examples/usb-get-motor-Informations.py
    Acquire the speed, position, torque and IMU values of the Motor (with motor time, firmware >= 2.62).
- examples/usb-get-motor-Info-time.py
    Same as usb-get-motor-Informations.py without the motor time setting.
- examples/usb-actuator.py
    Let the Motor go and return between 0 and 720 deg.
- examples/usb-button_trigger.py
    Get the button events of the Motor. Set ``port1`` in the file.
- examples/usb-sine-wave.py
    Sine wave position control with a graph (requires matplotlib, Linux only because of signal.setitimer).
- examples/usb-torque-control.py
    Demonstration for a torque control. Increase the torque as you rotate the Motor by hand.
- examples/usb-teaching-control.py
    Let the Motor record and playback your motion.
- examples/windows_examples/
    USB examples for Windows (COM port selection, PID / baud rate settings, taskset, etc.). See examples/readme.md for details.

BLE (Windows / Linux)
----------------------

.. warning::

   **Raspberry Pi: turn off Wi-Fi when using BLE.**
   The on-board Bluetooth of Raspberry Pi shares one radio chip with Wi-Fi, and the interference is severe.
   While Wi-Fi is on (2.4GHz), BLE connections to KeiganMotor fail very often ("Connection Failed to be Established"),
   and connecting to multiple Motors is practically impossible.
   Raspberry Pi 5 has the same problem (it uses the same kind of radio chip).
   In our test (2 Motors, connecting both 5 times):

   - Wi-Fi off: both Motors connected 5/5 times in about 2 sec (Raspberry Pi 4 and 5).
   - 2.4GHz Wi-Fi with network traffic: 1/5 (Raspberry Pi 5). On Raspberry Pi 4, a Motor could not be connected at all.
   - 2.4GHz Wi-Fi without traffic: 4/5, and connecting took longer (Raspberry Pi 5).
   - 5GHz Wi-Fi without traffic: 5/5 (Raspberry Pi 5).

   Use wired LAN (for SSH, etc.) and turn Wi-Fi off::

       sudo nmcli radio wifi off      # turn on again: sudo nmcli radio wifi on

   If you need Wi-Fi, use 5GHz only (the same SSID may be connected at 2.4GHz automatically).
   5GHz with network traffic and USB Bluetooth adapters have not been verified.

You need to know the MAC address of your Keigan Motor for BLE connection.
Scanning does not require sudo / administrator privileges.

KM1Scan.py

.. code-block:: python

  from pykeigan import blecontroller
  for km in blecontroller.scan(5.0):
      print(km['name'], ":", km['address'])

- Raspberry Pi: bleak uses BlueZ via D-Bus. Make sure the bluetooth service is running (``sudo systemctl enable --now bluetooth``) and the user is in the ``bluetooth`` group.
- Measurement values are received by BLE notifications. ``on_motor_measurement_value_cb``, ``on_motor_imu_measurement_cb``, ``on_motor_log_cb`` and ``on_motor_event_cb`` can be used in the same way as USBController. Callbacks are called from a background thread.

- Simplest Sample Code
    Rotate counter-clockwise with 1.0 rad/sec.

.. code-block:: python

  from pykeigan import blecontroller
  dev=blecontroller.BLEController("xx:xx:xx:xx:xx")
  dev.enable_action()
  dev.set_speed(1.0)
  dev.run_forward()

Connecting takes about 2-4 sec. On Windows, ``BLEController(address)`` connects directly without scanning (if Windows has seen the Motor before); otherwise it scans for the Motor first.
If establishing the connection fails, it retries automatically (``BLEController(address, timeout=10.0, retries=2)``: ``timeout`` [sec] is per scan / connection attempt).
It raises ``blecontroller.DeviceNotFoundError`` if the Motor is not found, and ``ConnectionError`` if all attempts fail.
On Raspberry Pi, if connections often fail, first check that Wi-Fi is off (see the warning above).

To check whether the radio environment is good enough for BLE, use ``dev.diagnose_link()`` (example: ``examples/ble-link-check.py``).
It measures the RSSI, the response time and failures of the link, the number of BLE devices nearby and the Wi-Fi of the PC,
and returns ``'level'`` (``'good'`` / ``'fair'`` / ``'poor'``) with advice for improvement.
``dev.link_stats()`` returns the response time and failures of the commands sent in normal use (no extra communication) for monitoring.
If connecting fails, ``blecontroller.diagnose_environment(address, error=e)`` diagnoses without connecting:
whether the Motor is advertising, its RSSI, the number of BLE devices nearby and the Wi-Fi of the PC (``ble-link-check.py`` does this automatically).

BLE examples take the MAC address as the first argument. If omitted, they scan and let you select the Motor from the list (connect automatically if only one is found)::

    python3 examples/ble-simple-connection.py xx:xx:xx:xx:xx:xx
    python3 examples/ble-simple-connection.py
      [0] KM-1U XXXX#54C : EF:16:B8:BB:D9:52 (RSSI -52)
      [1] KM-1U YYYY#12A : D1:5A:FA:A7:D9:5D (RSSI -70)
    Connect:[number] Rescan:[r] Quit:[q] >>

- examples/KM1Scan.py
    Scan Keigan Motors and print the names and MAC addresses (argument: scan seconds, default 10). Found Motors are printed immediately with the remaining time.
- examples/ble-scanner-connection.py
    Scan, select and connect to the Motor, and blink the LED. Press [s] to rescan and switch to another Motor (the connected Motor is disconnected before scanning, because a connected Motor does not advertise).
- examples/ble-simple-connection.py
    Basic connection to the Motor. Blink the LED and rotate at 5 rpm.
- examples/ble-rotate-the-motor.py
    Rotate the Motor forward (10 s), reverse (10 s), stop with torque and free.
- examples/ble-get-motor-Informations.py
    Acquire the status, speed, position, torque and IMU values of the Motor.
- examples/ble_select.py
    Common "scan and select" helper used by the BLE examples (``from ble_select import select_motor``).

Multiple Motors (BLE)
^^^^^^^^^^^^^^^^^^^^^^
Create one ``BLEController`` per MAC address to control multiple Motors at the same time.
Each controller has its own connection and callbacks (all controllers share one background thread).

.. code-block:: python

  from pykeigan import blecontroller
  blecontroller.scan(5.0)   # scan once first (connected Motors do not advertise)
  motors = [blecontroller.BLEController(a) for a in ["xx:xx:xx:xx:xx:xx", "yy:yy:yy:yy:yy:yy"]]
  for i, m in enumerate(motors):
      m.on_motor_measurement_value_cb = lambda v, i=i: print(i, v['position'])
      m.enable_continual_motor_measurement()

The multi-motor examples take MAC addresses as arguments. If omitted, they scan (10 s) and let you select Motors by numbers (e.g. ``0,1``, or ``a`` for all).
In a crowded BLE environment one scan may miss some Motors; press ``r`` to rescan, and newly found Motors are added to the list (the numbers of found Motors are kept)::

    python3 examples/ble-multi-simple-connection.py xx:xx:xx:xx:xx:xx yy:yy:yy:yy:yy:yy
    python3 examples/ble-multi-simple-connection.py
    Connect:[numbers e.g. 0,1 / a=all] Rescan:[r] Quit:[q] >>0,1

- examples/ble-multi-simple-connection.py
    Connect to multiple Motors, blink the LEDs in different colors and rotate them at 5 rpm at the same time.
- examples/ble-multi-get-motor-Informations.py
    Show the position, velocity, torque and notification rate [Hz] of all Motors in a table.
- examples/ble-multi-position-control.py
    Synchronized position control: all Motors move to the same angles and wait for all of them to arrive.
- examples/ble-multi-follow.py
    Leader / follower: turn the first Motor (free) by hand and the others follow it (``--reverse`` for the opposite direction).
- examples/ble_multi.py
    Common helpers for the multi-motor examples (select, connect, send to all Motors in parallel, disconnect).

Notes for multiple Motors:

- The number of simultaneous connections depends on the BLE adapter (about 5-7 in general; the built-in adapter of Raspberry Pi may be less stable). Use a USB BLE dongle if needed.
- Commands cannot be sent from callbacks (``RuntimeError``). Store values in the callback and send commands from another thread (see ble-multi-follow.py).

If the Motor is not found by scanning:

- Close smartphone apps (KMQuick etc.) or other PCs connected to the Motor. The Motor stops advertising while connected.
- BLE may be disabled after a USB connection. Enable it by KMQuick or reboot the Motor.
- Reset the interface of the Motor: https://document.keigan-motor.com/basic/reset

Release Notes
------------------
Release 3.0.0

- MCP server: ``pykeigan-mcp`` lets AI assistants (Claude Code, Claude Desktop, etc.) control a Motor over USB or BLE.
  ``pip install pykeigan_motor[mcp]`` (python >= 3.10), then e.g. ``claude mcp add keigan -- pykeigan-mcp --usb COM3``.
  Units are degrees and rpm. Speeds / torques above ``--max-rpm`` (60) / ``--max-torque`` (0.3 N.m) are rejected.
- Errors: new ``pykeigan.errors`` with the causes, remedies and the meaning of the info value of all the firmware error codes.
  ``errors.describe(log)`` makes a readable message. See "Errors and Troubleshooting" in the documentation.
- Errors: ``on_motor_error_cb`` (called only for errors) and ``last_error`` (USB / BLE).
  The log has ``identifier``, ``info``, ``command_name`` and ``error_name`` in addition to ``command_names`` and ``error_codes``.
  With ``debug_mode=True`` the cause and the remedy of errors are printed.
- ``flash_memory_states``: added ``FLASH_STATE_ERASING`` (10) and ``FLASH_STATE_READING`` (30) (``read_status()`` raised ``KeyError`` while erasing / reading).
- BLE: replaced bluepy with bleak. BLE now works on Windows and Linux (including Raspberry Pi 4/5) without sudo. python >= 3.8 is required for BLE.
- BLE: ``blecontroller.scan()``, connection retries (``BLEController(addr, timeout=10.0, retries=2)``), faster connection on Windows,
  ``DeviceNotFoundError``, notifications for measurement values / logs / events (callbacks same as USBController).
- BLE: link diagnostics (``diagnose_link()``, ``link_stats()``, ``blecontroller.diagnose_environment()``, ``blecontroller.check_wifi()``).
- BLE: ``read_imu_measurement_interval()``, ``read_motor_measurement_interval()`` and ``read_baud_rate()`` are supported.
- BLE: ``read_motor_measurement()`` / ``read_imu_measurement()`` return the latest notified value (within ``validation_threshold`` sec) or read the value directly.
- BLE (incompatible changes): removed ``BLEController.dev`` (bluepy Peripheral), ``start_command_log_capturing()`` and ``print_command_log()``.
  ``start_debug()`` only prints the command logs received by notifications. Commands raise ``ConnectionError`` while disconnected, and ``TimeoutError`` on timeout.
- Removed ``read_gpio_status()`` (register 0xCC is not supported by the library).
- USB: register reads return only a value received after the request (no stale cache).
  ``read_motor_measurement_interval()``, ``read_imu_measurement_interval()`` and ``read_baud_rate()`` are supported.
- USB: the end of a frame is found by its length byte (frames whose data contained 0D 0A were dropped),
  and the whole device name is read (it was truncated to 13 characters).
- USB: ``on_motor_log_cb`` also receives unknown commands / error codes.
- USB: ``USBController(port, open_timeout=None)``: raises ``ConnectionError`` after ``open_timeout`` sec if the port cannot be opened (default: retry forever as before).
- USB: ``read_motor_measurement()`` / ``read_imu_measurement()`` take ``validation_threshold`` (same as BLE).
- Python 3.9+: replaced ``Thread.isAlive()`` (removed in Python 3.9), so the port is closed at exit.
- ``read_motion()``: the completion callback is registered before sending the command.
- New BLE examples (scan & select, multiple Motors, link check) and usb-offset-position-control.py.

Release 2.4.0

- Added support both python2 and 3 support
- Update some examples
- Add reinit, reconnection during initialize

Release 2.2.5

- Respond to KeiganMotor firmware ver >= 2.40
- Bug fixes
- Added serial reconnection feature(USB)
- Added some new APIs
- Added some examples

Release 2.1.0

- Added python 2 support

Release 2.0.1

- Added APIs for reading and writing teaching data
- Added read_motion and write_motion_position

Release 2.0.0

- Method Names Renewal
- Added Debug Mode
- Added Data Acquisition on USB serial
- Added Windows and Mac Support for USB serial
