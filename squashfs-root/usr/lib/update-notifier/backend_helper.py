#!/usr/bin/python3

import argparse
import logging
import os
import subprocess
import sys

HAVE_APTDAEMON = False
try:
    import aptdaemon.gtk3widgets
    HAVE_APTDAEMON = True
except ImportError:
    pass


# show updates
def show_updates():
    """ show updates using update-manager """
    cmd = ["update-manager", "--no-update"]
    res = subprocess.call(cmd)
    return (res == 0)


# install all updates
def _install_all_updates_aptdaemon():
    from gi.repository import Gtk
    from aptdaemon import client, enums
    from aptdaemon.gtk3widgets import AptProgressDialog
    client = client.AptClient()
    trans = client.upgrade_system(safe_mode=True)
    dia = AptProgressDialog(trans)
    dia.connect("finished", Gtk.main_quit)
    dia.run()
    Gtk.main()
    return trans.exit == enums.EXIT_SUCCESS


def _install_all_updates_synaptic():
    cmd = ["/usr/bin/synaptic-pkexec",
           "--dist-upgrade-mode",
           "--non-interactive",
           "--hide-main-window",
           "-o", "Synaptic::AskRelated=true",
           ]
    return subprocess.call(cmd)


def install_all_updates():
    """ install all updates either with synaptic or aptdaemon """
    if HAVE_APTDAEMON:
        return _install_all_updates_aptdaemon()
    else:
        return _install_all_updates_synaptic()


# check updates
def _check_updates_aptdaemon():
    from gi.repository import Gtk
    from aptdaemon import client, enums
    from aptdaemon.gtk3widgets import AptProgressDialog
    client = client.AptClient()
    trans = client.update_cache()
    dia = AptProgressDialog(trans)
    dia.connect("finished", Gtk.main_quit)
    dia.run()
    Gtk.main()
    return trans.exit == enums.EXIT_SUCCESS


def _check_updates_gtk():
    cmd = ["/usr/bin/synaptic-pkexec",
           "--update-at-startup",
           "--non-interactive",
           "--hide-main-window",
           ]
    subprocess.call(cmd)


def check_updates():
    """ check for updates either with aptdaemon or synaptic """
    if HAVE_APTDAEMON:
        return _check_updates_aptdaemon()
    else:
        return _check_updates_gtk()


# start packagemanager
def start_packagemanager():
    if os.path.exists("/usr/bin/synaptic-pkexec"):
        cmd = ["/usr/bin/synaptic-pkexec"]
        return subprocess.call(cmd)
    elif os.path.exists("/usr/bin/software-center"):
        return subprocess.call(["/usr/bin/software-center"])
    else:
        logging.error("neither synaptic nor software-center installed")


# add cdrom
def _add_cdrom_sp(mount_path):
    from gi.repository import Gtk
    import dbus
    import dbus.mainloop.glib
    bus = dbus.SystemBus(mainloop=dbus.mainloop.glib.DBusGMainLoop())
    proxy = bus.get_object("com.ubuntu.SoftwareProperties", "/")
    backend = dbus.Interface(proxy, "com.ubuntu.SoftwareProperties")
    backend.AddCdromSource()
    backend.connect_to_signal(
        "SourcesListModified", Gtk.main_quit)
    backend.connect_to_signal(
        "CdromScanFailed", Gtk.main_quit)
    Gtk.main()
    if os.path.exists("/usr/bin/software-center"):
        subprocess.call(["/usr/bin/software-center"])


def _add_cdrom_synaptic(mount_path):
    cmd = ["/usr/bin/synaptic-pkexec", "--add-cdrom", mount_path]
    return subprocess.call(cmd)


def add_cdrom(mount_path):
    if os.path.exists("/usr/bin/synaptic-pkexec"):
        _add_cdrom_synaptic(mount_path)
    else:
        _add_cdrom_sp(mount_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='backend helper for update-notifier')
    parser.add_argument(
        '--debug', default=False, action="store_true",
        help='extra debug output')
    subparser = parser.add_subparsers(title="Commands")
    # show_update  - update-manager
    command = subparser.add_parser("show_updates")
    command.set_defaults(command="show_updates")
    # install_all - synaptic/aptdaemon install noninteractivly
    command = subparser.add_parser("install_all_updates")
    command.set_defaults(command="install_all_updates")
    # check_updates - synaptic --reload/aptdaemon reload
    command = subparser.add_parser("check_updates")
    command.set_defaults(command="check_updates")
    # start_pkgmanager
    command = subparser.add_parser("start_packagemanager")
    command.set_defaults(command="start_packagemanager")
    # add_cdrom
    command = subparser.add_parser("add_cdrom")
    command.add_argument("mount_path")
    command.set_defaults(command="add_cdrom")

    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    func_name = args.command
    f_kwargs = {}
    f = globals()[func_name]
    if args.command == "add_cdrom":
        f_kwargs["mount_path"] = args.mount_path
    res = f(**f_kwargs)

    if not res:
        sys.exit(1)
