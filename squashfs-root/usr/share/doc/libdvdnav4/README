What is this all about?
-----------------------

libdvdnav is a library that allows easy use of sophisticated DVD navigation
features such as DVD menus, multiangle playback and even interactive DVD games.
All this functionality is provided through a simple API which provides the
DVD playback as a single logical stream of blocks, intermitted by special
dvdnav events to report certain conditions. The main usage of libdvdnav is a
loop regularly calling a function to get the next block, surrounded by
additional calls to tell the library of user interaction.
The whole DVD virtual machine and internal playback states are completely
encapsulated.

Where does it come from?
------------------------

This library was based on a lot of code and expertise from the Ogle project.
Ogle was the first DVD player who implemented free DVD navigation. The
libdvdnav developers wish to express their gratitude to the Ogle people
for all the valuable research work they have done.

Initially, the dvdnav code was part of a plugin to the xine media player
called xine-dvdnav. Later on, the DVD VM specific code was split
from xine-dvdnav and went into the first version of libdvdnav.

Then, it was forked, and forked again on MPlayer repositories.
libdvdnav and libdvdread were merged, and then split again.

This is now a new fork libdvdnav, that was created to overcome the lack of
responsiveness of the official development channel (once again).

This new fork will try to simplify, stabilize, fix the security issues and the
numerous crashes and maintain a correct player-agnostic library for DVD playback.

This fork will try to maintain correct authorship tracking, by using git and a
proper history.

How can I use it?
-----------------

libdvdnav is completely licensed under GPL. You may use it at wish within the
bounds of this license. See the file "COPYING" for a copy of the GPL.

Sources for documentation on libdvdnav are:
* the examples directory contains a simple program using libdvdnav
  this one is well-commented and therefore a good starting point
* the public header dvdnav.h documents the API
* the public header dvdnav_events.h documents the dvdnav events
* doc/library_layout contains some info on the internal working of libdvdnav

Sources for documentation on DVD terminology, structure and surrounding concepts:
* doc/dvd_structures briefly explains DVD terms and organization
* a more detailed description of DVD structures is available at
  http://www.mpucoder.com/dvd/
* the ifo_types.h and nav_types.h headers are also interesting if you
  are already used to the sometimes cryptical abbreviations
