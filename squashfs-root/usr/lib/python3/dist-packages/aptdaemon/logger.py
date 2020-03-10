#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Logging facilities for aptdaemon
"""
# Copyright (C) 2013 Sebastian Heinlein <devel@glatzor.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("ColoredFormatter")

import logging
import os

# Define some foreground colors
BLACK = 30
RED = 31
GREEN = 32
YELLOW = 33
BLUE = 34
MAGENTA = 35
CYAN = 36
WHITE = 37

# Terminal control sequences to format output
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    logging.WARN: YELLOW,
    logging.INFO: BLUE,
    logging.DEBUG: CYAN,
    logging.CRITICAL: RED,
    logging.ERROR: RED
}


class ColoredFormatter(logging.Formatter):

    """Adds some color to the log messages.

    http://stackoverflow.com/questions/384076/\
            how-can-i-color-python-logging-output
    """

    def __init__(self, fmt=None, datefmt=None, use_color=True):
        logging.Formatter.__init__(self, fmt, datefmt)
        if os.getenv("TERM") in ["xterm", "xterm-colored", "linux"]:
            self.use_color = use_color
        else:
            self.use_color = False

    def format(self, record):
        """Return the formated output string."""
        if self.use_color and record.levelno in COLORS:
            record.levelname = (COLOR_SEQ % COLORS[record.levelno] +
                                record.levelname +
                                RESET_SEQ)
            record.name = COLOR_SEQ % GREEN + record.name + RESET_SEQ
            if record.levelno in [logging.CRITICAL, logging.ERROR]:
                record.msg = COLOR_SEQ % RED + record.msg + RESET_SEQ
        return logging.Formatter.format(self, record)
