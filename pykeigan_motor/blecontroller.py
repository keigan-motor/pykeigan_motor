#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
"""
from pykeigan_motor import controller as base
import struct, time
from bluepy import btle
from pykeigan_motor.utils import *


class BLEController(base.Controller):
    def __init__(self, addr):
        self.address = addr
        self.dev = btle.Peripheral(self.address, 'random')
        for v in self.dev.getCharacteristics():
            if v.uuid == 'f1400001-8936-4d35-a0ed-dfcd795baa8c':
                self.motor_control_handle = v.getHandle()
            if v.uuid == 'f1400003-8936-4d35-a0ed-dfcd795baa8c':
                self.motor_led_handle = v.getHandle()
            if v.uuid == 'f1400004-8936-4d35-a0ed-dfcd795baa8c':
                self.motor_measurement_handle = v.getHandle()
            if v.uuid == 'f1400005-8936-4d35-a0ed-dfcd795baa8c':
                self.motor_imu_measurement_handle = v.getHandle()
            if v.uuid == 'f1400006-8936-4d35-a0ed-dfcd795baa8c':
                self.motor_settings_handle = v.getHandle()

    def _run_command(self, val, characteristics=None):
        if characteristics == 'motor_control':
            self.dev.writeCharacteristic(self.motor_control_handle, val)
        elif characteristics == 'motor_led':
            self.dev.writeCharacteristic(self.motor_led_handle, val)
        elif characteristics == 'motor_settings':
            self.dev.writeCharacteristic(self.motor_settings_handle, val)
        else:
            raise ValueError('Invalid Characteristics')

    def connect(self):
        """
        Establish the BLE connection.
        """
        self.dev.connect(self.address, 'random')

    def disconnect(self):
        """
        Close the BLE connection.
        """
        self.dev.disconnect()

    def read_motor_measurement(self):
        """
        Get the position, velocity, and torque and store them to the properties 'position' in rad, 'velocity' in rad/sec, and 'torque' in N.m.
        """
        ba = self.dev.readCharacteristic(self.motor_measurement_handle)
        position = bytes2float(ba[0:4])
        velocity = bytes2float(ba[4:8])
        torque = bytes2float(ba[8:12])
        return {'position': position, 'velocity': velocity, 'torque': torque, 'received_unix_time': time.time()}

    def read_imu_measurement(self):
        """
        Get the x,y,z axis acceleration, temperature, and anguler velocities around x,y,z axis
        and store them to 'accel_x', 'accel_y', 'accel_z' in g(9.80665 m/s^2), 'temp' in degree Celsius, 'gyro_x', 'gyro_y', and 'gyro_z' in rad/sec. Need to call enableIMUMeasurement() before calling this function.
        """
        ba = self.dev.readCharacteristic(self.motor_imu_measurement_handle)
        if len(ba) != 14:
            raise ValueError("Reading imu values failed. Did you call enableIMUMeasurement() beforehand?")
        accel_x = bytes2int16_t(ba[0:2]) * 2.0 / 32767
        accel_y = bytes2int16_t(ba[2:4]) * 2.0 / 32767
        accel_z = bytes2int16_t(ba[4:6]) * 2.0 / 32767
        temp = bytes2int16_t(ba[6:8]) / 333.87 + 21.00
        gyro_x = bytes2int16_t(ba[8:10]) * 0.00013316211
        gyro_y = bytes2int16_t(ba[10:12]) * 0.00013316211
        gyro_z = bytes2int16_t(ba[12:14]) * 0.00013316211
        return {'accel_x': accel_x, 'accel_y': accel_y, 'accel_z': accel_z, 'temp': temp, 'gyro_x': gyro_x,
                'gyro_y': gyro_y, 'gyro_z': gyro_z, 'received_unix_time': time.time()}

    def __read_float_data(self, ba):
        return bytes2float(ba[4:8])

    def __read_uint8_data(self, ba):
        return bytes2uint8_t(ba[4:5])

    def __read_rgb_data(self, ba):
        return ba[4], ba[5], ba[6]

    def __read_devicename_data(self, ba):
        return ba[4:17].decode('utf-8')

    def __read_deviceinfo_data(self, ba):
        return ba[4:35].decode('utf-8')

    def __read_status_data(self, ba):
        bits_list = [int(n) for n in bin(bytes2uint8_t(ba[4:5]))[2:].zfill(8)]
        return {"isCheckSumEnabled": bits_list[0], "iMUMeasurement": bits_list[4], "motorMeasurement": bits_list[5],
                "queue": bits_list[6], "motorEnabled": bits_list[7],
                "flash_memory_state": self.flash_memory_states[bytes2uint8_t(ba[5:6])],
                "motor_control_mode": self.motor_control_modes[bytes2uint8_t(ba[6:7])]}

    def __read_setting_value(self, comm):
        float_value_comms = [0x02, 0x03, 0x07, 0x08, 0x0E, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21,
                             0x5B]
        valid_comms = [0x05, 0x3A, 0x46, 0x47, 0x9A]
        valid_comms.extend(float_value_comms)
        if not (comm in valid_comms):
            raise ValueError("Unknown Command")
        self.read_register(comm)
        ba = self.dev.readCharacteristic(self.motor_settings_handle)
        while len(ba) == 6:
            ba = self.dev.readCharacteristic(self.motor_settings_handle)
        if comm in float_value_comms:
            return self.__read_float_data(ba)
        if comm == 0x05:
            return self.__read_uint8_data(ba)
        if comm == 0x3A:
            return self.__read_rgb_data(ba)
        if comm == 0x46:
            return self.__read_devicename_data(ba)
        if comm == 0x47:
            return self.__read_deviceinfo_data(ba)
        if comm == 0x9A:
            return self.__read_status_data(ba)
        return ba

    def read_maxSpeed(self):
        return self.__read_setting_value(0x02)

    def read_minSpeed(self):
        return self.__read_setting_value(0x03)

    def read_curveType(self):
        return self.__read_setting_value(0x05)

    def read_acc(self):
        return self.__read_setting_value(0x07)

    def read_dec(self):
        return self.__read_setting_value(0x08)

    def read_maxTorque(self):
        return self.__read_setting_value(0x0E)

    def read_qCurrentP(self):
        return self.__read_setting_value(0x18)

    def read_qCurrentI(self):
        return self.__read_setting_value(0x19)

    def read_qCurrentD(self):
        return self.__read_setting_value(0x1A)

    def read_speedP(self):
        return self.__read_setting_value(0x1B)

    def read_speedI(self):
        return self.__read_setting_value(0x1C)

    def read_speedD(self):
        return self.__read_setting_value(0x1D)

    def read_positionP(self):
        return self.__read_setting_value(0x1E)

    def read_positionI(self):
        return self.__read_setting_value(0x1F)

    def read_positionD(self):
        return self.__read_setting_value(0x20)

    def read_posControlThreshold(self):
        return self.__read_setting_value(0x21)

    def read_ownColor(self):
        return self.__read_setting_value(0x3A)

    def read_deviceName(self):
        return self.__read_setting_value(0x46)

    def read_deviceInfo(self):
        return self.__read_setting_value(0x47)

    def read_positionOffset(self):
        return self.__read_setting_value(0x5B)

    def read_status(self):
        return self.__read_setting_value(0x9A)
