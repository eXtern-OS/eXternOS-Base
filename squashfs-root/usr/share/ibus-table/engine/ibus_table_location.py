# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2015 Mike FABIAN <mfabian@redhat.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

'''
Get locations where ibus-table stores stuff.

The directories used are according to the
“XDG Base Directory Specification”,
see: http://standards.freedesktop.org/basedir-spec/latest/index.html
'''

import os

ibus_table_location = {
    'data': '',
    'lib': '',
    'data_home': '',
    'cache_home': '',
}

def data():
    return ibus_table_location['data']

def lib():
    return ibus_table_location['lib']

def data_home():
    return ibus_table_location['data_home']

def cache_home():
    return ibus_table_location['cache_home']

def _init():
    ibus_table_location['data'] = os.getenv('IBUS_TABLE_LOCATION')
    if (not ibus_table_location['data']
        or not os.path.exists(ibus_table_location['data'])):
        ibus_table_location['data'] = "/usr/share/ibus-table/"

    ibus_table_location['lib'] = os.getenv('IBUS_TABLE_LIB_LOCATION')
    if (not ibus_table_location['lib']
        or not os.path.exists(ibus_table_location['lib'])):
        ibus_table_location['lib'] = "/usr/libexec"

    # $XDG_DATA_HOME defines the base directory relative to which user
    # specific data files should be stored. If $XDG_DATA_HOME is either
    # not set or empty, a default equal to $HOME/.local/share should be
    # used.
    ibus_table_location['data_home'] = os.getenv('IBUS_TABLE_DATA_HOME')
    if (not ibus_table_location['data_home']
        or not os.path.exists(ibus_table_location['data_home'])):
        ibus_table_location['data_home'] = os.getenv('XDG_DATA_HOME')
    if (not ibus_table_location['data_home']
        or not os.path.exists(ibus_table_location['data_home'])):
        ibus_table_location['data_home'] = os.path.expanduser('~/.local/share')
    ibus_table_location['data_home'] = os.path.join(
        ibus_table_location['data_home'], 'ibus-table')
    if not os.access(ibus_table_location['data_home'], os.F_OK):
        os.makedirs(ibus_table_location['data_home'])

    # $XDG_CACHE_HOME defines the base directory relative to which user
    # specific non-essential data files should be stored. If
    # $XDG_CACHE_HOME is either not set or empty, a default equal to
    # $HOME/.cache should be used.
    ibus_table_location['cache_home'] = os.getenv('IBUS_TABLE_CACHE_HOME')
    if (not ibus_table_location['cache_home']
        or not os.path.exists(ibus_table_location['cache_home'])):
        ibus_table_location['cache_home'] = os.getenv('XDG_CACHE_HOME')
    if (not ibus_table_location['cache_home']
        or not os.path.exists(ibus_table_location['cache_home'])):
        ibus_table_location['cache_home'] = os.path.expanduser('~/.cache')
    ibus_table_location['cache_home'] = os.path.join(
        ibus_table_location['cache_home'], 'ibus-table')
    if not os.access(ibus_table_location['cache_home'], os.F_OK):
        os.makedirs(ibus_table_location['cache_home'])

class __ModuleInitializer:
    def __init__(self):
        _init()
        return

    def __del__(self):
        return

__module_init = __ModuleInitializer()

