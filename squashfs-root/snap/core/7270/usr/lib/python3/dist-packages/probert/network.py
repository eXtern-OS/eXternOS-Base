# Copyright 2015 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import ipaddress
import logging
import os

import pyudev

from probert import _nl80211, _rtnetlink
from probert.utils import udev_get_attributes

log = logging.getLogger('probert.network')

# Standard interface flags (net/if.h)
IFF_UP = 0x1                   # Interface is up.
IFF_BROADCAST = 0x2            # Broadcast address valid.
IFF_DEBUG = 0x4                # Turn on debugging.
IFF_LOOPBACK = 0x8             # Is a loopback net.
IFF_POINTOPOINT = 0x10         # Interface is point-to-point link.
IFF_NOTRAILERS = 0x20          # Avoid use of trailers.
IFF_RUNNING = 0x40             # Resources allocated.
IFF_NOARP = 0x80               # No address resolution protocol.
IFF_PROMISC = 0x100            # Receive all packets.
IFF_ALLMULTI = 0x200           # Receive all multicast packets.
IFF_MASTER = 0x400             # Master of a load balancer.
IFF_SLAVE = 0x800              # Slave of a load balancer.
IFF_MULTICAST = 0x1000         # Supports multicast.
IFF_PORTSEL = 0x2000           # Can set media type.
IFF_AUTOMEDIA = 0x4000         # Auto media select active.

IFA_F_PERMANENT = 0x80

def _compute_type(iface):
    if not iface:
        return '???'

    sysfs_path = os.path.join('/sys/class/net', iface)
    if not os.path.exists(sysfs_path):
        print('No sysfs path to {}'.format(sysfs_path))
        return None

    DEV_TYPE = '???'

    with open(os.path.join(sysfs_path, 'type')) as t:
        type_value = t.read().split('\n')[0]
    if type_value == '1':
        DEV_TYPE = 'eth'
        if os.path.isdir(os.path.join(sysfs_path, 'wireless')) or \
           os.path.islink(os.path.join(sysfs_path, 'phy80211')):
            DEV_TYPE = 'wlan'
        elif os.path.isdir(os.path.join(sysfs_path, 'bridge')):
            DEV_TYPE = 'bridge'
        elif os.path.isfile(os.path.join('/proc/net/vlan', iface)):
            DEV_TYPE = 'vlan'
        elif os.path.isdir(os.path.join(sysfs_path, 'bonding')):
            DEV_TYPE = 'bond'
        elif os.path.isfile(os.path.join(sysfs_path, 'tun_flags')):
            DEV_TYPE = 'tap'
        elif os.path.isdir(
                os.path.join('/sys/devices/virtual/net', iface)):
            if iface.startswith('dummy'):
                DEV_TYPE = 'dummy'
    elif type_value == '24':  # firewire ;; IEEE 1394 - RFC 2734
        DEV_TYPE = 'eth'
    elif type_value == '32':  # InfiniBand
        if os.path.isdir(os.path.join(sysfs_path, 'bonding')):
            DEV_TYPE = 'bond'
        elif os.path.isdir(os.path.join(sysfs_path, 'create_child')):
            DEV_TYPE = 'ib'
        else:
            DEV_TYPE = 'ibchild'
    elif type_value == '512':
        DEV_TYPE = 'ppp'
    elif type_value == '768':
        DEV_TYPE = 'ipip'      # IPIP tunnel
    elif type_value == '769':
        DEV_TYPE = 'ip6tnl'   # IP6IP6 tunnel
    elif type_value == '772':
        DEV_TYPE = 'lo'
    elif type_value == '776':
        DEV_TYPE = 'sit'      # sit0 device - IPv6-in-IPv4
    elif type_value == '778':
        DEV_TYPE = 'gre'      # GRE over IP
    elif type_value == '783':
        DEV_TYPE = 'irda'     # Linux-IrDA
    elif type_value == '801':
        DEV_TYPE = 'wlan_aux'
    elif type_value == '65534':
        DEV_TYPE = 'tun'

    if iface.startswith('ippp') or iface.startswith('isdn'):
        DEV_TYPE = 'isdn'
    elif iface.startswith('mip6mnha'):
        DEV_TYPE = 'mip6mnha'

    if len(DEV_TYPE) == 0:
        print('Failed to determine interface type for {}'.format(iface))
        return None

    return DEV_TYPE


_scope_str = {
    0: 'global',
	200: "site",
	253: "link",
	254: "host",
	255: "nowhere",
}


class Address:

    def __init__(self, netlink_data):
        self.address = ipaddress.ip_interface(netlink_data['local'].decode('latin-1'))
        self.ip = self.address.ip
        self.family = netlink_data['family']
        if netlink_data.get('flags', 0) & IFA_F_PERMANENT:
            self.source = 'static'
        else:
            self.source = 'dhcp'
        scope = netlink_data['scope']
        self.scope = str(_scope_str.get(scope))


