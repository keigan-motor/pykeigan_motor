Python Library for Keigan Motor
=========================================

You can control your Keigan Motor through USB Serial and BLE.

https://www.keigan-motor.com/

At present we support Linux only for BLE, because the BLE feature of this library depends on bluepy(Python interface to Bluetooth LE on Linux) by Mr. Ian Harvey:

https://github.com/IanHarvey/bluepy

The USB serial feature should work on Windows and Mac too. Please use setup-usb.py to install.

Requirements
-----------
- python >= 3.5
- pyserial >= 3.4
- bluepy >= 1.1.4

Installation
-----------
| sudo apt install git
| git clone -b v2 https://github.com/keigan-motor/pykeigan_motor
| cd pykeigan_motor
| python setup.py install (or python setup-usb.py install )

USB Serial
-----------
.. code-block:: python

  from pykeigan import usbcontroller
  dev=usbcontroller.USBContoller('/dev/ttyUSB0')
  dev.enable_action()
  dev.set_speed(1.0)
  dev.run_forward()

BLE
----
.. code-block:: python

  from pykeigan import blecontroller
  dev=blecontroller.BLEController("xx:xx:xx:xx:xx")
  dev.enable_action()
  dev.set_speed(1.0)
  dev.run_forward()
