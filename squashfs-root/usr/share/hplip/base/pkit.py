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
# Author: Stan Dolson , Goutam Kodu
#

# Std Lib
import os
import os.path
import sys

# Local
from .g import *
from .codes import *
from . import utils, password
from installer import pluginhandler

# DBus
import dbus
import dbus.service

if PY3:
    try:
        from gi._gobject import MainLoop
    except:
        from gi.repository.GLib import MainLoop
else:
    from gobject import MainLoop

import warnings
# Ignore: .../dbus/connection.py:242: DeprecationWarning: object.__init__() takes no parameters
# (occurring on Python 2.6/dBus 0.83/Ubuntu 9.04)
warnings.simplefilter("ignore", DeprecationWarning)


class AccessDeniedException(dbus.DBusException):
    _dbus_error_name = 'com.hp.hplip.AccessDeniedException'

class UnsupportedException(dbus.DBusException):
    _dbus_error_name = 'com.hp.hplip.UnsupportedException'

class UsageError(dbus.DBusException):
    _dbus_error_name = 'com.hp.hplip.UsageError'


POLICY_KIT_ACTION = "com.hp.hplip"
INSTALL_PLUGIN_ACTION = "com.hp.hplip.installplugin"


def get_service_bus():
    return dbus.SystemBus()


def get_service(bus=None):
    if not bus:
        bus = get_service_bus()

    service = bus.get_object(BackendService.SERVICE_NAME, '/')
    service = dbus.Interface(service, BackendService.INTERFACE_NAME)
    return service


class PolicyKitAuthentication(object):
    def __init__(self):
        super(PolicyKitAuthentication, self).__init__()
        self.pkit = None
        self.auth = None


    def is_authorized(self, action_id, pid=None):
        if pid == None:
            pid = os.getpid()

        pid = dbus.UInt32(pid)

        authorized = self.policy_kit.IsProcessAuthorized(action_id, pid, False)
        log.debug("is_authorized(%s) = %r" % (action_id, authorized))

        return (authorized == 'yes')


    def obtain_authorization(self, action_id, widget=None):
        if self.is_authorized(action_id):
            return True

        xid = (widget and widget.get_toplevel().window.xid or 0)
        xid, pid = dbus.UInt32(xid), dbus.UInt32(os.getpid())

        granted = self.auth_agent.ObtainAuthorization(action_id, xid, pid)
        log.debug("obtain_authorization(%s) = %r" % (action_id, granted))

        return bool(granted)


    def get_policy_kit(self):
        if self.pkit:
            return self.pkit

        service = dbus.SystemBus().get_object('org.freedesktop.PolicyKit', '/')
        self.pkit = dbus.Interface(service, 'org.freedesktop.PolicyKit')
        return self.pkit

    policy_kit = property(get_policy_kit)


    def get_auth_agent(self):
        if self.auth:
            return self.auth

        self.auth = dbus.SessionBus().get_object(
            'org.freedesktop.PolicyKit.AuthenticationAgent', '/')
        return self.auth

    auth_agent = property(get_auth_agent)



class PolicyKitService(dbus.service.Object):
    def check_permission_v0(self, sender, action=POLICY_KIT_ACTION):
        if not sender:
            log.error("Session not authorized by PolicyKit")
            raise AccessDeniedException('Session not authorized by PolicyKit')

        try:
            policy_auth = PolicyKitAuthentication()
            bus = dbus.SystemBus()

            dbus_object = bus.get_object('org.freedesktop.DBus', '/')
            dbus_object = dbus.Interface(dbus_object, 'org.freedesktop.DBus')

            pid = dbus.UInt32(dbus_object.GetConnectionUnixProcessID(sender))

            granted = policy_auth.is_authorized(action, pid)
            if not granted:
                log.error("Process not authorized by PolicyKit")
                raise AccessDeniedException('Process not authorized by PolicyKit')

            granted = policy_auth.policy_kit.IsSystemBusNameAuthorized(action,
                                                                       sender,
                                                                       False)
            if granted != 'yes':
                log.error("Session not authorized by PolicyKit version 0")
                raise AccessDeniedException('Session not authorized by PolicyKit')

        except AccessDeniedException:
            log.warning("AccessDeniedException")
            raise

        except dbus.DBusException as ex:
            log.warning("AccessDeniedException %r", ex)
            raise AccessDeniedException(ex.message)


    def check_permission_v1(self, sender, connection, action=POLICY_KIT_ACTION):
        if not sender or not connection:
            log.error("Session not authorized by PolicyKit")
            raise AccessDeniedException('Session not authorized by PolicyKit')

        system_bus = dbus.SystemBus()
        obj = system_bus.get_object("org.freedesktop.PolicyKit1",
                                    "/org/freedesktop/PolicyKit1/Authority",
                                    "org.freedesktop.PolicyKit1.Authority")
        policy_kit = dbus.Interface(obj, "org.freedesktop.PolicyKit1.Authority")

        subject = (
           'system-bus-name',
            { 'name' : dbus.String(sender, variant_level = 1) }
        )
        details = { '' : '' }
        flags = dbus.UInt32(1)         # AllowUserInteraction = 0x00000001
        cancel_id = ''

        (ok, notused, details) = \
            policy_kit.CheckAuthorization(subject,
                                          action,
                                          details,
                                          flags,
                                          cancel_id)
        if not ok:
            log.error("Session not authorized by PolicyKit version 1")
            raise AccessDeniedException("Session not authorized by PolicyKit")

        return ok


