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

import sys
if sys.version_info < (3, 0, 0):
    reload (sys)
    sys.setdefaultencoding('utf-8')
import os
import os.path as path
import shutil
import sqlite3
import uuid
import time
import re
import chinese_variants

debug_level = int(0)

database_version = '1.00'

patt_r = re.compile(r'c([ea])(\d):(.*)')
patt_p = re.compile(r'p(-{0,1}\d)(-{0,1}\d)')

chinese_nocheck_chars = u"“”‘’《》〈〉〔〕「」『』【】〖〗（）［］｛｝"\
    u"．。，、；：？！…—·ˉˇ¨々～‖∶＂＇｀｜"\
    u"⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛"\
    u"АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯЁ"\
    u"ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"\
    u"⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛"\
    u"㎎㎏㎜㎝㎞㎡㏄㏎㏑㏒㏕"\
    u"ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"\
    u"⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇"\
    u"€＄￠￡￥"\
    u"¤→↑←↓↖↗↘↙"\
    u"ァアィイゥウェエォオカガキギクグケゲコゴサザシジ"\
    u"スズセゼソゾタダチヂッツヅテデトドナニヌネノハバパ"\
    u"ヒビピフブプヘベペホボポマミムメモャヤュユョヨラ"\
    u"リルレロヮワヰヱヲンヴヵヶーヽヾ"\
    u"ぁあぃいぅうぇえぉおかがきぎぱくぐけげこごさざしじ"\
    u"すずせぜそぞただちぢっつづてでとどなにぬねのはば"\
    u"ひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらり"\
    u"るれろゎわゐゑをん゛゜ゝゞ"\
    u"勹灬冫艹屮辶刂匚阝廾丨虍彐卩钅冂冖宀疒肀丿攵凵犭"\
    u"亻彡饣礻扌氵纟亠囗忄讠衤廴尢夂丶"\
    u"āáǎàōóǒòêēéěèīíǐìǖǘǚǜüūúǔù"\
    u"＋－＜＝＞±×÷∈∏∑∕√∝∞∟∠∣∥∧∨∩∪∫∮"\
    u"∴∵∶∷∽≈≌≒≠≡≤≥≦≧≮≯⊕⊙⊥⊿℃°‰"\
    u"♂♀§№☆★○●◎◇◆□■△▲※〓＃＆＠＼＾＿￣"\
    u"абвгдежзийклмнопрстуфхцчшщъыьэюяё"\
    u"ⅰⅱⅲⅳⅴⅵⅶⅷⅸⅹβγδεζηαικλμνξοπρστυφθψω"\
    u"①②③④⑤⑥⑦⑧⑨⑩①②③④⑤⑥⑦⑧⑨⑩"\
    u"㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩㈠㈡㈢㈣㈤㈥㈦㈧㈨㈩"\
    u"ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙㄧㄨㄩ"\
    u"ㄚㄛㄜㄝㄞㄟㄠㄡㄢㄣㄤㄥㄦ"

class ImeProperties:
    def __init__(self, db=None, default_properties={}):
        '''
        “db” is the handle of the sqlite3 database file obtained by
        sqlite3.connect().
        '''
        if not db:
            return None
        self.ime_property_cache = default_properties
        sqlstr = 'SELECT attr, val FROM main.ime;'
        try:
            results = db.execute(sqlstr).fetchall()
        except:
            import traceback
            traceback.print_exc()
        for result in results:
            self.ime_property_cache[result[0]] = result[1]

    def get(self, key):
        if key in self.ime_property_cache:
            return self.ime_property_cache[key]
        else:
            return None

