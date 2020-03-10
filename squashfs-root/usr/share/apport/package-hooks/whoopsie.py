#!/usr/bin/python
from glob import glob
from apport.hookutils import (attach_related_packages,
    command_output, attach_file_if_exists)
import os

def add_info(report, ui):
    # get info on all files in /var/crash/
    reports = glob('/var/crash/*')
    if reports:
        report['CrashReports'] = command_output(
            ['stat', '-c', '%a:%u:%g:%s:%y:%x:%n'] + reports)

    attach_related_packages(report, ['apport-noui'])
    # is the system set to autoreport crashes?
    if os.path.exists('/var/lib/apport/autoreport'):
        report['Tags'] += ' autoreport-true'
    else:
        report['Tags'] += ' autoreport-false'

    attach_file_if_exists(report, '/var/log/upstart/whoopsie.log')
