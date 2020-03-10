# helpviewer.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import os
import subprocess

# Hardcoded list of available help viewers
# FIXME: khelpcenter support would be nice
#KNOWN_VIEWERS = ["/usr/bin/yelp", "/usr/bin/khelpcenter"]
KNOWN_VIEWERS = ["/usr/bin/yelp"]


class HelpViewer:
    def __init__(self, docu):
        self.command = []
        self.docu = docu
        for viewer in KNOWN_VIEWERS:
            if os.path.exists(viewer):
                self.command = [viewer, "help:%s" % docu]
                break

    def check(self):
        """check if a viewer is available"""
        if self.command == []:
            return False
        else:
            return True

    def run(self):
        """open the documentation in the viewer"""
        # avoid running the help viewer as root
        if os.getuid() == 0 and 'SUDO_USER' in os.environ:
            self.command = ['sudo', '-u', os.environ['SUDO_USER']] +\
                self.command
        subprocess.Popen(self.command)
