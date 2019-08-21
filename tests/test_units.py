# -*- coding: utf-8 -*-
from pykeigan.utils import *

def test_float2bytes():
    result = float2bytes(1);
    assert result == b'?\x80\x00\00'

def test_bytes2float():
    result = bytes2float(b'?\x80\x00\00');
    assert result == 1
