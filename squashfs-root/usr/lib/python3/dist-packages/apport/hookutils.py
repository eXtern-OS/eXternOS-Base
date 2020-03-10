'''Convenience functions for use in package hooks.'''

# Copyright (C) 2008 - 2012 Canonical Ltd.
# Authors:
#   Matt Zimmerman <mdz@canonical.com>
#   Brian Murray <brian@ubuntu.com>
#   Martin Pitt <martin.pitt@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
# the full text of the license.

import subprocess
import os
import sys
import time
import datetime
import glob
import re
import stat
import base64
import tempfile
import shutil
import locale

from apport.packaging_impl import impl as packaging

import apport
import apport.fileutils

_invalid_key_chars_re = re.compile(r'[^0-9a-zA-Z_.-]')


def path_to_key(path):
    '''Generate a valid report key name from a file path.

    This will replace invalid punctuation symbols with valid ones.
    '''
    if sys.version[0] >= '3':
        if isinstance(path, bytes):
            path = path.decode('UTF-8')
    else:
        if not isinstance(path, bytes):
            path = path.encode('UTF-8')
    return _invalid_key_chars_re.sub('.', path.replace(' ', '_'))


def attach_file_if_exists(report, path, key=None, overwrite=True, force_unicode=False):
    '''Attach file contents if file exists.

    If key is not specified, the key name will be derived from the file
    name with path_to_key().

    If overwrite is True, an existing key will be updated. If it is False, a
    new key with '_' appended will be added instead.

    If the contents is valid UTF-8, or force_unicode is True, then the value
    will be a string, otherwise it will be bytes.
    '''
    if not key:
        key = path_to_key(path)

    if os.path.exists(path):
        attach_file(report, path, key, overwrite, force_unicode)


def read_file(path, force_unicode=False):
    '''Return the contents of the specified path.

    If the contents is valid UTF-8, or force_unicode is True, then the value
    will a string, otherwise it will be bytes.

    Upon error, this will deliver a text representation of the error,
    instead of failing.
    '''
    try:
        with open(path, 'rb') as f:
            contents = f.read().strip()
        if force_unicode:
            return contents.decode('UTF-8', errors='replace')
        try:
            return contents.decode('UTF-8')
        except UnicodeDecodeError:
            return contents
    except Exception as e:
        return 'Error: ' + str(e)


def attach_file(report, path, key=None, overwrite=True, force_unicode=False):
    '''Attach a file to the report.

    If key is not specified, the key name will be derived from the file
    name with path_to_key().

    If overwrite is True, an existing key will be updated. If it is False, a
    new key with '_' appended will be added instead.

    If the contents is valid UTF-8, or force_unicode is True, then the value
    will a string, otherwise it will be bytes.
    '''
    if not key:
        key = path_to_key(path)

    # Do not clobber existing keys
    if not overwrite:
        while key in report:
            key += '_'
    report[key] = read_file(path, force_unicode=force_unicode)


def attach_conffiles(report, package, conffiles=None, ui=None):
    '''Attach information about any modified or deleted conffiles.

    If conffiles is given, only this subset will be attached. If ui is given,
    ask whether the contents of the file may be added to the report; if this is
    denied, or there is no UI, just mark it as "modified" in the report.
    '''
    modified = packaging.get_modified_conffiles(package)

    for path, contents in modified.items():
        if conffiles and path not in conffiles:
            continue

        key = 'modified.conffile.' + path_to_key(path)
        if type(contents) == str and (contents == '[deleted]' or contents.startswith('[inaccessible')):
            report[key] = contents
            continue

        if ui:
            response = ui.yesno('It seems you have modified the contents of "%s".  Would you like to add the contents of it to your bug report?' % path)
            if response:
                report[key] = contents
            else:
                report[key] = '[modified]'
        else:
            report[key] = '[modified]'

        mtime = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
        report['mtime.conffile.' + path_to_key(path)] = mtime.isoformat()


