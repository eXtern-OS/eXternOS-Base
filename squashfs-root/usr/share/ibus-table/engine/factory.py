# -*- coding: utf-8 -*-
# vim:et sw=4 sts=4 sw=4
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

from gi import require_version
require_version('IBus', '1.0')
from gi.repository import IBus
import table
import tabsqlitedb
import os
import re

from gettext import dgettext
_  = lambda a : dgettext ("ibus-table", a)
N_ = lambda a : a

class EngineFactory (IBus.Factory):
    """Table IM Engine Factory"""
    def __init__ (self, bus, db="", icon=""):
        # db is the full path to the sql database
        if db:
            self.dbusname = os.path.basename(db).replace('.db','')
            udb = os.path.basename(db).replace('.db','-user.db')
            self.db = tabsqlitedb.tabsqlitedb(filename = db, user_db = udb)
            self.db.db.commit()
            self.dbdict = {self.dbusname:self.db}
        else:
            self.db = None
            self.dbdict = {}


        # init factory
        self.bus = bus
        super(EngineFactory, self).__init__(connection=bus.get_connection(),
                                            object_path=IBus.PATH_FACTORY)
        self.engine_id = 0
        self.engine_path = ''

    def do_create_engine(self, engine_name):
        engine_name = re.sub(r'^table:', '', engine_name)
        engine_base_path = "/com/redhat/IBus/engines/table/%s/engine/"
        path_patt = re.compile(r'[^a-zA-Z0-9_/]')
        self.engine_path = engine_base_path % path_patt.sub ('_', engine_name)
        try:
            if not self.db:
                # first check self.dbdict
                if not engine_name in self.dbdict:
                    try:
                        db_dir = os.path.join(
                            os.getenv('IBUS_TABLE_LOCATION'),'tables')
                    except:
                        db_dir = "/usr/share/ibus-table/tables"
                    db = os.path.join (db_dir, engine_name+'.db')
                    udb = engine_name+'-user.db'
                    if not os.path.exists(db):
                        byo_db_dir = os.path.join(
                            os.getenv('HOME'), '.ibus/byo-tables')
                        db = os.path.join(byo_db_dir, engine_name + '.db')
                    _sq_db = tabsqlitedb.tabsqlitedb(
                        filename = db, user_db = udb)
                    _sq_db.db.commit()
                    self.dbdict[engine_name] = _sq_db
            else:
                name = self.dbusname

            engine = table.tabengine(self.bus,
                                     self.engine_path + str(self.engine_id),
                                     self.dbdict[engine_name])
            self.engine_id += 1
            #return engine.get_dbus_object()
            return engine
        except:
            print("failed to create engine %s" %engine_name)
            import traceback
            traceback.print_exc ()
            raise Exception("Cannot create engine %s" %engine_name)

    def do_destroy (self):
        '''Destructor, which finish some task for IME'''
        #
        ## we need to sync the temp userdb in memory to the user_db on disk
        for _db in self.dbdict:
            self.dbdict[_db].sync_usrdb ()
        ##print "Have synced user db\n"
        super(EngineFactory, self).destroy()


