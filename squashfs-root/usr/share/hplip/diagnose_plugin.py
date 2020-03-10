#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# (c) Copyright 2015 HP Development Company, L.P.
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
# Author: Amarnath Chitumalla, Suma Byrappa
#

__version__ = '1.0'
__mod__ = 'hp-diagnose_plugin'
__title__ = 'Diagnose Plugin Utility'
__doc__ = "Diagnose HP Plugin. Installs plugins if absent"

# Std Lib
import sys
import getopt
import time
import os.path
import re
import os


# Local
from base.g import *
from base import utils, module

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from base.utils import dyn_import_mod as import_module


def usage(typ='text'):
    if typ == 'text':
        utils.log_title(__title__, __version__)
    utils.format_text(USAGE, typ, __title__, __mod__, __version__)
    sys.exit(0)


USAGE = [ (__doc__, "", "name", True),
          ("Usage: %s [OPTIONS]" % __mod__, "", "summary", True),
          utils.USAGE_OPTIONS,
          utils.USAGE_LOGGING1, utils.USAGE_LOGGING2, utils.USAGE_LOGGING3,
          utils.USAGE_HELP,
          utils.USAGE_SPACE,
          utils.USAGE_SEEALSO,
          ("hp-plugin", "", "seealso", False),
          ("hp-setup", "", "seealso", False),
          ("hp-firmware", "", "seealso", False),
        ]


mod = module.Module(__mod__, __title__, __version__, __doc__, USAGE,
                    (INTERACTIVE_MODE, GUI_MODE),
                    (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5), True)

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts( handle_device_printer=False)

plugin_path = None
install_mode = PLUGIN_REQUIRED
plugin_reason = PLUGIN_REASON_NONE

if mode == GUI_MODE:
    if ui_toolkit == 'qt3':
        log.error("Unable to load Qt3. Please use Qt4")

    else: #qt4
        if not utils.canEnterGUIMode4():
            log.error("%s requires GUI support . Is Qt4 installed?" % __mod__)
            sys.exit(1)

        # try:
        #     from PyQt4.QtGui import QApplication, QMessageBox
        #     from ui4.plugindiagnose import PluginDiagnose
        #     from installer import pluginhandler
        # except ImportError:
        #     log.error("Unable to load Qt4 support. Is it installed?")
        #     sys.exit(1)

        QApplication, ui_package = utils.import_dialog(ui_toolkit)
        ui = import_module(ui_package + ".plugindiagnose")
        from installer import pluginhandler

        app = QApplication(sys.argv)
        pluginObj = pluginhandler.PluginHandle()
        plugin_sts = pluginObj.getStatus()
        if plugin_sts == PLUGIN_INSTALLED:
            log.info("Device Plugin is already installed")
            sys.exit(0)
        elif plugin_sts == PLUGIN_NOT_INSTALLED:
            dialog = ui.PluginDiagnose(None, install_mode, plugin_reason)
        else:
            dialog = ui.PluginDiagnose(None, install_mode, plugin_reason, True)

        dialog.show()
        try:
            log.debug("Starting GUI loop...")
            app.exec_()
        except KeyboardInterrupt:
            log.error("User exit")
            sys.exit(0)
else: #Interaction mode
    log.error("Only Qt4 GUI mode is supported \n")
    usage()

log.info("")
log.info("Done.")
