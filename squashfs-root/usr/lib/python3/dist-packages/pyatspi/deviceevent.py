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

import pyatspi.registry as registry

from pyatspi.atspienum import *

import traceback

#------------------------------------------------------------------------------

class PressedEventType(AtspiEnum):
        _enum_lookup = {
                0:'KEY_PRESSED_EVENT',
                1:'KEY_RELEASED_EVENT',
                2:'BUTTON_PRESSED_EVENT',
                3:'BUTTON_RELEASED_EVENT',
        }

KEY_PRESSED_EVENT = PressedEventType(0)
KEY_RELEASED_EVENT = PressedEventType(1)
BUTTON_PRESSED_EVENT = PressedEventType(2)
BUTTON_RELEASED_EVENT = PressedEventType(3)

#------------------------------------------------------------------------------

class ControllerEventMask(AtspiEnum):
        _enum_lookup = {
                1:'KEY_PRESSED_EVENT_MASK',
                2:'KEY_RELEASED_EVENT_MASK',
                4:'BUTTON_PRESSED_EVENT_MASK',
                8:'BUTTON_RELEASED_EVENT_MASK',
        }

KEY_PRESSED_EVENT_MASK = ControllerEventMask(1)
KEY_RELEASED_EVENT_MASK = ControllerEventMask(2)
BUTTON_PRESSED_EVENT_MASK = ControllerEventMask(4)
BUTTON_RELEASED_EVENT_MASK = ControllerEventMask(8)

#------------------------------------------------------------------------------

class KeyEventType(AtspiEnum):
        _enum_lookup = {
                0:'KEY_PRESSED',
                1:'KEY_RELEASED',
        }
KEY_PRESSED = KeyEventType(0)
KEY_RELEASED = KeyEventType(1)

#------------------------------------------------------------------------------

class KeySynthType(AtspiEnum):
        _enum_lookup = {
                0:'KEY_PRESS',
                1:'KEY_RELEASE',
                2:'KEY_PRESSRELEASE',
                3:'KEY_SYM',
                4:'KEY_STRING',
        }

KEY_PRESS = KeySynthType(0)
KEY_PRESSRELEASE = KeySynthType(2)
KEY_RELEASE = KeySynthType(1)
KEY_STRING = KeySynthType(4)
KEY_SYM = KeySynthType(3)

#------------------------------------------------------------------------------

class ModifierType(AtspiEnum):
        _enum_lookup = {
                0:'MODIFIER_SHIFT',
                1:'MODIFIER_SHIFTLOCK',
                2:'MODIFIER_CONTROL',
                3:'MODIFIER_ALT',
                4:'MODIFIER_META',
                5:'MODIFIER_META2',
                6:'MODIFIER_META3',
                7:'MODIFIER_NUMLOCK',
        }

MODIFIER_ALT = ModifierType(3)
MODIFIER_CONTROL = ModifierType(2)
MODIFIER_META = ModifierType(4)
MODIFIER_META2 = ModifierType(5)
MODIFIER_META3 = ModifierType(6)
MODIFIER_NUMLOCK = ModifierType(7)
MODIFIER_SHIFT = ModifierType(0)
MODIFIER_SHIFTLOCK = ModifierType(1)

def allModifiers():
        """
        Generates all possible keyboard modifiers for use with 
        L{registry.Registry.registerKeystrokeListener}.
        """
        mask = 0
        while mask <= (1 << MODIFIER_NUMLOCK):
                yield mask
                mask += 1

#------------------------------------------------------------------------------

