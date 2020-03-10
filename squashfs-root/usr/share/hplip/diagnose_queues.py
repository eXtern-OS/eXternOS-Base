#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# (c) Copyright 2011-2015 HP Development Company, L.P.
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
# Author: Amarnath Chitumalla
#
from __future__ import print_function
__version__ = '1.1'
__title__ = 'AutoConfig Utility to check queues configuration'
__mod__ = 'hp-daignose-queues'
__doc__ = """Auto config utility for HPLIP supported multifunction Devices to diagnose queues configuration."""

# Std Lib
import sys
import os
import getopt


# Local
from base.g import *
from base import utils, module, queues, password

def usage(typ='text'):
    if typ == 'text':
        utils.log_title(__title__, __version__)
    utils.format_text(USAGE, typ, __title__, __mod__, __version__)
    sys.exit(0)



#########Main##########
USAGE = [(__doc__, "", "name", True),
         ("Usage: %s [MODE] [OPTIONS]" % __mod__, "", "summary", True),
          utils.USAGE_MODE,
          utils.USAGE_GUI_MODE,
          utils.USAGE_INTERACTIVE_MODE,
          utils.USAGE_SPACE,
         utils.USAGE_OPTIONS,
         utils.USAGE_LOGGING1, utils.USAGE_LOGGING2, utils.USAGE_LOGGING3,
         utils.USAGE_HELP,
        ]

try:
    log.set_module(__mod__)
    mod = module.Module(__mod__, __title__, __version__, __doc__, USAGE,
                    (INTERACTIVE_MODE, GUI_MODE),
                    (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5),
                    run_as_root_ok=True,quiet=True)
    try:
        opts, device_uri, printer_name, mode, ui_toolkit, loc = mod.parseStdOpts('hl:gsiu',
                     ['help', 'help-rest', 'help-man', 'help-desc', 'logging=','gui','interactive'],
                      handle_device_printer=False)


    except getopt.GetoptError as e:
        log.error(e.msg)
        usage()
        sys.exit(1)

    if os.getenv("HPLIP_DEBUG"):
        log.set_level('debug')

    log_level = 'info'
    quiet_mode = False
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()

        elif o == '--help-rest':
            usage('rest')

        elif o == '--help-man':
            usage('man')

        elif o == '--help-desc':
            print(__doc__, end=' ')
            sys.exit(0)

        elif o in ('-l', '--logging'):
            log_level = a.lower().strip()

        elif o == '-g':
            log_level = 'debug'

        elif o == '-s':
            quiet_mode = True

    if not log.set_level(log_level):
        usage()
    if not quiet_mode:
        utils.log_title(__title__, __version__)

    mod.lockInstance(__mod__, True)
    log_file = os.path.normpath('%s/hplip_queues.log'%prop.user_dir)
    log.debug(log.bold("Saving output in log file: %s" % log_file))
    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except OSError:
            pass
    log.set_logfile(log_file)
    log.set_where(log.LOG_TO_CONSOLE_AND_FILE)

    passwordObj = password.Password(mode)
    queues.main_function(passwordObj, mode,ui_toolkit, quiet_mode )


except KeyboardInterrupt:
    log.error("User exit")

mod.unlockInstance()
log.debug("Done.")
