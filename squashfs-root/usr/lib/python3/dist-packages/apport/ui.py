'''Abstract Apport user interface.

This encapsulates the workflow and common code for any user interface
implementation (like GTK, Qt, or CLI).
'''

# Copyright (C) 2007 - 2011 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import glob, sys, os.path, optparse, traceback, locale, gettext, re
import errno, zlib
import subprocess, threading, webbrowser
import signal
import time
import ast

import apport, apport.fileutils, apport.REThread

import apport.crashdb
from apport import unicode_gettext as _

if sys.version_info.major == 2:
    from ConfigParser import ConfigParser
    ConfigParser  # pyflakes
    PY3 = False
else:
    from configparser import ConfigParser
    PY3 = True

__version__ = '2.20.9'


def excstr(exception):
    '''Return exception message as unicode.'''

    if sys.version_info.major == 2:
        return str(exception).decode(locale.getpreferredencoding(), 'replace')
    return str(exception)


symptom_script_dir = os.environ.get('APPORT_SYMPTOMS_DIR',
                                    '/usr/share/apport/symptoms')
PF_KTHREAD = 0x200000


def get_pid(report):
    try:
        pid = re.search('Pid:\t(.*)\n', report.get('ProcStatus', '')).group(1)
        return int(pid)
    except (IndexError, AttributeError):
        return None


def still_running(pid):
    try:
        os.kill(int(pid), 0)
    except OSError as e:
        if e.errno == errno.ESRCH:
            return False
    return True


def find_snap(package):
    import requests_unixsocket

    session = requests_unixsocket.Session()
    try:
        r = session.get('http+unix://%2Frun%2Fsnapd.socket/v2/snaps/{}'.format(package))
        if r.status_code == 200:
            j = r.json()
            return j["result"]
    except Exception:
        return None


def thread_collect_info(report, reportfile, package, ui, symptom_script=None,
                        ignore_uninstalled=False):
    '''Collect information about report.

    Encapsulate calls to add_*_info() and update given report, so that this
    function is suitable for threading.

    ui must be a HookUI instance, it gets passed to add_hooks_info().

    If reportfile is not None, the file is written back with the new data.

    If symptom_script is given, it will be run first (for run_symptom()).
    '''
    try:
        report.add_gdb_info()
    except OSError:
        # it's okay if gdb is not installed on the client side; we'll get stack
        # traces on retracing.
        pass
    report.add_os_info()

    if symptom_script:
        symb = {}
        try:
            with open(symptom_script) as f:
                exec(compile(f.read(), symptom_script, 'exec'), symb)
            package = symb['run'](report, ui)
            if not package:
                apport.error('symptom script %s did not determine the affected package', symptom_script)
                return
            report['Symptom'] = os.path.splitext(os.path.basename(symptom_script))[0]
        except StopIteration:
            sys.exit(0)
        except Exception as e:
            apport.error('symptom script %s crashed:', symptom_script)
            traceback.print_exc()
            sys.exit(0)

    if not package:
        if 'ExecutablePath' in report:
            package = apport.fileutils.find_file_package(report['ExecutablePath'])
        else:
            raise KeyError('called without a package, and report does not have ExecutablePath')
    try:
        report.add_package_info(package)
    except ValueError:
        # this happens if we are collecting information on an uninstalled
        # package
        if not ignore_uninstalled:
            raise
    except SystemError as e:
        report['UnreportableReason'] = excstr(e)

    if 'UnreportableReason' not in report:
        if report.add_hooks_info(ui):
            sys.exit(0)

        # check package origin; we do that after adding hooks, so that hooks have
        # the chance to set a third-party CrashDB.
        try:
            if 'CrashDB' not in report and 'APPORT_DISABLE_DISTRO_CHECK' not in os.environ:
                if 'Package' not in report:
                    report['UnreportableReason'] = _('This package does not seem to be installed correctly')
                elif not apport.packaging.is_distro_package(report['Package'].split()[0]) and  \
                        not apport.packaging.is_native_origin_package(report['Package'].split()[0]):
                    # TRANS: %s is the name of the operating system
                    report['UnreportableReason'] = _(
                        'This is not an official %s package. Please remove any third party package and try again.') % report['DistroRelease'].split()[0]
        except ValueError:
            # this happens if we are collecting information on an uninstalled
            # package
            if not ignore_uninstalled:
                raise

    # add title
    if 'Title' not in report:
        title = report.standard_title()
        if title:
            report['Title'] = title

    # check obsolete packages
    if report.get('ProblemType') == 'Crash' and 'APPORT_IGNORE_OBSOLETE_PACKAGES' not in os.environ:
        old_pkgs = report.obsolete_packages()
        if old_pkgs:
            report['UnreportableReason'] = _('You have some obsolete package \
versions installed. Please upgrade the following packages and check if the \
problem still occurs:\n\n%s') % ', '.join(old_pkgs)

    # disabled: if we have a SIGABRT without an assertion message, declare as unreportable
    # if report.get('Signal') == '6' and 'AssertionMessage' not in report:
    #     report['UnreportableReason'] = _('The program crashed on an assertion failure, but the message could not be retrieved. Apport does not support reporting these crashes.')

    if reportfile:
        try:
            with open(reportfile, 'ab') as f:
                os.chmod(reportfile, 0)
                report.write(f, only_new=True)
        except IOError as e:
            # this should happen very rarely; presumably a new crash report is
            # being generated by a background apport instance (which will set
            # the file to permissions zero while writing), while the first
            # report is being processed
            apport.error('Cannot update %s: %s' % (reportfile, e))

        apport.fileutils.mark_report_seen(reportfile)
        os.chmod(reportfile, 0o640)


