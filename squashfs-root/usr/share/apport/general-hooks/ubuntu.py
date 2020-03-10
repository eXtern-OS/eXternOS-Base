'''Attach generally useful information, not specific to any package.

Copyright (C) 2009 Canonical Ltd.
Authors: Matt Zimmerman <mdz@canonical.com>,
         Brian Murray <brian@ubuntu.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

import re, os, os.path, time, sys, subprocess

import apport.packaging
import apport.hookutils
import problem_report
from apport import unicode_gettext as _
from glob import glob

if sys.version < '3':
    from urlparse import urljoin
    from urllib2 import urlopen
    (urljoin, urlopen)  # pyflakes
else:
    from urllib.parse import urljoin
    from urllib.request import urlopen


def add_info(report, ui):
    add_release_info(report)

    add_kernel_info(report)

    add_cloud_info(report)

    add_proposed_info(report)

    # collect a condensed version of /proc/cpuinfo
    apport.hookutils.attach_file(report, '/proc/cpuinfo',
                                 'ProcCpuinfo')
    short_cpuinfo = []
    for item in reversed(report.get('ProcCpuinfo', '').split('\n')):
        short_cpuinfo.append(item)
        if item.startswith('processor\t:'):
            break
    short_cpuinfo = reversed(short_cpuinfo)
    report['ProcCpuinfoMinimal'] = '\n'.join(short_cpuinfo)
    report.pop('ProcCpuinfo')

    hook_errors = [k for k in report.keys() if k.startswith('HookError_')]
    if hook_errors:
        add_tag(report, 'apport-hook-error')

    # locally installed python versions can cause a multitude of errors
    if report.get('ProblemType') == 'Package' or \
            'python' in report.get('InterpreterPath', '') or \
            'python' in report.get('ExecutablePath', ''):
        for python in ('python', 'python3'):
            add_python_details('%sDetails' % python.title(), python, report)

    try:
        report['ApportVersion'] = apport.packaging.get_version('apport')
    except ValueError:
        # might happen on local installs
        pass

    if report.get('ProblemType') == 'Package':
        # every error report regarding a package should have package manager
        # version information
        apport.hookutils.attach_related_packages(report, ['dpkg', 'apt'])
        check_for_disk_error(report)
        # check to see if the real root on a persistent media is full
        if 'LiveMediaBuild' in report:
            st = os.statvfs('/cdrom')
            free_mb = st.f_bavail * st.f_frsize / 1000000
            if free_mb < 10:
                report['UnreportableReason'] = 'Your system partition has less than \
%s MB of free space available, which leads to problems using applications \
and installing updates. Please free some space.' % (free_mb)

    match_error_messages(report)

    for attachment in ['DpkgTerminalLog', 'VarLogDistupgradeApttermlog']:
        if attachment in report:
            log_file = get_attachment_contents(report, attachment)
            untrimmed_dpkg_log = log_file
            check_attachment_for_errors(report, attachment)
            trimmed_log = get_attachment_contents(report, attachment)
            trimmed_log = trimmed_log.split('\n')
            lines = []
            for line in untrimmed_dpkg_log.splitlines():
                if line not in trimmed_log:
                    lines.append(str(line))
                elif line in trimmed_log:
                    trimmed_log.remove(line)
            dpkg_log_without_error = '\n'.join(lines)

    # crash reports from live system installer often expose target mount
    for f in ('ExecutablePath', 'InterpreterPath'):
        if f in report and report[f].startswith('/target/'):
            report[f] = report[f][7:]

    # Allow filing update-manager bugs with obsolete packages
    if report.get('Package', '').startswith('update-manager'):
        os.environ['APPORT_IGNORE_OBSOLETE_PACKAGES'] = '1'

    # file bugs against OEM project for modified packages
    if 'Package' in report:
        v = report['Package'].split()[1]
        oem_project = get_oem_project(report)
        if oem_project and ('common' in v or oem_project in v):
            report['CrashDB'] = 'canonical-oem'

    if 'Package' in report:
        package = report['Package'].split()[0]
        if package:
            apport.hookutils.attach_conffiles(report, package, ui=ui)

        # do not file bugs against "upgrade-system" if it is not installed (LP#404727)
        if package == 'upgrade-system' and 'not installed' in report['Package']:
            report['UnreportableReason'] = 'You do not have the upgrade-system package installed. Please report package upgrade failures against the package that failed to install, or against upgrade-manager.'

    if 'Package' in report:
        package = report['Package'].split()[0]
        if package:
            apport.hookutils.attach_upstart_overrides(report, package)
            apport.hookutils.attach_upstart_logs(report, package)

    # build a duplicate signature tag for package reports
    if report.get('ProblemType') == 'Package':

        if 'DpkgTerminalLog' in report:
            # this was previously trimmed in check_attachment_for_errors
            termlog = report['DpkgTerminalLog']
        elif 'VarLogDistupgradeApttermlog' in report:
            termlog = get_attachment_contents(report, 'VarLogDistupgradeApttermlog')
        else:
            termlog = None
        if termlog:
            (package, version) = report['Package'].split(None, 1)
            # for packages that run update-grub include /etc/default/grub
            UPDATE_BOOT = ['friendly-recovery', 'linux', 'memtest86+',
                           'plymouth', 'ubuntu-meta', 'virtualbox-ose']
            ug_failure = r'/etc/kernel/post(inst|rm)\.d/zz-update-grub exited with return code [1-9]+'
            mkconfig_failure = r'/usr/sbin/grub-mkconfig.*/etc/default/grub: Syntax error'
            if re.search(ug_failure, termlog) or re.search(mkconfig_failure, termlog):
                if report['SourcePackage'] in UPDATE_BOOT:
                    apport.hookutils.attach_default_grub(report, 'EtcDefaultGrub')
            dupe_sig = ''
            dupe_sig_created = False
            # messages we expect to see from a package manager (LP: #1692127)
            pkg_mngr_msgs = re.compile(r"""^(Authenticating|
                                             De-configuring|
                                             Examining|
                                             Installing|
                                             Preparing|
                                             Processing\ triggers|
                                             Purging|
                                             Removing|
                                             Replaced|
                                             Replacing|
                                             Setting\ up|
                                             Unpacking|
                                             Would remove).*
                                         \.\.\.\s*$""", re.X)
            for line in termlog.split('\n'):
                if pkg_mngr_msgs.search(line):
                    dupe_sig = '%s\n' % line
                    dupe_sig_created = True
                    continue
                dupe_sig += '%s\n' % line
                # this doesn't catch 'dpkg-divert: error' LP: #1581399
                if 'dpkg: error' in dupe_sig and line.startswith(' '):
                    if 'trying to overwrite' in line:
                        conflict_pkg = re.search('in package (.*) ', line)
                        if conflict_pkg and not apport.packaging.is_distro_package(conflict_pkg.group(1)):
                            report['UnreportableReason'] = _('An Ubuntu package has a file conflict with a package that is not a genuine Ubuntu package.')
                        add_tag(report, 'package-conflict')
                    if dupe_sig_created:
                        # the duplicate signature should be the first failure
                        report['DuplicateSignature'] = 'package:%s:%s\n%s' % (package, version, dupe_sig)
                        break
                if dupe_sig:
                    if dpkg_log_without_error.find(dupe_sig) != -1:
                        report['UnreportableReason'] = _('You have already encountered this package installation failure.')


def match_error_messages(report):
    # There are enough of these now that it is probably worth refactoring...
    # -mdz
    if report.get('ProblemType') == 'Package':
        if 'failed to install/upgrade: corrupted filesystem tarfile' in report.get('Title', ''):
            report['UnreportableReason'] = 'This failure was caused by a corrupted package download or file system corruption.'

        if 'is already installed and configured' in report.get('ErrorMessage', ''):
            report['SourcePackage'] = 'dpkg'


def check_attachment_for_errors(report, attachment):
    if report.get('ProblemType') == 'Package':
        wrong_grub_msg = _('''Your system was initially configured with grub version 2, but you have removed it from your system in favor of grub 1 without configuring it.  To ensure your bootloader configuration is updated whenever a new kernel is available, open a terminal and run:

      sudo apt-get install grub-pc
