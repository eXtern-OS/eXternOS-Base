# -*- coding: utf-8 -*-
#
# (c) Copyright 2001-2015 HP Development Company, L.P.
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
# Ported from Perl's Image::Size module by Randy J. Ray
#

# Std Lib
import os
import os.path
import re
import struct

# Re patterns
xbm_pat = re.compile(r'^\#define\s*\S*\s*(\d+)\s*\n\#define\s*\S*\s*(\d+)', re.IGNORECASE)
xpm_pat = re.compile(r'"\s*(\d+)\s+(\d+)(\s+\d+\s+\d+){1,2}\s*"', re.IGNORECASE)
ppm_pat1 = re.compile(r'^\#.*', re.IGNORECASE | re.MULTILINE)
ppm_pat2 = re.compile(r'^(P[1-6])\s+(\d+)\s+(\d+)', re.IGNORECASE)
ppm_pat3 = re.compile(r'IMGINFO:(\d+)x(\d+)', re.IGNORECASE)
tiff_endian_pat = re.compile(r'II\x2a\x00')


def readin(stream, length, offset=0):
    if offset != 0:
        stream.seek(offset, 0)

    return stream.read(length)


def xbmsize(stream):
    width, height = -1, -1
    match = xbm_pat.match(readin(stream,1024))

    try:
        width = int(match.group(1))
        height = int(match.group(2))
    except:
        pass

    return width, height


def xpmsize(stream):
    width, height = -1, -1
    match = re.search(xpm_pat, readin(stream, 1024))
    try:
        width = int(match.group(1))
        height = int(match.group(2))
    except:
        pass

    return width, height


def pngsize(stream): # also does MNG
    width, height = -1, -1

    if readin(stream, 4, 12) in ('IHDR', 'MHDR'):
        height, width = struct.unpack("!II", stream.read(8))

    return width,height


def jpegsize(stream):
    width, height = -1, -1
    stream.seek(2)
    while True:
        length = 4
        buffer = readin(stream, length)
        try:
            marker, code, length = struct.unpack("!c c h", buffer)
        except:
            break

        if marker != '\xff':
            break

        if 0xc0 <= ord(code) <= 0xc3:
            length = 5
            height, width = struct.unpack("!xhh", readin(stream, length))

        else:
            readin(stream, length-2)

    return width, height


def ppmsize(stream):
    width, height = -1, -1
    header = re.sub(ppm_pat1, '', readin(stream, 1024))
    match = ppm_pat2.match(header)
    typ = ''
    try:
        typ = match.group(1)
        width = int(match.group(2))
        height = int(match.group(3))
    except:
        pass

    if typ == 'P7':
        match = ppm_pat3.match(header)

        try:
            width = int(match.group(1))
            height = int(match.group(2))
        except:
            pass

    return width, height


def tiffsize(stream):
    header = readin(stream, 4)
    endian = ">"
    match = tiff_endian_pat.match(header)

    if match is not None:
        endian = "<"

    input = readin(stream, 4, 4)
    offset = struct.unpack('%si' % endian, input)[0]
    num_dirent = struct.unpack('%sH' % endian, readin(stream, 2, offset))[0]
    offset += 2
    num_dirent = offset+(num_dirent*12)
    width, height = -1, -1

    while True:
        ifd = readin(stream, 12, offset)

        if ifd == '' or offset > num_dirent:
            break

        offset += 12
        tag = struct.unpack('%sH'% endian, ifd[0:2])[0]
        type = struct.unpack('%sH' % endian, ifd[2:4])[0]

        if tag == 0x0100:
            width = struct.unpack("%si" % endian, ifd[8:12])[0] 

        elif tag == 0x0101:
            height = struct.unpack("%si" % endian, ifd[8:12])[0] 

    return width, height


def bmpsize(stream):
    width, height = struct.unpack("<II", readin(stream, 8, 18))
    return width, height


def gifsize(stream):
    # since we only care about the printed size of the image
    # we only need to get the logical screen sizes, which are
    # the maximum extents of the image. This code is much simpler
    # than the code from Image::Size
    #width, height = -1, -1
    buf = readin(stream, 7, 6) # LSx, GCTF, etc 
    height, width, flags, bci, par = struct.unpack('<HHBBB', buf)

    return width, height




TYPE_MAP = {re.compile('^GIF8[7,9]a')              : ('image/gif', gifsize),
             re.compile("^\xFF\xD8")                : ('image/jpeg', jpegsize),
             re.compile("^\x89PNG\x0d\x0a\x1a\x0a") : ('image/png', pngsize),
             re.compile("^P[1-7]")                  : ('image/x-portable-pixmap', ppmsize),
             re.compile('\#define\s+\S+\s+\d+')     : ('image/x-xbitmap', xbmsize),
             re.compile('\/\* XPM \*\/')            : ('image/x-xpixmap', xpmsize),
             re.compile('^MM\x00\x2a')              : ('image/tiff', tiffsize),
             re.compile('^II\*\x00')                : ('image/tiff', tiffsize),
             re.compile('^BM')                      : ('image/x-bitmap', bmpsize),
             re.compile("^\x8aMNG\x0d\x0a\x1a\x0a") : ('image/png', pngsize),
           }


def imagesize(filename, mime_type=''):
    width, height = -1, -1

    f = open(filename, 'r')
    buffer = f.read(4096)

    if not mime_type:
        for t in TYPE_MAP:
            match = t.search(buffer)
            if match is not None:
                mime_type, func = TYPE_MAP[t]
                break

    if mime_type and func:
        f.seek(0)
        width, height = func(f)
    else:
        width, height = -1, -1

    f.close()

    return height, width, mime_type

