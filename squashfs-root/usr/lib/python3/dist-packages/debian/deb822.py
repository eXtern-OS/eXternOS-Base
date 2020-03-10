# vim: fileencoding=utf-8
#
# A python interface for various rfc822-like formatted files used by Debian
# (.changes, .dsc, Packages, Sources, etc)
#
# Copyright (C) 2005-2006  dann frazier <dannf@dannf.org>
# Copyright (C) 2006-2010  John Wright <john@johnwright.org>
# Copyright (C) 2006       Adeodato Simó <dato@net.com.org.es>
# Copyright (C) 2008       Stefano Zacchiroli <zack@upsilon.cc>
# Copyright (C) 2014       Google, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from __future__ import absolute_import, print_function

from debian.deprecation import function_deprecated_by

try:
    import apt_pkg
    # This module uses apt_pkg only for its TagFile interface.
    apt_pkg.TagFile
    _have_apt_pkg = True
except (ImportError, AttributeError):
    _have_apt_pkg = False

import chardet
import collections
import datetime
import email.utils
import re
import subprocess
import sys
import warnings

from io import BytesIO, StringIO

import six

if sys.version >= '3':
    import io
    def _is_real_file(f):
        if not isinstance(f, io.IOBase):
            return False
        try:
            f.fileno()
            return True
        except (AttributeError, io.UnsupportedOperation):
            return False
else:
    def _is_real_file(f):
        return isinstance(f, file) and hasattr(f, 'fileno')


GPGV_DEFAULT_KEYRINGS = frozenset(['/usr/share/keyrings/debian-keyring.gpg'])
GPGV_EXECUTABLE = '/usr/bin/gpgv'


class Error(Exception):
    """Base class for custom exceptions in this module."""


class RestrictedFieldError(Error):
    """Raised when modifying the raw value of a field is not allowed."""


class TagSectionWrapper(collections.Mapping):
    """Wrap a TagSection object, using its find_raw method to get field values

    This allows us to pick which whitespace to strip off the beginning and end
    of the data, so we don't lose leading newlines.
    """

    def __init__(self, section):
        self.__section = section

    def __iter__(self):
        for key in self.__section.keys():
            if not key.startswith('#'):
                yield key

    def __len__(self):
        return len([key for key in self.__section.keys()
                    if not key.startswith('#')])

    def __getitem__(self, key):
        s = self.__section.find_raw(key)

        if s is None:
            raise KeyError(key)

        # Get just the stuff after the first ':'
        # Could use s.partition if we only supported python >= 2.5
        data = s[s.find(b':')+1:]

        # Get rid of spaces and tabs after the ':', but not newlines, and strip
        # off any newline at the end of the data.
        return data.lstrip(b' \t').rstrip(b'\n')


class OrderedSet(object):
    """A set-like object that preserves order when iterating over it

    We use this to keep track of keys in Deb822Dict, because it's much faster
    to look up if a key is in a set than in a list.
    """

    def __init__(self, iterable=[]):
        self.__set = set()
        self.__order = []
        for item in iterable:
            self.add(item)

    def add(self, item):
        if item not in self:
            # set.add will raise TypeError if something's unhashable, so we
            # don't have to handle that ourselves
            self.__set.add(item)
            self.__order.append(item)

    def remove(self, item):
        # set.remove will raise KeyError, so we don't need to handle that
        # ourselves
        self.__set.remove(item)
        self.__order.remove(item)

    def __iter__(self):
        # Return an iterator of items in the order they were added
        return iter(self.__order)

    def __len__(self):
        return len(self.__order)

    def __contains__(self, item):
        # This is what makes OrderedSet faster than using a list to keep track
        # of keys.  Lookup in a set is O(1) instead of O(n) for a list.
        return item in self.__set

    ### list-like methods
    append = add

    def extend(self, iterable):
        for item in iterable:
            self.add(item)
    ###


class Deb822Dict(collections.MutableMapping):
    """A dictionary-like object suitable for storing RFC822-like data.

    Deb822Dict behaves like a normal dict, except:
        - key lookup is case-insensitive
        - key order is preserved
        - if initialized with a _parsed parameter, it will pull values from
          that dictionary-like object as needed (rather than making a copy).
          The _parsed dict is expected to be able to handle case-insensitive
          keys.

    If _parsed is not None, an optional _fields parameter specifies which keys
    in the _parsed dictionary are exposed.
    """

    # See the end of the file for the definition of _strI

    def __init__(self, _dict=None, _parsed=None, _fields=None,
                 encoding="utf-8"):
        self.__dict = {}
        self.__keys = OrderedSet()
        self.__parsed = None
        self.encoding = encoding

        if _dict is not None:
            # _dict may be a dict or a list of two-sized tuples
            if hasattr(_dict, 'items'):
                items = _dict.items()
            else:
                items = list(_dict)

            try:
                for k, v in items:
                    self[k] = v
            except ValueError:
                this = len(self.__keys)
                len_ = len(items[this])
                raise ValueError('dictionary update sequence element #%d has '
                    'length %d; 2 is required' % (this, len_))
        
        if _parsed is not None:
            self.__parsed = _parsed
            if _fields is None:
                self.__keys.extend([ _strI(k) for k in self.__parsed ])
            else:
                self.__keys.extend([ _strI(f) for f in _fields if f in self.__parsed ])

    def _detect_encoding(self, value):
        """If value is not already Unicode, decode it intelligently."""
        if isinstance(value, bytes):
            try:
                return value.decode(self.encoding)
            except UnicodeDecodeError as e:
                # Evidently, the value wasn't encoded with the encoding the
                # user specified.  Try detecting it.
                warnings.warn('decoding from %s failed; attempting to detect '
                              'the true encoding' % self.encoding,
                              UnicodeWarning)
                result = chardet.detect(value)
                try:
                    return value.decode(result['encoding'])
                except UnicodeDecodeError:
                    raise e
                else:
                    # Assume the rest of the paragraph is in this encoding as
                    # well (there's no sense in repeating this exercise for
                    # every field).
                    self.encoding = result['encoding']
        else:
            return value

    ### BEGIN collections.MutableMapping methods

    def __iter__(self):
        for key in self.__keys:
            yield str(key)

    def __len__(self):
        return len(self.__keys)

    def __setitem__(self, key, value):
        key = _strI(key)
        self.__keys.add(key)
        self.__dict[key] = value
        
    def __getitem__(self, key):
        key = _strI(key)
        try:
            value = self.__dict[key]
        except KeyError:
            if self.__parsed is not None and key in self.__keys:
                value = self.__parsed[key]
            else:
                raise

        # TODO(jsw): Move the decoding logic into __setitem__ so that we decode
        # it once instead of every time somebody asks for it.  Even better if
        # Deb822* classes dealt in pure unicode and didn't care about the
        # encoding of the files they came from...but I don't know how to fix
        # that without breaking a bunch of users.
        return self._detect_encoding(value)

    def __delitem__(self, key):
        key = _strI(key)
        self.__keys.remove(key)
        try:
            del self.__dict[key]
        except KeyError:
            # If we got this far, the key was in self.__keys, so it must have
            # only been in the self.__parsed dict.
            pass

    def __contains__(self, key):
        key = _strI(key)
        return key in self.__keys

    if sys.version < '3':
        has_key = __contains__

    ### END collections.MutableMapping methods

    def __repr__(self):
        return '{%s}' % ', '.join(['%r: %r' % (k, v) for k, v in self.items()])

    def __eq__(self, other):
        mykeys = sorted(self)
        otherkeys = sorted(other)
        if not mykeys == otherkeys:
            return False

        for key in mykeys:
            if self[key] != other[key]:
                return False

        # If we got here, everything matched
        return True

    # Overriding __eq__ blocks inheritance of __hash__ in Python 3, and
    # instances of this class are not sensibly hashable anyway.
    __hash__ = None

    def copy(self):
        # Use self.__class__ so this works as expected for subclasses
        copy = self.__class__(self)
        return copy

    # TODO implement __str__() and make dump() use that?