def attach_upstart_overrides(report, package):
    '''Attach information about any Upstart override files'''

    try:
        files = apport.packaging.get_files(package)
    except ValueError:
        return

    for file in files:
        if os.path.exists(file) and file.startswith('/etc/init/'):
            override = file.replace('.conf', '.override')
            key = 'upstart.' + override.replace('/etc/init/', '')
            attach_file_if_exists(report, override, key)


def attach_upstart_logs(report, package):
    '''Attach information about a package's session upstart logs'''

    try:
        files = apport.packaging.get_files(package)
    except ValueError:
        return

    for f in files:
        if not os.path.exists(f):
            continue
        if f.startswith('/usr/share/upstart/sessions/'):
            log = os.path.basename(f).replace('.conf', '.log')
            key = 'upstart.' + log
            try:
                log = os.path.join(os.environ['XDG_CACHE_HOME'], 'upstart', log)
            except KeyError:
                try:
                    log = os.path.join(os.environ['HOME'], '.cache', 'upstart', log)
                except KeyError:
                    continue

            attach_file_if_exists(report, log, key)

        if f.startswith('/usr/share/applications/') and f.endswith('.desktop'):
            desktopname = os.path.splitext(os.path.basename(f))[0]
            key = 'upstart.application.' + desktopname
            log = 'application-%s.log' % desktopname
            try:
                log = os.path.join(os.environ['XDG_CACHE_HOME'], 'upstart', log)
            except KeyError:
                try:
                    log = os.path.join(os.environ['HOME'], '.cache', 'upstart', log)
                except KeyError:
                    continue

            attach_file_if_exists(report, log, key)


def attach_dmesg(report):
    '''Attach information from the kernel ring buffer (dmesg).

    This will not overwrite already existing information.
    '''
    if not report.get('CurrentDmesg', '').strip():
        report['CurrentDmesg'] = command_output(['dmesg'])


def attach_dmi(report):
    dmi_dir = '/sys/class/dmi/id'
    if os.path.isdir(dmi_dir):
        for f in os.listdir(dmi_dir):
            p = '%s/%s' % (dmi_dir, f)
            st = os.stat(p)
            # ignore the root-only ones, since they have serial numbers
            if not stat.S_ISREG(st.st_mode) or (st.st_mode & 4 == 0):
                continue
            if f in ('subsystem', 'uevent'):
                continue

            try:
                value = read_file(p)
            except (OSError, IOError):
                continue
            if value:
                report['dmi.' + f.replace('_', '.')] = value


def attach_hardware(report):
    '''Attach a standard set of hardware-related data to the report, including:

    - kernel dmesg (boot and current)
    - /proc/interrupts
    - /proc/cpuinfo
    - /proc/cmdline
    - /proc/modules
    - lspci -vvnn
    - lsusb
    - devices from udev
    - DMI information from /sys
    - prtconf (sparc)
    - pccardctl status/ident
    '''
    attach_dmesg(report)

    attach_file(report, '/proc/interrupts', 'ProcInterrupts')
    attach_file(report, '/proc/cpuinfo', 'ProcCpuinfo')
    attach_file(report, '/proc/cmdline', 'ProcKernelCmdLine')

    if os.path.exists('/sys/bus/pci'):
        report['Lspci'] = command_output(['lspci', '-vvnn'])
    report['Lsusb'] = command_output(['lsusb'])
    report['ProcModules'] = command_output(['sort', '/proc/modules'])
    report['UdevDb'] = command_output(['udevadm', 'info', '--export-db'])

    # anonymize partition labels
    labels = report['UdevDb']
    labels = re.sub('ID_FS_LABEL=(.*)', 'ID_FS_LABEL=<hidden>', labels)
    labels = re.sub('ID_FS_LABEL_ENC=(.*)', 'ID_FS_LABEL_ENC=<hidden>', labels)
    labels = re.sub('by-label/(.*)', 'by-label/<hidden>', labels)
    labels = re.sub('ID_FS_LABEL=(.*)', 'ID_FS_LABEL=<hidden>', labels)
    labels = re.sub('ID_FS_LABEL_ENC=(.*)', 'ID_FS_LABEL_ENC=<hidden>', labels)
    labels = re.sub('by-label/(.*)', 'by-label/<hidden>', labels)
    report['UdevDb'] = labels

    attach_dmi(report)

    # Use the hardware information to create a machine type.
    if 'dmi.sys.vendor' in report and 'dmi.product.name' in report:
        report['MachineType'] = '%s %s' % (report['dmi.sys.vendor'],
                                           report['dmi.product.name'])

    if command_available('prtconf'):
        report['Prtconf'] = command_output(['prtconf'])

    if command_available('pccardctl'):
        out = command_output(['pccardctl', 'status']).strip()
        if out:
            report['PccardctlStatus'] = out
        out = command_output(['pccardctl', 'ident']).strip()
        if out:
            report['PccardctlIdent'] = out


