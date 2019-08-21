# -*- coding: utf-8 -*-
from pykeigan.utils import *

def test_float2bytes():
    result = float2bytes(1);
    assert result == b'?\x80\x00\00'

def test_bytes2float():
    result = bytes2float(b'?\x80\x00\00');
    assert result == 1
        
def test_uint8_t2bytes(self):
    assert uint8_t2bytes(23)==b'\x17'
    
def test_bytes2uint8_t(self):
    assert bytes2uint8_t(b'\x17')==23
    
def test_uint16_t2bytes(self):
    assert uint16_t2bytes(23)==b'\x00\x17'
        
def test_bytes2uint16_t(self):
    assert bytes2int16_t(b'\x00\x17')==23
        
def test_bytes2int16_t(self):
    assert bytes2int16_t(b'\xff\xff')==-1
    
def test_uint32_t2bytes(self):
    assert uint32_t2bytes(16**6)==b'\x01\x00\x00\x00'
