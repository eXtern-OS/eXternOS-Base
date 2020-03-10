#  Copyright (c) 2004-2007 Canonical
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

from __future__ import absolute_import

from gi.repository import GLib
from gi.repository import GObject
from .Core.MetaRelease import MetaReleaseCore


class MetaRelease(MetaReleaseCore, GObject.GObject):

    __gsignals__ = {
        'new_dist_available': (GObject.SignalFlags.RUN_LAST,
                               None,
                               (GObject.TYPE_PYOBJECT,)),
        'dist_no_longer_supported': (GObject.SignalFlags.RUN_LAST,
                                     None,
                                     ()),
        'done_downloading': (GObject.SignalFlags.RUN_LAST,
                             None,
                             ())
    }

    def __init__(self, useDevelopmentRelease=False, useProposed=False):
        GObject.GObject.__init__(self)
        MetaReleaseCore.__init__(self, useDevelopmentRelease, useProposed)
        # in the gtk space to test if the download already finished
        # this is needed because gtk is not thread-safe
        GLib.timeout_add_seconds(1, self.check)

    def check(self):
        # check if we have a metarelease_information file
        if self.no_longer_supported is not None:
            self.emit("dist_no_longer_supported")
        if self.new_dist is not None:
            self.emit("new_dist_available", self.new_dist)
        if self.downloading:
            return True
        else:
            self.emit("done_downloading")
            return False
