
import os
import logging
import subprocess
import sys
import gettext
import errno

APPORT_WHITELIST = {
    "apt.log": "Aptlog",
    "apt-term.log": "Apttermlog",
    "apt-clone_system_state.tar.gz": "Aptclonesystemstate.tar.gz",
    "history.log": "Historylog",
    "lspci.txt": "Lspcitxt",
    "main.log": "Mainlog",
    "term.log": "Termlog",
    "screenlog.0": "Screenlog",
    "xorg_fixup.log": "Xorgfixup",
}


def _apport_append_logfiles(report, logdir="/var/log/dist-upgrade/"):
    dirname = 'VarLogDistupgrade'
    for fname in APPORT_WHITELIST:
        f = os.path.join(logdir, fname)
        if not os.path.isfile(f) or os.path.getsize(f) == 0:
            continue
        ident = dirname + APPORT_WHITELIST[fname]
        if os.access(f, os.R_OK):
            report[ident] = (open(f), )
        elif os.path.exists(f):
            try:
                from apport.hookutils import root_command_output
                report[ident] = root_command_output(
                    ["cat", '%s' % f], decode_utf8=False)
            except ImportError:
                logging.error("failed to import apport python module, "
                              "can't include: %s" % ident)


def apport_crash(type, value, tb):
    logging.debug("running apport_crash()")
    if "RELEASE_UPRADER_NO_APPORT" in os.environ:
        logging.debug("RELEASE_UPRADER_NO_APPORT env set")
        return False
    try:
        # we don't depend on python3-apport because of servers
        from apport_python_hook import apport_excepthook
        from apport.report import Report
    except ImportError as e:
        logging.error("failed to import apport python module, can't "
                      "generate crash: %s" % e)
        return False
    from .DistUpgradeVersion import VERSION
    # we pretend we are do-release-upgrade
    sys.argv[0] = "/usr/bin/do-release-upgrade"
    apport_excepthook(type, value, tb)
    # now add the files in /var/log/dist-upgrade/*
    if os.path.exists('/var/crash/_usr_bin_do-release-upgrade.0.crash'):
        report = Report()
        report.setdefault('Tags', 'dist-upgrade')
        release = 'Ubuntu %s' % VERSION[0:5]
        report.setdefault('DistroRelease', release)
        # use the version of the release-upgrader tarball, not the installed
        # package
        report.setdefault('Package', 'ubuntu-release-upgrader-core 1:%s' %
                          VERSION)
        _apport_append_logfiles(report)
        report.add_to_existing(
            '/var/crash/_usr_bin_do-release-upgrade.0.crash')
    return True


def apport_pkgfailure(pkg, errormsg):
    logging.debug("running apport_pkgfailure() %s: %s", pkg, errormsg)
    if "RELEASE_UPRADER_NO_APPORT" in os.environ:
        logging.debug("RELEASE_UPRADER_NO_APPORT env set")
        return False
    LOGDIR = "/var/log/dist-upgrade/"
    s = "/usr/share/apport/package_hook"

    # we do not report followup errors from earlier failures
    # dpkg messages will not be translated if DPKG_UNTRANSLATED_MESSAGES is
    # set which it is by default so check for the English message first
    if "dependency problems - leaving unconfigured" in errormsg:
        logging.debug("dpkg error because of dependency problems, not "
                      "reporting against %s " % pkg)
        return False
    needle = gettext.dgettext(
        'dpkg', "dependency problems - leaving unconfigured")
    if needle in errormsg:
        logging.debug("dpkg error because of dependency problems, not "
                      "reporting against %s " % pkg)
        return False
    # we do not run apport_pkgfailure for full disk errors
    if os.strerror(errno.ENOSPC) in errormsg:
        logging.debug("dpkg error because of full disk, not reporting "
                      "against %s " % pkg)
        return False

    if os.path.exists(s):
        args = [s, "-p", pkg]
        args.extend(["--tags", "dist-upgrade"])
        for fname in APPORT_WHITELIST:
            args.extend(["-l", os.path.join(LOGDIR, fname)])
        try:
            p = subprocess.Popen(args, stdin=subprocess.PIPE,
                                 universal_newlines=True)
            p.stdin.write(errormsg)
            p.stdin.close()
            #p.wait()
        except Exception as e:
            logging.warning("Failed to run apport (%s)" % e)
            return False
        return True
    return False


def run_apport():
    " run apport, check if we have a display "
    if "RELEASE_UPRADER_NO_APPORT" in os.environ:
        logging.debug("RELEASE_UPRADER_NO_APPORT env set")
        return False
    if "DISPLAY" in os.environ:
        # update-notifier will notify about the crash
        return True
    elif os.path.exists("/usr/bin/apport-cli"):
        try:
            return (subprocess.call("/usr/bin/apport-cli") == 0)
        except Exception:
            logging.exception("Unable to launch '/usr/bin/apport-cli'")
            return False
    logging.debug("can't find apport")
    return False


if __name__ == "__main__":
    apport_crash(None, None, None)
