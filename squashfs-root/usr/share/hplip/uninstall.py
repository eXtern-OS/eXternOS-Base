#!/usr/bin/python
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
__version__ = '1.0'
__title__ = 'HPLIP Uninstaller'
__mod__ = 'hp-uninstall'
__doc__ = "Uninstaller for HPLIP ."

# Std Lib
import getopt, os, sys, re, time

# Local
from base.g import *
from base import utils, tui
from installer.core_install import *


USAGE = [(__doc__, "", "name", True),
         ("Usage: %s [OPTIONS]" % __mod__, "", "summary", True),
         utils.USAGE_SPACE,
         utils.USAGE_OPTIONS,
         utils.USAGE_LOGGING1, utils.USAGE_LOGGING2, utils.USAGE_LOGGING3,
         ("Non-interactive mode:", "-n (without asking for permission)","option",False),
         utils.USAGE_HELP,
        ]


def usage(typ='text'):
    if typ == 'text':
        utils.log_title(__title__, __version__)

    utils.format_text(USAGE, typ, __title__, __mod__, __version__)
    sys.exit(0)

mode = INTERACTIVE_MODE
auto = False
log_level = None



log.set_module(__mod__)


try:
    opts, args = getopt.getopt(sys.argv[1:], 'hl:gn',
        ['help', 'help-rest', 'help-man', 'help-desc', 'gui', 'lang=','logging=', 'debug'])

except getopt.GetoptError as e:
    log.error(e.msg)
    usage()
    sys.exit(1)

if os.getenv("HPLIP_DEBUG"):
    log.set_level('debug')

for o, a in opts:
    if o in ('-h', '--help'):
        usage()

    elif o == '--help-rest':
        usage('rest')

    elif o == '--help-man':
        usage('man')

    elif o in ('-q', '--lang'):
        language = a.lower()

    elif o == '--help-desc':
        print(__doc__, end=' ')
        sys.exit(0)

    elif o in ('-l', '--logging'):
        log_level = a.lower().strip()
#        if not log.set_level(log_level):
#            usage()

    elif o in ('-g', '--debug'):
        log_level = 'debug'
#        log.set_level('debug')

    elif o == '-n':
        mode = NON_INTERACTIVE_MODE


if log_level is not None:
    if not log.set_level(log_level):
        usage()
        
log_file = os.path.normpath('%s/hplip-uninstall.log'%prop.user_dir)
if os.getuid() != 0:
    log.error("To run 'hp-uninstall' utility, you must have root privileges.(Try using 'sudo' or 'su -c')")
    sys.exit(1)

if os.path.exists(log_file):
    os.remove(log_file)

log.set_logfile(log_file)
log.set_where(log.LOG_TO_CONSOLE_AND_FILE)

log.debug("Log file=%s" % log_file)
log.debug("euid = %d" % os.geteuid())

utils.log_title(__title__, __version__, True)

log.info("Uninstaller log saved in: %s" % log.bold(log_file))
log.info("")

core =  CoreInstall(MODE_CHECK, INTERACTIVE_MODE)
core.init()

core.uninstall(mode)

