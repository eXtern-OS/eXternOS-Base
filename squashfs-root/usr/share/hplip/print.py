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

__version__ = '4.0'
__title__ = 'Print Utility'
__mod__ = 'hp-print'
__doc__ = "A simple print UI front-end to lp/lpr."

# Std Lib
import sys
import os
import getopt


# Local
from base.g import *
from base import utils, device, tui, module
from prnt import cups

log.set_module('hp-print')

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from base.utils import dyn_import_mod as import_module


app = None
printdlg = None


mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                    (GUI_MODE,), (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5))

mod.setUsage(module.USAGE_FLAG_DEVICE_ARGS | module.USAGE_FLAG_FILE_ARGS,
             see_also_list=['hp-printsettings'])

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts()

sts, printer_name, device_uri = mod.getPrinterName(printer_name, device_uri)
if not sts:
    sys.exit(1)

if ui_toolkit == 'qt3':
    if not utils.canEnterGUIMode():
        log.error("%s requires GUI support (try running with --qt4). Exiting." % __mod__)
        sys.exit(1)
else:
    if not utils.canEnterGUIMode4():
        log.error("%s requires GUI support (try running with --qt3). Exiting." % __mod__)
        sys.exit(1)

if ui_toolkit == 'qt3':
    try:
        from qt import *
        from ui.printerform import PrinterForm
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

    #print printer_name
    printdlg = PrinterForm(printer_name, mod.args)
    printdlg.show()
    app.setMainWidget(printdlg)

    try:
        log.debug("Starting GUI loop...")
        app.exec_loop()
    except KeyboardInterrupt:
        pass


else: # qt4
    # try:
    #     from PyQt4.QtGui import QApplication
    #     from ui4.printdialog import PrintDialog
    # except ImportError:
    #     log.error("Unable to load Qt4 support. Is it installed?")
    #     sys.exit(1)
    QApplication, ui_package = utils.import_dialog(ui_toolkit)
    ui = import_module(ui_package + ".printdialog")

    if 1:
        app = QApplication(sys.argv)
        dlg = ui.PrintDialog(None, printer_name, mod.args)
        dlg.show()
        try:
            log.debug("Starting GUI loop...")
            app.exec_()
        except KeyboardInterrupt:
            sys.exit(0)


sys.exit(0)


