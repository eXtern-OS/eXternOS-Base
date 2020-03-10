# apport package hook for ubuntu-drivers-common
# (c) 2012 Canonical Ltdt.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

import apport.hookutils

def add_info(report, ui):
    report['UbuntuDriversDebug'] = apport.hookutils.command_output(['ubuntu-drivers', 'debug'])
