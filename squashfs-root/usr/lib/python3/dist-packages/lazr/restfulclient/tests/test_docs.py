# Copyright 2009 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.restfulclient
#
# lazr.restfulclient is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# lazr.restfulclient is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.restfulclient.  If not, see <http://www.gnu.org/licenses/>.
"Test harness for doctests."

# pylint: disable-msg=E0611,W0142

__metaclass__ = type
__all__ = [
    'additional_tests',
    ]

import atexit
import doctest
import os
from pkg_resources import (
    resource_filename, resource_exists, resource_listdir, cleanup_resources)
import wsgi_intercept
from wsgi_intercept.httplib2_intercept import install, uninstall

# We avoid importing anything from lazr.restful into the module level,
# so that standalone_tests() can run without any support from
# lazr.restful.

DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)


def setUp(test):
    from lazr.restful.example.base.tests.test_integration import WSGILayer
    install()
    wsgi_intercept.add_wsgi_intercept(
        'cookbooks.dev', 80, WSGILayer.make_application)


def tearDown(test):
    from lazr.restful.example.base.interfaces import IFileManager
    from zope.component import getUtility
    uninstall()
    file_manager = getUtility(IFileManager)
    file_manager.files = {}
    file_manager.counter = 0


def find_doctests(suffix):
    """Find doctests matching a certain suffix."""
    # Always include README.txt.
    doctest_files = [
        os.path.abspath(resource_filename('lazr.restfulclient', 'README.txt'))]
    # Match other doctests against the suffix.
    if resource_exists('lazr.restfulclient', 'docs'):
        for name in resource_listdir('lazr.restfulclient', 'docs'):
            if name.endswith(suffix):
                doctest_files.append(
                    os.path.abspath(
                        resource_filename(
                            'lazr.restfulclient', 'docs/%s' % name)))
    return doctest_files


def additional_tests():
    "Run the doc tests (README.txt and docs/*, if any exist)"
    from lazr.restful.example.base.tests.test_integration import WSGILayer
    kwargs = dict(module_relative=False, optionflags=DOCTEST_FLAGS,
                  setUp=setUp, tearDown=tearDown)
    atexit.register(cleanup_resources)
    suite = doctest.DocFileSuite(*find_doctests('.txt'), **kwargs)
    suite.layer = WSGILayer
    return suite


def standalone_tests():
    "Run the tests that don't need lazr.restful."
    kwargs = dict(module_relative=False, optionflags=DOCTEST_FLAGS)
    atexit.register(cleanup_resources)
    suite = doctest.DocFileSuite(*find_doctests('.standalone.txt'), **kwargs)
    return suite
