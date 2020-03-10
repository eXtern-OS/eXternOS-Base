# (c) 2006 Canonical
# Author: Michael Vogt <michael.vogt@ubuntu.com>
#
# Released under the GPL
#

from __future__ import print_function
from __future__ import absolute_import

import warnings
warnings.filterwarnings("ignore", "apt API not stable yet", FutureWarning)
import apt
import dbus
import os

import language_support_pkgs
from LanguageSelector.LocaleInfo import LocaleInfo
import LanguageSelector.LangCache
from LanguageSelector.utils import *
from LanguageSelector import macros

# the language-selector abstraction
class LanguageSelectorBase(object):
    """ base class for language-selector code """

    def __init__(self, datadir=""):
        self._datadir = datadir
        # load the localeinfo "database"
        self._localeinfo = LocaleInfo("languagelist", self._datadir)
        self._cache = None

    def openCache(self, progress):
        self._cache = LanguageSelector.LangCache.LanguageSelectorPkgCache(self._localeinfo, progress)

    def getMissingLangPacks(self):
        """
        return a list of language packs that are not installed
        but should be installed
        """
        if self._datadir:
            ls = language_support_pkgs.LanguageSupport(self._cache, 
                    os.path.join(self._datadir, "data", "pkg_depends"))
        else:
            ls = language_support_pkgs.LanguageSupport(self._cache)
        missing = []
        for pack in ls.missing():  # ls.missing() returns a set; we need a list
            missing.append(pack)
        return missing

    def writeSysFormatsSetting(self, sysFormats):
        """ write various LC_* variables (e.g. de_DE.UTF-8) """
        bus = dbus.SystemBus()
        obj = bus.get_object('com.ubuntu.LanguageSelector','/')
        iface = dbus.Interface(obj,dbus_interface="com.ubuntu.LanguageSelector")
        iface.SetSystemDefaultFormatsEnv(sysFormats)

    def writeSysLanguageSetting(self, sysLanguage):
        """ write the system "LANGUAGE" and "LANG" variables """
        bus = dbus.SystemBus()
        obj = bus.get_object('com.ubuntu.LanguageSelector','/')
        iface = dbus.Interface(obj,dbus_interface="com.ubuntu.LanguageSelector")
        iface.SetSystemDefaultLanguageEnv(sysLanguage)

    def writeUserFormatsSetting(self, userFormats):
        """ write various LC_* variables (e.g. de_DE.UTF-8) """
        uid = os.getuid()
        if uid == 0:
            warnings.warn("No formats locale saved for user '%s'." % os.getenv('USER'))
            return
        bus = dbus.SystemBus()
        obj = bus.get_object('org.freedesktop.Accounts',
                            '/org/freedesktop/Accounts/User%i' % uid)
        iface = dbus.Interface(obj, dbus_interface='org.freedesktop.Accounts.User')
        macr = macros.LangpackMacros(self._datadir, userFormats)
        iface.SetFormatsLocale(macr['SYSLOCALE'])

    def writeUserLanguageSetting(self, userLanguage):
        """ write the user "LANGUAGE" and "LANG" variables """
        uid = os.getuid()
        if uid == 0:
            warnings.warn("No language saved for user '%s'." % os.getenv('USER'))
            return
        bus = dbus.SystemBus()
        obj = bus.get_object('org.freedesktop.Accounts',
                            '/org/freedesktop/Accounts/User%i' % uid)
        iface = dbus.Interface(obj, dbus_interface='org.freedesktop.Accounts.User')
        iface.SetLanguage(self.validateLangList(userLanguage))

    def validateLangList(self, userLanguage):
        """
        remove elements which can be assumed to cause user confusion
        """
        tmp = []
        is_eng = False
        for lang in userLanguage.split(':'):
            if lang == 'en_US':
                tmp.extend(['en_US', 'en'])
                break
            elif lang.startswith('en_') or lang == 'en':
                tmp.append(lang)
                is_eng = True
            elif not is_eng:
                tmp.append(lang)
        validatedLangList = ':'.join(tmp)
        if validatedLangList != userLanguage:
            warnings.warn('The language list was modified by the program.')
        return validatedLangList


if __name__ == "__main__":
    lsb = LanguageSelectorBase(datadir="..")
    lsb.openCache(apt.progress.OpProgress())
    print(lsb.verifyPackageLists())


