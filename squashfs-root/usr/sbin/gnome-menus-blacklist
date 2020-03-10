#! /usr/bin/python3

sourcedir = "/usr/share/applications"
destdir = "/usr/share/gnome/applications"
blacklist_file = "/etc/gnome/menus.blacklist"

import sys, os

# Parse blacklist file
blacklist = []
try:
    with open(blacklist_file, 'r', encoding='utf_8') as fp:
        for l in fp.readlines():
            l = l.strip()
            if l.startswith("#"):
                continue
            blacklist.append(l)
except IOError:
    sys.stderr.write("Warning: %s cannot be opened\n"%blacklist_file)

# Built the list of files to work on
sourcefiles = []
for root, dirs, files in os.walk (sourcedir):
    reldir = root[len(sourcedir)+1:]
    for f in files:
        relfile = os.path.join (reldir, f)
        if relfile.endswith(".desktop") and (f in blacklist or relfile in blacklist):
            sourcefiles.append(relfile)

# Remove obsolete files
for root, dirs, files in os.walk (destdir, topdown=False):
    reldir = root[len(destdir)+1:]
    for f in files:
        relfile = os.path.join (reldir, f)
        if f.endswith(".desktop") and relfile not in sourcefiles:
            os.remove (os.path.join (destdir, relfile))
    if reldir:
        try:
            os.rmdir (root)
        except OSError:
            pass

# Now process the files
for f in sourcefiles:
    sourcefile = os.path.join (sourcedir, f)
    destfile = os.path.join (destdir, f)
    absdir = os.path.dirname (destfile)

    # The mtime is used as a flag to check if the file has changed
    source_time = int (os.stat (sourcefile).st_mtime)
    try:
        dest_time = int (os.stat (destfile).st_mtime)
    except OSError:
        dest_time = 0
    if source_time == dest_time:
        continue

    # Copy file, adding a NoDisplay flag
    if not os.path.isdir (absdir):
        os.makedirs (absdir)
    with open(destfile, 'wt', encoding='utf_8') as fp_out:
        with open(sourcefile, 'rt', encoding='utf_8') as fp_in:
            for l in fp_in.readlines():
                if l.startswith ("NoDisplay="):
                    continue
                fp_out.write(l)
        if not l.endswith ("\n"):
            fp_out.write("\n")
        fp_out.write("NoDisplay=true\n")

    # Set mtime so that the file is not touched unless it has changed
    os.utime (destfile, (source_time, source_time))
