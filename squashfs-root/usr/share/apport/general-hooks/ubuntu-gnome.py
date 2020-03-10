'''Bugs and crashes for the Ubuntu GNOME flavour.

Copyright (C) 2013 Canonical Ltd.
Author: Martin Pitt <martin.pitt@ubuntu.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''


def add_info(report, ui):
    release = report.get('DistroRelease', '')

    msg = 'The GNOME3 PPA you are using is no longer supported for this Ubuntu release. Please '
    # redirect reports against PPA packages to ubuntu-gnome project
    if '[origin: LP-PPA-gnome3-team-gnome3' in report.get('Package', ''):
        report['CrashDB'] = '''{
           "impl": "launchpad",
           "project": "ubuntu-gnome",
           "bug_pattern_url": "http://people.canonical.com/~ubuntu-archive/bugpatterns/bugpatterns.xml",
           "dupdb_url": "http://phillw.net/ubuntu-gnome/apport_duplicates/",
        }'''

        # using the staging PPA?
        if 'LP-PPA-gnome3-team-gnome3-staging' in report.get('Package', ''):
            report.setdefault('Tags', '')
            report['Tags'] += ' gnome3-staging'
            if release in ('Ubuntu 14.04', 'Ubuntu 16.04'):
                report['UnreportableReason'] = '%s run "ppa-purge ppa:gnome3-team/gnome3-staging".' % msg

        # using the next PPA?
        elif 'LP-PPA-gnome3-team-gnome3-next' in report.get('Package', ''):
            report.setdefault('Tags', '')
            report['Tags'] += ' gnome3-next'
            if release in ('Ubuntu 14.04', 'Ubuntu 16.04'):
                report['UnreportableReason'] = '%s run "ppa-purge ppa:gnome3-team/gnome3-next".' % msg

        else:
            if release in ('Ubuntu 14.04', 'Ubuntu 16.04'):
                report['UnreportableReason'] = '%s run "ppa-purge ppa:gnome3-team/gnome3".' % msg

    if '[origin: LP-PPA-gnome3-team-gnome3' in report.get('Dependencies', ''):
        report.setdefault('Tags', '')
        report['Tags'] += ' gnome3-ppa'
        if release in ('Ubuntu 14.04', 'Ubuntu 16.04') and 'UnreportableReason' not in report:
            report['UnreportableReason'] = '%s use ppa-purge to remove the PPA.' % msg
