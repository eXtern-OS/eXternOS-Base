#  software-properties cloud-archive support
#
#  Copyright (c) 2013 Canonical Ltd.
#
#  Author: Scott Moser <smoser@ubuntu.org>
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

from __future__ import print_function

import apt_pkg
import os
import subprocess
from gettext import gettext as _

from softwareproperties.shortcuts import ShortcutException

RELEASE_MAP = {
    'folsom': 'precise',
    'grizzly': 'precise',
    'havana': 'precise',
    'icehouse': 'precise',
    'juno': 'trusty',
    'kilo': 'trusty',
    'liberty': 'trusty',
    'mitaka': 'trusty',
    'newton': 'xenial',
    'ocata': 'xenial',
    'pike': 'xenial',
    'queens': 'xenial',
    'rocky': 'bionic',
    'stein': 'bionic',
    'train': 'bionic',
    'ussuri': 'bionic',
}
MIRROR = "http://ubuntu-cloud.archive.canonical.com/ubuntu"
UCA = "Ubuntu Cloud Archive"
WEB_LINK = 'https://wiki.ubuntu.com/OpenStack/CloudArchive'
APT_INSTALL_KEY = ['apt-get', '--quiet', '--assume-yes', 'install',
                   'ubuntu-cloud-keyring']

ALIASES = {'tools-updates': 'tools'}
for _r in RELEASE_MAP:
    ALIASES["%s-updates" % _r] = _r

MAP = {
    'tools': {
        'sldfmt': '%(codename)s-updates/cloud-tools',
        'description': UCA + " for cloud-tools (JuJu and MAAS)"},
    'tools-proposed': {
        'sldfmt': '%(codename)s-proposed/cloud-tools',
        'description': UCA + " for cloud-tools (JuJu and MAAS) [proposed]"}
}

for _r in RELEASE_MAP:
    MAP[_r] = {
        'sldfmt': '%(codename)s-updates/' + _r,
        'description': UCA + ' for ' + 'OpenStack ' + _r.capitalize(),
        'release': RELEASE_MAP[_r]}
    MAP[_r + "-proposed"] = {
        'sldfmt': '%(codename)s-proposed/' + _r,
        'description': UCA + ' for ' + 'OpenStack %s [proposed]' % _r.capitalize(),
        'release': RELEASE_MAP[_r]}


class CloudArchiveShortcutHandler(object):
    def __init__(self, shortcut):
        self.shortcut = shortcut

        prefix = "cloud-archive:"

        subs = {'shortcut': shortcut, 'prefix': prefix,
                'ca_names': sorted(MAP.keys())}
        if not shortcut.startswith(prefix):
            raise ValueError(
                _("shortcut '%(shortcut)s' did not start with '%(prefix)s'")
                % subs)

        name_in = shortcut[len(prefix):]
        caname = ALIASES.get(name_in, name_in)

        subs.update({'input_name': name_in})
        if caname not in MAP:
            raise ShortcutException(
                _("'%(input_name)s': not a valid cloud-archive name.\n"
                  "Must be one of %(ca_names)s") % subs)

        self.caname = caname
        self._info = MAP[caname].copy()
        self._info['web_link' ] = WEB_LINK

    def info(self):
        return self._info

    def expand(self, codename, distro=None):
        if codename not in (MAP[self.caname]['release'],
                            os.environ.get("CA_ALLOW_CODENAME")):
            raise ShortcutException(
                _("cloud-archive for %(os_release)s only supported on %(codename)s")
                % {'codename': MAP[self.caname]['release'],
                   'os_release': self.caname.capitalize()})
        dist = MAP[self.caname]['sldfmt'] % {'codename': codename}
        line = ' '.join(('deb', MIRROR, dist, 'main',))
        return (line, _fname_for_caname(self.caname))

    def should_confirm(self):
        return True

    def add_key(self, keyserver=None):
        env = os.environ.copy()
        env['DEBIAN_FRONTEND'] = 'noninteractive'
        try:
            subprocess.check_call(args=APT_INSTALL_KEY, env=env)
        except subprocess.CalledProcessError:
            return False
        return True


def _fname_for_caname(caname):
    # caname is an entry in MAP ('tools' or 'tools-proposed')
    return os.path.join(
        apt_pkg.config.find_dir("Dir::Etc::sourceparts"),
        'cloudarchive-%s.list' % caname)


def shortcut_handler(shortcut):
    try:
        return CloudArchiveShortcutHandler(shortcut)
    except ValueError:
        return None
