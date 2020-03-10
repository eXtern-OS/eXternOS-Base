'''macros.py: Generate macro values from configuration values and provide
substitution functions.

The following macros are available:

  LCODE CCODE PKGCODE LOCALE
'''

from __future__ import print_function

import os
import re

def _file_map(file, key, sep = None):
    '''Look up key in given file ("key value" lines). Throw an exception if
    key was not found.'''

    val = None
    for l in open(file):
        try:
            (k, v) = l.split(sep)
        except ValueError:
            continue
        # sort out comments
        if k.find('#') >= 0 or v.find('#') >= 0:
            continue
        if k == key:
            val = v.strip()
    if val == None:
        raise KeyError('Key %s not found in %s' % (key, file))
    return val

class LangcodeMacros:
    
    LANGCODE_TO_LOCALE = '/usr/share/language-selector/data/langcode2locale'

    def __init__(self, langCode):
        self.macros = {}
        locales = {}
        for l in open(self.LANGCODE_TO_LOCALE):
            try:
                l = l.rstrip()
                (k, v) = l.split(':')
            except ValueError:
                continue
            if k.find('#') >= 0 or v.find('#') >= 0:
                continue
            if not k in locales:
                locales[k] = []
            locales[k].append(v)
        self['LOCALES'] = locales[langCode]

    def __getitem__(self, item):
        # return empty string as default
        return self.macros.get(item, '')

    def __setitem__(self, item, value):
        self.macros[item] = value

    def __contains__(self, item):
        return self.macros.__contains__(item)

class LangpackMacros:
    def __init__(self, datadir,locale):
        '''Initialize values of macros.

        This uses information from maps/, config/, some hardcoded aggregate
        strings (such as package names), and some external input:
        
        - locale: Standard locale representation (e. g. pt_BR.UTF-8)
                  Format is: ll[_CC][.UTF-8][@variant]
        '''

        self.LOCALE_TO_LANGPACK = os.path.join(datadir, 'data', 'locale2langpack')
        self.macros = {}
        self['LCODE'] = ''      # the language code
        self['CCODE'] = ''      # the country code if present
        self['VARIANT'] = ''    # the part behind the @ if present
        self['LOCALE'] = ''     # the locale with the .UTF-8 stripped off
        self['PKGCODE'] = ''    # the language code used in the language-packs
        self['SYSLOCALE'] = ''  # a generated full locale identifier, e.g. ca_ES.UTF-8@valencia
        # 'C' and 'POSIX' are not supported as locales, fall back to 'en_US'
        if locale == 'C' or locale == 'POSIX':
            locale = 'en_US'
        if '@' in locale:
            (locale, self['VARIANT']) = locale.split('@')
        if '.' in locale:
            locale = locale.split('.')[0]
        if '_' in locale:
            (self['LCODE'], self['CCODE']) = locale.split('_')
        else:
            self['LCODE'] = locale
        if len(self['VARIANT']) > 0:
            self['LOCALE'] = "%s@%s" % (locale, self['VARIANT'])
        else:
            self['LOCALE'] = locale
        # generate a SYSLOCALE from given components
        if len(self['LCODE']) > 0:
            if len(self['CCODE']) > 0:
                self['SYSLOCALE'] = "%s_%s.UTF-8" % (self["LCODE"], self["CCODE"])
            else:
                self['SYSLOCALE'] = "%s.UTF-8" % self['LCODE']
            if len(self['VARIANT']) > 0:
                self['SYSLOCALE'] = "%s@%s" % (self['SYSLOCALE'], self['VARIANT'])

        # package code
        try:
            self['PKGCODE'] = _file_map(self.LOCALE_TO_LANGPACK, self['LOCALE'], ':')
        except KeyError:
            self['PKGCODE'] = self['LCODE']

    def __getitem__(self, item):
        # return empty string as default
        return self.macros.get(item, '')

    def __setitem__(self, item, value):
        self.macros[item] = value

    def __contains__(self, item):
        return self.macros.__contains__(item)

    def subst_string(self, s):
        '''Substitute all macros in given string.'''

        re_macro = re.compile('%([A-Z]+)%')
        while 1:
            m = re_macro.search(s)
            if m:
                s = s[:m.start(1)-1] + self[m.group(1)] + s[m.end(1)+1:]
            else:
                break

        return s

    def subst_file(self, file):
        '''Substitute all macros in given file.'''

        s = open(file).read()
        open(file, 'w').write(self.subst_string(s))

    def subst_tree(self, root):
        '''Substitute all macros in given directory tree.'''

        for path, dirs, files in os.walk(root):
            for f in files:
                self.subst_file(os.path.join(root, path, f))

if __name__ == '__main__':
    datadir = '/usr/share/language-selector'
    for locale in ['de', 'de_DE', 'de_DE.UTF-8', 'de_DE.UTF-8@euro', 'fr_BE@latin', 'zh_CN.UTF-8', 'zh_TW.UTF-8', 'zh_HK.UTF-8', 'invalid_Locale']:
        l = LangpackMacros(datadir, locale)
        print('-------', locale, '---------------')
        template = '"%PKGCODE%: %LCODE% %CCODE% %VARIANT% %LOCALE% %SYSLOCALE%"'
        print('string:', l.subst_string(template))

        open('testtest', 'w').write(template)
        l.subst_file('testtest')
        print('file  :', open('testtest').read())
        os.unlink('testtest')