class tabsqlitedb:
    '''Phrase database for tables

    The phrases table in the database has columns with the names:

    “id”, “tabkeys”, “phrase”, “freq”, “user_freq”

    There are 2 databases, sysdb, userdb.

    sysdb: System database for the input method, for example something
           like /usr/share/ibus-table/tables/wubi-jidian86.db
           “user_freq” is always 0 in a system database.  “freq”
           is some number in a system database indicating a frequency
           of use of that phrase relative to the other phrases in that
           database.

    user_db: Database on disk where the phrases used or defined by the
           user are stored. “user_freq” is a counter which counts how
           many times that combination of “tabkeys” and “phrase” has
           been used. “freq” is equal to 0 for all combinations of
           “tabkeys” and “phrase” where an entry for that phrase is
           already in the system database which starts with the same
           “tabkeys”.
           For combinations of “tabkeys” and “phrase” which do not exist
           at all in the system database, “freq” is equal to -1 to
           indidated that this is a user defined phrase.
    '''
    def __init__(
            self, filename = None, user_db = None, create_database = False):
        global debug_level
        try:
            debug_level = int(os.getenv('IBUS_TABLE_DEBUG_LEVEL'))
        except (TypeError, ValueError):
            debug_level = int(0)
        self.old_phrases = []
        self.filename = filename
        self._user_db = user_db

        if create_database or os.path.isfile(self.filename):
            self.db = sqlite3.connect(self.filename)
        else:
            print('Cannot open database file %s' %self.filename)
        try:
            self.db.execute('PRAGMA encoding = "UTF-8";')
            self.db.execute('PRAGMA case_sensitive_like = true;')
            self.db.execute('PRAGMA page_size = 4096;')
            # 20000 pages should be enough to cache the whole database
            self.db.execute('PRAGMA cache_size = 20000;')
            self.db.execute('PRAGMA temp_store = MEMORY;')
            self.db.execute('PRAGMA journal_size_limit = 1000000;')
            self.db.execute('PRAGMA synchronous = NORMAL;')
        except:
            import traceback
            traceback.print_exc()
            print('Error while initializing database.')
        # create IME property table
        self.db.executescript(
            'CREATE TABLE IF NOT EXISTS main.ime (attr TEXT, val TEXT);')
        # Initalize missing attributes in the ime table with some
        # default values, they should be updated using the attributes
        # found in the source when creating a system database with
        # tabcreatedb.py
        self._default_ime_attributes = {
            'name':'',
            'name.zh_cn':'',
            'name.zh_hk':'',
            'name.zh_tw':'',
            'author':'somebody',
            'uuid':'%s' % uuid.uuid4(),
            'serial_number':'%s' % time.strftime('%Y%m%d'),
            'icon':'ibus-table.svg',
            'license':'LGPL',
            'languages':'',
            'language_filter':'',
            'valid_input_chars':'abcdefghijklmnopqrstuvwxyz',
            'max_key_length':'4',
            'commit_keys':'space',
            # 'forward_keys':'Return',
            'select_keys':'1,2,3,4,5,6,7,8,9,0',
            'page_up_keys':'Page_Up,minus',
            'page_down_keys':'Page_Down,equal',
            'status_prompt':'',
            'def_full_width_punct':'true',
            'def_full_width_letter':'false',
            'user_can_define_phrase':'false',
            'pinyin_mode':'false',
            'dynamic_adjust':'false',
            'auto_select':'false',
            'auto_commit':'false',
            # 'no_check_chars':u'',
            'description':'A IME under IBus Table',
            'layout':'us',
            'symbol':'',
            'rules':'',
            'least_commit_length':'0',
            'start_chars':'',
            'orientation':'true',
            'always_show_lookup':'true',
            'char_prompts':'{}'
            # we use this entry for those IME, which don't
            # have rules to build up phrase, but still need
            # auto commit to preedit
        }
        if create_database:
            select_sqlstr = '''
            SELECT val FROM main.ime WHERE attr = :attr;'''
            insert_sqlstr = '''
            INSERT INTO main.ime (attr, val) VALUES (:attr, :val);'''
            for attr in sorted(self._default_ime_attributes):
                sqlargs = {
                    'attr': attr,
                    'val': self._default_ime_attributes[attr]
                }
                if not self.db.execute(select_sqlstr, sqlargs).fetchall():
                    self.db.execute(insert_sqlstr, sqlargs)
        self.ime_properties = ImeProperties(
            db=self.db,
            default_properties=self._default_ime_attributes)
        # shared variables in this class:
        self._mlen = int(self.ime_properties.get("max_key_length"))
        self._is_chinese = self.is_chinese()
        self._is_cjk = self.is_cjk()
        self.user_can_define_phrase = self.ime_properties.get(
            'user_can_define_phrase')
        if self.user_can_define_phrase:
            if self.user_can_define_phrase.lower() == u'true' :
                self.user_can_define_phrase = True
            else:
                self.user_can_define_phrase = False
        else:
            print(
                'Could not find "user_can_define_phrase" entry from database, '
                + 'is it an outdated database?')
            self.user_can_define_phrase = False

        self.dynamic_adjust = self.ime_properties.get('dynamic_adjust')
        if self.dynamic_adjust:
            if self.dynamic_adjust.lower() == u'true' :
                self.dynamic_adjust = True
            else:
                self.dynamic_adjust = False
        else:
            print(
                'Could not find "dynamic_adjust" entry from database, '
                + 'is it an outdated database?')
            self.dynamic_adjust = False

        self.rules = self.get_rules ()
        self.possible_tabkeys_lengths = self.get_possible_tabkeys_lengths()
        self.startchars = self.get_start_chars ()

        if not user_db or create_database:
            # No user database requested or we are
            # just creating the system database and
            # we do not need a user database for that
            return

        if user_db != ":memory:":
            import ibus_table_location
            tables_path = path.join(ibus_table_location.data_home(),  "tables")
            if not path.isdir(tables_path):
                old_tables_path = os.path.join(
                    os.getenv('HOME'), '.ibus/tables')
                if path.isdir(old_tables_path):
                    if os.access(os.path.join(
                            old_tables_path, 'debug.log'), os.F_OK):
                        os.unlink(os.path.join(old_tables_path, 'debug.log'))
                    if os.access(os.path.join(
                            old_tables_path, 'setup-debug.log'), os.F_OK):
                        os.unlink(os.path.join(
                            old_tables_path, 'setup-debug.log'))
                    shutil.copytree(old_tables_path, tables_path)
                    shutil.rmtree(old_tables_path)
                    os.symlink(tables_path, old_tables_path)
                else:
                    os.makedirs(tables_path)
            user_db = path.join(tables_path, user_db)
            if not path.exists(user_db):
                sys.stderr.write(
                    'The user database %(udb)s does not exist yet.\n'
                    % {'udb': user_db})
            else:
                try:
                    desc = self.get_database_desc(user_db)
                    phrase_table_column_names = [
                        'id', 'tabkeys', 'phrase','freq','user_freq']
                    if (desc == None
                        or desc["version"] != database_version
                        or (self.get_number_of_columns_of_phrase_table(user_db)
                            != len(phrase_table_column_names))):
                        sys.stderr.write(
                            'The user database %s seems to be incompatible.\n'
                            % user_db)
                        if desc == None:
                            sys.stderr.write(
                                'There is no version information in '
                                + 'the database.\n')
                            self.old_phrases = self.extract_user_phrases(
                                user_db, old_database_version = '0.0')
                        elif desc["version"] != database_version:
                            sys.stderr.write(
                                'The version of the database does not match '
                                + '(too old or too new?).\n'
                                'ibus-table wants version=%s\n'
                                % database_version
                                + 'But the  database actually has version=%s\n'
                                % desc['version'])
                            self.old_phrases = self.extract_user_phrases(
                                user_db, old_database_version = desc['version'])
                        elif (self.get_number_of_columns_of_phrase_table(
                                user_db)
                              != len(phrase_table_column_names)):
                            sys.stderr.write(
                                'The number of columns of the database '
                                + 'does not match.\n'
                                + 'ibus-table expects %s columns.\n'
                                % len(phrase_table_column_names)
                                + 'But the database actually has %s columns.\n'
                                % self.get_number_of_columns_of_phrase_table(
                                    user_db)
                                + 'But the versions of the databases are '
                                + 'identical.\n'
                                + 'This should never happen!\n')
                            self.old_phrases = None
                        from time import strftime
                        timestamp = strftime('-%Y-%m-%d_%H:%M:%S')
                        sys.stderr.write(
                            'Renaming the incompatible database to "%s".\n'
                            % user_db+timestamp)
                        if os.path.exists(user_db):
                            os.rename(user_db, user_db+timestamp)
                        if os.path.exists(user_db+'-shm'):
                            os.rename(user_db+'-shm', user_db+'-shm'+timestamp)
                        if os.path.exists(user_db+'-wal'):
                            os.rename(user_db+'-wal', user_db+'-wal'+timestamp)
                        sys.stderr.write(
                            'Creating a new, empty database "s".\n'
                            % user_db)
                        self.init_user_db(user_db)
                        sys.stderr.write(
                            'If user phrases were successfully recovered from '
                            + 'the old,\n'
                            + 'incompatible database, they will be used to '
                            + 'initialize the new database.\n')
                    else:
                        sys.stderr.write(
                            'Compatible database %s found.\n' % user_db)
                except:
                    import traceback
                    traceback.print_exc()

        # open user phrase database
        try:
            sys.stderr.write(
                'Connect to the database %(name)s.\n' %{'name': user_db})
            self.db.execute('ATTACH DATABASE "%s" AS user_db;' % user_db)
            self.db.execute('PRAGMA user_db.encoding = "UTF-8";')
            self.db.execute('PRAGMA user_db.case_sensitive_like = true;')
            self.db.execute('PRAGMA user_db.page_size = 4096; ')
            self.db.execute('PRAGMA user_db.cache_size = 20000;')
            self.db.execute('PRAGMA user_db.temp_store = MEMORY;')
            self.db.execute('PRAGMA user_db.journal_mode = WAL;')
            self.db.execute('PRAGMA user_db.journal_size_limit = 1000000;')
            self.db.execute('PRAGMA user_db.synchronous = NORMAL;')
        except:
            sys.stderr.write('Could not open the database %s.\n' % user_db)
            from time import strftime
            timestamp = strftime('-%Y-%m-%d_%H:%M:%S')
            sys.stderr.write('Renaming the incompatible database to "%s".\n'
                             % user_db+timestamp)
            if os.path.exists(user_db):
                os.rename(user_db, user_db+timestamp)
            if os.path.exists(user_db+'-shm'):
                os.rename(user_db+'-shm', user_db+'-shm'+timestamp)
            if os.path.exists(user_db+'-wal'):
                os.rename(user_db+'-wal', user_db+'-wal'+timestamp)
            sys.stderr.write('Creating a new, empty database "%s".\n'
                             % user_db)
            self.init_user_db(user_db)
            self.db.execute('ATTACH DATABASE "%s" AS user_db;' % user_db)
            self.db.execute('PRAGMA user_db.encoding = "UTF-8";')
            self.db.execute('PRAGMA user_db.case_sensitive_like = true;')
            self.db.execute('PRAGMA user_db.page_size = 4096; ')
            self.db.execute('PRAGMA user_db.cache_size = 20000;')
            self.db.execute('PRAGMA user_db.temp_store = MEMORY;')
            self.db.execute('PRAGMA user_db.journal_mode = WAL;')
            self.db.execute('PRAGMA user_db.journal_size_limit = 1000000;')
            self.db.execute('PRAGMA user_db.synchronous = NORMAL;')
        self.create_tables("user_db")
        if self.old_phrases:
            sqlargs = []
            for x in self.old_phrases:
                sqlargs.append(
                    {'tabkeys': x[0],
                     'phrase': x[1],
                     'freq': x[2],
                     'user_freq': x[3]})
            sqlstr = '''
            INSERT INTO user_db.phrases (tabkeys, phrase, freq, user_freq)
            VALUES (:tabkeys, :phrase, :freq, :user_freq)
            '''
            try:
                self.db.executemany(sqlstr, sqlargs)
            except:
                import traceback
                traceback.print_exec()
            self.db.commit ()
            self.db.execute('PRAGMA wal_checkpoint;')

        # try create all tables in user database
        self.create_indexes ("user_db", commit=False)
        self.generate_userdb_desc ()

    def update_phrase(
            self, tabkeys=u'', phrase=u'',
            user_freq=0, database='user_db', commit=True):
        '''update phrase freqs'''
        if debug_level > 1:
            sys.stderr.write(
                'update_phrase() tabkeys=%(t)s phrase=%(p)s '
                % {'t': tabkeys, 'p': phrase}
                + 'user_freq=%(u)s database=%(d)s\n'
                % {'u': user_freq, 'd': database})
        if not tabkeys or not phrase:
            return
        sqlstr = '''
        UPDATE %s.phrases SET user_freq = :user_freq
        WHERE tabkeys = :tabkeys AND phrase = :phrase
        ;''' % database
        sqlargs = {'user_freq': user_freq, 'tabkeys': tabkeys, 'phrase': phrase}
        try:
            self.db.execute(sqlstr, sqlargs)
            if commit:
                self.db.commit()
        except:
            import traceback
            traceback.print_exc()

    def sync_usrdb (self):
        '''
        Trigger a checkpoint operation.
        '''
        if self._user_db is None:
            return
        self.db.commit()
        self.db.execute('PRAGMA wal_checkpoint;')

    def is_chinese (self):
        __lang = self.ime_properties.get('languages')
        if __lang:
            __langs = __lang.split(',')
            for _l in __langs:
                if _l.lower().find('zh') != -1:
                    return True
        return False

    def is_cjk(self):
        languages = self.ime_properties.get('languages')
        if languages:
            languages = languages.split(',')
            for language in languages:
                for lang in ['zh', 'ja', 'ko']:
                    if language.strip().startswith(lang):
                        return True
        return False

    def get_chinese_mode (self):
        try:
            __dict = {'cm0':0, 'cm1':1, 'cm2':2, 'cm3':3, 'cm4':4}
            __filt = self.ime_properties.get('language_filter')
            return __dict[__filt]
        except:
            return -1

    def get_select_keys (self):
        ret = self.ime_properties.get("select_keys")
        if ret:
            return ret
        return "1,2,3,4,5,6,7,8,9,0"

    def get_orientation (self):
        try:
            return int(self.ime_properties.get('orientation'))
        except:
            return 1

    def create_tables (self, database):
        '''Create tables that contain all phrase'''
        if database == 'main':
            sqlstr = '''
            CREATE TABLE IF NOT EXISTS %s.goucima
            (zi TEXT PRIMARY KEY, goucima TEXT);
            ''' % database
            self.db.execute (sqlstr)
            sqlstr = '''
            CREATE TABLE IF NOT EXISTS %s.pinyin
            (pinyin TEXT, zi TEXT, freq INTEGER);
            ''' % database
            self.db.execute(sqlstr)

        sqlstr = '''
        CREATE TABLE IF NOT EXISTS %s.phrases
        (id INTEGER PRIMARY KEY, tabkeys TEXT, phrase TEXT,
        freq INTEGER, user_freq INTEGER);
        ''' % database
        self.db.execute (sqlstr)
        self.db.commit()

    def update_ime (self, attrs):
        '''Update or insert attributes in ime table, attrs is a iterable object
        Like [(attr,val), (attr,val), ...]

        This is called only by tabcreatedb.py.
        '''
        select_sqlstr = 'SELECT val from main.ime WHERE attr = :attr'
        update_sqlstr = 'UPDATE main.ime SET val = :val WHERE attr = :attr;'
        insert_sqlstr = 'INSERT INTO main.ime (attr, val) VALUES (:attr, :val);'
        for attr, val in attrs:
            sqlargs = {'attr': attr, 'val': val}
            if self.db.execute(select_sqlstr, sqlargs).fetchall():
                self.db.execute(update_sqlstr, sqlargs)
            else:
                self.db.execute(insert_sqlstr, sqlargs)
        self.db.commit()
        # update ime properties cache:
        self.ime_properties = ImeProperties(
            db=self.db,
            default_properties=self._default_ime_attributes)
        # The self variables used by tabcreatedb.py need to be updated now:
        self._mlen = int(self.ime_properties.get('max_key_length'))
        self._is_chinese = self.is_chinese()
        self.user_can_define_phrase = self.ime_properties.get(
            'user_can_define_phrase')
        if self.user_can_define_phrase:
            if self.user_can_define_phrase.lower() == u'true' :
                self.user_can_define_phrase = True
            else:
                self.user_can_define_phrase = False
        else:
            print(
                'Could not find "user_can_define_phrase" entry from database, '
                + 'is it a outdated database?')
            self.user_can_define_phrase = False
        self.rules = self.get_rules()

    def get_rules (self):
        '''Get phrase construct rules'''
        rules = {}
        if self.user_can_define_phrase:
            try:
                _rules = self.ime_properties.get('rules')
                if _rules:
                    _rules = _rules.strip().split(';')
                for rule in _rules:
                    res = patt_r.match (rule)
                    if res:
                        cms = []
                        if res.group(1) == 'a':
                            rules['above'] = int(res.group(2))
                        _cms = res.group(3).split('+')
                        if len(_cms) > self._mlen:
                            print('rule: "%s" over max key length' %rule)
                            break
                        for _cm in _cms:
                            cm_res = patt_p.match(_cm)
                            cms.append((int(cm_res.group(1)),
                                        int(cm_res.group(2))))
                        rules[int(res.group(2))]=cms
                    else:
                        print('not a legal rule: "%s"' %rule)
            except Exception:
                import traceback
                traceback.print_exc ()
            return rules
        else:
            return ""

    def get_possible_tabkeys_lengths(self):
        '''Return a list of the possible lengths for tabkeys in this table.

        Example:

        If the table source has rules like:

            RULES = ce2:p11+p12+p21+p22;ce3:p11+p21+p22+p31;ca4:p11+p21+p31+p41

        self._rules will be set to

            self._rules={2: [(1, 1), (1, 2), (2, 1), (2, 2)], 3: [(1, 1), (1, 2), (2, 1), (3, 1)], 4: [(1, 1), (2, 1), (3, 1), (-1, 1)], 'above': 4}

        and then this function returns “[4, 4, 4]”

        Or, if the table source has no RULES but LEAST_COMMIT_LENGTH=2
        and MAX_KEY_LENGTH = 4, then it returns “[2, 3, 4]”

        I cannot find any tables which use LEAST_COMMIT_LENGTH though.
        '''
        if self.rules:
            max_len = self.rules["above"]
            return [len(self.rules[x]) for x in range(2, max_len+1)][:]
        else:
            try:
                least_commit_len = int(
                    self.ime_properties.get('least_commit_length'))
            except:
                least_commit_len = 0
            if least_commit_len > 0:
                return list(range(least_commit_len, self._mlen + 1))
            else:
                return []

    def get_start_chars (self):
        '''return possible start chars of IME'''
        return self.ime_properties.get('start_chars')

    def get_no_check_chars (self):
        '''Get the characters which engine should not change freq'''
        _chars = self.ime_properties.get('no_check_chars')
        if type(_chars) != type(u''):
            _chars = _chars.decode('utf-8')
        return _chars

    def add_phrases (self, phrases, database = 'main'):
        '''Add many phrases to database fast. Used by tabcreatedb.py when
        creating the system database from scratch.

        “phrases” is a iterable object which looks like:

            [(tabkeys, phrase, freq ,user_freq), (tabkeys, phrase, freq, user_freq), ...]

        This function does not check whether phrases are already
        there.  As this function is only used while creating the
        system database, it is not really necessary to check whether
        phrases are already there because the database is initially
        empty anyway. And the caller should take care that the
        “phrases” argument does not contain duplicates.

        '''
        if debug_level > 1:
            sys.stderr.write("add_phrases() len(phrases)=%s\n"
                             %len(phrases))
        insert_sqlstr = '''
        INSERT INTO %(database)s.phrases
        (tabkeys, phrase, freq, user_freq)
        VALUES (:tabkeys, :phrase, :freq, :user_freq);
        ''' % {'database': database}
        insert_sqlargs = []
        for (tabkeys, phrase, freq, user_freq) in phrases:
            insert_sqlargs.append({
                'tabkeys': tabkeys,
                'phrase': phrase,
                'freq': freq,
                'user_freq': user_freq})
        self.db.executemany(insert_sqlstr, insert_sqlargs)
        self.db.commit()
        self.db.execute('PRAGMA wal_checkpoint;')

    def add_phrase(
            self, tabkeys=u'', phrase=u'', freq=0, user_freq=0,
            database='main',commit=True):
        '''Add phrase to database, phrase is a object of
        (tabkeys, phrase, freq ,user_freq)
        '''
        if debug_level > 1:
            sys.stderr.write(
                'add_phrase tabkeys=%(t)s phrase=%(p)s '
                % {'t': tabkeys, 'p': phrase}
                + 'freq=%(f)s user_freq=%(u)s\n'
                % {'f': freq, 'u': user_freq})
        if not tabkeys or not phrase:
            return
        select_sqlstr = '''
        SELECT * FROM %(database)s.phrases
        WHERE tabkeys = :tabkeys AND phrase = :phrase;
        ''' % {'database': database}
        select_sqlargs = {'tabkeys': tabkeys, 'phrase': phrase}
        results = self.db.execute(select_sqlstr, select_sqlargs).fetchall()
        if results:
            # there is already such a phrase, i.e. add_phrase was called
            # in error, do nothing to avoid duplicate entries.
            if debug_level > 1:
                sys.stderr.write(
                    'add_phrase() '
                    + 'select_sqlstr=%(sql)s select_sqlargs=%(arg)s '
                    % {'sql': select_sqlstr, 'arg': select_sqlargs}
                    + 'already there!: results=%(r)s \n'
                    % {'r': results})
            return

        insert_sqlstr = '''
        INSERT INTO %(database)s.phrases
        (tabkeys, phrase, freq, user_freq)
        VALUES (:tabkeys, :phrase, :freq, :user_freq);
        ''' % {'database': database}
        insert_sqlargs = {
            'tabkeys': tabkeys,
            'phrase': phrase,
            'freq': freq,
            'user_freq': user_freq}
        if debug_level > 1:
            sys.stderr.write(
                'add_phrase() insert_sqlstr=%(sql)s insert_sqlargs=%(arg)s\n'
                % {'sql': insert_sqlstr, 'arg': insert_sqlargs})
        try:
            self.db.execute (insert_sqlstr, insert_sqlargs)
            if commit:
                self.db.commit()
        except:
            import traceback
            traceback.print_exc()

    def add_goucima (self, goucimas):
        '''Add goucima into database, goucimas is iterable object
        Like goucimas = [(zi,goucima), (zi,goucima), ...]
        '''
        sqlstr = '''
        INSERT INTO main.goucima (zi, goucima) VALUES (:zi, :goucima);
        '''
        sqlargs = []
        for zi, goucima in goucimas:
            sqlargs.append({'zi': zi, 'goucima': goucima})
        try:
            self.db.commit()
            self.db.executemany(sqlstr, sqlargs)
            self.db.commit()
            self.db.execute('PRAGMA wal_checkpoint;')
        except:
            import traceback
            traceback.print_exc()

    def add_pinyin (self, pinyins, database = 'main'):
        '''Add pinyin to database, pinyins is a iterable object
        Like: [(zi,pinyin, freq), (zi, pinyin, freq), ...]
        '''
        sqlstr = '''
        INSERT INTO %s.pinyin (pinyin, zi, freq) VALUES (:pinyin, :zi, :freq);
        ''' % database
        count = 0
        for pinyin, zi, freq in pinyins:
            count += 1
            pinyin = pinyin.replace(
                '1','!').replace(
                    '2','@').replace(
                        '3','#').replace(
                            '4','$').replace(
                                '5','%')
            try:
                self.db.execute(
                    sqlstr, {'pinyin': pinyin, 'zi': zi, 'freq': freq})
            except Exception:
                sys.stderr.write(
                    'Error when inserting into pinyin table. '
                    + 'count=%(c)s pinyin=%(p)s zi=%(z)s freq=%(f)s\n'
                    % {'c': count, 'p': pinyin, 'z': zi, 'f': freq})
                import traceback
                traceback.print_exc()
        self.db.commit()

    def optimize_database (self, database='main'):
        sqlstr = '''
            CREATE TABLE tmp AS SELECT * FROM %(database)s.phrases;
            DELETE FROM %(database)s.phrases;
            INSERT INTO %(database)s.phrases SELECT * FROM tmp ORDER BY
            tabkeys ASC, phrase ASC, user_freq DESC, freq DESC, id ASC;
            DROP TABLE tmp;
            CREATE TABLE tmp AS SELECT * FROM %(database)s.goucima;
            DELETE FROM %(database)s.goucima;
            INSERT INTO %(database)s.goucima SELECT * FROM tmp ORDER BY zi, goucima;
            DROP TABLE tmp;
            CREATE TABLE tmp AS SELECT * FROM %(database)s.pinyin;
            DELETE FROM %(database)s.pinyin;
            INSERT INTO %(database)s.pinyin SELECT * FROM tmp ORDER BY pinyin ASC, freq DESC;
            DROP TABLE tmp;
            ''' % {'database':database}
        self.db.executescript (sqlstr)
        self.db.executescript ("VACUUM;")
        self.db.commit()

    def drop_indexes(self, database):
        '''Drop the indexes in the database to reduce its size

        We do not use any indexes at the moment, therefore this
        function does nothing.
        '''
        if debug_level > 1:
            sys.stderr.write("drop_indexes()\n")
        return

    def create_indexes(self, database, commit=True):
        '''Create indexes for the database.

        We do not use any indexes at the moment, therefore
        this function does nothing. We used indexes before,
        but benchmarking showed that none of them was really
        speeding anything up, therefore we deleted all of them
        to get much smaller databases (about half the size).

        If some index turns out to be very useful in future, it could
        be created here (and dropped in “drop_indexes()”).
        '''
        if debug_level > 1:
            sys.stderr.write("create_indexes()\n")
        return

    def big5_code(self, phrase):
        try:
            big5 = phrase.encode('Big5')
        except:
            big5 = b'\xff\xff' # higher than any Big5 code
        return big5

    def best_candidates(
            self, typed_tabkeys=u'', candidates=[], chinese_mode=-1):
        '''
        “candidates” is an array containing something like:
        [(tabkeys, phrase, freq, user_freq), ...]

        “typed_tabkeys” is key sequence the user really typed, which
        maybe only the beginning part of the “tabkeys” in a matched
        candidate.
        '''
        maximum_number_of_candidates = 100
        engine_name = os.path.basename(self.filename).replace('.db', '')
        if engine_name in [
                'cangjie3', 'cangjie5', 'cangjie-big',
                'quick-classic', 'quick3', 'quick5']:
            code_point_function = self.big5_code
        else:
            code_point_function = lambda x: (1)
        if chinese_mode in (2, 3) and self._is_chinese:
            if chinese_mode == 2:
                bitmask = (1 << 0) # used in simplified Chinese
            else:
                bitmask = (1 << 1) # used in traditional Chinese
            return sorted(candidates,
                          key=lambda x: (
                              - int(
                                  typed_tabkeys == x[0]
                              ), # exact matches first!
                              -1*x[3],   # user_freq descending
                              # Prefer characters used in the
                              # desired Chinese variant:
                              -(bitmask
                                & chinese_variants.detect_chinese_category(
                                    x[1])),
                              -1*x[2],   # freq descending
                              len(x[0]), # len(tabkeys) ascending
                              x[0],      # tabkeys alphabetical
                              code_point_function(x[1][0]),
                              # Unicode codepoint of first character of phrase:
                              ord(x[1][0])
                          ))[:maximum_number_of_candidates]
        return sorted(candidates,
                      key=lambda x: (
                          - int(
                              typed_tabkeys == x[0]
                          ), # exact matches first!
                          -1*x[3],   # user_freq descending
                          -1*x[2],   # freq descending
                          len(x[0]), # len(tabkeys) ascending
                          x[0],      # tabkeys alphabetical
                          code_point_function(x[1][0]),
                          # Unicode codepoint of first character of phrase:
                          ord(x[1][0])
                      ))[:maximum_number_of_candidates]

    def select_words(
            self, tabkeys=u'', onechar=False, chinese_mode=-1,
            single_wildcard_char=u'', multi_wildcard_char=u'',
            auto_wildcard=False):
        '''
        Get matching phrases for tabkeys from the database.
        '''
        if not tabkeys:
            return []
        one_char_condition = ''
        if onechar:
            # for some users really like to select only single characters
            one_char_condition = ' AND length(phrase)=1 '

        sqlstr = '''
        SELECT tabkeys, phrase, freq, user_freq FROM
        (
            SELECT tabkeys, phrase, freq, user_freq FROM main.phrases
            WHERE tabkeys LIKE :tabkeys ESCAPE :escapechar %(one_char_condition)s
            UNION ALL
            SELECT tabkeys, phrase, freq, user_freq FROM user_db.phrases
            WHERE tabkeys LIKE :tabkeys ESCAPE :escapechar %(one_char_condition)s
        )
        ''' % {'one_char_condition': one_char_condition}
        escapechar = '☺'
        for c in '!@#':
            if c not in [single_wildcard_char, multi_wildcard_char]:
                escapechar = c
        tabkeys_for_like = tabkeys
        tabkeys_for_like = tabkeys_for_like.replace(
            escapechar, escapechar+escapechar)
        if '%' not in [single_wildcard_char, multi_wildcard_char]:
            tabkeys_for_like = tabkeys_for_like.replace('%', escapechar+'%')
        if '_' not in [single_wildcard_char, multi_wildcard_char]:
            tabkeys_for_like = tabkeys_for_like.replace('_', escapechar+'_')
        if single_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                single_wildcard_char, '_')
        if multi_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                multi_wildcard_char, '%%')
        if auto_wildcard:
            tabkeys_for_like += '%%'
        sqlargs = {'tabkeys': tabkeys_for_like, 'escapechar': escapechar}
        unfiltered_results = self.db.execute(sqlstr, sqlargs).fetchall()
        bitmask = None
        if chinese_mode == 0:
            bitmask = (1 << 0) # simplified only
        elif chinese_mode == 1:
            bitmask = (1 << 1) # traditional only
        if not bitmask:
            results = unfiltered_results
        else:
            results = []
            for result in unfiltered_results:
                if (bitmask
                    & chinese_variants.detect_chinese_category(result[1])):
                    results.append(result)
        # merge matches from the system database and from the user
        # database to avoid duplicates in the candidate list for
        # example, if we have the result ('aaaa', '工', 551000000, 0)
        # from the system database and ('aaaa', '工', 0, 5) from the
        # user database, these should be merged into one match
        # ('aaaa', '工', 551000000, 5).
        phrase_frequencies = {}
        for result in results:
            key = (result[0], result[1])
            if key not in phrase_frequencies:
                phrase_frequencies[key] = result
            else:
                phrase_frequencies.update([(
                    key,
                    key +
                    (
                        max(result[2], phrase_frequencies[key][2]),
                        max(result[3], phrase_frequencies[key][3]))
                )])
        best = self.best_candidates(
            typed_tabkeys=tabkeys,
            candidates=phrase_frequencies.values(),
            chinese_mode=chinese_mode)
        if debug_level > 1:
            sys.stderr.write("select_words() best=%s\n" %repr(best))
        return best

    def select_chinese_characters_by_pinyin(
            self, tabkeys=u'', chinese_mode=-1, single_wildcard_char=u'',
            multi_wildcard_char=u''):
        '''
        Get Chinese characters matching the pinyin given by tabkeys
        from the database.
        '''
        if not tabkeys:
            return []
        sqlstr = '''
        SELECT pinyin, zi, freq FROM main.pinyin WHERE pinyin LIKE :tabkeys
        ORDER BY freq DESC, pinyin ASC
        ;'''
        tabkeys_for_like = tabkeys
        if single_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                single_wildcard_char, '_')
        if multi_wildcard_char:
            tabkeys_for_like = tabkeys_for_like.replace(
                multi_wildcard_char, '%%')
        tabkeys_for_like += '%%'
        sqlargs = {'tabkeys': tabkeys_for_like}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        # now convert the results into a list of candidates in the format
        # which was returned before I simplified the pinyin database table.
        bitmask = None
        if chinese_mode == 0:
            bitmask = (1 << 0) # simplified only
        elif chinese_mode == 1:
            bitmask = (1 << 1) # traditional only
        phrase_frequencies = []
        for (pinyin, zi, freq) in results:
            if not bitmask:
                phrase_frequencies.append(tuple([pinyin, zi, freq, 0]))
            else:
                if bitmask & chinese_variants.detect_chinese_category(zi):
                    phrase_frequencies.append(tuple([pinyin, zi, freq, 0]))
        return self.best_candidates(
            typed_tabkeys=tabkeys,
            candidates=phrase_frequencies,
            chinese_mode=chinese_mode)

    def generate_userdb_desc (self):
        try:
            sqlstring = (
                'CREATE TABLE IF NOT EXISTS user_db.desc '
                + '(name PRIMARY KEY, value);')
            self.db.executescript (sqlstring)
            sqlstring = 'INSERT OR IGNORE INTO user_db.desc  VALUES (?, ?);'
            self.db.execute (sqlstring, ('version', database_version))
            sqlstring = (
                'INSERT OR IGNORE INTO user_db.desc  '
                + 'VALUES (?, DATETIME("now", "localtime"));')
            self.db.execute (sqlstring, ("create-time", ))
            self.db.commit ()
        except:
            import traceback
            traceback.print_exc ()

    def init_user_db(self, db_file):
        if not path.exists(db_file):
            db = sqlite3.connect(db_file)
            db.execute('PRAGMA encoding = "UTF-8";')
            db.execute('PRAGMA case_sensitive_like = true;')
            db.execute('PRAGMA page_size = 4096;')
            # 20000 pages should be enough to cache the whole database
            db.execute('PRAGMA cache_size = 20000;')
            db.execute('PRAGMA temp_store = MEMORY;')
            db.execute('PRAGMA journal_mode = WAL;')
            db.execute('PRAGMA journal_size_limit = 1000000;')
            db.execute('PRAGMA synchronous = NORMAL;')
            db.commit()

    def get_database_desc (self, db_file):
        if not path.exists (db_file):
            return None
        try:
            db = sqlite3.connect (db_file)
            desc = {}
            for row in db.execute ("SELECT * FROM desc;").fetchall():
                desc [row[0]] = row[1]
            db.close()
            return desc
        except:
            return None

    def get_number_of_columns_of_phrase_table(self, db_file):
        '''
        Get the number of columns in the 'phrases' table in
        the database in db_file.

        Determines the number of columns by parsing this:

        sqlite> select sql from sqlite_master where name='phrases';
        CREATE TABLE phrases
                (id INTEGER PRIMARY KEY, tabkeys TEXT, phrase TEXT,
                freq INTEGER, user_freq INTEGER)
        sqlite>

        This result could be on a single line, as above, or on multiple
        lines.
        '''
        if not path.exists (db_file):
            return 0
        try:
            db = sqlite3.connect (db_file)
            tp_res = db.execute(
                "select sql from sqlite_master where name='phrases';"
            ).fetchall()
            # Remove possible line breaks from the string where we
            # want to match:
            string = ' '.join(tp_res[0][0].splitlines())
            res = re.match(r'.*\((.*)\)', string)
            if res:
                tp = res.group(1).split(',')
                return len(tp)
            else:
                return 0
        except:
            return 0

    def get_goucima (self, zi):
        '''Get goucima of given character'''
        if not zi:
            return u''
        sqlstr = 'SELECT goucima FROM main.goucima WHERE zi = :zi;'
        results = self.db.execute(sqlstr, {'zi': zi}).fetchall()
        if results:
            goucima = results[0][0]
        else:
            goucima = u''
        if debug_level > 1:
            sys.stderr.write("get_goucima() goucima=%s\n" %goucima)
        return goucima

    def parse_phrase (self, phrase):
        '''Parse phrase to get its table code

        Example:

        Let’s assume we use wubi-jidian86. The rules in the source of
        that table are:

            RULES = ce2:p11+p12+p21+p22;ce3:p11+p21+p31+p32;ca4:p11+p21+p31+p-11

        “ce2” is a rule for phrases of length 2, “ce3” is a rule
        for phrases of length 3, “ca4” is a rule for phrases of
        length 4 *and* for all phrases with a length greater then
        4. “pnm” in such a rule means to use the n-th character of
        the phrase and take the m-th character of the table code of
        that character. I.e. “p-11” is the first character of the
        table code of the last character in the phrase.

        Let’s assume the phrase is “天下大事”. The goucima (構詞碼
        = “word formation keys”) for these 4 characters are:

            character goucima
            天        gdi
            下        ghi
            大        dddd
            事        gkvh

        (If no special goucima are defined by the user, the longest
        encoding for a single character in a table is the goucima for
        that character).

        The length of the phrase “天下大事” is 4 characters,
        therefore the rule ca4:p11+p21+p31+p-11 applies, i.e. the
        table code for “天下大事” is calculated by using the first,
        second, third and last character of the phrase and taking the
        first character of the goucima for each of these. Therefore,
        the table code for “天下大事” is “ggdg”.

        '''
        if debug_level > 1:
            sys.stderr.write(
                'parse_phrase() phrase=%(p)s rules%(r)s\n'
                % {'p': phrase, 'r': self.rules})
        if type(phrase) != type(u''):
            phrase = phrase.decode('UTF-8')
        # Shouldn’t this function try first whether the system database
        # already has an entry for this phrase and if yes return it
        # instead of constructing a new entry according to the rules?
        # And construct a new entry only when no entry already exists
        # in the system database??
        if len(phrase) == 0:
            return u''
        if len(phrase) == 1:
            return self.get_goucima(phrase)
        if not self.rules:
            return u''
        if len(phrase) in self.rules:
            rule = self.rules[len(phrase)]
        elif len(phrase) > self.rules['above']:
            rule = self.rules[self.rules['above']]
        else:
            sys.stderr.write(
                'No rule for this phrase length. phrase=%(p)s rules=%(r)s\n'
                %{'p': phrase, 'r': self.rules})
            return u''
        if len(rule) > self._mlen:
            sys.stderr.write(
                'Rule exceeds maximum key length. rule=%(r)s self._mlen=%(m)s\n'
                %{'r': rule, 'm': self._mlen})
            return u''
        tabkeys = u''
        for (zi, ma) in rule:
            if zi > 0:
                zi -= 1
            if ma > 0:
                ma -= 1
            tabkey = self.get_goucima(phrase[zi])[ma]
            if not tabkey:
                return u''
            tabkeys += tabkey
        if debug_level > 1:
            sys.stderr.write("parse_phrase() tabkeys=%s\n" %tabkeys)
        return tabkeys

    def is_in_system_database(self, tabkeys=u'', phrase=u''):
        '''
        Checks whether “phrase” can be matched in the system database
        with a key sequence *starting* with “tabkeys”.
        '''
        if debug_level > 1:
            sys.stderr.write(
                'is_in_system_database() tabkeys=%(t)s phrase=%(p)s\n'
                % {'t': tabkeys, 'p': phrase})
        if not tabkeys or not phrase:
            return False
        sqlstr = '''
        SELECT * FROM main.phrases
        WHERE tabkeys LIKE :tabkeys AND phrase = :phrase;
        '''
        sqlargs = {'tabkeys': tabkeys+'%%', 'phrase': phrase}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        if debug_level > 1:
            sys.stderr.write(
                'is_in_system_database() tabkeys=%(t)s phrase=%(p)s '
                % {'t': tabkeys, 'p': phrase}
                + 'results=%(r)s\n'
                % {'r': results})
        if results:
            return True
        else:
            return False

    def user_frequency(self, tabkeys=u'', phrase=u''):
        if debug_level > 1:
            sys.stderr.write(
                'user_frequency() tabkeys=%(t)s phrase=%(p)s\n'
                % {'t': tabkeys, 'p': phrase})
        if not tabkeys or not phrase:
            return 0
        sqlstr = '''
        SELECT sum(user_freq) FROM user_db.phrases
        WHERE tabkeys = :tabkeys AND phrase = :phrase GROUP BY tabkeys, phrase;
        '''
        sqlargs = {'tabkeys': tabkeys, 'phrase': phrase}
        result = self.db.execute(sqlstr, sqlargs).fetchall()
        if debug_level > 1:
            sys.stderr.write("user_frequency() result=%s\n" %result)
        if result:
            return result[0][0]
        else:
            return 0

    def check_phrase(self, tabkeys=u'', phrase=u''):
        '''Adjust user_freq in user database if necessary.

        Also, if the phrase is not in the system database, and it is a
        Chinese table, and defining user phrases is allowed, add it as
        a user defined phrase to the user database if it is not yet
        there.
        '''
        if debug_level > 1:
            sys.stderr.write(
                'check_phrase_internal() tabkey=%(t)s phrase=%(p)s\n'
                % {'t': tabkeys, 'p': phrase})
        if type(phrase) != type(u''):
            phrase = phrase.decode('utf8')
        if type(tabkeys) != type(u''):
            tabkeys = tabkeys.decode('utf8')
        if not tabkeys or not phrase:
            return
        if self._is_chinese and phrase in chinese_nocheck_chars:
            return
        if not self.dynamic_adjust:
            if not self.user_can_define_phrase or not self.is_chinese:
                return
            tabkeys = self.parse_phrase(phrase)
            if not tabkeys:
                # no tabkeys could be constructed from the rules in the table
                return
            if self.is_in_system_database(tabkeys=tabkeys, phrase=phrase):
                # if it is in the system database, it does not need to
                # be defined
                return
            if self.user_frequency(tabkeys=tabkeys, phrase=phrase) > 0:
                # if it is in the user database, it has been defined before
                return
            # add this user defined phrase to the user database:
            self.add_phrase(
                tabkeys=tabkeys, phrase=phrase, freq=-1, user_freq=1,
                database='user_db')
        else:
            if self.is_in_system_database(tabkeys=tabkeys, phrase=phrase):
                user_freq = self.user_frequency(tabkeys=tabkeys, phrase=phrase)
                if user_freq > 0:
                    self.update_phrase(
                        tabkeys=tabkeys, phrase=phrase, user_freq=user_freq+1)
                else:
                    self.add_phrase(
                        tabkeys=tabkeys, phrase=phrase, freq=0, user_freq=1,
                        database='user_db')
            else:
                if not self.user_can_define_phrase or not self.is_chinese:
                    return
                tabkeys = self.parse_phrase(phrase)
                if not tabkeys:
                    # no tabkeys could be constructed from the rules
                    # in the table
                    return
                user_freq = self.user_frequency(tabkeys=tabkeys, phrase=phrase)
                if user_freq > 0:
                    self.update_phrase(
                        tabkeys=tabkeys, phrase=phrase, user_freq=user_freq+1)
                else:
                    self.add_phrase(
                        tabkeys=tabkeys, phrase=phrase, freq=-1, user_freq=1,
                        database='user_db')

    def find_zi_code (self, phrase):
        '''
        Return the list of possible tabkeys for a phrase.

        For example, if “phrase” is “你” and the table is wubi-jidian.86.txt,
        the result will be ['wq', 'wqi', 'wqiy'] because that table
        contains the following 3 lines matching that phrase exactly:

        wq	你	597727619
        wqi	你	1490000000
        wqiy	你	1490000000
        '''
        if type(phrase) != type(u''):
            phrase = phrase.decode('utf8')
        sqlstr = '''
        SELECT tabkeys FROM main.phrases WHERE phrase = :phrase
        ORDER by length(tabkeys) ASC;
        '''
        sqlargs = {'phrase': phrase}
        results = self.db.execute(sqlstr, sqlargs).fetchall()
        list_of_possible_tabkeys = [x[0] for x in results]
        return list_of_possible_tabkeys

    def remove_phrase (
            self, tabkeys=u'', phrase=u'', database='user_db', commit=True):
        '''Remove phrase from database
        '''
        if not phrase:
            return
        if tabkeys:
            delete_sqlstr = '''
            DELETE FROM %(database)s.phrases
            WHERE tabkeys = :tabkeys AND phrase = :phrase;
            ''' % {'database': database}
        else:
            delete_sqlstr = '''
            DELETE FROM %(database)s.phrases
            WHERE phrase = :phrase;
            ''' % {'database': database}
        delete_sqlargs = {'tabkeys': tabkeys, 'phrase': phrase}
        self.db.execute(delete_sqlstr, delete_sqlargs)
        if commit:
            self.db.commit()

    def extract_user_phrases(
            self, database_file='', old_database_version='0.0'):
        '''extract user phrases from database'''
        sys.stderr.write(
            'Trying to recover the phrases from the old, '
            + 'incompatible database.\n')
        try:
            db = sqlite3.connect(database_file)
            db.execute('PRAGMA wal_checkpoint;')
            if old_database_version >= '1.00':
                phrases = db.execute(
                    '''
                    SELECT tabkeys, phrase, freq, sum(user_freq) FROM phrases
                    GROUP BY tabkeys, phrase, freq;
                    '''
                ).fetchall()
                db.close()
                phrases = sorted(
                    phrases, key=lambda x: (x[0], x[1], x[2], x[3]))
                sys.stderr.write(
                    'Recovered phrases from the old database: phrases=%s\n'
                    % repr(phrases))
                return phrases[:]
            else:
                # database is very old, it may still use many columns
                # of type INTEGER for the tabkeys. Therefore, ignore
                # the tabkeys in the database and try to get them
                # from the system database instead.
                phrases = []
                results = db.execute(
                    'SELECT phrase, sum(user_freq) '
                    + 'FROM phrases GROUP BY phrase;'
                ).fetchall()
                for result in results:
                    sqlstr = '''
                    SELECT tabkeys FROM main.phrases WHERE phrase = :phrase
                    ORDER BY length(tabkeys) DESC;
                    '''
                    sqlargs = {'phrase': result[0]}
                    tabkeys_results = self.db.execute(
                        sqlstr, sqlargs).fetchall()
                    if tabkeys_results:
                        phrases.append(
                            (tabkeys_results[0][0], result[0], 0, result[1]))
                    else:
                        # No tabkeys for that phrase could not be
                        # found in the system database.  Try to get
                        # tabkeys by calling self.parse_phrase(), that
                        # might return something if the table has
                        # rules to construct user defined phrases:
                        tabkeys = self.parse_phrase(result[0])
                        if tabkeys:
                            # for user defined phrases, the “freq” column is -1:
                            phrases.append((tabkeys, result[0], -1, result[1]))
                db.close()
                phrases = sorted(
                    phrases, key=lambda x: (x[0], x[1], x[2], x[3]))
                sys.stderr.write(
                    'Recovered phrases from the very old database: phrases=%s\n'
                    % repr(phrases))
                return phrases[:]
        except:
            import traceback
            traceback.print_exc()
            return []
