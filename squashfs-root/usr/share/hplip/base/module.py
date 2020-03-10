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

# Std Lib
import sys
import re
import getopt
import os

# Local
from .g import *
from . import tui, utils, device

USAGE_FLAG_NONE = 0x00
USAGE_FLAG_DEVICE_ARGS = 0x01
USAGE_FLAG_SUPRESS_G_DEBUG_FLAG = 0x02
USAGE_FLAG_FILE_ARGS = 0x04



class Module(object):
    def __init__(self, mod, title, version, doc,
                 usage_data=None, avail_modes=None,
                 supported_ui_toolkits=None,
                 run_as_root_ok=False, quiet=False, deprecated=False):

        self.mod = mod
        self.title = title
        self.version = version
        self.doc = doc
        self.usage_data = usage_data
        os.umask(0o037)
        log.set_module(mod)
        self.args = []
        self.quiet = quiet
        self.deprecated = deprecated
        self.lock_file = None
        self.help_only_support = False
        prop.prog = sys.argv[0]

        if os.getenv("HPLIP_DEBUG"):
            log.set_level('debug')

        self.avail_modes = avail_modes
        if supported_ui_toolkits is not None:
            self.supported_ui_toolkits = supported_ui_toolkits
            self.num_supported_ui_toolkits = len(self.supported_ui_toolkits)
        else:
            self.supported_ui_toolkits = []
            self.num_supported_ui_toolkits = 0

        self.default_ui_toolkit = sys_conf.get('configure', 'ui-toolkit', 'qt4')

        self.num_installed_ui_toolkits = 0
        self.installed_ui_toolkits = []
        if utils.to_bool(sys_conf.get('configure', 'qt3', '0')):
            self.installed_ui_toolkits.append(UI_TOOLKIT_QT3)
            self.num_installed_ui_toolkits += 1

        if utils.to_bool(sys_conf.get('configure', 'qt4', '0')):
            self.installed_ui_toolkits.append(UI_TOOLKIT_QT4)
            self.num_installed_ui_toolkits += 1

        if utils.to_bool(sys_conf.get('configure', 'qt5', '0')):
            self.installed_ui_toolkits.append(UI_TOOLKIT_QT5)
            self.num_installed_ui_toolkits += 1

        self.default_mode = INTERACTIVE_MODE

        self.num_valid_modes = 0
        if self.avail_modes is not None:
            if GUI_MODE in self.avail_modes and prop.gui_build and self.installed_ui_toolkits:
                self.num_valid_modes += 1

            if INTERACTIVE_MODE in self.avail_modes:
                self.num_valid_modes += 1

            if NON_INTERACTIVE_MODE in self.avail_modes:
                self.num_valid_modes += 1

        if self.avail_modes is not None:
            if INTERACTIVE_MODE in self.avail_modes:
                self.default_mode = INTERACTIVE_MODE

            elif NON_INTERACTIVE_MODE in self.avail_modes:
                self.default_mode = NON_INTERACTIVE_MODE

        if self.supported_ui_toolkits is not None and prop.gui_build and self.installed_ui_toolkits:

            if self.default_ui_toolkit == 'qt3' and UI_TOOLKIT_QT4 in self.supported_ui_toolkits and \
                UI_TOOLKIT_QT3 not in self.supported_ui_toolkits and INTERACTIVE_MODE in self.avail_modes:

                # interactive + qt4 and default is qt3 --> set to interactive (if avail) (e.g., hp-align)
                self.default_mode = INTERACTIVE_MODE
                self.default_ui_toolkit = 'none'

            elif (UI_TOOLKIT_QT4 in self.supported_ui_toolkits and self.default_ui_toolkit == 'qt4' and UI_TOOLKIT_QT4 in self.installed_ui_toolkits) or \
                 (UI_TOOLKIT_QT3 in self.supported_ui_toolkits and self.default_ui_toolkit == 'qt3' and UI_TOOLKIT_QT3 in self.installed_ui_toolkits) or \
                 (UI_TOOLKIT_QT5 in self.supported_ui_toolkits and self.default_ui_toolkit == 'qt5' and UI_TOOLKIT_QT5 in self.installed_ui_toolkits):
                self.default_mode = GUI_MODE

            elif self.default_ui_toolkit == 'qt3' and UI_TOOLKIT_QT3 not in self.supported_ui_toolkits:

                if UI_TOOLKIT_QT4 in self.supported_ui_toolkits and UI_TOOLKIT_QT4 in self.installed_ui_toolkits: # (e.g, hp-linefeedcal?)
                    self.default_ui_toolkit = 'qt4'
                    self.default_mode = GUI_MODE
                if UI_TOOLKIT_QT5 in self.supported_ui_toolkits and UI_TOOLKIT_QT5 in self.installed_ui_toolkits:
                    self.default_ui_toolkit = 'qt5'
                    self.default_mode = GUI_MODE

                elif INTERACTIVE_MODE in self.avail_modes:
                    self.default_mode = INTERACTIVE_MODE

                elif NON_INTERACTIVE_MODE in self.avail_modes:
                    self.default_mode = NON_INTERACTIVE_MODE

                else:
                    log.error("%s cannot be run using Qt3 toolkit." % self.mod)
