'''apport package hook for udev

(c) 2009 Canonical Ltd.
Author: Martin Pitt <martin.pitt@ubuntu.com>
'''

import os
import apport.hookutils

def add_info(report):
    apport.hookutils.attach_hardware(report)

    user_rules = []
    for f in os.listdir('/etc/udev/rules.d'):
        if not f.startswith('70-persistent-') and f != 'README':
            user_rules.append(f)

    if user_rules:
        report['CustomUdevRuleFiles'] = ' '.join(user_rules)
