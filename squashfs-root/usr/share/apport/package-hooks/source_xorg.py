#!/usr/bin/python3

'''Xorg Apport interface

Copyright (C) 2007-2012 Canonical Ltd.
Author: Bryce Harrington <bryce@canonical.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 2 of the License, or (at your
option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
the full text of the license.

Testing:  APPORT_STAGING="yes"
'''

from __future__ import absolute_import, print_function, unicode_literals

import re
import sys
import glob
import os.path
import subprocess
from apport.hookutils import *

has_xorglog = False
try:
    from xdiagnose.xorglog import XorgLog
    has_xorglog = True
except ImportError:
    pass

has_launchpad = False
try:
    from launchpadlib.launchpad import Launchpad
    has_launchpad = True
except ImportError:
    pass

core_x_packages = [
    'xorg', 'xorg-server', 'xserver-xorg-core', 'mesa'
    ]
video_packages = [
    'xserver-xorg-video-intel', 'xserver-xorg-video-nouveau', 'xserver-xorg-video-ati',
    ]
opt_debug = False

######
#
# Apport helper routines
#
######
def debug(text):
    if opt_debug:
        sys.stderr.write("%s\n" %(text))

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def retrieve_ubuntu_release_statuses():
    '''
    Attempts to access launchpad to get a mapping of Ubuntu releases to status.

    Returns a dictionary of ubuntu release keywords to their current status,
    or None in case of a failure reading launchpad.
    '''
    releases = { }
    if not has_launchpad:
        return None
    try:
        lp = Launchpad.login_anonymously('apport', 'production')
        d = lp.distributions['ubuntu']
        for series in d.series:
            releases[series.name] = series.status
    except:
        releases = None
    return releases

def installed_version(pkg):
    '''
    Queries apt for the version installed at time of filing
    '''
    script = subprocess.Popen(['apt-cache', 'policy', pkg], stdout=subprocess.PIPE)
    output = script.communicate()[0]
    return output.split('\n')[1].replace("Installed: ", "")

def is_process_running(proc):
    '''
    Determine if process has a registered process id
    '''
    log = command_output(['pidof', proc])
    if not log or log[:5] == "Error" or len(log)<1:
        return False
    return True

def is_xorg_keyboard_package(pkg):
    if (pkg == 'xkeyboard-config' or
        pkg == 'xkb-data'):
        return True
    else:
        return False

def is_xorg_input_package(pkg):
    if (is_xorg_keyboard_package(pkg) or
        pkg[:18] == 'xserver-xorg-input' or
        pkg[:10] == 'xf86-input'):
        return True
    else:
        return False

def is_xorg_video_package(pkg):
    if (pkg[:18] == 'xserver-xorg-video' or
        pkg[:6] == 'nvidia' or
        pkg[:10] == 'xf86-video'):
        return True
    else:
        return False

def nonfree_graphics_module(module_list = '/proc/modules'):
    '''
    Check loaded modules to see if a proprietary graphics driver is loaded.
    Return the first such driver found.
    '''
    try:
        mods = [l.split()[0] for l in open(module_list)]
    except IOError:
        return None

    for m in mods:
        if m == "nvidia":
            return m

def attach_command_output(report, command_list, key):
    debug(" %s" %(' '.join(command_list)))
    log = command_output(command_list)
    if not log or log[:5] == "Error":
        return
    report[key] = log

