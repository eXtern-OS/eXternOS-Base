# Copyright (C) 2017, Benjamin Drung <benjamin.drung@profitbricks.com>
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

"""Test suite for distro-info"""

import inspect
import os
import sys
import unittest


def get_source_files():
    """Return a list of sources files/directories (to check with flake8/pylint)"""
    scripts = ["debian-distro-info", "ubuntu-distro-info"]
    modules = ["distro_info_test"]
    py_files = ["distro_info.py", "setup.py"]

    files = []
    for code_file in scripts + modules + py_files:
        is_script = code_file in scripts
        if not os.path.exists(code_file):
            # The alternative path is needed for Debian's pybuild
            alternative = os.path.join(os.environ.get("OLDPWD", ""), code_file)
            code_file = alternative if os.path.exists(alternative) else code_file
        if is_script:
            with open(code_file, "rb") as script_file:
                shebang = script_file.readline().decode("utf-8")
            if ((sys.version_info[0] == 3 and "python3" in shebang) or
                    ("python" in shebang and "python3" not in shebang)):
                files.append(code_file)
        else:
            files.append(code_file)
    return files


def unittest_verbosity():
    """Return the verbosity setting of the currently running unittest
    program, or None if none is running.
    """
    frame = inspect.currentframe()
    while frame:
        self = frame.f_locals.get("self")
        if isinstance(self, unittest.TestProgram):
            return self.verbosity
        frame = frame.f_back
    return None