''')

        trim_dpkg_log(report)
        log_file = get_attachment_contents(report, attachment)

        if 'DpkgTerminalLog' in report \
           and re.search(r'^Not creating /boot/grub/menu.lst as you wish', report['DpkgTerminalLog'], re.MULTILINE):
            grub_hook_failure = True
        else:
            grub_hook_failure = False

        if report['Package'] not in ['grub', 'grub2']:
            # linux-image postinst emits this when update-grub fails
            # https://wiki.ubuntu.com/KernelTeam/DebuggingUpdateErrors
            grub_errors = [r'^User postinst hook script \[.*update-grub\] exited with value',
                           r'^run-parts: /etc/kernel/post(inst|rm).d/zz-update-grub exited with return code [1-9]+',
                           r'^/usr/sbin/grub-probe: error']

            for grub_error in grub_errors:
                if attachment in report and re.search(grub_error, log_file, re.MULTILINE):
                    # File these reports on the grub package instead
                    grub_package = apport.packaging.get_file_package('/usr/sbin/update-grub')
                    if grub_package is None or grub_package == 'grub' and 'grub-probe' not in log_file:
                        report['SourcePackage'] = 'grub'
                        if os.path.exists('/boot/grub/grub.cfg') and grub_hook_failure:
                            report['UnreportableReason'] = wrong_grub_msg
                    else:
                        report['SourcePackage'] = 'grub2'

        if report['Package'] != 'initramfs-tools':
            # update-initramfs emits this when it fails, usually invoked from the linux-image postinst
            # https://wiki.ubuntu.com/KernelTeam/DebuggingUpdateErrors
            if attachment in report and re.search(r'^update-initramfs: failed for ', log_file, re.MULTILINE):
                # File these reports on the initramfs-tools package instead
                report['SourcePackage'] = 'initramfs-tools'

        if report['Package'] in ['emacs22', 'emacs23', 'emacs-snapshot', 'xemacs21']:
            # emacs add-on packages trigger byte compilation, which might fail
            # we are very interested in reading the compilation log to determine
            # where to reassign this report to
            regex = r'^!! Byte-compilation for x?emacs\S+ failed!'
            if attachment in report and re.search(regex, log_file, re.MULTILINE):
                for line in log_file.split('\n'):
                    m = re.search(r'^!! and attach the file (\S+)', line)
                    if m:
                        path = m.group(1)
                        apport.hookutils.attach_file_if_exists(report, path)

        if report['Package'].startswith('linux-image-') and attachment in report:
            # /etc/kernel/*.d failures from kernel package postinst
            m = re.search(r'^run-parts: (/etc/kernel/\S+\.d/\S+) exited with return code \d+', log_file, re.MULTILINE)
            if m:
                path = m.group(1)
                package = apport.packaging.get_file_package(path)
                if package:
                    report['SourcePackage'] = package
                    report['ErrorMessage'] = m.group(0)
                    if package == 'grub-pc' and grub_hook_failure:
                        report['UnreportableReason'] = wrong_grub_msg
                else:
                    report['UnreportableReason'] = 'This failure was caused by a program which did not originate from Ubuntu'

        error_message = report.get('ErrorMessage')
        corrupt_package = 'This failure was caused by a corrupted package download or file system corruption.'
        out_of_memory = 'This failure was caused by the system running out of memory.'

        if 'failed to install/upgrade: corrupted filesystem tarfile' in report.get('Title', ''):
            report['UnreportableReason'] = corrupt_package

        if 'dependency problems - leaving unconfigured' in error_message:
            report['UnreportableReason'] = 'This failure is a followup error from a previous package install failure.'

        if 'failed to allocate memory' in error_message:
            report['UnreportableReason'] = out_of_memory

        if 'cannot access archive' in error_message:
            report['UnreportableReason'] = corrupt_package

        if re.search(r'(failed to read|failed in write|short read) on buffer copy', error_message):
            report['UnreportableReason'] = corrupt_package

        if re.search(r'(failed to read|failed to write|failed to seek|unexpected end of file or stream)', error_message):
            report['UnreportableReason'] = corrupt_package

        if re.search(r'(--fsys-tarfile|dpkg-deb --control) returned error exit status 2', error_message):
            report['UnreportableReason'] = corrupt_package

        if attachment in report and re.search(r'dpkg-deb: error.*is not a debian format archive', log_file, re.MULTILINE):
            report['UnreportableReason'] = corrupt_package

        if 'is already installed and configured' in report.get('ErrorMessage', ''):
            # there is insufficient information in the data currently gathered
            # so gather more data
            report['SourcePackage'] = 'dpkg'
            report['AptdaemonVersion'] = apport.packaging.get_version('aptdaemon')
            apport.hookutils.attach_file_if_exists(report, '/var/log/dpkg.log', 'DpkgLog')
            apport.hookutils.attach_file_if_exists(report, '/var/log/apt/term.log', 'AptTermLog')
            # gather filenames in /var/crash to see if there is one for dpkg
            reports = glob('/var/crash/*')
            if reports:
                report['CrashReports'] = apport.hookutils.command_output(
                    ['stat', '-c', '%a:%u:%g:%s:%y:%x:%n'] + reports)
            add_tag(report, 'already-installed')


def check_for_disk_error(report):
    devs_to_check = []
    if 'Dmesg.txt' not in report and 'CurrentDmesg.txt' not in report:
        return
    if 'Df.txt' not in report:
        return
    df = report['Df.txt']
    device_error = False
    for line in df:
        line = line.strip('\n')
        if line.endswith('/') or line.endswith('/usr') or line.endswith('/var'):
            # without manipulation it'd look like /dev/sda1
            device = line.split(' ')[0].strip('0123456789')
            device = device.replace('/dev/', '')
            devs_to_check.append(device)
    dmesg = report.get('CurrentDmesg.txt', report['Dmesg.txt'])
    for line in dmesg:
        line = line.strip('\n')
        if 'I/O error' in line:
            # no device in this line
            if 'journal commit I/O error' in line:
                continue
            for dev in devs_to_check:
                if re.search(dev, line):
                    error_device = dev
                    device_error = True
                    break
    if device_error:
        report['UnreportableReason'] = 'This failure was caused by a hardware error on /dev/%s' % error_device


def add_kernel_info(report):
    # This includes the Ubuntu packaged kernel version
    apport.hookutils.attach_file_if_exists(report, '/proc/version_signature', 'ProcVersionSignature')


def add_release_info(report):
    # https://bugs.launchpad.net/bugs/364649
    media = '/var/log/installer/media-info'
    apport.hookutils.attach_file_if_exists(report, media, 'InstallationMedia')

    # if we are running from a live system, add the build timestamp
    apport.hookutils.attach_file_if_exists(
        report, '/cdrom/.disk/info', 'LiveMediaBuild')
    if os.path.exists('/cdrom/.disk/info'):
        report['CasperVersion'] = apport.packaging.get_version('casper')

    # https://wiki.ubuntu.com/FoundationsTeam/Specs/OemTrackingId
    apport.hookutils.attach_file_if_exists(
        report, '/var/lib/ubuntu_dist_channel', 'DistributionChannelDescriptor')

    release_codename = apport.hookutils.command_output(['lsb_release', '-sc'], stderr=None)
    if release_codename.startswith('Error'):
        release_codename = None
    else:
        add_tag(report, release_codename)

    if os.path.exists(media):
        mtime = os.stat(media).st_mtime
        human_mtime = time.strftime('%Y-%m-%d', time.gmtime(mtime))
        delta = time.time() - mtime
        report['InstallationDate'] = 'Installed on %s (%d days ago)' % (human_mtime, delta / 86400)

    log = '/var/log/dist-upgrade/main.log'
    if os.path.exists(log):
        mtime = os.stat(log).st_mtime
        human_mtime = time.strftime('%Y-%m-%d', time.gmtime(mtime))
        delta = time.time() - mtime

        # Would be nice if this also showed which release was originally installed
        report['UpgradeStatus'] = 'Upgraded to %s on %s (%d days ago)' % (release_codename, human_mtime, delta / 86400)
    else:
        report['UpgradeStatus'] = 'No upgrade log present (probably fresh install)'

    # check for system-image version on phablet builds
    if apport.hookutils.command_available('system-image-cli'):
        report['SystemImageInfo'] = '%s' % apport.hookutils.command_output(
            ['system-image-cli', '-i'], stderr=None)


def add_proposed_info(report):
    '''Tag if package comes from -proposed'''

    if 'Package' not in report:
        return
    try:
        (package, version) = report['Package'].split()[:2]
    except ValueError:
        print('WARNING: malformed Package field: ' + report['Package'])
        return

    apt_cache = subprocess.Popen(['apt-cache', 'showpkg', package],
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
    out = apt_cache.communicate()[0]
    if apt_cache.returncode != 0:
        print('WARNING: apt-cache showpkg %s failed' % package)
        return

    found_proposed = False
    found_updates = False
    found_security = False
    for line in out.splitlines():
        if line.startswith(version + ' ('):
            if '-proposed_' in line:
                found_proposed = True
            if '-updates_' in line:
                found_updates = True
            if '-security' in line:
                found_security = True

    if found_proposed and not found_updates and not found_security:
        add_tag(report, 'package-from-proposed')


def add_cloud_info(report):
    # EC2 and Ubuntu Enterprise Cloud instances
    ec2_instance = False
    for pkg in ('ec2-init', 'cloud-init'):
        try:
            if apport.packaging.get_version(pkg):
                ec2_instance = True
                break
        except ValueError:
            pass
    if ec2_instance:
        metadata_url = 'http://169.254.169.254/latest/meta-data/'
        ami_id_url = urljoin(metadata_url, 'ami-id')

        try:
            ami = urlopen(ami_id_url, timeout=5).read()
        except Exception:
            ami = None

        if ami and ami.startswith(b'ami'):
            add_tag(report, 'ec2-images')
            fields = {'Ec2AMIManifest': 'ami-manifest-path',
                      'Ec2Kernel': 'kernel-id',
                      'Ec2Ramdisk': 'ramdisk-id',
                      'Ec2InstanceType': 'instance-type',
                      'Ec2AvailabilityZone': 'placement/availability-zone'}

            report['Ec2AMI'] = ami
            for key, value in fields.items():
                try:
                    report[key] = urlopen(urljoin(metadata_url, value), timeout=5).read()
                except Exception:
                    report[key] = 'unavailable'
        else:
            add_tag(report, 'uec-images')


def add_tag(report, tag):
    report.setdefault('Tags', '')
    if tag in report['Tags'].split():
        return
    report['Tags'] += ' ' + tag


def get_oem_project(report):
    '''Determine OEM project name from Distribution Channel Descriptor

    Return None if it cannot be determined or does not exist.
    '''
    dcd = report.get('DistributionChannelDescriptor', None)
    if dcd and dcd.startswith('canonical-oem-'):
        return dcd.split('-')[2]
    return None


def trim_dpkg_log(report):
    '''Trim DpkgTerminalLog to the most recent installation session.'''

    if 'DpkgTerminalLog' not in report:
        return
    if not report['DpkgTerminalLog'].strip():
        report['UnreportableReason'] = '/var/log/apt/term.log does not contain any data'
        return
    lines = []
    dpkg_log = report['DpkgTerminalLog']
    if isinstance(dpkg_log, bytes):
        trim_re = re.compile(b'^\(.* ... \d+ .*\)$')
        start_re = re.compile(b'^Log started:')
    else:
        trim_re = re.compile('^\(.* ... \d+ .*\)$')
        start_re = re.compile('^Log started:')
    for line in dpkg_log.splitlines():
        if start_re.match(line) or trim_re.match(line):
            lines = []
            continue
        lines.append(line)
    # If trimming the log file fails, return the whole log file.
    if not lines:
        return
    if isinstance(lines[0], str):
        report['DpkgTerminalLog'] = '\n'.join(lines)
    else:
        report['DpkgTerminalLog'] = '\n'.join([str(line.decode('UTF-8', 'replace')) for line in lines])


def get_attachment_contents(report, attachment):
    if isinstance(report[attachment], problem_report.CompressedValue):
        contents = report[attachment].get_value().decode('UTF-8')
    else:
        contents = report[attachment]
    return contents


def add_python_details(key, python, report):
    '''Add comma separated details about which python is being used'''
    python_path = apport.hookutils.command_output(['which', python])
    if python_path.startswith('Error: '):
        report[key] = 'N/A'
        return
    python_link = apport.hookutils.command_output(['readlink', '-f',
                                                  python_path])
    python_pkg = apport.fileutils.find_file_package(python_path)
    if python_pkg:
        python_pkg_version = apport.packaging.get_version(python_pkg)
    python_version = apport.hookutils.command_output([python_link,
                                                     '--version'])
    data = '%s, %s' % (python_link, python_version)
    if python_pkg:
        data += ', %s, %s' % (python_pkg, python_pkg_version)
    else:
        data += ', unpackaged'
    report[key] = data


if __name__ == '__main__':
    import sys

    # for testing: update report file given on command line
    if len(sys.argv) != 2:
        sys.stderr.write('Usage for testing this hook: %s <report file>\n' % sys.argv[0])
        sys.exit(1)

    report_file = sys.argv[1]

    report = apport.Report()
    with open(report_file, 'rb') as f:
        report.load(f)
    report_keys = set(report.keys())

    new_report = report.copy()
    add_info(new_report, None)

    new_report_keys = set(new_report.keys())

    # Show differences
    # N.B. Some differences will exist if the report file is not from your
    # system because the hook runs against your local system.
    changed = 0
    for key in sorted(report_keys | new_report_keys):
        if key in new_report_keys and key not in report_keys:
            print('+%s: %s' % (key, new_report[key]))
            changed += 1
        elif key in report_keys and key not in new_report_keys:
            print('-%s: (deleted)' % key)
            changed += 1
        elif key in report_keys and key in new_report_keys:
            if report[key] != new_report[key]:
                print('~%s: (changed)' % key)
                changed += 1
    print('%d items changed' % changed)
