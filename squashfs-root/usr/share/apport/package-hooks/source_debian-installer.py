'''Apport package hook for the Debian installer.

Copyright (C) 2011 Canonical Ltd.
Authors: Colin Watson <cjwatson@ubuntu.com>,
         Brian Murray <brian@ubuntu.com>'''

import os
from apport.hookutils import attach_hardware, command_available, command_output, attach_root_command_outputs


def add_installation_log(report, ident, name):
    if os.path.exists('/var/log/installer/%s' % name):
        f = '/var/log/installer/%s' % name
    elif os.path.exists('/var/log/%s' % name):
        f = '/var/log/%s' % name
    else:
        return

    if os.access(f, os.R_OK):
        report[ident] = (f,)
    else:
        attach_root_command_outputs(report, {ident: "cat '%s'" % f})


def add_info(report):
    attach_hardware(report)

    report['DiskUsage'] = command_output(['df'])
    report['MemoryUsage'] = command_output(['free'])

    if command_available('dmraid'):
        attach_root_command_outputs(report, {'DmraidSets': 'dmraid -s',
                                             'DmraidDevices': 'dmraid -r'})
        if command_available('dmsetup'):
            attach_root_command_outputs(report, {'DeviceMapperTables': 'dmsetup table'})

    try:
        installer_version = open('/var/log/installer/version')
        for line in installer_version:
            if line.startswith('ubiquity '):
                # File these reports on the ubiquity package instead
                report['SourcePackage'] = 'ubiquity'
                break
        installer_version.close()
    except IOError:
        pass

    add_installation_log(report, 'DIPartman', 'partman')
    add_installation_log(report, 'DISyslog', 'syslog')


if __name__ == '__main__':
    report = {}
    add_info(report)
    for key in report:
        if isinstance(report[key], type('')):
            print('%s: %s' % (key, report[key].split('\n', 1)[0]))
        else:
            print('%s: %s' % (key, type(report[key])))
