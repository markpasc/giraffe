#!/usr/bin/env python

from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='giraffe',
    version='1.0a1',

    packages=['giraffe'],
    py_modules=['reusably'],
    provides=['giraffe'],
    include_package_data=True,
    zip_safe=False,
)
