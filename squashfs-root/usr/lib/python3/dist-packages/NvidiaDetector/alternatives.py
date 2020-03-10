#
#       alternatives.py
#
#       Copyright 2010 Canonical Services Ltd
#       Author: Alberto Milone <alberto.milone@canonical.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import os
import re
import subprocess
from subprocess import Popen, PIPE, CalledProcessError

class MultiArchUtils(object):

    def __init__(self):
        # We have 2 alternatives, one for each architecture
        self._supported_architectures = {'i386': 'i386', 'amd64': 'x86_64'}
        self._main_arch = self._get_architecture()
        self._other_arch = list(self._supported_architectures.values())[
                          int(not list(self._supported_architectures.values()).index(self._main_arch))]

        # Make sure that the PATH environment variable is set
        if not os.environ.get('PATH'):
            os.environ['PATH'] = '/sbin:/usr/sbin:/bin:/usr/bin'

    def _get_architecture(self):
        dev_null = open('/dev/null', 'w')
        p1 = Popen(['dpkg', '--print-architecture'], stdout=PIPE,
                   stderr=dev_null, universal_newlines=True)
        p = p1.communicate()[0]
        dev_null.close()
        architecture = p.strip()
        return self._supported_architectures.get(architecture)

    def _get_alternative_name_from_arch(self, architecture):
        alternative = '%s-linux-gnu_gl_conf' % architecture
        return alternative

    def get_main_alternative_name(self):
        return self._get_alternative_name_from_arch(self._main_arch)

    def get_other_alternative_name(self):
        return self._get_alternative_name_from_arch(self._other_arch)

class Alternatives(object):

    def __init__(self, master_link):
        self._open_drivers_alternative = 'mesa/ld.so.conf'
        self._open_egl_drivers_alternative = 'mesa-egl/ld.so.conf'
        self._command = 'update-alternatives'
        self._master_link = master_link

        # Make sure that the PATH environment variable is set
        if not os.environ.get('PATH'):
            os.environ['PATH'] = '/sbin:/usr/sbin:/bin:/usr/bin'

    def list_alternatives(self):
        '''Get the list of alternatives for the master link'''
        dev_null = open('/dev/null', 'w')
        alternatives = []
        p1 = Popen([self._command, '--list', self._master_link],
                   stdout=PIPE, stderr=dev_null, universal_newlines=True)
        p = p1.communicate()[0]
        dev_null.close()
        c = p.split('\n')
        for line in c:
            line.strip() and alternatives.append(line.strip())

        return alternatives

    def get_current_alternative(self):
        '''Get the alternative in use'''
        dev_null = open('/dev/null', 'w')
        current_alternative = None
        p1 = Popen([self._command, '--query', self._master_link],
                   stdout=PIPE, stderr=dev_null, universal_newlines=True)
        p = p1.communicate()[0]
        dev_null.close()
        c = p.split('\n')
        for line in c:
            if line.strip().startswith('Value:'):
                return line.replace('Value:', '').strip()
        return None

    def get_alternative_by_name(self, name, ignore_pattern=None):
        '''Get the alternative link by providing the driver name

        ignore_pattern allows ignoring a substring in the name'''
        if ignore_pattern:
            name = name.replace(ignore_pattern, '')
        alternatives = self.list_alternatives()

        for alternative in alternatives:
            if alternative.split('/')[-2] == name:
                return alternative

        return None

    def get_open_drivers_alternative(self):
        '''Get the alternative link for open drivers'''
        return self.get_alternative_by_name(self._open_drivers_alternative)

    def get_open_egl_drivers_alternative(self):
        '''Get the alternative link for open EGL/GLES drivers'''
        return self.get_alternative_by_name(self._open_egl_drivers_alternative)

    def update_gmenu(self):
        '''Trigger gmenu so that the icons will show up in the menu'''
        try:
            subprocess.check_call(['dpkg-trigger', '--by-package=fakepackage',
                                   'gmenucache'])
            subprocess.check_call(['dpkg', '--configure', '-a'])
        except (OSError, CalledProcessError):
            pass

    def set_alternative(self, path):
        '''Tries to set an alternative and returns the boolean exit status'''
        try:
            subprocess.check_call([self._command, '--set',
                                   self._master_link, path])
            self.ldconfig()
        except CalledProcessError:
            return False

        self.update_gmenu()

        return True

    def ldconfig(self):
        '''Call ldconfig'''
        try:
            subprocess.check_call(['ldconfig'])
        except CalledProcessError:
            return False
        return True

    def resolve_module_alias(self, alias):
        '''Get the 1st kernel module name matching an alias'''
        dev_null = open('/dev/null', 'w')
        current_alternative = None
        p1 = Popen(['modprobe', '--resolve-alias', alias], stdout=PIPE,
                   stderr=dev_null, universal_newlines=True)
        p = p1.communicate()[0]
        dev_null.close()
        c = p.split('\n')
        for line in c:
            if line.strip().startswith('Usage:'):
                return None
            return line.strip()
        return None
