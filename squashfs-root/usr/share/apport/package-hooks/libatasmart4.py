'''apport package hook for libatasmart

(c) 2009 Canonical Ltd.
Author: Martin Pitt <martin.pitt@ubuntu.com>
'''

import os
import os.path
import apport.hookutils
import dbus

UD = 'org.freedesktop.UDisks'

def add_info(report):
    report['UdisksDump'] = apport.hookutils.command_output(['udisks', '--dump'])
    report['Udisks2Dump'] = apport.hookutils.command_output(['udisksctl', 'dump'])

    # grab SMART blobs
    dkd = dbus.Interface(dbus.SystemBus().get_object(UD,
        '/org/freedesktop/UDisks'), UD)
    for d in dkd.EnumerateDevices():
        dev_props = dbus.Interface(dbus.SystemBus().get_object(UD, d),
                dbus.PROPERTIES_IFACE)
        blob = dev_props.Get(UD, 'DriveAtaSmartBlob')
        if len(blob) > 0:
            report['AtaSmartBlob_' + os.path.basename(d)] = ''.join(map(chr, blob))

if __name__ == '__main__':
    r = {}
    add_info(r)
    for k, v in r.items():
        print('%s: "%s"' % (k, v))

