'''Functions to manage apport problem report files.'''

# Copyright (C) 2006 - 2009 Canonical Ltd.
# Author: Martin Pitt <martin.pitt@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import os, glob, subprocess, os.path, time, pwd, sys

try:
    from configparser import ConfigParser, NoOptionError, NoSectionError
    (ConfigParser, NoOptionError, NoSectionError)  # pyflakes
except ImportError:
    # Python 2
    from ConfigParser import ConfigParser, NoOptionError, NoSectionError

from problem_report import ProblemReport

from apport.packaging_impl import impl as packaging

report_dir = os.environ.get('APPORT_REPORT_DIR', '/var/crash')

_config_file = '~/.config/apport/settings'


def allowed_to_report():
    '''Check whether crash reporting is enabled.'''

    if not os.access("/usr/bin/whoopsie", os.X_OK):
        return True

    try:
        return subprocess.call(["/bin/systemctl", "-q", "is-enabled", "whoopsie.service"]) == 0
    except OSError:
        return False


def find_package_desktopfile(package):
    '''Return a package's .desktop file.

    If given package is installed and has a single .desktop file, return the
    path to it, otherwise return None.
    '''
    if package is None:
        return None

    desktopfile = None

    for line in packaging.get_files(package):
        if line.endswith('.desktop'):
            # restrict to autostart and applications, see LP#1147528
            if not line.startswith('/etc/xdg/autostart') and not line.startswith('/usr/share/applications/'):
                continue

            if desktopfile:
                return None  # more than one
            else:
                # only consider visible ones
                with open(line, 'rb') as f:
                    if b'NoDisplay=true' not in f.read():
                        desktopfile = line

    return desktopfile


def likely_packaged(file):
    '''Check whether the given file is likely to belong to a package.

    This is semi-decidable: A return value of False is definitive, a True value
    is only a guess which needs to be checked with find_file_package().
    However, this function is very fast and does not access the package
    database.
    '''
    pkg_whitelist = ['/bin/', '/boot', '/etc/', '/initrd', '/lib', '/sbin/',
                     '/opt', '/usr/', '/var']  # packages only ship executables in these directories

    whitelist_match = False
    for i in pkg_whitelist:
        if file.startswith(i):
            whitelist_match = True
            break
    return whitelist_match and not file.startswith('/usr/local/') and not \
        file.startswith('/var/lib/')


def find_file_package(file):
    '''Return the package that ships the given file.

    Return None if no package ships it.
    '''
    # resolve symlinks in directories
    (dir, name) = os.path.split(file)
    resolved_dir = os.path.realpath(dir)
    if os.path.isdir(resolved_dir):
        file = os.path.join(resolved_dir, name)

    if not likely_packaged(file):
        return None

    return packaging.get_file_package(file)


def seen_report(report):
    '''Check whether the report file has already been processed earlier.'''

    st = os.stat(report)
    return (st.st_atime > st.st_mtime) or (st.st_size == 0)


def mark_report_upload(report):
    upload = '%s.upload' % report.rsplit('.', 1)[0]
    uploaded = '%s.uploaded' % report.rsplit('.', 1)[0]
    # if uploaded exists and is older than the report remove it and upload
    if os.path.exists(uploaded) and os.path.exists(upload):
        report_st = os.stat(report)
        upload_st = os.stat(upload)
        if upload_st.st_mtime < report_st.st_mtime:
            os.unlink(upload)
    with open(upload, 'a'):
        pass


def mark_hanging_process(report, pid):
    if 'ExecutablePath' in report:
        subject = report['ExecutablePath'].replace('/', '_')
    else:
        raise ValueError('report does not have the ExecutablePath attribute')

    uid = os.getuid()
    base = '%s.%s.%s.hanging' % (subject, str(uid), pid)
    path = os.path.join(report_dir, base)
    with open(path, 'a'):
        pass


def mark_report_seen(report):
    '''Mark given report file as seen.'''

    st = os.stat(report)
    try:
        os.utime(report, (st.st_mtime, st.st_mtime - 1))
    except OSError:
        # file is probably not our's, so do it the slow and boring way
        # change the file's access time until it stat's different than the mtime.
        # This might take a while if we only have 1-second resolution. Time out
        # after 1.2 seconds.
        timeout = 12
        while timeout > 0:
            f = open(report)
            f.read(1)
            f.close()
            try:
                st = os.stat(report)
            except OSError:
                return

            if st.st_atime > st.st_mtime:
                break
            time.sleep(0.1)
            timeout -= 1

        if timeout == 0:
            # happens on noatime mounted partitions; just give up and delete
            delete_report(report)


def get_all_reports():
    '''Return a list with all report files accessible to the calling user.'''

    reports = []
    for r in glob.glob(os.path.join(report_dir, '*.crash')):
        try:
            if os.path.getsize(r) > 0 and os.access(r, os.R_OK | os.W_OK):
                reports.append(r)
        except OSError:
            # race condition, can happen if report disappears between glob and
            # stat
            pass
    return reports


def get_new_reports():
    '''Get new reports for calling user.

    Return a list with all report files which have not yet been processed
    and are accessible to the calling user.
    '''
    reports = []
    for r in get_all_reports():
        try:
            if not seen_report(r):
                reports.append(r)
        except OSError:
            # race condition, can happen if report disappears between glob and
            # stat
            pass
    return reports


