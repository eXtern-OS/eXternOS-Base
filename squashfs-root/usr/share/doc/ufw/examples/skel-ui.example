#! /usr/bin/python3
#
# skel-ui: skeleton frontend for ufw
#
# Copyright 2008 Canonical Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License version 3,
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import ufw.frontend
from ufw.common import UFWError
from ufw.util import error, warn

ufw.common.programName = "skel-ui"

import gettext
kwargs = {}
if sys.version_info[0] < 3:
    # In Python 2, ensure that the _() that gets installed into built-ins
    # always returns unicodes.  This matches the default behavior under Python
    # 3, although that keyword argument is not present in the Python 3 API.
    kwargs['unicode'] = True
gettext.install(ufw.common.programName, **kwargs)

if __name__ == "__main__":
    print(ufw.frontend.get_command_help())

