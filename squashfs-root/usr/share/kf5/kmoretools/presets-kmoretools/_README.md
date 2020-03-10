Info about this directory
=========================

Why?
----
Look at the KMoreTools documentation. The files are needed
1) to provide translations for non-installed programs
2) to fix the Exec lines for some desktop files (see .kmt-editin files)

From where?
-----------
All of the .desktop, .png and .svg files are copies from the upstream project.
In practice this means the files are taken from the KMoreTools contributor's
system's installed programs.

.png icons are taken in 32x32 pixels size.
(The filename of the icon is specified in the .desktop file.)

.kmt-edition files
------------------
Files with ".kmt-edition" in their names are created by the
KMoreTools authors as workaround because nothing suitable was provided upstream
or because something else had to be fixed with the desktop file.

Look at the comments in each of the .kmt-edition files to see why it was created.
The goal should be to bring these changes upstream and thus have as few kmt-edition
files as possible.
