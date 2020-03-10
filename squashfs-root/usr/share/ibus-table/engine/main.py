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
import optparse

from gi import require_version
require_version('IBus', '1.0')
from gi.repository import IBus
from gi.repository import GLib
import re
from signal import signal, SIGTERM, SIGINT

import factory
import tabsqlitedb

import ibus_table_location

db_dir = os.path.join (ibus_table_location.data(), 'tables')
byo_db_dir = os.path.join(ibus_table_location.data_home(), "byo-tables")
icon_dir = os.path.join (ibus_table_location.data(), 'icons')
setup_cmd = os.path.join(ibus_table_location.lib(), "ibus-setup-table")
logfile = os.path.join(ibus_table_location.cache_home(), 'debug.log')

opt = optparse.OptionParser()

opt.set_usage ('%prog --table a_table.db')
opt.add_option(
    '--table', '-t',
    action = 'store',
    type = 'string',
    dest = 'db',
    default = '',
    help = 'Set the IME table file, default: %default')
opt.add_option(
    '--daemon', '-d',
    action = 'store_true',
    dest = 'daemon',
    default=False,
    help = 'Run as daemon, default: %default')
opt.add_option(
    '--ibus', '-i',
    action = 'store_true',
    dest = 'ibus',
    default = False,
    help = 'Set the IME icon file, default: %default')
opt.add_option(
    '--xml', '-x',
    action = 'store_true',
    dest = 'xml',
    default = False,
    help = 'output the engines xml part, default: %default')
opt.add_option(
    '--no-debug', '-n',
    action = 'store_false', dest = 'debug',default = True,
    help = 'redirect stdout and stderr to ' + logfile + ', default: %default')
opt.add_option(
    '--profile', '-p',
    action = 'store_true', dest = 'profile', default = False,
    help = ('print profiling information into the debug log. '
            +'Works only together with --debug.'))

(options, args) = opt.parse_args()
#if not options.db:
#    opt.error('no db found!')

if (not options.xml) and options.debug:
    sys.stdout = open (logfile, mode='a', buffering=1)
    sys.stderr = open (logfile, mode='a', buffering=1)
    from time import strftime
    print('--- %s ---' %strftime('%Y-%m-%d: %H:%M:%S'))

if options.profile:
    import cProfile, pstats
    profile = cProfile.Profile()

class IMApp:
    def __init__(self, dbfile, exec_by_ibus):
        self.__mainloop = GLib.MainLoop()
        self.__bus = IBus.Bus()
        self.__bus.connect("disconnected", self.__bus_destroy_cb)
        self.__factory = factory.EngineFactory(self.__bus, dbfile)
        self.destroyed = False
        if exec_by_ibus:
            self.__bus.request_name("org.freedesktop.IBus.Table", 0)
        else:
            self.__component = IBus.Component(
                name='org.freedesktop.IBus.Table',
                description='Table Component',
                version='0.1.0',
                license='GPL',
                author='Yuwei Yu <acevery@gmail.com>',
                homepage='http://code.google.com/p/ibus/',
                textdomain='ibus-table')
            # now we get IME info from self.__factory.db
            engine_name = os.path.basename(
                self.__factory.db.filename).replace('.db', '')
            name = 'table:'+engine_name
            longname = self.__factory.db.ime_properties.get("name")
            description = self.__factory.db.ime_properties.get("description")
            language = self.__factory.db.ime_properties.get("languages")
            credit = self.__factory.db.ime_properties.get("credit")
            author = self.__factory.db.ime_properties.get("author")
            icon = self.__factory.db.ime_properties.get("icon")
            if icon:
                icon = os.path.join (icon_dir, icon)
                if not os.access( icon, os.F_OK):
                    icon = ''
            layout = self.__factory.db.ime_properties.get("layout")
            symbol = self.__factory.db.ime_properties.get("symbol")
            setup_arg = "{} --engine-name {}".format(setup_cmd, name)
            engine = IBus.EngineDesc(name=name,
                                        longname=longname,
                                        description=description,
                                        language=language,
                                        license=credit,
                                        author=author,
                                        icon=icon,
                                        layout=layout,
                                        symbol=symbol,
                                        setupdsis=setup_arg)
            self.__component.add_engines(engine)
            self.__bus.register_component(self.__component)


    def run(self):
        if options.profile:
            profile.enable()
        self.__mainloop.run()
        self.__bus_destroy_cb()

    def quit(self):
        self.__bus_destroy_cb()

    def __bus_destroy_cb(self, bus=None):
        if self.destroyed:
            return
        print("finalizing:)")
        self.__factory.do_destroy()
        self.destroyed = True
        self.__mainloop.quit()
        if options.profile:
            profile.disable()
            p = pstats.Stats(profile)
            p.strip_dirs()
            p.sort_stats('cumulative')
            p.print_stats('main', 25)
            p.print_stats('factory', 25)
            p.print_stats('tabsqlite', 25)
            p.print_stats('table', 25)

