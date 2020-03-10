# Orca
#
# Copyright (C) 2013-2014 Igalia, S.L.
#
# Author: Joanmarie Diggs <jdiggs@igalia.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., Franklin Street, Fifth Floor,
# Boston MA  02110-1301 USA.

__id__        = "$Id$"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2015 Canonical Ltd."
__license__   = "LGPL"

import pyatspi

import orca.orca as orca
import orca.scripts.default as default
import orca.speech as speech

from .script_utilities import Utilities

class Script(default.Script):

    def __init__(self, app):
        default.Script.__init__(self, app)

    def onActiveDescendantChanged(self, event):
        """Callback for object:active-descendant-changed accessibility events."""

        if not event.any_data:
            return

        # Unity's result accessible object does not technically get focus, so
        # we only check that its parent has focus.
        if not event.source.getState().contains(pyatspi.STATE_FOCUSED):
            return

        if self.stopSpeechOnActiveDescendantChanged(event):
            speech.stop()

        if event.source.getState().contains(pyatspi.STATE_MANAGES_DESCENDANTS) and \
           event.source.getRole() == pyatspi.ROLE_TOOL_BAR:
            orca.setLocusOfFocus(event, event.any_data, True, True)

    def locusOfFocusChanged(self, event, oldLocusOfFocus, newLocusOfFocus):
        if event.source.getState().contains(pyatspi.STATE_MANAGES_DESCENDANTS) and \
           event.source.getRole() == pyatspi.ROLE_TOOL_BAR:
            default.Script.locusOfFocusChanged(self, event, None, newLocusOfFocus)
        else:
            default.Script.locusOfFocusChanged(self, event, oldLocusOfFocus, newLocusOfFocus)

    def getUtilities(self):
        return Utilities(self)
