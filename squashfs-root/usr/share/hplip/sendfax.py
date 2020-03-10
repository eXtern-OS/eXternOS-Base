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

__version__ = '9.0'
__title__ = 'PC Sendfax Utility'
__mod__ = 'hp-sendfax'
__doc__ = "PC send fax for HPLIP supported multifunction printers."

# Std Lib
import sys
import os
import os.path
import getopt
import signal
import time
import operator
import subprocess


# Local
from base.g import *
import base.utils as utils
from base import device, tui, module
from base.sixext import to_unicode, to_string_utf8

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from base.utils import dyn_import_mod as import_module


username = prop.username
faxnum_list = []
recipient_list = []
group_list = []
prettyprint = False

mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                    (GUI_MODE, NON_INTERACTIVE_MODE),
                    (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5))

mod.setUsage(module.USAGE_FLAG_DEVICE_ARGS | module.USAGE_FLAG_SUPRESS_G_DEBUG_FLAG,
    extra_options=[
    ("Specify the fax number(s):", "-f<number(s)> or --faxnum=<number(s)> or --fax-num=<number(s)>  or --num=<number(s)>(-n only)", "option", False),
    ("Specify the recipient(s):", "-r<recipient(s)> or --recipient=<recipient(s)> (-n only)", "option", False),
    ("Specify the groups(s):", "--group=<group(s)> or --groups=<group(s)> (-n only)", "option", False) ],
    see_also_list=['hp-faxsetup', 'hp-fab'])

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts('f:r:g:',
                     ['faxnum=', 'fax-num=', 'recipient=', 'group=',
                      'groups=', 'gg'],
                      supress_g_debug_flag=True)

for o, a in opts:
    if o == '--gg':
        log.set_level('debug')

    elif o in ('-z', '--logfile'):
        log.set_logfile(a)
        log.set_where(log.LOG_TO_CONSOLE_AND_FILE)

    elif o == '--fax':
        printer_name = a

    elif o in ('-f', '--faxnum', '--fax-num', '--num'):
        faxnum_list.extend(a.split(','))

    elif o in ('-r', '--recipient'):
        recipient_list.extend(a.split(','))

    elif o in ('-g', '--group'):
        group_list.extend(a.split(','))


if not prop.fax_build:
    log.error("Fax is disabled (turned off during build). Exiting")
    sys.exit(1)

sts, printer_name, device_uri = mod.getPrinterName(printer_name, device_uri,
         filter={'fax-type': (operator.gt, 0)}, back_end_filter=['hpfax'])

if not sts:
    sys.exit(1)

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
        sendfax = None

        try:
            from qt import *
            from ui.faxsendjobform import FaxSendJobForm
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


        if os.geteuid() == 0:
            log.error("You must not be root to run this utility.")

            QMessageBox.critical(None,
                                 "HP Device Manager - Send Fax",
                                 "You must not be root to run hp-sendfax.",
                                  QMessageBox.Ok,
                                  QMessageBox.NoButton,
                                  QMessageBox.NoButton)

            sys.exit(1)

        # TODO: Fix instance lock
        sendfax = FaxSendJobForm(device_uri,
                                 printer_name,
                                 mod.args)

        app.setMainWidget(sendfax)

        pid = os.getpid()
        log.debug('pid=%d' % pid)

        sendfax.show()

        try:
            log.debug("Starting GUI loop...")
            app.exec_loop()
        except KeyboardInterrupt:
            pass

    else: # qt4
        # #try:
        # if 1:
        #     from PyQt4.QtGui import QApplication
        #     from ui4.sendfaxdialog import SendFaxDialog
        # #except ImportError:
        # if 0:
        #     log.error("Unable to load Qt4 support. Is it installed?")
        #     sys.exit(1)

        QApplication, ui_package = utils.import_dialog(ui_toolkit)
        ui = import_module(ui_package + ".sendfaxdialog")

        app = QApplication(sys.argv)
        dlg = ui.SendFaxDialog(None, printer_name, device_uri, mod.args)
        dlg.show()

        try:
            log.debug("Starting GUI loop...")
            app.exec_()
        except KeyboardInterrupt:
            sys.exit(0)