if utils.to_bool(sys_conf.get('configure', 'policy-kit')):
    class BackendService(PolicyKitService):
        INTERFACE_NAME = 'com.hp.hplip'
        SERVICE_NAME   = 'com.hp.hplip'

        def __init__(self, connection=None, path='/'):
            if connection is None:
                connection = get_service_bus()

            super(BackendService, self).__init__(connection, path)

            self.name = dbus.service.BusName(self.SERVICE_NAME, connection)
            self.loop = MainLoop()
            self.version = 0
            log.set_level("debug")

        def run(self, version=None):
            if version is None:
                version = policykit_version()
                if version is None:
                    log.error("Unable to determine installed PolicyKit version")
                    return

            self.version = version
            log.debug("Starting back-end service loop (version %d)" % version)

            self.loop.run()


        @dbus.service.method(dbus_interface=INTERFACE_NAME,
                                in_signature='s', out_signature='b',
                                sender_keyword='sender',
                                connection_keyword='connection')
        def installPlugin(self, src_dir, sender=None, connection=None):
            if self.version == 0:
                try:
                    self.check_permission_v0(sender, INSTALL_PLUGIN_ACTION)
                except AccessDeniedException as e:
                    log.error("installPlugin:  Failed due to permission error [%s]" %e)
                    return False

            elif self.version == 1:
                if not self.check_permission_v1(sender,
                                                connection,
                                                INSTALL_PLUGIN_ACTION):
                    return False

            else:
                log.error("installPlugin: invalid PolicyKit version %d" % self.version)
                return False

            log.debug("installPlugin: installing from '%s'" % src_dir)
            try:
                from installer import pluginhandler
            except ImportError as e:
                log.error("Failed to Import pluginhandler")
                return False

            pluginObj = pluginhandler.PluginHandle()
            if not pluginObj.copyFiles(src_dir):
                log.error("Plugin installation failed")
                return False

            return True


        @dbus.service.method(dbus_interface=INTERFACE_NAME,
                                in_signature='s', out_signature='b',
                                sender_keyword='sender',
                                connection_keyword='connection')
        def shutdown(self, arg, sender=None, connection=None):
            log.debug("Stopping backend service")
            self.loop.quit()

            return True



class PolicyKit(object):
    def __init__(self, version=None):
        if version is None:
            version = policykit_version()
            if version is None:
                log.debug("Unable to determine installed PolicyKit version")
                return

        self.bus = dbus.SystemBus()
        self.obj = self.bus.get_object(POLICY_KIT_ACTION, "/")
        self.iface = dbus.Interface(self.obj, dbus_interface=POLICY_KIT_ACTION)
        self.version = version

    def installPlugin(self, src_dir):
        if self.version == 0:
            auth = PolicyKitAuthentication()
            if not auth.is_authorized(INSTALL_PLUGIN_ACTION):
                if not auth.obtain_authorization(INSTALL_PLUGIN_ACTION):
                    return None

        try:
            ok = self.iface.installPlugin(src_dir)
            return ok
        except dbus.DBusException as e:
            log.debug("installPlugin: %s" % str(e))
            return False


    def shutdown(self):
        if self.version == 0:
            auth = PolicyKitAuthentication()
            if not auth.is_authorized(INSTALL_PLUGIN_ACTION):
                if not auth.obtain_authorization(INSTALL_PLUGIN_ACTION):
                    return None

        try:
            ok = self.iface.shutdown("")
            return ok
        except dbus.DBusException as e:
            log.debug("shutdown: %s" % str(e))
            return False





def run_plugin_command(required=True, plugin_reason=PLUGIN_REASON_NONE, Mode = GUI_MODE):

    if utils.to_bool(sys_conf.get('configure', 'policy-kit')):
        try:
            obj = PolicyKit()
            su_sudo = "%s"
            need_sudo = False
            log.debug("Using PolicyKit for authentication")
        except dbus.DBusException as ex:
            log.error("PolicyKit NOT installed when configured for use. [%s]"%ex)

    req = '--required'
    if not required:
        req = '--optional'

    if utils.which("hp-plugin"):
        p_path="hp-plugin"
    else:
        p_path="python ./plugin.py"

    cmd = "%s -u %s --reason %s" %(p_path, req, plugin_reason)   
    log.debug("%s" % cmd)
    status = os_utils.execute(cmd)

    return (status == 0, True)


def policykit_version():
    if os.path.isdir("/usr/share/polkit-1"):
        return 1
    elif os.path.isdir("/usr/share/PolicyKit"):
        return 0
    else:
        return None
