Python Library for Keigan Motor (v2)
==============================================

Introduction
---------------
You can control your Keigan Motor through USB Serial and BLE.

https://www.keigan-motor.com/

**This library has been updated from v1 to more than v2.**

**The method names are not comatible, but we added many important features.**

**We strongly recommend more than v2 from now on.**

**Just in case you can get v1 from: https://github.com/keigan-motor/pykeigan_motor/tree/v1**

At present we support Linux only for BLE, because the BLE functions of this library depends on bluepy(Python interface to Bluetooth LE on Linux by Mr. Ian Harvey):

https://github.com/IanHarvey/bluepy

The USB serial functions should work on Windows and Mac too.

Requirements
------------------

- python >= 3.5 (recommended)
- pyserial >= 3.4
- bluepy >= 1.1.4 (BLE support. Linux only)

**NOTE) This library runs on python 3.5 or later.**  

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
        sudo apt-get install python-pip libglib2.0-dev
        sudo pip install bluepy
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
  dev=usbcontroller.USBContoller('/dev/serial/by-id/usb-FTDI_FT230X_Basic_UART_DM00xxxx-if00-port0')
  dev.enable_action()
  dev.set_speed(1.0)
  dev.run_forward()

- examples/usb-simple-connection.py
    Basic connection to the Motor.
- examples/usb-rotate-the-motor.py
    Rotate the Motor continuously and stop.
- examples/usb-position-control.py
    Rotate the Motor to the relative and absolute position.
- examples/usb-get-motor-Informations.py
    Acquire the speed, position, torque and IMU values of the Motor.
- examples/usb-actuator.py
    Let the Motor go and return for the specific distance.
- examples/usb-torque-control.py
    Demonstration for a torque control. Increase the torque as you rotate the Motor by hand.
- examples/usb-teaching-control.py
    Let the Motor record and playback your motion.

BLE (for Linux Only)
----------------------
You need to know the MAC address of your Keigan Motor for BLE connection.

For example, you can use the following simple script. Please run with sudo.

KM1Scan.py

.. code-block:: python

  from bluepy.btle import Scanner
  scanner=Scanner()
  devices=scanner.scan(5.0)
  for dev in devices:
      for (adtype, desc, value) in dev.getScanData():
          if desc=="Complete Local Name" and "KM-1" in value:
              print(value,":",dev.addr)

- Simplest Sample Code
    Rotate counter-clockwise with 1.0 rad/sec.

.. code-block:: python

  from pykeigan import blecontroller
  dev=blecontroller.BLEController("xx:xx:xx:xx:xx")
  dev.enable_action()
  dev.set_speed(1.0)
  dev.run_forward()

- examples/ble-simple-connection.py
    Basic connection to the Motor.
- examples/ble-scanner-connection.py
    Connect to the Motor by BLE scanning.
- examples/ble-rotate-the-motor.py
    Rotate the Motor continuously and stop.
- examples/ble-get-motor-Informations.py
     Acquire the speed, position, torque and IMU values of the Motor.

Release Notes
------------------
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
