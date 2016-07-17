#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  setup.py
#  
#  Copyright 2015 notna <notna@apparat.org>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

try:
    from setuptools import setup
    print("Using setuptools")
except ImportError:
    print("Setuptools not installed!")
    from distutils.core import setup

try:
    with open('pypi.rst') as file:
        long_description = file.read()
except IOError:
    long_description = 'Packet based networking'

setup(name='packetmq',
      version='0.1.6a1',
      description='Packet based networking',
      url="http://packetmq.readthedocs.org/en/latest/",
      long_description=long_description,
      author='notna',
      author_email='notna@apparat.org',
      packages=['packetmq',
                ],
      package_data={'packetmq': ['docs/source/*']},
      data_files=[(".",["pypi.rst", "README.md", "requirements.txt"])],
      requires=["twisted","msgpack","bidict"],
      provides=["packetmq"],
      classifiers=["Development Status :: 4 - Beta",
                   "Framework :: Twisted",
                   "Intended Audience :: Developers",
                   "Intended Audience :: Information Technology",
                   "Intended Audience :: Telecommunications Industry",
                   "License :: OSI Approved",
                   "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 2.7",
                   "Topic :: Communications",
                   "Topic :: Internet",
                   "Topic :: Software Development",
                   "Topic :: Software Development :: Libraries",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
    keywords="bidict,packet,packetmq,twisted,tcp,socket,network",
     )
