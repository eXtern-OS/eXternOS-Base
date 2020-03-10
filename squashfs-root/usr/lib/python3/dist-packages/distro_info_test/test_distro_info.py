# test_distro_info.py - Test suite for distro_info
#
# Copyright (C) 2011, Benjamin Drung <bdrung@debian.org>
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

"""Test suite for distro_info"""

import datetime

from distro_info_test import unittest
from distro_info import DebianDistroInfo, UbuntuDistroInfo


class DebianDistroInfoTestCase(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """TestCase object for distro_info.DebianDistroInfo"""

    def setUp(self):  # pylint: disable=invalid-name
        self._distro_info = DebianDistroInfo()
        self._date = datetime.date(2011, 1, 10)

    def test_all(self):
        """Test: List all known Debian distributions."""
        all_distros = set(["buzz", "rex", "bo", "hamm", "slink", "potato",
                           "woody", "sarge", "etch", "lenny", "squeeze", "sid",
                           "experimental"])
        self.assertEqual(all_distros - set(self._distro_info.all), set())

    def test_devel(self):
        """Test: Get latest development Debian distribution."""
        self.assertEqual(self._distro_info.devel(self._date), "sid")

    def test_old(self):
        """Test: Get old (stable) Debian distribution."""
        self.assertEqual(self._distro_info.old(self._date), "etch")

    def test_stable(self):
        """Test: Get latest stable Debian distribution."""
        self.assertEqual(self._distro_info.stable(self._date), "lenny")

    def test_supported(self):
        """Test: List all supported Debian distribution."""
        self.assertEqual(self._distro_info.supported(self._date),
                         ["lenny", "squeeze", "sid", "experimental"])

    def test_testing(self):
        """Test: Get latest testing Debian distribution."""
        self.assertEqual(self._distro_info.testing(self._date), "squeeze")

    def test_valid(self):
        """Test: Check for valid Debian distribution."""
        self.assertTrue(self._distro_info.valid("sid"))
        self.assertTrue(self._distro_info.valid("stable"))
        self.assertFalse(self._distro_info.valid("foobar"))

    def test_unsupported(self):
        """Test: List all unsupported Debian distribution."""
        unsupported = ["buzz", "rex", "bo", "hamm", "slink", "potato", "woody",
                       "sarge", "etch"]
        self.assertEqual(self._distro_info.unsupported(self._date), unsupported)

    def test_codename(self):
        """Test: Codename decoding"""
        self.assertIsNone(self._distro_info.codename('foobar'))
        self.assertEqual(self._distro_info.codename('testing', self._date),
                         self._distro_info.testing(self._date))

    def test_codename_result(self):
        """Test: Check result set to codename."""
        self.assertEqual(self._distro_info.old(self._date, "codename"), "etch")
        self.assertEqual(self._distro_info.devel(self._date, result="codename"),
                         "sid")

    def test_fullname(self):
        """Test: Check result set to fullname."""
        self.assertEqual(self._distro_info.stable(self._date, "fullname"),
                         'Debian 5.0 "Lenny"')
        result = self._distro_info.testing(self._date, result="fullname")
        self.assertEqual(result, 'Debian 6.0 "Squeeze"')

    def test_release(self):
        """Test: Check result set to release."""
        self.assertEqual(self._distro_info.devel(self._date, "release"), "")
        self.assertEqual(self._distro_info.testing(self._date, "release"),
                         "6.0")
        self.assertEqual(self._distro_info.stable(self._date, result="release"),
                         "5.0")


class UbuntuDistroInfoTestCase(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """TestCase object for distro_info.UbuntuDistroInfo"""

    def setUp(self):  # pylint: disable=invalid-name
        self._distro_info = UbuntuDistroInfo()
        self._date = datetime.date(2011, 1, 10)

    def test_all(self):
        """Test: List all known Ubuntu distributions."""
        all_distros = set(["warty", "hoary", "breezy", "dapper", "edgy",
                           "feisty", "gutsy", "hardy", "intrepid", "jaunty",
                           "karmic", "lucid", "maverick", "natty"])
        self.assertEqual(all_distros - set(self._distro_info.all), set())

    def test_devel(self):
        """Test: Get latest development Ubuntu distribution."""
        self.assertEqual(self._distro_info.devel(self._date), "natty")

    def test_lts(self):
        """Test: Get latest long term support (LTS) Ubuntu distribution."""
        self.assertEqual(self._distro_info.lts(self._date), "lucid")

    def test_stable(self):
        """Test: Get latest stable Ubuntu distribution."""
        self.assertEqual(self._distro_info.stable(self._date), "maverick")

    def test_supported(self):
        """Test: List all supported Ubuntu distribution."""
        supported = ["dapper", "hardy", "karmic", "lucid", "maverick", "natty"]
        self.assertEqual(self._distro_info.supported(self._date), supported)

    def test_unsupported(self):
        """Test: List all unsupported Ubuntu distributions."""
        unsupported = ["warty", "hoary", "breezy", "edgy", "feisty", "gutsy",
                       "intrepid", "jaunty"]
        self.assertEqual(self._distro_info.unsupported(self._date), unsupported)

    def test_current_unsupported(self):
        """Test: List all unsupported Ubuntu distributions today."""
        unsupported = set(["warty", "hoary", "breezy", "edgy", "feisty",
                           "gutsy", "intrepid", "jaunty"])
        self.assertEqual(unsupported -
                         set(self._distro_info.unsupported()), set())

    def test_valid(self):
        """Test: Check for valid Ubuntu distribution."""
        self.assertTrue(self._distro_info.valid("lucid"))
        self.assertFalse(self._distro_info.valid("42"))

    def test_is_lts(self):
        """Test: Check if Ubuntu distribution is an LTS."""
        self.assertTrue(self._distro_info.is_lts("lucid"))
        self.assertFalse(self._distro_info.is_lts("42"))
        self.assertFalse(self._distro_info.is_lts("warty"))

    def test_codename(self):
        """Test: Check result set to codename."""
        self.assertEqual(self._distro_info.lts(self._date, "codename"), "lucid")
        self.assertEqual(self._distro_info.devel(self._date, result="codename"),
                         "natty")

    def test_fullname(self):
        """Test: Check result set to fullname."""
        self.assertEqual(self._distro_info.stable(self._date, "fullname"),
                         'Ubuntu 10.10 "Maverick Meerkat"')
        self.assertEqual(self._distro_info.lts(self._date, result="fullname"),
                         'Ubuntu 10.04 LTS "Lucid Lynx"')

    def test_release(self):
        """Test: Check result set to release."""
        self.assertEqual(self._distro_info.devel(self._date, "release"),
                         "11.04")
        self.assertEqual(self._distro_info.lts(self._date, result="release"),
                         "10.04 LTS")
