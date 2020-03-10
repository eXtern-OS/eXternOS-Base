'''Attach generally useful information, not specific to any package.'''

# Copyright (C) 2009 Canonical Ltd.
# Authors: Matt Zimmerman <mdz@canonical.com>
#          Martin Pitt <martin.pitt@ubuntu.com>
#          Brian Murray <brian@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import os, re
import apport.hookutils, apport.fileutils


def add_info(report, ui):
    nm = apport.hookutils.nonfree_kernel_modules()
    if nm:
        report['NonfreeKernelModules'] = ' '.join(nm)

    # check for low space
    mounts = {'/': 'system',
              '/var': '/var',
              '/tmp': '/tmp'}

    home = os.getenv('HOME')
    if home:
        mounts[home] = 'home'
    treshold = 50

    for mount in mounts:
        st = os.statvfs(mount)
        free_mb = st.f_bavail * st.f_frsize / 1000000

        if free_mb < treshold:
            report['UnreportableReason'] = 'Your %s partition has less than \
%s MB of free space available, which leads to problems using applications \
and installing updates. Please free some space.' % (mounts[mount], free_mb)

    # important glib errors/assertions (which should not have private data)
    if 'ExecutablePath' in report:
        path = report['ExecutablePath']
        gtk_like = (apport.fileutils.links_with_shared_library(path, 'libgtk') or
                    apport.fileutils.links_with_shared_library(path, 'libgtk-3') or
                    apport.fileutils.links_with_shared_library(path, 'libX11'))
        if gtk_like and apport.hookutils.in_session_of_problem(report):
            xsession_errors = apport.hookutils.xsession_errors()
            if xsession_errors:
                report['XsessionErrors'] = xsession_errors

    # using local libraries?
    if 'ProcMaps' in report:
        local_libs = set()
        for lib in re.finditer(r'\s(/[^ ]+\.so[.0-9]*)$', report['ProcMaps'], re.M):
            if not apport.fileutils.likely_packaged(lib.group(1)):
                local_libs.add(lib.group(1))
        if ui and local_libs:
            if not ui.yesno('''The crashed program seems to use third-party or local libraries:

%s

It is highly recommended to check if the problem persists without those first.

Do you want to continue the report process anyway?
''' % '\n'.join(local_libs)):
                raise StopIteration
            report['LocalLibraries'] = ' '.join(local_libs)
            report['Tags'] = (report.get('Tags', '') + ' local-libs').strip()

    # using third-party packages?
    if '[origin:' in report.get('Package', '') or '[origin:' in report.get('Dependencies', ''):
        report['Tags'] = (report.get('Tags', '') + ' third-party-packages').strip()

    # using ecryptfs?
    if os.path.exists(os.path.expanduser('~/.ecryptfs/wrapped-passphrase')):
        report['EcryptfsInUse'] = 'Yes'

    # filter out crashes on missing GLX (LP#327673)
    in_gl = '/usr/lib/libGL.so' in (report.get('StacktraceTop') or '\n').splitlines()[0]
    if in_gl and 'Loading extension GLX' not in apport.hookutils.read_file('/var/log/Xorg.0.log'):
        report['UnreportableReason'] = 'The X.org server does not support the GLX extension, which the crashed program expected to use.'
    # filter out package install failures due to a segfault
    if 'Segmentation fault' in report.get('ErrorMessage', '') \
            and report['ProblemType'] == 'Package':
        report['UnreportableReason'] = 'The package installation resulted in a segmentation fault which is better reported as a crash report rather than a package install failure.'

    # log errors
    if report['ProblemType'] == 'Crash':
        if os.path.exists('/run/systemd/system'):
            report['JournalErrors'] = apport.hookutils.command_output(
                ['journalctl', '-b', '--priority=warning', '--lines=1000'])


if __name__ == '__main__':
    r = {}
    add_info(r, None)
    for k in r:
        print('%s: %s' % (k, r[k]))
