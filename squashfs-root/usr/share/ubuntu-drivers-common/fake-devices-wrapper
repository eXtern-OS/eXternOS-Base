#! /usr/bin/python3
import sys
import os
import os.path
import subprocess

try:
    from gi.repository import UMockdev
except ImportError:
    print('Please install the gir1.2-umockdev-1.0 and umockdev packages for this', file=sys.stderr)
    sys.exit(1)

if len(sys.argv) < 2:
    print('Usage: %s <command> [args...]' % sys.argv[0], file=sys.stderr)
    sys.exit(1)

testbed = UMockdev.Testbed.new()

# fake an installed kmod?
if 'FAKE_INSTALLED_KMOD' in os.environ:
    with open(os.path.join(testbed.get_root_dir(), 'modinfo'), 'w') as f:
        f.write('''#!/bin/sh -e
if [ "$1" = %(mod)s ]; then
    echo "filename:  /some/path/%(mod)s.ko"
    exit 0
fi
exec /sbin/modinfo "$@"
''' % {'mod': os.environ['FAKE_INSTALLED_KMOD']})
        os.chmod(os.path.join(testbed.get_root_dir(), 'modinfo'), 0o755)
        os.environ['PATH'] = '%s:%s' % (testbed.get_root_dir(), os.environ['PATH'])

testbed.add_device('pci', 'nvidiacard', None,
                   ['modalias', 'pci:v000010DEd000010C3sv00sd01bc03sc00i00',
                    'vendor', '0x10DE',
                    'device', '0x10C3',
                   ], [])
testbed.add_device('pci', 'aticard', None,
                   ['modalias', 'pci:v00001002d00009611sv00sd00bc03sc00i00',
                    'vendor', '0x1002',
                    'device', '0x9611',
                   ], [])
testbed.add_device('pci', 'bcmwifi', None,
                   ['modalias', 'pci:v000014E4d00004353sv00sd01bc02sc80i00',
                    'vendor', '0x14E4',
                    'device', '0x4353',
                   ], [])

# skip hybrid system detection
os.environ['UBUNTU_DRIVERS_XORG_LOG'] = '/dev/null'

# run wrapped program
subprocess.call(['umockdev-wrapper'] + sys.argv[1:])