class Deb822(Deb822Dict):

    def __init__(self, sequence=None, fields=None, _parsed=None,
                 encoding="utf-8"):
        """Create a new Deb822 instance.

        :param sequence: a string, or any any object that returns a line of
            input each time, normally a file.  Alternately, sequence can
            be a dict that contains the initial key-value pairs. When
            python-apt is present, sequence can also be a compressed object,
            for example a file object associated to something.gz.

        :param fields: if given, it is interpreted as a list of fields that
            should be parsed (the rest will be discarded).

        :param _parsed: internal parameter.

        :param encoding: When parsing strings, interpret them in this encoding.
            (All values are given back as unicode objects, so an encoding is
            necessary in order to properly interpret the strings.)
        """

        if hasattr(sequence, 'items'):
            _dict = sequence
            sequence = None
        else:
            _dict = None
        Deb822Dict.__init__(self, _dict=_dict, _parsed=_parsed, _fields=fields,
                            encoding=encoding)

        if sequence is not None:
            try:
                self._internal_parser(sequence, fields)
            except EOFError:
                pass

        self.gpg_info = None

    @classmethod
    def iter_paragraphs(cls, sequence, fields=None, use_apt_pkg=False,
                        shared_storage=False, encoding="utf-8"):
        """Generator that yields a Deb822 object for each paragraph in sequence.

        :param sequence: same as in __init__.

        :param fields: likewise.

        :param use_apt_pkg: if sequence is a file, apt_pkg can be used
            if available to parse the file, since it's much much faster.  Set
            this parameter to True to enable use of apt_pkg. Note that the
            TagFile parser from apt_pkg is a much stricter parser of the
            Deb822 format, particularly with regards whitespace between
            paragraphs and comments within paragraphs. If these features are
            required (for example in debian/control files), ensure that this
            parameter is set to False.
        :param shared_storage: not used, here for historical reasons.  Deb822
            objects never use shared storage anymore.
        :param encoding: Interpret the paragraphs in this encoding.
            (All values are given back as unicode objects, so an encoding is
            necessary in order to properly interpret the strings.)
        """

        if _have_apt_pkg and use_apt_pkg and _is_real_file(sequence):
            kwargs = {}
            if sys.version >= '3':
                # bytes=True is supported for both Python 2 and 3, but we
                # only actually need it for Python 3, so this saves us from
                # having to require a newer version of python-apt for Python
                # 2 as well.  This allows us to apply our own encoding
                # handling, which is more tolerant of mixed-encoding files.
                kwargs['bytes'] = True
            parser = apt_pkg.TagFile(sequence, **kwargs)
            for section in parser:
                paragraph = cls(fields=fields,
                                _parsed=TagSectionWrapper(section),
                                encoding=encoding)
                if paragraph:
                    yield paragraph

        else:
            if isinstance(sequence, six.string_types + (six.binary_type,)):
                sequence = sequence.splitlines()
            iterable = iter(sequence)
            while True:
                x = cls(iterable, fields, encoding=encoding)
                if not x:
                    break
                yield x

    ###

    @staticmethod
    def _skip_useless_lines(sequence):
        """Yields only lines that do not begin with '#'.

        Also skips any blank lines at the beginning of the input.
        """
        at_beginning = True
        for line in sequence:
            # The bytes/str polymorphism required here to support Python 3
            # is unpleasant, but fortunately limited.  We need this because
            # at this point we might have been given either bytes or
            # Unicode, and we haven't yet got to the point where we can try
            # to decode a whole paragraph and detect its encoding.
            if isinstance(line, bytes):
                if line.startswith(b'#'):
                    continue
            else:
                if line.startswith('#'):
                    continue
            if at_beginning:
                if isinstance(line, bytes):
                    if not line.rstrip(b'\r\n'):
                        continue
                else:
                    if not line.rstrip('\r\n'):
                        continue
                at_beginning = False
            yield line

    def _internal_parser(self, sequence, fields=None):
        # The key is non-whitespace, non-colon characters before any colon.
        key_part = r"^(?P<key>[^: \t\n\r\f\v]+)\s*:\s*"
        single = re.compile(key_part + r"(?P<data>\S.*?)\s*$")
        multi = re.compile(key_part + r"$")
        multidata = re.compile(r"^\s(?P<data>.+?)\s*$")

        wanted_field = lambda f: fields is None or f in fields

        if isinstance(sequence, (six.string_types, bytes)):
            sequence = sequence.splitlines()

        curkey = None
        content = ""

        for line in self.gpg_stripped_paragraph(
                self._skip_useless_lines(sequence)):
            line = self._detect_encoding(line)

            m = single.match(line)
            if m:
                if curkey:
                    self[curkey] = content

                if not wanted_field(m.group('key')):
                    curkey = None
                    continue

                curkey = m.group('key')
                content = m.group('data')
                continue

            m = multi.match(line)
            if m:
                if curkey:
                    self[curkey] = content

                if not wanted_field(m.group('key')):
                    curkey = None
                    continue

                curkey = m.group('key')
                content = ""
                continue

            m = multidata.match(line)
            if m:
                content += '\n' + line # XXX not m.group('data')?
                continue

        if curkey:
            self[curkey] = content

    def __str__(self):
        return self.dump()

    def __unicode__(self):
        return self.dump()

    if sys.version >= '3':
        def __bytes__(self):
            return self.dump().encode(self.encoding)

    # __repr__ is handled by Deb822Dict

    def get_as_string(self, key):
        """Return the self[key] as a string (or unicode)

        The default implementation just returns unicode(self[key]); however,
        this can be overridden in subclasses (e.g. _multivalued) that can take
        special values.
        """
        return six.text_type(self[key])

    def dump(self, fd=None, encoding=None, text_mode=False):
        """Dump the the contents in the original format

        If fd is None, returns a unicode object.  Otherwise, fd is assumed to
        be a file-like object, and this method will write the data to it
        instead of returning a unicode object.

        If fd is not none and text_mode is False, the data will be encoded
        to a byte string before writing to the file.  The encoding used is
        chosen via the encoding parameter; None means to use the encoding the
        object was initialized with (utf-8 by default).  This will raise
        UnicodeEncodeError if the encoding can't support all the characters in
        the Deb822Dict values.
        """
        # Ideally this would never try to encode (that should be up to the
        # caller when opening the file), but we may still have users who rely
        # on the binary mode encoding.  But...might it be better to break them
        # than to introduce yet another parameter relating to encoding?

        if fd is None:
            fd = StringIO()
            return_string = True
        else:
            return_string = False

        if encoding is None:
            # Use the encoding we've been using to decode strings with if none
            # was explicitly specified
            encoding = self.encoding

        for key in self:
            value = self.get_as_string(key)
            if not value or value[0] == '\n':
                # Avoid trailing whitespace after "Field:" if it's on its own
                # line or the value is empty.  We don't have to worry about the
                # case where value == '\n', since we ensure that is not the
                # case in __setitem__.
                entry = '%s:%s\n' % (key, value)
            else:
                entry = '%s: %s\n' % (key, value)
            if not return_string and not text_mode:
                fd.write(entry.encode(encoding))
            else:
                fd.write(entry)
        if return_string:
            return fd.getvalue()

    ###

    def is_single_line(self, s):
        if s.count("\n"):
            return False
        else:
            return True

    isSingleLine = function_deprecated_by(is_single_line)

    def is_multi_line(self, s):
        return not self.is_single_line(s)

    isMultiLine = function_deprecated_by(is_multi_line)

    def _merge_fields(self, s1, s2):
        if not s2:
            return s1
        if not s1:
            return s2

        if self.is_single_line(s1) and self.is_single_line(s2):
            ## some fields are delimited by a single space, others
            ## a comma followed by a space.  this heuristic assumes
            ## that there are multiple items in one of the string fields
            ## so that we can pick up on the delimiter being used
            delim = ' '
            if (s1 + s2).count(', '):
                delim = ', '

            L = sorted((s1 + delim + s2).split(delim))

            prev = merged = L[0]

            for item in L[1:]:
                ## skip duplicate entries
                if item == prev:
                    continue
                merged = merged + delim + item
                prev = item
            return merged

        if self.is_multi_line(s1) and self.is_multi_line(s2):
            for item in s2.splitlines(True):
                if item not in s1.splitlines(True):
                    s1 = s1 + "\n" + item
            return s1

        raise ValueError

    _mergeFields = function_deprecated_by(_merge_fields)

    def merge_fields(self, key, d1, d2=None):
        ## this method can work in two ways - abstract that away
        if d2 == None:
            x1 = self
            x2 = d1
        else:
            x1 = d1
            x2 = d2

        ## we only have to do work if both objects contain our key
        ## otherwise, we just take the one that does, or raise an
        ## exception if neither does
        if key in x1 and key in x2:
            merged = self._mergeFields(x1[key], x2[key])
        elif key in x1:
            merged = x1[key]
        elif key in x2:
            merged = x2[key]
        else:
            raise KeyError

        ## back to the two different ways - if this method was called
        ## upon an object, update that object in place.
        ## return nothing in this case, to make the author notice a
        ## problem if she assumes the object itself will not be modified
        if d2 == None:
            self[key] = merged
            return None

        return merged

    mergeFields = function_deprecated_by(merge_fields)

    def split_gpg_and_payload(sequence):
        """Return a (gpg_pre, payload, gpg_post) tuple

        Each element of the returned tuple is a list of lines (with trailing
        whitespace stripped).
        """

        gpg_pre_lines = []
        lines = []
        gpg_post_lines = []
        state = b'SAFE'
        gpgre = re.compile(br'^-----(?P<action>BEGIN|END) PGP (?P<what>[^-]+)-----[\r\t ]*$')
        # Include whitespace-only lines in blank lines to split paragraphs.
        # (see #715558)
        blank_line = re.compile(br'^\s*$')
        first_line = True

        for line in sequence:
            # Some consumers of this method require bytes (encoding
            # detection and signature checking).  However, we might have
            # been given a file opened in text mode, in which case it's
            # simplest to encode to bytes.
            if sys.version >= '3' and isinstance(line, str):
                line = line.encode()

            line = line.strip(b'\r\n')

            # skip initial blank lines, if any
            if first_line:
                if blank_line.match(line):
                    continue
                else:
                    first_line = False

            m = gpgre.match(line)

            if not m:
                if state == b'SAFE':
                    if not blank_line.match(line):
                        lines.append(line)
                    else:
                        if not gpg_pre_lines:
                            # There's no gpg signature, so we should stop at
                            # this blank line
                            break
                elif state == b'SIGNED MESSAGE':
                    if blank_line.match(line):
                        state = b'SAFE'
                    else:
                        gpg_pre_lines.append(line)
                elif state == b'SIGNATURE':
                    gpg_post_lines.append(line)
            else:
                if m.group('action') == b'BEGIN':
                    state = m.group('what')
                elif m.group('action') == b'END':
                    gpg_post_lines.append(line)
                    break
                if not blank_line.match(line):
                    if not lines:
                        gpg_pre_lines.append(line)
                    else:
                        gpg_post_lines.append(line)

        if len(lines):
            return (gpg_pre_lines, lines, gpg_post_lines)
        else:
            raise EOFError('only blank lines found in input')

    split_gpg_and_payload = staticmethod(split_gpg_and_payload)

    def gpg_stripped_paragraph(cls, sequence):
        return cls.split_gpg_and_payload(sequence)[1]

    gpg_stripped_paragraph = classmethod(gpg_stripped_paragraph)

    def get_gpg_info(self, keyrings=None):
        """Return a GpgInfo object with GPG signature information

        This method will raise ValueError if the signature is not available
        (e.g. the original text cannot be found).

        :param keyrings: list of keyrings to use (see GpgInfo.from_sequence)
        """

        # raw_text is saved (as a string) only for Changes and Dsc (see
        # _gpg_multivalued.__init__) which is small compared to Packages or
        # Sources which contain no signature
        if not hasattr(self, 'raw_text'):
            raise ValueError("original text cannot be found")

        if self.gpg_info is None:
            self.gpg_info = GpgInfo.from_sequence(self.raw_text,
                                                  keyrings=keyrings)

        return self.gpg_info

    def validate_input(self, key, value):
        """Raise ValueError if value is not a valid value for key

        Subclasses that do interesting things for different keys may wish to
        override this method.
        """

        # The value cannot end in a newline (if it did, dumping the object
        # would result in multiple stanzas)
        if value.endswith('\n'):
            raise ValueError("value must not end in '\\n'")

        # Make sure there are no blank lines (actually, the first one is
        # allowed to be blank, but no others), and each subsequent line starts
        # with whitespace
        for line in value.splitlines()[1:]:
            if not line:
                raise ValueError("value must not have blank lines")
            if not line[0].isspace():
                raise ValueError("each line must start with whitespace")

    def __setitem__(self, key, value):
        self.validate_input(key, value)
        Deb822Dict.__setitem__(self, key, value)


