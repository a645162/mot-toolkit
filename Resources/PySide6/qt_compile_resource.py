# -*- coding: utf-8 -*-

import os

command = """
pyside6-rcc \
    resources.qrc \
    -o ../../src/mot_toolkit/gui/resources/resources.py
"""

ret = os.system(command.strip())

if ret != 0:
    print("Qt Resource Compile Failed!")
    exit(1)

print("Qt Resource Compile Done!")
