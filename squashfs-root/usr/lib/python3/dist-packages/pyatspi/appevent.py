#Copyright (C) 2008 Codethink Ltd

#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License version 2 as published by the Free Software Foundation.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU Lesser General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import string

class _ELessList(list):
        def __getitem__(self, index):
                try:
                        return list.__getitem__(self, index)
                except IndexError:
                        return None

class EventType(str):
        """
        Wraps the AT-SPI event type string so its components can be accessed 
        individually as klass (can't use the keyword class), major, minor, and detail 
        (klass_major_minor_detail).

        @note: All attributes of an instance of this class should be considered 
                public readable as it is acting a a struct.
        @ivar klass: Most general event type identifier (object, window, mouse, etc.)
        @type klass: string
        @ivar major: Second level event type description
        @type major: string
        @ivar minor: Third level event type description
        @type minor: string
        @ivar detail: Lowest level event type description
        @type detail: string
        @ivar name: Full, unparsed event name as received from AT-SPI
        @type name: string
        @cvar format: Names of the event string components
        @type format: 4-tuple of string
        """

        _SEPARATOR = ':'

        def __init__(self, name):
                """
                Parses the full AT-SPI event name into its components
                (klass:major:minor:detail). If the provided event name is an integer
                instead of a string, then the event is really a device event.

                @param name: Full AT-SPI event name
                @type name: string
                @raise AttributeError: When the given event name is not a valid string 
                """
                stripped = name.strip(self._SEPARATOR)
                separated = stripped.split(self._SEPARATOR, 3)
                self._separated = _ELessList(separated)

                self.klass = self._separated[0]
                self.major = self._separated[1]
                self.minor = self._separated[2]
                self.detail = self._separated[3]

        def is_subtype(self, event_type, excludeSelf = False):
                """
                Determines if the passed event type is a subtype
                of this event.
                """
                if event_type.klass and event_type.klass !=  self.klass:
                        return False
                else:
                        if event_type.major and event_type.major != self.major:
                                return False
                        else:
                                if event_type.minor and event_type.minor != self.minor:
                                        return False
                if (excludeSelf and event_type.klass == self.klass
                    and event_type.major == self.major and event_type.minor == self.minor):
                        return False
                return True

        @property
        def name(self):
                return str(self)

        @property
        def value(self):
                return str(self)
