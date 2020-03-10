# Copyright (C) 2008-2012  Canonical, Ltd.
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'PluginManager',
]


import os
import imp
import sys
import errno
import inspect
import logging

from janitor.plugincore.plugin import Plugin


SPACE = ' '
STR_TYPES = (basestring if str is bytes else str)


class PluginManager:
    """Find and load plugins.

    Plugins are stored in files named '*_plugin.py' in the list of directories
    given to the constructor.
    """

    def __init__(self, app, plugin_dirs):
        self._app = app
        # Make a copy to immune ourselves from mutability.  For safety, double
        # check a common mistake.
        if isinstance(plugin_dirs, STR_TYPES):
            raise TypeError(
                'Expected sequence, got {}'.format(type(plugin_dirs)))
        self._plugin_dirs = list(plugin_dirs)
        self._plugins = None

    def get_plugin_files(self):
        """Return all filenames in which plugins may be stored."""

        for dirname in self._plugin_dirs:
            try:
                basenames = [filename for filename in os.listdir(dirname)
                             if filename.endswith('_plugin.py')]
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise
                logging.debug('No such plugin directory: {}'.format(dirname))
                continue
            logging.debug(
                'Plugin modules in {}: {}'.format(
                    dirname, SPACE.join(basenames)))
            # Sort the base names alphabetically for predictability.
            for filename in sorted(basenames):
                yield os.path.join(dirname, filename)

    @property
    def plugin_files(self):
        for filename in self.get_plugin_files():
            yield filename

    def _find_plugins(self, module):
        """Find and instantiate all plugins in a module."""
        def is_plugin(target):
            # Don't return the base class itself.
            return (inspect.isclass(target) and
                    issubclass(target, Plugin) and
                    target is not Plugin)
        plugin_classes = [
            member
            for name, member in inspect.getmembers(module, is_plugin)
        ]
        logging.debug('Plugins in {}: {}'.format(
            module, SPACE.join(str(plugin) for plugin in plugin_classes)))
        for plugin_class in plugin_classes:
            yield plugin_class()

    def _load_module(self, filename):
        """Load a module from a filename."""
        logging.debug('Loading module from file {}'.format(filename))
        # 2012-06-08 BAW: I don't particularly like putting an entry in
        # sys.modules with the basename of the file.  Note that
        # imp.load_module() will reload the plugin if it's already been
        # imported, so check sys.modules first and don't reload the plugin
        # (this is a change in behavior from older versions, but a valid one I
        # think - reloading modules is problematic).  Ideally, we'd be using
        # __import__() but we can't guarantee that the path to the filename is
        # on sys.path, so we'll just live with this as the most backward
        # compatible implementation.
        #
        # The other problem is that the module could be encoded, but this
        # mechanism doesn't support PEP 263 style source file encoding
        # specifications.  To make matters worse, we can't use codecs.open()
        # with encoding='UTF-8' because imp.load_module() requires an actual
        # file object, not whatever codecs wrapper is used.  If we were Python
        # 3 only, we could use the built-in open(), but since we have to also
        # support Python 3, we just have to live with the platform dependent
        # default text encoding of built-in open().
        module_name, ignore = os.path.splitext(os.path.basename(filename))
        if module_name in sys.modules:
            return sys.modules[module_name]
        with open(filename, 'r') as fp:
            try:
                module = imp.load_module(
                    module_name, fp, filename,
                    ('.py', 'r', imp.PY_SOURCE))
            except Exception as error:
                logging.warning("Failed to load plugin '{}' ({})".format(
                                module_name, error))
                return None
            else:
                return module

    def get_plugins(self, condition=None, callback=None):
        """Return all plugins that have been found.

        Loaded plugins are cached, so they will only be loaded once.

        `condition` is matched against each plugin to determine whether it
        will be returned or not.  A `condition` of the string '*' matches all
        plugins.  The default condition matches all default plugins, since by
        default, plugins have a condition of the empty list.

        If `condition` matches the plugin's condition exactly, the plugin is
        returned.  The plugin's condition can also be a sequence, and if
        `condition` is in that sequence, the plugin is returned.

        Note that even though loaded plugins are cached, calling
        `get_plugin()` with different a `condition` can return a different set
        of plugins.

        If `callback` is specified, it is called after each plugin has
        been found, with the following arguments: filename, index of
        filename in list of files to be examined (starting with 0), and
        total number of files to be examined. The purpose of this is to
        allow the callback to inform the user in case things take a long
        time.
        """
        # By default, plugins have a condition of the empty list, so unless a
        # plugin has an explicit condition set, this will match everything.
        if condition is None:
            condition = []
        # Only load the plugins once, however when different conditions are
        # given, a different set of the already loaded plugins may be
        # returned.
        if self._plugins is None:
            self._plugins = []
            filenames = list(self.plugin_files)
            total = len(filenames)
            for i, filename in enumerate(filenames):
                if callback is not None:
                    callback(filename, i, total)
                module = self._load_module(filename)
                for plugin in self._find_plugins(module):
                    plugin.set_application(self._app)
                    self._plugins.append(plugin)
        # Now match each of the plugins against the specified condition,
        # returning only those that match, or all of them if there is no
        # condition.
        plugins = [
            plugin for plugin in self._plugins
            if (plugin.condition == condition or
                condition in plugin.condition or
                condition == '*')
        ]
        logging.debug("plugins for condition '{}' are '{}'".format(
            condition, plugins))
        return plugins