class NetworkInfo:
    def __init__(self, netlink_data, udev_data):
        self.update_from_netlink_data(netlink_data)
        self.udev_data = udev_data

        self.hwaddr = self.udev_data['attrs']['address']

        self.type = _compute_type(self.name)
        self.addresses = {}
        self.bond = self._get_bonding()
        self.bridge = self._get_bridging()


        # Wifi only things (set from UdevObserver.wlan_event)
        self.ssid = None
        self.ssids = []
        self.scan_state = None

    def update_from_netlink_data(self, netlink_data):
        self.netlink_data = netlink_data
        self.name = self.netlink_data.get('name', '').decode('utf-8', 'replace')
        self.flags = self.netlink_data['flags']
        self.ifindex = self.netlink_data['ifindex']
        # This is the logic ip from iproute2 uses to determine whether
        # to show NO-CARRIER or not. It only really makes sense for a
        # wired connection.
        self.is_connected = (not (self.flags & IFF_UP)) or (self.flags & IFF_RUNNING)


    def _get_hwvalues(self, keys, missing='Unknown value'):
        for key in keys:
            try:
                return self.udev_data[key]
            except KeyError:
                pass

        return missing

    @property
    def vendor(self):
        keys = [
            'ID_VENDOR_FROM_DATABASE',
            'ID_VENDOR',
            'ID_VENDOR_ID'
        ]
        return self._get_hwvalues(keys=keys, missing='Unknown Vendor')

    @property
    def model(self):
        keys = [
            'ID_MODEL_FROM_DATABASE',
            'ID_MODEL',
            'ID_MODEL_ID'
        ]
        return self._get_hwvalues(keys=keys, missing='Unknown Model')

    @property
    def driver(self):
        keys = [
            'ID_NET_DRIVER',
            'ID_USB_DRIVER',
        ]
        return self._get_hwvalues(keys=keys, missing='Unknown Driver')

    @property
    def devpath(self):
        keys = ['DEVPATH']
        return self._get_hwvalues(keys=keys, missing='Unknown devpath')

    @property
    def is_virtual(self):
        return self.devpath.startswith('/devices/virtual/')

    def _iface_is_master(self):
        return bool(self.flags & IFF_MASTER) != 0

    def _iface_is_slave(self):
        return bool(self.flags & IFF_SLAVE) != 0

    def _get_slave_iface_list(self):
        try:
            if self._iface_is_master():
                bond = open('/sys/class/net/%s/bonding/slaves' % self.name).read()
                return bond.split()
        except IOError:
            return []

    def _get_bond_mode(self, ):
        try:
            if self._iface_is_master():
                bond_mode = \
                    open('/sys/class/net/%s/bonding/mode' % self.name).read()
                return bond_mode.split()
        except IOError:
            return None

    def _get_bonding(self):
        ''' return bond structure for iface
           'bond': {
              'is_master': [True|False]
              'is_slave': [True|False]
              'slaves': []
              'mode': in BONDING_MODES.keys() or BONDING_MODES.values()
            }
        '''
        is_master = self._iface_is_master()
        is_slave = self._iface_is_slave()
        slaves = self._get_slave_iface_list()
        mode = self._get_bond_mode()
        if mode:
            mode_name = mode[0]
        else:
            mode_name = None
        bond = {
            'is_master': is_master,
            'is_slave': is_slave,
            'slaves': slaves,
            'mode': mode_name
        }
        return bond

    def _iface_is_bridge(self, ):
        bridge_path = os.path.join('/sys/class/net', self.name, 'bridge')
        return os.path.exists(bridge_path)

    def _iface_is_bridge_port(self):
        bridge_port = os.path.join('/sys/class/net', self.name, 'brport')
        return os.path.exists(bridge_port)

    def _get_bridge_iface_list(self):
        if self._iface_is_bridge():
            bridge_path = os.path.join('/sys/class/net', self.name, 'brif')
            return os.listdir(bridge_path)

        return []

    def _get_bridge_options(self):
        invalid_attrs = ['flush', 'bridge']  # needs root access, not useful

        options = {}
        if self._iface_is_bridge():
            bridge_path = os.path.join('/sys/class/net', self.name, 'bridge')
        elif self._iface_is_bridge_port():
            bridge_path = os.path.join('/sys/class/net', self.name, 'brport')
        else:
            return options

        for bridge_attr_name in [attr for attr in os.listdir(bridge_path)
                                 if attr not in invalid_attrs]:
            bridge_attr_file = os.path.join(bridge_path, bridge_attr_name)
            with open(bridge_attr_file) as bridge_attr:
                options[bridge_attr_name] = bridge_attr.read().strip()

        return options

    def _get_bridging(self):
        ''' return bridge structure for iface
           'bridge': {
              'is_bridge': [True|False],
              'is_port': [True|False],
              'interfaces': [],
              'options': {  # /sys/class/net/brX/bridge/<options key>
                  'sysfs_key': sysfs_value
              },
            }
        '''
        is_bridge = self._iface_is_bridge()
        is_port = self._iface_is_bridge_port()
        interfaces = self._get_bridge_iface_list()
        options = self._get_bridge_options()
        bridge = {
            'is_bridge': is_bridge,
            'is_port': is_port,
            'interfaces': interfaces,
            'options': options,
        }
        return bridge


