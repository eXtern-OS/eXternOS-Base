#!/usr/bin/python3

import sqlite3

import apt_pkg
apt_pkg.init()


class SqliteDatabase(object):

    def __init__(self, filename):
        self.con = sqlite3.connect(filename)
        self.component = ""

    def lookup(self, command):
        # deal with invalid unicode (LP: #1130444)
        command = command.encode("utf-8", "surrogateescape").decode("utf-8", "replace")
        results = []
        for row in self.con.execute(
                """
                SELECT packages.name, packages.version, packages.component
                FROM commands
                INNER JOIN packages on packages.pkgID = commands.pkgID
                WHERE commands.command=?
                ORDER BY packages.priority DESC
                """, (command,)).fetchall():
            results.append( (row[0], row[1], row[2]) )
        return results
                        
