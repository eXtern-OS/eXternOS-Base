# Copyright (C) 2017-2018, Benjamin Drung <bdrung@debian.org>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""test_flake8.py - Run flake8 check"""

import subprocess
import sys
import unittest

from . import get_source_files, unittest_verbosity


class Flake8TestCase(unittest.TestCase):
    """
    This unittest class provides a test that runs the flake8 code
    checker (which combines pycodestyle and pyflakes) on the Python
    source code. The list of source files is provided by the
    get_source_files() function.
    """

    def test_flake8(self):
        """Test: Run flake8 on Python source code"""
        with open("/proc/self/cmdline", "r") as cmdline_file:
            python_binary = cmdline_file.read().split("\0")[0]
        cmd = [python_binary, "-m", "flake8", "--max-line-length=99"] + get_source_files()
        if unittest_verbosity() >= 2:
            sys.stderr.write("Running following command:\n{}\n".format(" ".join(cmd)))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, close_fds=True)

        out, err = process.communicate()
        if process.returncode != 0:
            msgs = []
            if err:
                msgs.append("flake8 exited with code {} and has unexpected output on stderr:\n{}"
                            .format(process.returncode, err.decode().rstrip()))
            if out:
                msgs.append("flake8 found issues:\n{}".format(out.decode().rstrip()))
            if not msgs:
                msgs.append("flake8 exited with code {} and has no output on stdout or stderr."
                            .format(process.returncode))
            self.fail("\n".join(msgs))
