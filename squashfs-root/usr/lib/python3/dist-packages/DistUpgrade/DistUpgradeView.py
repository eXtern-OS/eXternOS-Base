# DistUpgradeView.py 
#  
#  Copyright (c) 2004,2005 Canonical
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

from .DistUpgradeGettext import gettext as _
from .DistUpgradeGettext import ngettext
from .telemetry import get as get_telemetry
import apt
from enum import Enum
import errno
import os
import apt_pkg 
import locale
import logging
import signal
import select

from .DistUpgradeApport import apport_pkgfailure


try:
    locale.setlocale(locale.LC_ALL, "")
    (code, ENCODING) = locale.getdefaultlocale()
except:
    logging.exception("getting the encoding failed")
    ENCODING = "utf-8"   #pyflakes

# if there is no encoding, setup UTF-8
if not ENCODING:
    ENCODING = "utf-8"
    os.putenv("LC_CTYPE", "C.UTF-8")
    try:
        locale.setlocale(locale.LC_CTYPE, "C.UTF-8")
    except locale.error:
        pass


# log locale information
logging.info("locale: '%s' '%s'" % locale.getlocale())


def FuzzyTimeToStr(sec):
  " return the time a bit fuzzy (no seconds if time > 60 secs "
  #print("FuzzyTimeToStr: ", sec)
  sec = int(sec)

  days = sec//(60*60*24)
  hours = sec//(60*60) % 24
  minutes = (sec//60) % 60
  seconds = sec % 60
  # 0 seonds remaining looks wrong and its "fuzzy" anyway
  if seconds == 0:
    seconds = 1

  # string map to make the re-ordering possible
  map = { "str_days" : "",
          "str_hours" : "",
          "str_minutes" : "",
          "str_seconds" : ""
        }
  
  # get the fragments, this is not ideal i18n wise, but its
  # difficult to do it differently
  if days > 0:
    map["str_days"] = ngettext("%li day","%li days", days) % days
  if hours > 0:
    map["str_hours"] = ngettext("%li hour","%li hours", hours) % hours
  if minutes > 0:
    map["str_minutes"] = ngettext("%li minute","%li minutes", minutes) % minutes
  map["str_seconds"] = ngettext("%li second","%li seconds", seconds) % seconds

  # now assemble the string
  if days > 0:
    # Don't print str_hours if it's an empty string, see LP: #288912
    if map["str_hours"] == '':
        return map["str_days"]
    # TRANSLATORS: you can alter the ordering of the remaining time
    # information here if you shuffle %(str_days)s %(str_hours)s %(str_minutes)s
    # around. Make sure to keep all '$(str_*)s' in the translated string
    # and do NOT change anything appart from the ordering.
    #
    # %(str_hours)s will be either "1 hour" or "2 hours" depending on the
    # plural form
    # 
    # Note: most western languages will not need to change this
    return _("%(str_days)s %(str_hours)s") % map
  # display no minutes for time > 3h, see LP: #144455
  elif hours > 3:
    return map["str_hours"]
  # when we are near the end, become more precise again
  elif hours > 0:
    # Don't print str_minutes if it's an empty string, see LP: #288912
    if map["str_minutes"] == '':
        return map["str_hours"]
    # TRANSLATORS: you can alter the ordering of the remaining time
    # information here if you shuffle %(str_hours)s %(str_minutes)s
    # around. Make sure to keep all '$(str_*)s' in the translated string
    # and do NOT change anything appart from the ordering.
    #
    # %(str_hours)s will be either "1 hour" or "2 hours" depending on the
    # plural form
    # 
    # Note: most western languages will not need to change this
    return _("%(str_hours)s %(str_minutes)s") % map
  elif minutes > 0:
    return map["str_minutes"]
  return map["str_seconds"]


class AcquireProgress(apt.progress.base.AcquireProgress):

  def __init__(self):
    super(AcquireProgress, self).__init__()
    self.est_speed = 0.0
  def start(self):
    super(AcquireProgress, self).start()
    self.est_speed = 0.0
    self.eta = 0.0
    self.percent = 0.0
    self.release_file_download_error = False
  def update_status(self, uri, descr, shortDescr, status):
    super(AcquireProgress, self).update_status(uri, descr, shortDescr, status)
    # FIXME: workaround issue in libapt/python-apt that does not 
    #        raise a exception if *all* files fails to download
    if status == apt_pkg.STAT_FAILED:
      logging.warning("update_status: dlFailed on '%s' " % uri)
      if uri.endswith("Release.gpg") or uri.endswith("Release"):
        # only care about failures from network, not gpg, bzip, those
        # are different issues
        for net in ["http","ftp","mirror"]:
          if uri.startswith(net):
            self.release_file_download_error = True
            break
  # required, otherwise the lucid version of python-apt gets really
  # unhappy, its expecting this function for apt.progress.base.AcquireProgress
  def pulse_items(self, arg):
    return True
  def pulse(self, owner=None):
    super(AcquireProgress, self).pulse(owner)
    self.percent = (((self.current_bytes + self.current_items) * 100.0) /
                    float(self.total_bytes + self.total_items))
    if self.current_cps > self.est_speed:
      self.est_speed = (self.est_speed+self.current_cps)/2.0
    if self.current_cps > 0:
      self.eta = ((self.total_bytes - self.current_bytes) /
                  float(self.current_cps))
    return True
  def isDownloadSpeedEstimated(self):
    return (self.est_speed != 0)
  def estimatedDownloadTime(self, required_download):
    """ get the estimated download time """
    if self.est_speed == 0:
      timeModem = required_download/(56*1024/8)  # 56 kbit 
      timeDSL = required_download/(1024*1024/8)  # 1Mbit = 1024 kbit
      s= _("This download will take about %s with a 1Mbit DSL connection "
           "and about %s with a 56k modem.") % (FuzzyTimeToStr(timeDSL), FuzzyTimeToStr(timeModem))
      return s
    # if we have a estimated speed, use it
    s = _("This download will take about %s with your connection. ") % FuzzyTimeToStr(required_download/self.est_speed)
    return s
    


class InstallProgress(apt.progress.base.InstallProgress):
  """ Base class for InstallProgress that supports some fancy
      stuff like apport integration
  """
  def __init__(self):
    apt.progress.base.InstallProgress.__init__(self)
    self.master_fd = None

  def wait_child(self):
      """Wait for child progress to exit.

      The return values is the full status returned from os.waitpid()
      (not only the return code).
      """
      while True:
          try:
              select.select([self.statusfd], [], [], self.select_timeout)
          except select.error as e:
              if e.args[0] != errno.EINTR:
                  raise
          self.update_interface()
          try:
              (pid, res) = os.waitpid(self.child_pid, os.WNOHANG)
              if pid == self.child_pid:
                  break
          except OSError as e:
              if e.errno != errno.EINTR:
                  raise
              if e.errno == errno.ECHILD:
                  break
      return res

  def run(self, pm):
    pid = self.fork()
    if pid == 0:
      # child, ignore sigpipe, there are broken scripts out there
      # like etckeeper (LP: #283642)
      signal.signal(signal.SIGPIPE,signal.SIG_IGN) 
      try:
        res = pm.do_install(self.writefd)
      except Exception as e:
        print("Exception during pm.DoInstall(): ", e)
        logging.exception("Exception during pm.DoInstall()")
        with open("/var/run/ubuntu-release-upgrader-apt-exception","w") as f:
            f.write(str(e))
        os._exit(pm.RESULT_FAILED)
      os._exit(res)
    self.child_pid = pid
    res = os.WEXITSTATUS(self.wait_child())
    return res
  
  def error(self, pkg, errormsg):
    " install error from a package "
    apt.progress.base.InstallProgress.error(self, pkg, errormsg)
    logging.error("got an error from dpkg for pkg: '%s': '%s'" % (pkg, errormsg))
    if "/" in pkg:
      pkg = os.path.basename(pkg)
    if "_" in pkg:
      pkg = pkg.split("_")[0]
    # now run apport
    apport_pkgfailure(pkg, errormsg)

class DumbTerminal(object):
    def call(self, cmd, hidden=False):
        " expects a command in the subprocess style (as a list) "
        import subprocess
        subprocess.call(cmd)

class DummyHtmlView(object):
    def open(self, url):
        pass
    def show(self):
      pass
    def hide(self):
      pass

class Step(Enum):
    PREPARE = 1
    MODIFY_SOURCES = 2
    FETCH = 3
    INSTALL = 4
    CLEANUP = 5
    REBOOT = 6
    N = 7

# Declare these translatable strings from the .ui files here so that
# xgettext picks them up.
( _("Preparing to upgrade"),
  _("Getting new software channels"),
  _("Getting new packages"),
  _("Installing the upgrades"),
  _("Cleaning up"),
)

class DistUpgradeView(object):
    " abstraction for the upgrade view "
    def __init__(self):
        self.needs_screen = False
        pass
    def getOpCacheProgress(self):
        " return a OpProgress() subclass for the given graphic"
        return apt.progress.base.OpProgress()
    def getAcquireProgress(self):
        " return an acquire progress object "
        return AcquireProgress()
    def getInstallProgress(self, cache=None):
        " return a install progress object "
        return InstallProgress()
    def getTerminal(self):
        return DumbTerminal()
    def getHtmlView(self):
        return DummyHtmlView()
    def updateStatus(self, msg):
        """ update the current status of the distUpgrade based
            on the current view
        """
        pass
    def abort(self):
        """ provide a visual feedback that the upgrade was aborted """
        pass
    def setStep(self, step):
        """ we have 6 steps current for a upgrade:
        1. Analyzing the system
        2. Updating repository information
        3. fetch packages
        3. Performing the upgrade
        4. Post upgrade stuff
        5. Complete
        """
        get_telemetry().add_stage(step.name)
        pass
    def hideStep(self, step):
        " hide a certain step from the GUI "
        pass
    def showStep(self, step):
        " show a certain step from the GUI "
        pass
    def confirmChanges(self, summary, changes, demotions, downloadSize,
                       actions=None, removal_bold=True):
        """ display the list of changed packages (apt.Package) and
            return if the user confirms them
        """
        self.confirmChangesMessage = ""
        self.demotions = demotions
        self.toInstall = []
        self.toReinstall = []
        self.toUpgrade = []
        self.toRemove = []
        self.toRemoveAuto = []
        self.toDowngrade = []
        for pkg in changes:
            if pkg.marked_install: 
              self.toInstall.append(pkg)
            elif pkg.marked_upgrade: 
              self.toUpgrade.append(pkg)
            elif pkg.marked_reinstall:
              self.toReinstall.append(pkg)
            elif pkg.marked_delete:
              if pkg._pcache._depcache.is_auto_installed(pkg._pkg):
                self.toRemoveAuto.append(pkg)
              else:
                self.toRemove.append(pkg)
            elif pkg.marked_downgrade: 
              self.toDowngrade.append(pkg)
        # do not bother the user with a different treeview
        self.toInstall = self.toInstall + self.toReinstall
        # sort it
        self.toInstall.sort()
        self.toUpgrade.sort()
        self.toRemove.sort()
        self.toRemoveAuto.sort()
        self.toDowngrade.sort()
        # now build the message (the same for all frontends)
        msg = "\n"
        pkgs_remove = len(self.toRemove) + len(self.toRemoveAuto)
        pkgs_inst = len(self.toInstall) + len(self.toReinstall)
        pkgs_upgrade = len(self.toUpgrade)
        # FIXME: show detailed packages
        if len(self.demotions) > 0:
          msg += ngettext(
            "%(amount)d installed package is no longer supported by Canonical. "
            "You can still get support from the community.",
            "%(amount)d installed packages are no longer supported by "
            "Canonical. You can still get support from the community.",
            len(self.demotions)) % { 'amount' : len(self.demotions) }
          msg += "\n\n"
        if pkgs_remove > 0:
          # FIXME: make those two separate lines to make it clear
          #        that the "%" applies to the result of ngettext
          msg += ngettext("%d package is going to be removed.",
                          "%d packages are going to be removed.",
                          pkgs_remove) % pkgs_remove
          msg += " "
        if pkgs_inst > 0:
          msg += ngettext("%d new package is going to be "
                          "installed.",
                          "%d new packages are going to be "
                          "installed.",pkgs_inst) % pkgs_inst
          msg += " "
        if pkgs_upgrade > 0:
          msg += ngettext("%d package is going to be upgraded.",
                          "%d packages are going to be upgraded.",
                          pkgs_upgrade) % pkgs_upgrade
          msg +=" "
        if downloadSize > 0:
          downloadSizeStr = apt_pkg.size_to_str(downloadSize)
          if isinstance(downloadSizeStr, bytes):
              downloadSizeStr = downloadSizeStr.decode(ENCODING)
          msg += _("\n\nYou have to download a total of %s. ") % (
              downloadSizeStr)
          msg += self.getAcquireProgress().estimatedDownloadTime(downloadSize)
        if ((pkgs_upgrade + pkgs_inst) > 0) and ((pkgs_upgrade + pkgs_inst + pkgs_remove) > 100):
          if self.getAcquireProgress().isDownloadSpeedEstimated():
            msg += "\n\n%s" % _( "Installing the upgrade "
                                 "can take several hours. Once the download "
                                 "has finished, the process cannot be canceled.")
          else:
            msg += "\n\n%s" % _( "Fetching and installing the upgrade "
                                 "can take several hours. Once the download "
                                 "has finished, the process cannot be canceled.")
        else:
          if pkgs_remove > 100:
            msg += "\n\n%s" % _( "Removing the packages "
                                 "can take several hours. ")
        # Show an error if no actions are planned
        if (pkgs_upgrade + pkgs_inst + pkgs_remove) < 1:
          # FIXME: this should go into DistUpgradeController
          summary = _("The software on this computer is up to date.")
          msg = _("There are no upgrades available for your system. "
                  "The upgrade will now be canceled.")
          self.error(summary, msg)
          return False
        # set the message
        self.confirmChangesMessage = msg
        return True

    def askYesNoQuestion(self, summary, msg, default='No'):
        " ask a Yes/No question and return True on 'Yes' "
        pass
    def confirmRestart(self):
        " generic ask about the restart, can be overridden "
        summary = _("Reboot required")
        msg =  _("The upgrade is finished and "
                 "a reboot is required. "
                 "Do you want to do this "
                 "now?")
        return self.askYesNoQuestion(summary, msg)
    def error(self, summary, msg, extended_msg=None):
        " display a error "
        pass
    def information(self, summary, msg, extended_msg=None):
        " display a information msg"
        pass
    def processEvents(self):
        """ process gui events (to keep the gui alive during a long
            computation """
        pass
    def pulseProgress(self, finished=False):
      """ do a progress pulse (e.g. bounce a bar back and forth, show
          a spinner)
      """
      pass
    def showDemotions(self, summary, msg, demotions):
      """
      show demoted packages to the user, default implementation
      is to just show a information dialog
      """
      self.information(summary, msg, "\n".join(demotions))

if __name__ == "__main__":
  fp = AcquireProgress()
  fp.pulse()
