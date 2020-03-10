'''Apport package hook for the Linux kernel.

(c) 2008 Canonical Ltd.
Contributors:
Matt Zimmerman <mdz@canonical.com>
Martin Pitt <martin.pitt@canonical.com>
Brian Murray <brian@canonical.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.
'''

import os.path, re
import apport
import apport.hookutils

SUBMIT_SCRIPT = "/usr/bin/kerneloops-submit"


def add_info(report, ui):

    # If running an upstream kernel, instruct reporter to file bug upstream
    abi = re.search("-(.*?)-", report['Uname'])
    if abi and (abi.group(1) == '999' or re.search("^0\d", abi.group(1))):
        ui.information("It appears you are currently running a mainline kernel.  It would be better to report this bug upstream at http://bugzilla.kernel.org/ so that the upstream kernel developers are aware of the issue.  If you'd still like to file a bug against the Ubuntu kernel, please boot with an official Ubuntu kernel and re-file.")
        report['UnreportableReason'] = 'The running kernel is not an Ubuntu kernel'
        return

    version_signature = report.get('ProcVersionSignature', '')
    if not version_signature.startswith('Ubuntu ') and 'CrashDB' not in report:
        report['UnreportableReason'] = 'The running kernel is not an Ubuntu kernel'
        return

    # Prevent reports against the linux-meta and linux-signed families, redirect to the main package.
    for src_pkg in ['linux-meta', 'linux-signed']:
        if report['SourcePackage'].startswith(src_pkg):
            report['SourcePackage'] = report['SourcePackage'].replace(src_pkg, 'linux', 1)

    report.setdefault('Tags', '')

    # Tag up back ported kernel reports for easy identification
    if report['SourcePackage'].startswith('linux-lts-'):
        report['Tags'] += ' qa-kernel-lts-testing'

    apport.hookutils.attach_hardware(report)
    apport.hookutils.attach_alsa(report)
    apport.hookutils.attach_wifi(report)
    apport.hookutils.attach_file(report, '/proc/fb', 'ProcFB')

    staging_drivers = re.findall("(\w+): module is from the staging directory",
                                 report['CurrentDmesg'])
    if staging_drivers:
        staging_drivers = list(set(staging_drivers))
        report['StagingDrivers'] = ' '.join(staging_drivers)
        report['Tags'] += ' staging'
        # Only if there is an existing title prepend '[STAGING]'.
        # Changed to prevent bug titles with just '[STAGING] '.
        if report.get('Title'):
            report['Title'] = '[STAGING] ' + report.get('Title')

    apport.hookutils.attach_file_if_exists(report, "/etc/initramfs-tools/conf.d/resume", key="HibernationDevice")

    uname_release = os.uname()[2]
    lrm_package_name = 'linux-restricted-modules-%s' % uname_release
    lbm_package_name = 'linux-backports-modules-%s' % uname_release

    apport.hookutils.attach_related_packages(report, [lrm_package_name, lbm_package_name, 'linux-firmware'])

    if ('Failure' in report and report['Failure'] == 'oops' and
            'OopsText' in report and os.path.exists(SUBMIT_SCRIPT)):
        # tag kerneloopses with the version of the kerneloops package
        apport.hookutils.attach_related_packages(report, ['kerneloops-daemon'])
        oopstext = report['OopsText']
        dupe_sig1 = None
        dupe_sig2 = None
        for line in oopstext.splitlines():
            if line.startswith('BUG:'):
                bug = re.compile('at [0-9a-f]+$')
                dupe_sig1 = bug.sub('at location', line)
            rip = re.compile('^[RE]?IP:')
            if re.search(rip, line):
                loc = re.compile('\[<[0-9a-f]+>\]')
                dupe_sig2 = loc.sub('location', line)
        if dupe_sig1 and dupe_sig2:
            report['DuplicateSignature'] = '%s %s' % (dupe_sig1, dupe_sig2)
        # it's from kerneloops, ask the user whether to submit there as well
        if ui:
            # Some OopsText begin with "--- [ cut here ] ---", so remove it
            oopstext = re.sub("---.*\n", "", oopstext)
            first_line = re.match(".*\n", oopstext)
            ip = re.search("(R|E)?IP\:.*\n", oopstext)
            kernel_driver = re.search("(R|E)?IP(:| is at) .*\[(.*)\]\n", oopstext)
            call_trace = re.search("Call Trace(.*\n){,10}", oopstext)
            oops = ''
            if first_line:
                oops += first_line.group(0)
            if ip:
                oops += ip.group(0)
            if call_trace:
                oops += call_trace.group(0)
            if kernel_driver:
                report['Tags'] += ' kernel-driver-%s' % kernel_driver.group(3)
            # 2012-01-13 - disable submission question as kerneloops.org is
            #   down
            # if ui.yesno("This report may also be submitted to "
            #     "http://kerneloops.org/ in order to help collect aggregate "
            #     "information about kernel problems. This aids in identifying "
            #     "widespread issues and problematic areas. A condensed "
            #     "summary of the Oops is shown below.  Would you like to submit "
            #     "information about this crash to kerneloops.org?"
            #     "\n\n%s" % oops):
            #     text = report['OopsText']
            #     proc = subprocess.Popen(SUBMIT_SCRIPT, stdin=subprocess.PIPE)
            #     proc.communicate(text)
    elif 'Failure' in report and ('resume' in report['Failure'] or
                                  'suspend' in report['Failure']):
        crash_signature = report.crash_signature()
        if crash_signature:
            report['DuplicateSignature'] = crash_signature

    if report.get('ProblemType') == 'Package':
        # in case there is a failure with a grub script
        apport.hookutils.attach_related_packages(report, ['grub-pc'])


if __name__ == '__main__':
    r = apport.Report()
    r.add_proc_info()
    r.add_os_info()
    r['ProcVersionSignature'] = 'Ubuntu 3.4.0'
    add_info(r, None)
    for k, v in r.items():
        print('%s: %s' % (k, v))