# XXX check what happens if input contains more that one signature
class GpgInfo(dict):
    """A wrapper around gnupg parsable output obtained via --status-fd

    This class is really a dictionary containing parsed output from gnupg plus
    some methods to make sense of the data.
    Keys are keywords and values are arguments suitably splitted.
    See /usr/share/doc/gnupg/DETAILS.gz"""

    # keys with format "key keyid uid"
    uidkeys = ('GOODSIG', 'EXPSIG', 'EXPKEYSIG', 'REVKEYSIG', 'BADSIG')

    def valid(self):
        """Is the signature valid?"""
        return 'GOODSIG' in self or 'VALIDSIG' in self
    
# XXX implement as a property?
# XXX handle utf-8 %-encoding
    def uid(self):
        """Return the primary ID of the signee key, None is not available"""
        pass

    @classmethod
    def from_output(cls, out, err=None):
        """Create a new GpgInfo object from gpg(v) --status-fd output (out) and
        optionally collect stderr as well (err).
        
        Both out and err can be lines in newline-terminated sequence or regular strings."""

        n = cls()

        if isinstance(out, six.string_types):
            out = out.split('\n')
        if isinstance(err, six.string_types):
            err = err.split('\n')

        n.out = out
        n.err = err
        
        header = '[GNUPG:] '
        for l in out:
            if not l.startswith(header):
                continue

            l = l[len(header):]
            l = l.strip('\n')

            # str.partition() would be better, 2.5 only though
            s = l.find(' ')
            key = l[:s]
            if key in cls.uidkeys:
                # value is "keyid UID", don't split UID
                value = l[s+1:].split(' ', 1)
            else:
                value = l[s+1:].split(' ')

            # Skip headers in the gpgv output that are not interesting
            # note NEWSI is actually NEWSIG but the above parsing loses the 'G'
            # if no keyid is included in the message. See
            # /usr/share/doc/gnupg/DETAILS.gz
            if key in ('NEWSI', 'NEWSIG', 'KEY_CONSIDERED', 'PROGRESS'):
                continue

            n[key] = value
        return n 

    @classmethod
    def from_sequence(cls, sequence, keyrings=None, executable=None):
        """Create a new GpgInfo object from the given sequence.

        :param sequence: sequence of lines of bytes or a single byte string

        :param keyrings: list of keyrings to use (default:
            ['/usr/share/keyrings/debian-keyring.gpg'])

        :param executable: list of args for subprocess.Popen, the first element
            being the gpgv executable (default: ['/usr/bin/gpgv'])
        """

        keyrings = keyrings or GPGV_DEFAULT_KEYRINGS
        executable = executable or [GPGV_EXECUTABLE]

        # XXX check for gpg as well and use --verify accordingly?
        args = list(executable)
        #args.extend(["--status-fd", "1", "--no-default-keyring"])
        args.extend(["--status-fd", "1"])
        for k in keyrings:
            args.extend(["--keyring", k])
        
        if "--keyring" not in args:
            raise IOError("cannot access any of the given keyrings")

        p = subprocess.Popen(args, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=False)
        # XXX what to do with exit code?

        if isinstance(sequence, bytes):
            inp = sequence
        else:
            inp = cls._get_full_bytes(sequence)
        out, err = p.communicate(inp)

        return cls.from_output(out.decode('utf-8'),
                               err.decode('utf-8'))

    @staticmethod
    def _get_full_bytes(sequence):
        """Return a byte string from a sequence of lines of bytes.

        This method detects if the sequence's lines are newline-terminated, and
        constructs the byte string appropriately.
        """
        # Peek at the first line to see if it's newline-terminated.
        sequence_iter = iter(sequence)
        try:
            first_line = next(sequence_iter)
        except StopIteration:
            return b""
        join_str = b'\n'
        if first_line.endswith(b'\n'):
            join_str = b''
        return first_line + join_str + join_str.join(sequence_iter)

    @classmethod
    def from_file(cls, target, *args, **kwargs):
        """Create a new GpgInfo object from the given file.

        See GpgInfo.from_sequence.
        """
        with open(target, 'rb') as target_file:
            return cls.from_sequence(target_file, *args, **kwargs)


