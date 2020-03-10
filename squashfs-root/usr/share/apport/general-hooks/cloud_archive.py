'''
Redirect reports on packages from the Ubuntu Cloud Archive to the
launchpad cloud-archive project.

Copyright (C) 2013 Canonical Ltd.
Author: James Page <james.page@ubuntu.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''
from apport import packaging


def add_info(report, ui):
    package = report.get('Package')
    if not package:
        return
    package = package.split()[0]
    try:
        if '~cloud' in packaging.get_version(package) and \
           packaging.get_package_origin(package) == 'Canonical':
            report['CrashDB'] = '''{
               "impl": "launchpad",
               "project": "cloud-archive",
               "bug_pattern_url": "http://people.canonical.com/~ubuntu-archive/bugpatterns/bugpatterns.xml",
            }'''
    except ValueError as e:
        if 'does not exist' in str(e):
            return
        else:
            raise e
