'''Python sys.excepthook hook to generate apport crash dumps.'''

# Copyright (c) 2006 - 2009 Canonical Ltd.
# Authors: Robert Collins <robert@ubuntu.com>
#          Martin Pitt <martin.pitt@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import os
import sys

CONFIG = '/etc/default/apport'


def enabled():
    '''Return whether Apport should generate crash reports.'''

    # This doesn't use apport.packaging.enabled() because it is too heavyweight
    # See LP: #528355
    import re
    try:
        with open(CONFIG) as f:
            conf = f.read()
        return re.search(r'^\s*enabled\s*=\s*0\s*$', conf, re.M) is None
    except IOError:
        # if the file does not exist, assume it's enabled
        return True


def apport_excepthook(exc_type, exc_obj, exc_tb):
    '''Catch an uncaught exception and make a traceback.'''

    # create and save a problem report. Note that exceptions in this code
    # are bad, and we probably need a per-thread reentrancy guard to
    # prevent that happening. However, on Ubuntu there should never be
    # a reason for an exception here, other than [say] a read only var
    # or some such. So what we do is use a try - finally to ensure that
    # the original excepthook is invoked, and until we get bug reports
    # ignore the other issues.

    # import locally here so that there is no routine overhead on python
    # startup time - only when a traceback occurs will this trigger.
    try:
        # ignore 'safe' exit types.
        if exc_type in (KeyboardInterrupt, ):
            return

        # do not do anything if apport was disabled
        if not enabled():
            return

        try:
            from cStringIO import StringIO
            StringIO  # pyflakes
        except ImportError:
            from io import StringIO

        import re, traceback
        from apport.fileutils import likely_packaged, get_recent_crashes

        # apport will look up the package from the executable path.
        try:
            binary = os.path.realpath(os.path.join(os.getcwd(), sys.argv[0]))
        except (TypeError, AttributeError, IndexError):
            # the module has mutated sys.argv, plan B
            try:
                binary = os.readlink('/proc/%i/exe' % os.getpid())
            except OSError:
                return

        # for interactive python sessions, sys.argv[0] == ''; catch that and
        # other irregularities
        if not os.access(binary, os.X_OK) or not os.path.isfile(binary):
            return

        # filter out binaries in user accessible paths
        if not likely_packaged(binary):
            return

        import apport.report

        pr = apport.report.Report()

        # special handling of dbus-python exceptions
        if hasattr(exc_obj, 'get_dbus_name'):
            name = exc_obj.get_dbus_name()
            if name == 'org.freedesktop.DBus.Error.NoReply':
                # NoReply is an useless crash, we do not even get the method it
                # was trying to call; needs actual crash from D-BUS backend (LP #914220)
                return
            elif name == 'org.freedesktop.DBus.Error.ServiceUnknown':
                dbus_service_unknown_analysis(exc_obj, pr)
            else:
                pr['_PythonExceptionQualifier'] = name

        # disambiguate OSErrors with errno:
        if exc_type == OSError and exc_obj.errno is not None:
            pr['_PythonExceptionQualifier'] = str(exc_obj.errno)

        # append a basic traceback. In future we may want to include
        # additional data such as the local variables, loaded modules etc.
        tb_file = StringIO()
        traceback.print_exception(exc_type, exc_obj, exc_tb, file=tb_file)
        pr['Traceback'] = tb_file.getvalue().strip()
        pr.add_proc_info(extraenv=['PYTHONPATH', 'PYTHONHOME'])
        pr.add_user_info()
        # override the ExecutablePath with the script that was actually running
        pr['ExecutablePath'] = binary
        if 'ExecutableTimestamp' in pr:
            pr['ExecutableTimestamp'] = str(int(os.stat(binary).st_mtime))
        try:
            pr['PythonArgs'] = '%r' % sys.argv
        except AttributeError:
            pass
        if pr.check_ignored():
            return
        mangled_program = re.sub('/', '_', binary)
        # get the uid for now, user name later
        user = os.getuid()
        pr_filename = '%s/%s.%i.crash' % (os.environ.get(
            'APPORT_REPORT_DIR', '/var/crash'), mangled_program, user)
        crash_counter = 0
        if os.path.exists(pr_filename):
            if apport.fileutils.seen_report(pr_filename):
                # flood protection
                with open(pr_filename, 'rb') as f:
                    crash_counter = get_recent_crashes(f) + 1
                if crash_counter > 1:
                    return

                # remove the old file, so that we can create the new one with
                # os.O_CREAT|os.O_EXCL
                os.unlink(pr_filename)
            else:
                # don't clobber existing report
                return

        if crash_counter:
            pr['CrashCounter'] = str(crash_counter)
        with os.fdopen(os.open(pr_filename,
                               os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640), 'wb') as f:
            pr.write(f)

    finally:
        # resume original processing to get the default behaviour,
        # but do not trigger an AttributeError on interpreter shutdown.
        if sys:
            sys.__excepthook__(exc_type, exc_obj, exc_tb)


def dbus_service_unknown_analysis(exc_obj, report):
    from glob import glob
    import subprocess, re
    try:
        from configparser import ConfigParser, NoSectionError, NoOptionError
        (ConfigParser, NoSectionError, NoOptionError)  # pyflakes
    except ImportError:
        # Python 2
        from ConfigParser import ConfigParser, NoSectionError, NoOptionError

    # determine D-BUS name
    m = re.search(r'name\s+(\S+)\s+was not provided by any .service',
                  exc_obj.get_dbus_message())
    if not m:
        if sys.stderr:
            sys.stderr.write('Error: cannot parse D-BUS name from exception: ' +
                             exc_obj.get_dbus_message())
            return

    dbus_name = m.group(1)

    # determine .service file and Exec name for the D-BUS name
    services = []  # tuples of (service file, exe name, running)
    for f in glob('/usr/share/dbus-1/*services/*.service'):
        cp = ConfigParser(interpolation=None)
        cp.read(f, encoding='UTF-8')
        try:
            if cp.get('D-BUS Service', 'Name') == dbus_name:
                exe = cp.get('D-BUS Service', 'Exec')
                running = (subprocess.call(['pidof', '-sx', exe], stdout=subprocess.PIPE) == 0)
                services.append((f, exe, running))
        except (NoSectionError, NoOptionError):
            if sys.stderr:
                sys.stderr.write('Invalid D-BUS .service file %s: %s' % (
                    f, exc_obj.get_dbus_message()))
            continue

    if not services:
        report['DbusErrorAnalysis'] = 'no service file providing ' + dbus_name
    else:
        report['DbusErrorAnalysis'] = 'provided by'
        for (service, exe, running) in services:
            report['DbusErrorAnalysis'] += ' %s (%s is %srunning)' % (
                service, exe, ('' if running else 'not '))


def install():
    '''Install the python apport hook.'''

    sys.excepthook = apport_excepthook
