#Copyright (C) 2010 Novell, Inc.
#Copyright (C) 2008 Codethink Ltd
#copyright: Copyright (c) 2005, 2007 IBM Corporation

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

#Portions of this code originally licensed and copyright (c) 2005, 2007
#IBM Corporation under the BSD license, available at
#U{http://www.opensource.org/licenses/bsd-license.php}

#authors: Peter Parente, Mark Doffman

#------------------------------------------------------------------------------

__all__ = ["Registry",
           "MAIN_LOOP_GLIB",
           "MAIN_LOOP_NONE",
           "set_default_registry"]

import os as _os
from gi.repository import Atspi
from gi.repository import GLib
import time

#------------------------------------------------------------------------------

MAIN_LOOP_GLIB = 'GLib'
MAIN_LOOP_QT   = 'Qt'
MAIN_LOOP_NONE = 'None'

#------------------------------------------------------------------------------

class Registry(object):
        """
        Wraps the Accessibility.Registry to provide more Pythonic registration for
        events.

        This object should be treated as a singleton, but such treatment is not
        enforced. You can construct another instance of this object and give it a
        reference to the Accessibility.Registry singleton. Doing so is harmless and
        has no point.

        @@ivar async: Should event dispatch to local listeners be decoupled from event
                receiving from the registry?
        @@type async: boolean
        @@ivar reg: Reference to the real, wrapped registry object
        @@type reg: Accessibility.Registry
        @@ivar dev: Reference to the device controller
        @@type dev: Accessibility.DeviceEventController
        @@ivar clients: Map of event names to client listeners
        @@type clients: dictionary
        @@ivar observers: Map of event names to AT-SPI L{_Observer} objects
        @@type observers: dictionary
        """
        __shared_state = {}

        def __init__(self):
                self.__dict__ = self.__shared_state

                try:
                        if (self.has_implementations):
                                return
                except (AttributeError):
                        pass

                self.has_implementations = False

                self.device_event_register = None
                self.app_event_register = None
                self.desktop = None

                self.main_loop = GLib.MainLoop()

        def __call__(self):
                """
                @@return: This instance of the registry
                @@rtype: L{Registry}
                """
                return self

        def _set_registry (self, main_loop_type, app_name=None):
                """
                Creates a new 'Registry' object and sets this object
                as the default returned by pyatspi.Registry.

                The default registry (without calling this function) uses the
                GLib main loop with caching. It connects to a registry daemon.

                This function should be called before pyatspi is used if you
                wish to change these defaults.

                @@param main_loop_type: 'GLib', 'None' or 'Qt'. If 'None' is selected then caching
                                       is disabled.

                @@param use_registry: Whether to connect to a registry daemon for device events.
                                     Without this the application to connect to must be declared in the
                                     app_name parameter.

                @@param app_name: D-Bus name of the application to connect to when not using the registry daemon.
                """

                self.has_implementations = True

                self.async = False	# not fully supported yet
                self.started = False
                self.event_listeners = dict()

        def _set_default_registry (self):
                self._set_registry (MAIN_LOOP_GLIB)

        def start(self, async=False, gil=True):
                """
                Enter the main loop to start receiving and dispatching events.

                @@param async: Should event dispatch be asynchronous (decoupled) from 
                        event receiving from the AT-SPI registry?
                @@type async: boolean
                @@param gil: Add an idle callback which releases the Python GIL for a few
                        milliseconds to allow other threads to run? Necessary if other threads
                        will be used in this process.
                @@type gil: boolean
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                self.started = True

                if gil:
                        def releaseGIL():
                                try:
                                        time.sleep(1e-2)
                                except KeyboardInterrupt as e:
                                        # store the exception for later
                                        releaseGIL.keyboard_exception = e
                                        self.stop()
                                return True
                        # make room for an exception if one occurs during the 
                        releaseGIL.keyboard_exception = None
                        i = GLib.idle_add(releaseGIL)
                        Atspi.event_main()
                        GLib.source_remove(i)
                        if releaseGIL.keyboard_exception is not None:
                                # raise an keyboard exception we may have gotten earlier
                                raise releaseGIL.keyboard_exception
                else:
                        Atspi.event_main()

                self.started = False

        def stop(self, *args):
                """
                Quits the main loop.
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                Atspi.event_quit()

        def getDesktopCount(self):
                """
                Gets the number of available desktops.

                @@return: Number of desktops
                @@rtype: integer
                """
                return 1

        def getDesktop(self, i):
                """
                Gets a reference to the i-th desktop.

                @@param i: Which desktop to get
                @@type i: integer
                @@return: Desktop reference
                @@rtype: Accessibility.Desktop
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                return Atspi.get_desktop(i)

        def eventWrapper(self, event, callback):
                return callback(event)

        def registerEventListener(self, client, *names):
                """
                Registers a new client callback for the given event names. Supports 
                registration for all subevents if only partial event name is specified.
                Do not include a trailing colon.

                For example, 'object' will register for all object events, 
                'object:property-change' will register for all property change events,
                and 'object:property-change:accessible-parent' will register only for the
                parent property change event.

                Registered clients will not be automatically removed when the client dies.
                To ensure the client is properly garbage collected, call 
                L{deregisterEventListener}.

                @@param client: Callable to be invoked when the event occurs
                @@type client: callable
                @@param names: List of full or partial event names
                @@type names: list of string
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                try:
                        listener = self.event_listeners[client]
                except:
                        listener = self.event_listeners[client] = Atspi.EventListener.new(self.eventWrapper, client)
                for name in names:
                        Atspi.EventListener.register (listener, name)

        def deregisterEventListener(self, client, *names):
                """
                Unregisters an existing client callback for the given event names. Supports 
                unregistration for all subevents if only partial event name is specified.
                Do not include a trailing colon.

                This method must be called to ensure a client registered by
                L{registerEventListener} is properly garbage collected.

                @@param client: Client callback to remove
                @@type client: callable
                @@param names: List of full or partial event names
                @@type names: list of string
                @@return: Were event names specified for which the given client was not
                        registered?
                @@rtype: boolean
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                try:
                        listener = self.event_listeners[client]
                except:
                        return
                for name in names:
                        Atspi.EventListener.deregister(listener, name)

        # -------------------------------------------------------------------------------

        # TODO: Remove this hack
        _KEY_PRESSED_EVENT=1
        _KEY_RELEASED_EVENT=2

        def makeSyncType(self, synchronous, preemptive, global_):
                result = Atspi.KeyListenerSyncType.NOSYNC
                if synchronous:
                        result |= Atspi.KeyListenerSyncType.SYNCHRONOUS
                if preemptive:
                        result |= Atspi.KeyListenerSyncType.CANCONSUME
                if global_:
                        result |= Atspi.KeyListenerSyncType.ALL_WINDOWS
                return result

        def makeKind(self, kind):
                result = 0
                for i in kind:
                        result |= (1 << i)
                return result

        def registerKeystrokeListener(self,
                                      client,
                                      key_set=[],
                                      mask=0,
                                      kind=(_KEY_PRESSED_EVENT, _KEY_RELEASED_EVENT),
                                      synchronous=True,
                                      preemptive=True,
                                      global_=False):
                """
                Registers a listener for key stroke events.

                @@param client: Callable to be invoked when the event occurs
                @@type client: callable
                @@param key_set: Set of hardware key codes to stop monitoring. Leave empty
                        to indicate all keys.
                @@type key_set: list of integer
                @@param mask: When the mask is None, the codes in the key_set will be 
                        monitored only when no modifier is held. When the mask is an 
                        integer, keys in the key_set will be monitored only when the modifiers in
                        the mask are held. When the mask is an iterable over more than one 
                        integer, keys in the key_set will be monitored when any of the modifier
                        combinations in the set are held.
                @@type mask: integer, iterable, None
                @@param kind: Kind of events to watch, KEY_PRESSED_EVENT or 
                        KEY_RELEASED_EVENT.
                @@type kind: list
                @@param synchronous: Should the callback notification be synchronous, giving
                        the client the chance to consume the event?
                @@type synchronous: boolean
                @@param preemptive: Should the callback be allowed to preempt / consume the
                        event?
                @@type preemptive: boolean
                @@param global_: Should callback occur even if an application not supporting
                        AT-SPI is in the foreground? (requires xevie)
                @@type global_: boolean
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                try:
                        listener = self.event_listeners[client]
                except:
                        listener = self.event_listeners[client] = Atspi.DeviceListener.new(self.eventWrapper, client)
                syncFlag = self.makeSyncType(synchronous, preemptive, global_)
                if hasattr(mask, '__iter__'):
                        masks = mask
                else:
                        masks = [mask]
                for m in masks:
                        Atspi.register_keystroke_listener(listener,
                                                          key_set,
                                                          m,
                                                          self.makeKind (kind),
                                                          syncFlag)

        def deregisterKeystrokeListener(self,
                                        client,
                                        key_set=[],
                                        mask=0,
                                        kind=(_KEY_PRESSED_EVENT, _KEY_RELEASED_EVENT)):
                """
                Deregisters a listener for key stroke events.

                @@param client: Callable to be invoked when the event occurs
                @@type client: callable
                @@param key_set: Set of hardware key codes to stop monitoring. Leave empty
                        to indicate all keys.
                @@type key_set: list of integer
                @@param mask: When the mask is None, the codes in the key_set will be 
                        monitored only when no modifier is held. When the mask is an 
                        integer, keys in the key_set will be monitored only when the modifiers in
                        the mask are held. When the mask is an iterable over more than one 
                        integer, keys in the key_set will be monitored when any of the modifier
                        combinations in the set are held.
                @@type mask: integer, iterable, None
                @@param kind: Kind of events to stop watching, KEY_PRESSED_EVENT or 
                        KEY_RELEASED_EVENT.
                @@type kind: list
                @@raise KeyError: When the client isn't already registered for events
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                try:
                        listener = self.event_listeners[client]
                except:
                        return

                if hasattr(mask, '__iter__'):
                        masks = mask
                else:
                        masks = [mask]
                for m in masks:
                        Atspi.deregister_keystroke_listener (listener, key_set,
                                m, self.makeKind(kind))

                # TODO: enqueueEvent, etc?

        def generateKeyboardEvent(self, keycode, keysym, kind):
                """
                Generates a keyboard event. One of the keycode or the keysym parameters
                should be specified and the other should be None. The kind parameter is 
                required and should be one of the KEY_PRESS, KEY_RELEASE, KEY_PRESSRELEASE,
                KEY_SYM, or KEY_STRING.

                @@param keycode: Hardware keycode or None
                @@type keycode: integer
                @@param keysym: Symbolic key string or None
                @@type keysym: string
                @@param kind: Kind of event to synthesize
                @@type kind: integer
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                if keysym is None:
                        keysym = ""
                Atspi.generate_keyboard_event (keycode, keysym, kind)

        def generateMouseEvent(self, x, y, name):
                """
                Generates a mouse event at the given absolute x and y coordinate. The kind
                of event generated is specified by the name. For example, MOUSE_B1P 
                (button 1 press), MOUSE_REL (relative motion), MOUSE_B3D (butten 3 
                double-click).

                @@param x: Horizontal coordinate, usually left-hand oriented
                @@type x: integer
                @@param y: Vertical coordinate, usually left-hand oriented
                @@type y: integer
                @@param name: Name of the event to generate
                @@type name: string
                """
                if not self.has_implementations:
                        self._set_default_registry ()
                Atspi.generate_mouse_event (x, y, name)


        def pumpQueuedEvents (self):
                """
                Dispatch events that have been queued.
                """
                pass

def set_default_registry (main_loop, app_name=None):
        registry = Registry ()
        registry._set_registry (main_loop, app_name)