class Network:

    def __init__(self):
        pass

    def probe(self):
        results = {}
        observer = UdevObserver()
        observer.start()
        for l in observer.links.values():
            results[l.name] = {
                'udev_data' : l.udev_data,
                'hwaddr' : l.hwaddr,
                'type' : l.type,
                'ip' : l.ip,
                'ip_sources' : l.ip_sources,
            }
            if l.type == 'wlan':
                results[l.name]['ssid'] = l.ssid.decode("utf-8")
                results[l.name]['ssids'] = l.ssids
                results[l.name]['scan_state'] = l.scan_state
            if l.type == 'bridge':
                results[l.name]['bridge'] = l.bridge
            if l.type == 'bond':
                results[l.name]['bond'] = l.bond

        print(results)
        return results


class UdevObserver:

    def __init__(self):
        self.links = {}
        self.context = pyudev.Context()

    def start(self):
        self.rtlistener = _rtnetlink.listener(self)
        self.rtlistener.start()

        self._fdmap =  {
            self.rtlistener.fileno(): self.rtlistener.data_ready,
            }

        try:
            self.wlan_listener = _nl80211.listener(self)
            self.wlan_listener.start()
            self._fdmap.update({
                self.wlan_listener.fileno(): self.wlan_listener.data_ready,
                })
        except RuntimeError:
            log.debug('could not start wlan_listener')

        return list(self._fdmap)

    def data_ready(self, fd):
        self._fdmap[fd]()

    def link_change(self, action, data):
        log.debug('link_change %s %s', action, data)
        for k, v in data.items():
            if isinstance(data, bytes):
                data[k] = data.decode('utf-8', 'replace')
        ifindex = data['ifindex']
        if action == 'DEL':
            if ifindex in self.links:
                del self.links[ifindex]
                self.del_link(ifindex)
            return
        if action == 'CHANGE':
            if ifindex in self.links:
                dev = self.links[ifindex]
                # Trigger a scan when a wlan device goes up
                # Not sure if this is required as devices seem to scan as soon
                # as they go up? (in which case this fails with EBUSY, so it's
                # just spam in the logs).
                if dev.type == 'wlan' and (not (dev.flags & IFF_UP)) and (data['flags'] & IFF_UP):
                    try:
                        self.wlan_listener.trigger_scan(ifindex)
                    except RuntimeError:
                        log.exception('on-up trigger_scan failed')
                dev.update_from_netlink_data(data)
            self.update_link(ifindex)
            return
        udev_devices = list(self.context.list_devices(IFINDEX=str(ifindex)))
        if len(udev_devices) == 0:
            # Has disappeared already?
            return
        udev_device = udev_devices[0]
        udev_data = dict(udev_device)
        udev_data['attrs'] = udev_get_attributes(udev_device)
        link = NetworkInfo(data, udev_data)
        self.links[data['ifindex']] = link
        self.new_link(ifindex, link)

    def addr_change(self, action, data):
        log.debug('addr_change %s %s', action, data)
        link = self.links.get(data['ifindex'])
        if link is None:
            return
        ip = data['local'].decode('latin-1')
        if action == 'DEL':
            link.addresses.pop(ip, None)
            return
        link.addresses[ip] = Address(data)

    def route_change(self, action, data):
        log.debug('route_change %s %s', action, data)

    def wlan_event(self, arg):
        log.debug('wlan_event %s', arg)
        ifindex = arg['ifindex']
        if ifindex < 0 or ifindex not in self.links:
            return
        link = self.links[ifindex]
        if arg['cmd'] == 'TRIGGER_SCAN':
            link.scan_state = 'scanning'
        if arg['cmd'] == 'NEW_SCAN_RESULTS' and 'ssids' in arg:
            ssids = set()
            for (ssid, status) in arg['ssids']:
                ssids.add(ssid)
                if status != "no status":
                    link.ssid = ssid
            link.ssids = sorted(ssids)
            link.scan_state = None
        if arg['cmd'] == 'NEW_INTERFACE' or arg['cmd'] == 'ASSOCIATE':
            if len(arg.get('ssids', [])) > 0:
                link.ssid = arg['ssids'][0][0]
        if arg['cmd'] == 'NEW_INTERFACE':
            if link.flags & IFF_UP:
                try:
                    self.wlan_listener.trigger_scan(ifindex)
                except RuntimeError: # Can't trigger a scan as non-root, that's OK.
                    log.exception('initial trigger_scan failed')
            else:
                try:
                    self.rtlistener.set_link_flags(ifindex, IFF_UP)
                except RuntimeError:
                    log.exception('set_link_flags failed')
        if arg['cmd'] == 'DISCONNECT':
            link.ssid = None

    def new_link(self, ifindex, link):
        pass

    def update_link(self, ifindex):
        pass

    def del_link(self, ifindex):
        pass


if __name__ == '__main__':
    import pprint
    import select
    c = UdevObserver()
    fds = c.start()

    pprint.pprint(c.links)

    poll_ob = select.epoll()
    for fd in fds:
        poll_ob.register(fd, select.EPOLLIN)
    while True:
        events = poll_ob.poll()
        for (fd, e) in events:
            c.data_ready(fd)
        pprint.pprint(c.links)