else: # NON_INTERACTIVE_MODE
    if os.getuid() == 0:
        log.error("%s cannot be run as root." % __mod__)
        sys.exit(1)

    try:
        import struct
        from base.sixext.moves import queue
        from base.sixext import PY3
        from base.sixext import  to_unicode
        from prnt import cups
        from base import magic

        try:
            from fax import fax
        except ImportError:
            # This can fail on Python < 2.3 due to the datetime module
            log.error("Fax address book disabled - Python 2.3+ required.")
            sys.exit(1)

        db =  fax.FaxAddressBook() # FAB instance

        try:
            import dbus
        except ImportError:
            log.error("PC send fax requires dBus and python-dbus")
            sys.exit(1)

        import warnings
        # Ignore: .../dbus/connection.py:242: DeprecationWarning: object.__init__() takes no parameters
        # (occurring on Python 2.6/dBus 0.83/Ubuntu 9.04)
        warnings.simplefilter("ignore", DeprecationWarning)

        dbus_avail, service, session_bus = device.init_dbus()

        if not dbus_avail or service is None:
            log.error("Unable to initialize dBus. PC send fax requires dBus and hp-systray support. Exiting.")
            sys.exit(1)

        phone_num_list = []

        log.debug("Faxnum list = %s" % faxnum_list)
        faxnum_list = utils.uniqueList(faxnum_list)
        log.debug("Unique list=%s" % faxnum_list)

        for f in faxnum_list:
            for c in f:
                if c not in '0123456789-(+) *#':
                    log.error("Invalid character in fax number '%s'. Only the characters '0123456789-(+) *#' are valid." % f)
                    sys.exit(1)

        log.debug("Group list = %s" % group_list)
        group_list = utils.uniqueList(group_list)
        log.debug("Unique list=%s" % group_list)

        for g in group_list:
            entries = db.group_members(g)
            if not entries:
                log.warn("Unknown group name: %s" % g)
            else:
                for e in entries:
                    recipient_list.append(e)

        log.debug("Recipient list = %s" % recipient_list)
        recipient_list = utils.uniqueList(recipient_list)
        log.debug("Unique list=%s" % recipient_list)

        for r in recipient_list:
            if db.get(r) is None:
                log.error("Unknown fax recipient '%s' in the recipient list." % r)
                all_entries = db.get_all_records()
                log.info(log.bold("\nKnown recipients (entries):"))

                for a in all_entries:
                    aa = db.get(a)
                    log.info("%s (fax number: %s)" % (a, aa['fax']))

                print()
                sys.exit(1)

        for p in recipient_list:
            a = db.get(p)
            if a['fax']:
                phone_num_list.append(a)
                log.debug("Name=%s Number=%s" % (a['name'], a['fax']))

        for p in faxnum_list:
            phone_num_list.append({'fax': p, 'name': to_unicode('Unknown')})
            log.debug("Number=%s" % p)

        log.debug("Phone num list = %s" % phone_num_list)

        if not phone_num_list:
            mod.usage(error_msg=["No recipients specified. Please use -f, -r, and/or -g to specify recipients."])

        allowable_mime_types = cups.getAllowableMIMETypes()

        # stat = ''
        # try :
        #     p = subprocess.Popen('getenforce', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #     stat, err = p.communicate()
        #     stat = to_string_utf8(stat)
        # except OSError :
        #     pass
        # except :
        #     log.exception()
        #     sys.exit(1)
        # if stat.strip('\n') == 'Enforcing' :
        #     log.error('Unable to add file. Please disable SeLinux.\nEither disable it manually or run hp-doctor from terminal.')
        #     sys.exit(0)

        for f in mod.args:
            path = os.path.realpath(f)
            log.debug(path)

            if os.path.exists(path):
                mime_type = magic.mime_type(path)
                log.debug(mime_type)
            else:
                log.error("File '%s' does not exist." % path)
                sys.exit(1)

            if mime_type not in allowable_mime_types:
                log.error("File '%s' has a non-allowed mime-type of '%s'" % (path, mime_type))
                sys.exit(1)

        log.info(log.bold("Using fax %s (%s)" % (printer_name, device_uri)))

        #ok, lock_file = utils.lock_app('%s-%s' % (__mod__, printer_name), True)
        mod.lockInstance(printer_name)

        try:
            ppd_file = cups.getPPD(printer_name)

            if ppd_file is not None and os.path.exists(ppd_file):
                if open(ppd_file, 'rb').read(8192).find(b'HP Fax') == -1:
                    log.error("Fax configuration error. The CUPS fax queue for '%s' is incorrectly configured. Please make sure that the CUPS fax queue is configured with the 'HP Fax' Model/Driver." % printer_name)
                    sys.exit(1)

            if not mod.args:
                mod.usage(error_msg=["No files specfied to send. Please specify the file(s) to send on the command line."])

            file_list = []

            for f in mod.args:

                #
                # Submit each file to CUPS for rendering by hpijsfax
                #
                path = os.path.realpath(f)
                log.debug(path)
                mime_type = magic.mime_type(path)

                if mime_type == 'application/hplip-fax': # .g3
                    log.info("\nPreparing fax file %s..." % f)
                    fax_file_fd = open(f, 'rb')
                    header = fax_file_fd.read(fax.FILE_HEADER_SIZE)
                    fax_file_fd.close()

                    mg, version, pages, hort_dpi, vert_dpi, page_size, \
                        resolution, encoding, reserved1, reserved2 = struct.unpack(">8sBIHHBBBII", header)

                    if mg != b'hplip_g3':
                        log.error("%s: Invalid file header. Bad magic." % f)
                        sys.exit(1)

                    file_list.append((f, mime_type, "", "", pages))

                else:
                    all_pages = True
                    page_range = ''
                    page_set = 0
                    nup = 1

                    cups.resetOptions()

                    if mime_type in ["application/x-cshell",
                                     "application/x-perl",
                                     "application/x-python",
                                     "application/x-shell",
                                     "text/plain",] and prettyprint:

                        cups.addOption('prettyprint')

                    if nup > 1:
                        cups.addOption('number-up=%d' % nup)

                    while True:

                        cups_printers = cups.getPrinters()
                        printer_state = cups.IPP_PRINTER_STATE_STOPPED
                        for p in cups_printers:
                            if p.name == printer_name:
                                printer_state = p.state

                        log.debug("Printer state = %d" % printer_state)

                        if printer_state == cups.IPP_PRINTER_STATE_IDLE:
                            log.debug("Printer name = %s file = %s" % (printer_name, path))
                            path = to_unicode(path, 'utf-8')

                            sent_job_id = cups.printFile(printer_name, path, os.path.basename(path))
                            log.info("\nRendering file '%s' (job %d)..." % (path, sent_job_id))
                            log.debug("Job ID=%d" % sent_job_id)
                            break
                        elif printer_state == cups.IPP_PRINTER_STATE_PROCESSING:
                            log.debug("Waiting for CUPS queue '%s' to become idle." % printer_name)
                        else:
                            log.error("The CUPS queue for '%s' is in a stopped or busy state (%d). Please check the queue and try again." % (printer_name, printer_state))
                            sys.exit(1)

                    cups.resetOptions()

                    #
                    # Wait for fax to finish rendering
                    #

                    end_time = time.time() + 120.0
                    while time.time() < end_time:
                        log.debug("Waiting for fax...")
                        try:
                            result = list(service.CheckForWaitingFax(device_uri, prop.username, sent_job_id))
                            log.debug(repr(result))

                        except dbus.exceptions.DBusException:
                            log.error("Cannot communicate with hp-systray. Canceling...")
                            cups.cancelJob(sent_job_id)
                            sys.exit(1)

                        fax_file = str(result[7])
                        log.info(fax_file)

                        if fax_file:
                            log.debug("Fax file=%s" % fax_file)
                            #title = str(result[5])
                            title = result[5]
                            break

                        time.sleep(1)

                    else:
                        log.error("Timeout waiting for rendering. Canceling job #%d..." % sent_job_id)
                        cups.cancelJob(sent_job_id)
                        sys.exit(1)

                    # open the rendered file to read the file header
                    f = open(fax_file, 'rb')
                    header = f.read(fax.FILE_HEADER_SIZE)

                    if len(header) != fax.FILE_HEADER_SIZE:
                        log.error("Invalid fax file! (truncated header or no data)")
                        sys.exit(1)

                    mg, version, total_pages, hort_dpi, vert_dpi, page_size, \
                        resolution, encoding, reserved1, reserved2 = \
                        struct.unpack(">8sBIHHBBBII", header[:fax.FILE_HEADER_SIZE])

                    log.debug("Magic=%s Ver=%d Pages=%d hDPI=%d vDPI=%d Size=%d Res=%d Enc=%d" %
                              (mg, version, total_pages, hort_dpi, vert_dpi, page_size, resolution, encoding))

                    file_list.append((fax_file, mime_type, "", title, total_pages))
                    f.close()

            #
            # Insure that the device is in an OK state
            #

            dev = None

            log.debug("\nChecking device state...")
            try:
                dev = fax.getFaxDevice(device_uri, printer_name)

                try:
                    dev.open()
                except Error as e:
                    log.warn(e.msg)

                try:
                    dev.queryDevice(quick=True)
                except Error as e:
                    log.error("Query device error (%s)." % e.msg)
                    dev.error_state = ERROR_STATE_ERROR

                if dev.error_state > ERROR_STATE_MAX_OK and \
                    dev.error_state not in (ERROR_STATE_LOW_SUPPLIES, ERROR_STATE_LOW_PAPER):

                    log.error("Device is busy or in an error state (code=%d). Please wait for the device to become idle or clear the error and try again." % dev.error_state)
                    sys.exit(1)

                user_conf.set('last_used', 'device_uri', dev.device_uri)

                log.debug("File list:")

                for f in file_list:
                    log.debug(str(f))

                service.SendEvent(device_uri, printer_name, EVENT_START_FAX_JOB, prop.username, 0, '')

                update_queue = queue.Queue()
                event_queue = queue.Queue()

                log.info("\nSending fax...")

                if not dev.sendFaxes(phone_num_list, file_list, "",
                                     "", None, False, printer_name,
                                     update_queue, event_queue):

                    log.error("Send fax is active. Please wait for operation to complete.")
                    service.SendEvent(device_uri, printer_name, EVENT_FAX_JOB_FAIL, prop.username, 0, '')
                    sys.exit(1)

                try:
                    cont = True
                    while cont:
                        while update_queue.qsize():
                            try:
                                status, page_num, phone_num = update_queue.get(0)
                            except queue.Empty:
                                break

                            if status == fax.STATUS_IDLE:
                                log.debug("Idle")

                            elif status == fax.STATUS_PROCESSING_FILES:
                                log.info("\nProcessing page %d" % page_num)

                            elif status == fax.STATUS_DIALING:
                                log.info("\nDialing %s..." % phone_num)

                            elif status == fax.STATUS_CONNECTING:
                                log.info("\nConnecting to %s..." % phone_num)

                            elif status == fax.STATUS_SENDING:
                                log.info("\nSending page %d to %s..." % (page_num, phone_num))

                            elif status == fax.STATUS_CLEANUP:
                                log.info("\nCleaning up...")

                            elif status in (fax.STATUS_ERROR, fax.STATUS_BUSY, fax.STATUS_COMPLETED):
                                cont = False

                                if status  == fax.STATUS_ERROR:
                                    log.error("Fax send error.")
                                    service.SendEvent(device_uri, printer_name, EVENT_FAX_JOB_FAIL, prop.username, 0, '')

                                elif status == fax.STATUS_BUSY:
                                    log.error("Fax device is busy. Please try again later.")
                                    service.SendEvent(device_uri, printer_name, EVENT_FAX_JOB_FAIL, prop.username, 0, '')

                                elif status == fax.STATUS_COMPLETED:
                                    log.info("\nCompleted successfully.")
                                    service.SendEvent(device_uri, printer_name, EVENT_END_FAX_JOB, prop.username, 0, '')

                        update_spinner()
                        time.sleep(2)

                    cleanup_spinner()

                except KeyboardInterrupt:
                    event_queue.put((fax.EVENT_FAX_SEND_CANCELED, '', '', ''))
                    service.SendEvent(device_uri, printer_name, EVENT_FAX_JOB_CANCELED, prop.username, 0, '')
                    log.error("Cancelling...")

            finally:
                log.debug("Waiting for send fax thread to exit...")
                if dev is not None:
                    dev.waitForSendFaxThread()
                    log.debug("Closing device...")
                    dev.close()

        finally:
            mod.unlockInstance()

    except KeyboardInterrupt:
        log.error("User exit")

log.info("")
log.info("Done.")
