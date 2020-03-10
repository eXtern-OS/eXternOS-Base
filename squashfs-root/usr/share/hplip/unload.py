#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# (c) Copyright 2003-2015 HP Development Company, L.P.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# Author: Don Welch
#

__version__ = '3.3'
__mod__ = 'hp-unload'
__title__ = 'Photo Card Access Utility'
__doc__ = "Access inserted photo cards on supported HPLIP printers. This provides an alternative for older devices that do not support USB mass storage or for access to photo cards over a network."

# Std Lib
import sys
import os
import os.path
import getopt
import re
import cmd
import time
import fnmatch
import string
import operator

try:
    import readline
except ImportError:
    pass

# Local
from base.g import *
from base.sixext import PY3
if PY3:
    log.error("This functionality is not spported in python3 environment.")
    sys.exit(1)

from base import device, utils, tui, module
from prnt import cups

# Console class (from ASPN Python Cookbook)
# Author:   James Thiele
# Date:     27 April 2004
# Version:  1.0
# Location: http://www.eskimo.com/~jet/python/examples/cmd/
# Copyright (c) 2004, James Thiele

class Console(cmd.Cmd):

    def __init__(self, pc):
        cmd.Cmd.__init__(self)
        self.intro  = "Type 'help' for a list of commands. Type 'exit' to quit."
        self.pc = pc
        disk_info = self.pc.info()
        pc.write_protect = disk_info[8]
        if pc.write_protect:
            log.warning("Photo card is write protected.")
        self.prompt = log.bold("pcard: %s > " % self.pc.pwd())

    # Command definitions
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print(self._hist)

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    def do_quit(self, args):
        """Exits from the console"""
        return -1

    # Command definitions to support Cmd object functionality
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        # The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    # Override methods in Cmd object
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   # sets up command completion
        self._hist    = []      # No history yet
        self._locals  = {}      # Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   # Clean up command completion
        print("Exiting...")

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [line.strip()]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def default(self, line):
        print(log.bold("ERROR: Unrecognized command. Use 'help' to list commands."))

    def do_ldir(self, args):
        """ List local directory contents."""
        os.system('ls -l')

    def do_lls(self, args):
        """ List local directory contents."""
        os.system('ls -l')

    def do_dir(self, args):
        """Synonym for the ls command."""
        return self.do_ls(args)

    def do_ls(self, args):
        """List photo card directory contents."""
        args = args.strip().lower()
        files = self.pc.ls(True, args)

        total_size = 0
        formatter = utils.TextFormatter(
                (
                    {'width': 14, 'margin' : 2},
                    {'width': 12, 'margin' : 2, 'alignment' : utils.TextFormatter.RIGHT},
                    {'width': 30, 'margin' : 2},
                )
            )

        print()
        print(log.bold(formatter.compose(("Name", "Size", "Type"))))

        num_files = 0
        for d in self.pc.current_directories():
            if d[0] in ('.', '..'):
                print(formatter.compose((d[0], "", "directory")))
            else:
                print(formatter.compose((d[0] + "/", "", "directory")))

        for f in self.pc.current_files():
            print(formatter.compose((f[0], utils.format_bytes(f[2]), self.pc.classify_file(f[0]))))
            num_files += 1
            total_size += f[2]

        print(log.bold("% d files, %s" % (num_files, utils.format_bytes(total_size, True))))


    def do_df(self, args):
        """Display free space on photo card.
        Options:
        -h\tDisplay in human readable format
        """
        freespace = self.pc.df()

        if args.strip().lower() == '-h':
            fs = utils.format_bytes(freespace)
        else:
            fs = utils.commafy(freespace)

        print("Freespace = %s Bytes" % fs)


    def do_cp(self, args, remove_after_copy=False):
        """Copy files from photo card to current local directory.
        Usage:
        \tcp FILENAME(S)|GLOB PATTERN(S)
        Example:
        \tCopy all JPEG and GIF files and a file named thumbs.db from photo card to local directory:
        \tcp *.jpg *.gif thumbs.db
        """
        args = args.strip().lower()

        matched_files = self.pc.match_files(args)

        if len(matched_files) == 0:
            print("ERROR: File(s) not found.")
        else:
            total, delta = self.pc.cp_multiple(matched_files, remove_after_copy, self.cp_status_callback, self.rm_status_callback)

            print(log.bold("\n%s transfered in %d sec (%d KB/sec)" % (utils.format_bytes(total), delta, (total/1024)/(delta))))

    def do_unload(self, args):
        """Unload all image files from photocard to current local directory.
        Note:
        \tSubdirectories on photo card are not preserved
        Options:
        -x\tDon't remove files after copy
        -p\tPrint unload list but do not copy or remove files"""
        args = args.lower().strip().split()
        dont_remove = False
        if '-x' in args:
            if self.pc.write_protect:
                log.error("Photo card is write protected. -x not allowed.")
                return
            else:
                dont_remove = True


        unload_list = self.pc.get_unload_list()
        print()

        if len(unload_list) > 0:
            if '-p' in args:

                max_len = 0
                for u in unload_list:
                    max_len = max(max_len, len(u[0]))

                formatter = utils.TextFormatter(
                        (
                            {'width': max_len+2, 'margin' : 2},
                            {'width': 12, 'margin' : 2, 'alignment' : utils.TextFormatter.RIGHT},
                            {'width': 12, 'margin' : 2},
                        )
                    )

                print()
                print(log.bold(formatter.compose(("Name", "Size", "Type"))))

                total = 0
                for u in unload_list:
                     print(formatter.compose(('%s' % u[0], utils.format_bytes(u[1]), '%s/%s' % (u[2], u[3]))))
                     total += u[1]


                print(log.bold("Found %d files to unload, %s" % (len(unload_list), utils.format_bytes(total, True))))
            else:
                print(log.bold("Unloading %d files..." % len(unload_list)))
                total, delta, was_cancelled = self.pc.unload(unload_list, self.cp_status_callback, self.rm_status_callback, dont_remove)
                print(log.bold("\n%s unloaded in %d sec (%d KB/sec)" % (utils.format_bytes(total), delta, (total/1024)/delta)))

        else:
            print("No image, audio, or video files found.")


    def cp_status_callback(self, src, trg, size):
        if size == 1:
            print()
            print(log.bold("Copying %s..." % src))
        else:
            print("\nCopied %s to %s (%s)..." % (src, trg, utils.format_bytes(size)))

    def rm_status_callback(self, src):
        print("Removing %s..." % src)



    def do_rm(self, args):
        """Remove files from photo card."""
        if self.pc.write_protect:
            log.error("Photo card is write protected. rm not allowed.")
            return

        args = args.strip().lower()

        matched_files = self.pc.match_files(args)

        if len(matched_files) == 0:
            print("ERROR: File(s) not found.")
        else:
            for f in matched_files:
                self.pc.rm(f, False)

        self.pc.ls()

    def do_mv(self, args):
        """Move files off photocard"""
        if self.pc.write_protect:
            log.error("Photo card is write protected. mv not allowed.")
            return
        self.do_cp(args, True)

    def do_lpwd(self, args):
        """Print name of local current/working directory."""
        print(os.getcwd())

    def do_lcd(self, args):
        """Change current local working directory."""
        try:
            os.chdir(args.strip())
        except OSError:
            print(log.bold("ERROR: Directory not found."))
        print(os.getcwd())

    def do_pwd(self, args):
        """Print name of photo card current/working directory
        Usage:
        \t>pwd"""
        print(self.pc.pwd())

    def do_cd(self, args):
        """Change current working directory on photo card.
        Note:
        \tYou may only specify one directory level at a time.
        Usage:
        \tcd <directory>
        """
        args = args.lower().strip()

        if args == '..':
            if self.pc.pwd() != '/':
                self.pc.cdup()

        elif args == '.':
            pass

        elif args == '/':
            self.pc.cd('/')

        else:
            matched_dirs = self.pc.match_dirs(args)

            if len(matched_dirs) == 0:
                print("Directory not found")

            elif len(matched_dirs) > 1:
                print("Pattern matches more than one directory")

            else:
                self.pc.cd(matched_dirs[0])

        self.prompt = log.bold("pcard: %s > " % self.pc.pwd())

    def do_cdup(self, args):
        """Change to parent directory."""
        self.do_cd('..')

    #def complete_cd( self, text, line, begidx, endidx ):
    #    print text, line, begidx, endidx
    #    #return "XXX"

    def do_cache(self, args):
        """Display current cache entries, or turn cache on/off.
        Usage:
        \tDisplay: cache
        \tTurn on: cache on
        \tTurn off: cache off
        """
        args = args.strip().lower()

        if args == 'on':
            self.pc.cache_control(True)

        elif args == 'off':
            self.pc.cache_control(False)

        else:
            if self.pc.cache_state():
                cache_info = self.pc.cache_info()

                t = list(cache_info.keys())
                t.sort()
                print()
                for s in t:
                    print("sector %d (%d hits)" % (s, cache_info[s]))

                print(log.bold("Total cache usage: %s (%s maximum)" % (utils.format_bytes(len(t)*512), utils.format_bytes(photocard.MAX_CACHE * 512))))
                print(log.bold("Total cache sectors: %s of %s" % (utils.commafy(len(t)), utils.commafy(photocard.MAX_CACHE))))
            else:
                print("Cache is off.")

    def do_sector(self, args):
        """Display sector data.
        Usage:
        \tsector <sector num>
        """
        args = args.strip().lower()
        cached = False
        try:
            sector = int(args)
        except ValueError:
            print("Sector must be specified as a number")
            return

        if self.pc.cache_check(sector) > 0:
            print("Cached sector")

        print(repr(self.pc.sector(sector)))


    def do_tree(self, args):
        """Display photo card directory tree."""
        tree = self.pc.tree()
        print()
        self.print_tree(tree)

    def print_tree(self, tree, level=0):
        for d in tree:
            if type(tree[d]) == type({}):
                print(''.join([' '*level*4, d, '/']))
                self.print_tree(tree[d], level+1)


    def do_reset(self, args):
        """Reset the cache."""
        self.pc.cache_reset()


    def do_card(self, args):
        """Print info about photocard."""
        print()
        print("Device URI = %s" % self.pc.device.device_uri)
        print("Model = %s" % self.pc.device.model_ui)
        print("Working dir = %s" % self.pc.pwd())
        disk_info = self.pc.info()
        print("OEM ID = %s" % disk_info[0])
        print("Bytes/sector = %d" % disk_info[1])
        print("Sectors/cluster = %d" % disk_info[2])
        print("Reserved sectors = %d" % disk_info[3])
        print("Root entries = %d" % disk_info[4])
        print("Sectors/FAT = %d" % disk_info[5])
        print("Volume label = %s" % disk_info[6])
        print("System ID = %s" % disk_info[7])
        print("Write protected = %d" % disk_info[8])
        print("Cached sectors = %s" % utils.commafy(len(self.pc.cache_info())))


    def do_display(self, args):
        """Display an image with ImageMagick.
        Usage:
        \tdisplay <filename>"""
        args = args.strip().lower()
        matched_files = self.pc.match_files(args)

        if len(matched_files) == 1:

            typ = self.pc.classify_file(args).split('/')[0]

            if typ == 'image':
                fd, temp_name = utils.make_temp_file()
                self.pc.cp(args, temp_name)
                os.system('display %s' % temp_name)
                os.remove(temp_name)

            else:
                print("File is not an image.")

        elif len(matched_files) == 0:
            print("File not found.")

        else:
            print("Only one file at a time may be specified for display.")

    def do_show(self, args):
        """Synonym for the display command."""
        self.do_display(args)

    def do_thumbnail(self, args):
        """Display an embedded thumbnail image with ImageMagick.
        Note:
        \tOnly works with JPEG/JFIF images with embedded JPEG/TIFF thumbnails
        Usage:
        \tthumbnail <filename>"""
        args = args.strip().lower()
        matched_files = self.pc.match_files(args)

        if len(matched_files) == 1:
            typ, subtyp = self.pc.classify_file(args).split('/')

            if typ == 'image' and subtyp in ('jpeg', 'tiff'):
                exif_info = self.pc.get_exif(args)

                dir_name, file_name=os.path.split(args)
                photo_name, photo_ext=os.path.splitext(args)

                if 'JPEGThumbnail' in exif_info:
                    temp_file_fd, temp_file_name = utils.make_temp_file()
                    open(temp_file_name, 'wb').write(exif_info['JPEGThumbnail'])
                    os.system('display %s' % temp_file_name)
                    os.remove(temp_file_name)

                elif 'TIFFThumbnail' in exif_info:
                    temp_file_fd, temp_file_name = utils.make_temp_file()
                    open(temp_file_name, 'wb').write(exif_info['TIFFThumbnail'])
                    os.system('display %s' % temp_file_name)
                    os.remove(temp_file_name)

                else:
                    print("No thumbnail found.")

            else:
                print("Incorrect file type for thumbnail.")

        elif len(matched_files) == 0:
            print("File not found.")
        else:
            print("Only one file at a time may be specified for thumbnail display.")

    def do_thumb(self, args):
        """Synonym for the thumbnail command."""
        self.do_thumbnail(args)

    def do_exif(self, args):
        """Display EXIF info for file.
        Usage:
        \texif <filename>"""
        args = args.strip().lower()
        matched_files = self.pc.match_files(args)

        if len(matched_files) == 1:
            typ, subtyp = self.pc.classify_file(args).split('/')
            #print "'%s' '%s'" % (typ, subtyp)

            if typ == 'image' and subtyp in ('jpeg', 'tiff'):
                exif_info = self.pc.get_exif(args)

                formatter = utils.TextFormatter(
                        (
                            {'width': 40, 'margin' : 2},
                            {'width': 40, 'margin' : 2},
                        )
                    )

                print()
                print(log.bold(formatter.compose(("Tag", "Value"))))

                ee = list(exif_info.keys())
                ee.sort()
                for e in ee:
                    if e not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename'):
                        #if e != 'EXIF MakerNote':
                        print(formatter.compose((e, '%s' % exif_info[e])))
                        #else:
                        #    print formatter.compose( ( e, ''.join( [ chr(x) for x in exif_info[e].values if chr(x) in string.printable ] ) ) )
            else:
                print("Incorrect file type for thumbnail.")

        elif len(matched_files) == 0:
            print("File not found.")
        else:
            print("Only one file at a time may be specified for thumbnail display.")

    def do_info(self, args):
        """Synonym for the exif command."""
        self.do_exif(args)

    def do_about(self, args):
        utils.log_title(__title__, __version__)


