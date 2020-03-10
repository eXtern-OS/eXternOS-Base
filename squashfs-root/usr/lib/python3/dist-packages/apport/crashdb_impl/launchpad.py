# vim: set fileencoding=UTF-8 :
'''Crash database implementation for Launchpad.'''

# Copyright (C) 2007 - 2009 Canonical Ltd.
# Authors: Martin Pitt <martin.pitt@ubuntu.com> and Markus Korn <thekorn@gmx.de>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import tempfile, atexit, os.path, re, gzip, sys, email, time, shutil

from httplib2 import FailedToDecompressContent
from io import BytesIO

if sys.version_info.major == 2:
    from urllib2 import HTTPSHandler, Request, build_opener
    from httplib import HTTPSConnection
    from urllib import urlencode, urlopen
    (HTTPSHandler, Request, build_opener, HTTPSConnection, urlencode, urlopen)  # pyflakes
    _python2 = True
else:
    from urllib.request import HTTPSHandler, Request, build_opener, urlopen
    from urllib.parse import urlencode
    from http.client import HTTPSConnection
    _python2 = False

try:
    from launchpadlib.errors import HTTPError
    from launchpadlib.launchpad import Launchpad
    Launchpad  # pyflakes
except ImportError:
    # if launchpadlib is not available, only client-side reporting will work
    Launchpad = None

import apport.crashdb
import apport

default_credentials_path = os.path.expanduser('~/.cache/apport/launchpad.credentials')


def filter_filename(attachments):
    for attachment in attachments:
        try:
            f = attachment.data.open()
        except (HTTPError, FailedToDecompressContent):
            apport.error('Broken attachment on bug, ignoring')
            continue
        name = f.filename
        if name.endswith('.txt') or name.endswith('.gz'):
            yield f


def id_set(tasks):
    # same as set(int(i.bug.id) for i in tasks) but faster
    return set(int(i.self_link.split('/').pop()) for i in tasks)


