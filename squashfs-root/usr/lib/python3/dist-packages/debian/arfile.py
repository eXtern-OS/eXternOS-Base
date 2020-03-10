# ArFile: a Python representation of ar (as in "man 1 ar") archives.
# Copyright (C) 2007    Stefano Zacchiroli  <zack@debian.org>
# Copyright (C) 2007    Filippo Giunchedi   <filippo@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import sys

GLOBAL_HEADER = b"!<arch>\n"
GLOBAL_HEADER_LENGTH = len(GLOBAL_HEADER)

FILE_HEADER_LENGTH = 60
FILE_MAGIC = b"`\n"

class ArError(Exception):
    pass

class ArFile(object):
    """ Representation of an ar archive, see man 1 ar.
    
    The interface of this class tries to mimick that of the TarFile module in
    the standard library.
    
    ArFile objects have the following (read-only) properties:
        - members       same as getmembers()
    """

    def __init__(self, filename=None, mode='r', fileobj=None,
                 encoding=None, errors=None):
        """ Build an ar file representation starting from either a filename or
        an existing file object. The only supported mode is 'r'.

        In Python 3, the encoding and errors parameters control how member
        names are decoded into Unicode strings. Like tarfile, the default
        encoding is sys.getfilesystemencoding() and the default error handling
        scheme is 'surrogateescape' (>= 3.2) or 'strict' (< 3.2).
        """

        self.__members = [] 
        self.__members_dict = {}
        self.__fname = filename
        self.__fileobj = fileobj
        if encoding is None:
            encoding = sys.getfilesystemencoding()
        self.__encoding = encoding
        if errors is None:
            if sys.version >= '3.2':
                errors = 'surrogateescape'
            else:
                errors = 'strict'
        self.__errors = errors
        
        if mode == "r":
            self.__index_archive()
        pass    # TODO write support

    def __index_archive(self):
        if self.__fname:
            fp = open(self.__fname, "rb")
        elif self.__fileobj:
            fp = self.__fileobj
        else:
            raise ArError("Unable to open valid file")

        if fp.read(GLOBAL_HEADER_LENGTH) != GLOBAL_HEADER:
            raise ArError("Unable to find global header")

        while True:
            newmember = ArMember.from_file(fp, self.__fname,
                                           encoding=self.__encoding,
                                           errors=self.__errors)
            if not newmember:
                break
            self.__members.append(newmember)
            self.__members_dict[newmember.name] = newmember
            if newmember.size % 2 == 0: # even, no padding
                fp.seek(newmember.size, 1) # skip to next header
            else:
                fp.seek(newmember.size + 1 , 1) # skip to next header
        
        if self.__fname:
            fp.close()

    def getmember(self, name):
        """ Return the (last occurrence of a) member in the archive whose name
        is 'name'. Raise KeyError if no member matches the given name.

        Note that in case of name collisions the only way to retrieve all
        members matching a given name is to use getmembers. """

        return self.__members_dict[name]

    def getmembers(self):
        """ Return a list of all members contained in the archive.

        The list has the same order of members in the archive and can contain
        duplicate members (i.e. members with the same name) if they are
        duplicate in the archive itself. """

        return self.__members

    members = property(getmembers)

    def getnames(self):
        """ Return a list of all member names in the archive. """

        return [f.name for f in self.__members]

    def extractall():
        """ Not (yet) implemented. """

        raise NotImplementedError  # TODO

    def extract(self, member, path):
        """ Not (yet) implemented. """

        raise NotImplementedError  # TODO

    def extractfile(self, member):
        """ Return a file object corresponding to the requested member. A member
        can be specified either as a string (its name) or as a ArMember
        instance. """

        # TODO(jsw): What is the point of this method?  It differs from
        # getmember in the following ways:
        #  - It returns the *first* member with the given name instead of the
        #    last.
        #  - If member is an ArMember, it uses that ArMember's name as the key.
        # The former just seems confusing (and this implementation less
        # efficient than getmember's - probably historical), and I'm having a
        # hard time seeing the use-case for the latter.
        for m in self.__members:
            if isinstance(member, ArMember) and m.name == member.name:
                return m
            elif member == m.name:
                return m
        return None

    # container emulation

    def __iter__(self):
        """ Iterate over the members of the present ar archive. """

        return iter(self.__members)

    def __getitem__(self, name):
        """ Same as .getmember(name). """

        return self.getmember(name)