def status_callback(src, trg, size):
    if size == 1:
        print()
        print(log.bold("Copying %s..." % src))
    else:
        print("\nCopied %s to %s (%s)..." % (src, trg, utils.format_bytes(size)))



mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                    (GUI_MODE, INTERACTIVE_MODE, NON_INTERACTIVE_MODE),
                    (UI_TOOLKIT_QT3,), False, False, True)

mod.setUsage(module.USAGE_FLAG_DEVICE_ARGS,
    extra_options=[("Output directory:", "-o<dir> or --output=<dir> (Defaults to current directory)(Only used for non-GUI modes)", "option", False)],
    see_also_list=['hp-toolbox'])

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts('o', ['output='])

from pcard import photocard

output_dir = os.getcwd()

for o, a in opts:
    if o in ('-o', '--output'):
        output_dir = a

if mode == GUI_MODE:
    if not utils.canEnterGUIMode():
        mode = INTERACTIVE_MODE

if mode == GUI_MODE:
    if ui_toolkit == 'qt4':
        log.error("%s does not support Qt4. Please use Qt3 or run in -i or -n modes.")
        sys.exit(1)

if mode in (INTERACTIVE_MODE, NON_INTERACTIVE_MODE):
    try:
        device_uri = mod.getDeviceUri(device_uri, printer_name,
            filter={'pcard-type' : (operator.eq, 1)})

        if not device_uri:
            sys.exit(1)
        log.info("Using device : %s\n" % device_uri)
        try:
            pc = photocard.PhotoCard( None, device_uri, printer_name )
        except Error as e:
            log.error("Unable to start photocard session: %s" % e.msg)
            sys.exit(1)

        pc.set_callback(update_spinner)

        try:
            pc.mount()
        except Error:
            log.error("Unable to mount photo card on device. Check that device is powered on and photo card is correctly inserted.")
            pc.umount()
            # TODO:
            #pc.device.sendEvent(EVENT_PCARD_UNABLE_TO_MOUNT, typ='error')
            sys.exit(1)

        log.info(log.bold("\nPhotocard on device %s mounted" % pc.device.device_uri))
        log.info(log.bold("DO NOT REMOVE PHOTO CARD UNTIL YOU EXIT THIS PROGRAM"))

        output_dir = os.path.realpath(os.path.normpath(os.path.expanduser(output_dir)))

        try:
            os.chdir(output_dir)
        except OSError:
            print(log.bold("ERROR: Output directory %s not found." % output_dir))
            sys.exit(1)


        if mode == INTERACTIVE_MODE: # INTERACTIVE_MODE
            console = Console(pc)
            try:
                try:
                    console . cmdloop()
                except KeyboardInterrupt:
                    log.error("Aborted.")
                except Exception as e:
                    log.error("An error occured: %s" % e)
            finally:
                pc.umount()

            # TODO:
            #pc.device.sendEvent(EVENT_END_PCARD_JOB)


        else: # NON_INTERACTIVE_MODE
            print("Output directory is %s" % os.getcwd())
            try:
                unload_list = pc.get_unload_list()
                print()

                if len(unload_list) > 0:

                    max_len = 0
                    for u in unload_list:
                        max_len = max(max_len, len(u[0]))

                    formatter = utils.TextFormatter(
                            (
                                {'width': max_len+2, 'margin' : 2},
                                {'width': 12, 'margin' : 2, 'alignment' : utils.TextFormatter.RIGHT},
                                {'width': 12, 'margin' : 2},
                            )
                        )

                    print()
                    print(log.bold(formatter.compose(("Name", "Size", "Type"))))

                    total = 0
                    for u in unload_list:
                         print(formatter.compose(('%s' % u[0], utils.format_bytes(u[1]), '%s/%s' % (u[2], u[3]))))
                         total += u[1]


                    print(log.bold("Found %d files to unload, %s\n" % (len(unload_list), utils.format_bytes(total, True))))
                    print(log.bold("Unloading files...\n"))
                    total, delta, was_cancelled = pc.unload(unload_list, status_callback, None, True)
                    print(log.bold("\n%s unloaded in %d sec (%d KB/sec)" % (utils.format_bytes(total), delta, (total/1024)/delta)))


            finally:
                pc.umount()

    except KeyboardInterrupt:
        log.error("User exit")


