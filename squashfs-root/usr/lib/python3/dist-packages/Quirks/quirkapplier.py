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

from glob import glob
import os
import sys
import tempfile
import logging

import xkit.xutils
import xkit.xorgparser

import Quirks.quirkreader
import Quirks.quirkinfo

class QuirkChecker:
    def __init__(self, handler, path='/usr/share/jockey/quirks'):
        self._handler = handler
        self.quirks_path = path
        self._quirks = []
        self.get_quirks_from_path()
        self._system_info = self.get_system_info()
        self._xorg_conf_d_path = '/usr/share/X11/xorg.conf.d'

    def get_quirks_from_path(self):
        '''check all the files in a directory looking for quirks'''
        self._quirks = []
        if os.path.isdir(self.quirks_path):
            for f in glob(os.path.join(self.quirks_path, '*')):
                if os.path.isfile(f):
                    logging.debug('Parsing %s' % f)
                    quirks = self.get_quirks_from_file(f)
                    self._quirks += quirks
        else:
            logging.debug('%s does not exist' % self.quirks_path)
        return self._quirks
        

    def get_quirks_from_file(self, quirk_file):
        '''check all the files in a directory looking for quirks'''
        # read other blacklist files (which we will not touch, but evaluate)
        quirk_file = Quirks.quirkreader.ReadQuirk(quirk_file)
        return quirk_file.get_quirks()

    def get_system_info(self):
        '''Get system info for the quirk'''
        quirk_info = Quirks.quirkinfo.QuirkInfo()
        return quirk_info.get_dmi_info()

    def matches_tags(self, quirk):
        '''See if tags match system info'''
        result = True
        for tag in quirk.match_tags.keys():
            for val in quirk.match_tags[tag]:
                if (self._system_info.get(tag) and self._system_info.get(tag) != val
                and len(quirk.match_tags[tag]) <= 1):
                    logging.debug('Failure to match %s with %s' %
                                  (self._system_info.get(tag), val))
                    return False
        logging.debug('Success')
        return result

    def _check_quirks(self, enable=True):
        '''Process quirks and do something with them'''
        for quirk in self._quirks:
            if self._handler.lower() in [x.lower().strip() for x in quirk.handler]:
                logging.debug('Processing quirk %s' % quirk.id)
                if self.matches_tags(quirk):
                    # Do something here
                    if enable:
                        logging.info('Applying quirk %s' % quirk.id)
                        self._apply_quirk(quirk)
                    else:
                        logging.info('Unapplying quirk %s' % quirk.id)
                        self._unapply_quirk(quirk)
                else:
                    logging.debug('Quirk doesn\'t match')
    
    def enable_quirks(self):
        '''Enable all quirks for a handler'''
        self._check_quirks(True)

    def disable_quirks(self):
        '''Disable all quirks for a handler'''
        self._check_quirks(False)

    def _get_destination_path(self, quirk):
        '''Return the path to the X config file'''
        return '%s/10-%s-%s.conf' % (self._xorg_conf_d_path,
                self._handler, quirk.id.lower().replace(' ', '-'))

    def _apply_quirk(self, quirk):
        '''Get the xorg snippet and apply it'''
        # Get the relevant x_snippet
        # Write conf file to /usr/share/X11/xorg.conf.d/file.conf
        destination = self._get_destination_path(quirk)
        tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp_file.write(quirk.x_snippet)
        tmp_file.close()
        tmp_xkit = xkit.xorgparser.Parser(tmp_file.name)
        # TODO: REMOVE THIS
        logging.debug(tmp_xkit.globaldict)
        os.unlink(tmp_file.name)
        try:
            logging.debug('Creating %s' % destination)
            tmp_xkit.write(destination)
        except IOError:
            logging.exception('Error during write()')
            return False
        return True

    def _unapply_quirk(self, quirk):
        '''Remove the file with the xorg snippet'''
        # Get the relevant x_snippet
        # Write conf file to /usr/share/X11/xorg.conf.d/file.conf
        destination = self._get_destination_path(quirk)
        logging.debug('Removing %s ...' % destination)
        try:
            os.unlink(destination)
        except (OSError, IOError):
            logging.exception('Cannot unlink destination')
            return False
        return True


def main():

    a = QuirkChecker('nvidia', path='/home/alberto/oem/jockey/quirks')
    a.enable_quirks()
    a.disable_quirks()
    print(os.path.abspath( __file__ ))
    #quirk_file = ReadQuirk("quirk_snippet.txt")
    #quirks = quirk_file.get_quirks()
    #for quirk in quirks:
        #print 'Quirk id: "%s"' % quirk.id
        #for tag in quirk.match_tags.keys():
            #print 'Matching "%s" with value "%s"' % (tag, quirk.match_tags[tag])
        #print quirk.x_snippet

    #tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    #tmp_file.write(quirk.x_snippet)
    #tmp_file.close()

    #tmp_xkit = xkit.xorgparser.Parser(tmp_file.name)
    #print tmp_xkit.globaldict
    #os.unlink(tmp_file.name)


    return 0

#if __name__ == '__main__':
    #main()