class CrashDatabase(apport.crashdb.CrashDatabase):
    '''Launchpad implementation of crash database interface.'''

    def __init__(self, auth, options):
        '''Initialize Launchpad crash database.

        You need to specify a launchpadlib-style credentials file to
        access launchpad. If you supply None, it will use
        default_credentials_path (~/.cache/apport/launchpad.credentials).

        Recognized options are:
        - distro: Name of the distribution in Launchpad
        - project: Name of the project in Launchpad
        (Note that exactly one of "distro" or "project" must be given.)
        - launchpad_instance: If set, this uses the given launchpad instance
          instead of production (optional). This can be overriden or set by
          $APPORT_LAUNCHPAD_INSTANCE environment.
        - cache_dir: Path to a permanent cache directory; by default it uses a
          temporary one. (optional). This can be overridden or set by
          $APPORT_LAUNCHPAD_CACHE environment.
        - escalation_subscription: This subscribes the given person or team to
          a bug once it gets the 10th duplicate.
        - escalation_tag: This adds the given tag to a bug once it gets more
          than 10 duplicates.
        - initial_subscriber: The Launchpad user which gets subscribed to newly
          filed bugs (default: "apport"). It should be a bot user which the
          crash-digger instance runs as, as this will get to see all bug
          details immediately.
        - triaging_team: The Launchpad user/team which gets subscribed after
          updating a crash report bug by the retracer (default:
          "ubuntu-crashes-universe")
        - architecture: If set, this sets and watches out for needs-*-retrace
          tags of this architecture. This is useful when being used with
          apport-retrace and crash-digger to process crash reports of foreign
          architectures. Defaults to system architecture.
        '''
        if os.getenv('APPORT_LAUNCHPAD_INSTANCE'):
            options['launchpad_instance'] = os.getenv(
                'APPORT_LAUNCHPAD_INSTANCE')
        if not auth:
            lp_instance = options.get('launchpad_instance')
            if lp_instance:
                auth = default_credentials_path + '.' + lp_instance.split('://', 1)[-1]
            else:
                auth = default_credentials_path
        apport.crashdb.CrashDatabase.__init__(self, auth, options)

        self.distro = options.get('distro')
        if self.distro:
            assert 'project' not in options, 'Must not set both "project" and "distro" option'
        else:
            assert 'project' in options, 'Need to have either "project" or "distro" option'

        if 'architecture' in options:
            self.arch_tag = 'need-%s-retrace' % options['architecture']
        else:
            self.arch_tag = 'need-%s-retrace' % apport.packaging.get_system_architecture()
        self.options = options
        self.auth = auth
        assert self.auth

        self.__launchpad = None
        self.__lp_distro = None
        self.__lpcache = os.getenv('APPORT_LAUNCHPAD_CACHE', options.get('cache_dir'))
        if not self.__lpcache:
            # use a temporary dir
            self.__lpcache = tempfile.mkdtemp(prefix='launchpadlib.cache.')
            atexit.register(shutil.rmtree, self.__lpcache, ignore_errors=True)

    @property
    def launchpad(self):
        '''Return Launchpad instance.'''

        if self.__launchpad:
            return self.__launchpad

        if Launchpad is None:
            if _python2:
                sys.stderr.write('ERROR: The python-launchpadlib package is not installed. This functionality is not available.\n')
            else:
                sys.stderr.write('ERROR: The python3-launchpadlib package is not installed. This functionality is not available.\n')

            sys.exit(1)

        if self.options.get('launchpad_instance'):
            launchpad_instance = self.options.get('launchpad_instance')
        else:
            launchpad_instance = 'production'

        auth_dir = os.path.dirname(self.auth)
        if auth_dir and not os.path.isdir(auth_dir):
            os.makedirs(auth_dir)

        try:
            self.__launchpad = Launchpad.login_with('apport-collect',
                                                    launchpad_instance,
                                                    launchpadlib_dir=self.__lpcache,
                                                    allow_access_levels=['WRITE_PRIVATE'],
                                                    credentials_file=self.auth,
                                                    version='1.0')
        except Exception as e:
            if hasattr(e, 'content'):
                msg = e.content
            else:
                msg = str(e)
            apport.error('connecting to Launchpad failed: %s\nYou can reset the credentials by removing the file "%s"', msg, self.auth)
            sys.exit(99)  # transient error

        return self.__launchpad

    def _get_distro_tasks(self, tasks):
        if not self.distro:
            raise StopIteration

        for t in tasks:
            if t.bug_target_name.lower() == self.distro or \
                    re.match(r'^.+\(%s.*\)$' % self.distro, t.bug_target_name.lower()):
                yield t

    @property
    def lp_distro(self):
        if self.__lp_distro is None:
            if self.distro:
                self.__lp_distro = self.launchpad.distributions[self.distro]
            elif 'project' in self.options:
                self.__lp_distro = self.launchpad.projects[self.options['project']]
            else:
                raise SystemError('distro or project needs to be specified in crashdb options')

        return self.__lp_distro

    def upload(self, report, progress_callback=None):
        '''Upload given problem report return a handle for it.

        This should happen noninteractively.

        If the implementation supports it, and a function progress_callback is
        passed, that is called repeatedly with two arguments: the number of
        bytes already sent, and the total number of bytes to send. This can be
        used to provide a proper upload progress indication on frontends.
        '''
        assert self.accepts(report)

        blob_file = self._generate_upload_blob(report)
        ticket = upload_blob(blob_file, progress_callback, hostname=self.get_hostname())
        blob_file.close()
        assert ticket
        return ticket

    def get_hostname(self):
        '''Return the hostname for the Launchpad instance.'''

        launchpad_instance = self.options.get('launchpad_instance')
        if launchpad_instance:
            if launchpad_instance == 'staging':
                hostname = 'staging.launchpad.net'
            else:
                hostname = 'launchpad.dev'
        else:
            hostname = 'launchpad.net'
        return hostname

    def get_comment_url(self, report, handle):
        '''Return an URL that should be opened after report has been uploaded
        and upload() returned handle.

        Should return None if no URL should be opened (anonymous filing without
        user comments); in that case this function should do whichever
        interactive steps it wants to perform.'''

        args = {}
        title = report.get('Title', report.standard_title())
        if title:
            # always use UTF-8 encoding, urlencode() blows up otherwise in
            # python 2.7
            if not isinstance(title, bytes):
                title = title.encode('UTF-8')
            args['field.title'] = title

        hostname = self.get_hostname()

        project = self.options.get('project')

        if not project:
            if 'SourcePackage' in report:
                return 'https://bugs.%s/%s/+source/%s/+filebug/%s?%s' % (
                    hostname, self.distro, report['SourcePackage'], handle, urlencode(args))
            else:
                return 'https://bugs.%s/%s/+filebug/%s?%s' % (
                    hostname, self.distro, handle, urlencode(args))
        else:
            return 'https://bugs.%s/%s/+filebug/%s?%s' % (
                hostname, project, handle, urlencode(args))

    def get_id_url(self, report, id):
        '''Return URL for a given report ID.

        The report is passed in case building the URL needs additional
        information from it, such as the SourcePackage name.

        Return None if URL is not available or cannot be determined.
        '''
        return 'https://bugs.launchpad.net/bugs/' + str(id)

    def download(self, id):
        '''Download the problem report from given ID and return a Report.'''

        report = apport.Report()
        b = self.launchpad.bugs[id]

        # parse out fields from summary
        m = re.search(r'(ProblemType:.*)$', b.description, re.S)
        if not m:
            m = re.search(r'^--- \r?$[\r\n]*(.*)', b.description, re.M | re.S)
        assert m, 'bug description must contain standard apport format data'

        description = m.group(1).encode('UTF-8').replace(b'\xc2\xa0', b' ').replace(b'\r\n', b'\n')

        if b'\n\n' in description:
            # this often happens, remove all empty lines between top and
            # 'Uname'
            if b'Uname:' in description:
                # this will take care of bugs like LP #315728 where stuff
                # is added after the apport data
                (part1, part2) = description.split(b'Uname:', 1)
                description = part1.replace(b'\n\n', b'\n') + b'Uname:' \
                    + part2.split(b'\n\n', 1)[0]
            else:
                # just parse out the Apport block; e. g. LP #269539
                description = description.split(b'\n\n', 1)[0]

        report.load(BytesIO(description))

        if 'Date' not in report:
            # We had not submitted this field for a while, claiming it
            # redundant. But it is indeed required for up-to-the-minute
            # comparison with log files, etc. For backwards compatibility with
            # those reported bugs, read the creation date
            try:
                report['Date'] = b.date_created.ctime()
            except AttributeError:
                # support older wadllib API which returned strings
                report['Date'] = b.date_created
        if 'ProblemType' not in report:
            if 'apport-bug' in b.tags:
                report['ProblemType'] = 'Bug'
            elif 'apport-crash' in b.tags:
                report['ProblemType'] = 'Crash'
            elif 'apport-kernelcrash' in b.tags:
                report['ProblemType'] = 'KernelCrash'
            elif 'apport-package' in b.tags:
                report['ProblemType'] = 'Package'
            else:
                raise ValueError('cannot determine ProblemType from tags: ' + str(b.tags))

        report['Tags'] = ' '.join(b.tags)

        if 'Title' in report:
            report['OriginalTitle'] = report['Title']

        report['Title'] = b.title

        for attachment in filter_filename(b.attachments):
            key, ext = os.path.splitext(attachment.filename)
            # ignore attachments with invalid keys
            try:
                report[key] = ''
            except Exception as e:
                continue
            if ext == '.txt':
                report[key] = attachment.read()
                try:
                    report[key] = report[key].decode('UTF-8')
                except UnicodeDecodeError:
                    pass
            elif ext == '.gz':
                try:
                    report[key] = gzip.GzipFile(fileobj=attachment).read()
                except IOError as e:
                    # some attachments are only called .gz, but are
                    # uncompressed (LP #574360)
                    if 'Not a gzip' not in str(e):
                        raise
                    attachment.seek(0)
                    report[key] = attachment.read()
            else:
                raise Exception('Unknown attachment type: ' + attachment.filename)
        return report

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
        bug = self.launchpad.bugs[id]

        # TODO: raise an error if key_filter is not a list or set
        if key_filter:
            skip_keys = set(report.keys()) - set(key_filter)
        else:
            skip_keys = None

        # we want to reuse the knowledge of write_mime() with all its different input
        # types and output formatting; however, we have to dissect the mime ourselves,
        # since we can't just upload it as a blob
        mime = tempfile.TemporaryFile()
        report.write_mime(mime, skip_keys=skip_keys)
        mime.flush()
        mime.seek(0)
        if _python2:
            msg = email.message_from_file(mime)
        else:
            msg = email.message_from_binary_file(mime)
        msg_iter = msg.walk()

        # first part is the multipart container
        part = _python2 and msg_iter.next() or msg_iter.__next__()
        assert part.is_multipart()

        # second part should be an inline text/plain attachments with all short
        # fields
        part = _python2 and msg_iter.next() or msg_iter.__next__()
        assert not part.is_multipart()
        assert part.get_content_type() == 'text/plain'

        if not key_filter:
            # when we update a complete report, we are updating an existing bug
            # with apport-collect
            x = bug.tags[:]  # LP#254901 workaround
            x.append('apport-collected')
            # add any tags (like the release) to the bug
            if 'Tags' in report:
                x += self._filter_tag_names(report['Tags']).split()
            bug.tags = x
            bug.lp_save()
            bug = self.launchpad.bugs[id]  # fresh bug object, LP#336866 workaround

        # short text data
        text = part.get_payload(decode=True).decode('UTF-8', 'replace')
        # text can be empty if you are only adding an attachment to a bug
        if text:
            if change_description:
                bug.description = bug.description + '\n--- \n' + text
                bug.lp_save()
            else:
                if not comment:
                    comment = bug.title
                bug.newMessage(content=text, subject=comment)

        # other parts are the attachments:
        for part in msg_iter:
            # print '   attachment: %s...' % part.get_filename()
            bug.addAttachment(comment=attachment_comment or '',
                              description=part.get_filename(),
                              content_type=None,
                              data=part.get_payload(decode=True),
                              filename=part.get_filename(), is_patch=False)

        mime.close()

    def update_traces(self, id, report, comment=''):
        '''Update the given report ID for retracing results.

        This updates Stacktrace, ThreadStacktrace, StacktraceTop,
        and StacktraceSource. You can also supply an additional comment.
        '''
        apport.crashdb.CrashDatabase.update_traces(self, id, report, comment)

        bug = self.launchpad.bugs[id]
        # ensure it's assigned to a package
        if 'SourcePackage' in report:
            for task in bug.bug_tasks:
                if task.target.resource_type_link.endswith('#distribution'):
                    task.target = self.lp_distro.getSourcePackage(name=report['SourcePackage'])
                    task.lp_save()
                    bug = self.launchpad.bugs[id]
                    break

        # remove core dump if stack trace is usable
        if report.has_useful_stacktrace():
            for a in bug.attachments:
                if a.title == 'CoreDump.gz':
                    try:
                        a.removeFromBug()
                    except HTTPError:
                        pass  # LP#249950 workaround
            try:
                task = self._get_distro_tasks(bug.bug_tasks)
                if _python2:
                    task = task.next()
                else:
                    task = task.__next__()
                if task.importance == 'Undecided':
                    task.importance = 'Medium'
                    task.lp_save()
            except StopIteration:
                pass  # no distro tasks

            # update bug title with retraced function name
            fn = report.stacktrace_top_function()
            if fn:
                m = re.match(r'^(.*crashed with SIG.* in )([^( ]+)(\(\).*$)', bug.title)
                if m and m.group(2) != fn:
                    bug.title = m.group(1) + fn + m.group(3)
                    try:
                        bug.lp_save()
                    except HTTPError:
                        pass  # LP#336866 workaround
                    bug = self.launchpad.bugs[id]

        self._subscribe_triaging_team(bug, report)

    def get_distro_release(self, id):
        '''Get 'DistroRelease: <release>' from the given report ID and return
        it.'''
        bug = self.launchpad.bugs[id]
        m = re.search('DistroRelease: ([-a-zA-Z0-9.+/ ]+)', bug.description)
        if m:
            return m.group(1)
        raise ValueError('URL does not contain DistroRelease: field')

    def get_affected_packages(self, id):
        '''Return list of affected source packages for given ID.'''

        bug_target_re = re.compile(
            r'/%s/(?:(?P<suite>[^/]+)/)?\+source/(?P<source>[^/]+)$' % self.distro)

        bug = self.launchpad.bugs[id]
        result = []

        for task in bug.bug_tasks:
            match = bug_target_re.search(task.target.self_link)
            if not match:
                continue
            if task.status in ('Invalid', "Won't Fix", 'Fix Released'):
                continue
            result.append(match.group('source'))
        return result

    def is_reporter(self, id):
        '''Check whether the user is the reporter of given ID.'''

        bug = self.launchpad.bugs[id]
        return bug.owner.name == self.launchpad.me.name

    def can_update(self, id):
        '''Check whether the user is eligible to update a report.

        A user should add additional information to an existing ID if (s)he is
        the reporter or subscribed, the bug is open, not a duplicate, etc. The
        exact policy and checks should be done according to the particular
        implementation.
        '''
        bug = self.launchpad.bugs[id]
        if bug.duplicate_of:
            return False

        if bug.owner.name == self.launchpad.me.name:
            return True

        # check subscription
        me = self.launchpad.me.self_link
        for sub in bug.subscriptions.entries:
            if sub['person_link'] == me:
                return True

        return False

    def get_unretraced(self):
        '''Return an ID set of all crashes which have not been retraced yet and
        which happened on the current host architecture.'''
        try:
            bugs = self.lp_distro.searchTasks(tags=self.arch_tag, created_since='2011-08-01')
            return id_set(bugs)
        except Exception as e:
            apport.error('connecting to Launchpad failed: %s', str(e))
            sys.exit(99)  # transient error

    def get_dup_unchecked(self):
        '''Return an ID set of all crashes which have not been checked for
        being a duplicate.

        This is mainly useful for crashes of scripting languages such as
        Python, since they do not need to be retraced. It should not return
        bugs that are covered by get_unretraced().'''

        try:
            bugs = self.lp_distro.searchTasks(tags='need-duplicate-check', created_since='2011-08-01')
            return id_set(bugs)
        except Exception as e:
            apport.error('connecting to Launchpad failed: %s', str(e))
            sys.exit(99)  # transient error

    def get_unfixed(self):
        '''Return an ID set of all crashes which are not yet fixed.

        The list must not contain bugs which were rejected or duplicate.

        This function should make sure that the returned list is correct. If
        there are any errors with connecting to the crash database, it should
        raise an exception (preferably IOError).'''

        bugs = self.lp_distro.searchTasks(tags='apport-crash')
        return id_set(bugs)

    def _get_source_version(self, package):
        '''Return the version of given source package in the latest release of
        given distribution.

        If 'distro' is None, we will look for a launchpad project .
        '''
        sources = self.lp_distro.main_archive.getPublishedSources(
            exact_match=True,
            source_name=package,
            distro_series=self.lp_distro.current_series
        )
        # first element is the latest one
        return sources[0].source_package_version

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
        # do not do version tracking yet; for that, we need to get the current
        # distrorelease and the current package version in that distrorelease
        # (or, of course, proper version tracking in Launchpad itself)

        try:
            b = self.launchpad.bugs[id]
        except KeyError:
            return 'invalid'

        if b.duplicate_of:
            return 'invalid'

        tasks = list(b.bug_tasks)  # just fetch it once

        if self.distro:
            distro_identifier = '(%s)' % self.distro.lower()
            fixed_tasks = list(filter(lambda task: task.status == 'Fix Released' and
                                      distro_identifier in task.bug_target_display_name.lower(), tasks))

            if not fixed_tasks:
                fixed_distro = list(filter(lambda task: task.status == 'Fix Released' and
                                           task.bug_target_name.lower() == self.distro.lower(), tasks))
                if fixed_distro:
                    # fixed in distro inself (without source package)
                    return ''

            if len(fixed_tasks) > 1:
                apport.warning('There is more than one task fixed in %s %s, using first one to determine fixed version', self.distro, id)
                return ''

            if fixed_tasks:
                task = fixed_tasks.pop()
                try:
                    return self._get_source_version(task.bug_target_display_name.split()[0])
                except IndexError:
                    # source does not exist any more
                    return 'invalid'
            else:
                # check if there only invalid ones
                invalid_tasks = list(filter(lambda task: task.status in ('Invalid', "Won't Fix", 'Expired') and
                                            distro_identifier in task.bug_target_display_name.lower(), tasks))
                if invalid_tasks:
                    non_invalid_tasks = list(filter(
                        lambda task: task.status not in ('Invalid', "Won't Fix", 'Expired') and
                        distro_identifier in task.bug_target_display_name.lower(), tasks))
                    if not non_invalid_tasks:
                        return 'invalid'
        else:
            fixed_tasks = list(filter(lambda task: task.status == 'Fix Released', tasks))
            if fixed_tasks:
                # TODO: look for current series
                return ''
            # check if there any invalid ones
            if list(filter(lambda task: task.status == 'Invalid', tasks)):
                return 'invalid'

        return None

    def duplicate_of(self, id):
        '''Return master ID for a duplicate bug.

        If the bug is not a duplicate, return None.
        '''
        b = self.launchpad.bugs[id].duplicate_of
        if b:
            return b.id
        else:
            return None

    def close_duplicate(self, report, id, master_id):
        '''Mark a crash id as duplicate of given master ID.

        If master is None, id gets un-duplicated.
        '''
        bug = self.launchpad.bugs[id]

        if master_id:
            assert id != master_id, 'cannot mark bug %s as a duplicate of itself' % str(id)

            # check whether the master itself is a dup
            master = self.launchpad.bugs[master_id]
            if master.duplicate_of:
                master = master.duplicate_of
                master_id = master.id
                if master.id == id:
                    # this happens if the bug was manually duped to a newer one
                    apport.warning('Bug %i was manually marked as a dupe of newer bug %i, not closing as duplicate',
                                   id, master_id)
                    return

            for a in bug.attachments:
                if a.title in ('CoreDump.gz', 'Stacktrace.txt',
                               'ThreadStacktrace.txt', 'ProcMaps.txt',
                               'ProcStatus.txt', 'Registers.txt',
                               'Disassembly.txt'):
                    try:
                        a.removeFromBug()
                    except HTTPError:
                        pass  # LP#249950 workaround

            bug = self.launchpad.bugs[id]  # fresh bug object, LP#336866 workaround
            bug.newMessage(content='Thank you for taking the time to report this crash and helping \
to make this software better.  This particular crash has already been reported and \
is a duplicate of bug #%i, so is being marked as such.  Please look at the \
other bug report to see if there is any missing information that you can \
provide, or to see if there is a workaround for the bug.  Additionally, any \
further discussion regarding the bug should occur in the other report.  \
Please continue to report any other bugs you may find.' % master_id,
                           subject='This bug is a duplicate')

            bug = self.launchpad.bugs[id]  # refresh, LP#336866 workaround
            if bug.private:
                bug.private = False

            # set duplicate last, since we cannot modify already dup'ed bugs
            if not bug.duplicate_of:
                bug.duplicate_of = master

            # cache tags of master bug report instead of performing multiple
            # queries
            master_tags = master.tags

            if len(master.duplicates) == 10:
                if 'escalation_tag' in self.options and self.options['escalation_tag'] not in master_tags and self.options.get('escalated_tag', ' invalid ') not in master_tags:
                    master.tags = master_tags + [self.options['escalation_tag']]  # LP#254901 workaround
                    master.lp_save()

                if 'escalation_subscription' in self.options and self.options.get('escalated_tag', ' invalid ') not in master_tags:
                    p = self.launchpad.people[self.options['escalation_subscription']]
                    master.subscribe(person=p)

            # requesting updated stack trace?
            if report.has_useful_stacktrace() and ('apport-request-retrace' in master_tags or
                                                   'apport-failed-retrace' in master_tags):
                self.update(master_id, report, 'Updated stack trace from duplicate bug %i' % id,
                            key_filter=['Stacktrace', 'ThreadStacktrace',
                                        'Package', 'Dependencies', 'ProcMaps', 'ProcCmdline'])

                master = self.launchpad.bugs[master_id]
                x = master.tags[:]  # LP#254901 workaround
                try:
                    x.remove('apport-failed-retrace')
                except ValueError:
                    pass
                try:
                    x.remove('apport-request-retrace')
                except ValueError:
                    pass
                master.tags = x
                try:
                    master.lp_save()
                except HTTPError:
                    pass  # LP#336866 workaround

            # white list of tags to copy from duplicates bugs to the master
            tags_to_copy = ['bugpattern-needed']
            for series in self.lp_distro.series:
                if series.status not in ['Active Development',
                                         'Current Stable Release',
                                         'Supported', 'Pre-release Freeze']:
                    continue
                tags_to_copy.append(series.name)
            # copy tags over from the duplicate bug to the master bug
            dupe_tags = set(bug.tags)
            # reload master tags as they may have changed
            master_tags = master.tags
            missing_tags = dupe_tags.difference(master_tags)

            for tag in missing_tags:
                if tag in tags_to_copy:
                    master_tags.append(tag)

            master.tags = master_tags
            master.lp_save()

        else:
            if bug.duplicate_of:
                bug.duplicate_of = None

        if bug._dirty_attributes:  # LP#336866 workaround
            bug.lp_save()

    def mark_regression(self, id, master):
        '''Mark a crash id as reintroducing an earlier crash which is
        already marked as fixed (having ID 'master').'''

        bug = self.launchpad.bugs[id]
        bug.newMessage(content='This crash has the same stack trace characteristics as bug #%i. \
However, the latter was already fixed in an earlier package version than the \
one in this report. This might be a regression or because the problem is \
in a dependent package.' % master,
                       subject='Possible regression detected')
        bug = self.launchpad.bugs[id]  # fresh bug object, LP#336866 workaround
        bug.tags = bug.tags + ['regression-retracer']  # LP#254901 workaround
        bug.lp_save()

    def mark_retraced(self, id):
        '''Mark crash id as retraced.'''

        bug = self.launchpad.bugs[id]
        if self.arch_tag in bug.tags:
            x = bug.tags[:]  # LP#254901 workaround
            x.remove(self.arch_tag)
            bug.tags = x
            try:
                bug.lp_save()
            except HTTPError:
                pass  # LP#336866 workaround

    def mark_retrace_failed(self, id, invalid_msg=None):
        '''Mark crash id as 'failed to retrace'.'''

        bug = self.launchpad.bugs[id]
        if invalid_msg:
            try:
                task = self._get_distro_tasks(bug.bug_tasks)
                if _python2:
                    task = task.next()
                else:
                    task = task.__next__()
            except StopIteration:
                # no distro task, just use the first one
                task = bug.bug_tasks[0]
            task.status = 'Invalid'
            task.lp_save()
            bug.newMessage(content=invalid_msg,
                           subject='Crash report cannot be processed')

            for a in bug.attachments:
                if a.title == 'CoreDump.gz':
                    try:
                        a.removeFromBug()
                    except HTTPError:
                        pass  # LP#249950 workaround
        else:
            if 'apport-failed-retrace' not in bug.tags:
                bug.tags = bug.tags + ['apport-failed-retrace']  # LP#254901 workaround
                bug.lp_save()

    def _mark_dup_checked(self, id, report):
        '''Mark crash id as checked for being a duplicate.'''

        bug = self.launchpad.bugs[id]

        # if we have a distro task without a package, fix it
        if 'SourcePackage' in report:
            for task in bug.bug_tasks:
                if task.target.resource_type_link.endswith('#distribution'):
                    task.target = self.lp_distro.getSourcePackage(
                        name=report['SourcePackage'])
                    try:
                        task.lp_save()
                        bug = self.launchpad.bugs[id]
                    except HTTPError:
                        # might fail if there is already another Ubuntu package task
                        pass
                    break

        if 'need-duplicate-check' in bug.tags:
            x = bug.tags[:]  # LP#254901 workaround
            x.remove('need-duplicate-check')
            bug.tags = x
            bug.lp_save()
            if 'Traceback' in report:
                for task in bug.bug_tasks:
                    if '#distribution' in task.target.resource_type_link:
                        if task.importance == 'Undecided':
                            task.importance = 'Medium'
                            task.lp_save()
        self._subscribe_triaging_team(bug, report)

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
        # we override the method here to check if the user actually has access
        # to the bug, and if the bug requests more retraces; in either case we
        # should file it.
        url = apport.crashdb.CrashDatabase.known(self, report)

        if not url:
            return url

        # record the fact that it is a duplicate, for triagers
        report['DuplicateOf'] = url

        try:
            f = urlopen(url + '/+text')
        except IOError:
            # if we are offline, or LP is down, upload will fail anyway, so we
            # can just as well avoid the upload
            return url

        line = f.readline()
        if not line.startswith(b'bug:'):
            # presumably a 404 etc. page, which happens for private bugs
            return True

        # check tags
        for line in f:
            if line.startswith(b'tags:'):
                if b'apport-failed-retrace' in line or b'apport-request-retrace' in line:
                    return None
                else:
                    break

            # stop at the first task, tags are in the first block
            if not line.strip():
                break

        return url

    def _subscribe_triaging_team(self, bug, report):
        '''Subscribe the right triaging team to the bug.'''

        # FIXME: this entire function is an ugly Ubuntu specific hack until LP
        # gets a real crash db; see https://wiki.ubuntu.com/CrashReporting

        if 'DistroRelease' in report and report['DistroRelease'].split()[0] != 'Ubuntu':
            return  # only Ubuntu bugs are filed private

        # use a url hack here, it is faster
        person = '%s~%s' % (self.launchpad._root_uri,
                            self.options.get('triaging_team', 'ubuntu-crashes-universe'))
        if not person.replace(str(self.launchpad._root_uri), '').strip('~') \
                in [str(sub).split('/')[-1] for sub in bug.subscriptions]:
            bug.subscribe(person=person)

    def _generate_upload_blob(self, report):
        '''Generate a multipart/MIME temporary file for uploading.

        You have to close the returned file object after you are done with it.
        '''
        # set reprocessing tags
        hdr = {}
        hdr['Tags'] = 'apport-%s' % report['ProblemType'].lower()
        a = report.get('PackageArchitecture')
        if not a or a == 'all':
            a = report.get('Architecture')
        if a:
            hdr['Tags'] += ' ' + a
        if 'Tags' in report:
            hdr['Tags'] += ' ' + self._filter_tag_names(report['Tags'])

        # privacy/retracing for distro reports
        # FIXME: ugly hack until LP has a real crash db
        if 'DistroRelease' in report:
            if a and ('VmCore' in report or 'CoreDump' in report or 'LaunchpadPrivate' in report):
                hdr['Private'] = 'yes'
                hdr['Subscribers'] = report.get('LaunchpadSubscribe',
                                                self.options.get('initial_subscriber', 'apport'))
                hdr['Tags'] += ' need-%s-retrace' % a
            elif 'Traceback' in report:
                hdr['Private'] = 'yes'
                hdr['Subscribers'] = 'apport'
                hdr['Tags'] += ' need-duplicate-check'
        if 'DuplicateSignature' in report and 'need-duplicate-check' not in hdr['Tags']:
                hdr['Tags'] += ' need-duplicate-check'

        # if we have checkbox submission key, link it to the bug; keep text
        # reference until the link is shown in Launchpad's UI
        if 'CheckboxSubmission' in report:
            hdr['HWDB-Submission'] = report['CheckboxSubmission']

        # order in which keys should appear in the temporary file
        order = ['ProblemType', 'DistroRelease', 'Package', 'Regression', 'Reproducible',
                 'TestedUpstream', 'ProcVersionSignature', 'Uname', 'NonfreeKernelModules']

        # write MIME/Multipart version into temporary file
        mime = tempfile.TemporaryFile()
        report.write_mime(mime, extra_headers=hdr,
                          skip_keys=['Tags', 'LaunchpadPrivate', 'LaunchpadSubscribe'],
                          priority_fields=order)
        mime.flush()
        mime.seek(0)

        return mime

    @classmethod
    def _filter_tag_names(klass, tags):
        '''Replace characters from tags which are not palatable to Launchpad'''

        res = ''
        for ch in tags.lower().encode('ASCII', errors='ignore'):
            if ch in b'abcdefghijklmnopqrstuvwxyz0123456789 ' or (len(res) > 0 and ch in b'+-.'):
                if _python2:
                    res += ch
                else:
                    res += chr(ch)
            else:
                res += '.'

        return res


