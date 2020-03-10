'''Abstract crash database interface.'''

# Copyright (C) 2007 - 2009 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import os, os.path, sys, shutil

try:
    from exceptions import Exception
    from urllib import quote_plus, urlopen
    URLError = IOError
    (quote_plus, urlopen)  # pyflakes
except ImportError:
    # python 3
    from functools import cmp_to_key
    from urllib.parse import quote_plus
    from urllib.request import urlopen
    from urllib.error import URLError

import apport


def _u(str):
    '''Convert str to an unicode if it isn't already.'''

    if isinstance(str, bytes):
        return str.decode('UTF-8', 'ignore')
    return str


class CrashDatabase:
    def __init__(self, auth_file, options):
        '''Initialize crash database connection.

        You need to specify an implementation specific file with the
        authentication credentials for retracing access for download() and
        update(). For upload() and get_comment_url() you can use None.

        options is a dictionary with additional settings from crashdb.conf; see
        get_crashdb() for details.
        '''
        self.auth_file = auth_file
        self.options = options
        self.duplicate_db = None

    def get_bugpattern_baseurl(self):
        '''Return the base URL for bug patterns.

        See apport.report.Report.search_bug_patterns() for details. If this
        function returns None, bug patterns are disabled.
        '''
        return self.options.get('bug_pattern_url')

    def accepts(self, report):
        '''Check if this report can be uploaded to this database.

        Crash databases might limit the types of reports they get with e. g.
        the "problem_types" option.
        '''
        if 'problem_types' in self.options:
            return report.get('ProblemType') in self.options['problem_types']

        return True

    #
    # API for duplicate detection
    #
    # Tests are in apport/crashdb_impl/memory.py.

    def init_duplicate_db(self, path):
        '''Initialize duplicate database.

        path specifies an SQLite database. It will be created if it does not
        exist yet.
        '''
        import sqlite3 as dbapi2

        assert dbapi2.paramstyle == 'qmark', \
            'this module assumes qmark dbapi parameter style'

        self.format_version = 3

        init = not os.path.exists(path) or path == ':memory:' or \
            os.path.getsize(path) == 0
        self.duplicate_db = dbapi2.connect(path, timeout=7200)

        if init:
            cur = self.duplicate_db.cursor()
            cur.execute('CREATE TABLE version (format INTEGER NOT NULL)')
            cur.execute('INSERT INTO version VALUES (?)', [self.format_version])

            cur.execute('''CREATE TABLE crashes (
                signature VARCHAR(255) NOT NULL,
                crash_id INTEGER NOT NULL,
                fixed_version VARCHAR(50),
                last_change TIMESTAMP,
                CONSTRAINT crashes_pk PRIMARY KEY (crash_id))''')

            cur.execute('''CREATE TABLE address_signatures (
                signature VARCHAR(1000) NOT NULL,
                crash_id INTEGER NOT NULL,
                CONSTRAINT address_signatures_pk PRIMARY KEY (signature))''')

            self.duplicate_db.commit()

        # verify integrity
        cur = self.duplicate_db.cursor()
        cur.execute('PRAGMA integrity_check')
        result = cur.fetchall()
        if result != [('ok',)]:
            raise SystemError('Corrupt duplicate db:' + str(result))

        try:
            cur.execute('SELECT format FROM version')
            result = cur.fetchone()
        except self.duplicate_db.OperationalError as e:
            if 'no such table' in str(e):
                # first db format did not have version table yet
                result = [0]
        if result[0] > self.format_version:
            raise SystemError('duplicate DB has unknown format %i' % result[0])
        if result[0] < self.format_version:
            print('duplicate db has format %i, upgrading to %i' %
                  (result[0], self.format_version))
            self._duplicate_db_upgrade(result[0])

    def check_duplicate(self, id, report=None):
        '''Check whether a crash is already known.

        If the crash is new, it will be added to the duplicate database and the
        function returns None. If the crash is already known, the function
        returns a pair (crash_id, fixed_version), where fixed_version might be
        None if the crash is not fixed in the latest version yet. Depending on
        whether the version in report is smaller than/equal to the fixed
        version or larger, this calls close_duplicate() or mark_regression().

        If the report does not have a valid crash signature, this function does
        nothing and just returns None.

        By default, the report gets download()ed, but for performance reasons
        it can be explicitly passed to this function if it is already available.
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        if not report:
            report = self.download(id)

        self._mark_dup_checked(id, report)

        if 'DuplicateSignature' in report:
            sig = report['DuplicateSignature']
        else:
            sig = report.crash_signature()
        existing = []
        if sig:
            # use real duplicate signature
            existing = self._duplicate_search_signature(sig, id)

            if existing:
                # update status of existing master bugs
                for (ex_id, _) in existing:
                    self._duplicate_db_sync_status(ex_id)
                existing = self._duplicate_search_signature(sig, id)

        try:
            report_package_version = report['Package'].split()[1]
        except (KeyError, IndexError):
            report_package_version = None

        # check the existing IDs whether there is one that is unfixed or not
        # older than the report's package version; if so, we have a duplicate.
        master_id = None
        master_ver = None
        for (ex_id, ex_ver) in existing:
            if not ex_ver or not report_package_version or apport.packaging.compare_versions(report_package_version, ex_ver) < 0:
                master_id = ex_id
                master_ver = ex_ver
                break
        else:
            # if we did not find a new enough open master report,
            # we have a regression of the latest fix. Mark it so, and create a
            # new unfixed ID for it later on
            if existing:
                self.mark_regression(id, existing[-1][0])

        # now query address signatures, they might turn up another duplicate
        # (not necessarily the same, due to Stacktraces sometimes being
        # slightly different)
        addr_sig = report.crash_signature_addresses()
        if addr_sig:
            addr_match = self._duplicate_search_address_signature(addr_sig)
            if addr_match and addr_match != master_id:
                if master_id is None:
                    # we have a duplicate only identified by address sig, close it
                    master_id = addr_match
                else:
                    # our bug is a dupe of two different masters, one from
                    # symbolic, the other from addr matching (see LP#943117);
                    # make them all duplicates of each other, using the lower
                    # number as master
                    if master_id < addr_match:
                        self.close_duplicate(report, addr_match, master_id)
                        self._duplicate_db_merge_id(addr_match, master_id)
                    else:
                        self.close_duplicate(report, master_id, addr_match)
                        self._duplicate_db_merge_id(master_id, addr_match)
                        master_id = addr_match
                        master_ver = None  # no version tracking for address signatures yet

        if master_id is not None and master_id != id:
            if addr_sig:
                self._duplicate_db_add_address_signature(addr_sig, master_id)
            self.close_duplicate(report, id, master_id)
            return (master_id, master_ver)

        # no duplicate detected; create a new record for the ID if we don't have one already
        if sig:
            cur = self.duplicate_db.cursor()
            cur.execute('SELECT count(*) FROM crashes WHERE crash_id == ?', [id])
            count_id = cur.fetchone()[0]
            if count_id == 0:
                cur.execute('INSERT INTO crashes VALUES (?, ?, ?, CURRENT_TIMESTAMP)', (_u(sig), id, None))
                self.duplicate_db.commit()
        if addr_sig:
            self._duplicate_db_add_address_signature(addr_sig, id)

        return None

    def known(self, report):
        '''Check if the crash db already knows about the crash signature.

        Check if the report has a DuplicateSignature, crash_signature(), or
        StacktraceAddressSignature, and ask the database whether the problem is
        already known. If so, return an URL where the user can check the status
        or subscribe (if available), or just return True if the report is known
        but there is no public URL. In that case the report will not be
        uploaded (i. e. upload() will not be called).

        Return None if the report does not have any signature or the crash
        database does not support checking for duplicates on the client side.

        The default implementation uses a text file format generated by
        duplicate_db_publish() at an URL specified by the "dupdb_url" option.
        Subclasses are free to override this with a custom implementation, such
        as a real database lookup.
        '''
        if not self.options.get('dupdb_url'):
            return None

        for kind in ('sig', 'address'):
            # get signature
            if kind == 'sig':
                if 'DuplicateSignature' in report:
                    sig = report['DuplicateSignature']
                else:
                    sig = report.crash_signature()
            else:
                sig = report.crash_signature_addresses()

            if not sig:
                continue

            # build URL where the data should be
            h = self.duplicate_sig_hash(sig)
            if not h:
                return None

            # the hash is already quoted, but we really want to open the quoted
            # file names; as urlopen() unquotes, we need to double-quote here
            # again so that urlopen() sees the single-quoted file names
            url = os.path.join(self.options['dupdb_url'], kind, quote_plus(h))

            # read data file
            try:
                f = urlopen(url)
                contents = f.read().decode('UTF-8')
                f.close()
                if '<title>404 Not Found' in contents:
                    continue
            except (IOError, URLError):
                # does not exist, failed to load, etc.
                continue

            # now check if we find our signature
            for line in contents.splitlines():
                try:
                    id, s = line.split(None, 1)
                    id = int(id)
                except ValueError:
                    continue
                if s == sig:
                    result = self.get_id_url(report, id)
                    if not result:
                        # if we can't have an URL, just report as "known"
                        result = '1'
                    return result

        return None

    def duplicate_db_fixed(self, id, version):
        '''Mark given crash ID as fixed in the duplicate database.

        version specifies the package version the crash was fixed in (None for
        'still unfixed').
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        cur = self.duplicate_db.cursor()
        n = cur.execute('UPDATE crashes SET fixed_version = ?, last_change = CURRENT_TIMESTAMP WHERE crash_id = ?',
                        (version, id))
        assert n.rowcount == 1
        self.duplicate_db.commit()

    def duplicate_db_remove(self, id):
        '''Remove crash from the duplicate database.

        This happens when a report got rejected or manually duplicated.
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        cur = self.duplicate_db.cursor()
        cur.execute('DELETE FROM crashes WHERE crash_id = ?', [id])
        cur.execute('DELETE FROM address_signatures WHERE crash_id = ?', [id])
        self.duplicate_db.commit()

    def duplicate_db_change_master_id(self, old_id, new_id):
        '''Change a crash ID.'''

        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        cur = self.duplicate_db.cursor()
        cur.execute('UPDATE crashes SET crash_id = ?, last_change = CURRENT_TIMESTAMP WHERE crash_id = ?',
                    [new_id, old_id])
        cur.execute('UPDATE address_signatures SET crash_id = ? WHERE crash_id = ?',
                    [new_id, old_id])
        self.duplicate_db.commit()

    def duplicate_db_publish(self, dir):
        '''Create text files suitable for www publishing.

        Create a number of text files in the given directory which Apport
        clients can use to determine whether a problem is already reported to
        the database, through the known() method. This directory is suitable
        for publishing to the web.

        The database is indexed by the first two fields of the duplicate or
        crash signature, to avoid having to download the entire database every
        time.

        If the directory already exists, it will be updated. The new content is
        built in a new directory which is the given one with ".new" appended,
        then moved to the given name in an almost atomic way.
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        # first create the temporary new dir; if that fails, nothing has been
        # changed and we fail early
        out = dir + '.new'
        os.mkdir(out)

        # crash addresses
        addr_base = os.path.join(out, 'address')
        os.mkdir(addr_base)
        cur_hash = None
        cur_file = None

        cur = self.duplicate_db.cursor()

        cur.execute('SELECT * from address_signatures ORDER BY signature')
        for (sig, id) in cur.fetchall():
            h = self.duplicate_sig_hash(sig)
            if h is None:
                # some entries can't be represented in a single line
                continue
            if h != cur_hash:
                cur_hash = h
                if cur_file:
                    cur_file.close()
                cur_file = open(os.path.join(addr_base, cur_hash), 'w')

            cur_file.write('%i %s\n' % (id, sig))

        if cur_file:
            cur_file.close()

        # duplicate signatures
        sig_base = os.path.join(out, 'sig')
        os.mkdir(sig_base)
        cur_hash = None
        cur_file = None

        cur.execute('SELECT signature, crash_id from crashes ORDER BY signature')
        for (sig, id) in cur.fetchall():
            h = self.duplicate_sig_hash(sig)
            if h is None:
                # some entries can't be represented in a single line
                continue
            if h != cur_hash:
                cur_hash = h
                if cur_file:
                    cur_file.close()
                cur_file = open(os.path.join(sig_base, cur_hash), 'wb')

            cur_file.write(('%i %s\n' % (id, sig)).encode('UTF-8'))

        if cur_file:
            cur_file.close()

        # switch over tree; this is as atomic as we can be with directories
        if os.path.exists(dir):
            os.rename(dir, dir + '.old')
        os.rename(out, dir)
        if os.path.exists(dir + '.old'):
            shutil.rmtree(dir + '.old')

    def _duplicate_db_upgrade(self, cur_format):
        '''Upgrade database to current format'''

        # Format 3 added a primary key which can't be done as an upgrade in
        # SQLite
        if cur_format < 3:
            raise SystemError('Cannot upgrade database from format earlier than 3')

        cur = self.duplicate_db.cursor()

        cur.execute('UPDATE version SET format = ?', (cur_format,))
        self.duplicate_db.commit()

        assert cur_format == self.format_version

    def _duplicate_search_signature(self, sig, id):
        '''Look up signature in the duplicate db.

        Return [(id, fixed_version)] tuple list.

        There might be several matches if a crash has been reintroduced in a
        later version. The results are sorted so that the highest fixed version
        comes first, and "unfixed" being the last result.

        id is the bug we are looking to find a duplicate for. The result will
        never contain id, to avoid marking a bug as a duplicate of itself if a
        bug is reprocessed more than once.
        '''
        cur = self.duplicate_db.cursor()
        cur.execute('SELECT crash_id, fixed_version FROM crashes WHERE signature = ? AND crash_id <> ?', [_u(sig), id])
        existing = cur.fetchall()

        def cmp(x, y):
            x = x[1]
            y = y[1]
            if x == y:
                return 0
            if x == '':
                if y is None:
                    return -1
                else:
                    return 1
            if y == '':
                if x is None:
                    return 1
                else:
                    return -1
            if x is None:
                return 1
            if y is None:
                return -1
            return apport.packaging.compare_versions(x, y)

        if sys.version[0] >= '3':
            existing.sort(key=cmp_to_key(cmp))
        else:
            existing.sort(cmp=cmp)

        return existing

    def _duplicate_search_address_signature(self, sig):
        '''Return ID for crash address signature.

        Return None if signature is unknown.
        '''
        if not sig:
            return None

        cur = self.duplicate_db.cursor()

        cur.execute('SELECT crash_id FROM address_signatures WHERE signature == ?', [sig])
        existing_ids = cur.fetchall()
        assert len(existing_ids) <= 1
        if existing_ids:
            return existing_ids[0][0]
        else:
            return None

    def _duplicate_db_dump(self, with_timestamps=False):
        '''Return the entire duplicate database as a dictionary.

        The returned dictionary maps "signature" to (crash_id, fixed_version)
        pairs.

        If with_timestamps is True, then the map will contain triples
        (crash_id, fixed_version, last_change) instead.

        This is mainly useful for debugging and test suites.
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        dump = {}
        cur = self.duplicate_db.cursor()
        cur.execute('SELECT * FROM crashes')
        for (sig, id, ver, last_change) in cur:
            if with_timestamps:
                dump[sig] = (id, ver, last_change)
            else:
                dump[sig] = (id, ver)
        return dump

    def _duplicate_db_sync_status(self, id):
        '''Update the duplicate db to the reality of the report in the crash db.

        This uses get_fixed_version() to get the status of the given crash.
        An invalid ID gets removed from the duplicate db, and a crash which got
        fixed is marked as such in the database.
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        cur = self.duplicate_db.cursor()
        cur.execute('SELECT fixed_version FROM crashes WHERE crash_id = ?', [id])
        db_fixed_version = cur.fetchone()
        if not db_fixed_version:
            return
        db_fixed_version = db_fixed_version[0]

        real_fixed_version = self.get_fixed_version(id)

        # crash got rejected
        if real_fixed_version == 'invalid':
            print('DEBUG: bug %i was invalidated, removing from database' % id)
            self.duplicate_db_remove(id)
            return

        # crash got fixed
        if not db_fixed_version and real_fixed_version:
            print('DEBUG: bug %i got fixed in version %s, updating database' % (id, real_fixed_version))
            self.duplicate_db_fixed(id, real_fixed_version)
            return

        # crash got reopened
        if db_fixed_version and not real_fixed_version:
            print('DEBUG: bug %i got reopened, dropping fixed version %s from database' % (id, db_fixed_version))
            self.duplicate_db_fixed(id, real_fixed_version)
            return

    def _duplicate_db_add_address_signature(self, sig, id):
        # sanity check
        existing = self._duplicate_search_address_signature(sig)
        if existing:
            if existing != id:
                raise SystemError('ID %i has signature %s, but database already has that signature for ID %i' % (
                    id, sig, existing))
        else:
            cur = self.duplicate_db.cursor()
            cur.execute('INSERT INTO address_signatures VALUES (?, ?)', (_u(sig), id))
            self.duplicate_db.commit()

    def _duplicate_db_merge_id(self, dup, master):
        '''Merge two crash IDs.

        This is necessary when having to mark a bug as a duplicate if it
        already is in the duplicate DB.
        '''
        assert self.duplicate_db, 'init_duplicate_db() needs to be called before'

        cur = self.duplicate_db.cursor()
        cur.execute('DELETE FROM crashes WHERE crash_id = ?', [dup])
        cur.execute('UPDATE address_signatures SET crash_id = ? WHERE crash_id = ?',
                    [master, dup])
        self.duplicate_db.commit()

    @classmethod
    def duplicate_sig_hash(klass, sig):
        '''Create a www/URL proof hash for a duplicate signature'''

        # cannot hash multi-line custom duplicate signatures
        if '\n' in sig:
            return None

        # custom DuplicateSignatures have a free format, split off first word
        i = sig.split(' ', 1)[0]
        # standard crash/address signatures use ':' as field separator, usually
        # for ExecutableName:Signal
        i = '_'.join(i.split(':', 2)[:2])
        # we manually quote '/' to make them nicer to read
        i = i.replace('/', '_')
        i = quote_plus(i.encode('UTF-8'))
        # avoid too long file names
        i = i[:200]
        return i

    #
    # Abstract functions that need to be implemented by subclasses
    #

    def upload(self, report, progress_callback=None):
        '''Upload given problem report return a handle for it.

        This should happen noninteractively.

        If the implementation supports it, and a function progress_callback is
        passed, that is called repeatedly with two arguments: the number of
        bytes already sent, and the total number of bytes to send. This can be
        used to provide a proper upload progress indication on frontends.

        Implementations ought to "assert self.accepts(report)". The UI logic
        already prevents uploading a report to a database which does not accept
        it, but for third-party users of the API this should still be checked.

        This method can raise a NeedsCredentials exception in case of failure.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_comment_url(self, report, handle):
        '''Return an URL that should be opened after report has been uploaded
        and upload() returned handle.

        Should return None if no URL should be opened (anonymous filing without
        user comments); in that case this function should do whichever
        interactive steps it wants to perform.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_id_url(self, report, id):
        '''Return URL for a given report ID.

        The report is passed in case building the URL needs additional
        information from it, such as the SourcePackage name.

        Return None if URL is not available or cannot be determined.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def download(self, id):
        '''Download the problem report from given ID and return a Report.'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

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
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def update_traces(self, id, report, comment=''):
        '''Update the given report ID for retracing results.

        This updates Stacktrace, ThreadStacktrace, StacktraceTop,
        and StacktraceSource. You can also supply an additional comment.
        '''
        self.update(id, report, comment, key_filter=[
            'Stacktrace', 'ThreadStacktrace', 'StacktraceSource', 'StacktraceTop'])

    def set_credentials(self, username, password):
        '''Set username and password.'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_distro_release(self, id):
        '''Get 'DistroRelease: <release>' from the report ID.'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_unretraced(self):
        '''Return set of crash IDs which have not been retraced yet.

        This should only include crashes which match the current host
        architecture.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_dup_unchecked(self):
        '''Return set of crash IDs which need duplicate checking.

        This is mainly useful for crashes of scripting languages such as
        Python, since they do not need to be retraced. It should not return
        bugs that are covered by get_unretraced().
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_unfixed(self):
        '''Return an ID set of all crashes which are not yet fixed.

        The list must not contain bugs which were rejected or duplicate.

        This function should make sure that the returned list is correct. If
        there are any errors with connecting to the crash database, it should
        raise an exception (preferably IOError).
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_fixed_version(self, id):
        '''Return the package version that fixes a given crash.

        Return None if the crash is not yet fixed, or an empty string if the
        crash is fixed, but it cannot be determined by which version. Return
        'invalid' if the crash report got invalidated, such as closed a
        duplicate or rejected.

        This function should make sure that the returned result is correct. If
        there are any errors with connecting to the crash database, it should
        raise an exception (preferably IOError).
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def get_affected_packages(self, id):
        '''Return list of affected source packages for given ID.'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def is_reporter(self, id):
        '''Check whether the user is the reporter of given ID.'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def can_update(self, id):
        '''Check whether the user is eligible to update a report.

        A user should add additional information to an existing ID if (s)he is
        the reporter or subscribed, the bug is open, not a duplicate, etc. The
        exact policy and checks should be done according to  the particular
        implementation.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def duplicate_of(self, id):
        '''Return master ID for a duplicate bug.

        If the bug is not a duplicate, return None.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def close_duplicate(self, report, id, master):
        '''Mark a crash id as duplicate of given master ID.

        If master is None, id gets un-duplicated.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def mark_regression(self, id, master):
        '''Mark a crash id as reintroducing an earlier crash which is
        already marked as fixed (having ID 'master').'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def mark_retraced(self, id):
        '''Mark crash id as retraced.'''

        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def mark_retrace_failed(self, id, invalid_msg=None):
        '''Mark crash id as 'failed to retrace'.

        If invalid_msg is given, the bug should be closed as invalid with given
        message, otherwise just marked as a failed retrace.

        This can be a no-op if you are not interested in this.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

    def _mark_dup_checked(self, id, report):
        '''Mark crash id as checked for being a duplicate

        This is an internal method that should not be called from outside.
        '''
        raise NotImplementedError('this method must be implemented by a concrete subclass')

#
# factory
#


def get_crashdb(auth_file, name=None, conf=None):
    '''Return a CrashDatabase object for the given crash db name.

    This reads the configuration file 'conf'.

    If name is None, it defaults to the 'default' value in conf.

    If conf is None, it defaults to the environment variable
    APPORT_CRASHDB_CONF; if that does not exist, the hardcoded default is
    /etc/apport/crashdb.conf. This Python syntax file needs to specify:

    - A string variable 'default', giving a default value for 'name' if that is
      None.

    - A dictionary 'databases' which maps names to crash db configuration
      dictionaries. These need to have at least the key 'impl' (Python module
      in apport.crashdb_impl which contains a concrete 'CrashDatabase' class
      implementation for that crash db type). Other generally known options are
      'bug_pattern_url', 'dupdb_url', and 'problem_types'.
    '''
    if not conf:
        conf = os.environ.get('APPORT_CRASHDB_CONF', '/etc/apport/crashdb.conf')
    settings = {}
    with open(conf) as f:
        exec(compile(f.read(), conf, 'exec'), settings)

    # Load third parties crashdb.conf
    confdDir = conf + '.d'
    if os.path.isdir(confdDir):
        for cf in os.listdir(confdDir):
            cfpath = os.path.join(confdDir, cf)
            if os.path.isfile(cfpath) and cf.endswith('.conf'):
                try:
                    with open(cfpath) as f:
                        exec(compile(f.read(), cfpath, 'exec'), settings['databases'])
                except Exception as e:
                    # ignore broken files
                    sys.stderr.write('Invalid file %s: %s\n' % (cfpath, str(e)))
                    pass

    if not name:
        name = settings['default']

    return load_crashdb(auth_file, settings['databases'][name])


def load_crashdb(auth_file, spec):
    '''Return a CrashDatabase object for a given DB specification.

    spec is a crash db configuration dictionary as described in get_crashdb().
    '''
    m = __import__('apport.crashdb_impl.' + spec['impl'], globals(), locals(), ['CrashDatabase'])
    return m.CrashDatabase(auth_file, spec)


class NeedsCredentials(Exception):
    '''This may be raised when unable to log in to the crashdb.'''
    pass