class PkgRelation(object):
    """Inter-package relationships

    Structured representation of the relationships of a package to another,
    i.e. of what can appear in a Deb882 field like Depends, Recommends,
    Suggests, ... (see Debian Policy 7.1).
    """

    # XXX *NOT* a real dependency parser, and that is not even a goal here, we
    # just parse as much as we need to split the various parts composing a
    # dependency, checking their correctness wrt policy is out of scope
    __dep_RE = re.compile(
            r'^\s*(?P<name>[a-zA-Z0-9.+\-]{2,})'
            r'(:(?P<archqual>([a-zA-Z0-9][a-zA-Z0-9-]*)))?'
            r'(\s*\(\s*(?P<relop>[>=<]+)\s*'
            r'(?P<version>[0-9a-zA-Z:\-+~.]+)\s*\))?'
            r'(\s*\[(?P<archs>[\s!\w\-]+)\])?\s*'
            r'((?P<restrictions><.+>))?\s*'
            r'$')
    __comma_sep_RE = re.compile(r'\s*,\s*')
    __pipe_sep_RE = re.compile(r'\s*\|\s*')
    __blank_sep_RE = re.compile(r'\s+')
    __restriction_sep_RE = re.compile(r'>\s*<')
    __restriction_RE = re.compile(
            r'(?P<enabled>\!)?'
            r'(?P<profile>[^\s]+)')

    ArchRestriction = collections.namedtuple('ArchRestriction',
            ['enabled', 'arch'])
    BuildRestriction = collections.namedtuple('BuildRestriction',
            ['enabled', 'profile'])

    @classmethod
    def parse_relations(cls, raw):
        """Parse a package relationship string (i.e. the value of a field like
        Depends, Recommends, Build-Depends ...)
        """
        def parse_archs(raw):
            # assumption: no space between '!' and architecture name
            archs = []
            for arch in cls.__blank_sep_RE.split(raw.strip()):
                disabled = arch[0] == '!'
                if disabled:
                    arch = arch[1:]
                archs.append(cls.ArchRestriction(not disabled, arch))
            return archs

        def parse_restrictions(raw):
            """ split a restriction formula into a list of restriction lists

            Each term in the restriction list is a namedtuple of form:

                (enabled, label)

            where
                enabled: boolean: whether the restriction is positive or negative
                profile: the profile name of the term e.g. 'stage1'
            """
            restrictions = []
            for rgrp in cls.__restriction_sep_RE.split(raw.lower().strip('<> ')):
                group = []
                for restriction in cls.__blank_sep_RE.split(rgrp):
                    match = cls.__restriction_RE.match(restriction)
                    if match:
                        parts = match.groupdict()
                        group.append(cls.BuildRestriction(
                                        parts['enabled'] != '!',
                                        parts['profile'],
                                    ))
                restrictions.append(group)
            return restrictions


        def parse_rel(raw):
            match = cls.__dep_RE.match(raw)
            if match:
                parts = match.groupdict()
                d = {
                        'name': parts['name'],
                        'archqual': parts['archqual'],
                        'version': None,
                        'arch': None,
                        'restrictions': None,
                    }
                if parts['relop'] or parts['version']:
                    d['version'] = (parts['relop'], parts['version'])
                if parts['archs']:
                    d['arch'] = parse_archs(parts['archs'])
                if parts['restrictions']:
                    d['restrictions'] = parse_restrictions(parts['restrictions'])
                return d
            else:
                warnings.warn('cannot parse package' \
                      ' relationship "%s", returning it raw' % raw)
                return { 'name': raw, 'version': None, 'arch': None }

        tl_deps = cls.__comma_sep_RE.split(raw.strip()) # top-level deps
        cnf = map(cls.__pipe_sep_RE.split, tl_deps)
        return [[parse_rel(or_dep) for or_dep in or_deps] for or_deps in cnf]

    @staticmethod
    def str(rels):
        """Format to string structured inter-package relationships
        
        Perform the inverse operation of parse_relations, returning a string
        suitable to be written in a package stanza.
        """
        def pp_arch(arch_spec):
            return '%s%s' % (
                    '' if arch_spec.enabled else '!',
                    arch_spec.arch,
                )

        def pp_restrictions(restrictions):
            s = []
            for term in restrictions:
                s.append('%s%s' % (
                            '' if term.enabled else '!',
                            term.profile
                        )
                    )
            return '<%s>' % ' '.join(s)

        def pp_atomic_dep(dep):
            s = dep['name']
            if dep.get('archqual') is not None:
                s += ':%s' % dep['archqual']
            if dep.get('version') is not None:
                s += ' (%s %s)' % dep['version']
            if dep.get('arch') is not None:
                s += ' [%s]' % ' '.join(map(pp_arch, dep['arch']))
            if dep.get('restrictions') is not None:
                s += ' %s' % ' '.join(map(pp_restrictions, dep['restrictions']))
            return s

        pp_or_dep = lambda deps: ' | '.join(map(pp_atomic_dep, deps))
        return ', '.join(map(pp_or_dep, rels))