def attach_alsa_old(report):
    ''' (loosely based on http://www.alsa-project.org/alsa-info.sh)
    for systems where alsa-info is not installed (i e, *buntu 12.04 and earlier)
    '''
    attach_file_if_exists(report, os.path.expanduser('~/.asoundrc'),
                          'UserAsoundrc')
    attach_file_if_exists(report, os.path.expanduser('~/.asoundrc.asoundconf'),
                          'UserAsoundrcAsoundconf')
    attach_file_if_exists(report, '/etc/asound.conf')
    attach_file_if_exists(report, '/proc/asound/version', 'AlsaVersion')
    attach_file(report, '/proc/cpuinfo', 'ProcCpuinfo')

    report['AlsaDevices'] = command_output(['ls', '-l', '/dev/snd/'])
    report['AplayDevices'] = command_output(['aplay', '-l'])
    report['ArecordDevices'] = command_output(['arecord', '-l'])

    report['PciMultimedia'] = pci_devices(PCI_MULTIMEDIA)

    cards = []
    if os.path.exists('/proc/asound/cards'):
        with open('/proc/asound/cards') as fd:
            for line in fd:
                if ']:' in line:
                    fields = line.lstrip().split()
                    cards.append(int(fields[0]))

    for card in cards:
        key = 'Card%d.Amixer.info' % card
        report[key] = command_output(['amixer', '-c', str(card), 'info'])
        key = 'Card%d.Amixer.values' % card
        report[key] = command_output(['amixer', '-c', str(card)])

        for codecpath in glob.glob('/proc/asound/card%d/codec*' % card):
            if os.path.isfile(codecpath):
                codec = os.path.basename(codecpath)
                key = 'Card%d.Codecs.%s' % (card, path_to_key(codec))
                attach_file(report, codecpath, key=key)
            elif os.path.isdir(codecpath):
                codec = os.path.basename(codecpath)
                for name in os.listdir(codecpath):
                    path = os.path.join(codecpath, name)
                    key = 'Card%d.Codecs.%s.%s' % (card, path_to_key(codec), path_to_key(name))
                    attach_file(report, path, key)


def attach_alsa(report):
    '''Attach ALSA subsystem information to the report.
    '''
    if os.path.exists('/usr/share/alsa-base/alsa-info.sh'):
        report['AlsaInfo'] = command_output(['/usr/share/alsa-base/alsa-info.sh', '--stdout', '--no-upload'])
    else:
        attach_alsa_old(report)

    report['AudioDevicesInUse'] = command_output(
        ['fuser', '-v'] + glob.glob('/dev/dsp*') + glob.glob('/dev/snd/*') + glob.glob('/dev/seq*'))

    if os.path.exists('/usr/bin/pacmd'):
        report['PulseList'] = command_output(['pacmd', 'list'])

    attach_dmi(report)
    attach_dmesg(report)