def cleanup (ima_ins):
    ima_ins.quit()
    sys.exit()

def indent(elem, level=0):
    '''Use to format xml Element pretty :)'''
    i = "\n" + level*"    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for e in elem:
            indent(e, level+1)
            if not e.tail or not e.tail.strip():
                e.tail = i + "    "
        if not e.tail or not e.tail.strip():
            e.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def main():
    if options.xml:
        from locale import getdefaultlocale
        from xml.etree.ElementTree import Element, SubElement, tostring
        # we will output the engines xml and return.
        # 1. we find all dbs in db_dir and extract the infos into
        #    Elements
        dbs = os.listdir(db_dir)
        dbs = filter (lambda x: x.endswith('.db'), dbs)

        _all_dbs = []
        for _db in dbs:
            _all_dbs.append(os.path.join (db_dir, _db))
        try:
            byo_dbs = os.listdir(byo_db_dir)
            byo_dbs = filter (lambda x: x.endswith('.db'), byo_dbs)
            for _db in byo_dbs:
                _all_dbs.append(os.path.join (byo_db_dir, _db))
        except OSError:
            # byo_db_dir does not exist or is not accessible
            pass

        egs = Element('engines')
        for _db in _all_dbs:
            _sq_db = tabsqlitedb.tabsqlitedb (_db, user_db=None)
            _engine = SubElement (egs,'engine')

            _name = SubElement (_engine, 'name')
            engine_name = os.path.basename(_db).replace ('.db','')
            _name.text = 'table:'+engine_name
            setup_arg = "{} --engine-name {}".format(setup_cmd, _name.text)

            _longname = SubElement (_engine, 'longname')
            _longname.text = ''
            # getdefaultlocale() returns something like ('ja_JP', 'UTF-8').
            # In case of C/POSIX locale it returns (None, None)
            _locale = getdefaultlocale()[0]
            if _locale:
                _locale = _locale.lower()
            else:
                _locale = 'en'
            _longname.text = _sq_db.ime_properties.get(
                '.'.join(['name', _locale]))
            if not _longname.text:
                _longname.text = _sq_db.ime_properties.get(
                    '.'.join(['name', _locale.split('_')[0]]))
            if not _longname.text:
                _longname.text = _sq_db.ime_properties.get('name')
            if not _longname.text:
                _longname.text = engine_name

            _language = SubElement (_engine, 'language')
            _langs = _sq_db.ime_properties.get('languages')
            if _langs:
                _langs = _langs.split (',')
                if len (_langs) == 1:
                    _language.text = _langs[0].strip()
                else:
                    # we ignore the place
                    _language.text = _langs[0].strip().split('_')[0]

            _license = SubElement (_engine, 'license')
            _license.text = _sq_db.ime_properties.get('license')

            _author = SubElement (_engine, 'author')
            _author.text  = _sq_db.ime_properties.get('author')

            _icon = SubElement (_engine, 'icon')
            _icon_basename = _sq_db.ime_properties.get('icon')
            if _icon_basename:
                _icon.text = os.path.join (icon_dir, _icon_basename)

            _layout = SubElement (_engine, 'layout')
            _layout.text = _sq_db.ime_properties.get('layout')

            _symbol = SubElement (_engine, 'symbol')
            _symbol.text = _sq_db.ime_properties.get('symbol')

            _desc = SubElement (_engine, 'description')
            _desc.text = _sq_db.ime_properties.get('description')

            _setup = SubElement (_engine, 'setup')
            _setup.text = setup_arg

        # now format the xmlout pretty
        indent (egs)
        egsout = tostring (egs, encoding='utf8').decode('utf-8')
        patt = re.compile (r'<\?.*\?>\n')
        egsout = patt.sub ('', egsout)
        sys.stdout.buffer.write((egsout+'\n').encode('utf-8'))
        return 0

    if options.daemon :
        if os.fork():
            sys.exit()
    if options.db:
        if os.access( options.db, os.F_OK):
            db = options.db
        else:
            db = '%s%s%s' % (db_dir, os.path.sep, os.path.basename(options.db))
    else:
        db = ""
    ima = IMApp(db, options.ibus)
    signal (SIGTERM, lambda signum, stack_frame: cleanup(ima))
    signal (SIGINT, lambda signum, stack_frame: cleanup(ima))
    try:
        ima.run()
    except KeyboardInterrupt:
        ima.quit()

if __name__ == "__main__":
    main()