class _lowercase_dict(dict):
    """Dictionary wrapper which lowercase keys upon lookup."""

    def __getitem__(self, key):
        return dict.__getitem__(self, key.lower())


class _PkgRelationMixin(object):
    """Package relationship mixin

    Inheriting from this mixin you can extend a Deb882 object with attributes
    letting you access inter-package relationship in a structured way, rather
    than as strings. For example, while you can usually use pkg['depends'] to
    obtain the Depends string of package pkg, mixing in with this class you
    gain pkg.depends to access Depends as a Pkgrel instance

    To use, subclass _PkgRelationMixin from a class with a _relationship_fields
    attribute. It should be a list of field names for which structured access
    is desired; for each of them a method wild be added to the inherited class.
    The method name will be the lowercase version of field name; '-' will be
    mangled as '_'. The method would return relationships in the same format of
    the PkgRelation' relations property.

    See Packages and Sources as examples.
    """

    def __init__(self, *args, **kwargs):
        self.__relations = _lowercase_dict({})
        self.__parsed_relations = False
        for name in self._relationship_fields:
            # To avoid reimplementing Deb822 key lookup logic we use a really
            # simple dict subclass which just lowercase keys upon lookup. Since
            # dictionary building happens only here, we ensure that all keys
            # are in fact lowercase.
            # With this trick we enable users to use the same key (i.e. field
            # name) of Deb822 objects on the dictionary returned by the
            # relations property.
            keyname = name.lower()
            if name in self:
                self.__relations[keyname] = None   # lazy value
                    # all lazy values will be expanded before setting
                    # __parsed_relations to True
            else:
                self.__relations[keyname] = []

    @property
    def relations(self):
        """Return a dictionary of inter-package relationships among the current
        and other packages.

        Dictionary keys depend on the package kind. Binary packages have keys
        like 'depends', 'recommends', ... while source packages have keys like
        'build-depends', 'build-depends-indep' and so on. See the Debian policy
        for the comprehensive field list.

        Dictionary values are package relationships returned as lists of lists
        of dictionaries (see below for some examples).

        The encoding of package relationships is as follows:
        - the top-level lists corresponds to the comma-separated list of
          Deb822, their components form a conjunction, i.e. they have to be
          AND-ed together
        - the inner lists corresponds to the pipe-separated list of Deb822,
          their components form a disjunction, i.e. they have to be OR-ed
          together
        - member of the inner lists are dictionaries with the following keys:
          - name:       package (or virtual package) name
          - version:    A pair <operator, version> if the relationship is
                        versioned, None otherwise. operator is one of "<<",
                        "<=", "=", ">=", ">>"; version is the given version as
                        a string.
          - arch:       A list of pairs <enabled, arch> if the
                        relationship is architecture specific, None otherwise.
                        Enabled is a boolean (false if the architecture is
                        negated with "!", true otherwise), arch the
                        Debian architecture name as a string.
          - restrictions: A list of lists of tuples <enabled, profile>
                        if there is a restriction formula defined, None
                        otherwise. Each list of tuples represents a restriction
                        list while each tuple represents an individual term
                        within the restriction list. Enabled is a boolean
                        (false if the restriction is negated with "!", true
                        otherwise). The profile is the name of the build
                        restriction.
                        https://wiki.debian.org/BuildProfileSpec

          The arch and restrictions tuples are available as named tuples so
          elements are available as term[0] or alternatively as
          term.enabled (and so forth).

        Examples:

          "emacs | emacsen, make, debianutils (>= 1.7)"     becomes
          [ [ {'name': 'emacs'}, {'name': 'emacsen'} ],
            [ {'name': 'make'} ],
            [ {'name': 'debianutils', 'version': ('>=', '1.7')} ] ]

          "tcl8.4-dev, procps [!hurd-i386]"                 becomes
          [ [ {'name': 'tcl8.4-dev'} ],
            [ {'name': 'procps', 'arch': (false, 'hurd-i386')} ] ]

          "texlive <!cross>"                                becomes
          [ [ {'name': 'texlive',
                    'restriction': [[(false, 'cross')]]} ] ]
        """
        if not self.__parsed_relations:
            lazy_rels = filter(lambda n: self.__relations[n] is None,
                    self.__relations.keys())
            for n in lazy_rels:
                self.__relations[n] = PkgRelation.parse_relations(self[n])
            self.__parsed_relations = True
        return self.__relations


