# -*- coding: utf-8 -*-
#
# magic.py
# determines a file type by its magic number
#
# Copyright (c) 2000, Jason Petrone <jp_py@demonseed.net>
# All Rights Reserved
#
# Modifications by Don Welch
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions and the following disclaimer in the documentation and/or
#     other materials provided with the distribution.
#     * Neither the name of the <ORGANIZATION> nor the names of its contributors may
#     be used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  Command Line Usage: running as `python magic.py file` will print
#                      a description of what 'file' is.
#
#  Module Usage:
#      magic.whatis(data): when passed a string 'data' containing
#                          binary or text data, a description of
#                          what the data is will be returned.
#
#      magic.mime_type(filename): returns a description of what the file
#                            '    filename' contains.
#

import re
import struct
import os.path

__version__ = '0.2'

magic = [
    [0, 'string', '=', b'#define', 'image/x-xbitmap'],
    [0, 'leshort', '=', 1538, 'application/x-alan-adventure-game'],
    [0, 'string', '=', b'TADS', 'application/x-tads-game'],
    [0, 'short', '=', 420, 'application/x-executable-file'],
    [0, 'short', '=', 421, 'application/x-executable-file'],
    [0, 'leshort', '=', 603, 'application/x-executable-file'],
    [0, 'string', '=', b'Core\001', 'application/x-executable-file'],
    [0, 'string', '=', b'AMANDA: TAPESTART DATE', 'application/x-amanda-header'],
    [0, 'belong', '=', 1011, 'application/x-executable-file'],
    [0, 'belong', '=', 999, 'application/x-library-file'],
    [0, 'belong', '=', 435, 'video/mpeg'],
    [0, 'belong', '=', 442, 'video/mpeg'],
    [0, 'beshort&0xfff0', '=', 65520, 'audio/mpeg'],
    [4, 'leshort', '=', 44817, 'video/fli'],
    [4, 'leshort', '=', 44818, 'video/flc'],
    [0, 'string', '=', b'MOVI', 'video/x-sgi-movie'],
    [4, 'string', '=', b'moov', 'video/quicktime'],
    [4, 'string', '=', b'mdat', 'video/quicktime'],
    [0, 'long', '=', 100554, 'application/x-apl-workspace'],
    [0, 'string', '=', b'FiLeStArTfIlEsTaRt', 'text/x-apple-binscii'],
    [0, 'string', '=', b'\012GL', 'application/data'],
    [0, 'string', '=', b'v\377', 'application/data'],
    [0, 'string', '=', b'NuFile', 'application/data'],
    [0, 'string', '=', b'N\365F\351l\345', 'application/data'],
    [0, 'belong', '=', 333312, 'application/data'],
    [0, 'belong', '=', 333319, 'application/data'],
    [257, 'string', '=', b'ustar\000', 'application/x-tar'],
    [257, 'string', '=', b'ustar  \000', 'application/x-gtar'],
    [0, 'short', '=', 70707, 'application/x-cpio'],
    [0, 'short', '=', 143561, 'application/x-bcpio'],
    [0, 'string', '=', b'070707', 'application/x-cpio'],
    [0, 'string', '=', b'070701', 'application/x-cpio'],
    [0, 'string', '=', b'070702', 'application/x-cpio'],
    [0, 'string', '=', b'!<arch>\012debian', 'application/x-dpkg'],
    [0, 'long', '=', 177555, 'application/x-ar'],
    [0, 'short', '=', 177555, 'application/data'],
    [0, 'long', '=', 177545, 'application/data'],
    [0, 'short', '=', 177545, 'application/data'],
    [0, 'long', '=', 100554, 'application/x-apl-workspace'],
    [0, 'string', '=', b'<ar>', 'application/x-ar'],
    [0, 'string', '=', b'!<arch>\012__________E', 'application/x-ar'],
    [0, 'string', '=', b'-h-', 'application/data'],
    [0, 'string', '=', b'!<arch>', 'application/x-ar'],
    [0, 'string', '=', b'<ar>', 'application/x-ar'],
    [0, 'string', '=', b'<ar>', 'application/x-ar'],
    [0, 'belong', '=', 1711210496, 'application/x-ar'],
    [0, 'belong', '=', 1013019198, 'application/x-ar'],
    [0, 'long', '=', 557605234, 'application/x-ar'],
    [0, 'lelong', '=', 177555, 'application/data'],
    [0, 'leshort', '=', 177555, 'application/data'],
    [0, 'lelong', '=', 177545, 'application/data'],
    [0, 'leshort', '=', 177545, 'application/data'],
    [0, 'lelong', '=', 236525, 'application/data'],
    [0, 'lelong', '=', 236526, 'application/data'],
    [0, 'lelong&0x8080ffff', '=', 2074, 'application/x-arc'],
    [0, 'lelong&0x8080ffff', '=', 2330, 'application/x-arc'],
    [0, 'lelong&0x8080ffff', '=', 538, 'application/x-arc'],
    [0, 'lelong&0x8080ffff', '=', 794, 'application/x-arc'],
    [0, 'lelong&0x8080ffff', '=', 1050, 'application/x-arc'],
    [0, 'lelong&0x8080ffff', '=', 1562, 'application/x-arc'],
    [0, 'string', '=', b'\032archive', 'application/data'],
    [0, 'leshort', '=', 60000, 'application/x-arj'],
    [0, 'string', '=', b'HPAK', 'application/data'],
    [0, 'string', '=', b'\351,\001JAM application/data', ''],
    [2, 'string', '=', b'-lh0-', 'application/x-lha'],
    [2, 'string', '=', b'-lh1-', 'application/x-lha'],
    [2, 'string', '=', b'-lz4-', 'application/x-lha'],
    [2, 'string', '=', b'-lz5-', 'application/x-lha'],
    [2, 'string', '=', b'-lzs-', 'application/x-lha'],
    [2, 'string', '=', b'-lh -', 'application/x-lha'],
    [2, 'string', '=', b'-lhd-', 'application/x-lha'],
    [2, 'string', '=', b'-lh2-', 'application/x-lha'],
    [2, 'string', '=', b'-lh3-', 'application/x-lha'],
    [2, 'string', '=', b'-lh4-', 'application/x-lha'],
    [2, 'string', '=', b'-lh5-', 'application/x-lha'],
    [0, 'string', '=', b'Rar!', 'application/x-rar'],
    [0, 'string', '=', b'SQSH', 'application/data'],
    [0, 'string', '=', b'UC2\032', 'application/data'],
    [0, 'string', '=', b'PK\003\004', 'application/zip'],
    [20, 'lelong', '=', 4257523676, 'application/x-zoo'],
    [10, 'string', '=', b'# This is a shell archive', 'application/x-shar'],
    [0, 'string', '=', b'*STA', 'application/data'],
    [0, 'string', '=', b'2278', 'application/data'],
    [0, 'beshort', '=', 560, 'application/x-executable-file'],
    [0, 'beshort', '=', 561, 'application/x-executable-file'],
    [0, 'string', '=', b'\000\004\036\212\200', 'application/core'],
    [0, 'string', '=', b'.snd', 'audio/basic'],
    [0, 'lelong', '=', 6583086, 'audio/basic'],
    [0, 'string', '=', b'MThd', 'audio/midi'],
    [0, 'string', '=', b'CTMF', 'audio/x-cmf'],
    [0, 'string', '=', b'SBI', 'audio/x-sbi'],
    [0, 'string', '=', b'Creative Voice File', 'audio/x-voc'],
    [0, 'belong', '=', 1314148939, 'audio/x-multitrack'],
    [0, 'string', '=', b'RIFF', 'audio/x-wav'],
    [0, 'string', '=', b'EMOD', 'audio/x-emod'],
    [0, 'belong', '=', 779248125, 'audio/x-pn-realaudio'],
    [0, 'string', '=', b'MTM', 'audio/x-multitrack'],
    [0, 'string', '=', b'if', 'audio/x-669-mod'],
    [0, 'string', '=', b'FAR', 'audio/mod'],
    [0, 'string', '=', b'MAS_U', 'audio/x-multimate-mod'],
    [44, 'string', '=', b'SCRM', 'audio/x-st3-mod'],
    [0, 'string', '=', b'GF1PATCH110\000ID#000002\000','audio/x-gus-patch'],
    [0, 'string', '=', b'GF1PATCH100\000ID#000002\000', 'audio/x-gus-patch'],
    [0, 'string', '=', b'JN', 'audio/x-669-mod'],
    [0, 'string', '=', b'UN05', 'audio/x-mikmod-uni'],
    [0, 'string', '=', b'Extended Module:', 'audio/x-ft2-mod'],
    [21, 'string', '=', b'!SCREAM!', 'audio/x-st2-mod'],
    [1080, 'string', '=', b'M.K.', 'audio/x-protracker-mod'],
    [1080, 'string', '=', b'M!K!', 'audio/x-protracker-mod'],
    [1080, 'string', '=', b'FLT4', 'audio/x-startracker-mod'],
    [1080, 'string', '=', b'4CHN', 'audio/x-fasttracker-mod'],
    [1080, 'string', '=', b'6CHN', 'audio/x-fasttracker-mod'],
    [1080, 'string', '=', b'8CHN', 'audio/x-fasttracker-mod'],
    [1080, 'string', '=', b'CD81', 'audio/x-oktalyzer-mod'],
    [1080, 'string', '=', b'OKTA', 'audio/x-oktalyzer-mod'],
    [1080, 'string', '=', b'16CN', 'audio/x-taketracker-mod'],
    [1080, 'string', '=', b'32CN', 'audio/x-taketracker-mod'],
    [0, 'string', '=', b'TOC', 'audio/x-toc'],
    [0, 'short', '=', 3401, 'application/x-executable-file'],
    [0, 'long', '=', 406, 'application/x-executable-file'],
    [0, 'short', '=', 406, 'application/x-executable-file'],
    [0, 'short', '=', 3001, 'application/x-executable-file'],
    [0, 'lelong', '=', 314, 'application/x-executable-file'],
    [0, 'string', '=', b'//', 'text/cpp'],
    [0, 'string', '=', b'\\\\1cw\\', 'application/data'],
    [0, 'string', '=', b'\\\\1cw', 'application/data'],
    [0, 'belong&0xffffff00', '=', 2231440384, 'application/data'],
    [0, 'belong&0xffffff00', '=', 2231487232, 'application/data'],
    [0, 'short', '=', 575, 'application/x-executable-file'],
    [0, 'short', '=', 577, 'application/x-executable-file'],
    [4, 'string', '=', b'pipe', 'application/data'],
    [4, 'string', '=', b'prof', 'application/data'],
    [0, 'string', '=', b': shell', 'application/data'],
    [0, 'string', '=', b'#!/bin/sh', 'application/x-sh'],
    [0, 'string', '=', b'#! /bin/sh', 'application/x-sh'],
    [0, 'string', '=', b'#! /bin/sh', 'application/x-sh'],
    [0, 'string', '=', b'#!/bin/csh', 'application/x-csh'],
    [0, 'string', '=', b'#! /bin/csh', 'application/x-csh'],
    [0, 'string', '=', b'#! /bin/csh', 'application/x-csh'],
    [0, 'string', '=', b'#!/bin/ksh', 'application/x-ksh'],
    [0, 'string', '=', b'#! /bin/ksh', 'application/x-ksh'],
    [0, 'string', '=', b'#! /bin/ksh', 'application/x-ksh'],
    [0, 'string', '=', b'#!/bin/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#! /bin/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#! /bin/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#!/usr/local/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#! /usr/local/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#!/usr/local/bin/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#! /usr/local/bin/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#! /usr/local/bin/tcsh', 'application/x-csh'],
    [0, 'string', '=', b'#!/usr/local/bin/zsh', 'application/x-zsh'],
    [0, 'string', '=', b'#! /usr/local/bin/zsh', 'application/x-zsh'],
    [0, 'string', '=', b'#! /usr/local/bin/zsh', 'application/x-zsh'],
    [0, 'string', '=', b'#!/usr/local/bin/ash', 'application/x-sh'],
    [0, 'string', '=', b'#! /usr/local/bin/ash', 'application/x-zsh'],
    [0, 'string', '=', b'#! /usr/local/bin/ash', 'application/x-zsh'],
    [0, 'string', '=', b'#!/usr/local/bin/ae', 'text/script'],
    [0, 'string', '=', b'#! /usr/local/bin/ae', 'text/script'],
    [0, 'string', '=', b'#! /usr/local/bin/ae', 'text/script'],
    [0, 'string', '=', b'#!/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#!/usr/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#!/usr/local/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/local/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/local/bin/nawk', 'application/x-awk'],
    [0, 'string', '=', b'#!/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#!/usr/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#!/usr/local/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/local/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/local/bin/gawk', 'application/x-awk'],
    [0, 'string', '=', b'#!/bin/awk', 'application/x-awk'],
    [0, 'string', '=', b'#! /bin/awk', 'application/x-awk'],
    [0, 'string', '=', b'#! /bin/awk', 'application/x-awk'],
    [0, 'string', '=', b'#!/usr/bin/awk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/bin/awk', 'application/x-awk'],
    [0, 'string', '=', b'#! /usr/bin/awk', 'application/x-awk'],
    [0, 'string', '=', b'BEGIN', 'application/x-awk'],
    [0, 'string', '=', b'#!/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#! /bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#! /bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'eval "exec /bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#!/usr/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#! /usr/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#! /usr/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'eval "exec /usr/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#!/usr/local/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#! /usr/local/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#! /usr/local/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'eval "exec /usr/local/bin/perl', 'application/x-perl'],
    [0, 'string', '=', b'#!/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#! /bin/python', 'application/x-python'],
    [0, 'string', '=', b'#! /bin/python', 'application/x-python'],
    [0, 'string', '=', b'eval "exec /bin/python', 'application/x-python'],
    [0, 'string', '=', b'#!/usr/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#! /usr/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#! /usr/bin/python', 'application/x-python'],
    [0, 'string', '=', b'eval "exec /usr/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#!/usr/local/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#! /usr/local/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#! /usr/local/bin/python', 'application/x-python'],
    [0, 'string', '=', b'eval "exec /usr/local/bin/python', 'application/x-python'],
    [0, 'string', '=', b'#!/usr/bin/env python', 'application/x-python'],
    [0, 'string', '=', b'#! /usr/bin/env python', 'application/x-python'],
    [0, 'string', '=', b'#!/bin/rc', 'text/script'],
    [0, 'string', '=', b'#! /bin/rc', 'text/script'],
    [0, 'string', '=', b'#! /bin/rc', 'text/script'],
    [0, 'string', '=', b'#!/bin/bash', 'application/x-sh'],
    [0, 'string', '=', b'#! /bin/bash', 'application/x-sh'],
    [0, 'string', '=', b'#! /bin/bash', 'application/x-sh'],
    [0, 'string', '=', b'#!/usr/local/bin/bash', 'application/x-sh'],
    [0, 'string', '=', b'#! /usr/local/bin/bash', 'application/x-sh'],
    [0, 'string', '=', b'#! /usr/local/bin/bash', 'application/x-sh'],
    [0, 'string', '=', b'#! /', 'text/script'],
    [0, 'string', '=', b'#! /', 'text/script'],
    [0, 'string', '=', b'#!/', 'text/script'],
    [0, 'string', '=', b'#! text/script', ''],
    [0, 'string', '=', b'\037\235', 'application/compress'],
    [0, 'string', '=', b'\037\213', 'application/x-gzip'],
    [0, 'string', '=', b'\037\036', 'application/data'],
    [0, 'short', '=', 17437, 'application/data'],
    [0, 'short', '=', 8191, 'application/data'],
    [0, 'string', '=', b'\377\037', 'application/data'],
    [0, 'short', '=', 145405, 'application/data'],
    [0, 'string', '=', b'BZh', 'application/x-bzip2'],
    [0, 'leshort', '=', 65398, 'application/data'],
    [0, 'leshort', '=', 65142, 'application/data'],
    [0, 'leshort', '=', 64886, 'application/x-lzh'],
    [0, 'string', '=', b'\037\237', 'application/data'],
    [0, 'string', '=', b'\037\236', 'application/data'],
    [0, 'string', '=', b'\037\240', 'application/data'],
    [0, 'string', '=', b'BZ', 'application/x-bzip'],
    [0, 'string', '=', b'\211LZO\000\015\012\032\012',
     'application/data'],
    [0, 'belong', '=', 507, 'application/x-object-file'],
    [0, 'belong', '=', 513, 'application/x-executable-file'],
    [0, 'belong', '=', 515, 'application/x-executable-file'],
    [0, 'belong', '=', 517, 'application/x-executable-file'],
    [0, 'belong', '=', 70231, 'application/core'],
    [24, 'belong', '=', 60011, 'application/data'],
    [24, 'belong', '=', 60012, 'application/data'],
    [24, 'belong', '=', 60013, 'application/data'],
    [24, 'belong', '=', 60014, 'application/data'],
    [0, 'belong', '=', 601, 'application/x-object-file'],
    [0, 'belong', '=', 607, 'application/data'],
    [0, 'belong', '=', 324508366, 'application/x-gdbm'],
    [0, 'lelong', '=', 324508366, 'application/x-gdbm'],
    [0, 'string', '=', b'GDBM', 'application/x-gdbm'],
    [0, 'belong', '=', 398689, 'application/x-db'],
    [0, 'belong', '=', 340322, 'application/x-db'],
    [0, 'string', '=', b'<list>\012<protocol bbn-m', 'application/data'],
    [0, 'string', '=', b'diff text/x-patch', ''],
    [0, 'string', '=', b'*** text/x-patch', ''],
    [0, 'string', '=', b'Only in text/x-patch', ''],
    [0, 'string', '=', b'Common subdirectories: text/x-patch', ''],
    [0, 'string', '=', b'!<arch>\012________64E', 'application/data'],
    [0, 'leshort', '=', 387, 'application/x-executable-file'],
    [0, 'leshort', '=', 392, 'application/x-executable-file'],
    [0, 'leshort', '=', 399, 'application/x-object-file'],
    [0, 'string', '=', b'\377\377\177', 'application/data'],
    [0, 'string', '=', b'\377\377|', 'application/data'],
    [0, 'string', '=', b'\377\377~', 'application/data'],
    [0, 'string', '=', b'\033c\033', 'application/data'],
    [0, 'long', '=', 4553207, 'image/x11'],
    [0, 'string', '=', b'!<PDF>!\012', 'application/x-prof'],
    [0, 'short', '=', 1281, 'application/x-locale'],
    [24, 'belong', '=', 60012, 'application/x-dump'],
    [24, 'belong', '=', 60011, 'application/x-dump'],
    [24, 'lelong', '=', 60012, 'application/x-dump'],
    [24, 'lelong', '=', 60011, 'application/x-dump'],
    [0, 'string', '=', b'\177ELF', 'application/x-executable-file'],
    [0, 'short', '=', 340, 'application/data'],
    [0, 'short', '=', 341, 'application/x-executable-file'],
    [1080, 'leshort', '=', 61267, 'application/x-linux-ext2fs'],
    [0, 'string', '=', b'\366\366\366\366', 'application/x-pc-floppy'],
    [774, 'beshort', '=', 55998, 'application/data'],
    [510, 'leshort', '=', 43605, 'application/data'],
    [1040, 'leshort', '=', 4991, 'application/x-filesystem'],
    [1040, 'leshort', '=', 5007, 'application/x-filesystem'],
    [1040, 'leshort', '=', 9320, 'application/x-filesystem'],
    [1040, 'leshort', '=', 9336, 'application/x-filesystem'],
    [0, 'string', '=', b'-rom1fs-\000', 'application/x-filesystem'],
    [395, 'string', '=', 'OS/2', 'application/x-bootable'],
    [0, 'string', '=', b'FONT', 'font/x-vfont'],
    [0, 'short', '=', 436, 'font/x-vfont'],
    [0, 'short', '=', 17001, 'font/x-vfont'],
    [0, 'string', '=', b'%!PS-AdobeFont-1.0', 'font/type1'],
    [6, 'string', '=', '%!PS-AdobeFont-1.0', 'font/type1'],
    [0, 'belong', '=', 4, 'font/x-snf'],
    [0, 'lelong', '=', 4, 'font/x-snf'],
    [0, 'string', '=', b'STARTFONT font/x-bdf', ''],
    [0, 'string', '=', b'\001fcp', 'font/x-pcf'],
    [0, 'string', '=', b'D1.0\015', 'font/x-speedo'],
    [0, 'string', '=', b'flf', 'font/x-figlet'],
    [0, 'string', '=', b'flc', 'application/x-font'],
    [0, 'belong', '=', 335698201, 'font/x-libgrx'],
    [0, 'belong', '=', 4282797902, 'font/x-dos'],
    [7, 'belong', '=', 4540225, 'font/x-dos'],
    [7, 'belong', '=', 5654852, 'font/x-dos'],
    [4098, 'string', '=', 'DOSFONT', 'font/x-dos'],
    [0, 'string', '=', b'<MakerFile', 'application/x-framemaker'],
    [0, 'string', '=', b'<MIFFile', 'application/x-framemaker'],
    [0, 'string', '=', b'<MakerDictionary', 'application/x-framemaker'],
    [0, 'string', '=', b'<MakerScreenFont', 'font/x-framemaker'],
    [0, 'string', '=', b'<MML', 'application/x-framemaker'],
    [0, 'string', '=', b'<BookFile', 'application/x-framemaker'],
    [0, 'string', '=', b'<Maker', 'application/x-framemaker'],
    [0, 'lelong&0377777777', '=', 41400407,
     'application/x-executable-file'],
    [0, 'lelong&0377777777', '=', 41400410,
     'application/x-executable-file'],
    [0, 'lelong&0377777777', '=', 41400413,
     'application/x-executable-file'],
    [0, 'lelong&0377777777', '=', 41400314,
     'application/x-executable-file'],
    [7, 'string', '=',
     '\357\020\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000',
     'application/core'],
    [0, 'lelong', '=', 11421044151, 'application/data'],
    [0, 'string', '=', b'GIMP Gradient', 'application/x-gimp-gradient'],
    [0, 'string', '=', b'gimp xcf', 'application/x-gimp-image'],
    [20, 'string', '=', b'GPAT', 'application/x-gimp-pattern'],
    [20, 'string', '=', b'GIMP', 'application/x-gimp-brush'],
    [0, 'string', '=', b'\336\022\004\225', 'application/x-locale'],
    [0, 'string', '=', b'\225\004\022\336', 'application/x-locale'],
    [0, 'beshort', '=', 627, 'application/x-executable-file'],
    [0, 'beshort', '=', 624, 'application/x-executable-file'],
    [0, 'string', '=', b'\000\001\000\000\000', 'font/ttf'],
    [0, 'long', '=', 1203604016, 'application/data'],
    [0, 'long', '=', 1702407010, 'application/data'],
    [0, 'long', '=', 1003405017, 'application/data'],
    [0, 'long', '=', 1602007412, 'application/data'],
    [0, 'belong', '=', 34603270, 'application/x-object-file'],
    [0, 'belong', '=', 34603271, 'application/x-executable-file'],
    [0, 'belong', '=', 34603272, 'application/x-executable-file'],
    [0, 'belong', '=', 34603275, 'application/x-executable-file'],
    [0, 'belong', '=', 34603278, 'application/x-library-file'],
    [0, 'belong', '=', 34603277, 'application/x-library-file'],
    [0, 'belong', '=', 34865414, 'application/x-object-file'],
    [0, 'belong', '=', 34865415, 'application/x-executable-file'],
    [0, 'belong', '=', 34865416, 'application/x-executable-file'],
    [0, 'belong', '=', 34865419, 'application/x-executable-file'],
    [0, 'belong', '=', 34865422, 'application/x-library-file'],
    [0, 'belong', '=', 34865421, 'application/x-object-file'],
    [0, 'belong', '=', 34275590, 'application/x-object-file'],
    [0, 'belong', '=', 34275591, 'application/x-executable-file'],
    [0, 'belong', '=', 34275592, 'application/x-executable-file'],
    [0, 'belong', '=', 34275595, 'application/x-executable-file'],
    [0, 'belong', '=', 34275598, 'application/x-library-file'],
    [0, 'belong', '=', 34275597, 'application/x-library-file'],
    [0, 'belong', '=', 557605234, 'application/x-ar'],
    [0, 'long', '=', 34078982, 'application/x-executable-file'],
    [0, 'long', '=', 34078983, 'application/x-executable-file'],
    [0, 'long', '=', 34078984, 'application/x-executable-file'],
    [0, 'belong', '=', 34341128, 'application/x-executable-file'],
    [0, 'belong', '=', 34341127, 'application/x-executable-file'],
    [0, 'belong', '=', 34341131, 'application/x-executable-file'],
    [0, 'belong', '=', 34341126, 'application/x-executable-file'],
    [0, 'belong', '=', 34210056, 'application/x-executable-file'],
    [0, 'belong', '=', 34210055, 'application/x-executable-file'],
    [0, 'belong', '=', 34341134, 'application/x-library-file'],
    [0, 'belong', '=', 34341133, 'application/x-library-file'],
    [0, 'long', '=', 65381, 'application/x-library-file'],
    [0, 'long', '=', 34275173, 'application/x-library-file'],
    [0, 'long', '=', 34406245, 'application/x-library-file'],
    [0, 'long', '=', 34144101, 'application/x-library-file'],
    [0, 'long', '=', 22552998, 'application/core'],
    [0, 'long', '=', 1302851304, 'font/x-hp-windows'],
    [0, 'string', '=', b'Bitmapfile', 'image/unknown'],
    [0, 'string', '=', b'IMGfile', 'CIS image/unknown'],
    [0, 'long', '=', 34341132, 'application/x-lisp'],
    [0, 'string', '=', b'msgcat01', 'application/x-locale'],
    [0, 'string', '=', b'HPHP48-', 'HP48 binary'],
    [0, 'string', '=', b'%%HP:', 'HP48 text'],
    [0, 'beshort', '=', 200, 'hp200 (68010) BSD'],
    [0, 'beshort', '=', 300, 'hp300 (68020+68881) BSD'],
    [0, 'beshort', '=', 537, '370 XA sysV executable'],
    [0, 'beshort', '=', 532, '370 XA sysV pure executable'],
    [0, 'beshort', '=', 54001, '370 sysV pure executable'],
    [0, 'beshort', '=', 55001, '370 XA sysV pure executable'],
    [0, 'beshort', '=', 56401, '370 sysV executable'],
    [0, 'beshort', '=', 57401, '370 XA sysV executable'],
    [0, 'beshort', '=', 531, 'SVR2 executable (Amdahl-UTS)'],
    [0, 'beshort', '=', 534, 'SVR2 pure executable (Amdahl-UTS)'],
    [0, 'beshort', '=', 530, 'SVR2 pure executable (USS/370)'],
    [0, 'beshort', '=', 535, 'SVR2 executable (USS/370)'],
    [0, 'beshort', '=', 479, 'executable (RISC System/6000 V3.1) or obj module'],
    [0, 'beshort', '=', 260, 'shared library'],
    [0, 'beshort', '=', 261, 'ctab data'],
    [0, 'beshort', '=', 65028, 'structured file'],
    [0, 'string', '=', b'0xabcdef', 'AIX message catalog'],
    [0, 'belong', '=', 505, 'AIX compiled message catalog'],
    [0, 'string', '=', b'<aiaff>', 'archive'],
    [0, 'string', '=', b'FORM', 'IFF data'],
    [0, 'string', '=', b'P1', 'image/x-portable-bitmap'],
    [0, 'string', '=', b'P2', 'image/x-portable-graymap'],
    [0, 'string', '=', b'P3', 'image/x-portable-pixmap'],
    [0, 'string', '=', b'P4', 'image/x-portable-bitmap'],
    [0, 'string', '=', b'P5', 'image/x-portable-graymap'],
    [0, 'string', '=', b'P6', 'image/x-portable-pixmap'],
    [0, 'string', '=', b'IIN1', 'image/tiff'],
    [0, 'string', '=', b'MM\000*', 'image/tiff'],
    [0, 'string', '=', b'II*\000', 'image/tiff'],
    [0, 'string', '=', b'\211PNG', 'image/png'],
    [1, 'string', '=', 'PNG', 'image/png'],
    [0, 'string', '=', b'GIF8', 'image/gif'],
    [0, 'string', '=', b'\361\000@\273', 'image/x-cmu-raster'],
    [0, 'string', '=', b'id=ImageMagick', 'MIFF image data'],
    [0, 'long', '=', 1123028772, 'Artisan image data'],
    [0, 'string', '=', b'#FIG', 'FIG image text'],
    [0, 'string', '=', b'ARF_BEGARF', 'PHIGS clear text archive'],
    [0, 'string', '=', b'@(#)SunPHIGS', 'SunPHIGS'],
    [0, 'string', '=', b'GKSM', 'GKS Metafile'],
    [0, 'string', '=', b'BEGMF', 'clear text Computer Graphics Metafile'],
    [0, 'beshort&0xffe0', '=', 32, 'binary Computer Graphics Metafile'],
    [0, 'beshort', '=', 12320, 'character Computer Graphics Metafile'],
    [0, 'string', '=', b'yz', 'MGR bitmap, modern format, 8-bit aligned'],
    [0, 'string', '=', b'zz','MGR bitmap, old format, 1-bit deep, 16-bit aligned'],
    [0, 'string', '=', b'xz','MGR bitmap, old format, 1-bit deep, 32-bit aligned'],
    [0, 'string', '=', b'yx', 'MGR bitmap, modern format, squeezed'],
    [0, 'string', '=', b'%bitmap\000', 'FBM image data'],
    [1, 'string', '=', 'PC Research, Inc', 'group 3 fax data'],
    [0, 'string', '=', b'hplip_g3', 'application/hplip-fax'],
    [0, 'beshort', '=', 65496, 'image/jpeg'],
    [0, 'string', '=', b'hsi1', 'image/x-jpeg-proprietary'],
    [0, 'string', '=', b'BM', 'image/x-bmp'],
    [0, 'string', '=', b'IC', 'image/x-ico'],
    [0, 'string', '=', b'PI', 'PC pointer image data'],
    [0, 'string', '=', b'CI', 'PC color icon data'],
    [0, 'string', '=', b'CP', 'PC color pointer image data'],
    [0, 'string', '=', b'/* XPM */', 'image/x-xpixmap'],
    [0, 'leshort', '=', 52306, 'RLE image data,'],
    [0, 'string', '=', b'Imagefile version-', 'iff image data'],
    [0, 'belong', '=', 1504078485, 'image/x-sun-raster'],
    [0, 'beshort', '=', 474, 'x/x-image-sgi'],
    [0, 'string', '=', b'IT01', 'FIT image data'],
    [0, 'string', '=', b'IT02', 'FIT image data'],
    [2048, 'string', '=', 'PCD_IPI', 'x/x-photo-cd-pack-file'],
    [0, 'string', '=', b'PCD_OPA', 'x/x-photo-cd-overfiew-file'],
    [0, 'string', '=', b'SIMPLE  =', 'FITS image data'],
    [0, 'string', '=', b'This is a BitMap file', 'Lisp Machine bit-array-file'],
    [0, 'string', '=', b'!!', 'Bennet Yee\'s "face" format'],
    [0, 'beshort', '=', 4112, 'PEX Binary Archive'],
    [3000, 'string', '=', b'Visio (TM) Drawing', '%s'],
    [0, 'leshort', '=', 502, 'basic-16 executable'],
    [0, 'leshort', '=', 503, 'basic-16 executable (TV)'],
    [0, 'leshort', '=', 510, 'application/x-executable-file'],
    [0, 'leshort', '=', 511, 'application/x-executable-file'],
    [0, 'leshort', '=', 512, 'application/x-executable-file'],
    [0, 'leshort', '=', 522, 'application/x-executable-file'],
    [0, 'leshort', '=', 514, 'application/x-executable-file'],
    [0, 'string', '=', b'\210OPS', 'Interleaf saved data'],
    [0, 'string', '=', b'<!OPS', 'Interleaf document text'],
    [4, 'string', '=', 'pgscriptver', 'IslandWrite document'],
    [13, 'string', '=', 'DrawFile', 'IslandDraw document'],
    [0, 'leshort&0xFFFC', '=', 38400, 'little endian ispell'],
    [0, 'beshort&0xFFFC', '=', 38400, 'big endian ispell'],
    [0, 'belong', '=', 3405691582, 'compiled Java class data,'],
    [0, 'beshort', '=', 44269, 'Java serialization data'],
    [0, 'string', '=', b'KarmaRHD', 'Version Karma Data Structure Version'],
    [0, 'string', '=', b'lect', 'DEC SRC Virtual Paper Lectern file'],
    [53, 'string', '=', 'yyprevious', 'C program text (from lex)'],
    [21, 'string', '=', 'generated by flex', 'C program text (from flex)'],
    [0, 'string', '=', b'%{', 'lex description text'],
    [0, 'short', '=', 32768, 'lif file'],
    [0, 'lelong', '=', 6553863, 'Linux/i386 impure executable (OMAGIC)'],
    [0, 'lelong', '=', 6553864, 'Linux/i386 pure executable (NMAGIC)'],
    [0, 'lelong', '=', 6553867, 'Linux/i386 demand-paged executable (ZMAGIC)'],
    [0, 'lelong', '=', 6553804, 'Linux/i386 demand-paged executable (QMAGIC)'],
    [0, 'string', '=', b'\007\001\000', 'Linux/i386 object file'],
    [0, 'string', '=', b'\001\003\020\004', 'Linux-8086 impure executable'],
    [0, 'string', '=', b'\001\003 \004', 'Linux-8086 executable'],
    [0, 'string', '=', b'\243\206\001\000', 'Linux-8086 object file'],
    [0, 'string', '=', b'\001\003\020\020', 'Minix-386 impure executable'],
    [0, 'string', '=', b'\001\003 \020', 'Minix-386 executable'],
    [0, 'string', '=', b'*nazgul*', 'Linux compiled message catalog'],
    [216, 'lelong', '=', 421, 'Linux/i386 core file'],
    [2, 'string', '=', 'LILO', 'Linux/i386 LILO boot/chain loader'],
    [0, 'string', '=', b'0.9', ''],
    [0, 'leshort', '=', 1078, 'font/linux-psf'],
    [4086, 'string', '=', 'SWAP-SPACE', 'Linux/i386 swap file'],
    [0, 'leshort', '=', 387, 'ECOFF alpha'],
    [514, 'string', '=', 'HdrS', 'Linux kernel'],
    [0, 'belong', '=', 3099592590, 'Linux kernel'],
    [0, 'string', '=', b'Begin3', 'Linux Software Map entry text'],
    [0, 'string', '=', b';;', 'Lisp/Scheme program text'],
    [0, 'string', '=', b'\012(', 'byte-compiled Emacs-Lisp program data'],
    [0, 'string', '=', b';ELC\023\000\000\000', 'byte-compiled Emacs-Lisp program data'],
    [0, 'string', '=', "(SYSTEM::VERSION '", 'CLISP byte-compiled Lisp program text'],
    [0, 'long', '=', 1886817234, 'CLISP memory image data'],
    [0, 'long', '=', 3532355184, 'CLISP memory image data, other endian'],
    [0, 'long', '=', 3725722773, 'GNU-format message catalog data'],
    [0, 'long', '=', 2500072158, 'GNU-format message catalog data'],
    [0, 'belong', '=', 3405691582, 'mach-o fat file'],
    [0, 'belong', '=', 4277009102, 'mach-o'],
    [11, 'string', '=', 'must be converted with BinHex', 'BinHex binary text'],
    [0, 'string', '=', b'SIT!', 'StuffIt Archive (data)'],
    [65, 'string', '=', 'SIT!', 'StuffIt Archive (rsrc + data)'],
    [0, 'string', '=', b'SITD', 'StuffIt Deluxe (data)'],
    [65, 'string', '=', 'SITD', 'StuffIt Deluxe (rsrc + data)'],
    [0, 'string', '=', b'Seg', 'StuffIt Deluxe Segment (data)'],
    [65, 'string', '=', 'Seg', 'StuffIt Deluxe Segment (rsrc + data)'],
    [0, 'string', '=', b'APPL', 'Macintosh Application (data)'],
    [65, 'string', '=', 'APPL', 'Macintosh Application (rsrc + data)'],
    [0, 'string', '=', b'zsys', 'Macintosh System File (data)'],
    [65, 'string', '=', 'zsys', 'Macintosh System File(rsrc + data)'],
    [0, 'string', '=', b'FNDR', 'Macintosh Finder (data)'],
    [65, 'string', '=', 'FNDR', 'Macintosh Finder(rsrc + data)'],
    [0, 'string', '=', b'libr', 'Macintosh Library (data)'],
    [65, 'string', '=', 'libr', 'Macintosh Library(rsrc + data)'],
    [0, 'string', '=', b'shlb', 'Macintosh Shared Library (data)'],
    [65, 'string', '=', 'shlb', 'Macintosh Shared Library(rsrc + data)'],
    [0, 'string', '=', b'cdev', 'Macintosh Control Panel (data)'],
    [65, 'string', '=', 'cdev', 'Macintosh Control Panel(rsrc + data)'],
    [0, 'string', '=', b'INIT', 'Macintosh Extension (data)'],
    [65, 'string', '=', 'INIT', 'Macintosh Extension(rsrc + data)'],
    [0, 'string', '=', b'FFIL', 'font/ttf'],
    [65, 'string', '=', 'FFIL', 'font/ttf'],
    [0, 'string', '=', b'LWFN', 'font/type1'],
    [65, 'string', '=', 'LWFN', 'font/type1'],
    [0, 'string', '=', b'PACT', 'Macintosh Compact Pro Archive (data)'],
    [65, 'string', '=', 'PACT', 'Macintosh Compact Pro Archive(rsrc + data)'],
    [0, 'string', '=', b'ttro', 'Macintosh TeachText File (data)'],
    [65, 'string', '=', 'ttro', 'Macintosh TeachText File(rsrc + data)'],
    [0, 'string', '=', b'TEXT', 'Macintosh TeachText File (data)'],
    [65, 'string', '=', 'TEXT', 'Macintosh TeachText File(rsrc + data)'],
    [0, 'string', '=', b'PDF', 'Macintosh PDF File (data)'],
    [65, 'string', '=', 'PDF', 'Macintosh PDF File(rsrc + data)'],
    [0, 'string', '=', b'# Magic', 'magic text file for file(1) cmd'],
    [0, 'string', '=', b'Relay-Version:', 'old news text'],
    [0, 'string', '=', b'#! rnews', 'batched news text'],
    [0, 'string', '=', b'N#! rnews', 'mailed, batched news text'],
    [0, 'string', '=', b'Forward to', 'mail forwarding text'],
    [0, 'string', '=', b'Pipe to', 'mail piping text'],
    [0, 'string', '=', b'Return-Path:', 'message/rfc822'],
    [0, 'string', '=', b'Path:', 'message/news'],
    [0, 'string', '=', b'Xref:', 'message/news'],
    [0, 'string', '=', b'From:', 'message/rfc822'],
    [0, 'string', '=', b'Article', 'message/news'],
    [0, 'string', '=', b'BABYL', 'message/x-gnu-rmail'],
    [0, 'string', '=', b'Received:', 'message/rfc822'],
    [0, 'string', '=', b'MIME-Version:', 'MIME entity text'],
    [0, 'string', '=', b'Content-Type: ', ''],
    [0, 'string', '=', b'Content-Type:', ''],
    [0, 'long', '=', 31415, 'Mirage Assembler m.out executable'],
    [0, 'string', '=', b'\311\304', 'ID tags data'],
    [0, 'string', '=', b'\001\001\001\001', 'MMDF mailbox'],
    [4, 'string', '=', 'Research,', 'Digifax-G3-File'],
    [0, 'short', '=', 256, 'raw G3 data, byte-padded'],
    [0, 'short', '=', 5120, 'raw G3 data'],
    [0, 'string', '=', b'RMD1', 'raw modem data'],
    [0, 'string', '=', b'PVF1\012', 'portable voice format'],
    [0, 'string', '=', b'PVF2\012', 'portable voice format'],
    [0, 'beshort', '=', 520, 'mc68k COFF'],
    [0, 'beshort', '=', 521, 'mc68k executable (shared)'],
    [0, 'beshort', '=', 522, 'mc68k executable (shared demand paged)'],
    [0, 'beshort', '=', 554, '68K BCS executable'],
    [0, 'beshort', '=', 555, '88K BCS executable'],
    [0, 'string', '=', b'S0', 'Motorola S-Record; binary data in text format'],
    [0, 'string', '=', b'@echo off', 'MS-DOS batch file text'],
    [128, 'string', '=', 'PE\000\000', 'MS Windows PE'],
    [0, 'leshort', '=', 332, 'MS Windows COFF Intel 80386 object file'],
    [0, 'leshort', '=', 358, 'MS Windows COFF MIPS R4000 object file'],
    [0, 'leshort', '=', 388, 'MS Windows COFF Alpha object file'],
    [0, 'leshort', '=', 616, 'MS Windows COFF Motorola 68000 object file'],
    [0, 'leshort', '=', 496, 'MS Windows COFF PowerPC object file'],
    [0, 'leshort', '=', 656, 'MS Windows COFF PA-RISC object file'],
    [0, 'string', '=', b'MZ', 'application/x-ms-dos-executable'],
    [0, 'string', '=', b'LZ', 'MS-DOS executable (built-in)'],
    [0, 'string', '=', b'regf', 'Windows NT Registry file'],
    [2080, 'string', '=', b'Microsoft Word 6.0 Document', 'text/vnd.ms-word'],
    [2080, 'string', '=', b'Documento Microsoft Word 6', 'text/vnd.ms-word'],
    [2112, 'string', '=', 'MSWordDoc', 'text/vnd.ms-word'],
    [0, 'belong', '=', 834535424, 'text/vnd.ms-word'],
    [0, 'string', '=', b'PO^Q`', 'text/vnd.ms-word'],
    [2080, 'string', '=', b'Microsoft Excel 5.0 Worksheet', 'application/vnd.ms-excel'],
    [2114, 'string', '=', 'Biff5', 'application/vnd.ms-excel'],
    [0, 'belong', '=', 6656, 'Lotus 1-2-3'],
    [0, 'belong', '=', 512, 'Lotus 1-2-3'],
    [1, 'string', '=', 'WPC', 'text/vnd.wordperfect'],
    [0, 'beshort', '=', 610, 'Tower/XP rel 2 object'],
    [0, 'beshort', '=', 615, 'Tower/XP rel 2 object'],
    [0, 'beshort', '=', 620, 'Tower/XP rel 3 object'],
    [0, 'beshort', '=', 625, 'Tower/XP rel 3 object'],
    [0, 'beshort', '=', 630, 'Tower32/600/400 68020 object'],
    [0, 'beshort', '=', 640, 'Tower32/800 68020'],
    [0, 'beshort', '=', 645, 'Tower32/800 68010'],
    [0, 'lelong', '=', 407, 'NetBSD little-endian object file'],
    [0, 'belong', '=', 407, 'NetBSD big-endian object file'],
    [0, 'belong&0377777777', '=', 41400413, 'NetBSD/i386 demand paged'],
    [0, 'belong&0377777777', '=', 41400410, 'NetBSD/i386 pure'],
    [0, 'belong&0377777777', '=', 41400407, 'NetBSD/i386'],
    [0, 'belong&0377777777', '=', 41400507, 'NetBSD/i386 core'],
    [0, 'belong&0377777777', '=', 41600413, 'NetBSD/m68k demand paged'],
    [0, 'belong&0377777777', '=', 41600410, 'NetBSD/m68k pure'],
    [0, 'belong&0377777777', '=', 41600407, 'NetBSD/m68k'],
    [0, 'belong&0377777777', '=', 41600507, 'NetBSD/m68k core'],
    [0, 'belong&0377777777', '=', 42000413, 'NetBSD/m68k4k demand paged'],
    [0, 'belong&0377777777', '=', 42000410, 'NetBSD/m68k4k pure'],
    [0, 'belong&0377777777', '=', 42000407, 'NetBSD/m68k4k'],
    [0, 'belong&0377777777', '=', 42000507, 'NetBSD/m68k4k core'],
    [0, 'belong&0377777777', '=', 42200413, 'NetBSD/ns32532 demand paged'],
    [0, 'belong&0377777777', '=', 42200410, 'NetBSD/ns32532 pure'],
    [0, 'belong&0377777777', '=', 42200407, 'NetBSD/ns32532'],
    [0, 'belong&0377777777', '=', 42200507, 'NetBSD/ns32532 core'],
    [0, 'belong&0377777777', '=', 42400413, 'NetBSD/sparc demand paged'],
    [0, 'belong&0377777777', '=', 42400410, 'NetBSD/sparc pure'],
    [0, 'belong&0377777777', '=', 42400407, 'NetBSD/sparc'],
    [0, 'belong&0377777777', '=', 42400507, 'NetBSD/sparc core'],
    [0, 'belong&0377777777', '=', 42600413, 'NetBSD/pmax demand paged'],
    [0, 'belong&0377777777', '=', 42600410, 'NetBSD/pmax pure'],
    [0, 'belong&0377777777', '=', 42600407, 'NetBSD/pmax'],
    [0, 'belong&0377777777', '=', 42600507, 'NetBSD/pmax core'],
    [0, 'belong&0377777777', '=', 43000413, 'NetBSD/vax demand paged'],
    [0, 'belong&0377777777', '=', 43000410, 'NetBSD/vax pure'],
    [0, 'belong&0377777777', '=', 43000407, 'NetBSD/vax'],
    [0, 'belong&0377777777', '=', 43000507, 'NetBSD/vax core'],
    [0, 'lelong', '=', 459141, 'ECOFF NetBSD/alpha binary'],
    [0, 'belong&0377777777', '=', 43200507, 'NetBSD/alpha core'],
    [0, 'belong&0377777777', '=', 43400413, 'NetBSD/mips demand paged'],
    [0, 'belong&0377777777', '=', 43400410, 'NetBSD/mips pure'],
    [0, 'belong&0377777777', '=', 43400407, 'NetBSD/mips'],
    [0, 'belong&0377777777', '=', 43400507, 'NetBSD/mips core'],
    [0, 'belong&0377777777', '=', 43600413, 'NetBSD/arm32 demand paged'],
    [0, 'belong&0377777777', '=', 43600410, 'NetBSD/arm32 pure'],
    [0, 'belong&0377777777', '=', 43600407, 'NetBSD/arm32'],
    [0, 'belong&0377777777', '=', 43600507, 'NetBSD/arm32 core'],
    [0, 'string', '=', b'StartFontMetrics', 'font/x-sunos-news'],
    [0, 'string', '=', b'StartFont', 'font/x-sunos-news'],
    [0, 'belong', '=', 326773060, 'font/x-sunos-news'],
    [0, 'belong', '=', 326773063, 'font/x-sunos-news'],
    [0, 'belong', '=', 326773072, 'font/x-sunos-news'],
    [0, 'belong', '=', 326773073, 'font/x-sunos-news'],
    [8, 'belong', '=', 326773573, 'font/x-sunos-news'],
    [8, 'belong', '=', 326773576, 'font/x-sunos-news'],
    [0, 'string', '=', b'Octave-1-L', 'Octave binary data (little endian)'],
    [0, 'string', '=', b'Octave-1-B', 'Octave binary data (big endian)'],
    [0, 'string', '=', b'\177OLF', 'OLF'],
    [0, 'beshort', '=', 34765, 'OS9/6809 module:'],
    [0, 'beshort', '=', 19196, 'OS9/68K module:'],
    [0, 'long', '=', 61374, 'OSF/Rose object'],
    [0, 'short', '=', 565, 'i386 COFF object'],
    [0, 'short', '=', 10775, '"compact bitmap" format (Poskanzer)'],
    [0, 'string', '=', b'%PDF-', 'application/pdf'],
    [0, 'lelong', '=', 101555, 'PDP-11 single precision APL workspace'],
    [0, 'lelong', '=', 101554, 'PDP-11 double precision APL workspace'],
    [0, 'leshort', '=', 407, 'PDP-11 executable'],
    [0, 'leshort', '=', 401, 'PDP-11 UNIX/RT ldp'],
    [0, 'leshort', '=', 405, 'PDP-11 old overlay'],
    [0, 'leshort', '=', 410, 'PDP-11 pure executable'],
    [0, 'leshort', '=', 411, 'PDP-11 separate I&D executable'],
    [0, 'leshort', '=', 437, 'PDP-11 kernel overlay'],
    [0, 'beshort', '=', 39168, 'PGP key public ring'],
    [0, 'beshort', '=', 38145, 'PGP key security ring'],
    [0, 'beshort', '=', 38144, 'PGP key security ring'],
    [0, 'beshort', '=', 42496, 'PGP encrypted data'],
    [0, 'string', '=', b'-----BEGIN PGP', 'PGP armored data'],
    [0, 'string', '=', b'# PaCkAgE DaTaStReAm', 'pkg Datastream (SVR4)'],
    [0, 'short', '=', 601, 'mumps avl global'],
    [0, 'short', '=', 602, 'mumps blt global'],
    [0, 'string', '=', b'%!', 'application/postscript'],
    [0, 'string', '=', b'\004%!', 'application/postscript'],
    [0, 'belong', '=', 3318797254, 'DOS EPS Binary File'],
    [0, 'string', '=', b'*PPD-Adobe:', 'application/pdf'],
    [0, 'string', '=', b'\033%-12345X@PJL', 'HP Printer Job Language data'],
    [0, 'string', '=', b'\033%-12345X@PJL', 'HP Printer Job Language data'],
    [0, 'string', '=', b'\033E\033', 'image/x-pcl-hp'],
    [0, 'string', '=', b'@document(', 'Imagen printer'],
    [0, 'string', '=', b'Rast', 'RST-format raster font data'],
    [0, 'belong&0xff00ffff', '=', 1442840576, 'ps database'],
    [0, 'long', '=', 1351614727, 'Pyramid 90x family executable'],
    [0, 'long', '=', 1351614728, 'Pyramid 90x family pure executable'],
    [0, 'long', '=', 1351614731, 'Pyramid 90x family demand paged pure executable'],
    [0, 'beshort', '=', 60843, ''],
    [0, 'string', '=', b'{\\\\rtf', 'Rich Text Format data,'],
    [38, 'string', '=', 'Spreadsheet', 'sc spreadsheet file'],
    [8, 'string', '=', '\001s SCCS', 'archive data'],
    [0, 'byte', '=', 46, 'Sendmail frozen configuration'],
    [0, 'short', '=', 10012, 'Sendmail frozen configuration'],
    [0, 'lelong', '=', 234, 'BALANCE NS32000 .o'],
    [0, 'lelong', '=', 4330, 'BALANCE NS32000 executable (0 @ 0)'],
    [0, 'lelong', '=', 8426, 'BALANCE NS32000 executable (invalid @ 0)'],
    [0, 'lelong', '=', 12522, 'BALANCE NS32000 standalone executable'],
    [0, 'leshort', '=', 4843, 'SYMMETRY i386 .o'],
    [0, 'leshort', '=', 8939, 'SYMMETRY i386 executable (0 @ 0)'],
    [0, 'leshort', '=', 13035, 'SYMMETRY i386 executable (invalid @ 0)'],
    [0, 'leshort', '=', 17131, 'SYMMETRY i386 standalone executable'],
    [0, 'string', '=', b'kbd!map', 'kbd map file'],
    [0, 'belong', '=', 407, 'old SGI 68020 executable'],
    [0, 'belong', '=', 410, 'old SGI 68020 pure executable'],
    [0, 'beshort', '=', 34661, 'disk quotas file'],
    [0, 'beshort', '=', 1286, 'IRIS Showcase file'],
    [0, 'beshort', '=', 550, 'IRIS Showcase template'],
    [0, 'belong', '=', 1396917837, 'IRIS Showcase file'],
    [0, 'belong', '=', 1413695053, 'IRIS Showcase template'],
    [0, 'belong', '=', 3735927486, 'IRIX Parallel Arena'],
    [0, 'beshort', '=', 352, 'MIPSEB COFF executable'],
    [0, 'beshort', '=', 354, 'MIPSEL COFF executable'],
    [0, 'beshort', '=', 24577, 'MIPSEB-LE COFF executable'],
    [0, 'beshort', '=', 25089, 'MIPSEL-LE COFF executable'],
    [0, 'beshort', '=', 355, 'MIPSEB MIPS-II COFF executable'],
    [0, 'beshort', '=', 358, 'MIPSEL MIPS-II COFF executable'],
    [0, 'beshort', '=', 25345, 'MIPSEB-LE MIPS-II COFF executable'],
    [0, 'beshort', '=', 26113, 'MIPSEL-LE MIPS-II COFF executable'],
    [0, 'beshort', '=', 320, 'MIPSEB MIPS-III COFF executable'],
    [0, 'beshort', '=', 322, 'MIPSEL MIPS-III COFF executable'],
    [0, 'beshort', '=', 16385, 'MIPSEB-LE MIPS-III COFF executable'],
    [0, 'beshort', '=', 16897, 'MIPSEL-LE MIPS-III COFF executable'],
    [0, 'beshort', '=', 384, 'MIPSEB Ucode'],
    [0, 'beshort', '=', 386, 'MIPSEL Ucode'],
    [0, 'belong', '=', 3735924144, 'IRIX core dump'],
    [0, 'belong', '=', 3735924032, 'IRIX 64-bit core dump'],
    [0, 'belong', '=', 3133063355, 'IRIX N32 core dump'],
    [0, 'string', '=', b'CrshDump', 'IRIX vmcore dump of'],
    [0, 'string', '=', b'SGIAUDIT', 'SGI Audit file'],
    [0, 'string', '=', b'WNGZWZSC', 'Wingz compiled script'],
    [0, 'string', '=', b'WNGZWZSS', 'Wingz spreadsheet'],
    [0, 'string', '=', b'WNGZWZHP', 'Wingz help file'],
    [0, 'string', '=', b'\\#Inventor', 'V IRIS Inventor 1.0 file'],
    [0, 'string', '=', b'\\#Inventor', 'V2 Open Inventor 2.0 file'],
    [0, 'string', '=', b'glfHeadMagic();', 'GLF_TEXT'],
    [4, 'belong', '=', 1090584576, 'GLF_BINARY_LSB_FIRST'],
    [4, 'belong', '=', 321, 'GLF_BINARY_MSB_FIRST'],
    [0, 'string', '=', b'<!DOCTYPE HTML', 'text/html'],
    [0, 'string', '=', b'<!doctype html', 'text/html'],
    [0, 'string', '=', b'<HEAD', 'text/html'],
    [0, 'string', '=', b'<head', 'text/html'],
    [0, 'string', '=', b'<TITLE', 'text/html'],
    [0, 'string', '=', b'<title', 'text/html'],
    [0, 'string', '=', b'<html', 'text/html'],
    [0, 'string', '=', b'<HTML', 'text/html'],
    [0, 'string', '=', b'<!DOCTYPE', 'exported SGML document text'],
    [0, 'string', '=', b'<!doctype', 'exported SGML document text'],
    [0, 'string', '=', b'<!SUBDOC', 'exported SGML subdocument text'],
    [0, 'string', '=', b'<!subdoc', 'exported SGML subdocument text'],
    [0, 'string', '=', b'<!--', 'exported SGML document text'],
    [0, 'string', '=', b'RTSS', 'NetMon capture file'],
    [0, 'string', '=', b'TRSNIFF data    \032', 'Sniffer capture file'],
    [0, 'string', '=', b'XCP\000', 'NetXRay capture file'],
    [0, 'ubelong', '=', 2712847316, 'tcpdump capture file (big-endian)'],
    [0, 'ulelong', '=', 2712847316, 'tcpdump capture file (little-endian)'],
    [0, 'string', '=', b'<!SQ DTD>', 'Compiled SGML rules file'],
    [0, 'string', '=', b'<!SQ A/E>', 'A/E SGML Document binary'],
    [0, 'string', '=', b'<!SQ STS>', 'A/E SGML binary styles file'],
    [0, 'short', '=', 49374, 'Compiled PSI (v1) data'],
    [0, 'short', '=', 49370, 'Compiled PSI (v2) data'],
    [0, 'short', '=', 125252, 'SoftQuad DESC or font file binary'],
    [0, 'string', '=', b'SQ BITMAP1', 'SoftQuad Raster Format text'],
    [0, 'string', '=', b'X SoftQuad', 'troff Context intermediate'],
    [0, 'belong&077777777', '=', 600413, 'sparc demand paged'],
    [0, 'belong&077777777', '=', 600410, 'sparc pure'],
    [0, 'belong&077777777', '=', 600407, 'sparc'],
    [0, 'belong&077777777', '=', 400413, 'mc68020 demand paged'],
    [0, 'belong&077777777', '=', 400410, 'mc68020 pure'],
    [0, 'belong&077777777', '=', 400407, 'mc68020'],
    [0, 'belong&077777777', '=', 200413, 'mc68010 demand paged'],
    [0, 'belong&077777777', '=', 200410, 'mc68010 pure'],
    [0, 'belong&077777777', '=', 200407, 'mc68010'],
    [0, 'belong', '=', 407, 'old sun-2 executable'],
    [0, 'belong', '=', 410, 'old sun-2 pure executable'],
    [0, 'belong', '=', 413, 'old sun-2 demand paged executable'],
    [0, 'belong', '=', 525398, 'SunOS core file'],
    [0, 'long', '=', 4197695630, 'SunPC 4.0 Hard Disk'],
    [0, 'string', '=', b'#SUNPC_CONFIG', 'SunPC 4.0 Properties Values'],
    [0, 'string', '=', b'snoop', 'Snoop capture file'],
    [36, 'string', '=', 'acsp', 'Kodak Color Management System, ICC Profile'],
    [0, 'string', '=', b'#!teapot\012xdr', 'teapot work sheet (XDR format)'],
    [0, 'string', '=', b'\032\001', 'Compiled terminfo entry'],
    [0, 'short', '=', 433, 'Curses screen image'],
    [0, 'short', '=', 434, 'Curses screen image'],
    [0, 'string', '=', b'\367\002', 'TeX DVI file'],
    [0, 'string', '=', b'\367\203', 'font/x-tex'],
    [0, 'string', '=', b'\367Y', 'font/x-tex'],
    [0, 'string', '=', b'\367\312', 'font/x-tex'],
    [0, 'string', '=', b'This is TeX,', 'TeX transcript text'],
    [0, 'string', '=', b'This is METAFONT,', 'METAFONT transcript text'],
    [2, 'string', '=', '\000\021', 'font/x-tex-tfm'],
    [2, 'string', '=', '\000\022', 'font/x-tex-tfm'],
    [0, 'string', '=', b'\\\\input\\', 'texinfo Texinfo source text'],
    [0, 'string', '=', b'This is Info file', 'GNU Info text'],
    [0, 'string', '=', b'\\\\input', 'TeX document text'],
    [0, 'string', '=', b'\\\\section', 'LaTeX document text'],
    [0, 'string', '=', b'\\\\setlength', 'LaTeX document text'],
    [0, 'string', '=', b'\\\\documentstyle', 'LaTeX document text'],
    [0, 'string', '=', b'\\\\chapter', 'LaTeX document text'],
    [0, 'string', '=', b'\\\\documentclass', 'LaTeX 2e document text'],
    [0, 'string', '=', b'\\\\relax', 'LaTeX auxiliary file'],
    [0, 'string', '=', b'\\\\contentsline', 'LaTeX table of contents'],
    [0, 'string', '=', b'\\\\indexentry', 'LaTeX raw index file'],
    [0, 'string', '=', b'\\\\begin{theindex}', 'LaTeX sorted index'],
    [0, 'string', '=', b'\\\\glossaryentry', 'LaTeX raw glossary'],
    [0, 'string', '=', b'\\\\begin{theglossary}', 'LaTeX sorted glossary'],
    [0, 'string', '=', b'This is makeindex', 'Makeindex log file'],
    [0, 'string', '=', b'**TI82**', 'TI-82 Graphing Calculator'],
    [0, 'string', '=', b'**TI83**', 'TI-83 Graphing Calculator'],
    [0, 'string', '=', b'**TI85**', 'TI-85 Graphing Calculator'],
    [0, 'string', '=', b'**TI92**', 'TI-92 Graphing Calculator'],
    [0, 'string', '=', b'**TI80**', 'TI-80 Graphing Calculator File.'],
    [0, 'string', '=', b'**TI81**', 'TI-81 Graphing Calculator File.'],
    [0, 'string', '=', b'TZif', 'timezone data'],
    [0, 'string', '=', b'\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\001\000', 'old timezone data'],
    [0, 'string', '=',
     '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\002\000',
     'old timezone data'],
    [0, 'string', '=',
     '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\003\000',
     'old timezone data'],
    [0, 'string', '=',
     '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\004\000',
     'old timezone data'],
    [0, 'string', '=',
     '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\005\000',
     'old timezone data'],
    [0, 'string', '=',
     '\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\000\006\000',
     'old timezone data'],
    [0, 'string', '=', b'.\\\\"', 'troff or preprocessor input text'],
    [0, 'string', '=', b'\'\\\\"', 'troff or preprocessor input text'],
    [0, 'string', '=', b'\'.\\\\"', 'troff or preprocessor input text'],
    [0, 'string', '=', b'\\\\"', 'troff or preprocessor input text'],
    [0, 'string', '=', b'x T', 'ditroff text'],
    [0, 'string', '=', b'@\357', 'very old (C/A/T) troff output data'],
    [0, 'string', '=', b'Interpress/Xerox', 'Xerox InterPress data'],
    [0, 'short', '=', 263, 'unknown machine executable'],
    [0, 'short', '=', 264, 'unknown pure executable'],
    [0, 'short', '=', 265, 'PDP-11 separate I&D'],
    [0, 'short', '=', 267, 'unknown pure executable'],
    [0, 'long', '=', 268, 'unknown demand paged pure executable'],
    [0, 'long', '=', 269, 'unknown demand paged pure executable'],
    [0, 'long', '=', 270, 'unknown readable demand paged pure executable'],
    [0, 'string', '=', b'begin uuencoded', 'or xxencoded text'],
    [0, 'string', '=', b'xbtoa Begin', "btoa'd text"],
    [0, 'string', '=', b'$\012ship', "ship'd binary text"],
    [0, 'string', '=', b'Decode the following with bdeco', 'bencoded News text'],
    [11, 'string', '=', 'must be converted with BinHex', 'BinHex binary text'],
    [0, 'short', '=', 610, 'Perkin-Elmer executable'],
    [0, 'beshort', '=', 572, 'amd 29k coff noprebar executable'],
    [0, 'beshort', '=', 1572, 'amd 29k coff prebar executable'],
    [0, 'beshort', '=', 160007, 'amd 29k coff archive'],
    [6, 'beshort', '=', 407, 'unicos (cray) executable'],
    [596, 'string', '=', 'X\337\377\377', 'Ultrix core file'],
    [0, 'string', '=', b'Joy!peffpwpc', 'header for PowerPC PEF executable'],
    [0, 'lelong', '=', 101557, 'VAX single precision APL workspace'],
    [0, 'lelong', '=', 101556, 'VAX double precision APL workspace'],
    [0, 'lelong', '=', 407, 'VAX executable'],
    [0, 'lelong', '=', 410, 'VAX pure executable'],
    [0, 'lelong', '=', 413, 'VAX demand paged pure executable'],
    [0, 'leshort', '=', 570, 'VAX COFF executable'],
    [0, 'leshort', '=', 575, 'VAX COFF pure executable'],
    [0, 'string', '=', b'LBLSIZE=', 'VICAR image data'],
    [43, 'string', '=', 'SFDU_LABEL', 'VICAR label file'],
    [0, 'short', '=', 21845, 'VISX image file'],
    [0, 'string', '=', b'\260\0000\000', 'VMS VAX executable'],
    [0, 'belong', '=', 50331648, 'VMS Alpha executable'],
    [1, 'string', '=', 'WPC', '(Corel/WP)'],
    [0, 'string', '=', b'core', 'core file (Xenix)'],
    [0, 'byte', '=', 128, '8086 relocatable (Microsoft)'],
    [0, 'leshort', '=', 65381, 'x.out'],
    [0, 'leshort', '=', 518, 'Microsoft a.out'],
    [0, 'leshort', '=', 320, 'old Microsoft 8086 x.out'],
    [0, 'lelong', '=', 518, 'b.out'],
    [0, 'leshort', '=', 1408, 'XENIX 8086 relocatable or 80286 small model'],
    [0, 'long', '=', 59399, 'object file (z8000 a.out)'],
    [0, 'long', '=', 59400, 'pure object file (z8000 a.out)'],
    [0, 'long', '=', 59401, 'separate object file (z8000 a.out)'],
    [0, 'long', '=', 59397, 'overlay object file (z8000 a.out)'],
    [0, 'string', '=', b'ZyXEL\002', 'ZyXEL voice data'],
    ]

magicNumbers = []
hexdigits = '0123456789abcdefABCDEF'


def strToNum(n):
    if n[:1] == 'x':
        n = '0' + n
    if n[:2] == '0x':
        # hex
        return int(n, 16)
    
    elif n[0] == '\\':
        # octal
        n = n[1:]
        return int(n, 8)
    
    else:
        return int(n)


def unescape(s):
    # replace string escape sequences
    while 1:
        m = re.search(r'\\', s)

        if not m:
            break

        x = m.start() + 1

        if m.end() == len(s):
            # escaped space at end
            s = s[:len(s) - 1] + ' '
        
        elif s[x:x + 2] == '0x':
            # hex ascii value
            c = chr(strToNum(s[x:x + 4]))
            s = s[:x - 1] + c + s[x + 4:]

        elif s[m.start() + 1] == 'x':
            # hex ascii value
            c = chr(strToNum(s[x:x + 3]))
            s = s[:x - 1] + c + s[x + 3:]
        
        elif 58 > ord(s[x]) > 47:
            # octal ascii value
            end = x

            while ord(s[end]) > 47 and ord(s[end]) < 58:
                end = end + 1
                if end > len(s) - 1:
                    break
            c = chr(strToNum(s[x - 1:end]))
            s = s[:x - 1] + c + s[end:]
        
        elif s[x] == 'n':
            # newline
            s = s[:x - 1] + '\n' + s[x + 1:]
        
        else:
            break

    return s


class magicTest:
    def __init__(self, offset, t, op, value, msg, mask=None):
        if t.count('&') > 0:
            mask = strToNum(t[t.index('&') + 1:])
            t = t[:t.index('&')]

        if type(offset) == type('a'):
            self.offset = strToNum(offset)
        else:
            self.offset = offset

        self.type = t 
        self.msg = msg
        self.subTests = []
        self.op = op
        self.mask = mask
        self.value = value

    def test(self, data):
        if self.mask:
            data = data & self.mask

        if self.op == '=':
            if self.value == data:
                return self.msg

        return None

    def compare(self, data):
        try:
            if self.type == 'string':
                
                (c, s) = (b'', b'')
                
                for i in range(0, len(self.value) + 1):
                    if i + self.offset > len(data) - 1:
                        break
                    s = s + c
                    [c, ] = struct.unpack('c', data[self.offset + i:self.offset + i+1])

                data = s
            
            elif self.type == 'short':
                [data, ] = struct.unpack('h', data[self.offset:self.offset + 2])
            
            elif self.type == 'leshort':
                [data, ] = struct.unpack('<h', data[self.offset:self.offset + 2])
            
            elif self.type == 'beshort':
                [data, ] = struct.unpack('>H', data[self.offset:self.offset + 2])

            elif self.type == 'long':
                [data, ] = struct.unpack('l', data[self.offset:self.offset + 4])

            elif self.type == 'lelong':
                [data, ] = struct.unpack('<l', data[self.offset:self.offset + 4])

            elif self.type == 'belong':
                [data, ] = struct.unpack('>l', data[self.offset:self.offset + 4])

            else:
                pass
                
        except:
            return None
        
        return self.test(data)


def load(file):
    global magicNumbers
    lines = open(file).readlines()
    last = {0: None}
    
    for line in lines:
        if re.match(r'\s*#', line):
            # comment
            continue
        
        else:
            # split up by space delimiters, and remove trailing space
            line = line.rstrip()
            line = re.split(r'\s*', line)
            
            if len(line) < 3:
                # bad line
                continue
            
            offset = line[0]
            type = line[1]
            value = line[2]
            level = 0

            while offset[0] == '>':
                # count the level of the type
                level = level + 1
                offset = offset[1:]
            
            l = magicNumbers

            if level > 0:
                l = last[level - 1].subTests

            if offset[0] in ('(', '&'):
                # don't handle indirect and relative offsets just yet
                pass
            
            else:
                operands = ['=', '<', '>', '&']
                if operands.count(value[0]) > 0:
                    # a comparison operator is specified
                    op = value[0]
                    value = value[1:]
                else:
                    if len(value) > 1 and value[0] == '\\' and operands.count(value[1]) > 0:
                        # literal value that collides with operands is escaped
                        value = value[1:]
                    
                    op = '='

                mask = None

                if type == 'string':
                    while 1:
                        value = unescape(value)
                        if value[len(value) - 1] == ' ' and len(line) > 3:
                            # last value was an escaped space, join
                            value = value + line[3]
                            del line[3]
                        else:
                            break
                else:
                    if value.count('&') != 0:
                        mask = value[value.index('&') + 1:]
                        value = value[:value.index('&') + 1]

                    try:
                        value = strToNum(value)
                    except:
                        continue

                    msg = ('').join(list(line[3:]))

                new = magicTest(offset, type, op, value, msg, mask)
                last[level] = new
                l.append(new)


def load(file):
    global magicNumbers
    lines = open(file).readlines()
    last = {0: None}
    for line in lines:
        if re.match(r'\s*#', line):
            # comment
            continue
        
        else:
            # split up by space delimiters, and remove trailing space
            line = line.rstrip()
            line = re.split(r'\s*', line)
            
            if len(line) < 3:
                # bad line
                continue
            
            offset = line[0]
            type = line[1]
            value = line[2]
            level = 0
            
            while offset[0] == '>':
                # count the level of the type
                level = level + 1
                offset = offset[1:]
            
            l = magicNumbers
            
            if level > 0:
                l = last[level - 1].subTests
            
            if offset[0] == '(':
                # don't handle indirect offsets just yet
                pass
            
            elif offset[0] == '&':
                # don't handle relative offsets just yet
                pass
            
            else:
                operands = ['=', '<', '>', '&']
                if operands.count(value[0]) > 0:

                    # a comparison operator is specified

                    op = value[0]
                    value = value[1:]
                else:
                    if len(value) > 1 and value[0] == '\\' and operands.count(value[1]) > 0:

                        # literal value that collides with operands is escaped

                        value = value[1:]
                    op = '='

                mask = None
                
                if type == 'string':
                    while 1:
                        value = unescape(value)
                        if value[len(value) - 1] == ' ' and len(line) > 3:

                            # last value was an escaped space, join

                            value = value + line[3]
                            del line[3]
                        else:
                            break
                else:
                    if value.count('&') != 0:
                        mask = value[value.index('&') + 1:]
                        value = value[:value.index('&') + 1]
                    try:
                        value = strToNum(value)
                    except:
                        continue
                    msg = ('').join(list(line[3:]))
                    
                new = magicTest(offset, type, op, value, msg, mask)
                last[level] = new
                l.append(new)


def whatis(data):
    for test in magicNumbers:
        m = test.compare(data)

        if m:
            return m

    # no matching, magic number. is it binary or text?
    for c in data:
        #if ord(c) > 128:
        if type(c) is int:
            c1 = c
        else:
            c1 = ord(c)

        if c1 == 0:
            return 'data'

    # its ASCII, now do C/CPP tests
    if data.find(b'#include', 0, 256) > -1 or data.find(b'/***', 0, 256) > -1:
        return 'text/cpp'

    # its ASCII, now do text tests
    if data.find(b'!/usr/bin/env python', 0, 256) > -1 or data.find(b'def ', 0, 8192) > -1:
        return 'application/x-python'

    return "text/plain"


def mime_type(f):
    if os.path.exists(f):
        if os.path.isdir(f):
            return "directory"

        return whatis(open(f, 'rb').read(8192))
    else:

        return ''


for m in magic:
    magicNumbers.append(magicTest(m[0], m[1], m[2], m[3], m[4]))
