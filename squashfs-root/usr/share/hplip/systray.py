#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch

__version__ = '2.0'
__mod__ = 'hp-systray'
__title__ = 'System Tray Status Service'
__doc__ = "System Tray monitors the HP device status and Displays"

# StdLib
import sys
import os
import getopt
import signal

# Local
from base.g import *
from base import utils, module
from prnt import cups



if __name__ == '__main__':

    # Create a new session ID for the tray.  This disassociates the
    # tray from the controlling terminal so that it cannot receive
    # keyboard interrupts.
    #
    # Only do this if we aren't already a session leader.  This test
    # only succeeds if we are executed from hp-toolbox.
    if os.getpgid(os.getpid()) != os.getpid():
        os.setsid()

    mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                       (GUI_MODE,), (UI_TOOLKIT_QT5, UI_TOOLKIT_QT4, UI_TOOLKIT_QT3))

    mod.setUsage(module.USAGE_FLAG_NONE,
        extra_options=[("Startup even if no hplip CUPS queues are present:", "-x or --force-startup", "option", False)])

    opts, device_uri, printer_name, mode, ui_toolkit, lang = \
        mod.parseStdOpts('x', ['force-startup','ignore-update-firsttime'], False)
        # ignore-update-firsttime is required. ui/systemtray and ui4/systemtray will read this value using sys.args.

    force_startup = False
    for o, a in opts:
        if o in ('-x', '--force-startup'):
            force_startup = True

    if os.getuid() == 0:
        log.error("hp-systray cannot be run as root. Exiting.")
        sys.exit(1)

    if ui_toolkit == 'qt3':
        if not utils.canEnterGUIMode():
            log.error("%s requires Qt3 GUI and DBus support. Exiting." % __mod__)
            sys.exit(1)
    
    else:
        if not utils.canEnterGUIMode4():
            log.error("%s requires Qt4 GUI and DBus support. Exiting." % __mod__)
            sys.exit(1)

    if not force_startup:
        # Check for any hp: or hpfax: queues. If none, exit
        if not utils.any([p.device_uri for p in cups.getPrinters()], lambda x : x.startswith('hp')):
            log.warn("No hp: or hpfax: devices found in any installed CUPS queue. Exiting.")
            sys.exit(1)

    mod.lockInstance()
    
    r1, w1 = os.pipe()
    log.debug("Creating pipe: hpssd (%d) ==> systemtray (%d)" % (w1, r1))
    
    parent_pid = os.getpid()
    child_pid1 = os.fork()
    
    if child_pid1:
        # parent (UI)
        os.close(w1)

        if ui_toolkit == 'qt3':
            try:
                import ui.systemtray as systray
            except ImportError:
                log.error("Unable to load Qt3 support. Is it installed?")
                sys.exit(1)                  
        
        else: # qt4
            try:
                if ui_toolkit == "qt4":
                    import ui4.systemtray as systray
                elif ui_toolkit == "qt5":
                    import ui5.systemtray as systray
            except ImportError as e:
                log.error(e)
                log.error("Unable to load Qt4/Qt5 support. Is it installed?")
                mod.unlockInstance()
                sys.exit(1)        

        try:
            systray.run(r1)
        finally:
            mod.unlockInstance()

    else:
        # child (dbus & device i/o [qt4] or dbus [qt3])
        os.close(r1)

        if ui_toolkit in  ('qt4', 'qt5'):
            r2, w2 = os.pipe()
            r3, w3 = os.pipe()
            
            log.debug("Creating pipe: hpssd (%d) ==> hpdio (%d)" % (w2, r2))
            log.debug("Creating pipe: hpdio (%d) ==> hpssd (%d)" % (w3, r3))
            
            child_pid2 = os.fork()
            if child_pid2:
                # parent (dbus)
                os.close(r2)
                
                import hpssd
                hpssd.run(w1, w2, r3)
                        
            else:
                # child (device i/o)
                os.close(w2)
                
                import hpdio
                hpdio.run(r2, w3) 
                
        else: # qt3
            import hpssd
            hpssd.run(w1)
