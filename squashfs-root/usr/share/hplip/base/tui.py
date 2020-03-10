# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

# Std Lib
import sys
import re

# Local
from .g import *
from . import utils
from .sixext import PY3
from .sixext.moves import input


def enter_yes_no(question, default_value='y', choice_prompt=None):
    if type(default_value) == type(""):
        if default_value == 'y':
            default_value = True
        else:
            default_value = False

    #assert default_value in [True, False]

    if choice_prompt is None:
        if default_value:
            question += " (y=yes*, n=no, q=quit) ? "
        else:
            question += " (y=yes, n=no*, q=quit) ? "
    else:
        question += choice_prompt

    while True:
        try:
            user_input = input(log.bold(question)).lower().strip()
        except EOFError:
            continue

        if not user_input:
            return True, default_value

        if user_input == 'n':
            return True, False

        if user_input == 'y':
            return True, True

        if user_input in ('q', 'c'): # q -> quit, c -> cancel
            return False, default_value

        log.error("Please press <enter> or enter 'y', 'n', or 'q'.")


def enter_range(question, min_value, max_value, default_value=None):
    while True:
        try:
            user_input = input(log.bold(question)).lower().strip()
        except EOFError:
            continue

        if not user_input:
            if default_value is not None:
                return True, default_value

        if user_input == 'q':
            return False, default_value

        try:
            value_int = int(user_input)
        except ValueError:
            log.error('Please enter a number between %d and %d, or "q" to quit.' %
                (min_value, max_value))
            continue

        if value_int < min_value or value_int > max_value:
            log.error('Please enter a number between %d and %d, or "q" to quit.' %
                (min_value, max_value))
            continue

        return True, value_int


def enter_choice(question, choices, default_value=None):
    if 'q' not in choices:
        choices.append('q')

    while True:
        try:
            user_input = input(log.bold(question)).lower().strip()
        except EOFError:
            continue


        if (not user_input and default_value) or user_input == default_value:
            if default_value == 'q':
                return False, default_value
            else:
                return True, default_value

        #print user_input
        if user_input == 'q':
            return False, user_input

        if user_input in choices:
            return True, user_input

        log.error("Please enter %s or press <enter> for the default of '%s'." %
            (', '.join(["'%s'" % x for x in choices]), default_value))


def title(text):
    log.info("")
    log.info("")
    log.info(log.bold(text))
    log.info(log.bold("-"*len(text)))


def header(text):
    c = len(text)
    log.info("")
    log.info("-"*(c+4))
    log.info("| "+text+" |")
    log.info("-"*(c+4))
    log.info("")


def load_paper_prompt(msg="", title=""):
    if not msg:
        msg = "A page will be printed.\nPlease load plain paper into the printer."
    return continue_prompt(msg)


def load_scanner_for_align_prompt():
    return continue_prompt("Load the alignment page on the scanner bed and push the 'Scan' or 'Enter' button on the printer to complete the alignment.")

def load_photo_paper_prompt():
    return continue_prompt("A page will be printed.\nPlease load HP Advanced Photo Paper - Glossy into the printer.")


def continue_prompt(prompt=''):
    while True:
        try:
            x = input(log.bold(prompt + " Press <enter> to continue or 'q' to quit: ")).lower().strip()
        except EOFError:
            continue

        if not x:
            return True

        elif x == 'q':
            return  False

        log.error("Please press <enter> or enter 'q' to quit.")


def enter_regex(regex, prompt, pattern, default_value=None):
    re_obj = re.compile(regex)
    while True:
        try:
            x = input(log.bold(prompt))
        except EOFError:
            continue

        if not x and default_value is not None:
            return default_value, x

        elif x == 'q':
            return False, default_value

        match = re_obj.search(x)

        if not match:
            log.error("Incorrect input. Please enter correct input.")
            continue

        return True, x


