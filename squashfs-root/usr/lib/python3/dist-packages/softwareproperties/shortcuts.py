#  Copyright (c) 2013 Canonical Ltd.
#
#  Author: Scott Moser <smoser@ubuntu.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import aptsources.distro
from gettext import gettext as _

_DEF_CODENAME = aptsources.distro.get_distro().codename


class ShortcutHandler(object):
    # the defeault ShortcutHandler only handles actual apt lines.
    # ie, 'shortcut' here is a line like you'd find in /etc/apt/sources.list:
    #   deb MIRROR RELEASE-POCKET COMPONENT
    def __init__(self, shortcut):
        self.shortcut = shortcut

    def add_key(self, keyserver=None):
        return True

    def expand(self, codename=None, distro=None):
        return (self.shortcut, None)

    def info(self):
        return {
            'description': _("No description available for '%(shortcut)s'") %
                             {'shortcut': self.shortcut},
            'web_link': _("web link unavailable")}

    def should_confirm(self):
        return False


class ShortcutException(Exception):
    pass


def shortcut_handler(shortcut):
    # this is the default shortcut handler, so it matches anything
    return ShortcutHandler(shortcut)

# vi: ts=4 expandtab
