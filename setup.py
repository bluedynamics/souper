# -*- coding: utf-8 -*-
from setuptools import setup


setup(
    # zest releaser does not change cfg file.
    version='1.1.2',
    # thanks to this bug
    # https://github.com/pypa/setuptools/issues/1136
    # we need one line in here:
    package_dir={"": "src"},
)
