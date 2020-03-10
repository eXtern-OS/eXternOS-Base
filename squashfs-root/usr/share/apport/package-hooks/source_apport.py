'''Apport package hook for apport itself.

This adds /var/log/apport.log and the file listing in /var/crash to the report.
'''

# Copyright 2007 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

from glob import glob
import apport.hookutils

APPORT_LOG = '/var/log/apport.log'


def add_info(report):
    apport.hookutils.attach_file_if_exists(report, APPORT_LOG, 'ApportLog')
    reports = glob('/var/crash/*')
    if reports:
        report['CrashReports'] = apport.hookutils.command_output(
            ['stat', '-c', '%a:%u:%g:%s:%y:%x:%n'] + reports)
