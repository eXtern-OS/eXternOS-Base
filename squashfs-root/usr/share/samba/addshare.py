#!/usr/bin/python
# Helper to add a share in the samba configuration file
# Eventually this should be replaced by a call to samba-tool, but
# for the moment that doesn't support setting individual configuration options.

import optparse
import os
import re
import shutil
import stat
import sys
import tempfile

parser = optparse.OptionParser()
parser.add_option("--configfile", type=str, metavar="CONFFILE",
                  help="Configuration file to use", default="/etc/samba/smb.conf")

(opts, args) = parser.parse_args()
if len(args) != 2:
    parser.print_usage()

(share, path) = args
done = False

inf = open(opts.configfile, 'r')
(fd, fn) = tempfile.mkstemp()
outf = os.fdopen(fd, 'w')

for l in inf.readlines():
    m = re.match(r"^\s*\[([^]]+)\]$", l)
    if m:
        name = m.groups(1)[0]
        if name.lower() == share.lower():
            sys.exit(0)
    outf.write(l)

if not os.path.isdir(path):
    os.makedirs(path)
outf.write("[%s]\n" % share)
outf.write("  path = %s\n" % path)
outf.write("  read only = no\n")
outf.write("\n")

os.fchmod(fd, stat.S_IMODE(os.stat(opts.configfile).st_mode))
outf.close()
shutil.move(fn, opts.configfile)
