'''Simple in-memory CrashDatabase implementation, mainly useful for testing.'''

# Copyright (C) 2007 - 2009 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import apport.crashdb
import apport


class CrashDatabase(apport.crashdb.CrashDatabase):
    '''Simple implementation of crash database interface which keeps everything
    in memory.

    This is mainly useful for testing and debugging.'''

    def __init__(self, auth_file, options):
        '''Initialize crash database connection.

        This class does not support bug patterns and authentication.'''

        apport.crashdb.CrashDatabase.__init__(self, auth_file, options)

        self.reports = []  # list of dictionaries with keys: report, fixed_version, dup_of, comment
        self.unretraced = set()
        self.dup_unchecked = set()

        if 'dummy_data' in options:
            self.add_dummy_data()

    def upload(self, report, progress_callback=None):
        '''Store the report and return a handle number (starting from 0).

        This does not support (nor need) progress callbacks.
        '''
        assert self.accepts(report)

        self.reports.append({'report': report, 'fixed_version': None, 'dup_of':
                             None, 'comment': ''})
        id = len(self.reports) - 1
        if 'Traceback' in report:
            self.dup_unchecked.add(id)
        else:
            self.unretraced.add(id)
        return id

    def get_comment_url(self, report, handle):
        '''Return http://<sourcepackage>.bugs.example.com/<handle> for package bugs
        or http://bugs.example.com/<handle> for reports without a SourcePackage.'''

        if 'SourcePackage' in report:
            return 'http://%s.bugs.example.com/%i' % (report['SourcePackage'], handle)
        else:
            return 'http://bugs.example.com/%i' % handle

    def get_id_url(self, report, id):
        '''Return URL for a given report ID.

        The report is passed in case building the URL needs additional
        information from it, such as the SourcePackage name.

        Return None if URL is not available or cannot be determined.
        '''
        return self.get_comment_url(report, id)

    def download(self, id):
        '''Download the problem report from given ID and return a Report.'''

        return self.reports[id]['report']

    def get_affected_packages(self, id):
        '''Return list of affected source packages for given ID.'''

        return [self.reports[id]['report']['SourcePackage']]

    def is_reporter(self, id):
        '''Check whether the user is the reporter of given ID.'''

        return True

    def can_update(self, id):
        '''Check whether the user is eligible to update a report.

        A user should add additional information to an existing ID if (s)he is
        the reporter or subscribed, the bug is open, not a duplicate, etc. The
        exact policy and checks should be done according to  the particular
        implementation.
        '''
        return self.is_reporter(id)

    def update(self, id, report, comment, change_description=False,
               attachment_comment=None, key_filter=None):
        '''Update the given report ID with all data from report.

        This creates a text comment with the "short" data (see
        ProblemReport.write_mime()), and creates attachments for all the
        bulk/binary data.

        If change_description is True, and the crash db implementation supports
        it, the short data will be put into the description instead (like in a
        new bug).

        comment will be added to the "short" data. If attachment_comment is
        given, it will be added to the attachment uploads.

        If key_filter is a list or set, then only those keys will be added.
        '''
        r = self.reports[id]
        r['comment'] = comment

        if key_filter:
            for f in key_filter:
                if f in report:
                    r['report'][f] = report[f]
        else:
            r['report'].update(report)

    def get_distro_release(self, id):
        '''Get 'DistroRelease: <release>' from the given report ID and return
        it.'''

        return self.reports[id]['report']['DistroRelease']

    def get_unfixed(self):
        '''Return an ID set of all crashes which are not yet fixed.

        The list must not contain bugs which were rejected or duplicate.

        This function should make sure that the returned list is correct. If
        there are any errors with connecting to the crash database, it should
        raise an exception (preferably IOError).'''

        result = set()
        for i in range(len(self.reports)):
            if self.reports[i]['dup_of'] is None and self.reports[i]['fixed_version'] is None:
                result.add(i)

        return result

    def get_fixed_version(self, id):
        '''Return the package version that fixes a given crash.

        Return None if the crash is not yet fixed, or an empty string if the
        crash is fixed, but it cannot be determined by which version. Return
        'invalid' if the crash report got invalidated, such as closed a
        duplicate or rejected.

        This function should make sure that the returned result is correct. If
        there are any errors with connecting to the crash database, it should
        raise an exception (preferably IOError).'''

        try:
            if self.reports[id]['dup_of'] is not None:
                return 'invalid'
            return self.reports[id]['fixed_version']
        except IndexError:
            return 'invalid'

    def duplicate_of(self, id):
        '''Return master ID for a duplicate bug.

        If the bug is not a duplicate, return None.
        '''
        return self.reports[id]['dup_of']

    def close_duplicate(self, report, id, master):
        '''Mark a crash id as duplicate of given master ID.

        If master is None, id gets un-duplicated.
        '''
        self.reports[id]['dup_of'] = master

    def mark_regression(self, id, master):
        '''Mark a crash id as reintroducing an earlier crash which is
        already marked as fixed (having ID 'master').'''

        assert self.reports[master]['fixed_version'] is not None
        self.reports[id]['comment'] = 'regression, already fixed in #%i' % master

    def _mark_dup_checked(self, id, report):
        '''Mark crash id as checked for being a duplicate.'''

        try:
            self.dup_unchecked.remove(id)
        except KeyError:
            pass  # happens when trying to check for dup twice

    def mark_retraced(self, id):
        '''Mark crash id as retraced.'''

        self.unretraced.remove(id)

    def get_unretraced(self):
        '''Return an ID set of all crashes which have not been retraced yet and
        which happened on the current host architecture.'''

        return self.unretraced

    def get_dup_unchecked(self):
        '''Return an ID set of all crashes which have not been checked for
        being a duplicate.

        This is mainly useful for crashes of scripting languages such as
        Python, since they do not need to be retraced. It should not return
        bugs that are covered by get_unretraced().'''

        return self.dup_unchecked

    def latest_id(self):
        '''Return the ID of the most recently filed report.'''

        return len(self.reports) - 1

    def add_dummy_data(self):
        '''Add some dummy crash reports.

        This is mostly useful for test suites.'''

        # signal crash with source package and complete stack trace
        r = apport.Report()
        r['Package'] = 'libfoo1 1.2-3'
        r['SourcePackage'] = 'foo'
        r['DistroRelease'] = 'FooLinux Pi/2'
        r['Signal'] = '11'
        r['ExecutablePath'] = '/bin/crash'

        r['StacktraceTop'] = '''foo_bar (x=1) at crash.c:28
d01 (x=1) at crash.c:29
raise () from /lib/libpthread.so.0
<signal handler called>
__frob (x=1) at crash.c:30'''
        self.upload(r)

        # duplicate of above crash (slightly different arguments and
        # package version)
        r = apport.Report()
        r['Package'] = 'libfoo1 1.2-4'
        r['SourcePackage'] = 'foo'
        r['DistroRelease'] = 'Testux 1.0'
        r['Signal'] = '11'
        r['ExecutablePath'] = '/bin/crash'

        r['StacktraceTop'] = '''foo_bar (x=2) at crash.c:28
d01 (x=3) at crash.c:29
raise () from /lib/libpthread.so.0
<signal handler called>
__frob (x=4) at crash.c:30'''
        self.upload(r)

        # unrelated signal crash
        r = apport.Report()
        r['Package'] = 'bar 42-4'
        r['SourcePackage'] = 'bar'
        r['DistroRelease'] = 'Testux 1.0'
        r['Signal'] = '11'
        r['ExecutablePath'] = '/usr/bin/broken'

        r['StacktraceTop'] = '''h (p=0x0) at crash.c:25
g (x=1, y=42) at crash.c:26
f (x=1) at crash.c:27
e (x=1) at crash.c:28
d (x=1) at crash.c:29'''
        self.upload(r)

        # Python crash
        r = apport.Report()
        r['Package'] = 'python-goo 3epsilon1'
        r['SourcePackage'] = 'pygoo'
        r['DistroRelease'] = 'Testux 2.2'
        r['ExecutablePath'] = '/usr/bin/pygoo'
        r['Traceback'] = '''Traceback (most recent call last):
  File "test.py", line 7, in <module>
    print(_f(5))
  File "test.py", line 5, in _f
    return g_foo00(x+1)
  File "test.py", line 2, in g_foo00
    return x/0
ZeroDivisionError: integer division or modulo by zero'''
        self.upload(r)

        # Python crash reoccurs in a later version (used for regression detection)
        r = apport.Report()
        r['Package'] = 'python-goo 5'
        r['SourcePackage'] = 'pygoo'
        r['DistroRelease'] = 'Testux 2.2'
        r['ExecutablePath'] = '/usr/bin/pygoo'
        r['Traceback'] = '''Traceback (most recent call last):
  File "test.py", line 7, in <module>
    print(_f(5))
  File "test.py", line 5, in _f
    return g_foo00(x+1)
  File "test.py", line 2, in g_foo00
    return x/0
ZeroDivisionError: integer division or modulo by zero'''
        self.upload(r)
