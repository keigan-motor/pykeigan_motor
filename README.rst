Python Library on Linux for Keigan Motor
=========================================

You can control your Keigan Motor through USB Serial and BLE.
https://www.keigan-motor.com/
Just now, we support Linux only, because we use bluepy https://github.com/IanHarvey/bluepy

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
