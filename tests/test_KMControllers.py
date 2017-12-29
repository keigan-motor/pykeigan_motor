# -*- coding: utf-8 -*-
from .context import KMControllers

import unittest


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def test_absolute_truth_and_meaning(self):
        assert True
        
    def test_float2bytes(self):
        assert KMControllers.float2bytes(-3)==bytearray([0xC0,0x40,0x00,0x00])
    
    def test_bytes2float(self):
        float_value=-3.4
        assert abs(KMControllers.bytes2float(bytearray([0xC0,0x59,0x99,0x99]))-float_value) < 0.0001
        
    def test_uint8_t2bytes(self):
        assert KMControllers.uint8_t2bytes(23)==b'\x17'
    
    def test_bytes2uint8_t(self):
        assert KMControllers.bytes2uint8_t(b'\x17')==23
    
    def test_uint16_t2bytes(self):
        assert KMControllers.uint16_t2bytes(23)==b'\x00\x17'
        
    def test_bytes2uint16_t(self):
        assert KMControllers.bytes2int16_t(b'\x00\x17')==23
        
    def test_bytes2int16_t(self):
        assert KMControllers.bytes2int16_t(b'\xff\xff')==-1
    
    def test_uint32_t2bytes(self):
        assert KMControllers.uint32_t2bytes(16**6)==b'\x01\x00\x00\x00'


if __name__ == '__main__':
    unittest.main()
