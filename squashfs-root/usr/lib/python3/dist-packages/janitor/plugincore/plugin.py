# Copyright (C) 2008-2012  Canonical, Ltd.
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
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
    'Plugin',
]


from janitor.plugincore.exceptions import UnimplementedMethod


class Plugin:
    """Base class for plugins.

    These plugins only do one thing: identify cruft. See the 'get_cruft'
    method for details.
    """

    # XXX BAW 2012-06-08: For historical reasons, we do not set
    # self._condition or self.app in a constructor.  This needs to be fixed.

    @property
    def condition(self):
        return (self._condition if hasattr(self, '_condition') else [])

    @condition.setter
    def condition(self, condition):
        self._condition = condition

    def set_application(self, app):
        """Set the Application instance this plugin belongs to."""
        self.app = app

    def do_cleanup_cruft(self):
        """Find cruft and clean it up.

        This is a helper method.
        """
        for cruft in self.get_cruft():
            cruft.cleanup()
        self.post_cleanup()

    def get_cruft(self):
        """Find some cruft in the system.

        This method MUST return an iterator (see 'yield' statement).
        This interface design allows cruft to be collected piecemeal,
        which makes it easier to show progress in the user interface.

        The base class default implementation of this raises an
        exception. Subclasses MUST override this method.
        """
        raise UnimplementedMethod(self.get_cruft)

    @property
    def cruft(self):
        for cruft in self.get_cruft():
            yield cruft

    def post_cleanup(self):
        """Do plugin-wide cleanup after the individual cleanup was performed.

        This is useful for stuff that needs to be processed in batches
        (e.g. for performance reasons) like package removal.
        """
        pass
