# -*- coding: utf-8 -*-
#
# (c) Copyright 20013 HP Development Company, L.P.
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
# Author: Sarbeswar Meher
#

import sys
from .g import *
import socket
from subprocess import Popen, PIPE
from . import utils
from .sixext import  to_string_utf8


def detectNetworkDevices(ttl=4, timeout=10):
    found_devices = {}

    if utils.which("avahi-browse") == '':
        log.error("Avahi-browse is not installed")
        return found_devices

    # Obtain all the resolved services which has service type '_printer._tcp' from avahi-browse
    p = Popen(['avahi-browse', '-kprt', '_printer._tcp'], stdout=PIPE)
    output = to_string_utf8(p.communicate()[0])
    for line in output.splitlines():
        if line.startswith('='):
            bits = line.split(';')
            if bits[2] == 'IPv4' and len(bits[7].split('.')) == 4:
                ip = bits[7]
                port = bits[8]
                # Run through the offered addresses and see if we have a bound local
                # address for it.
                try:
                    res = socket.getaddrinfo(ip, port, 0, 0, 0, socket.AI_ADDRCONFIG)
                    if res:
                        y = {'num_devices' : 1, 'num_ports': 1, 'product_id' : '', 'mac': '',
                             'status_code': 0, 'device2': '0', 'device3': '0', 'note': ''}
                        y['ip'] = ip
                        y['hn'] = bits[6].replace('.local', '')
                        details = bits[9].split('" "')
                        for item in details:
                            key, value = item.split('=', 1)
                            if key == 'ty':
                                y['mdns'] = value
                                y['device1'] = "MFG:Hewlett-Packard;MDL:%s;CLS:PRINTER;" % value
                                break
                        found_devices[y['ip']] = y
                        log.debug("ip=%s hn=%s ty=%s" %(ip,y['hn'], y['mdns']))
                except socket.gaierror:
                    pass
    log.debug("Found %d devices" % len(found_devices))

    return found_devices
