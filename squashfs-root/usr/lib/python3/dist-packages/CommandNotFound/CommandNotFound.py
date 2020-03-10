# (c) Zygmunt Krynicki 2005, 2006, 2007, 2008
# Licensed under GPL, see COPYING for the whole text

from __future__ import (
    print_function,
    absolute_import,
)

import gettext
import grp
import json
import logging
import os
import os.path
import posix
import sys
import subprocess

from CommandNotFound.db.db import SqliteDatabase

if sys.version >= "3":
    _gettext_method = "gettext"
else:
    _gettext_method = "ugettext"
_ = getattr(gettext.translation("command-not-found", fallback=True), _gettext_method)

    
def similar_words(word):
    """
    return a set with spelling1 distance alternative spellings

    based on http://norvig.com/spell-correct.html
    """
    alphabet = 'abcdefghijklmnopqrstuvwxyz-_0123456789'
    s = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in s if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in s if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in s for c in alphabet if b]
    inserts = [a + c + b     for a, b in s for c in alphabet]
    return set(deletes + transposes + replaces + inserts)


def user_can_sudo():
    try:
        groups = posix.getgroups()
        return (grp.getgrnam("sudo")[2] in groups or
                grp.getgrnam("admin")[2] in groups)
    except KeyError:
        return False


# the new style DB - if that exists we skip the legacy DB 
dbpath = "/var/lib/command-not-found/commands.db"
# the legacy DB shipped in the command-not-found-data package
legacy_db = "/usr/share/command-not-found/commands.db"
        

