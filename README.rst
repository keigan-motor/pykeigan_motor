Python Library for Keigan Motor
=========================================

You can control your Keigan Motor through USB Serial and BLE.

https://www.keigan-motor.com/

At present we support Linux only for BLE, because the BLE feature of this library depends on bluepy(Python interface to Bluetooth LE on Linux):

https://github.com/IanHarvey/bluepy

In the case you use USB serial only, you can use 

Installation
-----------
| pip install pykeigan

or 

| pip install pykeigan-usb

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

