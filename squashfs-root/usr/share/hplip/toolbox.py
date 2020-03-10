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
#
# Thanks to Henrique M. Holschuh <hmh@debian.org> for various security patches
#

__version__ = '15.0'
__mod__ = 'hp-toolbox'
__title__ = 'HP Device Manager'
__doc__ = """The HP Device Manager (aka "Toolbox") for HPLIP supported devices. Provides access to status, tools, and supplies levels."""

# Std Lib
import sys
import os
import getopt
import signal


# Local
from base.g import *
#from . import base.utils as utils
import base.utils as utils
from base import status, tui, module

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from base.utils import dyn_import_mod as import_module


w = None # write pipe
app = None
toolbox  = None
session_bus = None


def handle_session_signal(*args, **kwds):
    if kwds['interface'] == 'com.hplip.Toolbox' and \
        kwds['member'] == 'Event':

        event = device.Event(*args)
        event.debug()

        if event.event_code > EVENT_MAX_EVENT:
            event.event_code = status.MapPJLErrorCode(event.event_code)

        # regular user/device status event
        log.debug("Received event notifier: %d" % event.event_code)

        if not event.send_via_pipe(w, 'toolbox ui'):
            sys.exit(1)
            # if this fails, then hp-toolbox must be killed.
            # No need to continue running...


mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                    (GUI_MODE,), (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5))
mod.lockInstance()

mod.setUsage(module.USAGE_FLAG_NONE,
             extra_options=[("Disable dbus (Qt3 only):", "-x or --disable-dbus", "option", False)],
             see_also_list = ['hp-align', 'hp-clean', 'hp-colorcal', 'hp-devicesettings',
                              'hp-faxsetup', 'hp-firmware', 'hp-info', 'hp-levels',
                              'hp-linefeedcal', 'hp-makecopies', 'hp-plugin',
                              'hp-pqdiag', 'hp-print', 'hp-printsettings', 'hp-scan',
                              'hp-sendfax', 'hp-testpage', 'hp-timedate', 'hp-unload'])

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts('x', ['disable-dbus'])

disable_dbus = False

for o, a in opts:
    if o in ('-x', '--disable-dbus') and ui_toolkit == 'qt3':
        disable_dbus = True

if ui_toolkit == 'qt3':
    if not utils.canEnterGUIMode():
        log.error("%s requires GUI support. Exiting." % __mod__)
        sys.exit(1)
elif ui_toolkit == 'qt4':
    if not utils.canEnterGUIMode4():
        log.error("%s requires GUI support. Exiting." % __mod__)
        sys.exit(1)

child_pid, w, r = 0, 0, 0

