#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim:et sts=4 sw=4
#
# ibus-table - The Tables engine for IBus
#
# Copyright (c) 2008-2009 Yu Yuwei <acevery@gmail.com>
# Copyright (c) 2009-2014 Caius "kaio" CHANCE <me@kaio.net>
# Copyright (c) 2012-2015 Mike FABIAN <mfabian@redhat.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

import os
import sys
sys.path.append( os.path.dirname(os.path.abspath(__file__)) )
import tabsqlitedb
import bz2
import re

from optparse import OptionParser

_invalid_keyname_chars = " \t\r\n\"$&<>,+=#!()'|{}[]?~`;%\\"
def gconf_valid_keyname(kn):
    """
    Keynames must be ascii, and must not contain any invalid characters

    >>> gconf_valid_keyname('nyannyan')
    True

    >>> gconf_valid_keyname('nyan nyan')
    False

    >>> gconf_valid_keyname('nyannyan[')
    False

    >>> gconf_valid_keyname('nyan\tnyan')
    False
    """
    return not any(c in _invalid_keyname_chars or ord(c) > 127 for c in kn)

class InvalidTableName(Exception):
    """
    Raised when an invalid table name is given
    """
    def __init__(self, name):
        self.table_name = name

    def __str__(self):
        return ('Value of NAME attribute (%s) ' % self.table_name
                + 'cannot contain any of %r ' % _invalid_keyname_chars
                + 'and must be all ascii')

# we use OptionParser to parse the cmd arguments :)
usage = "usage: %prog [options]"
opt_parser = OptionParser(usage=usage)

opt_parser.add_option(
    '-n', '--name',
    action = 'store',
    dest='name',
    default = '',
    help = (
        'specifies the file name for the binary database for the IME. '
        + 'The default is "%default". If the file name of the database '
        + 'is not specified, the file name of the source file before '
        + 'the first "." will be appended with ".db" and that will be '
        + 'used as the file name of the database.'))

opt_parser.add_option(
    '-s', '--source',
    action = 'store',
    dest='source',
    default = '',
    help = (
        'specifies the file which contains the source of the IME. '
        + 'The default is "%default".'))

opt_parser.add_option(
    '-e', '--extra',
    action = 'store',
    dest='extra',
    default = '',
    help = (
        'specifies the file name for the extra words for the IME. '
        + 'The default is "%default".'))

opt_parser.add_option(
    '-p', '--pinyin',
    action = 'store',
    dest='pinyin',
    default = '/usr/share/ibus-table/data/pinyin_table.txt.bz2',
    help = (
        'specifies the source file for the  pinyin. '
        + 'The default is "%default".'))

opt_parser.add_option(
    '-o', '--no-create-index',
    action = 'store_false',
    dest='index',
    default = True,
    help = (
        'Do not create an index for a database '
        + '(Only for distrubution purposes, '
        + 'a normal user should not use this flag!)'))

opt_parser.add_option(
    '-i', '--create-index-only',
    action = 'store_true',
    dest='only_index',
    default = False,
    help = (
        'Only create an index for an existing database. '
        + 'Specifying the file name of the binary database '
        + 'with the -n or --name option is required '
        + 'when this option is used.'))

opt_parser.add_option(
    '-d', '--debug',
    action = 'store_true',
    dest='debug',
    default = False,
    help = 'Print extra debug messages.')

opts, args = opt_parser.parse_args()
if opts.only_index:
    if not opts.name:
        opt_parser.print_help()
        print(
            '\nPlease specify the file name of the database '
            + 'you want to create an index on!')
        sys.exit(2)
    if not os.path.exists(opts.name) or not os.path.isfile(opts.name):
        opt_parser.print_help()
        print("\nThe database file '%s' does not exist." %opts.name)
        sys.exit(2)

if not opts.name and opts.source:
    opts.name = os.path.basename(opts.source).split('.')[0] + '.db'

if not opts.name:
    opt_parser.print_help()
    print(
        '\nYou need to specify the file which '
        + 'contains the source of the IME!')
    sys.exit(2)