class UserInterface:
    '''Apport user interface API.

    This provides an abstract base class for encapsulating the workflow and
    common code for any user interface implementation (like GTK, Qt, or CLI).

    A concrete subclass must implement all the abstract ui_* methods.
    '''
    def __init__(self):
        '''Initialize program state and parse command line options.'''

        self.gettext_domain = 'apport'
        self.report = None
        self.report_file = None
        self.cur_package = None
        self.offer_restart = False
        self.specified_a_pkg = False

        try:
            self.crashdb = apport.crashdb.get_crashdb(None)
        except ImportError as e:
            # this can happen while upgrading python packages
            apport.fatal('Could not import module, is a package upgrade in progress? Error: %s', str(e))
        except KeyError:
            apport.fatal('/etc/apport/crashdb.conf is damaged: No default database')

        gettext.textdomain(self.gettext_domain)
        self.parse_argv()

    #
    # main entry points
    #

    def run_crashes(self):
        '''Present all currently pending crash reports.

        Ask the user what to do about them, and offer to file bugs for them.

        Crashes that occurred in a different desktop (logind) session than the
        one that is currently running are not processed. This skips crashes
        that happened during logout, which are uninteresting and confusing to
        see at the next login.

        Return True if at least one crash report was processed, False
        otherwise.
        '''
        result = False
        # for iterating over /var/crash (as opposed to running on or clicking
        # on a particular .crash file) we offer restarting
        self.offer_restart = True

        if os.geteuid() == 0:
            reports = apport.fileutils.get_new_system_reports()
            logind_session = None
        else:
            reports = apport.fileutils.get_new_reports()
            proc_pid_fd = os.open('/proc/%s' % os.getpid(), os.O_RDONLY | os.O_PATH | os.O_DIRECTORY)
            logind_session = apport.Report.get_logind_session(proc_pid_fd)

        for f in reports:
            if not self.load_report(f):
                continue

            # Skip crashes that happened during logout, which are uninteresting
            # and confusing to see at the next login. A crash happened and gets
            # reported in the same session if the logind session paths agree
            # and the session started before the report's "Date".
            if logind_session and '_LogindSession' in self.report and \
               'Date' in self.report:
                if logind_session[0] != self.report['_LogindSession'] or \
                   logind_session[1] > self.report.get_timestamp():
                    continue

            if self.report['ProblemType'] == 'Hang':
                self.finish_hang(f)
            else:
                self.run_crash(f)
            result = True

        return result

    def run_crash(self, report_file, confirm=True):
        '''Present and report a particular crash.

        If confirm is True, ask the user what to do about it, and offer to file
        a bug for it.

        If confirm is False, the user will not be asked, and the crash is
        reported right away.
        '''
        self.report_file = report_file

        try:
            try:
                apport.fileutils.mark_report_seen(report_file)
            except OSError:
                # not there any more? no problem, then it won't be regarded as
                # "seen" any more anyway
                pass
            if not self.report and not self.load_report(report_file):
                return

            if 'Ignore' in self.report:
                return

            # check for absent CoreDumps (removed if they exceed size limit)
            if self.report.get('ProblemType') == 'Crash' and 'Signal' in self.report and 'CoreDump' not in self.report and 'Stacktrace' not in self.report:
                subject = os.path.basename(self.report.get('ExecutablePath', _('unknown program')))
                heading = _('Sorry, the program "%s" closed unexpectedly') % subject
                self.ui_error_message(
                    _('Problem in %s') % subject,
                    '%s\n\n%s' % (heading, _('Your computer does not have enough free '
                                             'memory to automatically analyze the problem '
                                             'and send a report to the developers.')))
                return

            allowed_to_report = apport.fileutils.allowed_to_report()
            response = self.ui_present_report_details(allowed_to_report)
            if response['report'] or response['examine']:
                if 'Dependencies' not in self.report:
                    self.collect_info()

            if self.report is None:
                # collect() does that on invalid reports
                return

            if response['examine']:
                self.examine()
                return
            if response['restart']:
                self.restart()
            if response['blacklist']:
                self.report.mark_ignore()
            try:
                if response['remember']:
                    self.remember_send_report(response['report'])
            # use try/expect for python2 support. Old reports (generated pre-apport 2.20.10-0ubuntu4)
            # may not have the remember key and can be loaded afterwards (or after dist-upgrade)
            except KeyError:
                pass
            if not response['report']:
                return

            # We don't want to send crashes to the crash database for binaries
            # that changed since the crash happened. See LP: #1039220 for
            # details.
            if '_MarkForUpload' in self.report and \
                    self.report['_MarkForUpload'] != 'False':
                apport.fileutils.mark_report_upload(report_file)
            # We check for duplicates and unreportable crashes here, rather
            # than before we show the dialog, as we want to submit these to the
            # crash database, but not Launchpad.
            if self.crashdb.accepts(self.report):
                # FIXME: This behaviour is not really correct, but necessary as
                # long as we only support a single crashdb and have whoopsie
                # hardcoded. Once we have multiple crash dbs, we need to check
                # accepts() earlier, and not even present the data if none of
                # the DBs wants the report. See LP#957177 for details.
                if self.handle_duplicate():
                    return
                if self.check_unreportable():
                    return
                self.file_report()
        except IOError as e:
            # fail gracefully if file is not readable for us
            if e.errno in (errno.EPERM, errno.EACCES):
                self.ui_error_message(_('Invalid problem report'),
                                      _('You are not allowed to access this problem report.'))
                sys.exit(1)
            elif e.errno == errno.ENOSPC:
                self.ui_error_message(_('Error'),
                                      _('There is not enough disk space available to process this report.'))
                sys.exit(1)
            else:
                self.ui_error_message(_('Invalid problem report'), e.strerror)
                sys.exit(1)
        except OSError as e:
            # fail gracefully on ENOMEM
            if e.errno == errno.ENOMEM:
                apport.fatal('Out of memory, aborting')
            else:
                raise

    def finish_hang(self, f):
        '''Finish processing a hanging application after the core pipe handler
        has handed the report back.

        This will signal to whoopsie that the report needs to be uploaded.
        '''
        apport.fileutils.mark_report_upload(f)
        apport.fileutils.mark_report_seen(f)

    def run_hang(self, pid):
        '''Report an application hanging.

        This will first present a dialog containing the information it can
        collect from the running application (everything but the trace) with
        the option of terminating or restarting the application, optionally
        reporting that this error occurred.

        A SIGABRT will then be sent to the process and a series of
        noninteractive processes will collect the remaining information and
        mark the report for uploading.
        '''
        self.report = apport.Report('Hang')
        self.report.add_proc_info(pid)
        self.report.add_package_info()
        path = self.report.get('ExecutablePath', '')
        self.cur_package = apport.fileutils.find_file_package(path)
        self.report.add_os_info()
        allowed_to_report = apport.fileutils.allowed_to_report()
        response = self.ui_present_report_details(allowed_to_report,
                                                  modal_for=pid)
        if response['report']:
            apport.fileutils.mark_hanging_process(self.report, pid)
            os.kill(int(pid), signal.SIGABRT)
        else:
            os.kill(int(pid), signal.SIGKILL)

        if response['restart']:
            self.wait_for_pid(pid)
            self.restart()

    def wait_for_pid(self, pid):
        '''waitpid() does not work for non-child processes. Query the process
        state in a loop, waiting for "no such process."
        '''
        while True:
            try:
                os.kill(int(pid), 0)
            except OSError as e:
                if e.errno == errno.ESRCH:
                    break
                else:
                    raise
            time.sleep(1)

    def kill_segv(self, pid):
        os.kill(int(pid), signal.SIGSEGV)

    def run_report_bug(self, symptom_script=None):
        '''Report a bug.

        If a pid is given on the command line, the report will contain runtime
        debug information. Either a package or a pid must be specified; if none
        is given, show a list of symptoms.

        If a symptom script is given, this will be run first (used by
        run_symptom()).
        '''
        if not self.options.package and not self.options.pid and \
                not symptom_script:
            if self.run_symptoms():
                return True
            else:
                self.ui_error_message(_('No package specified'),
                                      _('You need to specify a package or a PID. See --help for more information.'))
            return False

        self.report = apport.Report('Bug')

        # if PID is given, add info
        if self.options.pid:
            try:
                proc_pid_fd = os.open('/proc/%s' % self.options.pid, os.O_RDONLY | os.O_PATH | os.O_DIRECTORY)
                with open('stat', opener=lambda path, mode: os.open(path, mode, dir_fd=proc_pid_fd)) as f:
                    stat = f.read().split()
                flags = int(stat[8])
                if flags & PF_KTHREAD:
                    # this PID is a kernel thread
                    self.options.package = 'linux'
                else:
                    self.report.add_proc_info(proc_pid_fd=proc_pid_fd)
            except (ValueError, IOError, OSError) as e:
                if hasattr(e, 'errno'):
                    # silently ignore nonexisting PIDs; the user must not close the
                    # application prematurely
                    if e.errno == errno.ENOENT:
                        return False
                    elif e.errno == errno.EACCES:
                        self.ui_error_message(_('Permission denied'),
                                              _('The specified process does not belong to you. Please run this program as the process owner or as root.'))
                        return False
                self.ui_error_message(_('Invalid PID'),
                                      _('The specified process ID does not belong to a program.'))
                return False
        else:
            self.report.add_proc_environ()

        if self.options.package:
            self.options.package = self.options.package.strip()
        # "Do what I mean" for filing against "linux"
        if self.options.package == 'linux':
            self.cur_package = apport.packaging.get_kernel_package()
        else:
            self.cur_package = self.options.package

        try:
            self.collect_info(symptom_script)
        except ValueError as e:
            if 'package' in str(e) and 'does not exist' in str(e):
                if not self.cur_package:
                    self.ui_error_message(_('Invalid problem report'),
                                          _('Symptom script %s did not determine an affected package') % symptom_script)
                else:
                    self.ui_error_message(_('Invalid problem report'),
                                          _('Package %s does not exist') % self.cur_package)
                return False
            else:
                raise

        if self.check_unreportable():
            return

        self.add_extra_tags()

        if self.handle_duplicate():
            return True

        # not useful for bug reports, and has potentially sensitive information
        try:
            del self.report['ProcCmdline']
        except KeyError:
            pass

        if self.options.save:
            try:
                with open(os.path.expanduser(self.options.save), 'wb') as f:
                    self.report.write(f)
            except (IOError, OSError) as e:
                self.ui_error_message(_('Cannot create report'), excstr(e))
        else:
            # show what's being sent
            allowed_to_report = apport.fileutils.allowed_to_report()
            response = self.ui_present_report_details(allowed_to_report)
            if response['report']:
                self.file_report()

        return True

    def run_update_report(self):
        '''Update an existing bug with locally collected information.'''

        # avoid irrelevant noise
        if not self.crashdb.can_update(self.options.update_report):
            self.ui_error_message(_('Updating problem report'),
                                  _('You are not the reporter or subscriber of this '
                                    'problem report, or the report is a duplicate or already '
                                    'closed.\n\nPlease create a new report using "apport-bug".'))
            return False

        is_reporter = self.crashdb.is_reporter(self.options.update_report)

        if not is_reporter:
            r = self.ui_question_yesno(
                _('You are not the reporter of this problem report. It '
                  'is much easier to mark a bug as a duplicate of another '
                  'than to move your comments and attachments to a new bug.\n\n'
                  'Subsequently, we recommend that you file a new bug report '
                  'using "apport-bug" and make a comment in this bug about '
                  'the one you file.\n\n'
                  'Do you really want to proceed?'))
            if not r:
                return False

        # list of affected source packages
        self.report = apport.Report('Bug')
        if self.options.package:
            pkgs = [self.options.package.strip()]
        else:
            pkgs = self.crashdb.get_affected_packages(self.options.update_report)

        info_collected = False
        for p in pkgs:
            # print('Collecting apport information for source package %s...' % p)
            self.cur_package = p
            self.report['SourcePackage'] = p
            self.report['Package'] = p  # no way to find this out

            # we either must have the package installed or a source package hook
            # available to collect sensible information
            try:
                apport.packaging.get_version(p)
            except ValueError:
                if not os.path.exists(os.path.join(apport.report._hook_dir, 'source_%s.py' % p)):
                    print('Package %s not installed and no hook available, ignoring' % p)
                    continue
            self.collect_info(ignore_uninstalled=True)
            info_collected = True

        if not info_collected:
            self.ui_info_message(_('Updating problem report'),
                                 _('No additional information collected.'))
            return False

        self.report.add_user_info()
        self.report.add_proc_environ()
        self.add_extra_tags()

        # delete the uninteresting keys
        del self.report['Date']
        try:
            del self.report['SourcePackage']
        except KeyError:
            pass

        if len(self.report) == 0:
            self.ui_info_message(_('Updating problem report'),
                                 _('No additional information collected.'))
            return False

        # show what's being sent
        allowed_to_report = apport.fileutils.allowed_to_report()
        response = self.ui_present_report_details(allowed_to_report)
        if response['report']:
            self.crashdb.update(self.options.update_report, self.report,
                                'apport information', change_description=is_reporter,
                                attachment_comment='apport information')
            return True

        return False

    def run_symptoms(self):
        '''Report a bug from a list of available symptoms.

        Return False if no symptoms are available.
        '''
        scripts = glob.glob(os.path.join(symptom_script_dir, '*.py'))

        symptom_names = []
        symptom_descriptions = []
        for script in scripts:
            # scripts with an underscore can be used for private libraries
            if os.path.basename(script).startswith('_'):
                continue
            symb = {}
            try:
                with open(script) as f:
                    exec(compile(f.read(), script, 'exec'), symb)
            except Exception:
                apport.error('symptom script %s is invalid', script)
                traceback.print_exc()
                continue
            if 'run' not in symb:
                apport.error('symptom script %s does not define run() function', script)
                continue
            symptom_names.append(os.path.splitext(os.path.basename(script))[0])
            symptom_descriptions.append(symb.get('description', symptom_names[-1]))

        if not symptom_names:
            return False

        symptom_descriptions, symptom_names = \
            zip(*sorted(zip(symptom_descriptions, symptom_names)))
        symptom_descriptions = list(symptom_descriptions)
        symptom_names = list(symptom_names)
        symptom_names.append(None)
        symptom_descriptions.append('Other problem')

        ch = self.ui_question_choice(_('What kind of problem do you want to report?'),
                                     symptom_descriptions, False)

        if ch is not None:
            symptom = symptom_names[ch[0]]
            if symptom:
                self.run_report_bug(os.path.join(symptom_script_dir, symptom + '.py'))
            else:
                return False

        return True

    def run_symptom(self):
        '''Report a bug with a symptom script.'''

        script = os.path.join(symptom_script_dir, self.options.symptom + '.py')
        if not os.path.exists(script):
            self.ui_error_message(_('Unknown symptom'),
                                  _('The symptom "%s" is not known.') % self.options.symptom)
            return

        self.run_report_bug(script)

    def run_argv(self):
        '''Call appopriate run_* method according to command line arguments.

        Return True if at least one report has been processed, and False
        otherwise.
        '''
        if self.options.symptom:
            self.run_symptom()
            return True
        elif hasattr(self.options, 'pid') and self.options.hanging:
            self.run_hang(self.options.pid)
            return True
        elif self.options.filebug:
            return self.run_report_bug()
        elif self.options.update_report is not None:
            return self.run_update_report()
        elif self.options.version:
            print(__version__)
            return True
        elif self.options.crash_file:
            try:
                self.run_crash(self.options.crash_file, False)
            except OSError as e:
                self.ui_error_message(_('Invalid problem report'), excstr(e))
            return True
        elif self.options.window:
                self.ui_info_message('', _('After closing this message '
                                           'please click on an application window to report a problem about it.'))
                xprop = subprocess.Popen(['xprop', '_NET_WM_PID'],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (out, err) = xprop.communicate()
                if xprop.returncode == 0:
                    try:
                        self.options.pid = int(out.split()[-1])
                    except ValueError:
                        self.ui_error_message(_('Cannot create report'),
                                              _('xprop failed to determine process ID of the window'))
                        return True
                    return self.run_report_bug()
                else:
                    self.ui_error_message(_('Cannot create report'),
                                          _('xprop failed to determine process ID of the window') + '\n\n' + err)
                    return True
        else:
            return self.run_crashes()

    #
    # methods that implement workflow bits
    #

    def parse_argv_update(self):
        '''Parse command line options when being invoked in update mode.

        Return (options, args).
        '''
        optparser = optparse.OptionParser(_('%prog <report number>'))
        optparser.add_option('-p', '--package',
                             help=_('Specify package name.'))
        optparser.add_option('--tag', action='append', default=[],
                             help=_('Add an extra tag to the report. Can be specified multiple times.'))
        (self.options, self.args) = optparser.parse_args()

        if len(self.args) != 1 or not self.args[0].isdigit():
            optparser.error('You need to specify a report number to update')
            sys.exit(1)

        self.options.update_report = int(self.args[0])
        self.options.symptom = None
        self.options.filebug = False
        self.options.crash_file = None
        self.options.version = None
        self.args = []

    def parse_argv(self):
        '''Parse command line options.

        If a single argument is given without any options, this tries to "do
        what I mean".
        '''
        # invoked in update mode?
        if len(sys.argv) > 0:
            if 'APPORT_INVOKED_AS' in os.environ:
                sys.argv[0] = os.path.join(os.path.dirname(sys.argv[0]),
                                           os.path.basename(os.environ['APPORT_INVOKED_AS']))
            cmd = sys.argv[0]
            if cmd.endswith('-update-bug') or cmd.endswith('-collect'):
                self.parse_argv_update()
                return

        optparser = optparse.OptionParser(_('%prog [options] [symptom|pid|package|program path|.apport/.crash file]'))
        optparser.add_option('-f', '--file-bug', action='store_true',
                             dest='filebug', default=False,
                             help=_('Start in bug filing mode. Requires --package and an optional --pid, or just a --pid. If neither is given, display a list of known symptoms. (Implied if a single argument is given.)'))
        optparser.add_option('-w', '--window', action='store_true', default=False,
                             help=_('Click a window as a target for filing a problem report.'))
        optparser.add_option('-u', '--update-bug', type='int', dest='update_report',
                             help=_('Start in bug updating mode. Can take an optional --package.'))
        optparser.add_option('-s', '--symptom', metavar='SYMPTOM',
                             help=_('File a bug report about a symptom. (Implied if symptom name is given as only argument.)'))
        optparser.add_option('-p', '--package',
                             help=_('Specify package name in --file-bug mode. This is optional if a --pid is specified. (Implied if package name is given as only argument.)'))
        optparser.add_option('-P', '--pid', type='int',
                             help=_('Specify a running program in --file-bug mode. If this is specified, the bug report will contain more information.  (Implied if pid is given as only argument.)'))
        optparser.add_option('--hanging', action='store_true', default=False,
                             help=_('The provided pid is a hanging application.'))
        optparser.add_option('-c', '--crash-file', metavar='PATH',
                             help=_('Report the crash from given .apport or .crash file instead of the pending ones in %s. (Implied if file is given as only argument.)') % apport.fileutils.report_dir)
        optparser.add_option('--save', metavar='PATH',
                             help=_('In bug filing mode, save the collected information into a file instead of reporting it. This file can then be reported later on from a different machine.'))
        optparser.add_option('--tag', action='append', default=[],
                             help=_('Add an extra tag to the report. Can be specified multiple times.'))
        optparser.add_option('-v', '--version', action='store_true',
                             help=_('Print the Apport version number.'))

        if len(sys.argv) > 0 and cmd.endswith('-bug'):
            for o in ('-f', '-u', '-s', '-p', '-P', '-c'):
                optparser.get_option(o).help = optparse.SUPPRESS_HELP

        (self.options, self.args) = optparser.parse_args()

        # mutually exclusive arguments
        if self.options.update_report:
            if self.options.filebug or self.options.window or self.options.symptom \
               or self.options.pid or self.options.crash_file or self.options.save:
                optparser.error('-u/--update-bug option cannot be used together with options for a new report')

        # "do what I mean" for zero or one arguments
        if len(sys.argv) == 0:
            return

        # no argument: default to "show pending crashes" except when called in
        # bug mode
        # NOTE: uses sys.argv, since self.args if empty for all the options,
        # e.g. "-v" or "-u $BUG"
        if len(sys.argv) == 1 and cmd.endswith('-bug'):
            self.options.filebug = True
            return

        # one argument: guess "file bug" mode by argument type
        if len(self.args) != 1:
            return

        # symptom?
        if os.path.exists(os.path.join(symptom_script_dir, self.args[0] + '.py')):
            self.options.filebug = True
            self.options.symptom = self.args[0]
            self.args = []

        # .crash/.apport file?
        elif self.args[0].endswith('.crash') or self.args[0].endswith('.apport'):
            self.options.crash_file = self.args[0]
            self.args = []

        # PID?
        elif self.args[0].isdigit():
            self.options.filebug = True
            self.options.pid = self.args[0]
            self.args = []

        # executable?
        elif '/' in self.args[0]:
            if self.args[0].startswith('/snap/bin'):
                # see if the snap has the same name as the executable
                snap = find_snap(self.args[0].split('/')[-1])
                if not snap:
                    optparser.error('%s is provided by a snap. No contact address has been provided; visit the forum at https://forum.snapcraft.io/ for help.' % self.args[0])
                elif snap.get("contact", ""):
                    optparser.error('%s is provided by a snap published by %s. Contact them via %s for help.' % (self.args[0], snap["developer"], snap["contact"]))
                else:
                    optparser.error('%s is provided by a snap published by %s. No contact address has been provided; visit the forum at https://forum.snapcraft.io/ for help.' % (self.args[0], snap["developer"]))
                sys.exit(1)
            else:
                pkg = apport.packaging.get_file_package(self.args[0])
                if not pkg:
                    optparser.error('%s does not belong to a package.' % self.args[0])
                    sys.exit(1)
            self.args = []
            self.options.filebug = True
            self.options.package = pkg

        # otherwise: package name
        else:
            self.options.filebug = True
            self.specified_a_pkg = True
            self.options.package = self.args[0]
            self.args = []

    def format_filesize(self, size):
        '''Format the given integer as humanly readable and i18n'ed file size.'''

        if size < 1000000:
            return locale.format('%.1f', size / 1000.) + ' KB'
        if size < 1000000000:
            return locale.format('%.1f', size / 1000000.) + ' MB'
        return locale.format('%.1f', size / float(1000000000)) + ' GB'

    def get_complete_size(self):
        '''Return the size of the complete report.'''

        # report wasn't loaded, so count manually
        size = 0
        for k in self.report:
            if self.report[k]:
                try:
                    # if we have a compressed value, take its size, but take
                    # base64 overhead into account
                    size += len(self.report[k].gzipvalue) * 8 / 6
                except AttributeError:
                    size += len(self.report[k])
        return size

    def get_reduced_size(self):
        '''Return the size of the reduced report.'''

        size = 0
        for k in self.report:
            if k != 'CoreDump':
                if self.report[k]:
                    try:
                        # if we have a compressed value, take its size, but take
                        # base64 overhead into account
                        size += len(self.report[k].gzipvalue) * 8 / 6
                    except AttributeError:
                        size += len(self.report[k])

        return size

    def can_examine_locally(self):
        '''Check whether to offer the "Examine locally" button.

        This will be true if the report has a core dump, apport-retrace is
        installed and a terminal is available (see ui_run_terminal()).
        '''
        if not self.report or 'CoreDump' not in self.report:
            return False

        try:
            if subprocess.call(['which', 'apport-retrace'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT) != 0:
                return False
        except OSError:
            return False

        try:
            return self.ui_run_terminal(None)
        except NotImplementedError:
            return False

    def restart(self):
        '''Reopen the crashed application.'''

        assert 'ProcCmdline' in self.report

        if os.fork() == 0:
            os.setsid()
            os.execlp('sh', 'sh', '-c', self.report.get('RespawnCommand', self.report['ProcCmdline']))
            sys.exit(1)

    def examine(self):
        '''Locally examine crash report.'''

        response = self.ui_question_choice(
            _('This will launch apport-retrace in a terminal window to examine the crash.'),
            [_('Run gdb session'),
             _('Run gdb session without downloading debug symbols'),
             # TRANSLATORS: %s contains the crash report file name
             _('Update %s with fully symbolic stack trace') % self.report_file,
            ],
            False)

        if response is None:
            return

        retrace_with_download = 'apport-retrace -S system -C %s -v ' % os.path.expanduser(
            '~/.cache/apport/retrace')
        retrace_no_download = 'apport-retrace '
        filearg = "'" + self.report_file.replace("'", "'\\''") + "'"

        cmds = {
            0: retrace_with_download + '--gdb ' + filearg,
            1: retrace_no_download + '--gdb ' + filearg,
            2: retrace_with_download + '--output ' + filearg + ' ' + filearg,
        }

        self.ui_run_terminal(cmds[response[0]])

    def remember_send_report(self, send_report):
        '''Put whoopsie in auto or never mode'''
        if send_report:
            send_report = "true"
        else:
            send_report = "false"
        try:
            subprocess.check_output(['/usr/bin/gdbus', 'call', '-y',
                                     '-d', 'com.ubuntu.WhoopsiePreferences',
                                     '-o', '/com/ubuntu/WhoopsiePreferences',
                                     '-m', 'com.ubuntu.WhoopsiePreferences.SetReportCrashes', send_report])
            subprocess.check_output(['/usr/bin/gdbus', 'call', '-y',
                                     '-d', 'com.ubuntu.WhoopsiePreferences',
                                     '-o', '/com/ubuntu/WhoopsiePreferences',
                                     '-m', 'com.ubuntu.WhoopsiePreferences.SetAutomaticallyReportCrashes', 'true'])
        except (OSError, subprocess.CalledProcessError) as e:
            self.ui_error_message(_("Can't remember send report status settings"), '%s\n\n%s' % (
                                  _("Saving crash reporting state failed. Can't set auto or never reporting mode."),
                                  excstr(e)))

    def check_report_crashdb(self):
        '''Process reports' CrashDB field, if present'''

        if 'CrashDB' not in self.report:
            return True

        # specification?
        if self.report['CrashDB'].lstrip().startswith('{'):
            try:
                spec = ast.literal_eval(self.report['CrashDB'])
                assert isinstance(spec, dict)
                assert 'impl' in spec
            except Exception as e:
                self.report['UnreportableReason'] = 'A package hook defines an invalid crash database definition:\n%s\n%s' % (self.report['CrashDB'], e)
                return False
            try:
                self.crashdb = apport.crashdb.load_crashdb(None, spec)
            except (ImportError, KeyError):
                self.report['UnreportableReason'] = 'A package hook wants to send this report to the crash database "%s" which does not exist.' % self.report['CrashDB']

        else:
            # DB name
            try:
                self.crashdb = apport.crashdb.get_crashdb(None, self.report['CrashDB'])
            except (ImportError, KeyError):
                self.report['UnreportableReason'] = 'A package hook wants to send this report to the crash database "%s" which does not exist.' % self.report['CrashDB']
                return False

        return True

    def collect_info(self, symptom_script=None, ignore_uninstalled=False,
                     on_finished=None):
        '''Collect additional information.

        Call all the add_*_info() methods and display a progress dialog during
        this.

        In particular, this adds OS, package and gdb information and checks bug
        patterns.

        If a symptom script is given, this will be run first (used by
        run_symptom()).
        '''
        self.report['_MarkForUpload'] = 'True'

        # check if we already ran (we might load a processed report), skip if so
        if (self.report.get('ProblemType') == 'Crash' and 'Stacktrace' in self.report) or (self.report.get('ProblemType') != 'Crash' and 'Dependencies' in self.report):

            if on_finished:
                on_finished()
            return

        # ensure that the crashed program is still installed:
        if self.report.get('ProblemType') == 'Crash':
            exe_path = self.report.get('ExecutablePath', '')
            if not os.path.exists(exe_path):
                msg = _('This problem report applies to a program which is not installed any more.')
                if exe_path:
                    msg = '%s (%s)' % (msg, self.report['ExecutablePath'])
                self.report['UnreportableReason'] = msg
                if on_finished:
                    on_finished()
                return

            if 'InterpreterPath' in self.report:
                if not os.path.exists(self.report['InterpreterPath']):
                    msg = _('This problem report applies to a program which is not installed any more.')
                    self.report['UnreportableReason'] = '%s (%s)' % (msg, self.report['InterpreterPath'])
                    if on_finished:
                        on_finished()
                    return

        # check if binary changed since the crash happened
        if 'ExecutablePath' in self.report and 'ExecutableTimestamp' in self.report:
            orig_time = int(self.report['ExecutableTimestamp'])
            del self.report['ExecutableTimestamp']
            cur_time = int(os.stat(self.report['ExecutablePath']).st_mtime)

            if orig_time != cur_time:
                self.report['_MarkForUpload'] = 'False'
                self.report['UnreportableReason'] = (
                    _('The problem happened with the program %s which changed '
                      'since the crash occurred.') % self.report['ExecutablePath'])
                return

        if not self.cur_package and 'ExecutablePath' not in self.report \
                and not symptom_script:
            # this happens if we file a bug without specifying a PID or a
            # package
            self.report.add_os_info()
        else:
            # since this might take a while, create separate threads and
            # display a progress dialog.
            self.ui_start_info_collection_progress()
            # only use a UI for asking questions if the crash db will accept
            # the report
            if self.crashdb.accepts(self.report):
                hookui = HookUI(self)
            else:
                hookui = None

            if 'Stacktrace' not in self.report:
                # save original environment, in case hooks change it
                orig_env = os.environ.copy()
                icthread = apport.REThread.REThread(target=thread_collect_info,
                                                    name='thread_collect_info',
                                                    args=(self.report, self.report_file, self.cur_package,
                                                          hookui, symptom_script, ignore_uninstalled))
                icthread.start()
                while icthread.isAlive():
                    self.ui_pulse_info_collection_progress()
                    if hookui:
                        try:
                            hookui.process_event()
                        except KeyboardInterrupt:
                            sys.exit(1)

                icthread.join()

                # restore original environment
                os.environ.clear()
                os.environ.update(orig_env)

                try:
                    icthread.exc_raise()
                except (IOError, EOFError, zlib.error) as e:
                    # can happen with broken core dumps
                    self.report['UnreportableReason'] = '%s\n\n%s' % (
                        _('This problem report is damaged and cannot be processed.'),
                        repr(e))
                    self.report['_MarkForUpload'] = 'False'
                except ValueError:  # package does not exist
                    snap = find_snap(self.cur_package)
                    if not snap:
                        pass
                    elif snap.get("contact", ""):
                        self.report['UnreportableReason'] = _('This report is about a snap published by %s. Contact them via %s for help.') % (snap["developer"], snap["contact"])
                        self.report['_MarkForUpload'] = 'False'
                    else:
                        self.report['UnreportableReason'] = _('This report is about a snap published by %s. No contact address has been provided; visit the forum at https://forum.snapcraft.io/ for help.') % snap["developer"]
                        self.report['_MarkForUpload'] = 'False'

                    if 'UnreportableReason' not in self.report:
                        self.report['UnreportableReason'] = _('This report is about a package that is not installed.')
                        self.report['_MarkForUpload'] = 'False'
                except Exception as e:
                    apport.error(repr(e))
                    self.report['UnreportableReason'] = _('An error occurred while attempting to '
                                                          'process this problem report:') + '\n\n' + str(e)
                    self.report['_MarkForUpload'] = 'False'

            snap = find_snap(self.cur_package)
            if snap and 'UnreportableReason' not in self.report and self.specified_a_pkg:
                if snap.get("contact", ""):
                    msg = _('You are about to report a bug against the deb package, but you also a have snap published by %s installed. You can contact them via %s for help. Do you want to continue with the bug report against the deb?') % (snap["developer"], snap["contact"])
                else:
                    msg = _('You are about to report a bug against the deb package, but you also a have snap published by %s installed. For the snap, no contact address has been provided; visit the forum at https://forum.snapcraft.io/ for help. Do you want to continue with the bug report against the deb?') % snap["developer"]

                if not self.ui_question_yesno(msg):
                    self.ui_stop_info_collection_progress()
                    sys.exit(0)
                    return

            if 'UnreportableReason' in self.report or not self.check_report_crashdb():
                self.ui_stop_info_collection_progress()
                if on_finished:
                    on_finished()
                return

            # check bug patterns
            if self.report.get('ProblemType') == 'KernelCrash' or self.report.get('ProblemType') == 'KernelOops' or 'Package' in self.report:
                bpthread = apport.REThread.REThread(target=self.report.search_bug_patterns,
                                                    args=(self.crashdb.get_bugpattern_baseurl(),))
                bpthread.start()
                while bpthread.isAlive():
                    self.ui_pulse_info_collection_progress()
                    try:
                        bpthread.join(0.1)
                    except KeyboardInterrupt:
                        sys.exit(1)
                try:
                    bpthread.exc_raise()
                except (IOError, EOFError, zlib.error) as e:
                    # can happen with broken gz values
                    self.report['UnreportableReason'] = '%s\n\n%s' % (
                        _('This problem report is damaged and cannot be processed.'),
                        repr(e))
                if bpthread.return_value():
                    self.report['_KnownReport'] = bpthread.return_value()

            # check crash database if problem is known
            if self.report.get('ProblemType') != 'Bug':
                known_thread = apport.REThread.REThread(target=self.crashdb.known,
                                                        args=(self.report,))
                known_thread.start()
                while known_thread.isAlive():
                    self.ui_pulse_info_collection_progress()
                    try:
                        known_thread.join(0.1)
                    except KeyboardInterrupt:
                        sys.exit(1)
                known_thread.exc_raise()
                val = known_thread.return_value()
                if val is not None:
                    if val is True:
                        self.report['_KnownReport'] = '1'
                    else:
                        self.report['_KnownReport'] = val

            # anonymize; needs to happen after duplicate checking, otherwise we
            # might damage the stack trace
            anonymize_thread = apport.REThread.REThread(target=self.report.anonymize)
            anonymize_thread.start()
            while anonymize_thread.isAlive():
                self.ui_pulse_info_collection_progress()
                try:
                    anonymize_thread.join(0.1)
                except KeyboardInterrupt:
                    sys.exit(1)
            anonymize_thread.exc_raise()

            self.ui_stop_info_collection_progress()

            # check that we were able to determine package names
            if 'UnreportableReason' not in self.report:
                if (('SourcePackage' not in self.report and 'Dependencies' not in self.report) or
                    (not self.report.get('ProblemType', '').startswith('Kernel') and
                     'Package' not in self.report)):
                    self.ui_error_message(_('Invalid problem report'),
                                          _('Could not determine the package or source package name.'))
                    # TODO This is not called consistently, is it really needed?
                    self.ui_shutdown()
                    sys.exit(1)

        if on_finished:
            on_finished()

    def open_url(self, url):
        '''Open the given URL in a new browser window.

        Display an error dialog if everything fails.
        '''
        (r, w) = os.pipe()
        if os.fork() > 0:
            os.close(w)
            (pid, status) = os.wait()
            if status:
                title = _('Unable to start web browser')
                error = _('Unable to start web browser to open %s.' % url)
                message = os.fdopen(r).readline()
                if message:
                    error += '\n' + message
                self.ui_error_message(title, error)
            try:
                os.close(r)
            except OSError:
                pass
            return

        os.setsid()
        os.close(r)

        # If we are called through pkexec/sudo, determine the real user id and
        # run the browser with it to get the user's web browser settings.

        try:
            uid = int(os.getenv('PKEXEC_UID', os.getenv('SUDO_UID')))
            sudo_prefix = ['sudo', '-H', '-u', '#' + str(uid)]
            # restore some environment for xdg-open; it's incredibly hard, or
            # alternatively, unsafe to funnel it through pkexec/env/sudo, so
            # grab it from gvfsd
            try:
                out = subprocess.check_output(
                    ['pgrep', '-a', '-x', '-u', str(uid), 'gvfsd']).decode('UTF-8')
                pid = out.splitlines()[0].split()[0]

                # find the D-BUS address
                with open('/proc/%s/environ' % pid, 'rb') as f:
                    env = f.read().split(b'\0')
                for e in env:
                    if e.startswith(b'DBUS_SESSION_BUS_ADDRESS='):
                        sudo_prefix.append('DBUS_SESSION_BUS_ADDRESS=' + e.split(b'=', 1)[1].decode())
                        break
            except (subprocess.CalledProcessError, IOError):
                pass

        except TypeError:
            sudo_prefix = []

        try:
            try:
                subprocess.call(sudo_prefix + ['xdg-open', url])
            except OSError as e:
                # fall back to webbrowser
                webbrowser.open(url, new=True, autoraise=True)
                sys.exit(0)
        except Exception as e:
            os.write(w, str(e))
            sys.exit(1)
        os._exit(0)

    def file_report(self):
        '''Upload the current report and guide the user to the reporting web page.'''
        # FIXME: This behaviour is not really correct, but necessary as
        # long as we only support a single crashdb and have whoopsie
        # hardcoded. Once we have multiple crash dbs, we need to check
        # accepts() earlier, and not even present the data if none of
        # the DBs wants the report. See LP#957177 for details.
        if not self.crashdb.accepts(self.report):
            return
        # drop PackageArchitecture if equal to Architecture
        if self.report.get('PackageArchitecture') == self.report.get('Architecture'):
            try:
                del self.report['PackageArchitecture']
            except KeyError:
                pass

        # StacktraceAddressSignature is redundant and does not need to clutter
        # the database
        try:
            del self.report['StacktraceAddressSignature']
        except KeyError:
            pass

        global __upload_progress
        __upload_progress = None

        def progress_callback(sent, total):
            global __upload_progress
            __upload_progress = float(sent) / total

        # drop internal/uninteresting keys, that start with "_"
        for k in list(self.report):
            if k.startswith('_'):
                del self.report[k]

        self.ui_start_upload_progress()
        upthread = apport.REThread.REThread(target=self.crashdb.upload,
                                            args=(self.report, progress_callback))
        upthread.start()
        while upthread.isAlive():
            self.ui_set_upload_progress(__upload_progress)
            try:
                upthread.join(0.1)
                upthread.exc_raise()
            except KeyboardInterrupt:
                sys.exit(1)
            except apport.crashdb.NeedsCredentials as e:
                message = _('Please enter your account information for the '
                            '%s bug tracking system')
                data = self.ui_question_userpass(message % excstr(e))
                if data is not None:
                    user, password = data
                    self.crashdb.set_credentials(user, password)
                    upthread = apport.REThread.REThread(target=self.crashdb.upload,
                                                        args=(self.report, progress_callback))
                    upthread.start()
            except (TypeError, SyntaxError, ValueError):
                raise
            except Exception as e:
                self.ui_error_message(_('Network problem'),
                                      '%s\n\n%s' % (
                                          _('Cannot connect to crash database, please check your Internet connection.'),
                                          excstr(e)))
                return

        upthread.exc_raise()
        ticket = upthread.return_value()
        self.ui_stop_upload_progress()

        url = self.crashdb.get_comment_url(self.report, ticket)
        if url:
            self.open_url(url)

    def load_report(self, path):
        '''Load report from given path and do some consistency checks.

        This might issue an error message and return False if the report cannot
        be processed, otherwise self.report is initialized and True is
        returned.
        '''
        try:
            self.report = apport.Report()
            with open(path, 'rb') as f:
                self.report.load(f, binary='compressed')
            if 'ProblemType' not in self.report:
                raise ValueError('Report does not contain "ProblemType" field')
        except MemoryError:
            self.report = None
            self.ui_error_message(_('Memory exhaustion'),
                                  _('Your system does not have enough memory to process this crash report.'))
            return False
        except IOError as e:
            self.report = None
            self.ui_error_message(_('Invalid problem report'), e.strerror)
            return False
        except (TypeError, ValueError, AssertionError, zlib.error) as e:
            self.report = None
            self.ui_error_message(_('Invalid problem report'),
                                  '%s\n\n%s' % (
                                      _('This problem report is damaged and cannot be processed.'),
                                      repr(e)))
            return False

        if 'Package' in self.report:
            self.cur_package = self.report['Package'].split()[0]
        else:
            self.cur_package = apport.fileutils.find_file_package(self.report.get('ExecutablePath', ''))

        return True

    def check_unreportable(self):
        '''Check if the current report is unreportable.

        If so, display an info message and return True.
        '''
        if not self.crashdb.accepts(self.report):
            return False
        if 'UnreportableReason' in self.report:
            if type(self.report['UnreportableReason']) == bytes:
                self.report['UnreportableReason'] = self.report['UnreportableReason'].decode('UTF-8')
            if 'Package' in self.report:
                title = _('Problem in %s') % self.report['Package'].split()[0]
            else:
                title = ''
            self.ui_info_message(title, _('The problem cannot be reported:\n\n%s') %
                                 self.report['UnreportableReason'])
            return True
        return False

    def get_desktop_entry(self):
        '''Return a .desktop info dictionary for the current report.

        Return None if report cannot be associated to a .desktop file.
        '''
        if 'DesktopFile' in self.report and os.path.exists(self.report['DesktopFile']):
            desktop_file = self.report['DesktopFile']
        else:
            try:
                desktop_file = apport.fileutils.find_package_desktopfile(self.cur_package)
            except ValueError:
                return None

        if not desktop_file:
            return None

        if PY3:
            cp = ConfigParser(interpolation=None, strict=False)
            kwargs = {'encoding': 'UTF-8'}
        else:
            cp = ConfigParser()
            kwargs = {}
        try:
            cp.read(desktop_file, **kwargs)
        except Exception as e:
            if 'onfig' in str(e.__class__) and 'arser' in str(e.__class__):
                sys.stderr.write('Warning! %s is broken: %s\n' % (desktop_file, str(e)))
                return None
            else:
                raise
        if not cp.has_section('Desktop Entry'):
            return None
        result = dict(cp.items('Desktop Entry'))
        if 'name' not in result:
            return None
        return result

    def handle_duplicate(self):
        '''Check if current report matches a bug pattern.

        If so, tell the user about it, open the existing bug in a browser, and
        return True.
        '''
        if not self.crashdb.accepts(self.report):
            return False
        if '_KnownReport' not in self.report:
            return False

        # if we have an URL, open it; otherwise this is just a marker that we
        # know about it
        if self.report['_KnownReport'].startswith('http'):
            self.ui_info_message(_('Problem already known'),
                                 _('This problem was already reported in the bug report displayed \
in the web browser. Please check if you can add any further information that \
might be helpful for the developers.'))

            self.open_url(self.report['_KnownReport'])
        else:
            self.ui_info_message(_('Problem already known'),
                                 _('This problem was already reported to developers. Thank you!'))

        return True

    def add_extra_tags(self):
        '''Add extra tags to report specified with --tags on CLI.'''

        assert self.report
        if self.options.tag:
            tags = self.report.get('Tags', '')
            if tags:
                tags += ' '
            self.report['Tags'] = tags + ' '.join(self.options.tag)

    #
    # abstract UI methods that must be implemented in derived classes
    #

    def ui_present_report_details(self, allowed_to_report=True, modal_for=None):
        '''Show details of the bug report.

        Return the action and options as a dictionary:

        - Valid keys are: report the crash ('report'), restart
          the crashed application ('restart'), or blacklist further crashes
          ('blacklist').
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_info_message(self, title, text):
        '''Show an information message box with given title and text.'''

        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_error_message(self, title, text):
        '''Show an error message box with given title and text.'''

        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_start_info_collection_progress(self):
        '''Open a indefinite progress bar for data collection.

        This tells the user to wait while debug information is being
        collected.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_pulse_info_collection_progress(self):
        '''Advance the data collection progress bar.

        This function is called every 100 ms.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_stop_info_collection_progress(self):
        '''Close debug data collection progress window.'''

        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_start_upload_progress(self):
        '''Open progress bar for data upload.

        This tells the user to wait while debug information is being uploaded.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_set_upload_progress(self, progress):
        '''Update data upload progress bar.

        Set the progress bar in the debug data upload progress window to the
        given ratio (between 0 and 1, or None for indefinite progress).

        This function is called every 100 ms.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_stop_upload_progress(self):
        '''Close debug data upload progress window.'''

        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_shutdown(self):
        '''Called right before terminating the program.

        This can be used for for cleaning up.
        '''
        pass

    def ui_run_terminal(self, command):
        '''Run command in, or check for a terminal window.

        If command is given, run command in a terminal window; raise an exception
        if terminal cannot be opened.

        If command is None, merely check if a terminal application is available
        and can be launched.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    #
    # Additional UI dialogs; these are not required by Apport itself, but can
    # be used by interactive package hooks
    #

    def ui_question_yesno(self, text):
        '''Show a yes/no question.

        Return True if the user selected "Yes", False if selected "No" or
        "None" on cancel/dialog closing.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_question_choice(self, text, options, multiple):
        '''Show an question with predefined choices.

        options is a list of strings to present. If multiple is True, they
        should be check boxes, if multiple is False they should be radio
        buttons.

        Return list of selected option indexes, or None if the user cancelled.
        If multiple == False, the list will always have one element.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_question_file(self, text):
        '''Show a file selector dialog.

        Return path if the user selected a file, or None if cancelled.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')

    def ui_question_userpass(self, message):
        '''Request username and password from user.

        message is the text to be presented to the user when requesting for
        username and password information.

        Return a tuple (username, password), or None if cancelled.
        '''
        raise NotImplementedError('this function must be overridden by subclasses')


class HookUI:
    '''Interactive functions which can be used in package hooks.

    This provides an interface for package hooks which need to ask interactive
    questions. Directly passing the UserInterface instance to the hooks needs
    to be avoided, since we need to call the UI methods in a different thread,
    and also don't want hooks to be able to poke in the UI.
    '''
    def __init__(self, ui):
        '''Create a HookUI object.

        ui is the UserInterface instance to wrap.
        '''
        self.ui = ui

        # variables for communicating with the UI thread
        self._request_event = threading.Event()
        self._response_event = threading.Event()
        self._request_fn = None
        self._request_args = None
        self._response = None

    #
    # API for hooks
    #

    def information(self, text):
        '''Show an information with OK/Cancel buttons.

        This can be used for asking the user to perform a particular action,
        such as plugging in a device which does not work.
        '''
        return self._trigger_ui_request('ui_info_message', '', text)

    def yesno(self, text):
        '''Show a yes/no question.

        Return True if the user selected "Yes", False if selected "No" or
        "None" on cancel/dialog closing.
        '''
        return self._trigger_ui_request('ui_question_yesno', text)

    def choice(self, text, options, multiple=False):
        '''Show an question with predefined choices.

        options is a list of strings to present. If multiple is True, they
        should be check boxes, if multiple is False they should be radio
        buttons.

        Return list of selected option indexes, or None if the user cancelled.
        If multiple == False, the list will always have one element.
        '''
        return self._trigger_ui_request('ui_question_choice', text, options, multiple)

    def file(self, text):
        '''Show a file selector dialog.

        Return path if the user selected a file, or None if cancelled.
        '''
        return self._trigger_ui_request('ui_question_file', text)

    #
    # internal API for inter-thread communication
    #

    def _trigger_ui_request(self, fn, *args):
        '''Called by HookUi functions in info collection thread.'''

        # only one at a time
        assert not self._request_event.is_set()
        assert not self._response_event.is_set()
        assert self._request_fn is None

        self._response = None
        self._request_fn = fn
        self._request_args = args
        self._request_event.set()
        self._response_event.wait()

        self._request_fn = None
        self._response_event.clear()

        return self._response

    def process_event(self):
        '''Called by GUI thread to check and process hook UI requests.'''

        # sleep for 0.1 seconds to wait for events
        self._request_event.wait(0.1)
        if not self._request_event.is_set():
            return

        assert not self._response_event.is_set()
        self._request_event.clear()
        self._response = getattr(self.ui, self._request_fn)(*self._request_args)
        self._response_event.set()
