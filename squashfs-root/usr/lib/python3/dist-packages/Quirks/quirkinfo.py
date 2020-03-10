# -*- coding: utf-8 -*-
# (c) 2012 Canonical Ltd.
#
# Authors: Alberto Milone <alberto.milone@canonical.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.




import os

dmi_keys = ('product_name', 'product_version',
             'sys_vendor', 'bios_version',
             'bios_vendor', 'bios_date',
             'board_name', 'board_vendor')

class QuirkInfo:
    def __init__(self):
        self.sys_dir = '/sys'
        self._quirk_info = {}.fromkeys(dmi_keys, '')

    def get_dmi_info(self):
        '''Return all the dmi info of the system hardware.

        Some or the whole Dmi info may not be available on
        some systems.

        The default implementation queries sysfs.
        '''
        for item in self._quirk_info.keys():
            try:
                value = open(os.path.join(self.sys_dir,
                    'class', 'dmi', 'id', item)).read().strip()
            except (OSError, IOError, UnicodeDecodeError):
                value = ''
            self._quirk_info[item] = value
        
        return self._quirk_info


def main():
    a = QuirkInfo()
    print(a.get_dmi_info())
    
    return 0

#if __name__ == '__main__':
    #main()

