#!/usr/bin/python3
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

import xkit.xutils
import xkit.xorgparser
import Quirks.quirkinfo

import tempfile
import os

class Quirk:

    def __init__(self, id=None, handler=[], x_snippet="", match_tags={}):
        self.id = id
        self.handler = handler
        self.x_snippet = x_snippet
        self.match_tags = {}.fromkeys(Quirks.quirkinfo.dmi_keys, '')

class ReadQuirk:

    def __init__(self, source=None):
        self.source = source
        
        #See if the source is a file or a file object
        #and act accordingly
        file = self.source
        if file == None:
            lines_list = []
        else:
            if not hasattr(file, 'write'):#it is a file
                myfile = open(file, 'r', encoding='utf-8')
                lines_list = myfile.readlines()
                myfile.close()
            else:#it is a file object
                lines_list = file.readlines()
        
        inside_quirk = False
        has_id = False
        has_handler = False
        inside_x_snippet = False
        self._quirks = []

        it = 0
        for line in lines_list:
            if line.strip().startswith('#'):
                continue
            if inside_quirk:
                if inside_x_snippet:

                    if line.lower().strip().startswith('endxorgsnippet'):
                        inside_x_snippet = False
                        continue
                    else:
                        self._quirks[it].x_snippet += line
                else:
                    #not in x_snippet
                    if not has_id and line.lower().strip().startswith('identifier'):
                        has_id = True
                        temp_str = "identifier"
                        id = line[line.lower().rfind(temp_str) + len(
                             temp_str):].strip().replace('"', '')
                        self._quirks[it].id = id
                        del temp_str
                    elif not has_handler and line.lower().strip().startswith('handler'):
                        has_handler = True
                        temp_str = "handler"
                        handler = line[line.lower().rfind(temp_str) + len(
                             temp_str):].strip().replace('"', '')
                        handlers_list = handler.split('|')
                        self._quirks[it].handler = handlers_list
                        del temp_str
                    elif line.lower().strip().startswith('match'):
                        temp_str = "match"
                        temp_bits = line[line.lower().rfind(temp_str) +
                                    len(temp_str):].strip().split('"')
                        tag_match = ''
                        tag_value = ''
                        tag_values = []
                        for elem in temp_bits:
                            if elem.strip():
                                if not tag_match:
                                    tag_match = elem.strip()
                                    #tag_values = []
                                else:
                                    tag_value = elem.strip()
                                    tag_values = tag_value.split('|')
                                    self._quirks[it].match_tags[tag_match] = tag_values
                                    break
                        del temp_bits
                        del temp_str
                        del tag_values
                    elif line.lower().strip().startswith('xorgsnippet'):
                        inside_x_snippet = True
                        self._quirks[it].x_snippet = ""
                        continue
        
                    elif line.lower().strip().startswith('endsection'):
                        #End Quirk
                        inside_quirk = False
                        if not self._quirks[it].id:
                            self._quirks.pop(it)
                        else:
                            it += 1
            else:
                if line.lower().strip().startswith('section') \
                and "quirk" in line.lower():
                    #Begin Quirk
                    inside_quirk = True
                    temp_quirk = Quirk()
                    self._quirks.append(temp_quirk)
                    del temp_quirk
                    continue

    def get_quirks(self):
        return self._quirks


#if __name__ == "__main__":
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