class _multivalued(Deb822):
    """A class with (R/W) support for multivalued fields.

    To use, create a subclass with a _multivalued_fields attribute.  It should
    be a dictionary with *lower-case* keys, with lists of human-readable
    identifiers of the fields as the values.  Please see Dsc, Changes, and
    PdiffIndex as examples.
    """

    def __init__(self, *args, **kwargs):
        Deb822.__init__(self, *args, **kwargs)

        for field, fields in self._multivalued_fields.items():
            try:
                contents = self[field]
            except KeyError:
                continue

            if self.is_multi_line(contents):
                self[field] = []
                updater_method = self[field].append
            else:
                self[field] = Deb822Dict()
                updater_method = self[field].update

            for line in filter(None, contents.splitlines()):
                updater_method(Deb822Dict(zip(fields, line.split())))

    def validate_input(self, key, value):
        if key.lower() in self._multivalued_fields:
            # It's difficult to write a validator for multivalued fields, and
            # basically futile, since we allow mutable lists.  In any case,
            # with sanity checking in get_as_string, we shouldn't ever output
            # unparseable data.
            pass
        else:
            Deb822.validate_input(self, key, value)

    def get_as_string(self, key):
        keyl = key.lower()
        if keyl in self._multivalued_fields:
            fd = StringIO()
            if hasattr(self[key], 'keys'): # single-line
                array = [ self[key] ]
            else: # multi-line
                fd.write(six.u("\n"))
                array = self[key]

            order = self._multivalued_fields[keyl]
            try:
                field_lengths = self._fixed_field_lengths
            except AttributeError:
                field_lengths = {}
            for item in array:
                for x in order:
                    raw_value = six.text_type(item[x])
                    try:
                        length = field_lengths[keyl][x]
                    except KeyError:
                        value = raw_value
                    else:
                        value = (length - len(raw_value)) * " " + raw_value
                    if "\n" in value:
                        raise ValueError("'\\n' not allowed in component of "
                                         "multivalued field %s" % key)
                    fd.write(six.u(" %s") % value)
                fd.write(six.u("\n"))
            return fd.getvalue().rstrip("\n")
        else:
            return Deb822.get_as_string(self, key)


class _gpg_multivalued(_multivalued):
    """A _multivalued class that can support gpg signed objects

    This class's feature is that it stores the raw text before parsing so that
    gpg can verify the signature.  Use it just like you would use the
    _multivalued class.

    This class only stores raw text if it is given a raw string, or if it
    detects a gpg signature when given a file or sequence of lines (see
    Deb822.split_gpg_and_payload for details).
    """

    def __init__(self, *args, **kwargs):
        try:
            sequence = args[0]
        except IndexError:
            sequence = kwargs.get("sequence", None)

        if sequence is not None:
            # If the input is a unicode object or a file opened in text mode,
            # we'll need to encode it back to bytes for gpg.  If it's not
            # actually in the encoding that we guess, then this probably won't
            # verify correctly, but this is the best we can reasonably manage.
            # For accurate verification, the file should be opened in binary
            # mode.
            encoding = (getattr(sequence, 'encoding', None)
                        or kwargs.get('encoding', 'utf-8') or 'utf-8')
            if isinstance(sequence, bytes):
                self.raw_text = sequence
            elif isinstance(sequence, six.string_types):
                self.raw_text = sequence.encode(encoding)
            elif hasattr(sequence, "items"):
                # sequence is actually a dict(-like) object, so we don't have
                # the raw text.
                pass
            else:
                try:
                    gpg_pre_lines, lines, gpg_post_lines = \
                        self.split_gpg_and_payload(
                            self._bytes(s, encoding) for s in sequence)
                except EOFError:
                    # Empty input
                    gpg_pre_lines = lines = gpg_post_lines = []
                if gpg_pre_lines and gpg_post_lines:
                    raw_text = BytesIO()
                    raw_text.write(b"\n".join(gpg_pre_lines))
                    raw_text.write(b"\n\n")
                    raw_text.write(b"\n".join(lines))
                    raw_text.write(b"\n\n")
                    raw_text.write(b"\n".join(gpg_post_lines))
                    self.raw_text = raw_text.getvalue()
                try:
                    args = list(args)
                    args[0] = lines
                except IndexError:
                    kwargs["sequence"] = lines

        _multivalued.__init__(self, *args, **kwargs)

    @staticmethod
    def _bytes(s, encoding):
        """Converts s to bytes if necessary, using encoding.

        If s is already bytes type, returns it directly.
        """
        if isinstance(s, bytes):
            return s
        if isinstance(s, six.string_types):
            return s.encode(encoding)
        raise TypeError('bytes or unicode/string required, not %s' % type(s))


class Dsc(_gpg_multivalued):
    _multivalued_fields = {
        "files": [ "md5sum", "size", "name" ],
        "checksums-sha1": ["sha1", "size", "name"],
        "checksums-sha256": ["sha256", "size", "name"],
        "checksums-sha512": ["sha512", "size", "name"],
    }