def command_available(command):
    '''Is given command on the executable search path?'''
    if 'PATH' not in os.environ:
        return False
    path = os.environ['PATH']
    for element in path.split(os.pathsep):
        if not element:
            continue
        filename = os.path.join(element, command)
        if os.path.isfile(filename) and os.access(filename, os.X_OK):
            return True
    return False


def command_output(command, input=None, stderr=subprocess.STDOUT,
                   keep_locale=False, decode_utf8=True):
    '''Try to execute given command (list) and return its stdout.

    In case of failure, a textual error gets returned. This function forces
    LC_MESSAGES to C, to avoid translated output in bug reports.

    If decode_utf8 is True (default), the output will be converted to a string,
    otherwise left as bytes.
    '''
    env = os.environ.copy()
    if not keep_locale:
        env['LC_MESSAGES'] = 'C'
    try:
        sp = subprocess.Popen(command, stdout=subprocess.PIPE,
                              stderr=stderr,
                              stdin=(input and subprocess.PIPE or None),
                              env=env)
    except OSError as e:
        return 'Error: ' + str(e)

    out = sp.communicate(input)[0]
    if sp.returncode == 0:
        res = out.strip()
    else:
        res = (b'Error: command ' + str(command).encode() + b' failed with exit code ' +
               str(sp.returncode).encode() + b': ' + out)

    if decode_utf8:
        res = res.decode('UTF-8', errors='replace')
    return res


def _root_command_prefix():
    if os.getuid() == 0:
        return []
    else:
        return ['pkexec']


def root_command_output(command, input=None, stderr=subprocess.STDOUT, decode_utf8=True):
    '''Try to execute given command (list) as root and return its stdout.

    This passes the command through pkexec, unless the caller is already root.

    In case of failure, a textual error gets returned.

    If decode_utf8 is True (default), the output will be converted to a string,
    otherwise left as bytes.
    '''
    assert isinstance(command, list), 'command must be a list'
    return command_output(_root_command_prefix() + command, input, stderr,
                          keep_locale=True, decode_utf8=decode_utf8)


def attach_root_command_outputs(report, command_map):
    '''Execute multiple commands as root and put their outputs into report.

    command_map is a keyname -> 'shell command' dictionary with the commands to
    run. They are all run through /bin/sh, so you need to take care of shell
    escaping yourself. To include stderr output of a command, end it with
    "2>&1".

    Just like root_command_output, this passes the command through pkexec,
    unless the caller is already root.

    This is preferrable to using root_command_output() multiple times, as that
    will ask for the password every time.
    '''
    wrapper_path = os.path.join(os.path.abspath(
        os.environ.get('APPORT_DATA_DIR', '/usr/share/apport')), 'root_info_wrapper')
    workdir = tempfile.mkdtemp()
    try:
        # create a shell script with all the commands
        script_path = os.path.join(workdir, ':script:')
        script = open(script_path, 'w')
        for keyname, command in command_map.items():
            assert hasattr(command, 'strip'), 'command must be a string (shell command)'
            # use "| cat" here, so that we can end commands with 2>&1
            # (otherwise it would have the wrong redirection order)
            script.write('%s | cat > %s\n' % (command, os.path.join(workdir, keyname)))
        script.close()

        # run script
        sp = subprocess.Popen(_root_command_prefix() + [wrapper_path, script_path])
        sp.wait()

        # now read back the individual outputs
        for keyname in command_map:
            try:
                with open(os.path.join(workdir, keyname), 'rb') as f:
                    buf = f.read().strip()
            except IOError:
                # this can happen if the user dismisses authorization in
                # _root_command_prefix
                continue
            # opportunistically convert to strings, like command_output()
            try:
                buf = buf.decode('UTF-8')
            except UnicodeDecodeError:
                pass
            if buf:
                report[keyname] = buf
            f.close()
    finally:
        shutil.rmtree(workdir)


