# utils.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2004-2013 Canonical
#
#  Authors: Michael Vogt <mvo@debian.org>
#           Michael Terry <michael.terry@canonical.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

from __future__ import print_function

from gettext import gettext as _
from gettext import ngettext
from stat import (S_IMODE, ST_MODE, S_IXUSR)
from math import ceil

import apt
import apt_pkg
apt_pkg.init_config()

import locale
import logging
import re
import os
import subprocess
import sys
import time
try:
    from urllib.request import (
        ProxyHandler,
        Request,
        build_opener,
        install_opener,
        urlopen,
    )
    from urllib.parse import urlsplit
except ImportError:
    from urllib2 import (
        ProxyHandler,
        Request,
        build_opener,
        install_opener,
        urlopen,
    )
    from urlparse import urlsplit

from copy import copy


class ExecutionTime(object):
    """
    Helper that can be used in with statements to have a simple
    measure of the timing of a particular block of code, e.g.
    with ExecutionTime("db flush"):
        db.flush()
    """
    def __init__(self, info=""):
        self.info = info

    def __enter__(self):
        self.now = time.time()

    def __exit__(self, type, value, stack):
        print("%s: %s" % (self.info, time.time() - self.now))


def get_string_with_no_auth_from_source_entry(entry):
    tmp = copy(entry)
    url_parts = urlsplit(tmp.uri)
    if url_parts.username:
        tmp.uri = tmp.uri.replace(url_parts.username, "hidden-u")
    if url_parts.password:
        tmp.uri = tmp.uri.replace(url_parts.password, "hidden-p")
    return str(tmp)


def is_unity_running():
    """ return True if Unity is currently running """
    unity_running = False
    try:
        import dbus
        bus = dbus.SessionBus()
        unity_running = bus.name_has_owner("com.canonical.Unity")
    except Exception as e:
        logging.exception("could not check for Unity dbus service")
    return unity_running


def is_child_of_process_name(processname, pid=None):
    if not pid:
        pid = os.getpid()
    while pid > 0:
        stat_file = "/proc/%s/stat" % pid
        with open(stat_file) as stat_f:
            stat = stat_f.read()
        # extract command (inside ())
        command = stat.partition("(")[2].rpartition(")")[0]
        if command == processname:
            return True
        # get parent (second to the right of command) and check that next
        pid = int(stat.rpartition(")")[2].split()[1])
    return False


def inside_chroot():
    """ returns True if we are inside a chroot
    """
    # if there is no proc or no pid 1 we are very likely inside a chroot
    if not os.path.exists("/proc") or not os.path.exists("/proc/1"):
        return True
    # if the inode is differnt for pid 1 "/" and our "/"
    return os.stat("/") != os.stat("/proc/1/root")


def wrap(t, width=70, subsequent_indent=""):
    """ helpers inspired after textwrap - unfortunately
        we can not use textwrap directly because it break
        packagenames with "-" in them into new lines
    """
    out = ""
    for s in t.split():
        if (len(out) - out.rfind("\n")) + len(s) > width:
            out += "\n" + subsequent_indent
        out += s + " "
    return out


def twrap(s, **kwargs):
    msg = ""
    paras = s.split("\n")
    for par in paras:
        s = wrap(par, **kwargs)
        msg += s + "\n"
    return msg


def lsmod():
    " return list of loaded modules (or [] if lsmod is not found) "
    modules = []
    # FIXME raise?
    if not os.path.exists("/sbin/lsmod"):
        return []
    p = subprocess.Popen(["/sbin/lsmod"], stdout=subprocess.PIPE,
                         universal_newlines=True)
    lines = p.communicate()[0].split("\n")
    # remove heading line: "Modules Size Used by"
    del lines[0]
    # add lines to list, skip empty lines
    for line in lines:
        if line:
            modules.append(line.split()[0])
    return modules


def check_and_fix_xbit(path):
    " check if a given binary has the executable bit and if not, add it"
    if not os.path.exists(path):
        return
    mode = S_IMODE(os.stat(path)[ST_MODE])
    if not ((mode & S_IXUSR) == S_IXUSR):
        os.chmod(path, mode | S_IXUSR)


