import sys
import os
import time

from apport.report import Report

from apport.packaging_impl import impl as packaging

Report  # pyflakes
packaging  # pyflakes

# fix gettext to output proper unicode strings
import gettext


def unicode_gettext(str):
    trans = gettext.gettext(str)
    if isinstance(trans, bytes):
        return trans.decode('UTF-8')
    else:
        return trans


def log(message, timestamp=False):
    '''Log the given string to stdout. Prepend timestamp if requested'''

    if timestamp:
        sys.stdout.write('%s: ' % time.strftime('%x %X'))
    print(message)


def fatal(msg, *args):
    '''Print out an error message and exit the program.'''

    error(msg, *args)
    sys.exit(1)


def error(msg, *args):
    '''Print out an error message.'''

    if sys.stderr:
        sys.stderr.write('ERROR: ')
        sys.stderr.write(msg % args)
        sys.stderr.write('\n')


def warning(msg, *args):
    '''Print out an warning message.'''

    if sys.stderr:
        sys.stderr.write('WARNING: ')
        sys.stderr.write(msg % args)
        sys.stderr.write('\n')


def memdbg(checkpoint):
    '''Print current memory usage.

    This is only done if $APPORT_MEMDEBUG is set.
    '''
    if 'APPORT_MEMDEBUG' not in os.environ or not sys.stderr:
        return

    memstat = {}
    with open('/proc/self/status') as f:
        for l in f:
            if l.startswith('Vm'):
                (field, size, unit) = l.split()
                memstat[field[:-1]] = int(size) / 1024.

    sys.stderr.write('Size: %.1f MB, RSS: %.1f MB, Stk: %.1f MB @ %s\n' %
                     (memstat['VmSize'], memstat['VmRSS'], memstat['VmStk'], checkpoint))
