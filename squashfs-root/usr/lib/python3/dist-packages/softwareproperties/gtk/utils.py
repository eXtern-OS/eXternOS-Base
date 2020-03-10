# Copyright (C) 2009 Canonical
#
# Authors:
#  Michael Vogt
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

from __future__ import print_function

import aptsources.distro
from datetime import datetime
import distro_info
from functools import wraps
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

import logging
LOG=logging.getLogger(__name__)

import time

def setup_ui(self, path, domain):
    # setup ui
    self.builder = Gtk.Builder()
    self.builder.set_translation_domain(domain)
    self.builder.add_from_file(path)
    self.builder.connect_signals(self)
    for o in self.builder.get_objects():
        if issubclass(type(o), Gtk.Buildable):
            name = Gtk.Buildable.get_name(o)
            setattr(self, name, o)
        else:
            logging.debug("can not get name for object '%s'" % o)

def has_gnome_online_accounts():
    try:
        d = Gio.DesktopAppInfo.new('gnome-online-accounts-panel.desktop')
        return d != None
    except Exception:
        return False

def is_current_distro_lts():
    distro = aptsources.distro.get_distro()
    di = distro_info.UbuntuDistroInfo()
    return di.is_lts(distro.codename)

def is_current_distro_supported():
    distro = aptsources.distro.get_distro()
    di = distro_info.UbuntuDistroInfo()
    return distro.codename in di.supported(datetime.now().date())

def retry(exceptions, tries=10, delay=0.1, backoff=2):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = '{}, Retrying in {} seconds...'.format(e, mdelay)
                    logging.warning(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
