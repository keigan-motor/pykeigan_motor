# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os import path
from io import open

import codecs
this_directory = path.abspath(path.dirname(__file__))
readme = open(path.join(this_directory, 'README.rst'), encoding='utf-8').read().replace("\r", "")

# This will be an error by Windows: `long_description` has syntax errors in markup and would not be rendered on PyPI. 
# with codecs.open(path.join(this_directory, 'README.rst'),'r','utf-8') as f:
#     readme = f.read()

setup(
    name='pykeigan_motor',
    version='3.0.0',
    description='Python Library for Keigan Motors (v3)',
    long_description=readme,
    long_description_content_type='text/x-rst',
    install_requires=['pyserial'],
    extras_require={
        'ble' : ['bleak>=0.22'],
        'mcp' : ['mcp>=2,<3; python_version>="3.10"'],  # MCP server (pykeigan-mcp). Python >= 3.10
    },
    entry_points={
        'console_scripts': ['pykeigan-mcp = pykeigan.mcp_cli:main',
                            'pykeigan-usb-check = pykeigan.usbcheck:main'],
    },
    author='Tomohiro Takata, Hiroshi Harada, Takashi Tokuda',
    author_email='takata@innovotion.co.jp, harada@keigan.co.jp, tokuda@keigan.co.jp',
    url='https://github.com/keigan-motor/pykeigan_motor',
    project_urls={
        'Documentation': 'https://docs.keigan-motor.com/apiDocument/pykeigan_motor/',
        'Source': 'https://github.com/keigan-motor/pykeigan_motor',
        'Issues': 'https://github.com/keigan-motor/pykeigan_motor/issues',
        'Homepage': 'https://www.keigan-motor.com/',
    },
    license='MIT',
    license_files=['MIT-LICENSE'],
    python_requires='>=3.5',  # 3.0.0 dropped python 2.7: pip on python 2 keeps installing 2.4.0
    keywords='keigan keiganmotor motor servo actuator robotics usb ble bluetooth bleak mcp',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Hardware',
    ],
    packages=find_packages(exclude=('tests', 'tests.*', 'docs'))
)
