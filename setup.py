#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

setup(
    name='regulations-parser',
    url='https://github.com/cfpb/regulations-parser',
    author='CFPB',
    author_email='tech@cfpb.gov',
    license='CC0',
    version='0.1.0',
    description='eCFR Parser for eRegulations',
    long_description=open('README.md').read()
            if os.path.exists('README.md') else '',

    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'lxml',
        'pyparsing',
        'inflection',
        'requests',
        'GitPython',
        'python-constraint',
    ],
    setup_requires=[
        'nose>=1.0'
    ],

    test_suite='xtdiff.tests',
)
