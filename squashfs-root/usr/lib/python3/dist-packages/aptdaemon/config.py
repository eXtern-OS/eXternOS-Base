"""Handling configuration files."""
# Copyright (C) 2010 Sebastian Heinlein <sevel@glatzor.de>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("ConfigWriter",)

import logging
import os

import apt_pkg

log = logging.getLogger("AptDaemon.ConfigWriter")


class Value(object):

    """Represents a value with position information.

    .. attribute:: string
        The value string.

    .. attribute:: line
        The line number of the configuration file in which the value is set.

    .. attribute:: start
        The position in the line at which the value starts.

    .. attribute:: end
        The position in the line at which the value ends.

    .. attribute:: quotes
        The outer qoutes of the value: ' or "
    """

    def __init__(self, line, start, quotes):
        self.string = ""
        self.start = start
        self.end = None
        self.line = line
        self.quotes = quotes

    def __cmp__(self, other):
        return self.string == other

    def __repr__(self):
        return "Value: '%s' (line %s: %s to %s)" % (self.string, self.line,
                                                    self.start, self.end)


class ConfigWriter(object):

    """Modifies apt configuration files."""

    def parse(self, lines):
        """Parse an ISC based apt configuration.

        :param lines: The list of lines of a configuration file.

        :returns: Dictionary of key, values found in the parsed configuration.
        """
        options = {}
        in_comment = False
        in_value = False
        prev_char = None
        option = []
        value = None
        option_name = ""
        value_list = []
        in_brackets = True
        level = 0
        for line_no, line in enumerate(lines):
            for char_no, char in enumerate(line):
                if not in_comment and char == "*" and prev_char == "/":
                    in_comment = True
                    prev_char = ""
                    continue
                elif in_comment and char == "/" and prev_char == "*":
                    # A multiline comment was closed
                    in_comment = False
                    prev_char = ""
                    option_name = option_name[:-1]
                    continue
                elif in_comment:
                    # We ignore the content of multiline comments
                    pass
                elif not in_value and ((char == "/" and prev_char == "/") or
                                       char == "#"):
                    # In the case of a line comment continue processing
                    # the next line
                    prev_char = ""
                    option_name = option_name[:-1]
                    break
                elif char in "'\"":
                    if in_value and value.quotes == char:
                        value.end = char_no
                        in_value = not in_value
                    elif not value:
                        value = Value(line_no, char_no, char)
                        in_value = not in_value
                    else:
                        value.string += char
                elif in_value:
                    value.string += char
                elif option_name and char == ":" and prev_char == ":":
                    option.append(option_name[:-1])
                    option_name = ""
                elif char.isalpha() or char in "/-:._+":
                    option_name += char.lower()
                elif char == ";":
                    if in_brackets:
                        value_list.append(value)
                        value = None
                        continue
                    if value_list:
                        log.debug("Found %s \"%s\"", "::".join(option),
                                  value_list)
                        options["::".join(option)] = value_list
                        value_list = []
                    elif value:
                        log.debug("Found %s \"%s\"", "::".join(option), value)
                        options["::".join(option)] = value
                    else:
                        log.debug("Skipping empty key %s", "::".join(option))
                    value = None
                    if level > 0:
                        option.pop()
                    else:
                        option = []
                elif char == "}":
                    level -= 1
                    in_brackets = False
                elif char == "{":
                    level += 1
                    if option_name:
                        option.append(option_name)
                        option_name = ""
                    in_brackets = True
                elif char in "\t\n ":
                    if option_name:
                        option.append(option_name)
                        option_name = ""
                        in_brackets = False
                else:
                    raise ValueError("Unknown char '%s' in line: '%s'" %
                                     (char, line))
                prev_char = char
        return options

    def set_value(self, option, value, defaultfile):
        """Change the value of an option in the configuration.

        :param option: The name of the option, e.g.
            'apt::periodic::AutoCleanInterval'.
        :param value: The value of the option. Will be converted to string.
        :param defaultfile: The filename of the ``/etc/apt/apt.conf.d``
            configuration snippet in which the option should be set.
            If the value is overriden by a later configuration file snippet
            it will be disabled in the corresponding configuration file.
        """
        # FIXME: Support value lists
        # Convert the value to string
        if value is True:
            value = "true"
        elif value is False:
            value = "false"
        else:
            value = str(value)
        # Check all configuration file snippets
        etc_parts = os.path.join(apt_pkg.config.find_dir("Dir::Etc"),
                                 apt_pkg.config.find_dir("Dir::Etc::Parts"))
        for filename in os.listdir(etc_parts):
            if filename < defaultfile:
                continue
            with open(os.path.join(etc_parts, filename)) as fd:
                lines = fd.readlines()
            config = self.parse(lines)
            try:
                val = config[option.lower()]
            except KeyError:
                if filename == defaultfile:
                    lines.append("%s '%s';\n" % (option, value))
                else:
                    continue
            else:
                # Check if the value needs to be changed at all
                if ((value == "true" and
                        val.string.lower() in ["yes", "with", "on",
                                               "enable"]) or
                        (value == "false" and
                         val.string.lower() in ["no", "without", "off",
                                                "disable"]) or
                        (str(value) == val.string)):
                    continue
                if filename == defaultfile:
                    line = lines[val.line]
                    new_line = line[:val.start + 1]
                    new_line += value
                    new_line += line[val.end:]
                    lines[val.line] = new_line
                else:
                    # Comment out existing values instead in non default
                    # configuration files
                    # FIXME Quite dangerous for brackets
                    lines[val.line] = "// %s" % lines[val.line]
            with open(os.path.join(etc_parts, filename), "w") as fd:
                log.debug("Writting %s", filename)
                fd.writelines(lines)
        if not os.path.exists(os.path.join(etc_parts, defaultfile)):
            with open(os.path.join(etc_parts, defaultfile), "w") as fd:
                log.debug("Writting %s", filename)
                line = "%s '%s';\n" % (option, value)
                fd.write(line)


def main():
    apt_pkg.init_config()
    cw = ConfigWriter()
    for filename in sorted(os.listdir("/etc/apt/apt.conf.d/")):
        lines = open("/etc/apt/apt.conf.d/%s" % filename).readlines()
        cw.parse(lines)
    print((cw.set_value("huhu::abc", "lumpi", "10glatzor")))

if __name__ == "__main__":
    main()

# vim:ts=4:sw=4:et
