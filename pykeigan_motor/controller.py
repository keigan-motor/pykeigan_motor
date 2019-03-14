#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thr Jan 10 09:13:24 2018

@author: takata@innovotion.co.jp
"""
import serial,struct,threading,atexit,time
from bluepy import btle
from pykeigan_motor.utils import *

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

    # Settings
    def set_max_speed(self,max_speed,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the maximum speed of rotation to the 'max_speed' in rad/sec.
        """
        command=b'\x02'
        values=float2bytes(max_speed)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_min_speed(self,min_speed,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the minimum speed of rotation to the 'min_speed' in rad/sec.
        """
        command=b'\x03'
        values=float2bytes(min_speed)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_curve_type(self,curve_type,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the acceleration or deceleration curve to the 'curve_type'.
        typedef enum curveType =
        {
            CURVE_TYPE_NONE = 0, // Turn off Motion control
            CURVE_TYPE_TRAPEZOID = 1, // Turn on Motion control with trapezoidal curve
        }
        """
        command=b'\x05'
        values=uint8_t2bytes(curve_type)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_acc(self,_acc,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the acceleration of rotation to the positive 'acc' in rad/sec^2.
        """
        command=b'\x07'
        values=float2bytes(_acc)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_dec(self,_dec,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the deceleration of rotation to the positive 'dec' in rad/sec^2.
        """
        command=b'\x08'
        values=float2bytes(_dec)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_max_torque(self,max_torque,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the maximum torque to the positive 'max_torque' in N.m.
        """
        command=b'\x0E'
        values=float2bytes(max_torque)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_teaching_interval(self,interval_ms,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the interval time of teaching to the positive integer "interval_ms" in ms.
        """
        command=b'\x16'
        values=uint32_t2bytes(interval_ms)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_playback_interval(self,interval_ms,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the interval time of playback to the positive integer "interval_ms" in ms.
        """
        command=b'\x17'
        values=uint32_t2bytes(interval_ms)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_qcurrent_p(self,q_current_p,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Proportional gain to the postiive 'q_current_p'.
        """
        command=b'\x18'
        values=float2bytes(q_current_p)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_qcurrent_i(self,q_current_i,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Integral gain to the positive 'q_current_i'.
        """
        command=b'\x19'
        values=float2bytes(q_current_i)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_qcurrent_d(self,q_current_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Differential gain to the postiive 'q_current_d'.
        """
        command=b'\x1A'
        values=float2bytes(q_current_d)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_speed_p(self,speed_p,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed PID controller's Proportional gain to the positive 'speed_p'.
        """
        command=b'\x1B'
        values=float2bytes(speed_p)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_speed_i(self,speed_i,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed PID controller's Integral gain to the positive 'speed_i'.
        """
        command=b'\x1C'
        values=float2bytes(speed_i)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_speed_d(self,speed_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed PID controller's Deferential gain to the positive 'speed_d'.
        """
        command=b'\x1D'
        values=float2bytes(speed_d)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_position_p(self,position_p,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Proportional gain to the positive 'position_p'.
        """
        command=b'\x1E'
        values=float2bytes(position_p)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_position_i(self,position_i,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Integral gain to the positive 'position_i'.
        """
        command=b'\x1F'
        values=float2bytes(position_i)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_position_d(self,position_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Differential gain to the positive 'position_d'.
        """
        command=b'\x20'
        values=float2bytes(position_d)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_pos_control_threshold(self,poscontrol_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the threshold of the deviation between the target and current position. While the deviation is more than the threshold, integral and differential gain is set to be zero.
        """
        command=b'\x21'
        values=float2bytes(poscontrol_d)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def reset_all_pid(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset all the PID parameters to the firmware default settings.
        """
        command=b'\x22'
        self._run_command(command+identifier+crc16,'motor_settings')

    def set_motor_measurement_interval(self,interval,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the interval to acquire motor measurement values. It is valid only for a wired connection(USB and I2C).
        """
        command=b'\x2C'
        values = uint8_t2bytes(interval)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_motor_measurement_settings(self,flag,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        ToDo
        """
        command=b'\x2D'
        values=uint8_t2bytes(flag)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    @property
    def interface_type(self):
        return {
            "BLE": 0b1,
            "USB": 0b1000,
            "I2C": 0b10000,
            "BTN": 0b10000000,
        }

    def set_interface(self,flag,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        You can enable or disable the data interfaces(physical 3 buttons, I2C, USB and BLE).
        The motor chooses the output interface of motor measurement values and IMU values as
        (High priority)BLE > USB > I2C(Low priority) by default.
        If you want to force it to send measurement values through USB,
        you need to set bit0(BLE) to OFF(0) and bit3(USB) to ON(1).
        For example, if you call set_interface(0b10001000), Physical 3 buttons: enabled, I2C: disabled, USB: enabled and BLE: disabled.
        To save this setting to the flash memory, ensure you call save_all_registers() .
        -----------
        bit7: Physical 3 buttons
        bit6: -
        bit5: -
        bit4: I2C(Wired)
        bit3: USB(Wired)
        bit2: -
        bit1: -
        bit0: BLE(Wireless)
        -----------
        """
        command=b'\x2E'
        values=uint8_t2bytes(flag)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_own_color(self,red,green,blue,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the own LED color.
        """
        command=b'\x3A'
        values=uint8_t2bytes(red)+uint8_t2bytes(green)+uint8_t2bytes(blue)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_imu_measurement_interval(self,interval,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the interval to acquire IMU measurement values. It is valid only for a wired connection(USB and I2C).
        """
        command=b'\x3C'
        values = uint8_t2bytes(interval)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def set_imu_measurement_settings(self,flag,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        ToDo
        """
        command=b'\x3D'
        values=uint8_t2bytes(flag)
        self._run_command(command+identifier+values+crc16,'motor_settings')


    def read_register(self,register,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        '''
        Read a specified setting (register).
        '''
        command=b'\x40'
        values=uint8_t2bytes(register)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def save_all_registers(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Save all settings (registers) in flash memory.
        """
        command=b'\x41'
        self._run_command(command+identifier+crc16,'motor_settings')

    def read_device_name(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        ToDo
        """
        command=b'\x46'
        self._run_command(command+identifier+crc16,'motor_settings')

    def read_device_info(self,infotype,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        # TODO:
        """
        command=b'\x47'
        values=uint8_t2bytes(infotype)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def reset_register(self,register,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset a specified register's value to the firmware default setting.
        """
        command=b'\x4E'
        values=uint8_t2bytes(register)
        self._run_command(command+identifier+values+crc16,'motor_settings')

    def reset_all_registers(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset all registers' values to the firmware default setting.
        """
        command=b'\x4F'
        self._run_command(command+identifier+crc16,'motor_settings')

    # Motor Action
    def disable_action(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Disable motor action.
        """
        command=b'\x50'
        self._run_command(command+identifier+crc16,'motor_control')

    def enable_action(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enable motor action.
        """
        command=b'\x51'
        self._run_command(command+identifier+crc16,'motor_control')

    def set_speed(self,speed,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed of rotation to the positive 'speed' in rad/sec.
        """
        command=b'\x58'
        values=float2bytes(speed)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def preset_position(self,position,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Preset the current absolute position as the specified 'position' in rad. (Set it to zero when setting origin)
        """
        command=b'\x5A'
        values=float2bytes(position)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def get_position_offset(self,position,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Get the offset value of the absolute position.
        """
        command=b'\x5B'
        values=float2bytes(position)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def run_forward(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Rotate the motor forward (counter clock-wise) at the speed set by 0x58: speed.
        """
        command=b'\x60'
        self._run_command(command+identifier+crc16,'motor_control')

    def run_reverse(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Rotate the motor reverse (clock-wise) at the speed set by 0x58: speed.
        """
        command=b'\x61'
        self._run_command(command+identifier+crc16,'motor_control')

    def run_at_velocity(self,velocity,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Rotate the motor at the 'velocity'. The velocity can be positive or negative.
        """
        command=b'\x62'
        values=float2bytes(velocity)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def move_to_pos(self,position,speed=None,identifier=b'\x00\x00',crc16=b'\x00\x00'):
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
        self._run_command(command+identifier+values+crc16,'motor_control')

    def move_by_dist(self,distance,speed=None,identifier=b'\x00\x00',crc16=b'\x00\x00'):
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
        self._run_command(command+identifier+values+crc16,'motor_control')

    def free_motor(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop the motor's excitation
        """
        command=b'\x6C'
        self._run_command(command+identifier+crc16,'motor_control')

    def stop_motor(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Decelerate the speed to zero and stop.
        """
        command=b'\x6D'
        self._run_command(command+identifier+crc16,'motor_control')

    def hold_torque(self,torque,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Keep and output the specified torque.
        """
        command=b'\x72'
        values=float2bytes(torque)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def move_to_pos_until_arrival(self,position,speed=None,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Move to the absolute 'position' at the 'speed'. If the speed is None, move at the speed set by 0x58: set_speed. This command is active until arriving the position. The next command execution waits in a queue.
        """
        if speed is not None:
            command=b'\x75'
            values=float2bytes(position)+float2bytes(speed)
        else:
            command=b'\x76'
            values=float2bytes(position)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def move_by_dist_until_arrival(self,position,speed=None,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Move the motor by the specified relative 'distance' from the current position at the 'speed'. If the speed is None, move at the speed set by 0x58: set_speed. This command is active until arriving the position. The next command execution waits in a queue.
        """
        if speed is None:
            command=b'\x77'
            values=float2bytes(position)+float2bytes(speed)
        else:
            command=b'\x78'
            values=float2bytes(position)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def start_doing_taskset(self,index,repeating,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Do taskset at the specified 'index' 'repeating' times.
        """
        command=b'\x81'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def stop_doing_taskset(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop doing the current taskset.
        """
        command=b'\x82'
        self._run_command(command+identifier+crc16,'motor_control')

    def start_playback_motion(self,index,repeating,option,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start to playback motion at the specified 'index' 'repeating' times.
        """
        command=b'\x85'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)+uint8_t2bytes(option)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def prepare_playback_motion(self,index,repeating,option,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Prepare to playback motion at the specified 'index' 'repeating' times.
        """
        command=b'\x86'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)+uint8_t2bytes(option)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def start_playback_motion_from_prep(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start to playback motion in the condition of the last preparePlaybackMotion.
        """
        command=b'\x87'
        self._run_command(command+identifier+crc16,'motor_control')

    def stop_playback_motion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop to playback motion.
        """
        command=b'\x88'
        self._run_command(command+identifier+crc16,'motor_control')

    # Queue
    def pause_queue(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Pause the queue until 0x91: resume is executed.
        """
        command=b'\x90'
        self._run_command(command+identifier+crc16,'motor_control')

    def resume_queue(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Resume the queue.
        """
        command=b'\x91'
        self._run_command(command+identifier+crc16,'motor_control')

    def wait_queue(self,waittime,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Wait the queue or pause the queue for the specified 'time' in msec and resume it automatically.
        """
        command=b'\x92'
        values=uint32_t2bytes(waittime)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def clear_queue(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Clear the queue. Erase all tasks in the queue. This command works when 0x90: pause or 0x92: wait are executed.
        """
        command=b'\x95'
        self._run_command(command+identifier+crc16,'motor_control')

    # Taskset
    def start_recording_taskset(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start recording taskset at the specified 'index' in the flash memory.
        In the case of KM-1, index value is from 0 to 49 (50 in total).
        """
        command=b'\xA0'
        values=uint16_t2bytes(index)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def stop_recording_taskset(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop recording taskset.
        This command works while 0xA0: startRecordingTaskset is executed.
        """
        command=b'\xA2'
        self._run_command(command+identifier+crc16,'motor_control')

    def erase_taskset(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase taskset at the specified index in the flash memory.
        In the case of KM-1, index value is from 0 to 49 (50 in total).
        """
        command=b'\xA3'
        values=uint16_t2bytes(index)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def erase_all_tasksets(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase all tasksets in the flash memory.
        """
        command=b'\xA4'
        self._run_command(command+identifier+crc16,'motor_control')

    # Teaching
    def start_teaching_motion(self,index,time_ms,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start teaching motion without preparing by specifying the 'index' in the flash memory and recording 'time' in milliseconds.
        In the case of KM-1, index value is from 0 to 9 (10 in total).  Recording time cannot exceed 65408 [msec].
        """
        command=b'\xA9'
        values=uint16_t2bytes(index)+uint32_t2bytes(time_ms)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def prepare_teaching_motion(self,index,time_ms,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Prepare teaching motion by specifying the 'index' in the flash memory and recording 'time' in milliseconds.
        In the case of KM-1, index value is from 0 to 9 (10 in total).  Recording time cannot exceed 65408 [msec].
        """
        command=b'\xAA'
        values=uint16_t2bytes(index)+uint32_t2bytes(time_ms)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def start_teaching_motion_from_prep(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start teaching motion in the condition of the last prepareTeachingMotion.
        This command works when the teaching index is specified by 0xAA: prepareTeachingMotion.
        """
        command=b'\xAB'
        self._run_command(command+identifier+crc16,'motor_control')

    def stop_teaching_motion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop teaching motion.
        """
        command=b'\xAC'
        self._run_command(command+identifier+crc16,'motor_control')

    def erase_motion(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase motion at the specified index in the flash memory.
        In the case of KM-1, index value is from 0 to 9 (10 in total).
        """
        command=b'\xAD'
        values=uint16_t2bytes(index)
        self._run_command(command+identifier+values+crc16,'motor_control')

    def erase_all_motions(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase all motions in the flash memory.
        """
        command=b'\xAE'
        self._run_command(command+identifier+crc16,'motor_control')

    # LED
    def set_led(self,ledState,red,green,blue,identifier=b'\x00\x00',crc16=b'\x00\x00'):
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
        self._run_command(command+identifier+values+crc16,"motor_control")

    def enable_continual_motor_measurement(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enable the motor measurement and start continual notification of the measurement values.
        """
        command=b'\xE6'
        self._run_command(command+identifier+crc16,'motor_control')

    def disable_continual_motor_measurement(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Disable the motor measurement and stop notification of the measurement values.
        """
        command=b'\xE7'
        self._run_command(command+identifier+crc16,'motor_control')

    # IMU
    def enable_continual_imu_measurement(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enable the IMU and start notification of the measurement values.
        """
        command=b'\xEA'
        self._run_command(command+identifier+crc16,'motor_control')

    def disable_continual_imu_measurement(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Disable the IMU and stop notification of the measurement values.
        """
        command=b'\xEB'
        self._run_command(command+identifier+crc16,'motor_control')

    # System
    def reboot(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reboot the system.
        """
        command=b'\xF0'
        self._run_command(command+identifier+crc16,'motor_control')

    def enter_device_firmware_update(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enter the device firmware update mode.
        Enter the device firmware update mode or bootloader mode. It goes with reboot.
        """
        command=b'\xFD'
        self._run_command(command+identifier+crc16,'motor_control')

    def read_max_speed(self):
        return self._read_setting_value(0x02)

    def read_min_speed(self):
        return self._read_setting_value(0x03)

    def read_curve_type(self):
        return self._read_setting_value(0x05)

    def read_acc(self):
        return self._read_setting_value(0x07)

    def read_dec(self):
        return self._read_setting_value(0x08)

    def read_max_torque(self):
        return self._read_setting_value(0x0E)

    def read_qcurrent_p(self):
        return self._read_setting_value(0x18)

    def read_qcurrent_i(self):
        return self._read_setting_value(0x19)

    def read_qcurrent_d(self):
        return self._read_setting_value(0x1A)

    def read_speed_p(self):
        return self._read_setting_value(0x1B)

    def read_speed_i(self):
        return self._read_setting_value(0x1C)

    def read_speed_d(self):
        return self._read_setting_value(0x1D)

    def read_position_p(self):
        return self._read_setting_value(0x1E)

    def read_position_i(self):
        return self._read_setting_value(0x1F)

    def read_position_d(self):
        return self._read_setting_value(0x20)

    def read_pos_control_threshold(self):
        return self._read_setting_value(0x21)

    def read_own_color(self):
        return self._read_setting_value(0x3A)

    def read_device_name(self):
        return self._read_setting_value(0x46)

    def read_deviceInfo(self):
        return self._read_setting_value(0x47)

    def read_position_offset(self):
        return self._read_setting_value(0x5B)

    def read_status(self):
        return self._read_setting_value(0x9A)

    def _read_setting_value(self, comm):#dummy
        pass