if ui_toolkit == 'qt3':
    try:
        from dbus import SessionBus
        import dbus.service
        from dbus.mainloop.glib import DBusGMainLoop, threads_init
        from gobject import MainLoop
        import glib
        glib.threads_init()
        dbus.mainloop.glib.threads_init()
    except ImportError:
        log.error("Unable to load dbus - Automatic status updates in HPLIP Device Manager will be disabled.")
        disable_dbus = True

    if not disable_dbus:
        r, w = os.pipe()
        parent_pid = os.getpid()
        log.debug("Parent PID=%d" % parent_pid)
        child_pid = os.fork()

    if disable_dbus or child_pid: # qt3/ui
        # parent (UI)
        log.set_module("hp-toolbox(UI)")

        if w:
            os.close(w)

        try:
            from qt import *
            from ui.devmgr4 import DevMgr4
        except ImportError:
            log.error("Unable to load Qt3 support. Is it installed?")
            sys.exit(1)

        # create the main application object
        app = QApplication(sys.argv)

        if loc is None:
            loc = user_conf.get('ui', 'loc', 'system')
            if loc.lower() == 'system':
                loc = str(QTextCodec.locale())
                log.debug("Using system locale: %s" % loc)

        if loc.lower() != 'c':
            e = 'utf8'
            try:
                l, x = loc.split('.')
                loc = '.'.join([l, e])
            except ValueError:
                l = loc
                loc = '.'.join([loc, e])

            log.debug("Trying to load .qm file for %s locale." % loc)
            trans = QTranslator(None)

            qm_file = 'hplip_%s.qm' % l
            log.debug("Name of .qm file: %s" % qm_file)
            loaded = trans.load(qm_file, prop.localization_dir)

            if loaded:
                app.installTranslator(trans)
            else:
                loc = 'c'

        if loc == 'c':
            log.debug("Using default 'C' locale")
        else:
            log.debug("Using locale: %s" % loc)
            QLocale.setDefault(QLocale(loc))
            prop.locale = loc
            try:
                locale.setlocale(locale.LC_ALL, locale.normalize(loc))
            except locale.Error:
                pass

        toolbox = DevMgr4(r, __version__, device_uri, disable_dbus)
        app.setMainWidget(toolbox)

        toolbox.show()

        try:
            try:
                log.debug("Starting GUI loop...")
                app.exec_loop()
            except KeyboardInterrupt:
                sys.exit(0)

        finally:
            if child_pid:
                log.debug("Killing child toolbox process (pid=%d)..." % child_pid)
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except OSError as e:
                    log.debug("Failed: %s" % e.message)

            mod.unlockInstance()
            sys.exit(0)

    elif not disable_dbus: # qt3/dbus
        # dBus
        log.set_module("hp-toolbox(dbus)")
        from base import device

        try:
            # child (dbus connector)
            os.close(r)

            dbus_loop = DBusGMainLoop(set_as_default=True)

            try:
                session_bus = dbus.SessionBus()
            except dbus.exceptions.DBusException as e:
                if os.getuid() != 0:
                    log.error("Unable to connect to dbus session bus. Exiting.")
                    sys.exit(1)
                else:
                    log.error("Unable to connect to dbus session bus (running as root?)")
                    sys.exit(1)

            # Receive events from the session bus
            session_bus.add_signal_receiver(handle_session_signal, sender_keyword='sender',
                destination_keyword='dest', interface_keyword='interface',
                member_keyword='member', path_keyword='path')

            log.debug("Entering main loop...")

            try:
                MainLoop().run()
            except KeyboardInterrupt:
                log.debug("Ctrl-C: Exiting...")

        finally:
            if parent_pid:
                log.debug("Killing parent toolbox process (pid=%d)..." % parent_pid)
                try:
                    os.kill(parent_pid, signal.SIGKILL)
                except OSError as e:
                    log.debug("Failed: %s" % e.message)

            mod.unlockInstance()

        sys.exit(0)

else: # qt4
    # if utils.ui_status[1] == "PyQt4":
    #     try:
    #         from PyQt4.QtGui import QApplication
    #         from ui4.devmgr5 import DevMgr5
    #     except ImportError as e:
    #         log.error(e)
    #         sys.exit(1)
    # elif utils.ui_status[1] == "PyQt5":
    #     try:
    #         from PyQt5.QtWidgets import QApplication
    #         from ui5.devmgr5 import DevMgr5
    #     except ImportError as e:
    #         log.error(e)
    #         import traceback
    #         traceback.print_exc()
    #         sys.exit(1)
    # else:
    #     log.error("Unable to load Qt support")
    #     sys.exit(1)
    QApplication, ui_package = utils.import_dialog(ui_toolkit)
    ui = import_module(ui_package + ".devmgr5")



    log.set_module("hp-toolbox(UI)")

    if 1:
    #try:
        app = QApplication(sys.argv)

        toolbox = ui.DevMgr5(__version__, device_uri,  None)
        toolbox.show()
        try:
            log.debug("Starting GUI loop...")
            app.exec_()
        except KeyboardInterrupt:
            sys.exit(0)

    if 1:
    #finally:
        mod.unlockInstance()
        sys.exit(0)
