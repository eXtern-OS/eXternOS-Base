'''apport package hook for udisks2

(c) 2011 Canonical Ltd.
Author: Martin Pitt <martin.pitt@ubuntu.com>
'''

import os
import os.path
import apport.hookutils
import dbus

def add_info(report):
    apport.hookutils.attach_hardware(report)

    user_rules = []
    for f in os.listdir('/etc/udev/rules.d'):
        if not f.startswith('70-persistent-') and f != 'README':
            user_rules.append(f)

    if user_rules:
        report['CustomUdevRuleFiles'] = ' '.join(user_rules)

    report['UDisksDump'] = apport.hookutils.command_output(['udisksctl', 'dump'])
    report['Mounts'] = apport.hookutils.command_output(['mount'])

if __name__ == '__main__':
    r = {}
    add_info(r)
    for k, v in r.items():
        print('%s: "%s"' % (k, v))

