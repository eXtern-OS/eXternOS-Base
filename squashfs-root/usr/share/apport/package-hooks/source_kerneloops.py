'''apport package hook for kerneloops

(c) 2014 Canonical Ltd.
Author: Brian Murray <brian@ubuntu.com>
'''

from apport import hookutils
import re

def add_info(report):

    hookutils.attach_dmesg(report)
    report['KernelSyslog'] = hookutils.recent_syslog(re.compile(r'kernel:'))
