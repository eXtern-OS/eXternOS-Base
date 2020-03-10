# LocaleInfo.py (c) 2006 Canonical, released under the GPL
#
# a helper class to get locale info

from __future__ import print_function
from __future__ import absolute_import

import re            
import subprocess
import gettext
import os
import pwd
import sys
import dbus
import warnings

from LanguageSelector import macros

from gettext import gettext as _
from xml.etree.ElementTree import ElementTree

class LocaleInfo(object):
    " class with handy functions to parse the locale information "
    
    environments = ["/etc/default/locale"]
    def __init__(self, languagelist_file, datadir):
        self._datadir = datadir
        LANGUAGELIST = os.path.join(datadir, 'data', languagelist_file)
        # map language to human readable name, e.g.:
        # "pt"->"Portuguise", "de"->"German", "en"->"English"
        self._lang = {}

        # map country to human readable name, e.g.:
        # "BR"->"Brasil", "DE"->"Germany", "US"->"United States"
        self._country = {}
        
        # map locale (language+country) to the LANGUAGE environment, e.g.:
        # "pt_PT"->"pt_PT:pt:pt_BR:en_GB:en"
        self._languagelist = {}
        
        # read lang file
        et = ElementTree(file="/usr/share/xml/iso-codes/iso_639_3.xml")
        it = et.iter('iso_639_3_entry')
        for elm in it:
            if "common_name" in elm.attrib:
                lang = elm.attrib["common_name"]
            else:
                lang = elm.attrib["name"]
            if "part1_code" in elm.attrib:
                code = elm.attrib["part1_code"]
            else:
                code = elm.attrib["id"]
            self._lang[code] = lang
        # Hack for Chinese langpack split
        # Translators: please translate 'Chinese (simplified)' and 'Chinese (traditional)' so that they appear next to each other when sorted alphabetically.
        self._lang['zh-hans'] = _("Chinese (simplified)")
        # Translators: please translate 'Chinese (simplified)' and 'Chinese (traditional)' so that they appear next to each other when sorted alphabetically.
        self._lang['zh-hant'] = _("Chinese (traditional)")
        # end hack
        
        # read countries
        et = ElementTree(file="/usr/share/xml/iso-codes/iso_3166.xml")
        it = et.iter('iso_3166_entry')
        for elm in it:
            if "common_name" in elm.attrib:
                descr = elm.attrib["common_name"]
            else:
                descr = elm.attrib["name"]
            if "alpha_2_code" in elm.attrib:
                code = elm.attrib["alpha_2_code"]
            else:
                code = elm.attrib["alpha_3_code"]
            self._country[code] = descr
            
        # read the languagelist
        with open(LANGUAGELIST) as f:
            for line in f:
                tmp = line.strip()
                if tmp.startswith("#") or tmp == "":
                    continue
                w = tmp.split(";")
                # FIXME: the latest localechoosers "languagelist" does
                # no longer have this field for most languages, so
                # deal with it and don't set LANGUAGE then
                # - the interessting question is what to do
                # if LANGUAGE is already set and the new
                localeenv = w[6].split(":")
                #print(localeenv)
                self._languagelist[localeenv[0]] = '%s' % w[6]

    def lang(self, code):
        """ map language code to language name """
        if code in self._lang:
            return self._lang[code]
        return ""

    def country(self, code):
        """ map country code to country name"""
        if code in self._country:
            return self._country[code]
        return ""

    def generated_locales(self):
        """ return a list of locales available on the system
            (running locale -a) """
        locales = []
        p = subprocess.Popen(["locale", "-a"], stdout=subprocess.PIPE,
                             universal_newlines=True)
        for line in p.communicate()[0].split("\n"):
            tmp = line.strip()
            if tmp.find('.utf8') < 0:
                continue
            # we are only interessted in the locale, not the codec
            macr = macros.LangpackMacros(self._datadir, tmp)
            locale = macr["LOCALE"]
            if not locale in locales:
                locales.append(locale)
        #print(locales)
        return locales

    def translate_language(self, lang):
        "return translated language"
        if lang in self._lang:
            lang_name = gettext.dgettext('iso_639', self._lang[lang])
            if lang_name == self._lang[lang]:
                lang_name = gettext.dgettext('iso_639_3', self._lang[lang])
            return lang_name
        else:
            return lang

    def translate_country(self, country):
        """
        return translated language and country of the given
        locale into the given locale, e.g. 
        (Deutsch, Deutschland) for de_DE
        """

#        macr = macros.LangpackMacros(self._datadir, locale)

#        #(lang, country) = locale.split("_")
#        country = macr['CCODE']
#        current_language = None
#        if "LANGUAGE" in os.environ:
#            current_language = os.environ["LANGUAGE"]
#        os.environ["LANGUAGE"]=locale
#        lang_name = self.translate_language(macr['LCODE'])
        if country in self._country:
            country_name = gettext.dgettext('iso_3166', self._country[country])
            return country_name
        else:
            return country
#        if current_language:
#            os.environ["LANGUAGE"] = current_language
#        else:
#            del os.environ["LANGUAGE"]
#        return (lang_name, country_name)

    def translate(self, locale, native=False, allCountries=False):
        """ get a locale code and output a human readable name """
        returnVal = ''
        macr = macros.LangpackMacros(self._datadir, locale)
        if native == True:
            current_language = None
            if "LANGUAGE" in os.environ:
                current_language = os.environ["LANGUAGE"]
            os.environ["LANGUAGE"] = macr["LOCALE"]

        lang_name = self.translate_language(macr["LCODE"])
        returnVal = lang_name
        if len(macr["CCODE"]) > 0:
            country_name = self.translate_country(macr["CCODE"])
            # get all locales for this language
            l = [k for k in self.generated_locales() if k.startswith(macr['LCODE'])]
            # only show region/country if we have more than one 
            if (allCountries == False and len(l) > 1) or allCountries == True:
                mycountry = self.country(macr['CCODE'])
                if mycountry:
                    returnVal = "%s (%s)" % (lang_name, country_name)
        if len(macr["VARIANT"]) > 0:
            returnVal = "%s - %s" % (returnVal, macr["VARIANT"])
        
        if native == True:
            if current_language:
                os.environ["LANGUAGE"] = current_language
            else:
                del os.environ["LANGUAGE"]
        return returnVal
         
