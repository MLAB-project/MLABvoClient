#!/usr/bin/python
# -*- coding: utf8 -*-

from setuptools import setup, find_packages
import sys
import os
import os.path as path

os.chdir(path.realpath(path.dirname(__file__)))

setup(
    name                = "MLABvo",
    version             = "0.0.3",
    author =            "Roman Dvorak",
    author_email        = "romandvorak@mlab.cz",
    description         = ("Software for getting data from MLAB virtual observatory servers"),
    license             = "General Public License v3'",
    keywords            = "ssh, virtual-observatory, data, store, server, storage, VO",
    url                 = "http://wiki.mlab.cz",
    packages    = ['MLABvo'],
    #packages    = find_packages("src"),
    package_dir = {'': 'src'},
    long_description    ="",
    classifiers         =[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: Czech',
        # 'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
