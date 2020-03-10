#!/usr/bin/python
# -*- coding: utf-8 -*-
'''apport package hook for bluez

(c) 2010 Free Software Foundation
Author:
Baptiste Mille-Mathias <baptistem@src.gnome.org>

'''
from apport.hookutils import *
import re

def add_info(report, ui):
    report['syslog'] = recent_syslog(re.compile(r'bluetooth', re.IGNORECASE))
    attach_hardware(report)
    if command_available('hciconfig'):
        report['hciconfig'] = command_output('hciconfig')
    if command_available('rfkill'):
        report['rfkill'] = command_output(['rfkill','list'])
    if command_available('getfacl'):
        report['getfacl'] = command_output(['getfacl','/dev/rfkill'])

    interesting_modules = ('btusb', 'rfcomm', 'sco', 'bnep', 'l2cap', 'bluetooth')
    interesting_modules_loaded = []

    for line in open('/proc/modules'):
        module = line.split()[0]
        if module in interesting_modules:
            interesting_modules_loaded.append(module)

    if interesting_modules_loaded:
        report['InterestingModules'] = ' '.join(interesting_modules_loaded)

