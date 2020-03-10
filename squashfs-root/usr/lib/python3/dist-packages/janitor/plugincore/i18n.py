# Copyright (C) 2008-2012  Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

"""Set up the gettext context."""


import os
import gettext


def setup_gettext():
    """Set up gettext for a module."""
    domain = 'update-manager'
    localedir = os.environ.get('LOCPATH', None)
    t = gettext.translation(domain, localedir=localedir, fallback=True)
    try:
        # We must receive unicodes from the catalog.  Python 2 by default
        # returns 8-bit strings from the .gettext() method, so use the unicode
        # variant.  If this doesn't exist, we're in Python 3 and there,
        # .gettext does the right thing.
        return t.ugettext
    except AttributeError:
        return t.gettext
