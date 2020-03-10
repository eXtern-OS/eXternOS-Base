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
__title__ = "Make Copies Utility"
__mod__ = 'hp-makecopies'
__doc__ = "PC initiated make copies function on supported HP AiO and MFP devices. (Note: Currently unsupported in Qt4.)"

# Std Lib
import sys
import os
import getopt
import re
from base.sixext.moves import queue
import time
import operator

# Local
from base.g import *
from base import utils, device, pml, tui, module
from copier import copier
from prnt import cups


mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                    (NON_INTERACTIVE_MODE, GUI_MODE),
                    (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5), False, False, True)

mod.setUsage(module.USAGE_FLAG_DEVICE_ARGS,
    extra_options=[
    ("Number of copies:", "-m<num_copies> or --copies=<num_copies> or --num=<num_copies> (1-99)", "option", False),
    ("Reduction/enlargement:", "-r<%> or --reduction=<%> or --enlargement=<%> (25-400%)", "option", False),
     ("Quality:", "-q<quality> or --quality=<quality> (where quality is: 'fast', 'draft', 'normal', 'presentation', or 'best')", "option", False),
     ("Contrast:", "-c<contrast> or --contrast=<contrast> (-5 to +5)", "option", False),
     ("Fit to page (flatbed only):", "-f or --fittopage or --fit (overrides reduction/enlargement)", "option", False)])

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts('m:r:q:c:f',
                     ['num=', 'copies=', 'reduction=', 'enlargement=', 'quality=',
                      'contrast=', 'fittopage', 'fit', 'fit-to-page'])

device_uri = mod.getDeviceUri(device_uri, printer_name,
    filter={'copy-type': (operator.gt, 0)})

if not device_uri:
    sys.exit(1)

log.info("Using device : %s\n" % device_uri)
num_copies = None
reduction = None
reduction_spec = False
contrast = None
quality = None
fit_to_page = None


for o, a in opts:
    if o in ('-m', '--num', '--copies'):
        try:
            num_copies = int(a)
        except ValueError:
            log.warning("Invalid number of copies. Set to default of 1.")
            num_copies = 1

        if num_copies < 1:
            log.warning("Invalid number of copies. Set to minimum of 1.")
            num_copies = 1

        elif num_copies > 99:
            log.warning("Invalid number of copies. Set to maximum of 99.")
            num_copies = 99

    elif o in ('-c', '--contrast'):
        try:
            contrast = int(a)
        except ValueError:
            log.warning("Invalid contrast setting. Set to default of 0.")
            contrast = 0

        if contrast < -5:
            log.warning("Invalid contrast setting. Set to minimum of -5.")
            contrast = -5

        elif contrast > 5:
            log.warning("Invalid contrast setting. Set to maximum of +5.")
            contrast = 5

        contrast *= 25

    elif o in ('-q', '--quality'):
        a = a.lower().strip()

        if a == 'fast':
            quality = pml.COPIER_QUALITY_FAST

        elif a.startswith('norm'):
            quality = pml.COPIER_QUALITY_NORMAL

        elif a.startswith('pres'):
            quality = pml.COPIER_QUALITY_PRESENTATION

        elif a.startswith('draf'):
            quality = pml.COPIER_QUALITY_DRAFT

        elif a == 'best':
            quality = pml.COPIER_QUALITY_BEST

        else:
            log.warning("Invalid quality. Set to default of 'normal'.")

    elif o in ('-r', '--reduction', '--enlargement'):
        reduction_spec = True
        try:
            reduction = int(a.replace('%', ''))
        except ValueError:
            log.warning("Invalid reduction %. Set to default of 100%.")
            reduction = 100

        if reduction < 25:
            log.warning("Invalid reduction %. Set to minimum of 25%.")
            reduction = 25

        elif reduction > 400:
            log.warning("Invalid reduction %. Set to maximum of 400%.")
            reduction = 400

    elif o in ('-f', '--fittopage', '--fit', '--fit-to-page'):
        fit_to_page = pml.COPIER_FIT_TO_PAGE_ENABLED



if fit_to_page == pml.COPIER_FIT_TO_PAGE_ENABLED and reduction_spec:
    log.warning("Fit to page specfied: Reduction/enlargement parameter ignored.")


if mode == GUI_MODE:
    if ui_toolkit == 'qt3':
        if not utils.canEnterGUIMode():
            log.error("%s requires GUI support (try running with --qt4). Also, try using non-interactive (-n) mode." % __mod__)
            sys.exit(1)
    else:
        if not utils.canEnterGUIMode4():
            log.error("%s requires GUI support (try running with --qt3). Also, try using non-interactive (-n) mode." % __mod__)
            sys.exit(1)