class Changes(_gpg_multivalued):
    _multivalued_fields = {
        "files": [ "md5sum", "size", "section", "priority", "name" ],
        "checksums-sha1": ["sha1", "size", "name"],
        "checksums-sha256": ["sha256", "size", "name"],
        "checksums-sha512": ["sha512", "size", "name"],
    }

    def get_pool_path(self):
        """Return the path in the pool where the files would be installed"""
    
        # This is based on the section listed for the first file.  While
        # it is possible, I think, for a package to provide files in multiple
        # sections, I haven't seen it in practice.  In any case, this should
        # probably detect such a situation and complain, or return a list...
        
        s = self['files'][0]['section']

        try:
            section, subsection = s.split('/')
        except ValueError:
            # main is implicit
            section = 'main'

        if self['source'].startswith('lib'):
            subdir = self['source'][:4]
        else:
            subdir = self['source'][0]

        return 'pool/%s/%s/%s' % (section, subdir, self['source'])


class PdiffIndex(_multivalued):
    _multivalued_fields = {
        "sha1-current": [ "SHA1", "size" ],
        "sha1-history": [ "SHA1", "size", "date" ],
        "sha1-patches": [ "SHA1", "size", "date" ],
    }

    @property
    def _fixed_field_lengths(self):
        fixed_field_lengths = {}
        for key in self._multivalued_fields:
            if hasattr(self[key], 'keys'):
                # Not multi-line -- don't need to compute the field length for
                # this one
                continue
            length = self._get_size_field_length(key)
            fixed_field_lengths[key] = {"size": length}
        return fixed_field_lengths

    def _get_size_field_length(self, key):
        lengths = [len(str(item['size'])) for item in self[key]]
        return max(lengths)


class Release(_multivalued):
    """Represents a Release file

    Set the size_field_behavior attribute to "dak" to make the size field
    length only as long as the longest actual value.  The default,
    "apt-ftparchive" makes the field 16 characters long regardless.
    """
    # FIXME: Add support for detecting the behavior of the input, if
    # constructed from actual 822 text.

    _multivalued_fields = {
        "md5sum": [ "md5sum", "size", "name" ],
        "sha1": [ "sha1", "size", "name" ],
        "sha256": [ "sha256", "size", "name" ],
        "sha512": [ "sha512", "size", "name" ],
    }

    __size_field_behavior = "apt-ftparchive"
    def set_size_field_behavior(self, value):
        if value not in ["apt-ftparchive", "dak"]:
            raise ValueError("size_field_behavior must be either "
                             "'apt-ftparchive' or 'dak'")
        else:
            self.__size_field_behavior = value
    size_field_behavior = property(lambda self: self.__size_field_behavior,
                                   set_size_field_behavior)

    @property
    def _fixed_field_lengths(self):
        fixed_field_lengths = {}
        for key in self._multivalued_fields:
            length = self._get_size_field_length(key)
            fixed_field_lengths[key] = {"size": length}
        return fixed_field_lengths

    def _get_size_field_length(self, key):
        if self.size_field_behavior == "apt-ftparchive":
            return 16
        elif self.size_field_behavior == "dak":
            lengths = [len(str(item['size'])) for item in self[key]]
            return max(lengths)


class Sources(Dsc, _PkgRelationMixin):
    """Represent an APT source package list"""

    _relationship_fields = [ 'build-depends', 'build-depends-indep',
            'build-conflicts', 'build-conflicts-indep', 'binary' ]

    def __init__(self, *args, **kwargs):
        Dsc.__init__(self, *args, **kwargs)
        _PkgRelationMixin.__init__(self, *args, **kwargs)

    @classmethod
    def iter_paragraphs(cls, sequence, fields=None, use_apt_pkg=True,
                        shared_storage=False, encoding="utf-8"):
        """Generator that yields a Deb822 object for each paragraph in Sources.

        Note that this overloaded form of the generator uses apt_pkg (a strict
        but fast parser) by default.

        See the Deb822.iter_paragraphs function for details.
        """
        return super(Sources, cls).iter_paragraphs(sequence, fields,
                                    use_apt_pkg, shared_storage, encoding)


class Packages(Deb822, _PkgRelationMixin):
    """Represent an APT binary package list"""

    _relationship_fields = [ 'depends', 'pre-depends', 'recommends',
            'suggests', 'breaks', 'conflicts', 'provides', 'replaces',
            'enhances' ]

    def __init__(self, *args, **kwargs):
        Deb822.__init__(self, *args, **kwargs)
        _PkgRelationMixin.__init__(self, *args, **kwargs)

    @classmethod
    def iter_paragraphs(cls, sequence, fields=None, use_apt_pkg=True,
                        shared_storage=False, encoding="utf-8"):
        """Generator that yields a Deb822 object for each paragraph in Packages.

        Note that this overloaded form of the generator uses apt_pkg (a strict
        but fast parser) by default.

        See the Deb822.iter_paragraphs function for details.
        """
        return super(Packages, cls).iter_paragraphs(sequence, fields,
                                    use_apt_pkg, shared_storage, encoding)


class _ClassInitMeta(type):
    """Metaclass for classes that can be initialized at creation time.

    Implement the method

      @classmethod
      def _class_init(cls, new_attrs):
        pass

    on a class, and apply this metaclass to it.  The _class_init method will be
    called right after the class is created.  The 'new_attrs' param is a dict
    containing the attributes added in the definition of the class.
    """

    def __init__(cls, name, bases, attrs):
        super(_ClassInitMeta, cls).__init__(name, bases, attrs)
        cls._class_init(attrs)


class RestrictedField(collections.namedtuple(
        'RestrictedField', 'name from_str to_str allow_none')):
    """Placeholder for a property providing access to a restricted field.

    Use this as an attribute when defining a subclass of RestrictedWrapper.
    It will be replaced with a property.  See the RestrictedWrapper
    documentation for an example.
    """

    def __new__(cls, name, from_str=None, to_str=None, allow_none=True):
        """Create a new RestrictedField placeholder.

        The getter that will replace this returns (or applies the given to_str
        function to) None for fields that do not exist in the underlying data
        object.

        :param field_name: The name of the deb822 field.
        :param from_str: The function to apply for getters (default is to return
            the string directly).
        :param to_str: The function to apply for setters (default is to use the
            value directly).  If allow_none is True, this function may return
            None, in which case the underlying key is deleted.
        :param allow_none: Whether it is allowed to set the value to None
            (which results in the underlying key being deleted).
        """
        return super(RestrictedField, cls).__new__(
            cls, name, from_str=from_str, to_str=to_str,
            allow_none=allow_none)


