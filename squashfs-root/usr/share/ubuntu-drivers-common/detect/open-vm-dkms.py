# ubuntu-drivers-common custom detect plugin for open-vm-dkms
#
# (C) 2012 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>

import os.path
import os


def detect(apt_cache):
    if os.path.exists('/sys/module/vmxnet'):
        return ['open-vm-dkms']
