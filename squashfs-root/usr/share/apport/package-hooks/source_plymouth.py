'''apport package hook for plymouth

Copyright 2010 Canonical Ltd.
Authors: Steve Langasek <steve.langasek@ubuntu.com>,
         Brian Murray <brian@ubuntu.com>
'''

from apport.hookutils import *

import os.path


def _attach_file_filtered(report, path, key=None):
    '''filter out password from grub configuration'''
    if not key:
        key = path_to_key(path)

    if os.path.exists(path):
        with open(path,'r') as f:
            filtered = [l if not l.startswith('password')
                        else '### PASSWORD LINE REMOVED ###'
                        for l in f.readlines()]
            report[key] = ''.join(filtered)


def add_info(report):
    attach_hardware(report)
    attach_file(report, '/proc/fb', 'ProcFB')
    attach_file(report, '/proc/cmdline', 'ProcCmdLine')
    attach_file(report, '/var/log/boot.log', 'BootLog')
    debug_log = '/var/log/plymouth-debug.log'
    if os.path.exists(debug_log):
        attach_root_command_outputs(report,
            {'PlymouthDebug': 'cat %s' % debug_log})
    _attach_file_filtered(report, '/etc/default/grub', 'EtcDefaultGrub')
    report['DefaultPlymouth'] = command_output(['readlink', '/etc/alternatives/default.plymouth'])
    report['TextPlymouth'] = command_output(['readlink', '/etc/alternatives/text.plymouth'])
