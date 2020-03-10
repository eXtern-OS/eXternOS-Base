# Copyright (c) 2008 Canonical
#
# AUTHOR:
# Siegfried-A. Gevatter <rainct@ubuntu.com>
#
# This file is part of AptUrl
#
# AptUrl is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# AptUrl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AptUrl; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import gettext
import subprocess

def _(str):
    return utf8(gettext.gettext(str))

def _n(singular, plural, n):
    return utf8(gettext.ngettext(singular, plural, n))

def utf8(str):
    if str is bytes:
        try:
            return str.decode('UTF-8')
        except UnicodeDecodeError:
            # assume latin1 as fallback
            return str.decode('latin1')
    else:
        return str

def get_dist():
    return subprocess.check_output(
        'lsb_release -c -s'.split(),
        universal_newlines=True).strip()


def parse_pkg(pkgobj):
    summary = ""
    description = ""
    pkg_description = pkgobj.candidate.description
    if pkg_description.count("\n") > 0:
        summary, description = pkg_description.split('\n', 1)
    else:
        summary = pkg_description
    lines = description.rstrip('\n').split('\n')
    if len(lines) > 1 and lines[-1].startswith('Homepage: '):
        homepage = lines[-1].split(' ', 1)[1]
        description = '\n'.join(lines[:-1])
    else:
        homepage = pkgobj.candidate.homepage
    return (summary, description, homepage)

def format_description(description):
    const = 'APTURL_DOUBLE_EMPTY_LINE_PLACEHOLDER'
    return description.replace('\n\n', const).replace('\n', ' ').replace(
        const, '\n\n')
