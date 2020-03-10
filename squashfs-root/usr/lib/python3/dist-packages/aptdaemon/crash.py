"""Apport integration to provide better problem reports."""
# Copyright (C) 2010 Sebastian Heinlein <devel@glatzor.de>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("create_report")

import os

import apport
import apport.fileutils
import apt_pkg

from . import enums


def create_report(error, traceback, trans=None):
    """Create an apport problem report for a given crash.

    :param error: The summary of the error.
    :param traceback: The traceback of the exception.
    :param trans: The optional transaction in which the crash occured.
    """
    if not apport.packaging.enabled() or os.getcwd() != "/":
        return

    uid = 0
    report = apport.Report("Crash")
    report["Title"] = error
    package = "aptdaemon"
    try:
        package_version = apport.packaging.get_version(package)
    except ValueError as e:
        if 'does not exist' in e.message:
            package_version = 'unknown'
    report['Package'] = '%s %s' % (package, package_version)
    report["SourcePackage"] = "aptdaemon"
    report["Traceback"] = traceback
    report["ExecutablePath"] = "/usr/sbin/aptd"
    report.add_os_info()

    # Attach information about the transaction
    if trans:
        report["Annotation"] = enums.get_role_error_from_enum(trans.role)
        report["TransactionRole"] = trans.role
        report["TransactionPackages"] = str([list(l) for l in trans.packages])
        report["TransactionDepends"] = str([list(l) for l in trans.depends])
        report["TransactionKwargs"] = str(trans.kwargs)
        report["TransactionLocale"] = trans.locale
        report["TransactionOutput"] = trans.output
        report["TransactionErrorCode"] = trans._error_property[0]
        report["TransactionErrorDetails"] = trans._error_property[1]
        uid = os.path.basename(trans.tid)

    # Write report
    report_path = apport.fileutils.make_report_path(report, uid)
    if not os.path.exists(report_path):
        report.write(open(report_path, 'wb'))

if __name__ == "__main__":
    apt_pkg.init_config()
    create_report('test', 'testtrace')

# vim:ts=4:sw=4:et
