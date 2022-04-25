#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: Hiroshi Harada (Keigan Inc.)
@author: Takashi Tokuda (Keigan Inc.)
"""
from pykeigan import controller as base
import serial, struct, threading, atexit, time
from pykeigan.utils import *


class USBController(base.Controller):
    def __init__(self, port='/dev/ttyUSB0',debug_mode=False, baud=115200, reconnect=True):
        self.DebugMode = debug_mode
        self.serial_buf = b''  # []
        self.setting_values = {}
        self.__motor_measurement_value = None
        self.__imu_measurement_value = None
        self.__motor_log_value = None
        self.__motor_event_value = None
        self.__read_motion_value = []
        self.worker=None
        self.port = port
        self.read_serial_polling_time = 0.004 
        self.shouldReconnect = reconnect
        self.try_reconnect = False
        self.reconn_err_cnt = 0
        #try to connect to serial port
        try:
            self.serial = serial.Serial(port, baud, 8, 'N', 1, None, False, True, write_timeout=0.1)
        except Exception as e:
            print('Error occured while trying to connect to serial port. Please recheck you USB connection.')
            print('attemping to reinit... ')
            time.sleep(3)
            self.reinit()
            return
            
        self.on_motor_measurement_value_cb = False
        self.on_motor_imu_measurement_cb = False
        self.on_motor_connection_error_cb = False
        self.on_motor_reconnection_cb = False
        self.on_read_motion_read_comp_cb = False
        self.on_motor_log_cb = False
        self.on_motor_event_cb = False
        self.is_check_sum_enabled = False
        self.auto_serial_reading=False
        self.set_interface(self.interface_type['USB'] + self.interface_type['BTN'])
        atexit.register(self.my_cleanup)
        
        #precheck whether data from motor is avaliable or not
        #print('-- precheck reading value')
        try:
            self.start_auto_serial_reading()
            self._read_setting_value(0x46)#motor_name
            self._read_setting_value(0x47)#motor_info
            
        except Exception as e:
            print('Precheck error: '+str(e))
            print('\tattemping to reconnect...')
            time.sleep(1)
            print('...reconnecting...')
            #self.disconnect()
            #self.__init__()
            
    def reinit(self):
        try:
            print('\n...reiniting...\n')
            self.__init__()
            return
        except Exception as e:
            time.sleep(3)
            self.reinit()
    
    def is_connected(self):
        return self.serial.isOpen()
    
    def connect(self):
        """
        Open the USB port.
        Should be after disconnection.
        """
        self.serial.open()
        self.start_auto_serial_reading()
        time.sleep(0.1)
    
    def recover(self):
        self.start_auto_serial_reading()

    def disconnect(self, reconnect=False):
        """
        Close the USB port.
        """
        self.shouldReconnect = reconnect
        self.my_cleanup()
        time.sleep(0.5)
        self.serial.close()

    def reconnect(self):
        if not self.shouldReconnect or self.try_reconnect: return
        self.disconnect(self.shouldReconnect)
        self.reconn_err_cnt=0
        self.try_reconnect = True

        while True:
            self.reconn_err_cnt += 1
            #print('Try reconnecting to : ', self.port," (",self.reconn_err_cnt,")")
            print('Try reconnecting to : '+str(self.port)+" ("+ str(self.reconn_err_cnt)+ ")")
            try:
                self.serial.open()
                self.set_interface(self.interface_type['USB'] + self.interface_type['BTN'])
            except Exception as e:
                # print(e)
                pass
            time.sleep(1)
            try:
                #self.connect()
                rd = self.serial.read(self.serial.inWaiting())
                self.try_reconnect=False
                self.start_auto_serial_reading()
                if (callable(self.on_motor_reconnection_cb)):
                    self.on_motor_reconnection_cb(self.reconn_err_cnt)
                break
            except serial.SerialException as e:
                print('Serial reconnection Failed.', self.reconn_err_cnt,e)
                continue
            except TypeError as e:
                continue
            except IOError as e:
                print('Serial reconnection Failed.', self.reconn_err_cnt,e)
                continue
            except Exception as e:
                break

        self.try_reconnect=False
    
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
        if self.auto_serial_reading:
            return
        self.auto_serial_reading = True
        if self.worker is None:
            self.worker = threading.Thread(target=self.__serial_schedule_worker)
            self.worker.setDaemon(True)
            self.worker.start()
            atexit.register(self.__all_done)

    def finish_auto_serial_reading(self):
        self.auto_serial_reading = False

    def __all_done(self):
        try:
            if self.worker.isAlive():
                self.worker.join(0.01)
                self.serial.close()
        except:
            return

    def _run_command(self, val, characteristics=None):
        try:
            crc_buf = calc_crc16_bytes(val)
            tx_buf = val+crc_buf
            self.serial.write(tx_buf)
        except serial.SerialException as e:
            # There is no new data from serial port
            self.reconnect()
            if (callable(self.on_motor_connection_error_cb)):              
                self.on_motor_connection_error_cb(e)
            return e
        except TypeError as e:
            # Disconnect of USB->UART occured
            self.reconnect()
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e
        except IOError as e:
            self.reconnect()
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            return e

    def __serial_schedule_worker(self):
        while True:
            if self.auto_serial_reading:
                time.sleep(self.read_serial_polling_time) # less than minimum motor measurement interval
                e_res = self.__read_serial_data()
            else:
                print("stop auto_serial_reading")

    def __read_serial_data(self):
        try:
            #print(self.serial.in_waiting, self.serial.inWaiting())
            rd = self.serial.read(self.serial.inWaiting())
        except serial.SerialException as e:
            print('serial.SerialException in __read_serial_data: ', e)
            # There is no new data from serial port
            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            self.reconnect()
            return e
        except TypeError as e:
            # Disconnect of USB->UART occured
            print('TypeError in __read_serial_data: ', e)

            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            self.reconnect()
            return e
        except IOError as e:
            print('IOError in __read_serial_data: ', e)

            if (callable(self.on_motor_connection_error_cb)):
                self.on_motor_connection_error_cb(e)
            self.reconnect()
            return e      

        self.serial_buf += rd

        """
        ------------------------------
        preamble detection logic
        ------------------------------
        """
        bf_len = len(self.serial_buf)
        is_pre = False
        if (bf_len < 8):
            return

        slice_idx = bf_len
        success = False
        i = 0

        while i < bf_len-3:
            # preamble detection
            if not is_pre and self.serial_buf[i:i+4] == b'\x00\x00\xaa\xaa':
                is_pre = True
                slice_idx = i
                for ie in range(i + 4, bf_len-3):
                    # postamble detection
                    if self.serial_buf[ie + 2:ie+4] == b'\x0d\x0a':
                        payload = self.serial_buf[i + 4: ie]
                        # CRC Verification
                        buf_to_validate = self.serial_buf[i + 4: ie + 2]
                        crc = calc_crc16(buf_to_validate)

                        if self.is_check_sum_enabled:
                            if calc_crc16(buf_to_validate) == 0:
                                success = self.__serialdataParse(payload)
                        else:
                            success = self.__serialdataParse(payload)
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
        elif datatype == 0xBA:  # モーター時刻+回転情報受信 モーターFW ver 2.62
            motor_time = bytes2uint32_t(payload[0:4])
            position = bytes2float(payload[4:8])
            velocity = bytes2float(payload[8:12])
            torque = bytes2float(payload[12:16])
            self.__motor_measurement_value = {'position': position, 'velocity': velocity, 'torque': torque,
                                              'received_unix_time': time.time(), 'motor_time': motor_time}
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
                self.setting_values[comm] = payload[3:40].decode('utf-8'), time.time()
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
            #print(payload)
            cmd = bytes2uint8_t(payload[2:3])
            err_code = bytes2uint32_t(payload[3:7])
            try:
                cmd_name = self.command_names[cmd]
            except KeyError:
                print('[Error info] No such command exists. cmd = ', hex(cmd))
                return True
            try:
                err_desc = self.error_codes[err_code]
                # print(err_code)
            except KeyError:
                print('[Error info] No such error_code exists. error_code = ', err_code)
                return True
            self.__motor_log_value={'command_names':cmd,'error_codes':err_code}
            if (callable(self.on_motor_log_cb)):
                self.on_motor_log_cb(self.__motor_log_value)
            if self.DebugMode:
                print(self.__motor_log_value['command_names'],self.__motor_log_value['error_codes'])
            return True
        elif datatype == 0xB7: #Position coordinates of "readMotion" (Motor firmware ver>=2.0)
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
            print("rev time", time.time() - received_unix_time)
            return val
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

    def my_cleanup(self):
        self.finish_auto_serial_reading()