def __filter_re_process(pattern, process):
    lines = ''
    while process.poll() is None:
        for line in process.stdout:
            line = line.decode('UTF-8', errors='replace')
            if pattern.search(line):
                lines += line
    process.stdout.close()
    process.wait()
    if process.returncode == 0:
        return lines
    return ''


def recent_syslog(pattern, path=None):
    '''Extract recent system messages which match a regex.

    pattern should be a "re" object. By default, messages are read from
    the systemd journal, or /var/log/syslog; but when giving "path", messages
    are read from there instead.
    '''
    if path:
        p = subprocess.Popen(['tail', '-n', '10000', path],
                             stdout=subprocess.PIPE)
    elif os.path.exists('/run/systemd/system'):
        p = subprocess.Popen(['journalctl', '--system', '--quiet', '-b', '-a'],
                             stdout=subprocess.PIPE)
    elif os.access('/var/log/syslog', os.R_OK):
        p = subprocess.Popen(['tail', '-n', '10000', '/var/log/syslog'],
                             stdout=subprocess.PIPE)
    return __filter_re_process(pattern, p)


def xsession_errors(pattern=None):
    '''Extract messages from ~/.xsession-errors.

    By default this parses out glib-style warnings, errors, criticals etc. and
    X window errors.  You can specify a "re" object as pattern to customize the
    filtering.

    Please note that you should avoid attaching the whole file to reports, as
    it can, and often does, contain sensitive and private data.
    '''
    path = os.path.expanduser('~/.xsession-errors')
    if not os.path.exists(path) or \
            not os.access(path, os.R_OK):
        return ''

    if not pattern:
        pattern = re.compile(r'^(\(.*:\d+\): \w+-(WARNING|CRITICAL|ERROR))|(Error: .*No Symbols named)|([^ ]+\[\d+\]: ([A-Z]+):)|([^ ]-[A-Z]+ \*\*:)|(received an X Window System error)|(^The error was \')|(^  \(Details: serial \d+ error_code)')

    lines = ''
    with open(path, 'rb') as f:
        for line in f:
            line = line.decode('UTF-8', errors='replace')
            if pattern.search(line):
                lines += line
    return lines


PCI_MASS_STORAGE = 0x01
PCI_NETWORK = 0x02
PCI_DISPLAY = 0x03
PCI_MULTIMEDIA = 0x04
PCI_MEMORY = 0x05
PCI_BRIDGE = 0x06
PCI_SIMPLE_COMMUNICATIONS = 0x07
PCI_BASE_SYSTEM_PERIPHERALS = 0x08
PCI_INPUT_DEVICES = 0x09
PCI_DOCKING_STATIONS = 0x0a
PCI_PROCESSORS = 0x0b
PCI_SERIAL_BUS = 0x0c


def pci_devices(*pci_classes):
    '''Return a text dump of PCI devices attached to the system.'''

    if not pci_classes:
        return command_output(['lspci', '-vvnn'])

    result = ''
    output = command_output(['lspci', '-vvmmnn'])
    for paragraph in output.split('\n\n'):
        pci_class = None
        slot = None

        for line in paragraph.split('\n'):
            try:
                key, value = line.split(':', 1)
            except ValueError:
                continue
            value = value.strip()
            key = key.strip()
            if key == 'Class':
                n = int(value[-5:-1], 16)
                pci_class = (n & 0xff00) >> 8
            elif key == 'Slot':
                slot = value

        if pci_class and slot and pci_class in pci_classes:
            if result:
                result += '\n\n'
            result += command_output(['lspci', '-vvnns', slot]).strip()

    return result


def usb_devices():
    '''Return a text dump of USB devices attached to the system.'''

    # TODO: would be nice to be able to filter by interface class
    return command_output(['lsusb', '-v'])


