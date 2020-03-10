# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

'''apport package hook for update-manager

(c) 2011 Canonical Ltd.
Author: Brian Murray <brian@ubuntu.com>
'''

import os
import re
import subprocess
from apport.hookutils import (
    attach_gsettings_package, attach_root_command_outputs,
    attach_file_if_exists, command_available,
    recent_syslog)


def run_hwe_command(option):
    command = ['hwe-support-status', option]
    sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          stdin=None)
    out = sp.communicate()[0]
    if sp.returncode == 0:
        res = out.strip()
    # exit code is 10 on unsupported HWE
    elif sp.returncode == 10:
        res = out.strip()
    else:
        res = (b'Error: command ' + str(command).encode() +
               b' failed with exit code ' +
               str(sp.returncode).encode() + b': ' + out)
    return res


def add_info(report, ui):

    problem_type = report.get("ProblemType", None)
    if problem_type == "Bug":
        response = ui.yesno("Is the issue you are reporting one you \
encountered when upgrading Ubuntu from one release to another?")
    else:
        response = None
    if response:
        os.execlp('apport-bug', 'apport-bug', 'ubuntu-release-upgrader')
    else:
        attach_gsettings_package(report, 'update-manager')
        attach_file_if_exists(report, '/var/log/apt/history.log',
                              'DpkgHistoryLog.txt')
        attach_file_if_exists(report, '/var/log/apt/term.log',
                              'DpkgTerminalLog.txt')
        attach_root_command_outputs(
            report,
            {'CurrentDmesg.txt':
                'dmesg | comm -13 --nocheck-order /var/log/dmesg -'})
        if command_available('hwe-support-status'):
            # not using apport's command_output because it doesn't expect a
            # return code of 10
            unsupported = run_hwe_command('--show-all-unsupported')
            if unsupported:
                report['HWEunsupported'] = unsupported
                report['HWEreplacements'] = \
                    run_hwe_command('--show-replacements')
        report["Aptdaemon"] = recent_syslog(re.compile("AptDaemon"))
