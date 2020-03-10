# DistUpgradeAptCdrom.py 
#  
#  Copyright (c) 2008 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import re
import os
import apt
import apt_pkg
import logging
import gzip
import shutil
import subprocess
import sys
import tempfile
from gettext import gettext as _


class AptCdromError(Exception):
    """ base exception for apt cdrom errors """
    pass


class AptCdrom(object):
    """ represents a apt cdrom object """

    def __init__(self, view, path):
        self.view = view
        self.cdrompath = path
        # the directories we found on disk with signatures, packages and i18n
        self.packages = set()
        self.signatures = set()
        self.i18n = set()
        apt_pkg.init_config()

    def restore_backup(self, backup_ext):
        """ restore the backup copy of the cdroms.list file 
           (*not* sources.list)! 
        """
        cdromstate = os.path.join(apt_pkg.config.find_dir("Dir::State"),
                                  apt_pkg.config.find("Dir::State::cdroms"))
        if os.path.exists(cdromstate + backup_ext):
            shutil.copy(cdromstate + backup_ext, cdromstate)
        # mvo: we don't have to care about restoring the sources.list here
        #      because aptsources will do this for us anyway

    def comment_out_cdrom_entry(self):
        """ comment out the cdrom entry """
        diskname = self._readDiskName()
        pentry = self._generateSourcesListLine(diskname, self.packages)
        sourceslist = apt_pkg.config.find_file("Dir::Etc::sourcelist")
        with open(sourceslist) as f:
            content = f.read()
        content = content.replace(pentry, "# %s" % pentry)
        with open(sourceslist, "w") as f:
            f.write(content)

    def _scanCD(self):
        """ 
        scan the CD for interessting files and return them as:
        (packagesfiles, signaturefiles, i18nfiles)
        """
        packages = set()
        signatures = set()
        i18n = set()
        for root, dirs, files in os.walk(self.cdrompath, topdown=True):
            if (root.endswith("debian-installer") or 
                    root.endswith("dist-upgrader")):
                del dirs[:]
                continue
            elif ".aptignr" in files:
                continue
            elif "Packages" in files:
                packages.add(os.path.join(root, "Packages"))
            elif "Packages.gz" in files:
                packages.add(os.path.join(root, "Packages.gz"))
            elif "Sources" in files or "Sources.gz" in files:
                logging.error(
                    "Sources entry found in %s but not supported" % root)
            elif "Release.gpg" in files:
                signatures.add(os.path.join(root, "Release.gpg"))
            elif "i18n" in dirs:
                for f in os.listdir(os.path.join(root, "i18n")):
                    i18n.add(os.path.join(root, "i18n", f))
            # there is nothing under pool but deb packages (no
            # indexfiles, so we skip that here
            elif os.path.split(root)[1] == "pool":
                del dirs[:]
        return (packages, signatures, i18n)

    def _writeDatabase(self):
        """ update apts cdrom.list """
        dbfile = apt_pkg.config.find_file("Dir::State::cdroms")
        cdrom = apt_pkg.Cdrom()
        id = cdrom.ident(apt.progress.base.CdromProgress())
        label = self._readDiskName()
        with open(dbfile, "a") as out:
            out.write('CD::%s "%s";\n' % (id, label))
            out.write('CD::%s::Label "%s";\n' % (id, label))

    def _dropArch(self, packages):
        """ drop architectures that are not ours """
        # create a copy
        packages = set(packages)
        # now go over the packagesdirs and drop stuff that is not
        # our binary-$arch 
        arch = apt_pkg.config.find("APT::Architecture")
        for d in set(packages):
            if "/binary-" in d and arch not in d:
                packages.remove(d)
        return packages
    
    def _readDiskName(self):
        # default to cdrompath if there is no name
        diskname = self.cdrompath
        info = os.path.join(self.cdrompath, ".disk", "info")
        if os.path.exists(info):
            with open(info) as f:
                diskname = f.read()
            for special in ('"', ']', '[', '_'):
                diskname = diskname.replace(special, '_')
        return diskname

    def _generateSourcesListLine(self, diskname, packages):
        # see apts indexcopy.cc:364 for details
        path = ""                                    
        dist = ""
        comps = []
        for d in packages:
            # match(1) is the path, match(2) the dist
            # and match(3) the components
            m = re.match("(.*)/dists/([^/]*)/(.*)/binary-*", d)
            if not m:
                raise AptCdromError(
                    _("Could not calculate sources.list entry"))
            path = m.group(1)
            dist = m.group(2)
            comps.append(m.group(3))
        if not path or not comps:
            return None
        comps.sort()
        pentry = "deb cdrom:[%s]/ %s %s" % (diskname, dist, " ".join(comps))
        return pentry

    def _copyTranslations(self, translations, targetdir=None):
        if not targetdir:
            targetdir = apt_pkg.config.find_dir("Dir::State::lists")
        diskname = self._readDiskName()
        for f in translations:
            fname = apt_pkg.uri_to_filename(
                "cdrom:[%s]/%s" % (diskname, f[f.find("dists"):]))
            outf = os.path.join(targetdir, os.path.splitext(fname)[0])
            if f.endswith(".gz"):
                with gzip.open(f) as g, open(outf, "wb") as out:
                    # uncompress in 64k chunks
                    while True:
                        s = g.read(64000)
                        out.write(s)
                        if s == b"":
                            break
            else:
                shutil.copy(f, outf)
        return True

    def _copyPackages(self, packages, targetdir=None):
        if not targetdir:
            targetdir = apt_pkg.config.find_dir("Dir::State::lists")
        # CopyPackages()
        diskname = self._readDiskName()
        for f in packages:
            fname = apt_pkg.uri_to_filename(
                "cdrom:[%s]/%s" % (diskname, f[f.find("dists"):]))
            outf = os.path.join(targetdir, os.path.splitext(fname)[0])
            if f.endswith(".gz"):
                with gzip.open(f) as g, open(outf, "wb") as out:
                    # uncompress in 64k chunks
                    while True:
                        s = g.read(64000)
                        out.write(s)
                        if s == b"":
                            break
            else:
                shutil.copy(f, outf)
        return True

    def _verifyRelease(self, signatures):
        " verify the signatues and hashes "
        for sig in signatures:
            basepath = os.path.split(sig)[0]
            # do gpg checking
            releasef = os.path.splitext(sig)[0]
            verify_env = os.environ.copy()
            cmd = ["apt-key", "--quiet", "verify", sig, releasef]
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(apt_pkg.config.dump())
                verify_env["APT_CONFIG"] = fp.name
                ret = subprocess.call(cmd, env=verify_env)
            if not (ret == 0):
                return False
            # now do the hash sum checks
            with open(releasef) as f:
                t = apt_pkg.TagFile(f)
                t.step()
                sha256_section = t.section["SHA256"]
            for entry in sha256_section.split("\n"):
                (hash, size, name) = entry.split()
                f = os.path.join(basepath, name)
                if not os.path.exists(f):
                    logging.info("ignoring missing '%s'" % f)
                    continue
                with open(f) as fp:
                    sum = apt_pkg.sha256sum(fp)
                if not (sum == hash):
                    logging.error(
                        "hash sum mismatch expected %s but got %s" % (
                            hash, sum))
                    return False
        return True

    def _copyRelease(self, signatures, targetdir=None):
        " copy the release file "
        if not targetdir:
            targetdir = apt_pkg.config.find_dir("Dir::State::lists")
        diskname = self._readDiskName()
        for sig in signatures:
            releasef = os.path.splitext(sig)[0]
            # copy both Release and Release.gpg
            for f in (sig, releasef):
                fname = apt_pkg.uri_to_filename(
                    "cdrom:[%s]/%s" % (diskname, f[f.find("dists"):]))
                shutil.copy(f, os.path.join(targetdir, fname))
        return True

    def _doAdd(self):
        " reimplement pkgCdrom::Add() in python "
        # os.walk() will not follow symlinks so we don't need
        # pkgCdrom::Score() and not dropRepeats() that deal with
        # killing the links
        (self.packages, self.signatures, self.i18n) = self._scanCD()
        self.packages = self._dropArch(self.packages)
        if len(self.packages) == 0:
            logging.error("no useable indexes found on CD, wrong ARCH?")
            raise AptCdromError(
                _("Unable to locate any package files, "
                  "perhaps this is not a Ubuntu Disc or the wrong "
                  "architecture?"))

        # CopyAndVerify
        if self._verifyRelease(self.signatures):
            self._copyRelease(self.signatures)
        
        # copy the packages and translations
        self._copyPackages(self.packages)
        self._copyTranslations(self.i18n)

        # add CD to cdroms.list "database" and update sources.list
        diskname = self._readDiskName()
        if not diskname:
            logging.error("no .disk/ directory found")
            return False
        debline = self._generateSourcesListLine(diskname, self.packages)
        
        # prepend to the sources.list
        sourceslist = apt_pkg.config.find_file("Dir::Etc::sourcelist")
        with open(sourceslist) as f:
            content = f.read()
        with open(sourceslist, "w") as f:
            f.write(
                "# added by the release upgrader\n%s\n%s" %
                (debline, content))
        self._writeDatabase()

        return True

    def add(self, backup_ext=None):
        " add a cdrom to apt's database "
        logging.debug("AptCdrom.add() called with '%s'", self.cdrompath)
        # do backup (if needed) of the cdroms.list file
        if backup_ext:
            cdromstate = os.path.join(
                apt_pkg.config.find_dir("Dir::State"),
                apt_pkg.config.find("Dir::State::cdroms"))
            if os.path.exists(cdromstate):
                shutil.copy(cdromstate, cdromstate + backup_ext)
        # do the actual work
        apt_pkg.config.set("Acquire::cdrom::mount", self.cdrompath)
        apt_pkg.config.set("APT::CDROM::NoMount", "true")
        # FIXME: add cdrom progress here for the view
        #progress = self.view.getCdromProgress()
        try:
            res = self._doAdd()
        except (SystemError, AptCdromError) as e:
            logging.error("can't add cdrom: %s" % e)
            self.view.error(_("Failed to add the CD"),
                            _("There was a error adding the CD, the "
                              "upgrade will abort. Please report this as "
                              "a bug if this is a valid Ubuntu CD.\n\n"
                              "The error message was:\n'%s'") % e)
            return False
        logging.debug("AptCdrom.add() returned: %s" % res)
        return res

    def __bool__(self):
        """ helper to use this as 'if cdrom:' """
        return self.cdrompath is not None

    if sys.version < '3':
        __nonzero__ = __bool__
