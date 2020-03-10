# test_help.py - Ensure scripts can run --help.
#
# Copyright (C) 2010, Stefano Rivera <stefanor@debian.org>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

import fcntl
import os
import select
import signal
import subprocess
import time

import setup
from distro_info_test import unittest

TIMEOUT = 5


class HelpTestCase(unittest.TestCase):
    @classmethod
    def populate(cls):
        for script in setup.SCRIPTS:
            setattr(cls, 'test_' + script, cls.make_help_tester(script))

    @classmethod
    def make_help_tester(cls, script):
        def tester(self):
            null = open('/dev/null', 'r')
            process = subprocess.Popen(['./' + script, '--help'],
                                       close_fds=True, stdin=null,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            started = time.time()
            out = []

            fds = [process.stdout.fileno(), process.stderr.fileno()]
            for file_descriptor in fds:
                fcntl.fcntl(file_descriptor, fcntl.F_SETFL,
                            fcntl.fcntl(file_descriptor, fcntl.F_GETFL) | os.O_NONBLOCK)

            while time.time() - started < TIMEOUT:
                for file_descriptor in select.select(fds, [], fds, TIMEOUT)[0]:
                    out.append(os.read(file_descriptor, 1024))
                if process.poll() is not None:
                    break

            if process.poll() is None:
                os.kill(process.pid, signal.SIGTERM)
                time.sleep(1)
                if process.poll() is None:
                    os.kill(process.pid, signal.SIGKILL)
            null.close()

            self.assertEqual(process.poll(), 0,
                             "%s failed to return usage within %i seconds.\n"
                             "Output:\n%s"
                             % (script, TIMEOUT, ''.encode('ascii').join(out)))
            process.stdout.close()
            process.stderr.close()
        return tester