#
# Launchpad storeblob API (should go into launchpadlib, see LP #315358)
#

_https_upload_callback = None


#
# This progress code is based on KodakLoader by Jason Hildebrand
# <jason@opensky.ca>. See http://www.opensky.ca/~jdhildeb/software/kodakloader/
# for details.
class HTTPSProgressConnection(HTTPSConnection):
    '''Implement a HTTPSConnection with an optional callback function for
    upload progress.'''

    def send(self, data):
        global _https_upload_callback

        # if callback has not been set, call the old method
        if not _https_upload_callback:
            HTTPSConnection.send(self, data)
            return

        sent = 0
        total = len(data)
        chunksize = 1024
        while sent < total:
            _https_upload_callback(sent, total)
            t1 = time.time()
            HTTPSConnection.send(self, data[sent:(sent + chunksize)])
            sent += chunksize
            t2 = time.time()

            # adjust chunksize so that it takes between .5 and 2
            # seconds to send a chunk
            if chunksize > 1024:
                if t2 - t1 < .5:
                    chunksize <<= 1
                elif t2 - t1 > 2:
                    chunksize >>= 1


class HTTPSProgressHandler(HTTPSHandler):

    def https_open(self, req):
        return self.do_open(HTTPSProgressConnection, req)


def upload_blob(blob, progress_callback=None, hostname='launchpad.net'):
    '''Upload blob (file-like object) to Launchpad.

    progress_callback can be set to a function(sent, total) which is regularly
    called with the number of bytes already sent and total number of bytes to
    send. It is called every 0.5 to 2 seconds (dynamically adapted to upload
    bandwidth).

    Return None on error, or the ticket number on success.

    By default this uses the production Launchpad hostname. Set
    hostname to 'launchpad.dev' or 'staging.launchpad.net' to use another
    instance for testing.
    '''
    ticket = None
    url = 'https://%s/+storeblob' % hostname

    global _https_upload_callback
    _https_upload_callback = progress_callback

    # build the form-data multipart/MIME request
    data = email.mime.multipart.MIMEMultipart()

    submit = email.mime.text.MIMEText('1')
    submit.add_header('Content-Disposition', 'form-data; name="FORM_SUBMIT"')
    data.attach(submit)

    form_blob = email.mime.base.MIMEBase('application', 'octet-stream')
    form_blob.add_header('Content-Disposition', 'form-data; name="field.blob"; filename="x"')
    form_blob.set_payload(blob.read().decode('ascii'))
    data.attach(form_blob)

    data_flat = BytesIO()
    if sys.version_info.major == 2:
        gen = email.generator.Generator(data_flat, mangle_from_=False)
    else:
        gen = email.generator.BytesGenerator(data_flat, mangle_from_=False)
    gen.flatten(data)

    # do the request; we need to explicitly set the content type here, as it
    # defaults to x-www-form-urlencoded
    req = Request(url, data_flat.getvalue())
    req.add_header('Content-Type', 'multipart/form-data; boundary=' + data.get_boundary())
    opener = build_opener(HTTPSProgressHandler)
    result = opener.open(req)
    ticket = result.info().get('X-Launchpad-Blob-Token')

    assert ticket
    return ticket