else: # GUI_MODE (qt3 only)
    try:
        from qt import *
        from ui import unloadform
    except ImportError:
        log.error("Unable to load Qt3 support. Is it installed?")
        sys.exit(1)

    app = QApplication(sys.argv)
    QObject.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))

    if loc is None:
        loc = user_conf.get('ui', 'loc', 'system')
        if loc.lower() == 'system':
            loc = str(QTextCodec.locale())
            log.debug("Using system locale: %s" % loc)

    if loc.lower() != 'c':
        e = 'utf8'
        try:
            l, x = loc.split('.')
            loc = '.'.join([l, e])
        except ValueError:
            l = loc
            loc = '.'.join([loc, e])

        log.debug("Trying to load .qm file for %s locale." % loc)
        trans = QTranslator(None)

        qm_file = 'hplip_%s.qm' % l
        log.debug("Name of .qm file: %s" % qm_file)
        loaded = trans.load(qm_file, prop.localization_dir)

        if loaded:
            app.installTranslator(trans)
        else:
            loc = 'c'

    if loc == 'c':
        log.debug("Using default 'C' locale")
    else:
        log.debug("Using locale: %s" % loc)
        QLocale.setDefault(QLocale(loc))
        prop.locale = loc
        try:
            locale.setlocale(locale.LC_ALL, locale.normalize(loc))
        except locale.Error:
            pass

    try:
        w = unloadform.UnloadForm(['cups'], device_uri, printer_name)
    except Error:
        log.error("Unable to connect to HPLIP I/O. Please (re)start HPLIP and try again.")
        sys.exit(1)

    app.setMainWidget(w)
    w.show()

    app.exec_loop()

log.info("")
log.info("Done.")
