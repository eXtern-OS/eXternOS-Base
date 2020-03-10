#    Gedit snippets plugin
#    Copyright (C) 2005-2006  Jesse van den Kieboom <jesse@icecrew.nl>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from gi.repository import GtkSource
import os

from .library import Library

global manager
manager = None

def get_language_manager():
    global manager

    if not manager:
        dirs = []

        for d in Library().systemdirs:
            dirs.append(os.path.join(d, 'lang'))

        manager = GtkSource.LanguageManager()
        manager.set_search_path(dirs + manager.get_search_path())

    return manager

# ex:ts=4:et:
