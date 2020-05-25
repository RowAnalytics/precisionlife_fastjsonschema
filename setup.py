#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    LONG_DESCRIPTION = readme.read()

# https://packaging.python.org/en/latest/single_source_version.html
try:
    execfile('precisionlife_fastjsonschema/version.py')
except NameError:
    exec(open('precisionlife_fastjsonschema/version.py').read())


setup(
    name='precisionlife_fastjsonschema',
    version=VERSION,
    packages=['precisionlife_fastjsonschema'],
    extras_require={
        'devel': [
            'colorama',
            'jsonschema',
            'json-spec',
            'pylint',
            'pytest',
            'pytest-benchmark',
            'pytest-cache',
            'validictory',
        ],
    },

    url='https://github.com/RowAnalytics/precisionlife_fastjsonschema',
    author='Zbigniew Skowron',
    author_email='zbigniew@precisionlife.com',
    description='Modified fastest Python implementation of JSON schema',
    long_description=LONG_DESCRIPTION,
    license='BSD',

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
