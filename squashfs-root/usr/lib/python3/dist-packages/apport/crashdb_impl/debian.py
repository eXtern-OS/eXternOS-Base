'''Debian crash database interface.'''

# Debian adaptation Copyright (C) 2012 Ritesh Raj Sarraf <rrs@debian.org>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.


import smtplib, tempfile
from email.mime.text import MIMEText

import apport
import apport.crashdb


class CrashDatabase(apport.crashdb.CrashDatabase):
    '''
    Debian crash database
    This is a Apport CrashDB implementation for interacting with Debian BTS
    '''
    def __init__(self, auth_file, options):
        '''
        Initialize crash database connection.

        Debian implementation is pretty basic as most of its bug management
        processes revolve around the email interface
        '''
        apport.crashdb.CrashDatabase.__init__(self, auth_file, options)
        self.options = options

        if not self.options.get('smtphost'):
            self.options['smtphost'] = 'reportbug.debian.org'

        if not self.options.get('recipient'):
            self.options['recipient'] = 'submit@bugs.debian.org'

    def accepts(self, report):
        '''
        Check if this report can be uploaded to this database.
        Checks for the proper settings of apport.
        '''
        if not self.options.get('sender') and 'UnreportableReason' not in report:
            report['UnreportableReason'] = 'Please configure sender settings in /etc/apport/crashdb.conf'

        # At this time, we are not ready to take CrashDumps
        if 'Stacktrace' in report and not report.has_useful_stacktrace():
            report['UnreportableReason'] = 'Incomplete backtrace. Please install the debug symbol packages'

        return apport.crashdb.CrashDatabase.accepts(self, report)

    def upload(self, report, progress_callback=None):
        '''Upload given problem report return a handle for it.

        In Debian, we use BTS, which is heavily email oriented
        This method crafts the bug into an email report understood by Debian BTS
        '''
        # first and foremost, let's check if the apport bug filing settings are set correct
        assert self.accepts(report)

        # Frame the report in the format the BTS understands
        try:
            (buggyPackage, buggyVersion) = report['Package'].split(' ')
        except (KeyError, ValueError):
            return False

        temp = tempfile.NamedTemporaryFile()

        temp.file.write(('Package: ' + buggyPackage + '\n').encode('UTF-8'))
        temp.file.write(('Version: ' + buggyVersion + '\n\n\n').encode('UTF-8'))
        temp.file.write(('=============================\n\n').encode('UTF-8'))

        # Let's remove the CoreDump first

        # Even if we have a valid backtrace, we already are reporting it as text
        # We don't want to send very large emails to the BTS.
        # OTOH, if the backtrace is invalid, has_useful_backtrace() will already
        # deny reporting of the bug report.
        try:
            del report['CoreDump']
        except KeyError:
            pass

        # Now write the apport bug report
        report.write(temp)

        temp.file.seek(0)

        msg = MIMEText(temp.file.read().decode('UTF-8'))
        msg['Subject'] = report['Title']
        msg['From'] = self.options['sender']
        msg['To'] = self.options['recipient']

        # Subscribe the submitted to the bug report
        msg.add_header('X-Debbugs-CC', self.options['sender'])
        msg.add_header('Usertag', 'apport-%s' % report['ProblemType'].lower())

        s = smtplib.SMTP(self.options['smtphost'])
        s.sendmail(self.options['sender'], self.options['recipient'], msg.as_string().encode('UTF-8'))
        s.quit()

    def get_comment_url(self, report, handle):
        '''
        Return an URL that should be opened after report has been uploaded
        and upload() returned handle.

        Should return None if no URL should be opened (anonymous filing without
        user comments); in that case this function should do whichever
        interactive steps it wants to perform.
        '''
        return None
