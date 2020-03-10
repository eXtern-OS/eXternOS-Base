#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main loop for aptdaemon."""
# Copyright (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("mainloop", "get_main_loop")

from gi.repository import GLib

mainloop = GLib.MainLoop()


def get_main_loop():
    """Return the glib main loop as a singleton."""
    return mainloop

# vim:ts=4:sw=4:et