def files_in_package(package, globpat=None):
    '''Retrieve a list of files owned by package, optionally matching globpat'''

    files = packaging.get_files(package)
    if globpat:
        result = [f for f in files if glob.fnmatch.fnmatch(f, globpat)]
    else:
        result = files
    return result


def attach_gconf(report, package):
    '''Obsolete'''

    # keeping a no-op function for some time to not break hooks
    pass


def attach_gsettings_schema(report, schema):
    '''Attach user-modified gsettings keys of a schema.'''

    cur_value = report.get('GsettingsChanges', '')

    defaults = {}  # schema -> key ->  value
    env = os.environ.copy()
    env['XDG_CONFIG_HOME'] = '/nonexisting'
    gsettings = subprocess.Popen(['gsettings', 'list-recursively', schema],
                                 env=env, stdout=subprocess.PIPE)
    for l in gsettings.stdout:
        try:
            (schema_name, key, value) = l.split(None, 2)
            value = value.rstrip()
        except ValueError:
            continue  # invalid line
        defaults.setdefault(schema_name, {})[key] = value

    gsettings = subprocess.Popen(['gsettings', 'list-recursively', schema],
                                 stdout=subprocess.PIPE)
    for l in gsettings.stdout:
        try:
            (schema_name, key, value) = l.split(None, 2)
            value = value.rstrip()
        except ValueError:
            continue  # invalid line

        if value != defaults.get(schema_name, {}).get(key, ''):
            if schema_name == b'org.gnome.shell' and \
                    key in [b'command-history', b'favorite-apps']:
                value = 'redacted by apport'
            cur_value += '%s %s %s\n' % (schema_name, key, value)

    report['GsettingsChanges'] = cur_value


def attach_gsettings_package(report, package):
    '''Attach user-modified gsettings keys of all schemas in a package.'''

    for schema_file in files_in_package(package, '/usr/share/glib-2.0/schemas/*.gschema.xml'):
        schema = os.path.basename(schema_file)[:-12]
        attach_gsettings_schema(report, schema)


def attach_network(report):
    '''Attach generic network-related information to report.'''

    report['IpRoute'] = command_output(['ip', 'route'])
    report['IpAddr'] = command_output(['ip', 'addr'])
    report['PciNetwork'] = pci_devices(PCI_NETWORK)
    attach_file_if_exists(report, '/etc/network/interfaces', key='IfupdownConfig')

    for var in ('http_proxy', 'ftp_proxy', 'no_proxy'):
        if var in os.environ:
            report[var] = os.environ[var]


def attach_wifi(report):
    '''Attach wireless (WiFi) network information to report.'''

    report['WifiSyslog'] = recent_syslog(re.compile(r'(NetworkManager|modem-manager|dhclient|kernel|wpa_supplicant)(\[\d+\])?:'))
    report['IwConfig'] = re.sub(
        'ESSID:(.*)', 'ESSID:<hidden>',
        re.sub('Encryption key:(.*)', 'Encryption key: <hidden>',
               re.sub('Access Point: (.*)', 'Access Point: <hidden>',
                      command_output(['iwconfig']))))
    report['RfKill'] = command_output(['rfkill', 'list'])
    if os.path.exists('/sbin/iw'):
        iw_output = command_output(['iw', 'reg', 'get'])
    else:
        iw_output = 'N/A'
    report['CRDA'] = iw_output

    attach_file_if_exists(report, '/var/log/wpa_supplicant.log', key='WpaSupplicantLog')


