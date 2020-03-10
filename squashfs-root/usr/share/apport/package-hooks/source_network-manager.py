'''Apport package hook for Network Manager

(c) 2008 Canonical Ltd.
Contributors:
Matt Zimmerman <mdz@canonical.com>
Martin Pitt <martin.pitt@canonical.com>
Mathieu Trudel-Lapierre <mathieu.trudel-lapierre@canonical.com>
Thomas Bechtold <thomasbechtold@jpberlin.de>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

import os
import subprocess
from apport.hookutils import *

def _network_interfaces():
    interfaces = []
    output = command_output(['ls', '-1', '/sys/class/net'])
    for device in output.split('\n'):
       interfaces.append(device)

    return interfaces

def _device_details(device):
    details = command_output(['udevadm', 'info', '--query=all', '--path', '/sys/class/net/%s' % device])

    # add the only extra thing of use from hal we don't get from udev.
    details = details + "\nX: INTERFACE_MAC="
    details = details + command_output(['cat', '/sys/class/net/%s/address' % device])
    return details

def add_info(report, ui=None):
    attach_network(report)
    attach_wifi(report)

    #this is the old config file (still read by NM if available)
    attach_file_if_exists(report, '/etc/NetworkManager/nm-system-settings.conf', 'nm-system-settings.conf')

    #the new default config file
    attach_file_if_exists(report, '/etc/NetworkManager/NetworkManager.conf', 'NetworkManager.conf')

    # attach NetworkManager.state: it gives us good hints in rfkill-related bugs.
    attach_file_if_exists(report, '/var/lib/NetworkManager/NetworkManager.state', 'NetworkManager.state')

    for interface in _network_interfaces():
        key = 'NetDevice.%s' % interface
        report[key] = _device_details(interface)

    interesting_modules = { 'ndiswrapper' : 'driver-ndiswrapper',
                            'ath_hal' : 'driver-madwifi',
                            'b44' : 'driver-b44' }
    interesting_modules_loaded = []
    tags = []
    for line in open('/proc/modules'):
        module = line.split()[0]
        if module in interesting_modules:
            tags.append(interesting_modules[module])
            interesting_modules_loaded.append(module)

    if interesting_modules_loaded:
        report['InterestingModules'] = ' '.join(interesting_modules_loaded)
        report.setdefault('Tags', '')
        report['Tags'] += ' ' + ' '.join(tags)

    #add output of nmcli
    report['nmcli-nm'] = command_output(['nmcli', '-f', 'all', 'gen'])
    report['nmcli-dev'] = command_output(['nmcli', '-f', 'all', 'dev'])
    report['nmcli-con'] = command_output(['nmcli', '-f', 'all', 'con'])


## Only for debugging ##
if __name__ == '__main__':
    report = {}
    report['CrashDB'] = 'ubuntu'
    add_info(report, None)
    for key in report:
        print('%s: %s' % (key, report[key]))
