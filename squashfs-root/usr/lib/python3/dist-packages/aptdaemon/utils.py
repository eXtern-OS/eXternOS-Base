"""Module with little helper functions and classes:

deprecated - decorator to emit a warning if a depreacted function is used
"""
# Copyright (C) 2008-2009 Sebastian Heinlein <sevel@glatzor.de>
#
# Licensed under the GNU General Public License Version 2
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("deprecated", "IsoCodes")

import sys
import gettext
import functools
import warnings
from xml.etree import ElementTree

if sys.version >= '3':
    _gettext_method = "gettext"
else:
    _gettext_method = "ugettext"


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.

    Taken from http://wiki.python.org/moin/PythonDecoratorLibrary
    #GeneratingDeprecationWarnings
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(
            "Call to deprecated function %(funcname)s." % {
                'funcname': func.__name__,
            },
            category=DeprecationWarning,
            filename=func.__code__.co_filename,
            lineno=func.__code__.co_firstlineno + 1
        )
        return func(*args, **kwargs)
    return new_func


class IsoCodes(object):

    """Provides access to the iso-codes language, script and country
    database.
    """

    def __init__(self, norm, tag, fallback_tag=None):
        filename = "/usr/share/xml/iso-codes/%s.xml" % norm
        et = ElementTree.ElementTree(file=filename)
        self._dict = {}
        self.norm = norm
        for element in list(et.iter()):
            iso_code = element.get(tag)
            if not iso_code and fallback_tag:
                iso_code = element.get(fallback_tag)
            if iso_code:
                self._dict[iso_code] = element.get("name")

    def get_localised_name(self, value, locale):
        try:
            name = self._dict[value]
        except KeyError:
            return None
        trans = gettext.translation(domain=self.norm, fallback=True,
                                    languages=[locale])
        return getattr(trans, _gettext_method)(name)

    def get_name(self, value):
        try:
            return self._dict[value]
        except KeyError:
            return None


def split_package_id(package):
    """Return the name, the version number and the release of the
    specified package."""
    if "=" in package:
        name, version = package.split("=", 1)
        release = None
    elif "/" in package:
        name, release = package.split("/", 1)
        version = None
    else:
        name = package
        version = release = None
    return name, version, release


# vim:ts=4:sw=4:et
