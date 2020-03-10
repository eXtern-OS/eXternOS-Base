# Copyright 2009 Canonical Ltd.

# This file is part of lazr.restfulclient.
#
# lazr.restfulclient is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, version 3 of the
# License.
#
# lazr.restfulclient is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.restfulclient. If not, see <http://www.gnu.org/licenses/>.

"""Tests for the OAuth-aware classes."""

__metaclass__ = type


import os
import os.path
import shutil
import stat
import tempfile
import unittest

from lazr.restfulclient.authorize import oauth
from lazr.restfulclient.authorize.oauth import (
    AccessToken,
    Consumer,
    OAuthAuthorizer,
    )


class TestConsumer(unittest.TestCase):

    def test_data_fields(self):
        consumer = Consumer("key", "secret", "application")
        self.assertEqual(consumer.key, "key")
        self.assertEqual(consumer.secret, "secret")
        self.assertEqual(consumer.application_name, "application")

    def test_default_application_name(self):
        # Application name defaults to None
        consumer = Consumer("key", "secret")
        self.assertEqual(consumer.application_name, None)


class TestSystemWideConsumer(unittest.TestCase):

    def setUp(self):
        """Save the original 'platform' and 'socket' modules.

        The tests will be replacing them with dummies.
        """
        self.original_platform = oauth.platform
        self.original_socket = oauth.socket

    def tearDown(self):
        """Replace the original 'platform' and 'socket' modules."""
        oauth.platform = self.original_platform
        oauth.socket = self.original_socket

    def _set_hostname(self, hostname):
        """Changes the socket module to simulate the given hostname."""
        class DummySocket:
            def gethostname(self):
                return hostname
        oauth.socket = DummySocket()

    def _set_platform(self, linux_distribution, system):
        """Changes the platform module to simulate different behavior.

        :param linux_distribution: A tuple to be returned by
            linux_distribution(), or a callable that implements
            linux_distribution().
        :param system: A string to be returned by system()
        """

        if isinstance(linux_distribution, tuple):
            def get_linux_distribution(self):
                return linux_distribution
        else:
            # The caller provided their own implementation of
            # linux_distribution().
            get_linux_distribution = linux_distribution

        class DummyPlatform:
            linux_distribution = get_linux_distribution
            def system(self):
                return system
        oauth.platform = DummyPlatform()

    def _broken(self):
        """Raises an exception."""
        raise Exception("Oh noes!")

    def test_useful_linux_distribution(self):
        # If platform.linux_distribution returns a tuple of useful
        # strings, as it does on Ubuntu, we'll use the first string
        # for the system type.
        self._set_platform(('Fooix', 'String2', 'String3'), 'FooOS')
        self._set_hostname("foo")
        consumer = oauth.SystemWideConsumer("app name")
        self.assertEqual(
            consumer.key, 'System-wide: Fooix (foo)')

    def test_empty_linux_distribution(self):
        # If platform.linux_distribution returns a tuple of empty
        # strings, as it does on Windows and Mac OS X, we fall back to
        # the result of platform.system().
        self._set_platform(('', '', ''), 'BarOS')
        self._set_hostname("bar")
        consumer = oauth.SystemWideConsumer("app name")
        self.assertEqual(
            consumer.key, 'System-wide: BarOS (bar)')

    def test_broken_linux_distribution(self):
        # If platform.linux_distribution raises an exception (which
        # can happen with older versions of Python), we fall back to
        # the result of platform.system().
        self._set_platform(self._broken, 'BazOS')
        self._set_hostname("baz")
        consumer = oauth.SystemWideConsumer("app name")
        self.assertEqual(
            consumer.key, 'System-wide: BazOS (baz)')


class TestOAuthAuthorizer(unittest.TestCase):
    """Test for the OAuth Authorizer."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_save_to_and_load_from__path(self):
        # Credentials can be saved to and loaded from a file using
        # save_to_path() and load_from_path().
        credentials_path = os.path.join(self.temp_dir, 'credentials')
        credentials = OAuthAuthorizer(
            'consumer.key', consumer_secret='consumer.secret',
            access_token=AccessToken('access.key', 'access.secret'))
        credentials.save_to_path(credentials_path)
        self.assertTrue(os.path.exists(credentials_path))

        # Make sure the file is readable and writable by the user, but
        # not by anyone else.
        self.assertEqual(stat.S_IMODE(os.stat(credentials_path).st_mode),
                          stat.S_IREAD | stat.S_IWRITE)

        loaded_credentials = OAuthAuthorizer.load_from_path(credentials_path)
        self.assertEqual(loaded_credentials.consumer.key, 'consumer.key')
        self.assertEqual(
            loaded_credentials.consumer.secret, 'consumer.secret')
        self.assertEqual(
            loaded_credentials.access_token.key, 'access.key')
        self.assertEqual(
            loaded_credentials.access_token.secret, 'access.secret')

def test_suite():
    return unittest.TestLoader().loadTestsFromName(__name__)