class ArMember(object):
    """ Member of an ar archive.

    Implements most of a file object interface: read, readline, next,
    readlines, seek, tell, close.
    
    ArMember objects have the following (read-only) properties:
        - name      member name in an ar archive
        - mtime     modification time
        - owner     owner user
        - group     owner group
        - fmode     file permissions
        - size      size in bytes
        - fname     file name"""

    def __init__(self):
        self.__name = None      # member name (i.e. filename) in the archive
        self.__mtime = None     # last modification time
        self.__owner = None     # owner user
        self.__group = None     # owner group
        self.__fmode = None     # permissions
        self.__size = None      # member size in bytes
        self.__fname = None     # file name associated with this member
        self.__fp = None        # file pointer 
        self.__offset = None    # start-of-data offset
        self.__end = None       # end-of-data offset

    def from_file(fp, fname, encoding=None, errors=None):
        """fp is an open File object positioned on a valid file header inside
        an ar archive. Return a new ArMember on success, None otherwise. """

        buf = fp.read(FILE_HEADER_LENGTH)

        if not buf:
            return None

        # sanity checks
        if len(buf) < FILE_HEADER_LENGTH:
            raise IOError("Incorrect header length")

        if buf[58:60] != FILE_MAGIC:
            raise IOError("Incorrect file magic")

        if sys.version >= '3':
            if encoding is None:
                encoding = sys.getfilesystemencoding()
            if errors is None:
                if sys.version >= '3.2':
                    errors = 'surrogateescape'
                else:
                    errors = 'strict'

        # http://en.wikipedia.org/wiki/Ar_(Unix)    
        #from   to     Name                      Format
        #0      15     File name                 ASCII
        #16     27     File modification date    Decimal
        #28     33     Owner ID                  Decimal
        #34     39     Group ID                  Decimal
        #40     47     File mode                 Octal
        #48     57     File size in bytes        Decimal
        #58     59     File magic                \140\012

        # XXX struct.unpack can be used as well here
        f = ArMember()
        f.__name = buf[0:16].split(b"/")[0].strip()
        if sys.version >= '3':
            f.__name = f.__name.decode(encoding, errors)
        f.__mtime = int(buf[16:28])
        f.__owner = int(buf[28:34])
        f.__group = int(buf[34:40])
        f.__fmode  = buf[40:48]  # XXX octal value
        f.__size  = int(buf[48:58])

        f.__fname = fname
        f.__offset = fp.tell() # start-of-data
        f.__end = f.__offset + f.__size

        return f

    from_file = staticmethod(from_file)
    
    # file interface

    # XXX this is not a sequence like file objects
    def read(self, size=0):
        if self.__fp is None:
            self.__fp = open(self.__fname, "rb")
            self.__fp.seek(self.__offset)

        cur = self.__fp.tell()

        if size > 0 and size <= self.__end - cur: # there's room
            return self.__fp.read(size)

        if cur >= self.__end or cur < self.__offset:
            return b''

        return self.__fp.read(self.__end - cur)

    def readline(self, size=None):
        if self.__fp is None:
            self.__fp = open(self.__fname, "rb")
            self.__fp.seek(self.__offset)

        if size is not None: 
            buf = self.__fp.readline(size)
            if self.__fp.tell() > self.__end:
                return b''

            return buf

        buf = self.__fp.readline()
        if self.__fp.tell() > self.__end:
            return b''
        else:
            return buf

    def readlines(self, sizehint=0):
        if self.__fp is None:
            self.__fp = open(self.__fname, "rb")
            self.__fp.seek(self.__offset)
        
        buf = None
        lines = []
        while True: 
            buf = self.readline()
            if not buf: 
                break
            lines.append(buf)

        return lines

    def seek(self, offset, whence=0):
        if self.__fp is None:
            self.__fp = open(self.__fname, "rb")
            self.__fp.seek(self.__offset)

        if self.__fp.tell() < self.__offset:
            self.__fp.seek(self.__offset)

        if whence < 2 and offset + self.__fp.tell() < self.__offset:
            raise IOError("Can't seek at %d" % offset)
        
        if whence == 1:
            self.__fp.seek(offset, 1)
        elif whence == 0:
            self.__fp.seek(self.__offset + offset, 0)
        elif whence == 2:
            self.__fp.seek(self.__end + offset, 0)

    def tell(self):
        if self.__fp is None:
            self.__fp = open(self.__fname, "rb")
            self.__fp.seek(self.__offset)

        cur = self.__fp.tell()
        
        if cur < self.__offset:
            return 0
        else:
            return cur - self.__offset

    def seekable(self):
        return True

    def close(self):
        if self.__fp is not None:
            self.__fp.close()
   
    def next(self):
        return self.readline()
    
    def __iter__(self):
        def nextline():
            line = self.readline()
            if line:
                yield line

        return iter(nextline())

    name = property(lambda self: self.__name)
    mtime = property(lambda self: self.__mtime)
    owner = property(lambda self: self.__owner)
    group = property(lambda self: self.__group)
    fmode = property(lambda self: self.__fmode)
    size = property(lambda self: self.__size)
    fname = property(lambda self: self.__fname)

if __name__ == '__main__':
    # test
    # ar r test.ar <file1> <file2> .. <fileN>
    a = ArFile("test.ar")
    print("\n".join(a.getnames()))
