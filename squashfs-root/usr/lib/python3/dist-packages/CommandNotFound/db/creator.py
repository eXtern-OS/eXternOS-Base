#!/usr/bin/python3

import errno
import json
import logging
import os
import sqlite3
import sys
import time

import apt_pkg
apt_pkg.init()

# TODO:
# - add apt.conf.d snippet for download handling
# - add apt::update::post-invoke-success handler

component_priorities = {
    'main': 120,
    'universe': 100,
    'contrib': 80,
    'restricted': 60,
    'non-free': 40,
    'multiverse': 20,
}

# pkgnames in here are blacklisted


create_db_sql="""
           CREATE TABLE IF NOT EXISTS "commands" 
           (
            [cmdID] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            [pkgID] INTEGER NOT NULL,
            [command] TEXT,
            FOREIGN KEY ([pkgID]) REFERENCES "pkgs" ([pkgID])
           );
           CREATE TABLE IF NOT EXISTS "packages"
           (
            [pkgID] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            [name] TEXT,
            [version] TEXT,
            [component] TEXT,
            [priority] INTEGER
           );
           CREATE INDEX IF NOT EXISTS idx_commands_command ON commands (command);
           CREATE INDEX IF NOT EXISTS idx_packages_name ON packages (name);
"""

# FIXME:
# - add support for foreign arch in DB (add foreign commands if there
#   is not native command)
# - addd support for -backports: pkgname must be appended with /backports
#   and only be shown if there is no other command available
# - do not re-create the DB everytime, only if sources.list changed
# - add "last-mtime" into the DB, then we can skip all packages files
#   where the mtime is older and we only need to update the DB

class measure:
    def __init__(self, what, stats):
        self.what = what
        self.stats = stats
    def __enter__(self):
        self.now = time.time()
    def __exit__(self, *args):
        if not self.what in self.stats:
            self.stats[self.what] = 0
        self.stats[self.what] += time.time() - self.now


