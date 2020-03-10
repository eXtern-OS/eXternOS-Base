# ubuntu-drivers-common custom detect plugin for sl-modem
#
# (C) 2012 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

import os
import re
import logging
import subprocess

modem_re = re.compile(r'^\s*\d+\s*\[Modem\s*\]')
modem_as_subdevice_re = re.compile(r'^card [0-9].*[mM]odem')

pkg = 'sl-modem-daemon'


def detect(apt_cache):
    # Check in /proc/asound/cards
    try:
        with open('/proc/asound/cards') as f:
            for l in f:
                if modem_re.match(l):
                    return [pkg]
    except IOError as e:
        logging.debug('could not open /proc/asound/cards: %s', e)

    # Check aplay -l
    try:
        env = os.environ.copy()
        try:
            del env['LANGUAGE']
        except KeyError:
            pass
        env['LC_ALL'] = 'C'
        aplay = subprocess.Popen(
            ['aplay', '-l'], env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
        (aplay_out, aplay_err) = aplay.communicate()

        if aplay.returncode != 0:
            logging.error('aplay -l failed with %i: %s' % (aplay.returncode,
                          aplay_err))
            return None
    except OSError:
        logging.exception('could not open aplay -l')
        return None

    for row in aplay_out.splitlines():
        if modem_as_subdevice_re.match(row):
            return [pkg]

    return None
