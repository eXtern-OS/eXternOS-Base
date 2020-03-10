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
    'ComputerJanitorException',
    'UnimplementedMethod',
]


from janitor.plugincore.i18n import setup_gettext
_ = setup_gettext()


class ComputerJanitorException(Exception):
    """Base class for all Computer Janitor exceptions."""


class UnimplementedMethod(ComputerJanitorException, NotImplementedError):
    """A method expected by the Computer Janitor API is unimplemented."""

    def __init__(self, method):
        self._method = method

    def __str__(self):
        # Why do we use %s here instead of $strings or {} format placeholders?
        # It's because we don't want to break existing translations.
        return _('Unimplemented method: %s') % self._method.__name__
