Python Library on Linux for Keigan Motor
=========================================

You can control your Keigan Motor through USB Serial and BLE.

https://www.keigan-motor.com/

At present we support Linux only, because this library depends on bluepy(Python interface to Bluetooth LE on Linux):

https://github.com/IanHarvey/bluepy

Installation
-----------
| sudo apt install git
| git clone https://github.com/keigan-motor/pykeigan_motor
| cd pykeigan_motor
| python setup.py install


USB Serial
-----------
.. code-block:: python

  from pykeigan_motor import KMControllers
  dev=KMControllers.USBContoller('/dev/ttyUSB0')
  dev.enable()
  dev.speed(1.0)
  dev.runForward()

BLE
----
.. code-block:: python

  from pykeigan_motor import KMControllers
  dev=KMControllers.BLEController("xx:xx:xx:xx:xx")
  dev.enable()
  dev.speed(1.0)
  dev.runForward()
