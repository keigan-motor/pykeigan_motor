# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('MIT-LICENSE') as f:
    license = f.read()

setup(
    name='pykeigan_motor',
    version='0.2.0',
    description='Python module for Keigan Motors',
    long_description=readme,
    install_requires=['pyserial'],
    author='Tomohiro Takata, Hiroshi Harada',
    author_email='takata@innovotion.co.jp, harada@keigan.co.jp',
    url='https://github.com/keigan-motor/pykeigan_motor',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
