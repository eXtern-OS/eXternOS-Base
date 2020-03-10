'''Apport package hook for the Linux nexus7 kernel.

(c) 2012 Canonical Ltd.
Author: Martin Pitt <martin.pitt@canonical.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''


def add_info(report, ui):
    # direct bugs to the ubuntu-nexus7 project
    report['CrashDB'] = '''{"impl": "launchpad",
                            "project": "ubuntu-nexus7",
                            "bug_pattern_url": "http://people.canonical.com/~ubuntu-archive/bugpatterns/bugpatterns.xml",
                          }'''

    # collect information from original kernel hook
    report.add_hooks_info(ui, srcpackage='linux')

    # add additional tags
    report['Tags'] += ' mobile nexus7'