#                    sys.exit(1)
                    self.help_only_support = True

            elif self.default_ui_toolkit == 'qt4' and UI_TOOLKIT_QT4 not in self.supported_ui_toolkits:

                if UI_TOOLKIT_QT3 in self.supported_ui_toolkits and UI_TOOLKIT_QT3 in self.installed_ui_toolkits: # (e.g., hp-unload)
                    self.default_ui_toolkit = 'qt3'
                    self.default_mode = GUI_MODE

                elif INTERACTIVE_MODE in self.avail_modes:
                    self.default_mode = INTERACTIVE_MODE

                elif NON_INTERACTIVE_MODE in self.avail_modes:
                    self.default_mode = NON_INTERACTIVE_MODE

                else:
                    log.error("%s cannot be run using Qt4 toolkit." % self.mod)
#                    sys.exit(1)
                    self.help_only_support = True


        self.mode = self.default_mode

        #log.debug("Default ui-toolkit: %s" % self.default_ui_toolkit)
        #log.debug("Default mode: %s" % self.default_mode)

        if os.getuid() == 0 and not run_as_root_ok:
            log.warn("%s should not be run as root/superuser." % mod)


    def setUsage(self, include_flags=0, extra_options=None,
                 extra_notes=None, see_also_list=None):

        if self.doc:
            self.usage_data = [(self.doc, "", "name", True)]
        else:
            self.usage_data = []

        summary = ['Usage:', self.mod]
        content = []
        notes = []

        if include_flags & USAGE_FLAG_DEVICE_ARGS == USAGE_FLAG_DEVICE_ARGS:
            summary.append('[DEVICE_URI|PRINTER_NAME]')
            content.append(utils.USAGE_ARGS)
            content.append(utils.USAGE_DEVICE)
            content.append(utils.USAGE_PRINTER)

        if self.avail_modes is not None and self.num_valid_modes > 0:
            summary.append('[MODE]')
            content.append(utils.USAGE_SPACE)
            content.append(utils.USAGE_MODE)

            if self.num_installed_ui_toolkits > 0:
                if GUI_MODE in self.avail_modes and prop.gui_build:
                    content.append(utils.USAGE_GUI_MODE)

            if INTERACTIVE_MODE in self.avail_modes:
                content.append(utils.USAGE_INTERACTIVE_MODE)

            if NON_INTERACTIVE_MODE in self.avail_modes:
                content.append(utils.USAGE_NON_INTERACTIVE_MODE)

        # [options]
        summary.append('[OPTIONS]')
        content.append(utils.USAGE_SPACE)
        content.append(utils.USAGE_OPTIONS)

        if self.avail_modes is not None and GUI_MODE in self.avail_modes and \
            self.supported_ui_toolkits is not None and self.num_supported_ui_toolkits > 0 and \
            prop.gui_build and self.num_installed_ui_toolkits > 0:

            if UI_TOOLKIT_QT3 in self.supported_ui_toolkits and UI_TOOLKIT_QT3 in self.installed_ui_toolkits:
                content.append(utils.USAGE_USE_QT3)

            if UI_TOOLKIT_QT4 in self.supported_ui_toolkits and UI_TOOLKIT_QT4 in self.installed_ui_toolkits:
                content.append(utils.USAGE_USE_QT4)

            if UI_TOOLKIT_QT5 in self.supported_ui_toolkits and UI_TOOLKIT_QT5 in self.installed_ui_toolkits:
                content.append(utils.USAGE_USE_QT5)
                

        content.append(utils.USAGE_LOGGING1)
        content.append(utils.USAGE_LOGGING2)
        if include_flags & USAGE_FLAG_SUPRESS_G_DEBUG_FLAG != USAGE_FLAG_SUPRESS_G_DEBUG_FLAG:
            content.append(utils.USAGE_LOGGING3) # Issue with --gg in hp-sendfax

        # --loc/--lang
        #if self.avail_modes is not None and GUI_MODE in self.avail_modes and prop.gui_build:
        #    content.append(utils.USAGE_LANGUAGE)

        content.append(utils.USAGE_HELP)

        if extra_options is not None:
            for e in extra_options:
                content.append(e)

        # [FILES]
        if include_flags & USAGE_FLAG_FILE_ARGS:
            summary.append('[FILES]')

        # Notes
        if extra_notes is not None or notes:
            content.append(utils.USAGE_SPACE)
            content.append(utils.USAGE_NOTES)

            for n in notes:
                content.append(n)

            if extra_notes is not None:
                for n in extra_notes:
                    content.append(n)

        # See Also
        if see_also_list is not None:
            content.append(utils.USAGE_SPACE)
            content.append(utils.USAGE_SEEALSO)
            for s in see_also_list:
                content.append((s, '', 'seealso', False))

        content.insert(0, (' '.join(summary), '', 'summary', True))

        for c in content:
            self.usage_data.append(c)


    def parseStdOpts(self, extra_params=None,
                     extra_long_params=None,
                     handle_device_printer=True,
                     supress_g_debug_flag=False):

        params = 'l:h' # 'l:hq:'
        if not supress_g_debug_flag:
            params = ''.join([params, 'g'])

        long_params = ['logging=', 'help', 'help-rest', 'help-man',
                       'help-desc',
                       #'lang=', 'loc=',
                       'debug', 'dbg']

        if handle_device_printer:
            params = ''.join([params, 'd:p:P:'])
            long_params.extend(['device=', 'device-uri=', 'printer=', 'printer-name'])

        if self.num_valid_modes > 0:
            if GUI_MODE in self.avail_modes and prop.gui_build:
                params = ''.join([params, 'u'])
                long_params.extend(['gui', 'ui'])

            if INTERACTIVE_MODE in self.avail_modes:
                params = ''.join([params, 'i'])
                long_params.extend(['interactive', 'text'])

            if NON_INTERACTIVE_MODE in self.avail_modes:
                params = ''.join([params, 'n'])
                long_params.extend(['noninteractive', 'non-interactive', 'batch'])

        if self.supported_ui_toolkits is not None and \
            self.num_supported_ui_toolkits >= 1 and prop.gui_build and \
            self.avail_modes is not None and GUI_MODE in self.avail_modes:

            if UI_TOOLKIT_QT3 in self.supported_ui_toolkits and UI_TOOLKIT_QT3 in self.installed_ui_toolkits:
                long_params.extend(['qt3', 'use-qt3'])

            if UI_TOOLKIT_QT4 in self.supported_ui_toolkits and UI_TOOLKIT_QT4 in self.installed_ui_toolkits:
                long_params.extend(['qt4', 'use-qt4'])

        if extra_params is not None:
            params = ''.join([params, extra_params])

        if extra_long_params is not None:
            long_params.extend(extra_long_params)

        opts = None
        show_usage = None
        device_uri = None
        printer_name = None
        error_msg = []
        mode = self.default_mode
        if prop.gui_build:
            ui_toolkit = self.default_ui_toolkit
        else:
            ui_toolkit = 'none'
        lang = None

        try:
            opts, self.args = getopt.getopt(sys.argv[1:], params, long_params)
        except getopt.GetoptError as e:
            error_msg = [e.msg]

        else:
            for o, a in opts:
                if o in ('-d', '--device', '--device-uri'):
                    device_uri = a

                elif o in ('-P', '-p', '--printer', '--printer-name'):
                    printer_name = a

                elif o in ('-l', '--logging'):
                    log_level = a.lower().strip()
                    if not log.set_level(log_level):
                        show_usage = 'text'

                elif o in ('-g', '--debug', '--dbg'):
                    log.set_level('debug')

                elif o in ('-u', '--gui', '--ui'):
                    if self.avail_modes is not None and GUI_MODE in self.avail_modes and \
                        self.supported_ui_toolkits is not None and prop.gui_build:
                        mode = GUI_MODE
                    else:
                        error_msg.append("Unable to enter GUI mode.")

                elif o in ('-i', '--interactive', '--text'):
                    if self.avail_modes is not None and INTERACTIVE_MODE in self.avail_modes:
                        mode = INTERACTIVE_MODE
                        ui_toolkit = 'none'

                elif o in ('-n', '--non-interactive', '--batch'):
                    if self.avail_modes is not None and NON_INTERACTIVE_MODE in self.avail_modes:
                        mode = NON_INTERACTIVE_MODE
                        ui_toolkit = 'none'

                elif o in ('-h', '--help'):
                    show_usage = 'text'

                elif o == '--help-rest':
                    show_usage = 'rest'

                elif o == '--help-man':
                    show_usage = 'man'

                elif o == '--help-desc':
                    show_usage = 'desc'

                elif o in ('--qt3', '--use-qt3'):
                    if self.avail_modes is not None and GUI_MODE in self.avail_modes:
                        if self.supported_ui_toolkits is not None and \
                            UI_TOOLKIT_QT3 in self.supported_ui_toolkits and prop.gui_build and \
                            UI_TOOLKIT_QT3 in self.installed_ui_toolkits:

                            mode = GUI_MODE
                            ui_toolkit = 'qt3'
                        else:
                            error_msg.append("%s does not support Qt3. Unable to enter GUI mode." % self.mod)

                elif o in ('--qt4', '--use-qt4'):
                    if self.avail_modes is not None and GUI_MODE in self.avail_modes:
                        if self.supported_ui_toolkits is not None and \
                            UI_TOOLKIT_QT4 in self.supported_ui_toolkits and prop.gui_build and \
                            UI_TOOLKIT_QT4 in self.installed_ui_toolkits:

                            mode = GUI_MODE
                            ui_toolkit = 'qt4'
                        else:
                            error_msg.append("%s does not support Qt4. Unable to enter GUI mode." % self.mod)
 
                elif o in ('--qt5', '--use-qt5'):
                    if self.avail_modes is not None and GUI_MODE in self.avail_modes:
                        if self.supported_ui_toolkits is not None and \
                            UI_TOOLKIT_QT5 in self.supported_ui_toolkits and prop.gui_build and \
                            UI_TOOLKIT_QT5 in self.installed_ui_toolkits:

                            mode = GUI_MODE
                            ui_toolkit = 'qt5'
                        else:
                            error_msg.append("%s does not support Qt4. Unable to enter GUI mode." % self.mod)
               

                #elif o in ('--lang', '--loc'):
                #    if a.strip() == '?':
                #        utils.log_title(self.title, self.version)
                #        self.showLanguages()
                #        sys.exit(0)
                #    else:
                #        lang = utils.validate_language(a.lower())

        if error_msg:
            show_usage = 'text'

        if self.help_only_support:
            if show_usage or error_msg:
                self.usage(show_usage, error_msg)
            else:
                log.info(log.bold("\nPlease check usage '%s --help'"%self.mod))
                show_usage = 'text'
        else:
            self.usage(show_usage, error_msg)

        if show_usage is not None:
            sys.exit(0)

        self.mode = mode
        return opts, device_uri, printer_name, mode, ui_toolkit, lang


    def showLanguages(self):
        f = tui.Formatter()
        f.header = ("Language Code", "Alternate Name(s)")
        for loc, ll in list(supported_locales.items()):
            f.add((ll[0], ', '.join(ll[1:])))

        f.output()


    def usage(self, show_usage='text', error_msg=None):
        if show_usage is None:
            if not self.quiet:
                self.showTitle()
            return

        if show_usage == 'text':
            self.showTitle()
            log.info()

        if show_usage == 'desc':
            print(self.doc)

        else:
            utils.format_text(self.usage_data, show_usage, self.title, self.mod, self.version)

            if error_msg:
                for e in error_msg:
                    log.error(e)

                sys.exit(1)

            sys.exit(0)

            if show_usage == 'text':
                sys.exit(0)


    def showTitle(self, show_ver=True):
        if not self.quiet:
            log.info("")

            if show_ver:
                log.info(log.bold("HP Linux Imaging and Printing System (ver. %s)" % prop.version))
            else:
                log.info(log.bold("HP Linux Imaging and Printing System"))

            log.info(log.bold("%s ver. %s" % (self.title, self.version)))
            log.info("")
            log.info("Copyright (c) 2001-15 HP Development Company, LP")
            log.info("This software comes with ABSOLUTELY NO WARRANTY.")
            log.info("This is free software, and you are welcome to distribute it")
            log.info("under certain conditions. See COPYING file for more details.")
            log.info("")
            if self.deprecated:
                log.warn(log.bold("%s support is deprecated. Feature can be used as is. Fixes or updates will not be provided" %self.title))
                log.info("")


    def getDeviceUri(self, device_uri=None, printer_name=None, back_end_filter=device.DEFAULT_BE_FILTER,
                     filter=device.DEFAULT_FILTER, devices=None, restrict_to_installed_devices=True):
        """ Validate passed in parameters, and, if in text mode, have user select desired device to use.
            Used for tools that are device-centric and accept -d (and maybe also -p).
            Use the filter(s) to restrict what constitute valid devices.

            Return the matching device URI based on:
            1. Passed in device_uri if it is valid (filter passes)
            2. Corresponding device_uri from the printer_name if it is valid (filter passes) ('*' means default printer)
            3. User input from menu (based on bus and filter)

            device_uri and printer_name can both be specified if they correspond to the same device.

            Returns:
                device_uri|None
                (returns None if passed in device_uri is invalid or printer_name doesn't correspond to device_uri)
        """

        log.debug("getDeviceUri(%s, %s, %s, %s, , %s)" %
            (device_uri, printer_name, back_end_filter, filter, restrict_to_installed_devices))
        log.debug("Mode=%s" % self.mode)

        scan_uri_flag = False
        if 'hpaio' in back_end_filter:
            scan_uri_flag = True

        device_uri_ok = False
        printer_name_ok = False
        device_uri_ret = None

        if devices is None:
            devices = device.getSupportedCUPSDevices(back_end_filter, filter)
            log.debug(devices)
            if not devices and restrict_to_installed_devices:
                log.error("No device found that support this feature.")
                return None

        if device_uri is not None:
            if device_uri in devices:
                device_uri_ok = True

            elif restrict_to_installed_devices:
                log.error("'%s' device doesn't support this feature (or) Invalid device URI" % device_uri)
                return None

            else:
                device_uri_ok = True

        if printer_name is not None:
            #Find the printer_name in the models of devices
            log.debug(devices)
            for uri in devices:
               log.debug(uri)
               back_end, is_hp, bb, model, serial, dev_file, host, zc, port = \
                            device.parseDeviceURI(uri)
               log.debug("back_end=%s, is_hp=%s, bb=%s, model=%s, serial=%s, dev_file=%s, host=%s, zc=%s, port= %s" % (back_end, is_hp, bb, model, serial, dev_file, host, zc, port))
               cups_printer = devices[uri]
               if printer_name.lower() in [m.lower() for m in cups_printer]:
                   printer_name_ok = True 
                   printer_name_device_uri = device_uri = uri
                   device_uri_ok = True
            if printer_name_ok is not True: 
               log.error("'%s' device doesn't support this feature (or) Invalid printer name" % printer_name)
               printer_name = None
               if restrict_to_installed_devices:
                    return None



        if device_uri is not None and printer_name is None and device_uri_ok: # Only device_uri specified
            device_uri_ret = device_uri

        elif device_uri is not None and printer_name is not None: # Both specified
            if device_uri_ok and printer_name_ok:
                if device_uri == printer_name_device_uri:
                    device_uri_ret = device_uri
                else:
                    log.error("Printer name %s and device URI %s refer to different devices." % (printer_name, device_uri))
                    printer_name, printer_name = None, None

        elif device_uri is None and printer_name is not None and printer_name_ok: # Only printer name specified
            device_uri_ret = device.getDeviceURIByPrinterName(printer_name, scan_uri_flag)

        elif len(devices) == 1: # Nothing specified, and only 1 device avail.
            device_uri_ret = list(devices.keys())[0]

        if device_uri_ret is None and len(devices):
            if self.mode == INTERACTIVE_MODE:
                device_uri_ret = tui.device_table(devices, scan_uri_flag)
            else:
                device_uri_ret = list(devices.keys())[0]

        if device_uri_ret is not None:
            user_conf.set('last_used', 'device_uri', device_uri_ret)

        else:
            if self.mode in (INTERACTIVE_MODE, NON_INTERACTIVE_MODE):
                log.error("No device selected/specified or that supports this functionality.")
                sys.exit(1)
