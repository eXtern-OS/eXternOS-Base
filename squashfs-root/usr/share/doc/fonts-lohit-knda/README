Lohit Project Information :-
See https://fedorahosted.org/lohit/ for more details.

Mailing list:-
http://www.redhat.com/mailman/listinfo/lohit-devel-list

Generating ttf from source file:
Note: If you have downloaded ttf tarball this step is not required.
1. Building ttf file with fontforge.
- Open .sfd file in Fontforge.
- Import .fea file using (File->Merge Feature Info)
- File-> Generate fonts.

2. Using Makefile (Recommended)
- In terminal change directory to lohit downloaded tarball and run 
- $make ttf  
- This will generate ttf.

3. Building webfonts
- Fedora users -> $yum install sfntly  
- Check if your distro has sfntly, if not Download sfntly for building web fonts.
	- Download "sfntly-read-only.zip" from http://code.google.com/p/sfntly/downloads/list 
	- Go to java folder and run $ant
	- Copy sfnttool.jar to /usr/share/java/
- $make woff eot
- This will generate webfonts.
4. $make all will generate all binaries.

Installing fonts:
Fedora or other linux distro
1. Using graphics user interface
- open ttf using gnome-font-viewer or kfontview
- click on install fonts

2. Using terminal
- copy font to /~.local/share/fonts
- run $fc-cache
- open gedit, it should be listed now

Windows
1. Nicely documented on http://windows.microsoft.com/en-in/windows-vista/install-or-uninstall-fonts 