#        if "_" in locale:
#            #(lang, country) = locale.split("_")
#            (lang_name, country_name) = self.translate_locale(locale)
#            # get all locales for this language
#            l = [k for k in self.generated_locales() if k.startswith(macr['LCODE'])]
#            # only show region/country if we have more than one 
#            if len(l) > 1:
#                mycountry = self.country(macr['CCODE'])
#                if mycountry:
#                    return "%s (%s)" % (lang_name, country_name)
#                else:
#                    return lang_name
#            else:
#                return lang_name
#        return self.translate_language(locale)

    def makeEnvString(self, code):
        """ input is a language code, output a string that can be put in
            the LANGUAGE enviroment variable.
            E.g: en_DK -> en_DK:en
        """
        if not code:
            return ''
        macr = macros.LangpackMacros(self._datadir, code)
        langcode = macr['LCODE']
        locale = macr['LOCALE']
        # first check if we got somethign from languagelist
        if locale in self._languagelist:
            langlist = self._languagelist[locale]
        # if not, fall back to "dumb" behaviour
        elif locale == langcode:
            langlist = locale
        else:
            langlist = "%s:%s" % (locale, langcode)
        if not (langlist.endswith(':en') or langlist == 'en'):
            langlist = "%s:en" % langlist
        return langlist

    def getUserDefaultLanguage(self):
        formats = ''
        language = ''
        result = []
        fname = os.path.expanduser("~/.pam_environment")
        if os.path.exists(fname) and \
           os.access(fname, os.R_OK):
            with open(fname) as f:
                for line in f:
                    match_language = re.match(r'LANGUAGE(\s+DEFAULT)?=(.*)$',line)
                    if match_language:
                        language = match_language.group(2)
        user_name = pwd.getpwuid(os.geteuid()).pw_name
        try:
            bus = dbus.SystemBus()
            obj = bus.get_object('org.freedesktop.Accounts', '/org/freedesktop/Accounts')
            iface = dbus.Interface(obj, dbus_interface='org.freedesktop.Accounts')
            user_path = iface.FindUserByName(user_name)

            obj = bus.get_object('org.freedesktop.Accounts', user_path)
            iface = dbus.Interface(obj, dbus_interface='org.freedesktop.DBus.Properties')
            formats = iface.Get('org.freedesktop.Accounts.User', 'FormatsLocale')
            if len(language) == 0:
                firstLanguage = iface.Get('org.freedesktop.Accounts.User', 'Language')
                language = self.makeEnvString(firstLanguage)
        except Exception as msg:
            # a failure here shouldn't trigger a fatal error
            warnings.warn(msg.args[0])
            pass
        if len(language) == 0 and "LANGUAGE" in os.environ:
            language = os.environ["LANGUAGE"]
        if len(formats) == 0 and "LC_NAME" in os.environ:
            formats = os.environ["LC_NAME"]
        if len(formats) == 0 and "LANG" in os.environ:
            formats = os.environ["LANG"]
        if len(formats) > 0 and len(language) == 0:
            language = self.makeEnvString(formats)
        result.append(formats)
        result.append(language)
        return result

    def getSystemDefaultLanguage(self):
        lang = ''
        formats = ''
        language = ''
        result = []
        for fname in self.environments:
            if os.path.exists(fname) and \
               os.access(fname, os.R_OK):
                with open(fname) as f:
                    for line in f:
                        # support both LANG="foo" and LANG=foo
                        if line.startswith("LANG"):
                            line = line.replace('"','')
                        match_lang = re.match(r'LANG=(.*)$',line)
                        if match_lang:
                            lang = match_lang.group(1)
                        if line.startswith("LC_TIME"):
                            line = line.replace('"','')
                        match_formats = re.match(r'LC_TIME=(.*)$',line)
                        if match_formats:
                            formats = match_formats.group(1)
                        if line.startswith("LANGUAGE"):
                            line = line.replace('"','')
                        match_language = re.match(r'LANGUAGE=(.*)$',line)
                        if match_language:
                            language = match_language.group(1)
        if len(lang) == 0:
            # fall back is 'en_US'
            lang = 'en_US.UTF-8'
        if len(language) == 0:
            # LANGUAGE has not been defined, generate a string from the provided LANG value
            language = self.makeEnvString(lang)
        if len(formats) == 0:
            formats = lang
        result.append(formats)
        result.append(language)
        return result

    def isSetSystemFormats(self):
        if not os.access(self.environments[0], os.R_OK):
            return False
        with open(self.environments[0]) as f:
            for line in f:
                if line.startswith("LC_TIME="):
                    return True
        return False


if __name__ == "__main__":
    datadir = "/usr/share/language-selector/"
    li = LocaleInfo("languagelist", datadir)

    print("default system locale and languages: '%s'" % li.getSystemDefaultLanguage())
    print("default user locale and languages: '%s'" % li.getUserDefaultLanguage())

    print(li._lang)
    print(li._country)
    print(li._languagelist)
    print(li.generated_locales())