if mode == GUI_MODE:
    if ui_toolkit == 'qt3':
        app = None
        makecopiesdlg = None

        try:
            from qt import *
            from ui.makecopiesform import MakeCopiesForm
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

        bus = ['cups']
        makecopiesdlg = MakeCopiesForm(bus, device_uri, printer_name,
                                       num_copies, contrast, quality,
                                       reduction, fit_to_page)

        makecopiesdlg.show()
        app.setMainWidget(makecopiesdlg)

        try:
            log.debug("Starting GUI loop...")
            app.exec_loop()
        except KeyboardInterrupt:
            pass

    else: # qt4
        try:
            from PyQt4.QtGui import QApplication
            from ui4.makecopiesdialog import MakeCopiesDialog
        except ImportError:
            log.error("Unable to load Qt4 support. Is it installed?")
            sys.exit(1)

        #try:
        if 1:
            app = QApplication(sys.argv)
            dlg = MakeCopiesDialog(None, device_uri)
            dlg.show()
            try:
                log.debug("Starting GUI loop...")
                app.exec_()
            except KeyboardInterrupt:
                sys.exit(0)

        #finally:
        if 1:
            sys.exit(0)


else: # NON_INTERACTIVE_MODE
    try:
        dev = copier.PMLCopyDevice(device_uri, printer_name)

        try:
            try:
                dev.open()

                if num_copies is None:
                    result_code, num_copies = dev.getPML(pml.OID_COPIER_NUM_COPIES)

                if contrast is None:
                    result_code, contrast = dev.getPML(pml.OID_COPIER_CONTRAST)

                if reduction is None:
                    result_code, reduction = dev.getPML(pml.OID_COPIER_REDUCTION)

                if quality is None:
                    result_code, quality = dev.getPML(pml.OID_COPIER_QUALITY)

                if fit_to_page is None and dev.copy_type == COPY_TYPE_DEVICE:
                    result_code, fit_to_page = dev.getPML(pml.OID_COPIER_FIT_TO_PAGE)
                else:
                    fit_to_page = pml.COPIER_FIT_TO_PAGE_DISABLED

                result_code, max_reduction = dev.getPML(pml.OID_COPIER_REDUCTION_MAXIMUM)
                result_code, max_enlargement = dev.getPML(pml.OID_COPIER_ENLARGEMENT_MAXIMUM)

            except Error as e:
                log.error(e.msg)
                sys.exit(1)

            scan_src = dev.mq.get('scan-src', SCAN_SRC_FLATBED)
            log.debug(scan_src)

            if scan_src == SCAN_SRC_SCROLLFED:
                fit_to_page = pml.COPIER_FIT_TO_PAGE_DISABLED

            log.debug("num_copies = %d" % num_copies)
            log.debug("contrast= %d" % contrast)
            log.debug("reduction = %d" % reduction)
            log.debug("quality = %d" % quality)
            log.debug("fit_to_page = %d" % fit_to_page)
            log.debug("max_reduction = %d" % max_reduction)
            log.debug("max_enlargement = %d" % max_enlargement)
            log.debug("scan_src = %d" % scan_src)

            update_queue = queue.Queue()
            event_queue = queue.Queue()

            dev.copy(num_copies, contrast, reduction,
                     quality, fit_to_page, scan_src,
                     update_queue, event_queue)


            cont = True
            while cont:
                while update_queue.qsize():
                    try:
                        status = update_queue.get(0)
                    except queue.Empty:
                        break

                    if status == copier.STATUS_IDLE:
                        log.debug("Idle")
                        continue

                    elif status in (copier.STATUS_SETTING_UP, copier.STATUS_WARMING_UP):
                        log.info("Warming up...")
                        continue

                    elif status == copier.STATUS_ACTIVE:
                        log.info("Copying...")
                        continue

                    elif status in (copier.STATUS_ERROR, copier.STATUS_DONE):

                        if status == copier.STATUS_ERROR:
                            log.error("Copier error!")
                            dev.sendEvent(EVENT_COPY_JOB_FAIL)
                            cont = False
                            break

                        elif status == copier.STATUS_DONE:
                            cont = False
                            break

                time.sleep(2)

        finally:
            dev.close()

    except KeyboardInterrupt:
        log.error("User interrupt. Canceling...")
        event_queue.put(copier.COPY_CANCELED)
        dev.sendEvent(EVENT_COPY_JOB_CANCELED)

    dev.waitForCopyThread()
    dev.sendEvent(EVENT_END_COPY_JOB)
    log.info("")
    log.info("Done.")

