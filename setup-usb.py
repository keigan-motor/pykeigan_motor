# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='pykeigan_motor_usb',
    version='2.1.0',
    description='Python Library for Keigan Motors on USB',
    long_description=readme,
    install_requires=['pyserial'],
    author='Tomohiro Takata, Hiroshi Harada',
    author_email='takata@innovotion.co.jp, harada@keigan.co.jp',
    url='https://github.com/keigan-motor/pykeigan_motor',
    license='MIT-LICENSE',
    packages=find_packages(exclude=('tests', 'docs'))
)