#
# Unit tests
#

if __name__ == '__main__':
    import unittest, subprocess
    from unittest.mock import patch

    crashdb = None
    _segv_report = None
    _python_report = None
    _uncommon_description_report = None

    class _T(unittest.TestCase):
        # this assumes that a source package 'coreutils' exists and builds a
        # binary package 'coreutils'
        test_package = 'coreutils'
        test_srcpackage = 'coreutils'

        #
        # Generic tests, should work for all CrashDB implementations
        #

        def setUp(self):
            global crashdb
            if not crashdb:
                crashdb = self._get_instance()
            self.crashdb = crashdb

            # create a local reference report so that we can compare
            # DistroRelease, Architecture, etc.
            self.ref_report = apport.Report()
            self.ref_report.add_os_info()
            self.ref_report.add_user_info()
            self.ref_report['SourcePackage'] = 'coreutils'

            # Objects tests rely on.
            self._create_project('langpack-o-matic')

        def _create_project(self, name):
            '''Create a project using launchpadlib to be used by tests.'''

            project = self.crashdb.launchpad.projects[name]
            if not project:
                self.crashdb.launchpad.projects.new_project(
                    description=name + 'description',
                    display_name=name,
                    name=name,
                    summary=name + 'summary',
                    title=name + 'title')

        @property
        def hostname(self):
            '''Get the Launchpad hostname for the given crashdb.'''

            return self.crashdb.get_hostname()

        def get_segv_report(self, force_fresh=False):
            '''Generate SEGV crash report.

            This is only done once, subsequent calls will return the already
            existing ID, unless force_fresh is True.

            Return the ID.
            '''
            global _segv_report
            if not force_fresh and _segv_report is not None:
                return _segv_report

            r = self._generate_sigsegv_report()
            r.add_package_info(self.test_package)
            r.add_os_info()
            r.add_gdb_info()
            r.add_user_info()
            self.assertEqual(r.standard_title(), 'crash crashed with SIGSEGV in f()')

            # add some binary gibberish which isn't UTF-8
            r['ShortGibberish'] = ' "]\xb6"\n'
            r['LongGibberish'] = 'a\nb\nc\nd\ne\n\xff\xff\xff\n\f'

            # create a bug for the report
            bug_target = self._get_bug_target(self.crashdb, r)
            self.assertTrue(bug_target)

            id = self._file_bug(bug_target, r)
            self.assertTrue(id > 0)

            sys.stderr.write('(Created SEGV report: https://%s/bugs/%i) ' % (self.hostname, id))
            if not force_fresh:
                _segv_report = id
            return id

        def get_python_report(self):
            '''Generate Python crash report.

            Return the ID.
            '''
            global _python_report
            if _python_report is not None:
                return _python_report

            r = apport.Report('Crash')
            r['ExecutablePath'] = '/bin/foo'
            r['Traceback'] = '''Traceback (most recent call last):
  File "/bin/foo", line 67, in fuzz
    print(weird)
NameError: global name 'weird' is not defined'''
            r['Tags'] = 'boogus pybogus'
            r.add_package_info(self.test_package)
            r.add_os_info()
            r.add_user_info()
            self.assertEqual(r.standard_title(),
                             "foo crashed with NameError in fuzz(): global name 'weird' is not defined")

            bug_target = self._get_bug_target(self.crashdb, r)
            self.assertTrue(bug_target)

            id = self._file_bug(bug_target, r)
            self.assertTrue(id > 0)
            sys.stderr.write('(Created Python report: https://%s/bugs/%i) ' % (self.hostname, id))
            _python_report = id
            return id

        def get_uncommon_description_report(self, force_fresh=False):
            '''File a bug report with an uncommon description.

            This is only done once, subsequent calls will return the already
            existing ID, unless force_fresh is True.

            Example taken from real LP bug 269539. It contains only
            ProblemType/Architecture/DistroRelease in the description, and has
            free-form description text after the Apport data.

            Return the ID.
            '''
            global _uncommon_description_report
            if not force_fresh and _uncommon_description_report is not None:
                return _uncommon_description_report

            desc = '''problem

ProblemType: Package
Architecture: amd64
DistroRelease: Ubuntu 8.10

more text

and more
'''
            bug = self.crashdb.launchpad.bugs.createBug(
                title='mixed description bug',
                description=desc,
                target=self.crashdb.lp_distro)
            sys.stderr.write('(Created uncommon description: https://%s/bugs/%i) ' % (self.hostname, bug.id))

            if not force_fresh:
                _uncommon_description_report = bug.id
            return bug.id

        def test_1_download(self):
            '''download()'''

            r = self.crashdb.download(self.get_segv_report())
            self.assertEqual(r['ProblemType'], 'Crash')
            self.assertEqual(r['Title'], 'crash crashed with SIGSEGV in f()')
            self.assertEqual(r['DistroRelease'], self.ref_report['DistroRelease'])
            self.assertEqual(r['Architecture'], self.ref_report['Architecture'])
            self.assertEqual(r['Uname'], self.ref_report['Uname'])
            self.assertEqual(r.get('NonfreeKernelModules'),
                             self.ref_report.get('NonfreeKernelModules'))
            self.assertEqual(r.get('UserGroups'), self.ref_report.get('UserGroups'))
            tags = set(r['Tags'].split())
            self.assertEqual(tags, set([self.crashdb.arch_tag, 'apport-crash',
                                        apport.packaging.get_system_architecture()]))

            self.assertEqual(r['Signal'], '11')
            self.assertTrue(r['ExecutablePath'].endswith('/crash'))
            self.assertEqual(r['SourcePackage'], self.test_srcpackage)
            self.assertTrue(r['Package'].startswith(self.test_package + ' '))
            self.assertIn('f (x=42)', r['Stacktrace'])
            self.assertIn('f (x=42)', r['StacktraceTop'])
            self.assertIn('f (x=42)', r['ThreadStacktrace'])
            self.assertGreater(len(r['CoreDump']), 1000)
            self.assertIn('Dependencies', r)
            self.assertIn('Disassembly', r)
            self.assertIn('Registers', r)

            # check tags
            r = self.crashdb.download(self.get_python_report())
            tags = set(r['Tags'].split())
            self.assertEqual(tags, set(['apport-crash', 'boogus', 'pybogus',
                                        'need-duplicate-check', apport.packaging.get_system_architecture()]))

        def test_2_update_traces(self):
            '''update_traces()'''

            r = self.crashdb.download(self.get_segv_report())
            self.assertIn('CoreDump', r)
            self.assertIn('Dependencies', r)
            self.assertIn('Disassembly', r)
            self.assertIn('Registers', r)
            self.assertIn('Stacktrace', r)
            self.assertIn('ThreadStacktrace', r)
            self.assertEqual(r['Title'], 'crash crashed with SIGSEGV in f()')

            # updating with a useless stack trace retains core dump
            r['StacktraceTop'] = '?? ()'
            r['Stacktrace'] = 'long\ntrace'
            r['ThreadStacktrace'] = 'thread\neven longer\ntrace'
            r['FooBar'] = 'bogus'
            self.crashdb.update_traces(self.get_segv_report(), r, 'I can has a better retrace?')
            r = self.crashdb.download(self.get_segv_report())
            self.assertIn('CoreDump', r)
            self.assertIn('Dependencies', r)
            self.assertIn('Disassembly', r)
            self.assertIn('Registers', r)
            self.assertIn('Stacktrace', r)  # TODO: ascertain that it's the updated one
            self.assertIn('ThreadStacktrace', r)
            self.assertNotIn('FooBar', r)
            self.assertEqual(r['Title'], 'crash crashed with SIGSEGV in f()')

            tags = self.crashdb.launchpad.bugs[self.get_segv_report()].tags
            self.assertIn('apport-crash', tags)
            self.assertNotIn('apport-collected', tags)

            # updating with a useful stack trace removes core dump
            r['StacktraceTop'] = 'read () from /lib/libc.6.so\nfoo (i=1) from /usr/lib/libfoo.so'
            r['Stacktrace'] = 'long\ntrace'
            r['ThreadStacktrace'] = 'thread\neven longer\ntrace'
            self.crashdb.update_traces(self.get_segv_report(), r, 'good retrace!')
            r = self.crashdb.download(self.get_segv_report())
            self.assertNotIn('CoreDump', r)
            self.assertIn('Dependencies', r)
            self.assertIn('Disassembly', r)
            self.assertIn('Registers', r)
            self.assertIn('Stacktrace', r)
            self.assertIn('ThreadStacktrace', r)
            self.assertNotIn('FooBar', r)

            # as previous title had standard form, the top function gets
            # updated
            self.assertEqual(r['Title'], 'crash crashed with SIGSEGV in read()')

            # respects title amendments
            bug = self.crashdb.launchpad.bugs[self.get_segv_report()]
            bug.title = 'crash crashed with SIGSEGV in f() on exit'
            try:
                bug.lp_save()
            except HTTPError:
                pass  # LP#336866 workaround
            r['StacktraceTop'] = 'read () from /lib/libc.6.so\nfoo (i=1) from /usr/lib/libfoo.so'
            self.crashdb.update_traces(self.get_segv_report(), r, 'good retrace with title amendment')
            r = self.crashdb.download(self.get_segv_report())
            self.assertEqual(r['Title'], 'crash crashed with SIGSEGV in read() on exit')

            # does not destroy custom titles
            bug = self.crashdb.launchpad.bugs[self.get_segv_report()]
            bug.title = 'crash is crashy'
            try:
                bug.lp_save()
            except HTTPError:
                pass  # LP#336866 workaround

            r['StacktraceTop'] = 'read () from /lib/libc.6.so\nfoo (i=1) from /usr/lib/libfoo.so'
            self.crashdb.update_traces(self.get_segv_report(), r, 'good retrace with custom title')
            r = self.crashdb.download(self.get_segv_report())
            self.assertEqual(r['Title'], 'crash is crashy')

            # test various situations which caused crashes
            r['Stacktrace'] = ''  # empty file
            r['ThreadStacktrace'] = '"]\xb6"\n'  # not interpretable as UTF-8, LP #353805
            r['StacktraceSource'] = 'a\nb\nc\nd\ne\n\xff\xff\xff\n\f'
            self.crashdb.update_traces(self.get_segv_report(), r, 'tests')

        def test_get_comment_url(self):
            '''get_comment_url() for non-ASCII titles'''

            # UTF-8 bytestring, works in both python 2.7 and 3
            title = b'1\xc3\xa4\xe2\x99\xa52'

            # distro, UTF-8 bytestring
            r = apport.Report('Bug')
            r['Title'] = title
            url = self.crashdb.get_comment_url(r, 42)
            self.assertTrue(url.endswith('/ubuntu/+filebug/42?field.title=1%C3%A4%E2%99%A52'))

            # distro, unicode
            r['Title'] = title.decode('UTF-8')
            url = self.crashdb.get_comment_url(r, 42)
            self.assertTrue(url.endswith('/ubuntu/+filebug/42?field.title=1%C3%A4%E2%99%A52'))

            # package, unicode
            r['SourcePackage'] = 'coreutils'
            url = self.crashdb.get_comment_url(r, 42)
            self.assertTrue(url.endswith('/ubuntu/+source/coreutils/+filebug/42?field.title=1%C3%A4%E2%99%A52'))

        def test_update_description(self):
            '''update() with changing description'''

            bug_target = self.crashdb.lp_distro.getSourcePackage(name='bash')
            bug = self.crashdb.launchpad.bugs.createBug(
                description='test description for test bug.',
                target=bug_target,
                title='testbug')
            id = bug.id
            self.assertTrue(id > 0)
            sys.stderr.write('(https://%s/bugs/%i) ' % (self.hostname, id))

            r = apport.Report('Bug')

            r['OneLiner'] = b'bogus\xe2\x86\x92'.decode('UTF-8')
            r['StacktraceTop'] = 'f()\ng()\nh(1)'
            r['ShortGoo'] = 'lineone\nlinetwo'
            r['DpkgTerminalLog'] = 'one\ntwo\nthree\nfour\nfive\nsix'
            r['VarLogDistupgradeBinGoo'] = b'\x01' * 1024

            self.crashdb.update(id, r, 'NotMe', change_description=True)

            r = self.crashdb.download(id)

            self.assertEqual(r['OneLiner'], b'bogus\xe2\x86\x92'.decode('UTF-8'))
            self.assertEqual(r['ShortGoo'], 'lineone\nlinetwo')
            self.assertEqual(r['DpkgTerminalLog'], 'one\ntwo\nthree\nfour\nfive\nsix')
            self.assertEqual(r['VarLogDistupgradeBinGoo'], b'\x01' * 1024)

            self.assertEqual(self.crashdb.launchpad.bugs[id].tags,
                             ['apport-collected'])

        def test_update_comment(self):
            '''update() with appending comment'''

            bug_target = self.crashdb.lp_distro.getSourcePackage(name='bash')
            # we need to fake an apport description separator here, since we
            # want to be lazy and use download() for checking the result
            bug = self.crashdb.launchpad.bugs.createBug(
                description='Pr0blem\n\n--- \nProblemType: Bug',
                target=bug_target,
                title='testbug')
            id = bug.id
            self.assertTrue(id > 0)
            sys.stderr.write('(https://%s/bugs/%i) ' % (self.hostname, id))

            r = apport.Report('Bug')

            r['OneLiner'] = 'bogus→'
            r['StacktraceTop'] = 'f()\ng()\nh(1)'
            r['ShortGoo'] = 'lineone\nlinetwo'
            r['DpkgTerminalLog'] = 'one\ntwo\nthree\nfour\nfive\nsix'
            r['VarLogDistupgradeBinGoo'] = '\x01' * 1024

            self.crashdb.update(id, r, 'meow', change_description=False)

            r = self.crashdb.download(id)

            self.assertNotIn('OneLiner', r)
            self.assertNotIn('ShortGoo', r)
            self.assertEqual(r['ProblemType'], 'Bug')
            self.assertEqual(r['DpkgTerminalLog'], 'one\ntwo\nthree\nfour\nfive\nsix')
            self.assertEqual(r['VarLogDistupgradeBinGoo'], '\x01' * 1024)

            self.assertEqual(self.crashdb.launchpad.bugs[id].tags,
                             ['apport-collected'])

        def test_update_filter(self):
            '''update() with a key filter'''

            bug_target = self.crashdb.lp_distro.getSourcePackage(name='bash')
            bug = self.crashdb.launchpad.bugs.createBug(
                description='test description for test bug',
                target=bug_target,
                title='testbug')
            id = bug.id
            self.assertTrue(id > 0)
            sys.stderr.write('(https://%s/bugs/%i) ' % (self.hostname, id))

            r = apport.Report('Bug')

            r['OneLiner'] = 'bogus→'
            r['StacktraceTop'] = 'f()\ng()\nh(1)'
            r['ShortGoo'] = 'lineone\nlinetwo'
            r['DpkgTerminalLog'] = 'one\ntwo\nthree\nfour\nfive\nsix'
            r['VarLogDistupgradeBinGoo'] = '\x01' * 1024

            self.crashdb.update(id, r, 'NotMe', change_description=True,
                                key_filter=['ProblemType', 'ShortGoo', 'DpkgTerminalLog'])

            r = self.crashdb.download(id)

            self.assertNotIn('OneLiner', r)
            self.assertEqual(r['ShortGoo'], 'lineone\nlinetwo')
            self.assertEqual(r['ProblemType'], 'Bug')
            self.assertEqual(r['DpkgTerminalLog'], 'one\ntwo\nthree\nfour\nfive\nsix')
            self.assertNotIn('VarLogDistupgradeBinGoo', r)

            self.assertEqual(self.crashdb.launchpad.bugs[id].tags, [])

        def test_get_distro_release(self):
            '''get_distro_release()'''

            self.assertEqual(self.crashdb.get_distro_release(self.get_segv_report()),
                             self.ref_report['DistroRelease'])

        def test_get_affected_packages(self):
            '''get_affected_packages()'''

            self.assertEqual(self.crashdb.get_affected_packages(self.get_segv_report()),
                             [self.ref_report['SourcePackage']])

        def test_is_reporter(self):
            '''is_reporter()'''

            self.assertTrue(self.crashdb.is_reporter(self.get_segv_report()))
            self.assertFalse(self.crashdb.is_reporter(1))

        def test_can_update(self):
            '''can_update()'''

            self.assertTrue(self.crashdb.can_update(self.get_segv_report()))
            self.assertFalse(self.crashdb.can_update(1))

        def test_duplicates(self):
            '''duplicate handling'''

            # initially we have no dups
            self.assertEqual(self.crashdb.duplicate_of(self.get_segv_report()), None)
            self.assertEqual(self.crashdb.get_fixed_version(self.get_segv_report()), None)

            segv_id = self.get_segv_report()
            known_test_id = self.get_uncommon_description_report()
            known_test_id2 = self.get_uncommon_description_report(force_fresh=True)

            # dupe our segv_report and check that it worked; then undupe it
            r = self.crashdb.download(segv_id)
            self.crashdb.close_duplicate(r, segv_id, known_test_id)
            self.assertEqual(self.crashdb.duplicate_of(segv_id), known_test_id)

            # this should be a no-op
            self.crashdb.close_duplicate(r, segv_id, known_test_id)
            self.assertEqual(self.crashdb.duplicate_of(segv_id), known_test_id)

            self.assertEqual(self.crashdb.get_fixed_version(segv_id), 'invalid')
            self.crashdb.close_duplicate(r, segv_id, None)
            self.assertEqual(self.crashdb.duplicate_of(segv_id), None)
            self.assertEqual(self.crashdb.get_fixed_version(segv_id), None)

            # this should have removed attachments; note that Stacktrace is
            # short, and thus inline
            r = self.crashdb.download(self.get_segv_report())
            self.assertNotIn('CoreDump', r)
            self.assertNotIn('Disassembly', r)
            self.assertNotIn('ProcMaps', r)
            self.assertNotIn('ProcStatus', r)
            self.assertNotIn('Registers', r)
            self.assertNotIn('ThreadStacktrace', r)

            # now try duplicating to a duplicate bug; this should automatically
            # transition to the master bug
            self.crashdb.close_duplicate(apport.Report(), known_test_id,
                                         known_test_id2)
            self.crashdb.close_duplicate(r, segv_id, known_test_id)
            self.assertEqual(self.crashdb.duplicate_of(segv_id),
                             known_test_id2)

            self.crashdb.close_duplicate(apport.Report(), known_test_id, None)
            self.crashdb.close_duplicate(apport.Report(), known_test_id2, None)
            self.crashdb.close_duplicate(r, segv_id, None)

            # this should be a no-op
            self.crashdb.close_duplicate(apport.Report(), known_test_id, None)
            self.assertEqual(self.crashdb.duplicate_of(known_test_id), None)

            self.crashdb.mark_regression(segv_id, known_test_id)
            self._verify_marked_regression(segv_id)

        def test_marking_segv(self):
            '''processing status markings for signal crashes'''

            # mark_retraced()
            unretraced_before = self.crashdb.get_unretraced()
            self.assertIn(self.get_segv_report(), unretraced_before)
            self.assertNotIn(self.get_python_report(), unretraced_before)
            self.crashdb.mark_retraced(self.get_segv_report())
            unretraced_after = self.crashdb.get_unretraced()
            self.assertNotIn(self.get_segv_report(), unretraced_after)
            self.assertEqual(unretraced_before,
                             unretraced_after.union(set([self.get_segv_report()])))
            self.assertEqual(self.crashdb.get_fixed_version(self.get_segv_report()), None)

            # mark_retrace_failed()
            self._mark_needs_retrace(self.get_segv_report())
            self.crashdb.mark_retraced(self.get_segv_report())
            self.crashdb.mark_retrace_failed(self.get_segv_report())
            unretraced_after = self.crashdb.get_unretraced()
            self.assertNotIn(self.get_segv_report(), unretraced_after)
            self.assertEqual(unretraced_before,
                             unretraced_after.union(set([self.get_segv_report()])))
            self.assertEqual(self.crashdb.get_fixed_version(self.get_segv_report()), None)

            # mark_retrace_failed() of invalid bug
            self._mark_needs_retrace(self.get_segv_report())
            self.crashdb.mark_retraced(self.get_segv_report())
            self.crashdb.mark_retrace_failed(self.get_segv_report(), "I don't like you")
            unretraced_after = self.crashdb.get_unretraced()
            self.assertNotIn(self.get_segv_report(), unretraced_after)
            self.assertEqual(unretraced_before,
                             unretraced_after.union(set([self.get_segv_report()])))
            self.assertEqual(self.crashdb.get_fixed_version(self.get_segv_report()),
                             'invalid')

        def test_marking_project(self):
            '''processing status markings for a project CrashDB'''

            # create a distro bug
            distro_bug = self.crashdb.launchpad.bugs.createBug(
                description='foo',
                tags=self.crashdb.arch_tag,
                target=self.crashdb.lp_distro,
                title='ubuntu distro retrace bug')
            # print('distro bug: https://staging.launchpad.net/bugs/%i' % distro_bug.id)

            # create a project crash DB and a bug
            launchpad_instance = os.environ.get('APPORT_LAUNCHPAD_INSTANCE') or 'staging'

            project_db = CrashDatabase(
                os.environ.get('LP_CREDENTIALS'),
                {'project': 'langpack-o-matic', 'launchpad_instance': launchpad_instance})
            project_bug = project_db.launchpad.bugs.createBug(
                description='bar',
                tags=project_db.arch_tag,
                target=project_db.lp_distro,
                title='project retrace bug')
            # print('project bug: https://staging.launchpad.net/bugs/%i' % project_bug.id)

            # on project_db, we recognize the project bug and can mark it
            unretraced_before = project_db.get_unretraced()
            self.assertIn(project_bug.id, unretraced_before)
            self.assertNotIn(distro_bug.id, unretraced_before)
            project_db.mark_retraced(project_bug.id)
            unretraced_after = project_db.get_unretraced()
            self.assertNotIn(project_bug.id, unretraced_after)
            self.assertEqual(unretraced_before,
                             unretraced_after.union(set([project_bug.id])))
            self.assertEqual(self.crashdb.get_fixed_version(project_bug.id), None)

        def test_marking_foreign_arch(self):
            '''processing status markings for a project CrashDB'''

            # create a DB for fake arch
            launchpad_instance = os.environ.get('APPORT_LAUNCHPAD_INSTANCE') or 'staging'
            fakearch_db = CrashDatabase(
                os.environ.get('LP_CREDENTIALS'),
                {'distro': 'ubuntu', 'launchpad_instance': launchpad_instance,
                 'architecture': 'fakearch'})

            fakearch_unretraced_before = fakearch_db.get_unretraced()
            systemarch_unretraced_before = self.crashdb.get_unretraced()

            # create a bug with a fake architecture
            bug = self.crashdb.launchpad.bugs.createBug(
                description='foo',
                tags=['need-fakearch-retrace'],
                target=self.crashdb.lp_distro,
                title='ubuntu distro retrace bug for fakearch')
            print('fake arch bug: https://staging.launchpad.net/bugs/%i' % bug.id)

            fakearch_unretraced_after = fakearch_db.get_unretraced()
            systemarch_unretraced_after = self.crashdb.get_unretraced()

            self.assertEqual(systemarch_unretraced_before, systemarch_unretraced_after)
            self.assertEqual(fakearch_unretraced_after,
                             fakearch_unretraced_before.union(set([bug.id])))

        def test_marking_python(self):
            '''processing status markings for interpreter crashes'''

            unchecked_before = self.crashdb.get_dup_unchecked()
            self.assertIn(self.get_python_report(), unchecked_before)
            self.assertNotIn(self.get_segv_report(), unchecked_before)
            self.crashdb._mark_dup_checked(self.get_python_report(), self.ref_report)
            unchecked_after = self.crashdb.get_dup_unchecked()
            self.assertNotIn(self.get_python_report(), unchecked_after)
            self.assertEqual(unchecked_before,
                             unchecked_after.union(set([self.get_python_report()])))
            self.assertEqual(self.crashdb.get_fixed_version(self.get_python_report()), None)

        def test_update_traces_invalid(self):
            '''updating an invalid crash

            This simulates a race condition where a crash being processed gets
            invalidated by marking it as a duplicate.
            '''
            id = self.get_segv_report(force_fresh=True)

            r = self.crashdb.download(id)

            self.crashdb.close_duplicate(r, id, self.get_segv_report())

            # updating with a useful stack trace removes core dump
            r['StacktraceTop'] = 'read () from /lib/libc.6.so\nfoo (i=1) from /usr/lib/libfoo.so'
            r['Stacktrace'] = 'long\ntrace'
            r['ThreadStacktrace'] = 'thread\neven longer\ntrace'
            self.crashdb.update_traces(id, r, 'good retrace!')

            r = self.crashdb.download(id)
            self.assertNotIn('CoreDump', r)

        @patch.object(CrashDatabase, '_get_source_version')
        def test_get_fixed_version(self, *args):
            '''get_fixed_version() for fixed bugs

            Other cases are already checked in test_marking_segv() (invalid
            bugs) and test_duplicates (duplicate bugs) for efficiency.
            '''
            # staging.launchpad.net often does not have Quantal, so mock-patch
            # it to a known value
            CrashDatabase._get_source_version.return_value = '3.14'
            self._mark_report_fixed(self.get_segv_report())
            fixed_ver = self.crashdb.get_fixed_version(self.get_segv_report())
            self.assertEqual(fixed_ver, '3.14')
            self._mark_report_new(self.get_segv_report())
            self.assertEqual(self.crashdb.get_fixed_version(self.get_segv_report()), None)

        #
        # Launchpad specific implementation and tests
        #

        @classmethod
        def _get_instance(klass):
            '''Create a CrashDB instance'''

            launchpad_instance = os.environ.get('APPORT_LAUNCHPAD_INSTANCE') or 'staging'

            return CrashDatabase(os.environ.get('LP_CREDENTIALS'),
                                 {'distro': 'ubuntu',
                                  'launchpad_instance': launchpad_instance})

        def _get_bug_target(self, db, report):
            '''Return the bug_target for this report.'''

            project = db.options.get('project')
            if 'SourcePackage' in report:
                return db.lp_distro.getSourcePackage(name=report['SourcePackage'])
            elif project:
                return db.launchpad.projects[project]
            else:
                return self.lp_distro

        def _file_bug(self, bug_target, report, description=None):
            '''File a bug report for a report.

            Return the bug ID.
            '''
            # unfortunately staging's +storeblob API hardly ever works, so we
            # must avoid using it. Fake it by manually doing the comments and
            # attachments that +filebug would ordinarily do itself when given a
            # blob handle.

            if description is None:
                description = 'some description'

            mime = self.crashdb._generate_upload_blob(report)
            if _python2:
                msg = email.message_from_file(mime)
            else:
                msg = email.message_from_binary_file(mime)
            mime.close()
            msg_iter = msg.walk()

            # first one is the multipart container
            header = _python2 and msg_iter.next() or msg_iter.__next__()
            assert header.is_multipart()

            # second part should be an inline text/plain attachments with all short
            # fields
            part = _python2 and msg_iter.next() or msg_iter.__next__()
            assert not part.is_multipart()
            assert part.get_content_type() == 'text/plain'
            description += '\n\n' + part.get_payload(decode=True).decode('UTF-8', 'replace')

            # create the bug from header and description data
            bug = self.crashdb.launchpad.bugs.createBug(
                description=description,
                # temporarily disabled to work around SSLHandshakeError on
                # private attachments
                # private=(header['Private'] == 'yes'),
                tags=header['Tags'].split(),
                target=bug_target,
                title=report.get('Title', report.standard_title()))

            # nwo add the attachments
            for part in msg_iter:
                assert not part.is_multipart()
                bug.addAttachment(comment='',
                                  description=part.get_filename(),
                                  content_type=None,
                                  data=part.get_payload(decode=True),
                                  filename=part.get_filename(), is_patch=False)

            for subscriber in header['Subscribers'].split():
                sub = self.crashdb.launchpad.people[subscriber]
                if sub:
                    bug.subscribe(person=sub)

            return bug.id

        def _mark_needs_retrace(self, id):
            '''Mark a report ID as needing retrace.'''

            bug = self.crashdb.launchpad.bugs[id]
            if self.crashdb.arch_tag not in bug.tags:
                bug.tags = bug.tags + [self.crashdb.arch_tag]
                bug.lp_save()

        def _mark_needs_dupcheck(self, id):
            '''Mark a report ID as needing duplicate check.'''

            bug = self.crashdb.launchpad.bugs[id]
            if 'need-duplicate-check' not in bug.tags:
                bug.tags = bug.tags + ['need-duplicate-check']
                bug.lp_save()

        def _mark_report_fixed(self, id):
            '''Close a report ID as "fixed".'''

            bug = self.crashdb.launchpad.bugs[id]
            tasks = list(bug.bug_tasks)
            assert len(tasks) == 1
            t = tasks[0]
            t.status = 'Fix Released'
            t.lp_save()

        def _mark_report_new(self, id):
            '''Reopen a report ID as "new".'''

            bug = self.crashdb.launchpad.bugs[id]
            tasks = list(bug.bug_tasks)
            assert len(tasks) == 1
            t = tasks[0]
            t.status = 'New'
            t.lp_save()

        def _verify_marked_regression(self, id):
            '''Verify that report ID is marked as regression.'''

            bug = self.crashdb.launchpad.bugs[id]
            self.assertIn('regression-retracer', bug.tags)

        def test_project(self):
            '''reporting crashes against a project instead of a distro'''

            launchpad_instance = os.environ.get('APPORT_LAUNCHPAD_INSTANCE') or 'staging'
            # crash database for langpack-o-matic project (this does not have
            # packages in any distro)
            crashdb = CrashDatabase(os.environ.get('LP_CREDENTIALS'),
                                    {'project': 'langpack-o-matic',
                                     'launchpad_instance': launchpad_instance})
            self.assertEqual(crashdb.distro, None)

            # create Python crash report
            r = apport.Report('Crash')
            r['ExecutablePath'] = '/bin/foo'
            r['Traceback'] = '''Traceback (most recent call last):
  File "/bin/foo", line 67, in fuzz
    print(weird)
NameError: global name 'weird' is not defined'''
            r.add_os_info()
            r.add_user_info()
            self.assertEqual(r.standard_title(),
                             "foo crashed with NameError in fuzz(): global name 'weird' is not defined")

            # file it
            bug_target = self._get_bug_target(crashdb, r)
            self.assertEqual(bug_target.name, 'langpack-o-matic')

            id = self._file_bug(bug_target, r)
            self.assertTrue(id > 0)
            sys.stderr.write('(https://%s/bugs/%i) ' % (self.hostname, id))

            # update
            r = crashdb.download(id)
            r['StacktraceTop'] = 'read () from /lib/libc.6.so\nfoo (i=1) from /usr/lib/libfoo.so'
            r['Stacktrace'] = 'long\ntrace'
            r['ThreadStacktrace'] = 'thread\neven longer\ntrace'
            crashdb.update_traces(id, r, 'good retrace!')
            r = crashdb.download(id)

            # test fixed version
            self.assertEqual(crashdb.get_fixed_version(id), None)
            crashdb.close_duplicate(r, id, self.get_uncommon_description_report())
            self.assertEqual(crashdb.duplicate_of(id), self.get_uncommon_description_report())
            self.assertEqual(crashdb.get_fixed_version(id), 'invalid')
            crashdb.close_duplicate(r, id, None)
            self.assertEqual(crashdb.duplicate_of(id), None)
            self.assertEqual(crashdb.get_fixed_version(id), None)

        def test_download_robustness(self):
            '''download() of uncommon description formats'''

            # only ProblemType/Architecture/DistroRelease in description
            r = self.crashdb.download(self.get_uncommon_description_report())
            self.assertEqual(r['ProblemType'], 'Package')
            self.assertEqual(r['Architecture'], 'amd64')
            self.assertTrue(r['DistroRelease'].startswith('Ubuntu '))

        def test_escalation(self):
            '''Escalating bugs with more than 10 duplicates'''

            launchpad_instance = os.environ.get('APPORT_LAUNCHPAD_INSTANCE') or 'staging'
            db = CrashDatabase(os.environ.get('LP_CREDENTIALS'),
                               {'distro': 'ubuntu',
                                'launchpad_instance': launchpad_instance,
                                'escalation_tag': 'omgkittens',
                                'escalation_subscription': 'apport-hackers'})

            count = 0
            p = db.launchpad.people[db.options['escalation_subscription']].self_link
            # needs to have 13 consecutive valid bugs without dupes
            first_dup = 10070
            try:
                for b in range(first_dup, first_dup + 13):
                    count += 1
                    sys.stderr.write('%i ' % b)
                    db.close_duplicate(apport.Report(), b, self.get_segv_report())
                    b = db.launchpad.bugs[self.get_segv_report()]
                    has_escalation_tag = db.options['escalation_tag'] in b.tags
                    has_escalation_subscription = any([s.person_link == p for s in b.subscriptions])
                    if count <= 10:
                        self.assertFalse(has_escalation_tag)
                        self.assertFalse(has_escalation_subscription)
                    else:
                        self.assertTrue(has_escalation_tag)
                        self.assertTrue(has_escalation_subscription)
            finally:
                for b in range(first_dup, first_dup + count):
                    sys.stderr.write('R%i ' % b)
                    db.close_duplicate(apport.Report(), b, None)
            sys.stderr.write('\n')

        def test_marking_python_task_mangle(self):
            '''source package task fixup for marking interpreter crashes'''

            self._mark_needs_dupcheck(self.get_python_report())
            unchecked_before = self.crashdb.get_dup_unchecked()
            self.assertIn(self.get_python_report(), unchecked_before)

            # add an upstream task, and remove the package name from the
            # package task; _mark_dup_checked is supposed to restore the
            # package name
            b = self.crashdb.launchpad.bugs[self.get_python_report()]
            if b.private:
                b.private = False
                b.lp_save()
            t = b.bug_tasks[0]
            t.target = self.crashdb.launchpad.distributions['ubuntu']
            t.lp_save()
            b.addTask(target=self.crashdb.launchpad.projects['coreutils'])

            r = self.crashdb.download(self.get_python_report())
            self.crashdb._mark_dup_checked(self.get_python_report(), r)

            unchecked_after = self.crashdb.get_dup_unchecked()
            self.assertNotIn(self.get_python_report(), unchecked_after)
            self.assertEqual(unchecked_before,
                             unchecked_after.union(set([self.get_python_report()])))

            # upstream task should be unmodified
            b = self.crashdb.launchpad.bugs[self.get_python_report()]
            self.assertEqual(b.bug_tasks[0].bug_target_name, 'coreutils')
            self.assertEqual(b.bug_tasks[0].status, 'New')
            self.assertEqual(b.bug_tasks[0].importance, 'Undecided')

            # package-less distro task should have package name fixed
            self.assertEqual(b.bug_tasks[1].bug_target_name, 'coreutils (Ubuntu)')
            self.assertEqual(b.bug_tasks[1].status, 'New')
            self.assertEqual(b.bug_tasks[1].importance, 'Medium')

            # should not confuse get_fixed_version()
            self.assertEqual(self.crashdb.get_fixed_version(self.get_python_report()), None)

        @classmethod
        def _generate_sigsegv_report(klass, signal='11'):
            '''Create a test executable which will die with a SIGSEGV, generate a
            core dump for it, create a problem report with those two arguments
            (ExecutablePath and CoreDump) and call add_gdb_info().

            Return the apport.report.Report.
            '''
            workdir = None
            orig_cwd = os.getcwd()
            pr = apport.report.Report()
            try:
                workdir = tempfile.mkdtemp()
                atexit.register(shutil.rmtree, workdir)
                os.chdir(workdir)

                # create a test executable
                with open('crash.c', 'w') as fd:
                    fd.write('''
int f(x) {
    int* p = 0; *p = x;
    return x+1;
}
int main() { return f(42); }
''')
                assert subprocess.call(['gcc', '-g', 'crash.c', '-o', 'crash']) == 0
                assert os.path.exists('crash')

                # call it through gdb and dump core
                subprocess.call(['gdb', '--batch', '--ex', 'run', '--ex',
                                 'generate-core-file core', './crash'], stdout=subprocess.PIPE)
                assert os.path.exists('core')
                subprocess.check_call(['sync'])
                assert subprocess.call(['readelf', '-n', 'core'],
                                       stdout=subprocess.PIPE) == 0

                pr['ExecutablePath'] = os.path.join(workdir, 'crash')
                pr['CoreDump'] = (os.path.join(workdir, 'core'),)
                pr['Signal'] = signal

                pr.add_gdb_info()
            finally:
                os.chdir(orig_cwd)

            return pr

    unittest.main()