def rm_f(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class DbCreator:
    def __init__(self, files):
        self.files = files
        self.primary_arch = apt_pkg.get_architectures()[0]
        self.stats = {"total": 0,"total_time": time.time()}
    def create(self, dbname):
        metadata_file = dbname+".metadata"
        if not self._db_update_needed(metadata_file):
            logging.info(
                "%s does not require an update (inputs unchanged)", dbname)
            return
        tmpdb = dbname+".tmp"
        with sqlite3.connect(tmpdb) as con:
            con.executescript(create_db_sql)
            self._fill_commands(con)
        # remove now stale metadata
        rm_f(metadata_file)
        # put database in place
        os.rename(tmpdb, dbname)
        # add new metadata
        with open(metadata_file, "w") as fp:
            json.dump(self._calc_input_metadata(), fp)
    def _db_update_needed(self, metadata_file):
        if not os.path.exists(metadata_file):
            return True
        try:
            with open(metadata_file) as fp:
                meta = json.load(fp)
            return meta != self._calc_input_metadata()
        except Exception as e:
            logging.warning("cannot read %s: %s", metadata_file, e)
            return True
    def _calc_input_metadata(self):
        meta = {}
        for p in self.files:
            st = os.stat(p)
            meta[p] = {
                'st_ino': st.st_ino,
                'st_dev': st.st_dev,
                'st_uid': st.st_uid,
                'st_gid': st.st_gid,
                'st_size': st.st_size,
                'st_mtime': st.st_mtime,
            }
        return meta
    def _fill_commands(self, con):
        for f in self.files:
            with open(f) as fp:
                self._parse_single_commands_file(con, fp)
        self.stats["total_time"] = time.time() - self.stats["total_time"]
        logging.info("processed %i packages in %.2fs" % (
            self.stats["total"], self.stats["total_time"]))
    def _in_db(self, con, command, pkgname):
        already_in_db = con.execute(
            """
            SELECT packages.pkgID, name, version 
            FROM commands 
            INNER JOIN packages on packages.pkgID = commands.pkgID
            WHERE commands.command=? AND packages.name=?;
            """, (command, pkgname)).fetchone()
        return already_in_db
    def _delete_pkgid(self, con, pkgid):
        con.execute("DELETE FROM packages WHERE pkgID=?", (pkgid,) )
        con.execute("DELETE FROM commands WHERE pkgID=?", (pkgid,) )
    def _get_pkgid(self, con, pkgname):
        have_pkg = con.execute(
            "SELECT pkgID from packages WHERE name=?", (pkgname,)).fetchone()
        if have_pkg:
            return have_pkg[0]
        return None
    def _insert_package(self, con, pkgname, version, component, priority):
        cur=con.execute("""
            INSERT INTO packages (name, version, component, priority)
            VALUES (?, ?, ?, ?);
            """, (pkgname, version, component, priority))
        return cur.lastrowid
    def _insert_command(self, con, command, pkg_id):
        con.execute("""
        INSERT INTO commands (command, pkgID) VALUES (?, ?);
        """, (command, pkg_id))
    def _parse_single_commands_file(self, con, fp):
        tagf = apt_pkg.TagFile(fp)
        # file empty
        if not tagf.step():
            return
        # read header
        suite=tagf.section["suite"]
        # FIXME: support backports
        if suite.endswith("-backports"):
            return
        component=tagf.section["component"]
        arch=tagf.section["arch"]
        # FIXME: add code for secondary arch handling!
        if arch != "all" and arch != self.primary_arch:
            return
        # step over the pkgs
        while tagf.step():
            self.stats["total"] += 1
            pkgname=tagf.section["name"]
            # allow to override the viisble pkgname to accomodate for
            # cases like "python2.7" which is part of python2.7-minimal
            # but users should just install python2.7
            if tagf.section.get("visible-pkgname"):
                pkgname = tagf.section["visible-pkgname"]
            version=tagf.section.get("version", "")
            ignore_commands=set()
            if tagf.section.get("ignore-commands", ""):
                ignore_commands=set(tagf.section.get("ignore-commands", "").split(","))
            for command in tagf.section["commands"].split(","):
                if command in ignore_commands:
                    continue
                # see if we have the command already
                with measure("sql_already_db", self.stats):
                    already_in_db=self._in_db(con, command, pkgname)
                if already_in_db:
                    # we found a version that is higher what we have
                    # in the DB -> remove current, insert higher
                    if apt_pkg.version_compare(version, already_in_db[2]) > 0:
                        logging.debug("replacing exiting %s in DB (higher version)" % command)
                        with measure("sql_delete_already_in_db", self.stats):
                            self._delete_pkgid(con, already_in_db[0])
                    else:
                        logging.debug("skipping %s from %s (lower/same version)" % (command, suite))
                        continue
                logging.debug("adding %s from %s/%s (%s)" % (
                    command, pkgname, version, suite))
                # insert new data
                with measure("sql_have_pkg", self.stats):
                    pkg_id = self._get_pkgid(con, pkgname)
                if not pkg_id:
                    priority = component_priorities[component]
                    priority += int(tagf.section.get("priority-bonus", "0"))
                    with measure("sql_insert_pkg", self.stats):
                        pkg_id = self._insert_package(con, pkgname, version, component, priority)
                with measure("sql_insert_cmd", self.stats):
                    self._insert_command(con, command, pkg_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 3:
        print("usage: %s <output-db-path> <files...>" % sys.argv[0])
        print(" e.g.: %s commands.db ./dists/*/*/*/Commands-*" % sys.argv[0])
        print(" e.g.: %s /var/lib/command-not-found/commands.db  /var/lib/apt/lists/*Commands-*", sys.argv[0])
        sys.exit(1)
    col = DbCreator(sys.argv[2:])
    col.create(sys.argv[1])
    for stat, amount in col.stats.items():
        logging.debug("%s: %s" % (stat, amount))

