#!/usr/bin/python
# Helper to set a global option in the samba configuration file
# Eventually this should be replaced by a call to samba-tool, but
# for the moment that doesn't support setting individual configuration options.

import optparse
import os
import re
import shutil
import stat
import tempfile

parser = optparse.OptionParser()
parser.add_option("--configfile", type=str, metavar="CONFFILE",
                  help="Configuration file to use", default="/etc/samba/smb.conf")

(opts, args) = parser.parse_args()
if len(args) != 2:
    parser.print_usage()

(key, value) = args
inglobal = False
done = False

inf = open(opts.configfile, 'r')
(fd, fn) = tempfile.mkstemp()
outf = os.fdopen(fd, 'w')

for l in inf.readlines():
    m = re.match(r"^\s*\[([^]]+)\]$", l)
    if m:
        if inglobal and not done:
            outf.write("  %s = %s\n" % (key, value))
            done = True
        inglobal = (m.groups(1)[0] in ("global", "globals"))
    elif inglobal and re.match(r"^(\s*)" + key + r"(\s*)=.*$", l):
        l = re.sub(r"^(\s*)" + key + r"(\s*)=.*$",
                r"\1" + key + r"\2=\2" + value, l)
        done = True
    outf.write(l)

if not done:
    outf.write("%s = %s\n" % (key, value))

os.fchmod(fd, stat.S_IMODE(os.stat(opts.configfile).st_mode))
outf.close()
shutil.move(fn, opts.configfile)