def country_mirror():
    " helper to get the country mirror from the current locale "
    # special cases go here
    lang_mirror = {'c': ''}
    # no lang, no mirror
    if 'LANG' not in os.environ:
        return ''
    lang = os.environ['LANG'].lower()
    # check if it is a special case
    if lang[:5] in lang_mirror:
        return lang_mirror[lang[:5]]
    # now check for the most comon form (en_US.UTF-8)
    if "_" in lang:
        country = lang.split(".")[0].split("_")[1]
        if "@" in country:
            country = country.split("@")[0]
        return country + "."
    else:
        return lang[:2] + "."
    return ''


def get_dist():
    " return the codename of the current runing distro "
    # support debug overwrite
    dist = os.environ.get("META_RELEASE_FAKE_CODENAME")
    if dist:
        logging.warning("using fake release name '%s' (because of "
                        "META_RELEASE_FAKE_CODENAME environment) " % dist)
        return dist
    # then check the real one
    from subprocess import Popen, PIPE
    p = Popen(["lsb_release", "-c", "-s"], stdout=PIPE,
              universal_newlines=True)
    res = p.wait()
    if res != 0:
        sys.stderr.write("lsb_release returned exitcode: %i\n" % res)
        return "unknown distribution"
    dist = p.stdout.readline().strip()
    p.stdout.close()
    return dist


def get_dist_version():
    " return the version of the current running distro "
    # support debug overwrite
    desc = os.environ.get("META_RELEASE_FAKE_VERSION")
    if desc:
        logging.warning("using fake release version '%s' (because of "
                        "META_RELEASE_FAKE_VERSION environment) " % desc)
        return desc
    # then check the real one
    from subprocess import Popen, PIPE
    p = Popen(["lsb_release", "-r", "-s"], stdout=PIPE,
              universal_newlines=True)
    res = p.wait()
    if res != 0:
        sys.stderr.write("lsb_release returned exitcode: %i\n" % res)
        return "unknown distribution"
    desc = p.stdout.readline().strip()
    p.stdout.close()
    return desc


class HeadRequest(Request):
    def get_method(self):
        return "HEAD"


def url_downloadable(uri, debug_func=None):
    """
    helper that checks if the given uri exists and is downloadable
    (supports optional debug_func function handler to support
     e.g. logging)

    Supports http (via HEAD) and ftp (via size request)
    """
    if not debug_func:
        lambda x: True
    debug_func("url_downloadable: %s" % uri)
    (scheme, netloc, path, querry, fragment) = urlsplit(uri)
    debug_func("s='%s' n='%s' p='%s' q='%s' f='%s'" % (scheme, netloc, path,
                                                       querry, fragment))
    if scheme in ("http", "https"):
        try:
            http_file = urlopen(HeadRequest(uri))
            http_file.close()
            if http_file.code == 200:
                return True
            return False
        except Exception as e:
            debug_func("error from httplib: '%s'" % e)
            return False
    elif scheme == "ftp":
        import ftplib
        try:
            f = ftplib.FTP(netloc)
            f.login()
            f.cwd(os.path.dirname(path))
            size = f.size(os.path.basename(path))
            f.quit()
            if debug_func:
                debug_func("ftplib.size() returned: %s" % size)
            if size != 0:
                return True
        except Exception as e:
            if debug_func:
                debug_func("error from ftplib: '%s'" % e)
            return False
    return False


def init_proxy(gsettings=None):
    """ init proxy settings

    * first check for http_proxy environment (always wins),
    * then check the apt.conf http proxy,
    * then look into synaptics conffile
    * then into gconf  (if gconfclient was supplied)
    """
    SYNAPTIC_CONF_FILE = "/root/.synaptic/synaptic.conf"
    proxies = {}
    # generic apt config wins
    if apt_pkg.config.find("Acquire::http::Proxy") != '':
        proxies["http"] = apt_pkg.config.find("Acquire::http::Proxy")
    # then synaptic
    elif os.path.exists(SYNAPTIC_CONF_FILE):
        cnf = apt_pkg.Configuration()
        apt_pkg.read_config_file(cnf, SYNAPTIC_CONF_FILE)
        use_proxy = cnf.find_b("Synaptic::useProxy", False)
        if use_proxy:
            proxy_host = cnf.find("Synaptic::httpProxy")
            proxy_port = str(cnf.find_i("Synaptic::httpProxyPort"))
            if proxy_host and proxy_port:
                proxies["http"] = "http://%s:%s/" % (proxy_host, proxy_port)
    if apt_pkg.config.find("Acquire::https::Proxy") != '':
        proxies["https"] = apt_pkg.config.find("Acquire::https::Proxy")
    elif "http" in proxies:
        proxies["https"] = proxies["http"]
    # if we have a proxy, set it
    if proxies:
        # basic verification
        for proxy in proxies.values():
            if not re.match("https?://\w+", proxy):
                print("proxy '%s' looks invalid" % proxy, file=sys.stderr)
                return
        proxy_support = ProxyHandler(proxies)
        opener = build_opener(proxy_support)
        install_opener(opener)
        if "http" in proxies:
            os.putenv("http_proxy", proxies["http"])
        if "https" in proxies:
            os.putenv("https_proxy", proxies["https"])
    return proxies


