#!/usr/bin/python

# grep the names of all Debian native packages out of Sources files
# Copyright (C) 2007 Stefano Zacchiroli <zack@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from __future__ import print_function

import sys

from debian import deb822

for fname in sys.argv[1:]:
    f = open(fname)
    for stanza in deb822.Sources.iter_paragraphs(f):
        pieces = stanza['version'].split('-')
        if len(pieces) < 2:
            print(stanza['package'])
    f.close()

