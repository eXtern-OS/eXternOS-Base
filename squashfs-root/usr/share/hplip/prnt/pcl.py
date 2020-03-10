# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

# Std Lib
import struct

# Local
from base import pml
from base.sixext import to_bytes_utf8

ESC = to_bytes_utf8('\x1b')
RESET = to_bytes_utf8('\x1bE')
UEL = to_bytes_utf8('\x1b%-12345X')
PJL_ENTER_LANG = to_bytes_utf8("@PJL ENTER LANGUAGE=PCL3GUI\n")
PJL_BEGIN_JOB = to_bytes_utf8('@PJL JOB NAME="unnamed"\n')
PJL_END_JOB = to_bytes_utf8('@PJL EOJ\n')

def buildPCLCmd(punc, letter1, letter2, data=None, value=None):
    if data is None:
        return to_bytes_utf8('').join([ESC, to_bytes_utf8(punc), to_bytes_utf8(letter1), to_bytes_utf8(str(value)), to_bytes_utf8(letter2)])
    return to_bytes_utf8('').join([ESC, to_bytes_utf8(punc), to_bytes_utf8(letter1), to_bytes_utf8(str(len(data))), to_bytes_utf8(letter2), data])


def buildEmbeddedPML(pml):
    return to_bytes_utf8('').join([UEL, PJL_ENTER_LANG, RESET, pml, RESET, UEL])


def buildEmbeddedPML2(pml):
    return to_bytes_utf8('').join([RESET, UEL, PJL_BEGIN_JOB, PJL_ENTER_LANG, RESET, pml, RESET, PJL_END_JOB, RESET, UEL])


def buildDynamicCounter(counter):
    #return ''.join([UEL, PJL_ENTER_LANG, ESC, '*o5W\xc0\x01', struct.pack(">I", counter)[1:], UEL])
    return to_bytes_utf8('').join([UEL, PJL_ENTER_LANG, ESC, b'*o5W\xc0\x01', struct.pack(">I", counter)[1:], PJL_END_JOB, UEL])

def buildRP(a, f, c, d, e):
    return to_bytes_utf8('').join([b'\x00'*600, RESET, UEL, PJL_ENTER_LANG, buildPCLCmd('&', 'b', 'W', pml.buildEmbeddedPMLSetPacket('1.1.1.36', a + f + c + d + e, pml.TYPE_STRING)), RESET, UEL])