def attach_printing(report):
    '''Attach printing information to the report.

    Based on http://wiki.ubuntu.com/PrintingBugInfoScript.
    '''
    attach_file_if_exists(report, '/etc/papersize', 'Papersize')
    attach_file_if_exists(report, '/var/log/cups/error_log', 'CupsErrorLog')
    report['Locale'] = command_output(['locale'])
    report['Lpstat'] = command_output(['lpstat', '-v'])

    ppds = glob.glob('/etc/cups/ppd/*.ppd')
    if ppds:
        nicknames = command_output(['fgrep', '-H', '*NickName'] + ppds)
        report['PpdFiles'] = re.sub(r'/etc/cups/ppd/(.*).ppd:\*NickName: *"(.*)"', r'\g<1>: \g<2>', nicknames)

    report['PrintingPackages'] = package_versions(
        'foo2zjs', 'foomatic-db', 'foomatic-db-engine',
        'foomatic-db-gutenprint', 'foomatic-db-hpijs', 'foomatic-filters',
        'foomatic-gui', 'hpijs', 'hplip', 'm2300w', 'min12xxw', 'c2050',
        'hpoj', 'pxljr', 'pnm2ppa', 'splix', 'hp-ppd', 'hpijs-ppds',
        'linuxprinting.org-ppds', 'openprinting-ppds',
        'openprinting-ppds-extra', 'ghostscript', 'cups',
        'cups-driver-gutenprint', 'foomatic-db-gutenprint', 'ijsgutenprint',
        'cupsys-driver-gutenprint', 'gimp-gutenprint', 'gutenprint-doc',
        'gutenprint-locales', 'system-config-printer-common', 'kdeprint')


def attach_mac_events(report, profiles=None):
    '''Attach MAC information and events to the report.'''

    # Allow specifying a string, or a list of strings
    if isinstance(profiles, str):
        profiles = [profiles]

    mac_regex = r'audit\(|apparmor|selinux|security'
    mac_re = re.compile(mac_regex, re.IGNORECASE)
    aa_regex = 'apparmor="DENIED".+?profile=([^ ]+?)[ ]'
    aa_re = re.compile(aa_regex, re.IGNORECASE)

    if 'KernLog' not in report:
        report['KernLog'] = __filter_re_process(
            mac_re, subprocess.Popen(['dmesg'], stdout=subprocess.PIPE))

    if 'AuditLog' not in report and os.path.exists('/var/run/auditd.pid'):
        attach_root_command_outputs(report, {'AuditLog': 'egrep "' + mac_regex + '" /var/log/audit/audit.log'})

    attach_file_if_exists(report, '/proc/version_signature', 'ProcVersionSignature')
    attach_file(report, '/proc/cmdline', 'ProcCmdline')

    for match in re.findall(aa_re, report.get('KernLog', '') + report.get('AuditLog', '')):
        if not profiles:
            _add_tag(report, 'apparmor')
            break

        try:
            if match[0] == '"':
                profile = match[1:-1]
            elif sys.version[0] >= '3':
                profile = bytes.fromhex(match).decode('UTF-8', errors='replace')
            else:
                profile = match.decode('hex', errors='replace')
        except Exception:
            continue

        for search_profile in profiles:
            if re.match('^' + search_profile + '$', profile):
                _add_tag(report, 'apparmor')
                break


def _add_tag(report, tag):
    '''Adds or appends a tag to the report'''
    current_tags = report.get('Tags', '')
    if current_tags:
        current_tags += ' '
    report['Tags'] = current_tags + tag


def attach_related_packages(report, packages):
    '''Attach version information for related packages

    In the future, this might also run their hooks.
    '''
    report['RelatedPackageVersions'] = package_versions(*packages)


def package_versions(*packages):
    '''Return a text listing of package names and versions.

    Arguments may be package names or globs, e. g. "foo*"
    '''
    if not packages:
        return ''
    versions = []
    for package_pattern in packages:
        if not package_pattern:
            continue

        matching_packages = packaging.package_name_glob(package_pattern)

        if not matching_packages:
            versions.append((package_pattern, 'N/A'))

        for package in sorted(matching_packages):
            try:
                version = packaging.get_version(package)
            except ValueError:
                version = 'N/A'
            if version is None:
                version = 'N/A'
            versions.append((package, version))

    package_width, version_width = \
        map(max, [map(len, t) for t in zip(*versions)])

    fmt = '%%-%ds %%s' % package_width
    return '\n'.join([fmt % v for v in versions])


