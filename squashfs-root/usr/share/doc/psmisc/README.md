[<img alt="Coverity Scan Build Status" src="https://scan.coverity.com/projects/2048/badge.svg"/>](https://scan.coverity.com/projects/psmisc)
# psmisc

A package of small utilities that use the proc file-system.

* *fuser* - Identifies processes using files or sockets
* *killall* - kills processes by name, e.g. killall -HUP named
* *prtstat* - prints statistics of a process
* *pslog* - prints log path(s) of a process
* *pstree* - shows the currently running processes as a tree
* *peekfd* - shows the data travelling over a file descriptor

psmisc is now hosted on gitlab at https://gitlab.com/psmisc/psmisc
for bugs or issues please use the issue tracker at
https://gitlab.com/psmisc/psmisc/issues

## Email List
No email list as such, but there is a Gitter room found at https://gitter.im/psmisc/Lobby
This is an experimental trial of how Gitter works with a Gitlab project such as psmisc but
its better than no email list.

## fuser on network fs
On network file-systems, fuser can hang because its trying to stat files
that may go away.  If you use the --with-timeout-stat option during
the configure step then fuser will fork a process to run stat. This means
fuser doesn't hang, but it is much slower.

## Credits

### Translations
My thanks for the various translators who have cheerfully given me the po
files to make psmisc speak different languages.  If your language is not
supported then let me know, all it takes is translating one file in
a certain manner.

### Icons
The pstree icons were drawn by Tatlin at Coresis who has given permission
for them to be used for psmisc.

## Copyright Change
The license has changed to GPL for version 20 onwards with permission
of the original authors.  People who want to use these programs under
the previous license will have to look at psmisc 19 or below.