class CommandNotFound(object):

    programs_dir = "programs.d"
    max_len = 256
    
    prefixes = (
        "/snap/bin",
        "/bin",
        "/usr/bin",
        "/usr/local/bin",
        "/sbin",
        "/usr/sbin",
        "/usr/local/sbin",
        "/usr/games")

    snap_cmd = "/usr/bin/snap"

    output_fd = sys.stderr

    def __init__(self, data_dir="/usr/share/command-not-found"):
        self.sources_list = self._getSourcesList()
        # a new style DB means we can skip loading the old legacy static DB
        if os.path.exists(dbpath):
            self.db = SqliteDatabase(dbpath)
        elif os.path.exists(legacy_db):
            self.db = SqliteDatabase(legacy_db)
        self.user_can_sudo = user_can_sudo()
        self.euid = posix.geteuid()

    def spelling_suggestions(self, word, min_len=3):
        """ try to correct the spelling """
        possible_alternatives = []
        if not (min_len <= len(word) <= self.max_len):
            return possible_alternatives
        for w in similar_words(word):
            packages = self.get_packages(w)
            for (package, ver, comp) in packages:
                possible_alternatives.append((w, package, comp, ver))
        return possible_alternatives

    def get_packages(self, command):
        return self.db.lookup(command)

    def get_snaps(self, command):
        exact_result = []
        mispell_result = []
        if not os.path.exists(self.snap_cmd):
            logging.debug("%s not exists" % self.snap_cmd)
            return [], []
        try:
            with open(os.devnull) as devnull:
                output = subprocess.check_output(
                    [self.snap_cmd, "advise-snap", "--format=json",
                     "--command", command],
                    stderr=devnull,
                    universal_newlines=True)
        except subprocess.CalledProcessError as e:
            logging.debug("calling snap advice-snap returned an error: %s" % e)
            return [], []
        logging.debug("got %s from snap advise-snap" % output)
        try:
            snaps = json.loads(output)
        except json.JSONDecodeError as e:
            logging.debug("cannot decoding json: %s" % e)
            return [], []
        for snap in snaps:
            if snap["Command"] == command:
                exact_result.append((snap["Snap"], snap["Command"], snap.get("Version")))
            else:
                mispell_result.append((snap["Command"], snap["Snap"], snap.get("Version")))
        return exact_result, mispell_result
    
    def getBlacklist(self):
        try:
            with open(os.sep.join((os.getenv("HOME", "/root"), ".command-not-found.blacklist"))) as blacklist:
                return [line.strip() for line in blacklist if line.strip() != ""]
        except IOError:
            return []

    def _getSourcesList(self):
        try:
            import apt_pkg
            from aptsources.sourceslist import SourcesList
            apt_pkg.init()
        except (SystemError, ImportError):
            return []
        sources_list = set([])
        # The matcher parses info files from
        # /usr/share/python-apt/templates/
        # But we don't use the calculated data, skip it
        for source in SourcesList(withMatcher=False):
            if not source.disabled and not source.invalid:
                for component in source.comps:
                    sources_list.add(component)
        return sources_list

    def install_prompt(self, package_name):
        if not "COMMAND_NOT_FOUND_INSTALL_PROMPT" in os.environ:
            return
        if package_name:
            prompt = _("Do you want to install it? (N/y)")
            if sys.version >= '3':
                answer = input(prompt)
                raw_input = lambda x: x  # pyflakes
            else:
                answer = raw_input(prompt)
                if sys.stdin.encoding and isinstance(answer, str):
                    # Decode the answer so that we get an unicode value
                    answer = answer.decode(sys.stdin.encoding)
            if answer.lower() == _("y"):
                if self.euid == 0:
                    command_prefix = ""
                else:
                    command_prefix = "sudo "
                install_command = "%sapt install %s" % (command_prefix, package_name)
                print("%s" % install_command, file=sys.stdout)
                subprocess.call(install_command.split(), shell=False)

    def print_spelling_suggestions(self, word, mispell_packages, mispell_snaps, max_alt=15):
        """ print spelling suggestions for packages and snaps """
        if len(mispell_packages)+len(mispell_snaps) > max_alt:
            print("", file=self.output_fd)
            print(_("Command '%s' not found, but there are %s similar ones.") % (word, len(mispell_packages)), file=self.output_fd)
            print("", file=self.output_fd)
            self.output_fd.flush()
            return
        elif len(mispell_packages)+len(mispell_snaps) > 0:
            print("", file=self.output_fd)
            print(_("Command '%s' not found, did you mean:") % word, file=self.output_fd)
            print("", file=self.output_fd)
            for (command, snap, ver) in mispell_snaps:
                if ver:
                    ver = " (%s)" % ver
                else:
                    ver = ""
                print(_("  command '%s' from snap %s%s") % (command, snap, ver), file=self.output_fd)
            for (command, package, comp, ver) in mispell_packages:
                if ver:
                    ver = " (%s)" % ver
                else:
                    ver = ""
                print(_("  command '%s' from deb %s%s") % (command, package, ver), file=self.output_fd)
        print("", file=self.output_fd)
        if len(mispell_snaps) > 0:
            print(_("See 'snap info <snapname>' for additional versions."), file=self.output_fd)
        elif len(mispell_packages) > 0:
            if self.user_can_sudo:
                print(_("Try: %s <deb name>") % "sudo apt install", file=self.output_fd)
            else:
                print(_("Try: %s <deb name>") % "apt install", file=self.output_fd)
        print("", file=self.output_fd)
        self.output_fd.flush()

    def _print_exact_header(self, command):
        print(file=self.output_fd)
        print(_("Command '%(command)s' not found, but can be installed with:") % {
            'command': command}, file=self.output_fd)
        print(file=self.output_fd)

    def advice_single_snap_package(self, command, packages, snaps):
        self._print_exact_header(command)
        snap = snaps[0]
        if self.euid == 0:
            print("snap install %s" % snap[0], file=self.output_fd)
        elif self.user_can_sudo:
            print("sudo snap install %s" % snap[0], file=self.output_fd)
        else:
            print("snap install %s" % snap[0], file=self.output_fd)
            print(_("Please ask your administrator."))
        print("", file=self.output_fd)                    
        self.output_fd.flush()
        
    def advice_single_deb_package(self, command, packages, snaps):
        self._print_exact_header(command)
        if self.euid == 0:
            print("apt install %s" % packages[0][0], file=self.output_fd)
            self.install_prompt(packages[0][0])
        elif self.user_can_sudo:
            print("sudo apt install %s" % packages[0][0], file=self.output_fd)
            self.install_prompt(packages[0][0])
        else:
            print("apt install %s" % packages[0][0], file=self.output_fd)
            print(_("Please ask your administrator."))
            if not packages[0][2] in self.sources_list:
                print(_("You will have to enable the component called '%s'") % packages[0][2], file=self.output_fd)
        print("", file=self.output_fd)                    
        self.output_fd.flush()

    def sudo(self):
        if self.euid != 0 and self.user_can_sudo:
            return "sudo "
        return "" 

    def advice_multi_deb_package(self, command, packages, snaps):
        self._print_exact_header(command)
        pad = max([len(s[0]) for s in snaps+packages])
        for i, package in enumerate(packages):
            ver = ""
            if package[1]:
                if i == 0 and len(package) > 1:
                    ver = "  # version %s, or" % (package[1])
                else:
                    ver = "  # version %s" % (package[1])
            if package[2] in self.sources_list:
                print("%sapt install %-*s%s" % (self.sudo(), pad, package[0], ver), file=self.output_fd)
            else:
                print("%sapt install %-*s%s" % (self.sudo(), pad, package[0], ver) + " (" + _("You will have to enable component called '%s'") % package[2] + ")", file=self.output_fd)
        if self.euid != 0 and not self.user_can_sudo:
            print("", file=self.output_fd)
            print(_("Ask your administrator to install one of them."), file=self.output_fd)
        print("", file=self.output_fd)
        self.output_fd.flush()

    def advice_multi_snap_packages(self, command, packages, snaps):
        self._print_exact_header(command)
        pad = max([len(s[0]) for s in snaps+packages])
        for i, snap in enumerate(snaps):
            ver = ""
            if snap[2]:
                if i == 0 and len(snaps) > 0:
                    ver = "  # version %s, or" % snap[2]
                else:
                    ver = "  # version %s" % snap[2]
            print("%ssnap install %-*s%s" % (self.sudo(), pad, snap[0], ver), file=self.output_fd)
        print("", file=self.output_fd)
        print(_("See 'snap info <snapname>' for additional versions."), file=self.output_fd)
        print("", file=self.output_fd)
        self.output_fd.flush()

    def advice_multi_mixed_packages(self, command, packages, snaps):
        self._print_exact_header(command)
        pad = max([len(s[0]) for s in snaps+packages])
        for i, snap in enumerate(snaps):
            ver=""
            if snap[2]:
                if i == 0:
                    ver = "  # version %s, or" % snap[2]
                else:
                    ver = "  # version %s" % snap[2]
            print("%ssnap install %-*s%s" % (self.sudo(), pad, snap[0], ver), file=self.output_fd)
        for package in packages:
            ver=""
            if package[1]:
                ver = "  # version %s" % package[1]
            print("%sapt  install %-*s%s" % (self.sudo(), pad, package[0], ver), file=self.output_fd)
        print("", file=self.output_fd)
        if len(snaps) == 1:
            print(_("See 'snap info %s' for additional versions.") % snaps[0][0], file=self.output_fd)
        else:
            print(_("See 'snap info <snapname>' for additional versions."), file=self.output_fd)
        print("", file=self.output_fd)
        self.output_fd.flush()
        
    def advise(self, command, ignore_installed=False):
        " give advice where to find the given command to stderr "
        def _in_prefix(prefix, command):
            " helper that returns if a command is found in the given prefix "
            return (os.path.exists(os.path.join(prefix, command))
                    and not os.path.isdir(os.path.join(prefix, command)))

        if len(command) > self.max_len:
            return False
        
        if command.startswith("/"):
            if os.path.exists(command):
                prefixes = [os.path.dirname(command)]
            else:
                prefixes = []
        else:
            prefixes = [prefix for prefix in self.prefixes if _in_prefix(prefix, command)]

        # check if we have it in a common prefix that may not be in the PATH
        if prefixes and not ignore_installed:
            if len(prefixes) == 1:
                print(_("Command '%(command)s' is available in '%(place)s'") % {"command": command, "place": os.path.join(prefixes[0], command)}, file=self.output_fd)
            else:
                print(_("Command '%(command)s' is available in the following places") % {"command": command}, file=self.output_fd)
                for prefix in prefixes:
                    print(" * %s" % os.path.join(prefix, command), file=self.output_fd)
            missing = list(set(prefixes) - set(os.getenv("PATH", "").split(":")))
            if len(missing) > 0:
                print(_("The command could not be located because '%s' is not included in the PATH environment variable.") % ":".join(missing), file=self.output_fd)
                if "sbin" in ":".join(missing):
                    print(_("This is most likely caused by the lack of administrative privileges associated with your user account."), file=self.output_fd)
            return False

        # do not give advice if we are in a situation where apt
        # or aptitude are not available (LP: #394843)
        if not (os.path.exists("/usr/bin/apt") or
                os.path.exists("/usr/bin/aptitude")):
            return False

        if command in self.getBlacklist():
            return False
        packages = self.get_packages(command)
        snaps, mispell_snaps = self.get_snaps(command)
        logging.debug("got debs: %s snaps: %s" % (packages, snaps))
        if len(packages) == 0 and len(snaps) == 0:
            mispell_packages = self.spelling_suggestions(command)
            if len(mispell_packages) > 0 or len(mispell_snaps) > 0:
                self.print_spelling_suggestions(command, mispell_packages, mispell_snaps)
        elif len(packages) == 0 and len(snaps) == 1:
            self.advice_single_snap_package(command, packages, snaps)
        elif len(snaps) > 0 and len(packages) == 0:
            self.advice_multi_snap_packages(command, packages, snaps)
        elif len(packages) == 1 and len(snaps) == 0:
            self.advice_single_deb_package(command, packages, snaps)
        elif len(packages) > 1 and len(snaps) == 0:
            self.advice_multi_deb_package(command, packages, snaps)
        elif len(packages) > 0 and len(snaps) > 0:
            self.advice_multi_mixed_packages(command, packages, snaps)

        # python is special, on 18.04 and newer python2 is no longer installed
        # which means there is no "python" binary. However python3 is installed
        # by default. So in addition to the advise how to install it from the
        # repo also add information that python3 is already installed.
        if command == "python" and os.path.exists("/usr/bin/python3"):
            print("You also have python3 installed, you can run 'python3' instead.")
            print("")

        return (len(packages) > 0 or len(snaps) > 0 or
                len(mispell_snaps) > 0 or len(mispell_packages) > 0)