def get_all_system_reports():
    '''Get all system reports.

    Return a list with all report files which belong to a system user (i. e.
    uid < 500 according to LSB).
    '''
    reports = []
    for r in glob.glob(os.path.join(report_dir, '*.crash')):
        try:
            st = os.stat(r)
            if st.st_size > 0 and st.st_uid < 500:
                # filter out guest session crashes; they might have a system UID
                try:
                    pw = pwd.getpwuid(st.st_uid)
                    if pw.pw_name.startswith('guest'):
                        continue
                except KeyError:
                    pass

                reports.append(r)
        except OSError:
            # race condition, can happen if report disappears between glob and
            # stat
            pass
    return reports


def get_new_system_reports():
    '''Get new system reports.

    Return a list with all report files which have not yet been processed
    and belong to a system user (i. e. uid < 500 according to LSB).
    '''
    return [r for r in get_all_system_reports() if not seen_report(r)]


def delete_report(report):
    '''Delete the given report file.

    If unlinking the file fails due to a permission error (if report_dir is not
    writable to normal users), the file will be truncated to 0 bytes instead.
    '''
    try:
        os.unlink(report)
    except OSError:
        with open(report, 'w') as f:
            f.truncate(0)


def get_recent_crashes(report):
    '''Return the number of recent crashes for the given report file.

    Return the number of recent crashes (currently, crashes which happened more
    than 24 hours ago are discarded).
    '''
    pr = ProblemReport()
    pr.load(report, False, key_filter=['CrashCounter', 'Date'])
    try:
        count = int(pr['CrashCounter'])
        report_time = time.mktime(time.strptime(pr['Date']))
        cur_time = time.mktime(time.localtime())
        # discard reports which are older than 24 hours
        if cur_time - report_time > 24 * 3600:
            return 0
        return count
    except (ValueError, KeyError):
        return 0


def make_report_file(report, uid=None):
    '''Construct a canonical pathname for a report and open it for writing

    If uid is not given, it defaults to the uid of the current process.
    The report file must not exist already, to prevent losing previous reports
    or symlink attacks.

    Return an open file object for binary writing.
    '''
    if 'ExecutablePath' in report:
        subject = report['ExecutablePath'].replace('/', '_')
    elif 'Package' in report:
        subject = report['Package'].split(None, 1)[0]
    else:
        raise ValueError('report has neither ExecutablePath nor Package attribute')

    if not uid:
        uid = os.getuid()

    path = os.path.join(report_dir, '%s.%s.crash' % (subject, str(uid)))
    if sys.version >= '3':
        return open(path, 'xb')
    else:
        return os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640), 'wb')


def check_files_md5(sumfile):
    '''Check file integrity against md5 sum file.

    sumfile must be md5sum(1) format (relative to /).

    Return a list of files that don't match.
    '''
    assert os.path.exists(sumfile)
    m = subprocess.Popen(['/usr/bin/md5sum', '-c', sumfile],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd='/', env={})
    out = m.communicate()[0].decode()

    # if md5sum succeeded, don't bother parsing the output
    if m.returncode == 0:
        return []

    mismatches = []
    for l in out.splitlines():
        if l.endswith('FAILED'):
            mismatches.append(l.rsplit(':', 1)[0])

    return mismatches


def get_config(section, setting, default=None, path=None, bool=False):
    '''Return a setting from user configuration.

    This is read from ~/.config/apport/settings or path. If bool is True, the
    value is interpreted as a boolean.
    '''
    if not get_config.config:
        get_config.config = ConfigParser()
        euid = os.geteuid()
        egid = os.getegid()
        try:
            # drop permissions temporarily to try open users config file
            os.seteuid(os.getuid())
            os.setegid(os.getgid())
            if path:
                get_config.config.read(path)
            else:
                get_config.config.read(os.path.expanduser(_config_file))
        finally:
            os.seteuid(euid)
            os.setegid(egid)

    try:
        if bool:
            return get_config.config.getboolean(section, setting)
        else:
            return get_config.config.get(section, setting)
    except (NoOptionError, NoSectionError):
        return default


get_config.config = None


def shared_libraries(path):
    '''Get libraries with which the specified binary is linked.

    Return a library name -> path mapping, for example 'libc.so.6' ->
    '/lib/x86_64-linux-gnu/libc.so.6'.
    '''
    libs = {}

    ldd = subprocess.Popen(['ldd', path], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           universal_newlines=True)
    for line in ldd.stdout:
        try:
            name, rest = line.split('=>', 1)
        except ValueError:
            continue

        name = name.strip()
        # exclude linux-vdso since that is a virtual so
        if 'linux-vdso' in name:
            continue
        # this is usually "path (address)"
        rest = rest.split()[0].strip()
        if rest.startswith('('):
            continue
        libs[name] = rest
    ldd.stdout.close()
    ldd.wait()

    if ldd.returncode != 0:
        return {}
    return libs


def links_with_shared_library(path, lib):
    '''Check if the binary at path links with the library named lib.

    path should be a fully qualified path (e.g. report['ExecutablePath']),
    lib may be of the form 'lib<name>' or 'lib<name>.so.<version>'
    '''
    libs = shared_libraries(path)

    if lib in libs:
        return True

    for linked_lib in libs:
        if linked_lib.startswith(lib + '.so.'):
            return True

    return False