def main ():
    def debug_print ( message ):
        if opts.debug:
            print(message)

    if not opts.only_index:
        try:
            os.unlink (opts.name)
        except:
            pass

    debug_print ("Processing Database")
    db = tabsqlitedb.tabsqlitedb(filename = opts.name,
                                 user_db = None,
                                 create_database = True)

    def parse_source (f):
        _attri = []
        _table = []
        _gouci = []
        patt_com = re.compile(r'^###.*')
        patt_blank = re.compile(r'^[ \t]*$')
        patt_conf = re.compile(r'[^\t]*=[^\t]*')
        patt_table = re.compile(r'([^\t]+)\t([^\t]+)\t([0-9]+)(\t.*)?$')
        patt_gouci = re.compile(r' *[^\s]+ *\t *[^\s]+ *$')

        for l in f:
            if (not patt_com.match(l)) and (not patt_blank.match(l)):
                for _patt, _list in (
                        (patt_table, _table),
                        (patt_gouci, _gouci),
                        (patt_conf, _attri)):
                    if _patt.match(l):
                        _list.append(l)
                        break

        if not _gouci:
            # The user didn’t provide goucima (goucima = 構詞碼 =
            # “word formation keys”) in the table source, so we use
            # the longest encoding for a single character as the
            # goucima for that character.
            #
            # Example:
            #
            # wubi-jidian86.txt contains:
            #
            #     a         工      99454797
            #     aaa	工      551000000
            #     aaaa      工      551000000
            #     aaad      工期    5350000
            #     ... and more matches for compounds containing 工
            #
            # The longest key sequence to type 工 as a single
            # character is “aaaa”.  Therefore, the goucima of 工 is
            # “aaaa” (There is one other character with the same goucima
            # in  wubi-jidian86.txt, 㠭 also has the goucima “aaaa”).
            gouci_dict = {}
            for line in _table:
                res = patt_table.match(line)
                if res and len(res.group(2)) == 1:
                    if res.group(2) in gouci_dict:
                        if len(res.group(1)) > len(gouci_dict[res.group(2)]):
                            gouci_dict[res.group(2)] = res.group(1)
                    else:
                        gouci_dict[res.group(2)] = res.group(1)
            for key in gouci_dict:
                _gouci.append('%s\t%s' %(key, gouci_dict[key]))
            _gouci.sort()

        return (_attri, _table, _gouci)

    def parse_pinyin (f):
        _pinyins = []
        patt_com = re.compile(r'^#.*')
        patt_blank = re.compile(r'^[ \t]*$')
        patt_py = re.compile(r'(.*)\t(.*)\t(.*)')
        patt_yin = re.compile(r'[a-z]+[1-5]')

        for l in f:
            if type(l) != type(u''):
                l = l.decode('utf-8')
            if ( not patt_com.match(l) ) and ( not patt_blank.match(l) ):
                res = patt_py.match(l)
                if res:
                    yins = patt_yin.findall(res.group(2))
                    for yin in yins:
                        _pinyins.append("%s\t%s\t%s" \
                                % (res.group(1), yin, res.group(3)))
        return _pinyins[:]

    def parse_extra (f):
        _extra = []
        patt_com = re.compile(r'^###.*')
        patt_blank = re.compile(r'^[ \t]*$')
        patt_extra = re.compile(r'(.*)\t(.*)')

        for l in f:
            if ( not patt_com.match(l) ) and ( not patt_blank.match(l) ):
                if patt_extra.match(l):
                    _extra.append(l)

        return _extra

    def pinyin_parser (f):
        for py in f:
            if type(py) != type(u''):
                py = py.decode('utf-8')
            _zi, _pinyin, _freq = py.strip().split()
            yield (_pinyin, _zi, _freq)

    def phrase_parser (f):
        phrase_list = []
        for l in f:
            if type(l) != type(u''):
                l = l.decode('utf-8')
            xingma, phrase, freq = l.split('\t')[:3]
            if phrase == 'NOSYMBOL':
                phrase = u''
            phrase_list.append((xingma, phrase, int(freq), 0))
        return phrase_list

    def goucima_parser (f):
        for l in f:
            if type(l) != type(u''):
                l = l.decode('utf-8')
            zi, gcm = l.strip().split()
            yield (zi, gcm)

    def attribute_parser (f):
        for l in f:
            if type(l) != type(u''):
                l = l.decode('utf-8')
            try:
                attr, val = l.strip().split('=')
            except:
                attr, val = l.strip().split('==')
            attr = attr.strip().lower()
            val = val.strip()
            yield (attr, val)

    def extra_parser (f):
        extra_list = []
        for l in f:
            if type(l) != type(u''):
                l = l.decode('utf-8')
            phrase, freq = l.strip().split ()
            _tabkey = db.parse_phrase(phrase)
            if _tabkey:
                extra_list.append((_tabkey, phrase, freq, 0))
            else:
                print('No tabkeys found for “%s”, not adding.\n' %phrase)
        return extra_list

    def get_char_prompts(f):
        '''
        Returns something like

        ("char_prompts", "{'a': '日', 'b': '日', 'c': '金', ...}")

        i.e. the attribute name "char_prompts" and as its value
        the string representation of a Python dictionary.
        '''
        char_prompts = {}
        start = False
        for l in f:
            if type(l) != type(u''):
                l = l.decode('utf-8')
            if re.match(r'^BEGIN_CHAR_PROMPTS_DEFINITION', l):
                start = True
                continue
            if not start:
                continue
            if re.match(r'^END_CHAR_PROMPTS_DEFINITION', l):
                break
            match = re.search(r'^(?P<char>[^\s]+)[\s]+(?P<prompt>[^\s]+)', l)
            if match:
                char_prompts[match.group('char')] = match.group('prompt')
        return ("char_prompts", repr(char_prompts))

    if opts.only_index:
        debug_print ('Only create Indexes')
        debug_print ( "Optimizing database " )
        db.optimize_database ()

        debug_print ('Create Indexes ')
        db.create_indexes ('main')
        debug_print ('Done! :D')
        return 0

    # now we parse the ime source file
    debug_print ("\tLoad sources \"%s\"" % opts.source)
    patt_s = re.compile( r'.*\.bz2' )
    _bz2s = patt_s.match(opts.source)
    if _bz2s:
        source = bz2.BZ2File(opts.source, "r").read()
    else:
        source = open(opts.source, mode='r', encoding='UTF-8').read()
    source = source.replace('\r\n', '\n')
    source = source.split('\n')
    # first get config line and table line and goucima line respectively
    debug_print ('\tParsing table source file ')
    attri, table, gouci =  parse_source(source)

    debug_print('\t  get attribute of IME :)')
    attributes = list(attribute_parser(attri))
    attributes.append(get_char_prompts(source))
    debug_print('\t  add attributes into DB ')
    db.update_ime( attributes )
    db.create_tables('main')

    # second, we use generators for database generating:
    debug_print ('\t  get phrases of IME :)')
    phrases = phrase_parser ( table)

    # now we add things into db
    debug_print('\t  add phrases into DB ')
    db.add_phrases(phrases)

    if db.ime_properties.get('user_can_define_phrase').lower() == u'true':
        debug_print ('\t  get goucima of IME :)')
        goucima = goucima_parser (gouci)
        debug_print ('\t  add goucima into DB ')
        db.add_goucima ( goucima )

    if db.ime_properties.get('pinyin_mode').lower() == u'true':
        debug_print ('\tLoad pinyin source \"%s\"' % opts.pinyin)
        _bz2p = patt_s.match(opts.pinyin)
        if _bz2p:
            pinyin_s = bz2.BZ2File ( opts.pinyin, "r" )
        else:
            pinyin_s = file ( opts.pinyin, 'r' )
        debug_print ('\tParsing pinyin source file ')
        pyline = parse_pinyin (pinyin_s)
        debug_print ('\tPreapring pinyin entries')
        pinyin = pinyin_parser (pyline)
        debug_print ('\t  add pinyin into DB ')
        db.add_pinyin ( pinyin )

    debug_print ("Optimizing database ")
    db.optimize_database ()

    if (db.ime_properties.get('user_can_define_phrase').lower() == u'true'
        and opts.extra):
        debug_print( '\tPreparing for adding extra words' )
        db.create_indexes ('main')
        debug_print ('\tLoad extra words source \"%s\"' % opts.extra)
        _bz2p = patt_s.match(opts.extra)
        if _bz2p:
            extra_s = bz2.BZ2File ( opts.extra, "r" )
        else:
            extra_s = file ( opts.extra, 'r' )
        debug_print ('\tParsing extra words source file ')
        extraline = parse_extra (extra_s)
        debug_print ('\tPreparing extra words lines')
        extrawds = extra_parser (extraline)
        debug_print( '\t  we have %d extra phrases from source' % len(extrawds))
        # first get the entry of original phrases from
        # phrases-[(xingma, phrase, int(freq), 0)]
        orig_phrases = {}
        for x in phrases:
            orig_phrases.update({"%s\t%s" % (x[0], x[1]):x})
        debug_print('\t  the len of orig_phrases is: %d' % len(orig_phrases))
        extra_phrases = {}
        for x in extrawds:
            extra_phrases.update({"%s\t%s" % (x[0], x[1]):x})
        debug_print('\t  the len of extra_phrases is: %d' % len(extra_phrases))
        # pop duplicated keys
        for x in extra_phrases:
            if x in orig_phrases:
                extra_phrases.pop(x)
        debug_print('\t  %d extra phrases will be added' % len(extra_phrases))
        new_phrases = list(extra_phrases.values())
        debug_print('\tAdding extra words into DB ')
        db.add_phrases (new_phrases)
        debug_print('Optimizing database ')
        db.optimize_database ()

    if opts.index:
        debug_print ('Create Indexes ')
        db.create_indexes ('main')
    else:
        debug_print(
            "We don't create an index on the database, "
            + "you should only activate this function "
            + "for distribution purposes.")
        db.drop_indexes ('main')
    debug_print ('Done! :D')

if __name__ == "__main__":
    main ()
