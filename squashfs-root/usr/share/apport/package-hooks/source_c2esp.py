'''apport package hook for c2esp

(c) 2009 Canonical Ltd.
Author: Brian Murray <brian@ubuntu.com>
'''

from apport.hookutils import *

def add_info(report):
    attach_hardware(report)
    attach_printing(report)