@six.add_metaclass(_ClassInitMeta)
class RestrictedWrapper(object):
    """Base class to wrap a Deb822 object, restricting write access to some keys.

    The underlying data is hidden internally.  Subclasses may keep a reference
    to the data before giving it to this class's constructor, if necessary, but
    RestrictedProperty should cover most use-cases.  The dump method from
    Deb822 is directly proxied.

    Typical usage:

        class Foo(object):
            def __init__(self, ...):
                # ...

            @staticmethod
            def from_str(self, s):
                # Parse s...
                return Foo(...)

            def to_str(self):
                # Return in string format.
                return ...

        class MyClass(deb822.RestrictedWrapper):
            def __init__(self):
                data = deb822.Deb822()
                data['Bar'] = 'baz'
                super(MyClass, self).__init__(data)

            foo = deb822.RestrictedProperty(
                    'Foo', from_str=Foo.from_str, to_str=Foo.to_str)

            bar = deb822.RestrictedProperty('Bar', allow_none=False)

        d = MyClass()
        d['Bar'] # returns 'baz'
        d['Bar'] = 'quux' # raises RestrictedFieldError
        d.bar = 'quux'
        d.bar # returns 'quux'
        d['Bar'] # returns 'quux'

        d.foo = Foo(...)
        d['Foo'] # returns string representation of foo
    """

    @classmethod
    def _class_init(cls, new_attrs):
        restricted_fields = []
        for attr_name, val in new_attrs.items():
            if isinstance(val, RestrictedField):
                restricted_fields.append(val.name.lower())
                cls.__init_restricted_field(attr_name, val)
        cls.__restricted_fields = frozenset(restricted_fields)

    @classmethod
    def __init_restricted_field(cls, attr_name, field):
        def getter(self):
            val = self.__data.get(field.name)
            if field.from_str is not None:
                return field.from_str(val)
            return val

        def setter(self, val):
            if val is not None and field.to_str is not None:
                val = field.to_str(val)
            if val is None:
                if field.allow_none:
                    if field.name in self.__data:
                        del self.__data[field.name]
                else:
                    raise TypeError('value must not be None')
            else:
                self.__data[field.name] = val

        setattr(cls, attr_name, property(getter, setter, None, field.name))

    def __init__(self, data):
        """Initializes the wrapper over 'data', a Deb822 object."""
        super(RestrictedWrapper, self).__init__()
        self.__data = data

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        if key.lower() in self.__restricted_fields:
            raise RestrictedFieldError(
                '%s may not be modified directly; use the associated'
                ' property' % key)
        self.__data[key] = value

    def __delitem__(self, key):
        if key.lower() in self.__restricted_fields:
            raise RestrictedFieldError(
                '%s may not be modified directly; use the associated'
                ' property' % key)
        del self.__data[key]

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def dump(self, *args, **kwargs):
        """Calls dump() on the underlying data object.

        See Deb822.dump for more information.
        """
        return self.__data.dump(*args, **kwargs)


class Removals(Deb822):
    """Represent an ftp-master removals.822 file

    Removal of packages from the archive are recorded by ftp-masters.
    See https://ftp-master.debian.org/#removed

    Note: this API is experimental and backwards-incompatible changes might be
    required in the future. Please use it and help us improve it!
    """
    __sources_line_re = re.compile(r'\s*'
                            r'(?P<package>.+?)'
                            r'_'
                            r'(?P<version>[^\s]+)'
                            r'\s*'
                        )
    __binaries_line_re = re.compile(r'\s*'
                            r'(?P<package>.+?)'
                            r'_'
                            r'(?P<version>[^\s]+)'
                            r'\s+'
                            r'\[(?P<archs>.+)\]'
                        )

    @property
    def date(self):
        """ a datetime object for the removal action """
        ts = email.utils.mktime_tz(email.utils.parsedate_tz(self['date']))
        return datetime.datetime.fromtimestamp(ts)

    @property
    def bug(self):
        """ list of bug numbers that had requested the package removal

        The bug numbers are returned as integers.

        Note: there is normally only one entry in this list but there may be
        more than one.
        """
        if 'bug' not in self:
            return []
        return [int(b) for b in self['bug'].split(",")]

    @property
    def also_wnpp(self):
        """ list of WNPP bug numbers closed by the removal

        The bug numbers are returned as integers.
        """
        if 'also-wnpp' not in self:
            return []
        return [int(b) for b in self['also-wnpp'].split(" ")]

    @property
    def also_bugs(self):
        """ list of bug numbers in the package closed by the removal

        The bug numbers are returned as integers.

        Removal of a package implicitly also closes all bugs associated with
        the package.
        """
        if 'also-bugs' not in self:
            return []
        return [int(b) for b in self['also-bugs'].split(" ")]

    @property
    def sources(self):
        """ list of source packages that were removed

        A list of dicts is returned, each dict has the form:
            {
                'source': 'some-package-name',
                'version': '1.2.3-1'
            }

        Note: There may be no source packages removed at all if the removal is
        only of a binary package. An empty list is returned in that case.
        """
        if hasattr(self, '_sources'):
            return self._sources

        s = []
        if 'sources' in self:
            for line in self['sources'].splitlines():
                matches = self.__sources_line_re.match(line)
                if matches:
                    s.append({
                            'source': matches.group('package'),
                            'version': matches.group('version'),
                        })
        self._sources = s
        return s

    @property
    def binaries(self):
        """ list of binary packages that were removed

        A list of dicts is returned, each dict has the form:
            {
                'package': 'some-package-name',
                'version': '1.2.3-1',
                'architectures': set(['i386', 'amd64'])
            }
        """
        if hasattr(self, '_binaries'):
            return self._binaries

        b = []
        if 'binaries' in self:
            for line in self['binaries'].splitlines():
                matches = self.__binaries_line_re.match(line)
                if matches:
                    b.append({
                            'package': matches.group('package'),
                            'version': matches.group('version'),
                            'architectures':
                                    set(matches.group('archs').split(', ')),
                        })
        self._binaries = b
        return b


class _CaseInsensitiveString(str):
    """Case insensitive string.
    """

    def __new__(cls, str_):
        s = str.__new__(cls, str_)
        s.str_lower = str_.lower()
        s.str_lower_hash = hash(s.str_lower)
        return s

    def __hash__(self):
        return self.str_lower_hash

    def __eq__(self, other):
        return self.str_lower == other.lower()

    def lower(self):
        return self.str_lower


_strI = _CaseInsensitiveString
