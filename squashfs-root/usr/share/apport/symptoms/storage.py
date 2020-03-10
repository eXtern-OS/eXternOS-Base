# Storage device related problems
# Author: Martin Pitt <martin.pitt@ubuntu.com>
# (C) 2009 Canonical Ltd.
# License: GPL v2 or later.

from glob import glob
import subprocess
import apport.hookutils
import time
import os

description = 'External or internal storage devices (e. g. USB sticks)'

def run(report, ui):
    problem = ui.choice('What particular problem do you observe?',
        ['Removable storage device is not mounted automatically',
         'Internal hard disk partition cannot be mounted manually',
         'Internal hard disk partition is not displayed in Places menu',
         'No permission to access files on storage device',
         'Documents cannot be opened in desktop UI on storage device',
         'Other problem',
        ])

    if problem is None:
        raise StopIteration
    problem = problem[0]

    if problem == 0:
        return problem_removable(report, ui)
    if problem == 1:
        report['Title'] = 'Internal hard disk partition cannot be mounted manually'
        return 'udisks2'
    if problem == 2:
        report['Title'] = 'Internal hard disk partition is not displayed in Places menu'
        return get_desktop_vfs(ui)
    if problem == 3:
        return problem_permission(report, ui)
    if problem == 4:
        report['Title'] = 'Documents cannot be opened in desktop UI on storage device'
        return get_desktop_vfs(ui)
    if problem == 5:
        ui.information('Please use "ubuntu-bug <packagename>" to report a bug against the particular package')
        raise StopIteration

    assert False, 'not reached'

def problem_removable(report, ui):
    ui.information('Please disconnect the problematic device now if it is still plugged in.')

    ud_mon = subprocess.Popen(['udisksctl', 'monitor'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    udev_mon = subprocess.Popen(['udevadm', 'monitor', '--udev', '-e'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    try:
        gvfs_mon = subprocess.Popen(['gvfs-mount', '-oi'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
    except OSError:
        gvfs_mon = None
    old_mounts = set(open('/proc/mounts').readlines())
    old_devices = set(glob('/dev/sd*'))

    ui.information('Please connect the problematic device now.')
    time.sleep(10)

    new_mounts = set(open('/proc/mounts').readlines())
    new_devices = set(glob('/dev/sd*'))

    ud_mon.terminate()
    out, err = ud_mon.communicate()
    report['UdisksMonitorLog'] = out
    if err:
        report['UdisksMonitorError'] = err

    udev_mon.terminate()
    out, err = udev_mon.communicate()
    report['UdevMonitorLog'] = out
    if err:
        report['UdevMonitorError'] = err

    if gvfs_mon:
        gvfs_mon.terminate()
        out, err = gvfs_mon.communicate()
        report['GvfsMonitorLog'] = out
        if err:
            report['GvfsMonitorError'] = err

    new_devices = new_devices - old_devices
    new_mounts = new_mounts - old_mounts

    report['HotplugNewDevices'] = ' '.join(new_devices)
    report['HotplugNewMounts'] = '\n'.join(new_mounts)

    apport.hookutils.attach_dmesg(report)

    if not new_devices:
        return apport.packaging.get_kernel_package()

    if new_mounts:
        if ui.yesno('The plugged in device was automounted:\n\n%s\n'
                'Do you still need to report a problem about this?' % report['HotplugNewMounts']):
            return 'udisks2'
        else:
            raise StopIteration

    if 'SUBSYSTEM=block' not in report['UdevMonitorLog']:
        report['Title'] = 'Removable storage device not detected as block device'
        return 'udev'

    report['Title'] = 'Does not detect hotplugged storage device'
    for d in new_devices:
        if 'DEVNAME=' + d not in report['UdevMonitorLog']:
            return 'udev'
        if ' %s\n' % d not in report['UdisksMonitorLog']:
            return 'udisks2'
    return get_desktop_vfs(ui)

def problem_permission(report, ui):
    '''No permission to access files on storage device'''

    report['Title'] = 'No permission to access files on storage device'
    return 'udisks2'

def get_desktop_vfs(ui):
    if subprocess.call(['pgrep', '-u', str(os.getuid()), '-x', 'gnome-session']) == 0:
        return 'gvfs'
    if subprocess.call(['pgrep', '-u', str(os.getuid()), '-x', 'ksmserver']) == 0:
        return 'kdelibs5'

    ui.information('Sorry, you are not running GNOME or KDE. Automounting needs to be provided by your desktop environment.')
    raise StopIteration
