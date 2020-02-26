#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
from pykeigan import controller as base
import serial, struct, threading, atexit, time
from pykeigan.utils import *


class USBController(base.Controller):
    def __init__(self, port='/dev/ttyUSB0',debug_mode=False):
        self.DebugMode = debug_mode
        self.serial_buf = b''  # []
        self.setting_values = {}
        self.__motor_measurement_value = None
        self.__imu_measurement_value = None
        self.__motor_log_value = None
        self.__motor_event_value = None
        self.__read_motion_value = []
        self.port = port
        self.serial = serial.Serial(port, 115200, 8, 'N', 1, None, False, True)
        self.on_motor_measurement_value_cb = False
        self.on_motor_imu_measurement_cb = False
        self.on_motor_connection_error_cb = False
        self.on_read_motion_read_comp_cb = False
        self.on_motor_log_cb = False
        self.on_motor_event_cb = False
        self.set_interface(self.interface_type['USB'] + self.interface_type['BTN'])
        self.start_auto_serial_reading()

        atexit.register(self.my_cleanup)

    def connect(self):
        """
        Open the USB port.
        """
        self.serial = serial.Serial(self.port, 115200, 8, 'N', 1, None, False, True)

    def disconnect(self):
        """
        Close the USB port.
        """
        self.my_cleanup()
        time.sleep(0.5)
        self.serial.close()

    def start_debug(self):
        """
        Start to print command logs.
        """
        self.DebugMode = True

    def finish_debug(self):
        """
        Finish to print command logs.
        """
        self.DebugMode = False

    def start_auto_serial_reading(self):
        self.auto_serial_reading = True
        self.t = threading.Thread(target=self.__serial_schedule_worker)
        self.t.setDaemon(True)
        self.t.start()
        atexit.register(self.__all_done)

    def finish_auto_serial_reading(self):
        self.auto_serial_reading = False

    def __all_done(self):
        try:
            if self.t.isAlive():
                self.t.join(0.01)
                self.serial.close()
        except:
            return

    def _run_command(self, val, characteristics=None):
        try:
            self.serial.write(val)
        except serial.SerialException as e:
            self.serial.close()
            # There is no new data from serial port
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e
        except TypeError as e:
            # Disconnect of USB->UART occured
            self.serial.close()
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e
        except IOError as e:
            self.serial.close()
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e

    def __serial_schedule_worker(self):
        while True:
            time.sleep(100 / 1000)  # 100ms
            e_res = self.__read_serial_data()
            if e_res or self.auto_serial_reading == False:  # 例外発生でスレッド停止
                self.auto_serial_reading = False
                break

    def __read_serial_data(self):
        # rd = self.serial.read(self.serial.inWaiting())
        try:
            rd = self.serial.read(self.serial.inWaiting())
        except serial.SerialException as e:
            self.serial.close()
            # There is no new data from serial port
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e
        except TypeError as e:
            # Disconnect of USB->UART occured
            self.serial.close()
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e
        except IOError as e:
            self.serial.close()
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e
        '''
        for bt in rd:
            if type(bt) is str:
                self.serial_buf.append(ord(bt))
            elif type(bt) is int:
                self.serial_buf.append(bt)

            #print bt.encode('hex')
        '''
        self.serial_buf += rd
        # ------------------------------#
        #   プリアンブル検出ロジック　
        # ------------------------------#

        bf_len = len(self.serial_buf)
        is_pre = False  # プリアンブル検出したか
        if (bf_len < 8):
            return

        slice_idx = bf_len  # 抽出済みとしてバッファーから削除するインデックス

        i = 0
        while i < bf_len-3:
            # プリアンブル検出
            if not is_pre and self.serial_buf[i:i+4] == b'\x00\x00\xaa\xaa':
                is_pre = True
                slice_idx = i #ポストアンブルが見つからなかったときプリアンブルより前をバッファーから削除
                for ie in range(i + 4, bf_len-3):
                    # ポストアンブル検出
                    if self.serial_buf[ie + 2:ie+4] == b'\x0d\x0a':
                        # crc = self.serial_buf[ie] << 8 | self.serial_buf[ie + 1]  # CRC
                        payload = self.serial_buf[i + 4: ie]  # 情報バイト
                        self.__serialdataParse(payload)
                        slice_idx = ie + 4
                        i = ie + 3
                        is_pre = False
                        break
            i += 1
        self.serial_buf = self.serial_buf[slice_idx:]

    def __serialdataParse(self, byte_array):
        v_len = len(byte_array)
        if (v_len < 3 or bytes2uint8_t(byte_array[0:1]) != v_len):
            return False
        datatype = bytes2uint8_t(byte_array[1:2])
        payload = byte_array[2:]
        if datatype == 0xB4:  # モーター回転情報受信
            position = bytes2float(payload[0:4])
            velocity = bytes2float(payload[4:8])
            torque = bytes2float(payload[8:12])
            self.__motor_measurement_value = {'position': position, 'velocity': velocity, 'torque': torque,
                                              'received_unix_time': time.time()}
            if (callable(self.on_motor_measurement_value_cb)):
                self.on_motor_measurement_value_cb(self.__motor_measurement_value)
            return True
        elif datatype == 0xB5:  # IMU情報受信
            accel_x = bytes2int16_t(payload[0:2]) * 2.0 / 32767
            accel_y = bytes2int16_t(payload[2:4]) * 2.0 / 32767
            accel_z = bytes2int16_t(payload[4:6]) * 2.0 / 32767
            temp = bytes2int16_t(payload[6:8]) / 333.87 + 21.00
            gyro_x = bytes2int16_t(payload[8:10]) * 0.00013316211
            gyro_y = bytes2int16_t(payload[10:12]) * 0.00013316211
            gyro_z = bytes2int16_t(payload[12:14]) * 0.00013316211
            self.__imu_measurement_value = {'accel_x': accel_x, 'accel_y': accel_y, 'accel_z': accel_z, 'temp': temp,
                                            'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z,
                                            'received_unix_time': time.time()}
            if (callable(self.on_motor_imu_measurement_cb)):
                self.on_motor_imu_measurement_cb(self.__imu_measurement_value)
            return True
        elif datatype == 0x40: #Register infomations
            float_value_comms = [0x02, 0x03, 0x07, 0x08, 0x0E, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20,
                                 0x21, 0x5B]
            comm = bytes2uint8_t(payload[2:3])
            if comm in float_value_comms:
                self.setting_values[comm] = bytes2float(payload[3:7]), time.time()
                return True
            elif comm == 0x05:
                self.setting_values[comm] = bytes2uint8_t(payload[3:4]), time.time()
                return True
            elif comm == 0x3A:
                self.setting_values[comm] = (bytes2uint8_t(payload[3:4]), bytes2uint8_t(payload[4:5]), bytes2uint8_t(payload[5:6])), time.time()
                return True
            elif comm == 0x46:
                self.setting_values[comm] = payload[3:16].decode('utf-8'), time.time()
                return True
            elif comm == 0x47:
                self.setting_values[comm] = payload[3:34].decode('utf-8'), time.time()
                return True
            elif comm == 0x9A:
                bits_list = [int(n) for n in bin(bytes2uint8_t(payload[3:4]))[2:].zfill(8)]
                self.setting_values[comm] = {"isCheckSumEnabled": bits_list[0], "iMUMeasurement": bits_list[4],
                                             "motorMeasurement": bits_list[5], "queue": bits_list[6],
                                             "motorEnabled": bits_list[7],
                                             "flash_memory_state": self.flash_memory_states[
                                                 bytes2uint8_t(payload[4:5])],
                                             "motor_control_mode": self.motor_control_modes[
                                                 bytes2uint8_t(payload[5:6])]}, time.time()
                return True
            else:
                return False
        elif datatype == 0xBE:  # command log (Error or Success information)
            self.__motor_log_value={'command_names':self.command_names[bytes2uint8_t(payload[2:3])],'error_codes':self.error_codes[bytes2uint32_t(payload[3:7])]}
            if (callable(self.on_motor_log_cb)):
                self.on_motor_log_cb(self.__motor_log_value)
            if self.DebugMode:
                print(self.__motor_log_value['command_names'],self.__motor_log_value['error_codes'])
            return True
        elif datatype == 0xB7: #Position coordinates of "readMotion" (Motor farm ver>=2.0)
            motion_index=bytes2uint16_t(payload[0:2])
            total_pos_len = bytes2uint32_t(payload[2:6])
            payload_fast_pos_idx=bytes2uint32_t(payload[6:10])
            payload_pos_len=bytes2uint32_t(payload[10:14])
            ar=[]
            for i in range(payload_pos_len):
                try:
                    ar.append(bytes2float(payload[14+(i*4):18+(i*4)]))
                except:
                    break
            try:
                del self.__read_motion_value[payload_fast_pos_idx:]
            except:
                pass
            self.__read_motion_value.extend(ar)

            if(len(self.__read_motion_value) >= total_pos_len): #Completed receiving all data
                if (callable(self.on_read_motion_read_comp_cb)):
                    self.on_read_motion_read_comp_cb(motion_index, self._read_motion_value())
            return True
        elif datatype == 0xCE:  # Event notification from KeiganMotor. (MotorFarmVar >2.28)
            self.__motor_event_value={'event_type':self.event_types[bytes2uint8_t(payload[0:1])],'number':bytes2uint8_t(payload[1:2]),'state':bytes2uint8_t(payload[2:3])}
            if (callable(self.on_motor_event_cb)):
                self.on_motor_event_cb(self.__motor_event_value)

            return True            
        else:  # Unknown data
            return False

    def _read_setting_value(self, comm, validation_threshold=1.0):#Register infomation
        float_value_comms = [0x02, 0x03, 0x07, 0x08, 0x0E, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x21,
                             0x5B]
        valid_comms = [0x05, 0x3A, 0x46, 0x47, 0x9A]
        valid_comms.extend(float_value_comms)
        if not (comm in valid_comms):
            raise ValueError("Unknown Command")
        self.read_register(comm)
        time.sleep(0.15)
        if not self.auto_serial_reading:
            raise ValueError("Disabled reading serial data. Try calling start_auto_serial_reading()")
        if comm in self.setting_values.keys():
            val, received_unix_time = self.setting_values[comm]
            if time.time() - received_unix_time < validation_threshold:
                return val
            else:
                raise ValueError("No data within ", validation_threshold, " sec")
        else:
            raise ValueError("No data received")

    def __read_measurement_value(self, comm, validation_threshold=1.0):
        measurement_value=None
        if not (comm in [0xB4, 0xB5]):
            raise ValueError("Unknown Command")
        if not self.auto_serial_reading:
            raise ValueError("Disabled reading serial data. Try calling start_serial_reading().")
        if comm == 0xB4:
            measurement_value = self.__motor_measurement_value
        elif comm == 0xB5:
            measurement_value = self.__imu_measurement_value
        if measurement_value is None:
            if comm == 0xB4:
                raise ValueError("No data received. Try calling enable_continual_motor_measurement().")
            if comm == 0xB5:
                raise ValueError("No data received. Try calling enable_continual_imu_measurement().")
        elif time.time() - measurement_value['received_unix_time'] < validation_threshold:
            return measurement_value
        else:
            if comm == 0xB4:
                raise ValueError("No data within ", validation_threshold, " sec.")
            if comm == 0xB5:
                raise ValueError("No data within ", validation_threshold, " sec.")

    def _read_motion_value(self):
        return self.__read_motion_value

    def read_motor_measurement(self):
        return self.__read_measurement_value(0xB4)

    def read_imu_measurement(self):
        return self.__read_measurement_value(0xB5)


    #修了イベント　測定値のスレッドを停止する後処理
    def my_cleanup(self):
        self.finish_auto_serial_reading()
