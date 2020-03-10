from __future__ import print_function

import warnings
warnings.filterwarnings("ignore", "apt API not stable yet", FutureWarning)
import apt

import language_support_pkgs

class LanguagePackageStatus(object):
    def __init__(self, languageCode, pkg_template):
        self.languageCode = languageCode
        self.pkgname_template = pkg_template
        self.available = False
        self.installed = False
        self.doChange = False

    def __str__(self):
        return 'LanguagePackageStatus(langcode: %s, pkgname %s, available: %s, installed: %s, doChange: %s' % (
                self.languageCode, self.pkgname_template, str(self.available),
                str(self.installed), str(self.doChange))

# the language-support information
class LanguageInformation(object):
    def __init__(self, cache, languageCode=None, language=None):
        #FIXME:
        #needs a new structure:
        #languagePkgList[LANGCODE][tr|fn|in|wa]=[packages available for that language in that category]
        #@property for each category
        #@property for each LANGCODE
        self.languageCode = languageCode
        self.language = language
        # langPack/support status 
        self.languagePkgList = {}
        self.languagePkgList["languagePack"] = LanguagePackageStatus(languageCode, "language-pack-%s")
        for langpkg_status in self.languagePkgList.values():
            pkgname = langpkg_status.pkgname_template % languageCode
            langpkg_status.available = pkgname in cache
            if langpkg_status.available:
                langpkg_status.installed = cache[pkgname].is_installed
        
    @property
    def inconsistent(self):
        " returns True if only parts of the language support packages are installed "
        if (not self.notInstalled and not self.fullInstalled) : return True
        return False
    @property
    def fullInstalled(self):
        " return True if all of the available language support packages are installed "
        for pkg in self.languagePkgList.values() :
            if not pkg.available : continue
            if not ((pkg.installed and not pkg.doChange) or (not pkg.installed and pkg.doChange)) : return False
        return True
    @property
    def notInstalled(self):
        " return True if none of the available language support packages are installed "
        for pkg in self.languagePkgList.values() :
            if not pkg.available : continue
            if not ((not pkg.installed and not pkg.doChange) or (pkg.installed and pkg.doChange)) : return False
        return True
    @property
    def changes(self):
        " returns true if anything in the state of the language packs/support changes "
        for pkg in self.languagePkgList.values() :
            if (pkg.doChange) : return True
        return False
    def __str__(self):
        return "%s (%s)" % (self.language, self.languageCode)

# the pkgcache stuff
class ExceptionPkgCacheBroken(Exception):
    pass

class LanguageSelectorPkgCache(apt.Cache):

    def __init__(self, localeinfo, progress):
        apt.Cache.__init__(self, progress)
        if self._depcache.broken_count > 0:
            raise ExceptionPkgCacheBroken()
        self._localeinfo = localeinfo
        self.lang_support = language_support_pkgs.LanguageSupport(self)

    @property
    def havePackageLists(self):
        " verify that a network package lists exists "
        for metaindex in self._list.list:
            for indexfile in metaindex.index_files:
                if indexfile.archive_uri("").startswith("cdrom:"):
                    continue
                if indexfile.archive_uri("").startswith("http://security.ubuntu.com"):
                    continue
                if indexfile.label != "Debian Package Index":
                    continue
                if indexfile.exists and indexfile.has_packages:
                    return True
        return False

    def clear(self):
        """ clear the selections """
        self._depcache.init()

    def getChangesList(self):
        to_inst = []
        to_rm = []
        for pkg in self.get_changes():
            if pkg.marked_install or pkg.marked_upgrade:
                to_inst.append(pkg.name)
            if pkg.marked_delete:
                to_rm.append(pkg.name)
        return (to_inst,to_rm)

    def tryChangeDetails(self, li):
        " commit changed status of list items"""
        # we iterate over items of type LanguagePackageStatus
        for (key, item) in li.languagePkgList.items():
            if item.doChange:
                pkgs = self.lang_support.by_locale(li.languageCode, installed=item.installed)
                #print("XXX pkg list for lang %s, installed: %s" % (item.languageCode, str(item.installed)))
                try:
                    if item.installed:
                        # We are selective when deleting language support packages to
                        # prevent removal of packages that are not language specific.
                        for pkgname in pkgs:
                            if pkgname.startswith('language-pack-') or \
                               pkgname.endswith('-' + li.languageCode):
                                self[pkgname].mark_delete()
                    else:
                        for pkgname in pkgs:
                            self[pkgname].mark_install()
                except SystemError:
                    raise ExceptionPkgCacheBroken()

    def getLanguageInformation(self):
        """ returns a list with language packs/support packages """
        res = []
        for (code, lang) in self._localeinfo._lang.items():
            if code == 'zh':
                continue
            li = LanguageInformation(self, code, lang)
            if [s for s in li.languagePkgList.values() if s.available]:
                res.append(li)

        return res


if __name__ == "__main__":

    from LocaleInfo import LocaleInfo
    datadir = "/usr/share/language-selector"
    li = LocaleInfo("languagelist", datadir)

    lc = LanguageSelectorPkgCache(li,apt.progress.OpProgress())
    print("available language information")
    print(", ".join(["%s" %x for x in lc.getLanguageInformation()]))