def ttysize():
    try:
        if PY3:
            import subprocess # TODO: Replace with subprocess (commands is deprecated in Python 3.0)
            ln1 = subprocess.getoutput('stty -a').splitlines()[0]
        else:
            import commands
            ln1 = commands.getoutput('stty -a').splitlines()[0]
        vals = {'rows':None, 'columns':None}
        for ph in ln1.split(';'):
            x = ph.split()
            if len(x) == 2:
                vals[x[0]] = x[1]
                vals[x[1]] = x[0]
        return int(vals['rows']), int(vals['columns'])
    except TypeError:
        return 40, 64


class ProgressMeter(object):
    def __init__(self, prompt="Progress:"):
        self.progress = 0
        self.prompt = prompt
        self.prev_length = 0
        self.spinner = "\|/-\|/-*"
        self.spinner_pos = 0
        self.max_size = ttysize()[1] - len(prompt) - 25
        self.update(0)

    def update(self, progress, msg=''): # progress in %
        self.progress = progress

        x = int(self.progress * self.max_size / 100)
        if x > self.max_size: x = self.max_size

        if self.progress >= 100:
            self.spinner_pos = 8
            self.progress = 100

        sys.stdout.write("\b" * self.prev_length)

        y = "%s [%s%s%s] %d%%  %s   " % \
            (self.prompt, '*'*(x-1), self.spinner[self.spinner_pos],
             ' '*(self.max_size-x), self.progress, msg)

        sys.stdout.write(y)

        sys.stdout.flush()
        self.prev_length = len(y)
        self.spinner_pos = (self.spinner_pos + 1) % 8



class Formatter(object):
    def __init__(self, margin=2, header=None, min_widths=None, max_widths=None):
        self.margin = margin # int
        self.header = header # tuple of strings
        self.rows = [] # list of tuples
        self.max_widths = max_widths # tuple of ints
        self.min_widths = min_widths # tuple of ints


    def add(self, row_data): # tuple of strings
        self.rows.append(row_data)


    def output(self):
        if self.rows:
            num_cols = len(self.rows[0])
            for r in self.rows:
                if len(r) != num_cols:
                    log.error("Invalid number of items in row: %s" % r)
                    return

            if len(self.header) != num_cols:
                log.error("Invalid number of items in header.")

            min_calc_widths = []
            for c in self.header:
                header_parts = c.split(' ')
                max_width = 0
                for x in header_parts:
                    max_width = max(max_width, len(x))

                min_calc_widths.append(max_width)

            max_calc_widths = []
            for x, c in enumerate(self.header):
                max_width = 0
                for r in self.rows:
                    max_width = max(max_width, len(r[x]))

                max_calc_widths.append(max_width)

            max_screen_width = None

            if self.max_widths is None:
                max_screen_width = ttysize()[1]
                def_max = 8*(max_screen_width/num_cols)/10
                self.max_widths = []
                for c in self.header:
                    self.max_widths.append(def_max)
            else:
                if len(self.max_widths) != num_cols:
                    log.error("Invalid number of items in max col widths.")

            if self.min_widths is None:
                if max_screen_width is None:
                    max_screen_width = ttysize()[1]
                def_min = 4*(max_screen_width/num_cols)/10
                self.min_widths = []
                for c in self.header:
                    self.min_widths.append(def_min)
            else:
                if len(self.min_widths) != num_cols:
                    log.error("Invalid number of items in min col widths.")

            col_widths = []
            formats = []
            for m1, m2, m3, m4 in zip(self.min_widths, min_calc_widths,
                                      self.max_widths, max_calc_widths):
                col_width = max(max(m1, m2), min(m3, m4))
                col_widths.append(col_width)
                formats.append({'width': col_width, 'margin': self.margin})

            formatter = utils.TextFormatter(tuple(formats))

            log.info(formatter.compose(self.header))

            sep = []
            for c in col_widths:
                sep.append('-'*int(c))

            log.info(formatter.compose(tuple(sep)))

            for r in self.rows:
                log.info(formatter.compose(r))

        else:
            log.error("No data rows")



ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2


