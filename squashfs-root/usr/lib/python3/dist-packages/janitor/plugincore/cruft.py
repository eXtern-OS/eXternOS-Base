# Copyright (C) 2008-2012  Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'Cruft']


from janitor.plugincore.i18n import setup_gettext
_ = setup_gettext()


from janitor.plugincore.exceptions import UnimplementedMethod


class Cruft:
    """One piece of cruft to be cleaned out.

    A piece of cruft can be a file, a package, a configuration tweak that is
    missing, or something else.

    This is a base class, which does nothing. Subclasses do the actual work,
    though they must override the `get_shortname()` and `cleanup()` methods.
    """

    def get_prefix(self):
        """Return the unique prefix used to group this type of cruft.

        For example, the .deb package called 'foo' would have a prefix
        of 'deb'. This way, the package foo is not confused with the
        file foo, or the username foo.

        Subclasses SHOULD define this. The default implementation
        returns the name of the class, which is rarely useful to
        the user.
        """
        return self.__class__.__name__

    @property
    def prefix(self):
        return self.get_prefix()

    def get_prefix_description(self):
        """Return human-readable description of class of cruft."""
        return self.get_description()

    @property
    def prefix_description(self):
        return self.get_prefix_description()

    def get_shortname(self):
        """Return the name of this piece of cruft.

        The name should be something that the user will understand.  For
        example, it might be the name of a package, or the full path to a
        file.

        The name should be unique within the unique prefix returned by
        `get_prefix()`.  The prefix MUST NOT be included by this method, the
        `get_name()` method does that instead.  The intent is that
        `get_shortname()` will be used by the user interface in contexts where
        the prefix is shown separately from the short name, and `get_name()`
        when a single string is used.

        Subclasses MUST define this.  The default implementation raises an
        exception.
        """
        raise UnimplementedMethod(self.get_shortname)

    @property
    def shortname(self):
        return self.get_shortname()

    def get_name(self):
        """Return prefix plus name.

        See `get_prefix()` and `get_shortname()` for a discussion of the
        prefix and the short name.  This method will return the prefix, a
        colon, and the short name.

        The long name will used to store state/configuration data: _this_
        package should not be removed.
        """
        return '{}:{}'.format(self.prefix, self.shortname)

    @property
    def name(self):
        return self.get_name()

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self.name)

    def get_description(self):
        """Return a description of this piece of cruft.

        This may be arbitrarily long.  The user interface will take care of
        breaking it into lines or otherwise presenting it to the user in a
        nice manner.  The description should be plain text UTF-8 unicode.

        The default implementation returns the empty string.  Subclasses MAY
        override this as they wish.
        """
        return ''

    @property
    def description(self):
        return self.get_description()

    def get_disk_usage(self):
        """Return amount of disk space reserved by this piece of cruft.

        The unit is bytes.

        The disk space in question should be the amount that will be freed if
        the cruft is cleaned up.  The amount may be an estimate (i.e. a
        guess).  It is intended to be shown to the user to help them decide
        what to remove and what to keep.

        This will also be used by the user interface to better estimate how
        much remaining time there is when cleaning up a lot of cruft.

        For some types of cruft, this is not applicable and they should return
        `None`.  The base class implementation does that, so subclasses MUST
        define this method if it is useful for them to return something else.

        The user interface will distinguish between None (not applicable) and
        0 (no disk space being used).
        """
        return None

    @property
    def disk_usage(self):
        return self.get_disk_usage()

    def cleanup(self):
        """Clean up this piece of cruft.

        Depending on the type of cruft, this may mean removing files,
        packages, modifying configuration files, or something else.

        The default implementation raises an exception.  Subclasses MUST
        override this.
        """
        raise UnimplementedMethod(self.cleanup)