#            else:
#                log.debug("No device selected/specified")

        return device_uri_ret


    def getPrinterName(self, printer_name, device_uri, back_end_filter=device.DEFAULT_BE_FILTER,
                       filter=device.DEFAULT_FILTER, restrict_to_installed_devices=True):
        """ Validate passed in parameters, and, if in text mode, have user select desired printer to use.
            Used for tools that are printer queue-centric and accept -p (and maybe also -d).
            Use the filter(s) to restrict what constitute valid printers.

            Return the matching printer_name based on:
            1. Passed in printer_name if it is valid (filter passes) ('*' means default printer)
            2. From single printer_name of corresponding passed in device_uri (filter passes)
            3. User input from menu (CUPS printer list, filtered) [or if > 1 queue for device_uri]

            device_uri and printer_name can both be specified if they correspond to the same device.

            Returns:
                (printer_name|None, device_uri|None) (tuple)
                (returns None if passed in printer_name is invalid or device_uri doesn't correspond to printer_name)
        """

        log.debug("getPrinterName(%s, %s, %s, %s)" % (device_uri, printer_name, back_end_filter, filter))
        log.debug("Mode=%s" % self.mode)

        device_uri_ok = False
        printer_name_ok = False
        printer_name_ret = None
        device_uri_ret = None

        printers = device.getSupportedCUPSPrinterNames(back_end_filter, filter)
        log.debug(printers)

        if not printers:
            log.error("No device found that support this feature.")
            return False, None, None

        if device_uri is not None:
            devices = device.getSupportedCUPSDevices(back_end_filter, filter)
            if device_uri in devices:
                device_uri_ok = True
                device_uri_ret = device_uri
            else:
                log.error("'%s' device doesn't support this feature (or) Invalid device URI" % device_uri)
                device_uri = None
                if restrict_to_installed_devices:
                    return False, None, None

        if printer_name is not None:
            if printer_name == '*':
                from prnt import cups
                default_printer = cups.getDefaultPrinter()
                if default_printer is not None:
                    printer_name_ret = default_printer
                else:
                    log.error("CUPS default printer not set")
                    printer_name = None

            else:
                if printer_name.lower() in [p.lower() for p in printers]:
                    printer_name_ok = True
                    device_uri_ret = device.getDeviceURIByPrinterName(printer_name)
                else:
                    log.error("'%s' device doesn't support this feature (or) Invalid printer name" % printer_name)
                    printer_name = None
                    if restrict_to_installed_devices:
                        return False, None, None

        if device_uri is not None and printer_name is None and device_uri_ok: # Only device_uri specified
            if len(devices[device_uri]) == 1:
                printer_name_ret = devices[device_uri][0]

        elif device_uri is not None and printer_name is not None: # Both specified
            if device_uri_ok and printer_name_ok:
                if device_uri == device_uri_ret:
                    printer_name_ret = printer_name
                else:
                    log.error("Printer name and device URI refer to different devices.")

        elif device_uri is None and printer_name is not None and printer_name_ok: # Only printer name specified
            printer_name_ret = printer_name

        elif len(printers) == 1: # nothing specified, and only 1 avail. printer
            printer_name_ret = printers[0]

        if printer_name_ret is None and self.mode in (INTERACTIVE_MODE, NON_INTERACTIVE_MODE) and len(printers):
            printer_name_ret = tui.printer_table(printers)

        if printer_name_ret is not None and device_uri_ret is None:
            device_uri_ret = device.getDeviceURIByPrinterName(printer_name_ret)

        if device_uri_ret is not None:
            user_conf.set('last_used', 'device_uri', device_uri_ret)

        if printer_name_ret is not None:
            user_conf.set('last_used', 'printer_name', printer_name_ret)

        else:
            if self.mode in (INTERACTIVE_MODE, NON_INTERACTIVE_MODE):
                log.error("No printer selected/specified or that supports this functionality.")
                sys.exit(1)
            else:
                log.debug("No printer selected/specified")

        return True, printer_name_ret, device_uri_ret


    def lockInstance(self, suffix='',suppress_error=False):
        if suffix:
            ok, self.lock_file = utils.lock_app('-'.join([self.mod, suffix]),suppress_error)
        else:
            ok, self.lock_file = utils.lock_app(self.mod,suppress_error)

        if not ok:
            sys.exit(1)


    def unlockInstance(self):
        if self.lock_file is not None:
            utils.unlock(self.lock_file)
