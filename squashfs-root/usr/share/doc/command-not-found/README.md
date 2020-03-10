# Command-not-found

This application implements the command-not-found spec at:
https://wiki.ubuntu.com/CommandNotFoundMagic

If you want automatic prompts to install the package, set
COMMAND_NOT_FOUND_INSTALL_PROMPT in your environment.

To use it in bash, please add the following line to your .bashrc file:
. /etc/bash_command_not_found

To use it in zsh, please add the following line to your .zshrc file:
. /etc/zsh_command_not_found
Note that it overrides the preexec and precmd functions, in case you have
defined your own.

## Data sources

Command-not-found will for the following data sources:
1. sqlite3 DB in /usr/share/command-not-found/commands.db, if that is
   *not* found it will fallback to (2)
2. legacy /usr/share/command-not-found/programs.d/*.db gdbm style database

The datasource (1) is generated from data found on the archive server
in deb822 format. The data is generated via
https://code.launchpad.net/~mvo/command-not-found-extractor/+git/command-not-found-extractor
and is downloaded via `apt update`.

The datasource (2) is generated via a static `command-not-found-data`
deb package. It is less rich and dynamic than (1) and should be
considered legacy and only be used if no better data source is
available.

### DB schemas

#### Legacy DB:

Simple key/value store with key `program_name` (e.g. bash) and value a
comma separated list of packages that provide the program name. The
filename indicates the component and architecuture via:
`$component-$arch.db`.

#### Sqlite3 DB:

The database looks like this:
```
           CREATE TABLE IF NOT EXISTS "commands" 
           (
            [command] TEXT PRIMARY KEY NOT NULL,
            [pkgID] INTEGER NOT NULL,
            FOREIGN KEY ([pkgID]) REFERENCES "pkgs" ([pkgID])
           );
           CREATE TABLE IF NOT EXISTS "packages"
           (
            [pkgID] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            [name] TEXT,
            [version] TEXT,
            [priority] INTEGER
           );
```

There is no need to store the component because we do not display that
in c-n-f. Note that the "name" in the "pkgs" table may include an
architecture qualifier. This is an optimization for multi-arch
systems, by default if there is "bash:amd64" and "bash:i386" on an
amd64 multi-arch systems we will not store "bash:i386" in the DB at
all and will store "bash:amd64" just as "bash". However for commands
that are only available for the foreign arch (e.g. "wine:i386") the
full qualified package name is stored in the DB and used in the c-n-f
output.


## Development

To run the tests type:

    $ python -m unittest discover

