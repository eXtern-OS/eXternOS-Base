'''
Determine rudimentary package and version information for click packages to
enable bucketing on the Error Tracker.

Copyright (C) 2014 Canonical Ltd.
Author: Brian Murray <brian@canonical.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

import subprocess


def add_info(report, ui):
    exec_path = report.get('ExecutablePath')
    if not exec_path:
        return
    if not exec_path.startswith('/opt/click.ubuntu.com') and \
            not exec_path.startswith('/usr/share/click/preinstalled'):
        return
    # indicate that the crash is from a click package so the Error Tracker
    # will not ask for a core dump
    report['ClickPackage'] = "True"
    click_info = subprocess.Popen(['click', 'info', exec_path],
                                  stdout=subprocess.PIPE,
                                  universal_newlines=True)
    out = click_info.communicate()[0]
    for line in out.splitlines():
        if 'name' in line:
            package = line.strip(' ,').split(': ')[1]
            package = package.replace('"', '')
        if 'version' in line:
            version = line.strip(' ,').split(': ')[1]
            version = version.replace('"', '')
        if 'architecture' in line:
            pkg_arch = line.strip(' ,').split(': ')[1]
            pkg_arch = pkg_arch.replace('"', '')
    report['Package'] = '%s %s' % (package, version)
    report['SourcePackage'] = package
    report['PackageArchitecture'] = pkg_arch
