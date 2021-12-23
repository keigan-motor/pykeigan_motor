# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path
import codecs
this_directory = path.abspath(path.dirname(__file__))
readme = open(path.join(this_directory, 'README.rst'), encoding='utf-8').read().replace("\r", "")

# This will be an error by Windows: `long_description` has syntax errors in markup and would not be rendered on PyPI. 
# with codecs.open(path.join(this_directory, 'README.rst'),'r','utf-8') as f:
#     readme = f.read()

setup(
    name='pykeigan_motor',
    version='2.3.1',
    description='Python Library for Keigan Motors (v2)',
    long_description=readme,
    long_description_content_type='text/x-rst',
    install_requires=['pyserial'],
    extras_require={'ble' : ['bluepy']},
    author='Tomohiro Takata, Hiroshi Harada, Takashi Tokuda',
    author_email='takata@innovotion.co.jp, harada@keigan.co.jp, tokuda@keigan.co.jp',
    url='https://github.com/keigan-motor/pykeigan_motor',
    license='MIT-LICENSE',
    packages=find_packages(exclude=('tests', 'docs'))
)
