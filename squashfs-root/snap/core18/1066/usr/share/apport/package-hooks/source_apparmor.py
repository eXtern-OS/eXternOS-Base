'''apport package hook for apparmor

(c) 2009-2014 Canonical Ltd.
Author: Steve Beattie <sbeattie@ubuntu.com>
        Jamie Strandboge <jamie@canonical.com>
License: GPLv2
'''

from apport.hookutils import (attach_file, attach_file_if_exists, packaging,
                              command_output, root_command_output)
import os
import re
import codecs


def stringify(s):
    '''Converts a byte array into a unicode string'''
    return codecs.latin_1_decode(s)[0]


def recent_kernlog(pattern):
    '''Extract recent messages from kern.log or message which match a regex.
       pattern should be a "re" object.  '''
    lines = ''
    if os.path.exists('/var/log/kern.log'):
        file = '/var/log/kern.log'
    elif os.path.exists('/var/log/messages'):
        file = '/var/log/messages'
    else:
        return lines

    with open(file, 'rb') as f:
        for l in f.readlines():
            line = stringify(l)
            if pattern.search(line):
                lines += line
    return lines


def recent_syslog(pattern):
    '''Extract recent messages from syslog which match a regex.
       pattern should be a "re" object.  '''
    lines = ''
    if os.path.exists('/var/log/syslog'):
        file = '/var/log/syslog'
    else:
        return lines

    with open(file, 'rb') as f:
        for l in f.readlines():
            line = stringify(l)
            if pattern.search(line):
                lines += line
    return lines


def add_info(report, ui):
    attach_file(report, '/proc/version_signature', 'ProcVersionSignature')
    attach_file(report, '/proc/cmdline', 'ProcKernelCmdline')

    sec_re = re.compile('audit\(|apparmor|selinux|security', re.IGNORECASE)
    report['KernLog'] = recent_kernlog(sec_re)
    # DBus messages are reported to syslog
    dbus_sec_re = re.compile('dbus.* apparmor', re.IGNORECASE)
    report['Syslog'] = recent_syslog(dbus_sec_re)

    packages = ['apparmor', 'apparmor-utils', 'libapparmor1',
                'libapparmor-dev', 'libapparmor-perl', 'apparmor-utils',
                'apparmor-profiles', 'apparmor-easyprof',
                'python3-apparmor', 'python-apparmor', 'libpam-apparmor',
                'libapache2-mod-apparmor', 'python3-libapparmor',
                'python-libapparmor', 'auditd', 'libaudit0']

    versions = ''
    for package in packages:
        try:
            version = packaging.get_version(package)
        except ValueError:
            version = 'N/A'
        if version is None:
            version = 'N/A'
        versions += '%s %s\n' % (package, version)
    report['ApparmorPackages'] = versions

    # These need to be run as root
    report['ApparmorStatusOutput'] = root_command_output(['/usr/sbin/apparmor_status'])
    report['PstreeP'] = command_output(['/usr/bin/pstree', '-p'])
    attach_file_if_exists(report, '/var/log/audit/audit.log', 'audit.log')