def on_battery():
    """
    Check via dbus if the system is running on battery.
    This function is using UPower per default, if UPower is not
    available it falls-back to DeviceKit.Power.
    """
    try:
        import dbus
        bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
        try:
            devobj = bus.get_object('org.freedesktop.UPower',
                                    '/org/freedesktop/UPower')
            dev = dbus.Interface(devobj, 'org.freedesktop.DBus.Properties')
            return dev.Get('org.freedesktop.UPower', 'OnBattery')
        except dbus.exceptions.DBusException as e:
            error_unknown = 'org.freedesktop.DBus.Error.ServiceUnknown'
            if e._dbus_error_name != error_unknown:
                raise
            devobj = bus.get_object('org.freedesktop.DeviceKit.Power',
                                    '/org/freedesktop/DeviceKit/Power')
            dev = dbus.Interface(devobj, "org.freedesktop.DBus.Properties")
            return dev.Get("org.freedesktop.DeviceKit.Power", "on_battery")
    except Exception as e:
        #import sys
        #print("on_battery returned error: ", e, file=sys.stderr)
        return False


def inhibit_sleep():
    """
    Send a dbus signal to logind to not suspend the system, it will be
    released when the return value drops out of scope
    """
    try:
        from gi.repository import Gio, GLib
        connection = Gio.bus_get_sync(Gio.BusType.SYSTEM)

        var, fdlist = connection.call_with_unix_fd_list_sync(
            'org.freedesktop.login1', '/org/freedesktop/login1',
            'org.freedesktop.login1.Manager', 'Inhibit',
            GLib.Variant('(ssss)',
                         ('shutdown:sleep',
                          'UpdateManager', 'Updating System',
                          'block')),
            None, 0, -1, None, None)
        inhibitor = Gio.UnixInputStream(fd=fdlist.steal_fds()[var[0]])

        return inhibitor
    except Exception:
        #print("could not send the dbus Inhibit signal: %s" % e)
        return False


def str_to_bool(str):
    if str == "0" or str.upper() == "FALSE":
        return False
    return True


def get_lang():
    import logging
    try:
        (locale_s, encoding) = locale.getdefaultlocale()
        return locale_s
    except Exception:
        logging.exception("gedefaultlocale() failed")
        return None


def get_ubuntu_flavor(cache=None):
    """ try to guess the flavor based on the running desktop """
    # this will (of course) not work in a server environment,
    # but the main use case for this is to show the right
    # release notes.
    pkg = get_ubuntu_flavor_package(cache=cache)
    return pkg.split('-', 1)[0]


def _load_meta_pkg_list():
    # This could potentially introduce a circular dependency, but the config
    # parser logic is simple, and doesn't rely on any UpdateManager code.
    from DistUpgrade.DistUpgradeConfigParser import DistUpgradeConfig
    parser = DistUpgradeConfig('/usr/share/ubuntu-release-upgrader')
    return parser.getlist('Distro', 'MetaPkgs')


def get_ubuntu_flavor_package(cache=None):
    """ try to guess the flavor metapackage based on the running desktop """
    # From spec, first if ubuntu-desktop is installed, use that.
    # Second, grab first installed one from DistUpgrade.cfg.
    # Lastly, fallback to ubuntu-desktop again.
    meta_pkgs = ['ubuntu-desktop']

    try:
        meta_pkgs.extend(sorted(_load_meta_pkg_list()))
    except Exception as e:
        print('Could not load list of meta packages:', e)

    if cache is None:
        cache = apt.Cache()
    for meta_pkg in meta_pkgs:
        cache_pkg = cache[meta_pkg] if meta_pkg in cache else None
        if cache_pkg and cache_pkg.is_installed:
            return meta_pkg
    return 'ubuntu-desktop'


