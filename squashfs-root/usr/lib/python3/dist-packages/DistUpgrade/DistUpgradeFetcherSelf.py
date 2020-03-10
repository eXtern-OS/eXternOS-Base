# DistUpgradeFetcherSelf.py
#  
#  Copyright (c) 2007-2012 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import logging
import shutil

from .DistUpgradeFetcherCore import DistUpgradeFetcherCore


class DistUpgradeFetcherSelf(DistUpgradeFetcherCore):
    def __init__(self, new_dist, progress, options, view):
        DistUpgradeFetcherCore.__init__(self, new_dist, progress)
        self.view = view
        # user chose to use the network, otherwise it would not be
        # possible to download self
        self.run_options += ["--with-network"]
        # make sure to run self with proper options
        if options.cdromPath is not None:
            self.run_options += ["--cdrom=%s" % options.cdromPath]
        if options.frontend is not None:
            self.run_options += ["--frontend=%s" % options.frontend]

    def error(self, summary, message):
        return self.view.error(summary, message)

    def runDistUpgrader(self):
        " overwrite to ensure that the log is copied "
        # copy log so it isn't overwritten
        logging.info("runDistUpgrader() called, re-exec self")
        logging.shutdown()
        shutil.copy("/var/log/dist-upgrade/main.log",
                    "/var/log/dist-upgrade/main_update_self.log")
        # re-exec self
        DistUpgradeFetcherCore.runDistUpgrader(self)
