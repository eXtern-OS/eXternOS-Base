'''apport package hook for evince

(c) 2009-2011 Canonical Ltd.
Author:
Jamie Strandboge <jamie@ubuntu.com>

'''

from apport.hookutils import *
from os import path
import re

def add_info(report):
    attach_conffiles(report, 'evince')
    attach_related_packages(report, ['apparmor', 'libapparmor1',
        'libapparmor-perl', 'apparmor-utils', 'auditd', 'libaudit1'])

    attach_mac_events(report, ['/usr/bin/evince',
                               '/usr/bin/evince-previewer',
                               '/usr/bin/evince-thumbnailer'])
