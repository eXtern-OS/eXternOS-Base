# ubuntu-drivers-common custom detect plugin for arm GLES drivers
#
# (C) 2012 Canonical Ltd.
# Author: Oliver Grawert <ogra@ubuntu.com>
#
# This plugin detects GLES driver packages based on pattern matching
# against the "Hardware" line in /proc/cpuinfo.
#
# To add a new SoC, simply insert a line into the db variable with the
# following format:
#
# '<Pattern from your cpuinfo output>': '<Name of the driver package>',
#

import logging

db = {'OMAP4 Panda board': 'pvr-omap4',
      'OMAP4430 Panda Board': 'pvr-omap4',
      'OMAP4430 4430SDP board': 'pvr-omap4',
      'cardhu': 'nvidia-tegra',
      'ventana': 'nvidia-tegra',
      'Toshiba AC100 / Dynabook AZ': 'nvidia-tegra',
      }


def detect(apt_cache):
    board = ''
    pkg = None

    try:
        with open('/proc/cpuinfo') as file:
            for line in file:
                if 'Hardware' in line:
                    board = line.split(':')[1].strip()
    except IOError as err:
        logging.debug('could not open /proc/cpuinfo: %s', err)

    for pattern in db.keys():
        if pattern in board:
            pkg = [db[pattern]]

    return pkg