def align(line, width=70, alignment=ALIGN_LEFT):
    space = width - len(line)

    if alignment == ALIGN_CENTER:
        return ' '*(space/2) + line + \
               ' '*(space/2 + space%2)

    elif alignment == ALIGN_RIGHT:
        return ' '*space + line

    else:
        return line + ' '*space


def format_paragraph(paragraph, width=None, alignment=ALIGN_LEFT):
    if width is None:
        width = ttysize()[1]

    result = []
    words = paragraph.split()
    try:
        current, words = words[0], words[1:]
    except IndexError:
        return [paragraph]

    for word in words:
        increment = 1 + len(word)

        if len(current) + increment > width:
            result.append(align(current, width, alignment))
            current = word

        else:
            current = current+" "+word

    result.append(align(current, width, alignment))
    return result


def printer_table(printers):
    header("SELECT PRINTER")
    last_used_printer_name = user_conf.get('last_used', 'printer_name')
    ret = None

    table = Formatter(header=('Num', 'CUPS Printer'),
                              max_widths=(8, 100), min_widths=(8, 20))

    default_index = None
    for x, _ in enumerate(printers):
        if last_used_printer_name == printers[x]:
            table.add((str(x) + '*', printers[x]))
            default_index = x
        else:
            table.add((str(x), printers[x]))

    table.output()

    if default_index is not None:
        ok, i = enter_range("\nEnter number 0...%d for printer (q=quit, <enter>=default: *%d) ?" % (x, default_index),
                                0, x, default_index)
    else:
        ok, i = enter_range("\nEnter number 0...%d for printer (q=quit) ?" % x, 0, x)

    if ok:
        ret = printers[i]

    else :
        sys.exit(0)
    return ret


def device_table(devices, scan_flag=False):
    header("SELECT DEVICE")
    last_used_device_uri = user_conf.get('last_used', 'device_uri')
    ret = None

    if scan_flag:
        table = Formatter(header=('Num', 'Scan device URI'),
                                 max_widths=(8, 100), min_widths=(8, 12))
    else:
        table = Formatter(header=('Num', 'Device URI', 'CUPS Printer(s)'),
                                 max_widths=(8, 100, 100), min_widths=(8, 12, 12))

    default_index = None
    device_index = {}
    for x, d in enumerate(devices):
        device_index[x] = d
        if last_used_device_uri == d:
            if scan_flag:
                table.add((str(x) + "*", d))
            else:
                table.add((str(x) + "*", d, ','.join(devices[d])))
            default_index = x
        else:
            if scan_flag:
                table.add((str(x), d))
            else:
                table.add((str(x), d, ','.join(devices[d])))

    table.output()

    if default_index is not None:
        ok, i = enter_range("\nEnter number 0...%d for device (q=quit, <enter>=default: %d*) ?" % (x, default_index),
                                0, x, default_index)
    else:
        ok, i = enter_range("\nEnter number 0...%d for device (q=quit) ?" % x, 0, x)

    if ok:
        ret = device_index[i]

    else :
        sys.exit(0)
    return ret


def connection_table():
    ret, ios, x = None, {0: ('usb', "Universal Serial Bus (USB)") }, 1

    if prop.net_build:
        ios[x] = ('net', "Network/Ethernet/Wireless (direct connection or JetDirect)")
        x += 1

    if prop.par_build:
        ios[x] = ('par', "Parallel Port (LPT:)")
        x += 1

    if len(ios) > 1:
        header("SELECT CONNECTION (I/O) TYPE")

        table = Formatter(header=('Num', 'Connection Type', 'Description'),
                          max_widths=(8, 20, 80), min_widths=(8, 10, 40))

        for x, data in list(ios.items()):
            if x == 0:
                table.add((str(x) + "*", data[0], data[1]))
            else:
                table.add((str(x), data[0], data[1]))

        table.output()

        ok, val = enter_range("\nEnter number 0...%d for connection type (q=quit, enter=usb*) ? " % x,
            0, x, 0)

        if ok:
            ret = [ios[val][0]]

    else:
        ret = ['usb']

    return ret