def retval(command_list):
    '''
    Call the command and return the command exit code
    '''
    return subprocess.call(
        command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def ubuntu_variant_name():
    '''
    Detect if system runs kubuntu by looking for kdesudo or ksmserver

    Returns 'ubuntu' or 'kubuntu' as appropriate.
    '''
    if (retval(['which', 'kdesudo']) == 0 and
        retval(['pgrep', '-x', '-u', str(os.getuid()), 'ksmserver']) == 0):
        return "kubuntu"
    else:
        return "ubuntu"

def ubuntu_code_name():
    '''
    Return the LSB ubuntu release code name, 'dapper', 'natty', etc.
    '''
    debug(" lsb_release -sc")
    code_name = command_output(['lsb_release','-sc'])
    if code_name[:5] == "Error":
        return None
    return code_name

######
#
# Supportability tests
#
######

def check_is_supported(report, ui=None):
    '''
    Bug reports against the development release are higher priority than
    ones filed against already released versions.  We steer reporters of
    the latter towards technical support resources, which are better geared
    for helping end users solve problems with their installations.
    '''
    distro_codename = ubuntu_code_name()
    report['DistroCodename'] = distro_codename
    report['DistroVariant'] = ubuntu_variant_name()
    report['Tags'] += ' ' + report['DistroVariant']

    if not ui:
        return

    # Look up status of this and other releases
    release_status = retrieve_ubuntu_release_statuses()
    if not release_status or not report['DistroCodename']:
        # Problem accessing launchpad, can't tell anything about status
        # so assume by default that it's supportable.
        return True
    status = release_status.get(distro_codename, "Unknown")

    if status == "Active Development":
        # Allow user to set flags for things that may help prioritize support
        response = ui.choice(
            "Thank you for testing the '%s' development version of Ubuntu.\n"
            "You may mark any of the following that apply to help us better\n"
            "process your issue." %(distro_codename),
            [
                "Regression",
                "Has happened more than once",
                "I can reproduce the bug",
                "I know a workaround",
                "I know the fix for this",
                ],
            multiple=True
            )
        if response == None:
            return False
        if 0 in response:
            # TODO: Prompt for what type of regression and when it started
            # Perhaps parse dpkg.log for update dates
            report['Tags'] += ' regression'
        if 1 not in response:
            report['Tags'] += ' single-occurrence'
        if 2 in response:
            report['Tags'] += ' reproducible'
        if 3 in response:
            report['Tags'] += ' has-workaround'
        if 4 in response:
            report['Tags'] += ' has-fix'
        return True

    elif status == "Obsolete":
        ui.information("Sorry, the '%s' version of Ubuntu is obsolete, which means the developers no longer accept bug reports about it." %(distro_codename))
        report['UnreportableReason'] = 'Unsupported Ubuntu Release'
        return False

    return True

def check_is_reportable(report, ui=None):
    '''Checks system to see if there is any reason the configuration is not
    valid for filing bug reports'''

    version_signature = report.get('ProcVersionSignature', '')
    if version_signature and not version_signature.startswith('Ubuntu '):
        report['UnreportableReason'] = 'The running kernel is not an Ubuntu kernel: %s' %version_signature
        return False

    bios = report.get('dmi.bios.version', '')
    if bios.startswith('VirtualBox '):
        report['SourcePackage'] = "virtualbox-ose"
        return False

    product_name = report.get('dmi.product.name', '')
    if product_name.startswith('VMware '):
        report['UnreportableReason'] = 'VMware is installed.  If you upgraded X recently be sure to upgrade vmware to a compatible version.'
        return False

    if os.path.exists('/var/log/nvidia-installer.log'):
        # User has installed nVidia drivers manually at some point.
        # This can cause problems, although the packaging scripts should prevent this situation now.
        attach_file(report, '/var/log/nvidia-installer.log', 'nvidia-installer.log')
        report['Tags'] += ' ' + 'possible-manual-nvidia-install'

    return True

######
#
# Attach relevant data files
#
######

def attach_dkms_info(report, ui=None):
    '''
    DKMS is the dynamic kernel module service, for rebuilding modules
    against a new kernel on the fly, during boot.  Occasionally this fails
    such as when installing/upgrading with proprietary video drivers.
    '''
    if os.path.lexists('/var/lib/dkms'):
        # Gather any dkms make.log files for proprietary drivers
        for logfile in glob.glob("/var/lib/dkms/*/*/build/make.log"):
            attach_file(report, logfile, "make.log")
        attach_command_output(report, ['dkms', 'status'], 'DkmsStatus')

def attach_dist_upgrade_status(report, ui=None):
    '''
    This routine indicates whether a system was upgraded from a prior
    release of ubuntu, or was a fresh install of this release.
    '''
    attach_file_if_exists(report, "/var/log/dpkg.log", "DpkgLog")
    if os.path.lexists('/var/log/dist-upgrade/main.log'):
        attach_command_output(
            report,
            ['tail', '-n', '1', '/var/log/dist-upgrade/main.log'],
            'DistUpgraded')
        return True
    else:
        report['DistUpgraded'] = 'Fresh install'
        return False

def attach_graphic_card_pci_info(report, ui=None):
    '''
    Extracts the device system and subsystem IDs for the video card.
    Note that the user could have multiple video cards installed, so
    this may return a multi-line string.
    '''
    info = ''
    display_pci = pci_devices(PCI_DISPLAY)
    for paragraph in display_pci.split('\n\n'):
        for line in paragraph.split('\n'):
            if ':' not in line:
                continue
            m = re.match(r'(.*?):\s(.*)', line)
            if not m:
                continue
            key, value = m.group(1), m.group(2)
            value = value.strip()
            key = key.strip()
            if "VGA compatible controller" in key:
                info += "%s\n" % (value)
            elif key == "Subsystem":
                info += "  %s: %s\n" %(key, value)
    report['GraphicsCard'] = info

def attach_xorg_package_versions(report, ui=None):
    '''
    Gathers versions for various X packages of interest
    '''
    for package in [
        "xserver-xorg-core",
        "libgl1-mesa-glx",
        "libgl1-mesa-dri",
        "libdrm2",
        "compiz",
        "xserver-xorg-input-evdev",
        "xserver-xorg-video-intel",
        "xserver-xorg-video-ati",
        "xserver-xorg-video-nouveau"]:
        report['version.%s' %(package)] = package_versions(package)

def attach_xorg_info(report, ui=None):
    '''
    Attaches basic xorg debugging info
    '''
    from pathlib import Path
    HomeXorgLog = os.path.join(str(Path.home()), '.local/share/xorg/Xorg.0.log')

    attach_file_if_exists(report, '/var/log/boot.log', 'BootLog')
    attach_file_if_exists(report, '/var/log/plymouth-debug.log', 'PlymouthDebug')
    attach_file_if_exists(report, '/etc/X11/xorg.conf', 'XorgConf')
    if os.path.exists(HomeXorgLog) :
        attach_file_if_exists(report, HomeXorgLog, 'XorgLog')
        attach_file_if_exists(report, HomeXorgLog + '.old', 'XorgLogOld')
    else:
        attach_file_if_exists(report, '/var/log/Xorg.0.log', 'XorgLog')
        attach_file_if_exists(report, '/var/log/Xorg.0.log.old', 'XorgLogOld')

    if os.path.lexists('/var/log/Xorg.0.log') and has_xorglog:
        try:
            xlog = XorgLog('/var/log/Xorg.0.log')
            report['xserver.bootTime'] = xlog.boot_time
            report['xserver.version'] = xlog.xserver_version
            report['xserver.logfile'] = xlog.boot_logfile
            report['xserver.devices'] = xlog.devices_table()
            report['xserver.outputs'] = xlog.outputs_table()
            report['xserver.configfile'] = str(xlog.xorg_conf_path)
            report['xserver.errors'] = "\n".join(xlog.errors_filtered())
            if xlog.video_driver is not None:
                report['xserver.video_driver'] = xlog.video_driver.lower()
        except:
            # The parser can fail if the log file has invalid characters (e.g. funky EDID)
            pass

    if ui:
        display_manager_files = {}
        if os.path.lexists('/var/log/lightdm'):
            display_manager_files['LightdmLog'] = 'cat /var/log/lightdm/lightdm.log'
            display_manager_files['LightdmDisplayLog'] = 'cat /var/log/lightdm/x-0.log'
            display_manager_files['LightdmGreeterLog'] = 'cat /var/log/lightdm/x-0-greeter.log'
            display_manager_files['LightdmGreeterLogOld'] = 'cat /var/log/lightdm/x-0-greeter.log.old'

        if ui.yesno("Your display manager log files may help developers diagnose the bug, but may contain sensitive information such as your hostname.  Do you want to include these logs in your bug report?") == True:
            attach_root_command_outputs(report, display_manager_files)

def attach_2d_info(report, ui=None):
    '''
    Attaches various data for debugging modesetting and graphical issues.
    '''
    if os.environ.get('DISPLAY'):
        # For resolution/multi-head bugs
        attach_command_output(report, ['xrandr', '--verbose'], 'Xrandr')
        attach_file_if_exists(report,
                              os.path.expanduser('~/.config/monitors.xml'),
                              'MonitorsUser.xml')
        attach_file_if_exists(report,
                              '/etc/gnome-settings-daemon/xrandr/monitors.xml',
                              'MonitorsGlobal.xml')

        # For font dpi bugs
        attach_command_output(report, ['xdpyinfo'], 'xdpyinfo')

def attach_3d_info(report, ui=None):
    # How are the alternatives set?
    attach_command_output(report, ['ls','-l','/etc/alternatives/gl_conf'], 'GlAlternative')

    # Detect software rasterizer
    xorglog = report.get('XorgLog', '')
    if type(xorglog) is str:
        xorglog = xorglog.encode('utf-8')
    if len(xorglog)>0:
        if b'reverting to software rendering' in xorglog:
            report['Renderer'] = 'Software'
        elif b'Direct rendering disabled' in xorglog:
            report['Renderer'] = 'Software'

    if ui and report.get('Renderer', '') == 'Software':
        ui.information("Your system is providing 3D via software rendering rather than hardware rendering.  This is a compatibility mode which should display 3D graphics properly but the performance may be very poor.  If the problem you're reporting is related to graphics performance, your real question may be why X didn't use hardware acceleration for your system.")

    # Plugins
    attach_command_output(report, [
        'gconftool-2', '--get', '/apps/compiz-1/general/screen0/options/active_plugins'],
        'CompizPlugins')

    # User configuration
    attach_command_output(report, [
        'gconftool-2', '-R', '/apps/compiz-1'],
        'GconfCompiz')

    # Compiz internal state if compiz crashed
    if report.get('SourcePackage','Unknown') == "compiz" and "ProcStatus" in report:
        compiz_pid = 0
        pid_line = re.search("Pid:\t(.*)\n", report["ProcStatus"])
        if pid_line:
            compiz_pid = pid_line.groups()[0]
        compiz_state_file = '/tmp/compiz_internal_state%s' % compiz_pid
        attach_file_if_exists(report, compiz_state_file, "compiz_internal_states")

    # Remainder of this routine requires X running
    if not os.environ.get('DISPLAY'):
        return

    # Unity test
    if os.path.lexists('/usr/lib/nux/unity_support_test'):
        try:
            debug(" unity_support_test")
            ust = command_output([
                '/usr/lib/nux/unity_support_test', '-p', '-f'])
            ust = ust.replace('\x1b','').replace('[0;38;48m','').replace('[1;32;48m','')
            report['UnitySupportTest'] = ust
        except AssertionError:
            report['UnitySupportTest'] = 'FAILED TO RUN'
        for testcachefile in glob.glob('/tmp/unity*'):
            attach_file(report, testcachefile)

    attach_file_if_exists(report,
                          os.path.expanduser('~/.drirc'),
                          'drirc')

    if (is_process_running('compiz') or
        (report.get('SourcePackage','Unknown') == "compiz" and report.get('ProblemType', '') == 'Crash')
        ):
        report['CompositorRunning'] = 'compiz'

        # Compiz Version
        compiz_version = command_output(['compiz', '--version'])
        if compiz_version:
            version = compiz_version.split(' ')[1]
            version = version[:3]
            if is_number(version):
                compiz_version_string = 'compiz-%s' % version
                report['Tags'] += ' ' + compiz_version_string

        # Fullscreen Window Unredirection settings
        report['CompositorUnredirectFSW'] = command_output(
            ['gsettings','get','org.compiz.composite:/org/compiz/', 'unredirect-fullscreen-windows']
            )
        report['CompositorUnredirectDriverBlacklist'] = command_output(
            ['gsettings','get','org.compiz.opengl:/org/compiz/', 'unredirect-driver-blacklist']
            )
    elif is_process_running('kwin'):
        report['CompositorRunning'] = 'kwin'
    else:
        report['CompositorRunning'] = 'None'

def attach_input_device_info(report, ui=None):
    '''
    Gathers data for debugging keyboards, mice, and other input devices.
    '''
    # Only collect the following data if X11 is available
    if not os.environ.get('DISPLAY'):
        return

    # For input device bugs
    attach_command_output(report, ['xinput', '--list'], 'xinput')
    attach_command_output(report, ['gconftool-2', '-R', '/desktop/gnome/peripherals'], 'peripherals')

    # For keyboard bugs only
    if is_xorg_keyboard_package(report.get('SourcePackage','Unknown')):
        attach_command_output(report, ['setxkbmap', '-print'], 'setxkbmap')
        attach_command_output(report, ['xkbcomp', ':0', '-w0', '-'], 'xkbcomp')
        attach_command_output(report, ['locale'], 'locale')
        if ui and ui.yesno("Your kernel input device details (lsinput and dmidecode) may be useful to the developers, but gathering it requires admin privileges. Would you like to include this info?") == True:
            attach_root_command_outputs(report, {
                'lsinput.txt': 'lsinput',
                'dmidecode.txt': 'dmidecode',
                })

def attach_nvidia_info(report, ui=None):
    '''
    Gathers special files for the nvidia proprietary driver
    '''
    # Attach information for upstreaming nvidia binary bugs
    if nonfree_graphics_module() != 'nvidia':
        return

    report['version.nvidia-graphics-drivers'] = package_versions("nvidia-graphics-drivers-*")

    for logfile in glob.glob('/proc/driver/nvidia/*'):
        if os.path.isfile(logfile):
            attach_file_if_exists(report, logfile)

    for logfile in glob.glob('/proc/driver/nvidia/*/*'):
        if os.path.basename(logfile) != 'README':
            attach_file_if_exists(report, logfile)

    if os.path.exists('/usr/bin/nvidia-bug-report.sh'):
        if (ui and (ui.yesno("Would you like to generate and attach an NVIDIA bug reporting file? (~/nvidia-bug-report.log.gz)") == True)):
            attach_root_command_outputs(report, {
                    'NvidiaBugReportLog': 'nvidia-bug-report.sh',
                })
            attach_file_if_exists(report, os.path.expanduser('~/nvidia-bug-report.log.gz'),
                                  'nvidia-bug-report.log.gz')

    if os.environ.get('DISPLAY'):
        # Attach output of nvidia-settings --query if we've got a display
        # to connect to.
        attach_command_output(report, ['nvidia-settings', '-q', 'all'], 'nvidia-settings')

    attach_command_output(report, ['jockey-text', '-l'], 'JockeyStatus')
    attach_command_output(report, ['update-alternatives', '--display', 'gl_conf'], 'GlConf')

    # File any X crash with -nvidia involved with the -nvidia bugs
    if (report.get('ProblemType', '') == 'Crash' and 'Traceback' not in report):
        if report.get('SourcePackage','Unknown') in core_x_packages:
            report['SourcePackage'] = "nvidia-graphics-drivers"

def attach_gpu_hang_info(report, ui):
    '''
    Surveys reporter for some additional clarification on GPU freezes
    '''
    if not ui:
        return
    if not 'freeze' in report['Tags']:
        return

    if not ui.yesno("Did your system recently lock up and/or require a hard reboot?"):
        # If user isn't experiencing freeze symptoms, the remaining questions aren't relevant
        report['Tags'] += ' false-gpu-hang'
        report['Title'] = report['Title'].replace('GPU lockup', 'False GPU lockup')
        return

    text = 'How frequently have you been experiencing lockups like this?'
    choices = [
        "I don't know",
        "This is the first time",
        "Very infrequently",
        "Once a week",
        "Several times a week",
        "Several times a day",
        "Continuously",
        ]
    response = ui.choice(text, choices)
    if response == None:
        raise StopIteration
    report['GpuHangFrequency'] = choices[response[0]]

    # Don't ask more questions if bug is infrequent
    if response[0] < 3:
        return

    text = "When did you first start experiencing these lockups?"
    choices = [
        "I don't know",
        "Since before I upgraded",
        "Immediately after installing this version of Ubuntu",
        "Since a couple weeks or more",
        "Within the last week or two",
        "Within the last few days",
        "Today",
        ]
    response = ui.choice(text, choices)
    if response == None:
        raise StopIteration
    report['GpuHangStarted'] = choices[response[0]]

    text = "Are you able to reproduce the lockup at will?"
    choices = [
        "I don't know",
        "Seems to happen randomly",
        "Occurs more often under certain circumstances",
        "Yes, I can easily reproduce it",
        ]
    response = ui.choice(text, choices)
    if response == None:
        raise StopIteration
    report['GpuHangReproducibility'] = choices[response[0]]

def attach_debugging_interest_level(report, ui):
    if not ui:
        return

    if (report.get('SourcePackage','Unknown') in core_x_packages or
        report.get('SourcePackage','Unknown') in video_packages):
        text = "Would you be willing to do additional debugging work?"
        choices = [
            "I don't know",
            "No",
            "I just need to know a workaround",
            "Yes, if not too technical",
            "Yes",
            "Yes, including running git bisection searches",
            ]
        response = ui.choice(text, choices)
        if response == None:
            raise StopIteration
        choice = response[0]
        if choice>0:
            report['ExtraDebuggingInterest'] = choices[choice]

def add_info(report, ui):
    report.setdefault('Tags', '')

    # Verify the bug is valid to be filed
    if check_is_reportable(report, ui) == False:
        return False
    if check_is_supported(report, ui) == False:
        return False

    debug("attach_gpu_hang_info")
    attach_gpu_hang_info(report, ui)
    debug("attach_xorg_package_versions")
    attach_xorg_package_versions(report, ui)
    debug("attach_dist_upgrade_status")
    attach_dist_upgrade_status(report, ui)
    try:
        debug("attach_hardware")
        attach_hardware(report)
    except:
        debug("Failed to attach hardware.")
    debug("attach_xorg_info")
    attach_xorg_info(report, ui)

    pkg = report.get('SourcePackage','Unknown')
    if is_xorg_input_package(pkg):
        debug("attach_input_device_info")
        attach_input_device_info(report, ui)
    else:
        debug("attach_graphic_card_pci_info")
        attach_graphic_card_pci_info(report, ui)
        debug("attach_dkms_info")
        attach_dkms_info(report, ui)
        debug("attach_nvidia_info")
        attach_nvidia_info(report, ui)
        debug("attach_2d_info")
        attach_2d_info(report, ui)
        debug("attach_3d_info")
        attach_3d_info(report, ui)

    debug("attach_debugging_interest_level")
    attach_debugging_interest_level(report, ui)
    return True

## DEBUGING ##
if __name__ == '__main__':
    import sys

    opt_debug = True

    report = {}
    if not add_info(report, None):
        print("Unreportable bug")
        sys.exit(1)
    for key in report:
        print('[%s]\n%s' % (key, report[key]))
