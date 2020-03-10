'''apport package hook for ureadahead

(c) 2009 Canonical Ltd.
Author: Scott James Remnant <scott@ubuntu.com>
'''

import os
import apport.hookutils

def add_info(report):
    for f in os.listdir('/var/lib/ureadahead'):
        if f == 'pack':
            report['PackDump'] = apport.hookutils.command_output(['ureadahead', '--dump'])
        elif f.endswith('.pack'):
            report['PackDump'+f[:-5].title()] = apport.hookutils.command_output(['ureadahead', '--dump'])
