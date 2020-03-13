# Copyright © 2012-2013 Piotr Ożarowski <piotr@debian.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import logging
from glob import glob1
from os.path import dirname

log = logging.getLogger('dhpython')

plugins = {}
for i in (i[7:-3] for i in glob1(dirname(__file__), 'plugin_*.py')):
    try:
        module = __import__("dhpython.build.plugin_%s" % i, fromlist=[i])
        module.BuildSystem.NAME = i
        module.BuildSystem.is_usable()
        plugins[i] = module.BuildSystem
    except Exception as err:
        if log.level < logging.INFO:
            log.debug("cannot initialize '%s' plugin", i, exc_info=True)
        else:
            log.debug("cannot initialize '%s' plugin: %s", i, err)
