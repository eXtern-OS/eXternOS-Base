"""Apport integration to provide better problem reports."""
# Copyright (C) 2010-2011 Sebastian Heinlein <devel@glatzor.de>
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

import os
import re

import apport
import apport.hookutils
import apt_pkg

apt_pkg.init()


def add_info(report):
    """Collect and append additional information about a crash.

    Note: Please consider that aptdaemon also manually creates
          apport reports for failed transaction which don't result
          in a crash of aptdaemon, see aptdaemon.crash

    :param report: The apport report of an aptdaemon crash
    """
    # Attach apt configuration
    report["AptConfig"] = apt_pkg.config.dump()
    # Attach the sources list
    sources_list = ""
    etc_main = os.path.join(apt_pkg.config.find_dir("Dir::Etc"),
                            apt_pkg.config.find_file("Dir::Etc::sourcelist"))
    try:
        with open(etc_main) as fd_main:
            sources_list += fd_main.read()
    except:
        pass
    dir_parts = os.path.join(apt_pkg.config.find_dir("Dir::Etc"),
                             apt_pkg.config.find_dir("Dir::Etc::Sourceparts"))
    for filename in os.listdir(dir_parts):
        if not filename.endswith(".list"):
            continue
        try:
            with open(os.path.join(dir_parts, filename)) as fd_part:
                sources_list += fd_part.read()
        except:
            continue
    # Remove passwords from the sources list
    report["SourcesList"] = re.sub("://\w+?:\w+?@", "://USER:SECRET@",
                                   sources_list)

    # Add some logging data
    apport.hookutils.attach_file_if_exists(report, "/var/log/apt/history.log"
                                           "AptHistoryLog")
    apport.hookutils.attach_file_if_exists(report, "/var/log/apt/term.log",
                                           "AptTermLog")
    apport.hookutils.attach_file_if_exists(report, "/var/log/dpkg.log",
                                           "DpkgLog")
    report["SysLog"] = apport.hookutils.recent_syslog(re.compile("AptDaemon"))

# vim:ts=4:sw=4:et
