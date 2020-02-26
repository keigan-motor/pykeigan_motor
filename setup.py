# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path
import codecs
this_directory = path.abspath(path.dirname(__file__))
with codecs.open(path.join(this_directory, 'README.rst'),'r','utf-8') as f:
    readme = f.read()

setup(
    name='pykeigan_motor',
    version='2.2.1',
    description='Python Library for Keigan Motors (v2)',
    long_description=readme,
    long_description_content_type='text/x-rst',
    install_requires=['pyserial'],
    extras_require={'ble' : ['bluepy']},
    author='Tomohiro Takata, Hiroshi Harada',
    author_email='takata@innovotion.co.jp, harada@keigan.co.jp',
    url='https://github.com/keigan-motor/pykeigan_motor',
    license='MIT-LICENSE',
    packages=find_packages(exclude=('tests', 'docs'))
)
