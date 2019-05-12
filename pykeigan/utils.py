# -*- coding: utf-8 -*-

import struct

def float2bytes(float_value):
    float_value=float(float_value)
    return struct.pack("!f", float_value)

def bytes2float(byte_array):
    return struct.unpack('!f',byte_array)[0]

def uint8_t2bytes(uint8_value):
    uint8_value=int(uint8_value)
    if uint8_value<0:
        raise TypeError("Argument should be positive or equal to zero")
    if uint8_value>256-1:
        raise TypeError("Argument should be less than 256")
    return struct.pack("B",uint8_value)

def uint16_t2bytes(uint16_value):
    uint16_value=int(uint16_value)
    if uint16_value<0:
        raise TypeError("Argument should be positive or equal to zero")
    if uint16_value>256**2-1:
        raise TypeError("Argument should be less than 256**2")
    val1=int(uint16_value/256)
    val2=uint16_value-val1*256
    return struct.pack("BB",val1,val2)

def uint32_t2bytes(uint32_value):
    uint32_value=int(uint32_value)
    if uint32_value<0:
        raise TypeError("Argument should be positive or equal to zero")
    if uint32_value>256**4-1:
        raise TypeError("Argument should be less than 256**4")
    val1=int(uint32_value/256**3)
    val2=int((uint32_value-val1*256**3)/256**2)
    val3=int((uint32_value-val1*256**3-val2*256**2)/256)
    val4=uint32_value-val1*256**3-val2*256**2-val3*256
    return struct.pack("BBBB",val1,val2,val3,val4)

def bytes2uint32_t(ba):
    return struct.unpack(">I",ba)[0]

def bytes2uint16_t(ba):
    return struct.unpack(">H", ba)[0]

def bytes2uint8_t(ba):
    return struct.unpack("B",ba)[0]

def bytes2int16_t(ba):
    return struct.unpack(">h",ba)[0]

def deg2rad(degree):
    return degree*0.017453292519943295

def rad2deg(radian):
    return radian/ 0.017453292519943295

def rpm2rad_per_sec(rpm):
    return rpm *0.10471975511965977

def rad_per_sec2rpm(radian_per_sec):
    return radian_per_sec/0.10471975511965977