def get_ubuntu_flavor_name(cache=None):
    """ try to guess the flavor name based on the running desktop """
    pkg = get_ubuntu_flavor_package(cache=cache)
    lookup = {'ubuntustudio-desktop': 'Ubuntu Studio'}
    if pkg in lookup:
        return lookup[pkg]
    elif pkg.endswith('-desktop'):
        return capitalize_first_word(pkg.rsplit('-desktop', 1)[0])
    elif pkg.endswith('-netbook'):
        return capitalize_first_word(pkg.rsplit('-netbook', 1)[0])
    else:
        return 'Ubuntu'


# Unused by update-manager, but still used by ubuntu-release-upgrader
def error(parent, summary, message):
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk, Gdk
    d = Gtk.MessageDialog(parent=parent,
                          flags=Gtk.DialogFlags.MODAL,
                          type=Gtk.MessageType.ERROR,
                          buttons=Gtk.ButtonsType.CLOSE)
    d.set_markup("<big><b>%s</b></big>\n\n%s" % (summary, message))
    d.realize()
    d.get_window().set_functions(Gdk.WMFunction.MOVE)
    d.set_title("")
    d.run()
    d.destroy()
    return False


def humanize_size(bytes):
    """
    Convert a given size in bytes to a nicer better readable unit
    """

    if bytes < 1000 * 1000:
        # to have 0 for 0 bytes, 1 for 0-1000 bytes and for 1 and above
        # round up
        size_in_kb = int(ceil(bytes / float(1000)))
        # TRANSLATORS: download size of small updates, e.g. "250 kB"
        return ngettext("%(size).0f kB", "%(size).0f kB", size_in_kb) % {
            "size": size_in_kb}
    else:
        # TRANSLATORS: download size of updates, e.g. "2.3 MB"
        return locale.format_string(_("%.1f MB"), bytes / 1000.0 / 1000.0)


def get_arch():
    return apt_pkg.config.find("APT::Architecture")


def is_port_already_listening(port):
    """ check if the current system is listening on the given tcp port """
    # index in the line
    INDEX_LOCAL_ADDR = 1
    #INDEX_REMOTE_ADDR = 2
    INDEX_STATE = 3
    # state (st) that we care about
    STATE_LISTENING = '0A'
    # read the data
    with open("/proc/net/tcp") as net_tcp:
        for line in net_tcp.readlines():
            line = line.strip()
            if not line:
                continue
            # split, values are:
            #   sl  local_address rem_address   st tx_queue rx_queue tr
            #   tm->when retrnsmt   uid  timeout inode
            values = line.split()
            state = values[INDEX_STATE]
            if state != STATE_LISTENING:
                continue
            local_port_str = values[INDEX_LOCAL_ADDR].split(":")[1]
            local_port = int(local_port_str, 16)
            if local_port == port:
                return True
    return False


def iptables_active():
    """ Return True if iptables is active """
    # FIXME: is there a better way?
    iptables_empty = """Chain INPUT (policy ACCEPT)
target     prot opt source               destination

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination
"""
    if os.getuid() != 0:
        raise OSError("Need root to check the iptables state")
    if not os.path.exists("/sbin/iptables"):
        return False
    out = subprocess.Popen(["iptables", "-nL"],
                           stdout=subprocess.PIPE,
                           universal_newlines=True).communicate()[0]
    if out == iptables_empty:
        return False
    return True


def capitalize_first_word(string):
    """ this uppercases the first word's first letter
    """
    if len(string) > 1 and string[0].isalpha() and not string[0].isupper():
        return string[0].capitalize() + string[1:]
    return string


def get_package_label(pkg):
    """ this takes a package synopsis and uppercases the first word's
        first letter
    """
    name = getattr(pkg.candidate, "summary", "")
    return capitalize_first_word(name)


if __name__ == "__main__":
    #print(mirror_from_sources_list())
    #print(on_battery())
    #print(inside_chroot())
    #print(iptables_active())
    error(None, "bar", "baz")