class DeviceEvent(list):
        """
        Wraps an AT-SPI device event with a more Pythonic interface. Primarily adds
        a consume attribute which can be used to cease propagation of a device event.

        @ivar consume: Should this event be consumed and not allowed to pass on to
                observers further down the dispatch chain in this process or possibly
                system wide?
        @type consume: boolean
        @ivar type: Kind of event, KEY_PRESSED_EVENT or KEY_RELEASED_EVENT
        @type type: Accessibility.EventType
        @ivar id: Serial identifier for this key event
        @type id: integer
        @ivar hw_code: Hardware scan code for the key
        @type hw_code: integer
        @ivar modifiers: Modifiers held at the time of the key event
        @type modifiers: integer
        @ivar timestamp: Time at which the event occurred relative to some platform
                dependent starting point (e.g. XWindows start time)
        @type timestamp: integer
        @ivar event_string: String describing the key pressed (e.g. keysym)
        @type event_string: string
        @ivar is_text: Is the event representative of text to be inserted (True), or 
                of a control key (False)?
        @type is_text: boolean
        """
        def __new__(cls, type, id, hw_code, modifiers, timestamp, event_string, is_text):
                return list.__new__(cls, (type, id, hw_code, modifiers, timestamp, event_string, is_text))
        def __init__(self, type, id, hw_code, modifiers, timestamp, event_string, is_text):
                list.__init__(self, (type, id, hw_code, modifiers, timestamp, event_string, is_text))
                self.consume = False
        def _get_type(self):
                return self[0]
        def _set_type(self, val):
                self[0] = val
        type = property(fget=_get_type, fset=_set_type)
        def _get_id(self):
                return self[1]
        def _set_id(self, val):
                self[1] = val
        id = property(fget=_get_id, fset=_set_id)
        def _get_hw_code(self):
                return self[2]
        def _set_hw_code(self, val):
                self[2] = val
        hw_code = property(fget=_get_hw_code, fset=_set_hw_code)
        def _get_modifiers(self):
                return self[3]
        def _set_modifiers(self, val):
                self[3] = val
        modifiers = property(fget=_get_modifiers, fset=_set_modifiers)
        def _get_timestamp(self):
                return self[4]
        def _set_timestamp(self, val):
                self[4] = val
        timestamp = property(fget=_get_timestamp, fset=_set_timestamp)
        def _get_event_string(self):
                return self[5]
        def _set_event_string(self, val):
                self[5] = val
        event_string = property(fget=_get_event_string, fset=_set_event_string)
        def _get_is_text(self):
                return self[6]
        def _set_is_text(self, val):
                self[6] = val
        is_text = property(fget=_get_is_text, fset=_set_is_text)

        def __str__(self):
                """
                Builds a human readable representation of the event.

                @return: Event description
                @rtype: string
                """
                import constants
                if self.type == constants.KEY_PRESSED_EVENT:
                        kind = 'pressed'
                elif self.type == constants.KEY_RELEASED_EVENT:
                        kind = 'released'
                return """\
%s
\thw_code: %d
\tevent_string: %s
\tmodifiers: %d
\tid: %d
\ttimestamp: %d
\tis_text: %s""" % (kind, self.hw_code, self.event_string, self.modifiers,
                self.id, self.timestamp, self.is_text)

#------------------------------------------------------------------------------

class EventListenerMode(list):
        def __new__(cls, synchronous, preemptive, global_):
                return list.__new__(cls, (synchronous, preemptive, global_))
        def __init__(self, synchronous, preemptive, global_):
                list.__init__(self, (synchronous, preemptive, global_))
        def _get_synchronous(self):
                return self[0]
        def _set_synchronous(self, val):
                self[0] = val
        synchronous = property(fget=_get_synchronous, fset=_set_synchronous)
        def _get_preemptive(self):
                return self[1]
        def _set_preemptive(self, val):
                self[1] = val
        preemptive = property(fget=_get_preemptive, fset=_set_preemptive)
        def _get_global_(self):
                return self[2]
        def _set_global_(self, val):
                self[2] = val
        global_ = property(fget=_get_global_, fset=_set_global_)

#------------------------------------------------------------------------------

class KeyDefinition(list):
        def __new__(cls, keycode, keysym, keystring, unused):
                return list.__new__(cls, (keycode, keysym, keystring, unused))
        def __init__(self, keycode, keysym, keystring, unused):
                list.__init__(self, (keycode, keysym, keystring, unused))
        def _get_keycode(self):
                return self[0]
        def _set_keycode(self, val):
                self[0] = val
        keycode = property(fget=_get_keycode, fset=_set_keycode)
        def _get_keysym(self):
                return self[1]
        def _set_keysym(self, val):
                self[1] = val
        keysym = property(fget=_get_keysym, fset=_set_keysym)
        def _get_keystring(self):
                return self[2]
        def _set_keystring(self, val):
                self[2] = val
        keystring = property(fget=_get_keystring, fset=_set_keystring)
        def _get_unused(self):
                return self[3]
        def _set_unused(self, val):
                self[3] = val
        unused = property(fget=_get_unused, fset=_set_unused)