def _get_module_license(module):
    '''Return the license for a given kernel module.'''

    try:
        modinfo = subprocess.Popen(['/sbin/modinfo', module],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = modinfo.communicate()[0].decode('UTF-8')
        if modinfo.returncode != 0:
            return 'invalid'
    except OSError:
        return None
    for l in out.splitlines():
        fields = l.split(':', 1)
        if len(fields) < 2:
            continue
        if fields[0] == 'license':
            return fields[1].strip()

    return None


def nonfree_kernel_modules(module_list='/proc/modules'):
    '''Check loaded modules and return a list of those which are not free.'''

    try:
        with open(module_list) as f:
            mods = [l.split()[0] for l in f]
    except IOError:
        return []

    nonfree = []
    for m in mods:
        s = _get_module_license(m)
        if s and not ('GPL' in s or 'BSD' in s or 'MPL' in s or 'MIT' in s):
            nonfree.append(m)

    return nonfree


def __drm_con_info(con):
    info = ''
    for f in os.listdir(con):
        path = os.path.join(con, f)
        if f == 'uevent' or not os.path.isfile(path):
            continue
        val = open(path, 'rb').read().strip()
        # format some well-known attributes specially
        if f == 'modes':
            val = val.replace(b'\n', b' ')
        if f == 'edid':
            val = base64.b64encode(val)
            f += '-base64'
        info += '%s: %s\n' % (f, val.decode('UTF-8', errors='replace'))
    return info


def attach_drm_info(report):
    '''Add information about DRM hardware.

    Collect information from /sys/class/drm/.
    '''
    drm_dir = '/sys/class/drm'
    if not os.path.isdir(drm_dir):
        return
    for f in os.listdir(drm_dir):
        con = os.path.join(drm_dir, f)
        if os.path.exists(os.path.join(con, 'enabled')):
            # DRM can set an arbitrary string for its connector paths.
            report['DRM.' + path_to_key(f)] = __drm_con_info(con)


def in_session_of_problem(report):
    '''Check if the problem happened in the currently running XDG session.

    This can be used to determine if e. g. ~/.xsession-errors is relevant and
    should be attached.

    Return None if this cannot be determined.
    '''
    session_id = os.environ.get('XDG_SESSION_ID')
    if not session_id:
        # fall back to reading cgroup
        with open('/proc/self/cgroup') as f:
            for line in f:
                line = line.strip()
                if 'name=systemd:' in line and line.endswith('.scope') and '/session-' in line:
                    session_id = line.split('/session-', 1)[1][:-6]
                    break
            else:
                return None

    # report time is in local TZ
    orig_ctime = locale.getlocale(locale.LC_TIME)
    try:
        try:
            locale.setlocale(locale.LC_TIME, 'C')
            report_time = time.mktime(time.strptime(report['Date']))
        except KeyError:
            return None
        finally:
            locale.setlocale(locale.LC_TIME, orig_ctime)
    except locale.Error:
        return None

    # determine session creation time
    try:
        session_start_time = os.stat('/run/systemd/sessions/' + session_id).st_mtime
    except (IOError, OSError):
        return None

    return session_start_time <= report_time


def attach_default_grub(report, key=None):
    '''attach /etc/default/grub after filtering out password lines'''

    path = '/etc/default/grub'
    if not key:
        key = path_to_key(path)

    if os.path.exists(path):
        with open(path, 'r') as f:
            filtered = [l if not l.startswith('password')
                        else '### PASSWORD LINE REMOVED ###'
                        for l in f.readlines()]
            report[key] = ''.join(filtered)


# backwards compatible API
shared_libraries = apport.fileutils.shared_libraries
links_with_shared_library = apport.fileutils.links_with_shared_library
