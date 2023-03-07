#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
@author: harada@keigan.co.jp
"""
import serial,struct,threading,atexit,time
from pykeigan.utils import *

class Controller:
    def __init__(self):
        pass

    def _run_command(self,val,characteristics):
        pass
    @property
    def flash_memory_states(self):
        return {0:"FLASH_STATE_READY",1:"FLASH_STATE_TEACHING_PREPARE",2:"FLASH_STATE_TEACHING_DOING",3:"FLASH_STATE_PLAYBACK_PREPARE",4:"FLASH_STATE_PLAYBACK_DOING",5:"FLASH_STATE_PLAYBACK_PAUSING",6:"FLASH_STATE_TASKSET_RECORDING",7:"FLASH_STATE_TASKSET_DOING",8:"FLASH_STATE_TASKSET_PAUSING",20:"FLASH_STATE_IMU"}

    @property
    def motor_control_modes(self):
        return {0:"MOTOR_CONTROL_MODE_NONE",1:"MOTOR_CONTROL_MODE_VELOCITY",2:"MOTOR_CONTROL_MODE_POSITION",3:"MOTOR_CONTROL_MODE_TORQUE",0xFF:"MOTOR_CONTROL_MODE_OTHERS"}
    
    @property
    def baud_rates(self):
        return {0:"115200",1:"230400",2:"250000",3:"460800",4:"921600",5:"1000000"}

    @property
    def error_codes(self):
        return {
                0x00:"KM_SUCCESS",
                0x03:"KM_ERROR_NOT_FOUND",
                0x05:"KM_ERROR_INVALID_COMMAND",
                0x06:"KM_ERROR_INVALID_PARAM",
                0x07:"KM_ERROR_STORAGE_FULL",
                0x08:"KM_ERROR_INVALID_FLASH_STATE", 
                0x09:"KM_ERROR_INVALID_LENGTH",
                0x0A:"KM_ERROR_INVALID_CHECKSUM",
                0x0F:"KM_ERROR_FORBIDDEN",
                0x10:"KM_ERROR_INVALID_ADDR",
                0x14:"KM_ERROR_MOTOR_DISABLED",
                0x46:"KM_ERROR_NRF_DEVICE", 
                0x50:"KM_ERROR_WDT_EVENT",
                0x51:"KM_ERROR_OVER_HEAT",
                0x64:"KM_SUCCESS_ARRIVAL"
                }
    
    @property
    def command_names(self):
        return {
                0x00:"unknown",
                0x02:"set_max_speed",
                0x03:"set_min_speed",
                0x05:"set_curve_type",
                0x07:"set_acc",
                0x08:"set_dec",
                0x0e:"set_max_torque",
                0x16:"set_teaching_interval",
                0x17:"set_playback_interval",
                0x18:"set_qcurrent_p",
                0x19:"set_qcurrent_i",
                0x1A:"set_qcurrent_d",
                0x1B:"set_speed_p",
                0x1C:"set_speed_i",
                0x1D:"set_speed_d",
                0x1E:"set_position_p",
                0x1F:"set_position_i",
                0x20:"set_position_d",
                0x21:"set_pos_control_threshold",
                0x22:"reset_all_pid",
                0x23:"set_pid_table_value",
                0x24:"select_pid_table",
                0x25:"read_pid_table",
                0x27:"set_low_pass_filter",
                0x2B:"set_notify_pos_arrival_settings",
                0x2C:"set_motor_measurement_interval",
                0x2D:"set_motor_measurement_settings",
                0x2E:"set_interface",
                0x30:"set_response",
                0x31:"set_safe_run_settings",
                0x32:"set_safety_settings",
                0x33:"set_limit_current",
                0x37:"set_linkage_key",
                0x3A:"set_own_color",
                0x3C:"set_imu_measurement_interval",
                0x3D:"set_imu_measurement_settings",
                0x40:"read_register",
                0x41:"save_all_registers",
                0x46:"read_device_name",
                0x47:"read_device_info",
                0x4E:"reset_register",
                0x4F:"reset_all_registers",
                0x50:"disable_action",
                0x51:"enable_action",
                0x58:"set_speed",
                0x5A:"preset_position",
                0x5B:"get_position_offset",
                0x60:"run_forward",
                0x61:"run_reverse",
                0x62:"run_at_velocity",
                0x65:"move_to_pos",
                0x66:"move_to_pos",
                0x67:"move_by_dist",
                0x68:"move_by_dist",
                0x6A:"enable_action_task",
                0x6B:"disable_action_task",
                0x6C:"free_motor",
                0x6D:"stop_motor",
                0x72:"hold_torque",
                0x75:"move_to_pos_wait",
                0x76:"move_to_pos_wait",
                0x77:"move_by_dist_wait",
                0x78:"move_by_dist_wait",
                0x81:"start_doing_taskset",
                0x82:"stop_doing_taskset",
                0x85:"start_playback_motion",
                0x86:"prepare_playback_motion",
                0x87:"start_playback_motion_from_prep",
                0x88:"stop_playback_motion",
                0x90:"pause_queue",
                0x91:"resume_queue",
                0x92:"wait_queue",
                0x94:"erase_task",
                0x95:"clear_queue",
                0x96:"wait_queue_until_input",
                0x9A:"read_status",
                0xA0:"start_recording_taskset",
                0xA2:"stop_recording_taskset",
                0xA3:"erase_taskset",
                0xA4:"erase_all_tasksets",
                0xA5:"set_taskset_name",
                0xA6:"read_taskset_info",
                0xA7:"read_taskset_usage",
                0xA8:"set_trigger_taskset_settings",
                0xA9:"start_teaching_motion",
                0xAA:"prepare_teaching_motion",
                0xAB:"start_teaching_motion_from_prep",
                0xAC:"stop_teaching_motion",
                0xAD:"erase_motion",
                0xAE:"erase_all_motions",
                0xAF:"set_motion_name",
                0xB0:"read_motion_info",
                0xB1:"read_motion_usage",
                0xB2:"set_trigger_motion_settings",
                0xB7:"read_motion",
                0xB8:"write_motion_position",
                0xBC:"set_autostart_setting",
                0xBD:"set_button_setting",
                0xBE:"read_error",
                0xC0:"set_i2c_address",
                0xC3:"set_baud_rate",
                0xE0:"set_led",
                0xE6:"enable_motor_measurement",
                0xE7:"disable_motor_measurement",
                0xEA:"enable_imu_measurement",
                0xEB:"disable_imu_measurement",
                0xF0:"reboot",
                0xF3:"enable_check_sum"
                }
    
    @property
    def event_types(self):
        return {1:"button", 10:"gpio"}
    
    # Settings
    def set_max_speed(self,max_speed,identifier=b'\x00\x00'):
        """
        Set the maximum speed of rotation to the 'max_speed' in rad/sec.
        """
        command=b'\x02'
        values=float2bytes(max_speed)
        self._run_command(command+identifier+values,'motor_rx')

    def set_min_speed(self,min_speed,identifier=b'\x00\x00'):
        """
        Set the minimum speed of rotation to the 'min_speed' in rad/sec.
        """
        command=b'\x03'
        values=float2bytes(min_speed)
        self._run_command(command+identifier+values,'motor_rx')

    def set_curve_type(self,curve_type,identifier=b'\x00\x00'):
        """
        Set the acceleration or deceleration curve to the 'curve_type'.
        typedef enum curveType =
        {
            CURVE_TYPE_NONE = 0, // Turn off Motion control
            CURVE_TYPE_TRAPEZOID = 1, // Turn on Motion control with trapezoidal curve
            CURVE_TYPE_DIRECT_POS = 10 // Turn off Motion control (Direct position control)
        }
        """
        command=b'\x05'
        values=uint8_t2bytes(curve_type)
        self._run_command(command+identifier+values,'motor_rx')

    def set_acc(self,_acc,identifier=b'\x00\x00'):
        """
        Set the acceleration of rotation to the positive 'acc' in rad/sec^2.
        """
        command=b'\x07'
        values=float2bytes(_acc)
        self._run_command(command+identifier+values,'motor_rx')

    def set_dec(self,_dec,identifier=b'\x00\x00'):
        """
        Set the deceleration of rotation to the positive 'dec' in rad/sec^2.
        """
        command=b'\x08'
        values=float2bytes(_dec)
        self._run_command(command+identifier+values,'motor_rx')

    def set_max_torque(self,max_torque,identifier=b'\x00\x00'):
        """
        Set the maximum torque to the positive 'max_torque' in N.m.
        """
        command=b'\x0E'
        if max_torque < 0:
            raise ValueError("Value out of range")
        values=float2bytes(max_torque)
        self._run_command(command+identifier+values,'motor_rx')

    def set_teaching_interval(self,interval_ms,identifier=b'\x00\x00'):
        """
        Set the interval time of teaching to the positive integer "interval_ms" in ms.
        """
        command=b'\x16'
        values=uint32_t2bytes(interval_ms)
        self._run_command(command+identifier+values,'motor_rx')

    def set_playback_interval(self,interval_ms,identifier=b'\x00\x00'):
        """
        Set the interval time of playback to the positive integer "interval_ms" in ms.
        """
        command=b'\x17'
        values=uint32_t2bytes(interval_ms)
        self._run_command(command+identifier+values,'motor_rx')

    def set_qcurrent_p(self,q_current_p,identifier=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Proportional gain to the postiive 'q_current_p'.
        """
        command=b'\x18'
        values=float2bytes(q_current_p)
        self._run_command(command+identifier+values,'motor_rx')

    def set_qcurrent_i(self,q_current_i,identifier=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Integral gain to the positive 'q_current_i'.
        """
        command=b'\x19'
        values=float2bytes(q_current_i)
        self._run_command(command+identifier+values,'motor_rx')

    def set_qcurrent_d(self,q_current_d,identifier=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Differential gain to the postiive 'q_current_d'.
        """
        command=b'\x1A'
        values=float2bytes(q_current_d)
        self._run_command(command+identifier+values,'motor_rx')

    def set_speed_p(self,speed_p,identifier=b'\x00\x00'):
        """
        Set the speed PID controller's Proportional gain to the positive 'speed_p'.
        """
        command=b'\x1B'
        values=float2bytes(speed_p)
        self._run_command(command+identifier+values,'motor_rx')

    def set_speed_i(self,speed_i,identifier=b'\x00\x00'):
        """
        Set the speed PID controller's Integral gain to the positive 'speed_i'.
        """
        command=b'\x1C'
        values=float2bytes(speed_i)
        self._run_command(command+identifier+values,'motor_rx')

    def set_speed_d(self,speed_d,identifier=b'\x00\x00'):
        """
        Set the speed PID controller's Deferential gain to the positive 'speed_d'.
        """
        command=b'\x1D'
        values=float2bytes(speed_d)
        self._run_command(command+identifier+values,'motor_rx')

    def set_position_p(self,position_p,identifier=b'\x00\x00'):
        """
        Set the position PID controller's Proportional gain to the positive 'position_p'.
        """
        command=b'\x1E'
        values=float2bytes(position_p)
        self._run_command(command+identifier+values,'motor_rx')

    def set_position_i(self,position_i,identifier=b'\x00\x00'):
        """
        Set the position PID controller's Integral gain to the positive 'position_i'.
        """
        command=b'\x1F'
        values=float2bytes(position_i)
        self._run_command(command+identifier+values,'motor_rx')

    def set_position_d(self,position_d,identifier=b'\x00\x00'):
        """
        Set the position PID controller's Differential gain to the positive 'position_d'.
        """
        command=b'\x20'
        values=float2bytes(position_d)
        self._run_command(command+identifier+values,'motor_rx')

    def set_pos_control_threshold(self,poscontrol_d,identifier=b'\x00\x00'):
        """
        Set the threshold of the deviation between the target and current position. While the deviation is more than the threshold, integral and differential gain is set to be zero.
        """
        command=b'\x21'
        values=float2bytes(poscontrol_d)
        self._run_command(command+identifier+values,'motor_rx')

    def reset_all_pid(self,identifier=b'\x00\x00'):
        """
        Reset all the PID parameters to the firmware default settings.
        """
        command=b'\x22'
        self._run_command(command+identifier,'motor_rx')

    def set_motor_measurement_interval(self,interval,identifier=b'\x00\x00'):
        """
        Set the notification interval of motor measurement values. It is valid only for USB(UART) and BLE.
        In case of BLE, the allowed minimum value is 100 [ms]. 
        -----------
        0:      2 [ms]
        1:      5 [ms]
        2:     10 [ms]
        3:     20 [ms]
        4:     50 [ms]
        5:    100 [ms]
        6:    200 [ms]
        7:    500 [ms]
        8:   1000 [ms]
        9:   2000 [ms]
        10:  5000 [ms]
        11: 10000 [ms]
        -----------        
        """
        command=b'\x2C'
        values = uint8_t2bytes(interval)
        self._run_command(command+identifier+values,'motor_rx')

    def set_motor_measurement_settings(self,flag,identifier=b'\x00\x00'):
        """
        Set the notification setting of motor measurement values.
        -----------
        bit7: -
        bit6: -
        bit5: -
        bit4: -
        bit3: -
        bit2: -
        bit1: Notification of motor measurement (1:ON, 0:OFF)
        bit0: To start Notification of motor measurement when booting(1:ON, 0:OFF)
        -----------
        """
        command=b'\x2D'
        values=uint8_t2bytes(flag)
        self._run_command(command+identifier+values,'motor_rx')

    def set_limit_current(self,limit,identifier=b'\x00\x00'):

        """
        Set current limit threshold to cut off. It is based on Iq current.
        Please use this function if you are using 
        """
        
        command=b'\x33'
        values=float2bytes(limit)

        self._run_command(command+identifier+values,'motor_rx')

    @property
    def interface_type(self):
        return {
            "BLE": 0b1,
            "USB": 0b1000,
            "I2C": 0b10000,
            "BTN": 0b10000000,
        }

    def set_interface(self,flag,identifier=b'\x00\x00'):
        """
        You can enable or disable the data interfaces(physical 3 buttons, I2C, USB and BLE).
        The motor chooses the output interface of motor measurement values and IMU values as
        (High priority)BLE > USB > I2C(Low priority) by default.
        If you want to force it to send measurement values through USB,
        you need to set bit0(BLE) to OFF(0) and bit3(USB) to ON(1).
        For example, if you call set_interface(0b10001000), Physical 3 buttons: enabled, I2C: disabled, USB: enabled and BLE: disabled.
        To save this setting to the flash memory, ensure you call saveAllRegisters().@n
        -----------
        - bit7: Physical 3 buttons
        - bit6: UART2
        - bit5: Digital In
        - bit4: I2C(Wired)
        - bit3: UART1(USB, Wired)
        - bit2: -
        - bit1: Linkage
        - bit0: BLE(Wireless)
        -----------
        """
        command=b'\x2E'
        values=uint8_t2bytes(flag)
        self._run_command(command+identifier+values,'motor_rx')

    def set_safe_run_settings(self,isEnabled,timeout,stopAction,identifier=b'\x00\x00'):
        """set_safe_run_settings

        Set safe run mode to stop motor automatically when it cannot receive next command within a certain period (timeout).

        Args:
            isEnabled (bool): true if setting safe run mode enabled
            timeout (int): stop action will occur after this period
            stopAction (int):
                - 0: free_motor
                - 1: disable_motor_action
                - 2: stop_motor
                - 3: Fix to the current position (move_to)
        """
        command=b'\x31'
        values=uint8_t2bytes(isEnabled)+uint32_t2bytes(timeout)+uint8_t2bytes(stopAction)
        self._run_command(command+identifier+values,'motor_rx')

    def set_own_color(self,red,green,blue,identifier=b'\x00\x00'):
        """
        Set the own LED color(red:0-255, green:0-255, blue:0-255).
        """
        command=b'\x3A'
        values=uint8_t2bytes(red)+uint8_t2bytes(green)+uint8_t2bytes(blue)
        self._run_command(command+identifier+values,'motor_rx')

    def set_imu_measurement_interval(self,interval,identifier=b'\x00\x00'):
        """
        Set the notification interval of IMU measurement values. It is valid only for USB(UART) and BLE.
        In case of BLE, the allowed minimum value is 100 [ms]. 
        -----------
        0:     10 [ms]
        1:     20 [ms]
        2:     50 [ms]
        3:    100 [ms]
        4:    200 [ms]
        5:    500 [ms]
        6:   1000 [ms]
        7:   2000 [ms]
        9:   5000 [ms]
        10: 10000 [ms]
        -----------     
        """
        command=b'\x3C'
        values = uint8_t2bytes(interval)
        self._run_command(command+identifier+values,'motor_rx')

    def set_imu_measurement_settings(self,flag,identifier=b'\x00\x00'):
        """
        Set the notification setting of IMU.
        -----------
        bit7: -
        bit6: -
        bit5: -
        bit4: -
        bit3: -
        bit2: -
        bit1: Notification of IMU (1:ON, 0:OFF)
        bit0: To start Notification of IMU when booting(1:ON, 0:OFF)
        -----------
        """
        command=b'\x3D'
        values=uint8_t2bytes(flag)
        self._run_command(command+identifier+values,'motor_rx')

    def set_autostart_setting(self, mode, identifier=b'\x00\x00'):
        """
        Set the button setting  (Motor Firmware Ver. requires >= 2.42)
        -----------
        mode = 0:  Without auto start 
        mode = 1:  Auto start doing taskset (config by set_taskset_trigger_settings)
        mode = 2:  Auto start playback motion (config by set_motion_trigger_settings)
        -----------
        """
        command=b'\xBC'
        values=uint8_t2bytes(mode)
        self._run_command(command+identifier+values,'motor_rx')


    def set_button_setting(self, mode, identifier=b'\x00\x00'):
        """
        Set the button setting  (MotorFirmVer. >= 2.28)
        -----------
        mode = 0:  Manual button mode with Motion 
        mode = 1:  Manual button mode with Taskset
        mode = 30: Child button mode (Receive button action event from KeiganMotor)
        -----------
        """
        command=b'\xBD'
        values=uint8_t2bytes(mode)
        self._run_command(command+identifier+values,'motor_rx')

    def set_baud_rate(self, baud, identifier=b'\x00\x00'):
        """
        Set baud rate for serial communication setting 
        (baud rate unit is kbps)
        -----------
        0: 115200 
        1: 230400 
        2: 250000
        3: 460800
        4: 921600
        5: 1000000 (1M)
        -----------
        """
        command=b'\xC3'
        values=uint8_t2bytes(baud)
        self._run_command(command+identifier+values,'motor_rx')


    def set_notify_pos_arrival_settings(self, isEnabled, tolerance, settleTime, identifier=b'\x00\x00'):
        """
        Set notification settings when arriving at the target position 
        """
        command=b'\x2B'
        values=uint8_t2bytes(isEnabled)+float2bytes(tolerance)+uint32_t2bytes(settleTime)
        self._run_command(command+identifier+values,'motor_rx')


    def read_register(self,register,identifier=b'\x00\x00'):
        '''
        Read a specified setting (register).
        '''
        command=b'\x40'
        values=uint8_t2bytes(register)
        self._run_command(command+identifier+values,'motor_rx')

    def save_all_registers(self,identifier=b'\x00\x00'):
        """
        Save all settings (registers) in flash memory.
        """
        command=b'\x41'
        self._run_command(command+identifier,'motor_rx')
        time.sleep(3) # wait for next command to store registers in flash

    def reset_register(self,register,identifier=b'\x00\x00'):
        """
        Reset a specified register's value to the firmware default setting.
        """
        command=b'\x4E'
        values=uint8_t2bytes(register)
        self._run_command(command+identifier+values,'motor_rx')

    def reset_all_registers(self,identifier=b'\x00\x00'):
        """
        Reset all registers' values to the firmware default setting.
        """
        command=b'\x4F'
        self._run_command(command+identifier,'motor_rx')

    # Motor Action
    def disable_action(self,identifier=b'\x00\x00'):
        """
        Disable motor action.
        """
        command=b'\x50'
        self._run_command(command+identifier,'motor_tx')

    def enable_action(self,identifier=b'\x00\x00'):
        """
        Enable motor action.
        """
        command=b'\x51'
        self._run_command(command+identifier,'motor_tx')

    def set_speed(self,speed,identifier=b'\x00\x00'):
        """
        Set the speed of rotation to the positive 'speed' in rad/sec.
        """
        command=b'\x58'
        values=float2bytes(speed)
        self._run_command(command+identifier+values,'motor_tx')

    def preset_position(self,position,identifier=b'\x00\x00'):
        """
        Preset the current absolute position as the specified 'position' in rad. (Set it to zero when setting origin)
        """
        command=b'\x5A'
        values=float2bytes(position)
        self._run_command(command+identifier+values,'motor_tx')

    def get_position_offset(self,position,identifier=b'\x00\x00'):
        """
        Get the offset value of the absolute position.
        """
        command=b'\x5B'
        values=float2bytes(position)
        self._run_command(command+identifier+values,'motor_tx')

    def run_forward(self,identifier=b'\x00\x00'):
        """
        Rotate the motor forward (counter clock-wise) at the speed set by 0x58: speed.
        """
        command=b'\x60'
        self._run_command(command+identifier,'motor_tx')

    def run_reverse(self,identifier=b'\x00\x00'):
        """
        Rotate the motor reverse (clock-wise) at the speed set by 0x58: speed.
        """
        command=b'\x61'
        self._run_command(command+identifier,'motor_tx')

    def run_at_velocity(self,velocity,identifier=b'\x00\x00'):
        """
        Rotate the motor at the 'velocity'. The velocity can be positive or negative.
        """
        command=b'\x62'
        values=float2bytes(velocity)
        self._run_command(command+identifier+values,'motor_tx')

    def move_to_pos(self,position,speed=None,identifier=b'\x00\x00'):
        """
        Move the motor to the specified absolute 'position' at the 'speed'.
        If the speed is None, move at the speed set by 0x58: set_speed.
        """
        if speed is not None:
            command=b'\x65'
            values=float2bytes(position)+float2bytes(speed)
        else:
            command=b'\x66'
            values=float2bytes(position)
        self._run_command(command+identifier+values,'motor_tx')

    def move_by_dist(self,distance,speed=None,identifier=b'\x00\x00'):
        """
        Move the motor by the specified relative 'distance' from the current position at the 'speed'.
        If the speed is None, move at the speed set by 0x58: set_speed.
        """
        if speed is not None:
            command=b'\x67'
            values=float2bytes(distance)+float2bytes(speed)
        else:
            command=b'\x68'
            values=float2bytes(distance)
        self._run_command(command+identifier+values,'motor_tx')

    def move_to_pos_wait(self,position,speed=None,identifier=b'\x00\x00'):
        """
        Move the motor to the specified absolute 'position' at the 'speed'.
        It pauses the queue to handle commands in motor side at the same time.
        "Queue" will resume automatically if it arrives at the target position.
        See "set_notify_pos_arrival_settings" to change parameters such as the tolerance.
        If the speed is None, move at the speed set by 0x58: set_speed.
        """
        if speed is not None:
            command=b'\x75'
            values=float2bytes(position)+float2bytes(speed)
        else:
            command=b'\x76'
            values=float2bytes(position)
        self._run_command(command+identifier+values,'motor_tx')

    def move_by_dist_wait(self,distance,speed=None,identifier=b'\x00\x00'):
        """
        Move the motor by the specified relative 'distance' from the current position at the 'speed'.
        It pauses the queue to handle commands in motor side at the same time.
        The queue will be resumed automatically if it arrives at the target position.
        See "set_notify_pos_arrival_settings" to change parameters such as the tolerance.
        If the speed is None, move at the speed set by 0x58: set_speed.
        """
        if speed is not None:
            command=b'\x77'
            values=float2bytes(distance)+float2bytes(speed)
        else:
            command=b'\x78'
            values=float2bytes(distance)
        self._run_command(command+identifier+values,'motor_tx')

    def disable_action_task(self,identifier=b'\x00\x00'):
        """
        Disable motor action. (Firmware ver. requires >= 2.42)
        This function can be stored in taskset, while disable_action() cannot be stored.
        """       
        command=b'\x6A'
        self._run_command(command+identifier,'motor_tx') 

    def enable_action_task(self,identifier=b'\x00\x00'):
        """
        Enable motor action. (Firmware ver. requires >= 2.42)
        This function can be stored in taskset, while enable_action() cannot be stored.
        """       
        command=b'\x6B'
        self._run_command(command+identifier,'motor_tx') 

    def free_motor(self,identifier=b'\x00\x00'):
        """
        Stop the motor's excitation
        """
        command=b'\x6C'
        self._run_command(command+identifier,'motor_tx')

    def stop_motor(self,identifier=b'\x00\x00'):
        """
        Decelerate the speed to zero and stop.
        """
        command=b'\x6D'
        self._run_command(command+identifier,'motor_tx')

    def hold_torque(self,torque,identifier=b'\x00\x00'):
        """
        Keep and output the specified torque.
        """
        command=b'\x72'
        values=float2bytes(torque)
        self._run_command(command+identifier+values,'motor_tx')

    def start_doing_taskset(self,index,repeating,identifier=b'\x00\x00'):
        """
        Do taskset at the specified 'index' 'repeating' times.
        """
        command=b'\x81'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)
        self._run_command(command+identifier+values,'motor_tx')

    def stop_doing_taskset(self,identifier=b'\x00\x00'):
        """
        Stop doing the current taskset.
        """
        command=b'\x82'
        self._run_command(command+identifier,'motor_tx')

    def start_playback_motion(self,index,repeating,option,identifier=b'\x00\x00'):
        """
        Start to playback motion at the specified 'index' 'repeating' times.
        """
        command=b'\x85'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)+uint8_t2bytes(option)
        self._run_command(command+identifier+values,'motor_tx')

    def prepare_playback_motion(self,index,repeating,option,identifier=b'\x00\x00'):
        """
        Prepare to playback motion at the specified 'index' 'repeating' times.
        """
        command=b'\x86'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)+uint8_t2bytes(option)
        self._run_command(command+identifier+values,'motor_tx')

    def start_playback_motion_from_prep(self,identifier=b'\x00\x00'):
        """
        Start to playback motion in the condition of the last preparePlaybackMotion.
        """
        command=b'\x87'
        self._run_command(command+identifier,'motor_tx')

    def stop_playback_motion(self,identifier=b'\x00\x00'):
        """
        Stop to playback motion.
        """
        command=b'\x88'
        self._run_command(command+identifier,'motor_tx')

    # Queue
    def pause_queue(self,identifier=b'\x00\x00'):
        """
        Pause the queue until 0x91: resume is executed.
        """
        command=b'\x90'
        self._run_command(command+identifier,'motor_tx')

    def resume_queue(self,identifier=b'\x00\x00'):
        """
        Resume the queue.
        """
        command=b'\x91'
        self._run_command(command+identifier,'motor_tx')

    def wait_queue(self,waittime,identifier=b'\x00\x00'):
        """
        Wait the queue or pause the queue for the specified 'time' in msec and resume it automatically.
        """
        command=b'\x92'
        values=uint32_t2bytes(waittime)
        self._run_command(command+identifier+values,'motor_tx')

    def clear_queue(self,identifier=b'\x00\x00'):
        """
        Clear the queue. Erase all tasks in the queue. This command works when 0x90: pause or 0x92: wait are executed.
        """
        command=b'\x95'
        self._run_command(command+identifier,'motor_tx')


    def wait_queue_until_input(self, pin, event=2, timeout=0, sub_pin1=0xFF, sub_state1=0, sub_pin2=0xFF, sub_state2=0, sub_pin3=0xFF, sub_state3=0, identifier=b'\x00\x00'):
        """
        Wait the queue or pause the queue for the specified GPIO digital pin event.
        It is resumd automatically if timeout[ms] passed.
        event parameter is as follows.
        -----------
        1: RISING (Low to High) 
        2: FALLING (High to Low)
        -----------
        """
        command=b'\x96'
        values=uint8_t2bytes(pin)+uint8_t2bytes(event)+uint32_t2bytes(timeout)+uint8_t2bytes(sub_pin1)+uint8_t2bytes(sub_state1)+uint8_t2bytes(sub_pin2)+uint8_t2bytes(sub_state2)+uint8_t2bytes(sub_pin3)+uint8_t2bytes(sub_state3)
        self._run_command(command+identifier+values,'motor_tx')        


    # Taskset
    def start_recording_taskset(self,index,identifier=b'\x00\x00'):
        """
        Start recording taskset at the specified 'index' in the flash memory.
        In the case of KM-1, index value is from 0 to 49 (50 in total).
        """
        command=b'\xA0'
        values=uint16_t2bytes(index)
        self._run_command(command+identifier+values,'motor_tx')

    def stop_recording_taskset(self,identifier=b'\x00\x00'):
        """
        Stop recording taskset.
        This command works while 0xA0: startRecordingTaskset is executed.
        """
        command=b'\xA2'
        self._run_command(command+identifier,'motor_tx')

    def erase_taskset(self,index,identifier=b'\x00\x00'):
        """
        Erase taskset at the specified index in the flash memory.
        In the case of KM-1, index value is from 0 to 49 (50 in total).
        """
        command=b'\xA3'
        values=uint16_t2bytes(index)
        self._run_command(command+identifier+values,'motor_tx')

    def erase_all_tasksets(self,identifier=b'\x00\x00'):
        """
        Erase all tasksets in the flash memory.
        """
        command=b'\xA4'
        self._run_command(command+identifier,'motor_tx')

    def set_trigger_taskset_settings(self,index,repeating,identifier=b'\x00\x00'):
        """
        Set taskset settings by trigger such as button
        """
        command=b'\xA8'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)
        self._run_command(command+identifier+values,'motor_tx')


    # Teaching
    def start_teaching_motion(self,index,time_ms,identifier=b'\x00\x00'):
        """
        Start teaching motion without preparing by specifying the 'index' in the flash memory and recording 'time' in milliseconds.
        In the case of KM-1, index value is from 0 to 9 (10 in total).  Recording time cannot exceed 65408 [msec].
        """
        command=b'\xA9'
        values=uint16_t2bytes(index)+uint32_t2bytes(time_ms)
        self._run_command(command+identifier+values,'motor_tx')

    def prepare_teaching_motion(self,index,time_ms,identifier=b'\x00\x00'):
        """
        Prepare teaching motion by specifying the 'index' in the flash memory and recording 'time' in milliseconds.
        In the case of KM-1, index value is from 0 to 9 (10 in total).  Recording time cannot exceed 65408 [msec].
        """
        command=b'\xAA'
        values=uint16_t2bytes(index)+uint32_t2bytes(time_ms)
        self._run_command(command+identifier+values,'motor_tx')

    def start_teaching_motion_from_prep(self,identifier=b'\x00\x00'):
        """
        Start teaching motion in the condition of the last prepareTeachingMotion.
        This command works when the teaching index is specified by 0xAA: prepareTeachingMotion.
        """
        command=b'\xAB'
        self._run_command(command+identifier,'motor_tx')

    def stop_teaching_motion(self,identifier=b'\x00\x00'):
        """
        Stop teaching motion.
        """
        command=b'\xAC'
        self._run_command(command+identifier,'motor_tx')

    def erase_motion(self,index,identifier=b'\x00\x00'):
        """
        Erase motion at the specified index in the flash memory.
        In the case of KM-1, index value is from 0 to 9 (10 in total).
        """
        command=b'\xAD'
        values=uint16_t2bytes(index)
        self._run_command(command+identifier+values,'motor_tx')

    def erase_all_motions(self,identifier=b'\x00\x00'):
        """
        Erase all motions in the flash memory.
        """
        command=b'\xAE'
        self._run_command(command+identifier,'motor_tx')

    def set_trigger_motion_settings(self,index,repeating,option,autoStart,identifier=b'\x00\x00'):
        """
        Set playback motion settings by trigger such as button
        """
        command=b'\xB2'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)+uint8_t2bytes(option)+uint8_t2bytes(autoStart)
        self._run_command(command+identifier+values,'motor_tx')

    def read_motion(self,index,read_comp_cb,identifier=b'\x00\x00'):
        """
        Externally output the motion stored by direct teaching. (Motor farm ver>=2.0)
        It is valid only for a wired connection(USB).
          callback signature
            read_comp_cb(motion_index,motion_value[])
        """
        command=b'\xB7'
        values = uint16_t2bytes(index)
        self._run_command(command + identifier + values, 'motor_tx')
        self.on_read_motion_read_comp_cb=read_comp_cb
        return True

    def write_motion_position(self,position,identifier=b'\x00\x00'):
        """
        Record one coordinate of movement from the outside. (Motor farm ver>=2.0)
        It is valid only for a wired connection(USB).
            ※ This command can not be accepted unless it is in prepareTeaching state.What to do after running "prepareTeachingMotion"
            ※ This command records coordinates one by one. If one record is made, it will be waiting to record the next coordinate.
            ※ After recording coordinates with this command, recording can not be completed normally unless stopTeaching is executed.
        """
        command=b'\xB8'
        values = float2bytes(position)
        self._run_command(command + identifier + values, 'motor_tx')

    # LED
    def set_led(self,ledState,red,green,blue,identifier=b'\x00\x00'):
        """
        Set the LED state (off, solid, flash and dim) and color intensity (red, green and blue).
        typedef enum ledState =
        {
            LED_STATE_OFF = 0, // LED off
            LED_STATE_ON_SOLID = 1, // LED solid
            LED_STATE_ON_FLASH = 2, // LED flash
            LED_STATE_ON_DIM = 3 // LED dim
        }
        """
        command=b'\xE0'
        values=uint8_t2bytes(ledState)+uint8_t2bytes(red)+uint8_t2bytes(green)+uint8_t2bytes(blue)
        self._run_command(command+identifier+values,"motor_tx")

    def enable_continual_motor_measurement(self,identifier=b'\x00\x00'):
        """
        Enable the motor measurement and start continual notification of the measurement values.
        """
        command=b'\xE6'
        self._run_command(command+identifier,'motor_tx')

    def disable_continual_motor_measurement(self,identifier=b'\x00\x00'):
        """
        Disable the motor measurement and stop notification of the measurement values.
        """
        command=b'\xE7'
        self._run_command(command+identifier,'motor_tx')

    # IMU
    def enable_continual_imu_measurement(self,identifier=b'\x00\x00'):
        """
        Enable the IMU and start notification of the measurement values.
        """
        command=b'\xEA'
        self._run_command(command+identifier,'motor_tx')

    def disable_continual_imu_measurement(self,identifier=b'\x00\x00'):
        """
        Disable the IMU and stop notification of the measurement values.
        """
        command=b'\xEB'
        self._run_command(command+identifier,'motor_tx')

    # System
    def reboot(self,identifier=b'\x00\x00'):
        """
        Reboot the system.
        """
        command=b'\xF0'
        self._run_command(command+identifier,'motor_tx')

    def enable_check_sum(self,isEnabled,identifier=b'\x00\x00'):
        command=b'\xF3'
        values=uint8_t2bytes(isEnabled)
        self._run_command(command+identifier+values,'motor_tx')

    def enter_device_firmware_update(self,identifier=b'\x00\x00'):
        """
        Enter the device firmware update mode or bootloader mode. It goes with reboot.
        """
        command=b'\xFD'
        self._run_command(command+identifier,'motor_tx')

    def read_max_speed(self):
        """
        Read the current maximum speed of rotation 'max_speed' in rad/sec.
        """
        return self._read_setting_value(0x02)

    def read_min_speed(self):
        """
        Read the current minimum speed of rotation 'min_speed' in rad/sec.
        """
        return self._read_setting_value(0x03)

    def read_curve_type(self):
        """
        Read the current acceleration or deceleration curve 'curve_type'.
        typedef enum curveType =
        {
            CURVE_TYPE_NONE = 0, // Turn off Motion control
            CURVE_TYPE_TRAPEZOID = 1, // Turn on Motion control with trapezoidal curve
        }
        """
        return self._read_setting_value(0x05)

    def read_acc(self):
        """
        Read the current acceleration of rotation 'acc' in rad/sec^2.
        """
        return self._read_setting_value(0x07)

    def read_dec(self):
        """
        Read the current deceleration of rotation 'acc' in rad/sec^2.
        """
        return self._read_setting_value(0x08)

    def read_max_torque(self):
        """
        Read the current maximum torque 'max_torque' in N.m.
        """
        return self._read_setting_value(0x0E)

    def read_qcurrent_p(self):
        """
        Read the q-axis current PID controller's Proportional gain 'q_current_p'.
        """
        return self._read_setting_value(0x18)

    def read_qcurrent_i(self):
        """
        Read the q-axis current PID controller's Integral gain 'q_current_i'.
        """
        return self._read_setting_value(0x19)

    def read_qcurrent_d(self):
        """
        Read the q-axis current PID controller's Differential gain 'q_current_d'.
        """
        return self._read_setting_value(0x1A)

    def read_speed_p(self):
        """
        Read the speed PID controller's Proportional gain 'speed_p'.
        """
        return self._read_setting_value(0x1B)

    def read_speed_i(self):
        """
        Read the speed PID controller's Integral gain 'speed_i'.
        """
        return self._read_setting_value(0x1C)

    def read_speed_d(self):
        """
        Read the speed PID controller's Differential gain 'speed_d'.
        """
        return self._read_setting_value(0x1D)

    def read_position_p(self):
        """
        Read the position PID controller's Proportional gain 'position_p'.
        """
        return self._read_setting_value(0x1E)

    def read_position_i(self):
        """
        Read the position PID controller's Integral gain 'position_i'.
        """
        return self._read_setting_value(0x1F)

    def read_position_d(self):
        """
        Read the position PID controller's Differential gain 'position_d'.
        """
        return self._read_setting_value(0x20)

    def read_pos_control_threshold(self):
        """
        Read the threshold of the deviation between the target and current position. While the deviation is more than the threshold, integral and differential gain is set to be zero.
        """
        return self._read_setting_value(0x21)

    def read_own_color(self):
        """
        ToDo
        Read the own LED color. Return (red,green,blue).
        """
        return self._read_setting_value(0x3A)

    def read_device_name(self):
        """
        Read the device name of the motor.
        """
        return self._read_setting_value(0x46)

    def read_device_info(self):
        """
        Get the device information of the motor.
        """
        return self._read_setting_value(0x47)

    def read_status(self):
        """
        Read the motor status: 'isCheckSumEnabled', 'iMUMeasurement', 'motorMeasurement', 'queue', 'motorEnabled', 'flash_memory_state', 'motor_control_mode'.
        """
        return self._read_setting_value(0x9A)

    def read_baud_rate(self):
        """
        Get the baud rate of UART(USB).
        """
        return self._read_setting_value(0xC3)        

    def read_motor_measurement_interval(self):
        """
        Get the motor measurement interval.
        """
        return self._read_setting_value(0x2C)                

    def read_imu_measurement_interval(self):
        """
        Get the motor measurement interval.
        """
        return self._read_setting_value(0x3C) 


    def _read_setting_value(self, comm):#dummy
        pass
    def _read_motion_value(self):#dummy
        pass

    def read_gpio_status(self):
        """
        Read the GPIO status of the motor.
        """
        return self._read_setting_value(0xCC)
