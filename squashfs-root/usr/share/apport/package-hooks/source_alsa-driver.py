'''apport package hook for ALSA packages

(c) 2009 Canonical Ltd.
Author:
Matt Zimmerman <mdz@ubuntu.com>

'''

from apport.hookutils import *

def add_info(report):
	attach_alsa(report)
