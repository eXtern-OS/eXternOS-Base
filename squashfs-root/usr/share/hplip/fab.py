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

__version__ = '6.0'
__title__ = "Fax Address Book"
__mod__ = 'hp-fab'
__doc__ = "A simple fax address book for HPLIP."

# Std Lib
import cmd
import getopt
import os


# Local
from base.g import *
from base import utils, tui, module
from base.sixext.moves import input

try:
    from importlib import import_module
except ImportError as e:
    log.debug(e)
    from base.utils import dyn_import_mod as import_module


# Console class (from ASPN Python Cookbook)
# Author:   James Thiele
# Date:     27 April 2004
# Version:  1.0
# Location: http://www.eskimo.com/~jet/python/examples/cmd/
# Copyright (c) 2004, James Thiele
class Console(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.intro  = "Type 'help' for a list of commands. Type 'exit' or 'quit' to quit."
        self.db =  fax.FaxAddressBook() # database instance
        self.prompt = log.bold("hp-fab > ")

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

        self.do_list('')

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
        log.error("Unrecognized command. Use 'help' to list commands.")

    def get_nickname(self, args, fail_if_match=True, alt_text=False):
        if not args:
            while True:
                if alt_text:
                    nickname = input(log.bold("Enter the name to add to the group (<enter>=done*, c=cancel) ? ")).strip()
                else:
                    nickname = input(log.bold("Enter name (c=cancel) ? ")).strip()

                if nickname.lower() == 'c':
                    print(log.red("Canceled"))
                    return ''

                if not nickname:
                    if alt_text:
                        return ''
                    else:
                        log.error("Name must not be blank.")
                        continue


                if fail_if_match:
                    if self.db.get(nickname) is not None:
                        log.error("Name already exists. Please choose a different name.")
                        continue

                else:
                    if self.db.get(nickname) is None:
                        log.error("Name not found. Please enter a different name.")
                        continue

                break

        else:
            nickname = args.strip()

            if fail_if_match:
                if self.db.get(nickname) is not None:
                    log.error("Name already exists. Please choose a different name.")
                    return ''

            else:
                if self.db.get(nickname) is None:
                    log.error("Name not found. Please enter a different name.")
                    return ''

        return nickname


    def get_groupname(self, args, fail_if_match=True, alt_text=False):
        all_groups = self.db.get_all_groups()

        if not args:
            while True:
                if alt_text:
                    groupname = input(log.bold("Enter the group to join (<enter>=done*, c=cancel) ? ")).strip()
                else:
                    groupname = input(log.bold("Enter the group (c=cancel) ? ")).strip()


                if groupname.lower() == 'c':
                    print(log.red("Canceled"))
                    return ''

                if not groupname:
                    if alt_text:
                        return ''
                    else:
                        log.error("The group name must not be blank.")
                        continue

                if groupname == 'All':
                    print("Cannot specify group 'All'. Please choose a different group.")
                    return ''

                if fail_if_match:
                    if groupname in all_groups:
                        log.error("Group already exists. Please choose a different group.")
                        continue

                else:
                    if groupname not in all_groups:
                        log.error("Group not found. Please enter a different group.")
                        continue

                break

        else:
            groupname = args.strip()

            if fail_if_match:
                if groupname in all_groups:
                    log.error("Group already exists. Please choose a different group.")
                    return ''

            else:
                if groupname not in all_groups:
                    log.error("Group not found. Please enter a different group.")
                    return ''

        return groupname

    def do_list(self, args):
        """
        List names and/or groups.
        list [names|groups|all|]
        dir [names|groups|all|]
        """

        if args:
            scope = args.strip().split()[0]

            if args.startswith('nam'):
                self.do_names('')
                return

            elif args.startswith('gro'):
                self.do_groups('')
                return

        self.do_names('')
        self.do_groups('')

    do_dir = do_list

    def do_names(self, args):
        """
        List names.
        names
        """
        all_entries = self.db.get_all_records()
        log.debug(all_entries)

        print(log.bold("\nNames:\n"))
        if len(all_entries) > 0:

            f = tui.Formatter()
            f.header = ("Name", "Fax Number", "Notes", "Member of Group(s)")
            for name, e in list(all_entries.items()):
                if not name.startswith('__'):
                    f.add((name, e['fax'], e['notes'], ', '.join(e['groups'])))

            f.output()

        else:
            print("(None)")

        print()

    def do_groups(self, args):
        """
        List groups.
        groups
        """
        all_groups = self.db.get_all_groups()
        log.debug(all_groups)

        print(log.bold("\nGroups:\n"))
        if len(all_groups):

            f = tui.Formatter()
            f.header = ("Group", "Members")
            for group in all_groups:
                f.add((group, ', '.join([x for x in self.db.group_members(group) if not x.startswith('__')])))
            f.output()

        else:
            print("(None)")

        print()


    def do_edit(self, args):
        """
        Edit an name.
        edit [name]
        modify [name]
        """
        nickname = self.get_nickname(args, fail_if_match=False)
        if not nickname: return

        e = self.db.get(nickname)
        log.debug(e)

        print(log.bold("\nEdit/modify information for %s:\n" % nickname))

#        save_title = e['title']
#        title = raw_input(log.bold("Title (<enter>='%s', c=cancel) ? " % save_title)).strip()
#
#        if title.lower() == 'c':
#            print log.red("Canceled")
#            return
#
#        if not title:
#            title = save_title
#
#        save_firstname = e['firstname']
#        firstname = raw_input(log.bold("First name (<enter>='%s', c=cancel) ? " % save_firstname)).strip()
#
#        if firstname.lower() == 'c':
#            print log.red("Canceled")
#            return
#
#        if not firstname:
#            firstname = save_firstname
#
#        save_lastname = e['lastname']
#        lastname = raw_input(log.bold("Last name (<enter>='%s', c=cancel) ? " % save_lastname)).strip()
#
#        if lastname.lower() == 'c':
#            print log.red("Canceled")
#            return
#
#        if not lastname:
#            lastname = save_lastname

        lastname = ''
        firstname = ''
        title = ''

        save_faxnum = e['fax']
        while True:
            faxnum = input(log.bold("Fax Number (<enter>='%s', c=cancel) ? " % save_faxnum)).strip()

            if faxnum.lower() == 'c':
                print(log.red("Canceled"))
                return

            if not faxnum and not save_faxnum:
                log.error("Fax number must not be empty.")
                continue

            if not faxnum:
                faxnum = save_faxnum

            ok = True
            for c in faxnum:
                if c not in '0123456789-(+) *#':
                    log.error("Invalid characters in fax number. Fax number may only contain '0123456789-(+) '")
                    ok = False
                    break


            if ok: break

        save_notes = e['notes']
        notes = input(log.bold("Notes (<enter>='%s', c=cancel) ? " % save_notes)).strip()

        if notes.lower() == 'c':
            print(log.red("Canceled"))
            return

        if not notes:
            notes = save_notes

        if e['groups']:
            print("\nLeave or Stay in a Group:\n")

        new_groups = []
        for g in e['groups']:
            if g == 'All':
                continue

            ok, ans = tui.enter_yes_no("Stay in group %s " % g,
                choice_prompt="(y=yes* (stay), n=no (leave), c=cancel) ? ")

            if not ok:
                print(log.red("Canceled"))
                return

            if ans:
                new_groups.append(g)

        print("\nJoin New Group(s):\n")

        while True:
            add_group = self.get_groupname('', fail_if_match=False, alt_text=True)

            if add_group.lower() == 'c':
                print(log.red("Canceled"))
                return

            if not add_group:
                break

            all_groups = self.db.get_all_groups()

            if add_group not in all_groups:
                log.warn("Group not found.")
                ok, ans = tui.enter_yes_no("Is this a new group",
                    choice_prompt="(y=yes* (new), n=no, c=cancel) ? ")

                if not ok:
                    print(log.red("Canceled"))
                    return

                if not ans:
                    continue

            if add_group in e['groups']:
                log.error("Group already specified. Choose a different group name or press <enter> to continue.")
                continue

            new_groups.append(add_group)

        self.db.set(nickname, title, firstname, lastname, faxnum, new_groups, notes)
        self.do_show(nickname)

        print()

    do_modify = do_edit


    def do_editgrp(self, args):
        """
        Edit a group.
        editgrp [group]
        modifygrp [group]
        """
        group = self.get_groupname(args, fail_if_match=False)
        if not group: return

        old_entries = self.db.group_members(group)

        new_entries = []

        print("\nExisting Names in Group:\n")

        for e in old_entries:
            if not e.startswith('__'):
                ok, ans = tui.enter_yes_no("Should '%s' stay in this group " % e,
                    choice_prompt="(y=yes* (stay), n=no (leave), c=cancel) ? ")
            else:
                continue

            if not ok:
                print(log.red("Canceled"))
                return

            if ans:
                new_entries.append(e)

        print("\nAdd New Names to Group:\n")

        while True:
            nickname = self.get_nickname('', fail_if_match=False, alt_text=True)

            if nickname.lower() == 'c':
                print(log.red("Canceled"))
                return

            if not nickname.lower():
                break

            new_entries.append(nickname)

        self.db.update_groups(group, new_entries)

        print()

    do_modifygrp = do_editgrp


    def do_add(self, args):
        """
        Add an name.
        add [name]
        new [name]
        """
        nickname = self.get_nickname(args, fail_if_match=True)
        if not nickname: return

        print(log.bold("\nEnter information for %s:\n" % nickname))

#        title = raw_input(log.bold("Title (c=cancel) ? ")).strip()
#
#        if title.lower() == 'c':
#            print log.red("Canceled")
#            return
#
#        firstname = raw_input(log.bold("First name (c=cancel) ? ")).strip()
#
#        if firstname.lower() == 'c':
#            print log.red("Canceled")
#            return
#
#        lastname = raw_input(log.bold("Last name (c=cancel) ? ")).strip()
#
#        if lastname.lower() == 'c':
#            print log.red("Canceled")
#            return

        title = ''
        firstname = ''
        lastname = ''

        while True:
            faxnum = input(log.bold("Fax Number (c=cancel) ? ")).strip()

            if faxnum.lower() == 'c':
                print(log.red("Canceled"))
                return

            if not faxnum:
                log.error("Fax number must not be empty.")
                continue

            ok = True
            for c in faxnum:
                if c not in '0123456789-(+) *#':
                    log.error("Invalid characters in fax number. Fax number may only contain '0123456789-(+) *#'")
                    ok = False
                    break


            if ok: break

        notes = input(log.bold("Notes (c=cancel) ? ")).strip()

        if notes.strip().lower() == 'c':
            print(log.red("Canceled"))
            return

        groups = []
        all_groups = self.db.get_all_groups()
        while True:
            add_group = input(log.bold("Member of group (<enter>=done*, c=cancel) ? " )).strip()

            if add_group.lower() == 'c':
                print(log.red("Canceled"))
                return

            if not add_group:
                break

            if add_group == 'All':
                print(log.red("Cannot specify 'All'."))
                continue

            if add_group not in all_groups:
                log.warn("Group not found.")

                while True:
                    user_input = input(log.bold("Is this a new group (y=yes*, n=no) ? ")).lower().strip()

                    if user_input not in ['', 'n', 'y']:
                        log.error("Please enter 'y', 'n' or press <enter> for 'yes'.")
                        continue

                    break

                if user_input == 'n':
                    continue

            if add_group in groups:
                log.error("Group already specified. Choose a different group name or press <enter> to continue.")
                continue

            groups.append(add_group)

        groups.append('All')

        self.db.set(nickname, title, firstname, lastname, faxnum, groups, notes)
        self.do_show(nickname)


    do_new = do_add


    def do_addgrp(self, args):
        """
        Add a group.
        addgrp [group]
        newgrp [group]
        """
        group = self.get_groupname(args, fail_if_match=True)
        if not group: return

        entries = []
        while True:
            nickname = self.get_nickname('', fail_if_match=False, alt_text=True)

            if nickname.lower() == 'c':
                print(log.red("Canceled"))
                return

            if not nickname.lower():
                break

            entries.append(nickname)

        self.db.update_groups(group, entries)

        print()

    do_newgrp = do_addgrp


    def do_view(self, args):
        """
        View all name data.
        view
        """
        all_entries = self.db.get_all_records()
        log.debug(all_entries)

        print(log.bold("\nView all Data:\n"))
        if len(all_entries) > 0:

            f = tui.Formatter()
            f.header = ("Name", "Fax", "Notes", "Member of Group(s)")

            for name, e in list(all_entries.items()):
                if not name.startswith('__'):
                    f.add((name, e['fax'], e['notes'], ', '.join(e['groups'])))

            f.output()

        print()



    def do_show(self, args):
        """
        Show a name (all details).
        show [name]
        details [name]
        """
        name = self.get_nickname(args, fail_if_match=False)
        if not name: return

        e = self.db.get(name)
        if e:
            f = tui.Formatter()
            f.header = ("Key", "Value")
            f.add(("Name:", name))
            #f.add(("Title:", e['title']))
            #f.add(("First Name:", e['firstname']))
            #f.add(("Last Name:", e['lastname']))
            f.add(("Fax Number:", e['fax']))
            f.add(("Notes:", e['notes']))
            f.add(("Member of Group(s):", ', '.join(e['groups'])))

            f.output()

        else:
            log.error("Name not found. Use the 'names' command to view all names.")

        print()

    do_details = do_show

    def do_rm(self, args):
        """
        Remove a name.
        rm [name]
        del [name]
        """
        nickname = self.get_nickname(args, fail_if_match=False)
        if not nickname: return

        self.db.delete(nickname)

        print()

    do_del = do_rm

    def do_rmgrp(self, args):
        """
        Remove a group.
        rmgrp [group]
        delgrp [group]
        """
        group = self.get_groupname(args, fail_if_match=False)
        if not group: return

        self.db.delete_group(group)

        print()

    do_delgrp = do_rmgrp


    def do_about(self, args):
        """About fab."""
        utils.log_title(__title__, __version__)

    def do_import(self, args):
        """
        Import LDIF
        import <filename> [type]
        [type] = vcf|ldif|auto
        """
        args = args.strip().split()

        if not args:
            log.error("You must specify a filename to import from.")
            return

        filename = args[0]

        if len(args) > 1:
            typ = args[1].lower()
        else:
            typ = 'auto'

        if typ not in ('auto', 'ldif', 'vcf', 'vcard'):
            log.error("Invalid type: %s" % typ)
            return

        if not os.path.exists(filename):
            log.error("File %s not found." % filename)
            return

        if typ == 'auto':
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.vcf':
                typ = 'vcf'
            elif ext == '.ldif':
                typ = 'ldif'
            else:
                head = open(filename, 'r').read(1024).lower()
                if 'begin:vcard' in head:
                    typ = 'vcf'
                else:
                    typ = 'ldif'

        if typ == 'ldif':
            print("Importing from LDIF file %s..." % filename)
            ok, error_str = self.db.import_ldif(filename)

        elif typ in ('vcard', 'vcf'):
            print("Importing from VCF file %s..." % filename)
            ok, error_str = self.db.import_vcard(filename)

        if not ok:
            log.error(error_str)
        else:
            self.do_list('')

        print()




mod = module.Module(__mod__, __title__, __version__, __doc__, None,
                    (GUI_MODE, INTERACTIVE_MODE),
                    (UI_TOOLKIT_QT3, UI_TOOLKIT_QT4, UI_TOOLKIT_QT5))

mod.setUsage(module.USAGE_FLAG_NONE)

opts, device_uri, printer_name, mode, ui_toolkit, loc = \
    mod.parseStdOpts(handle_device_printer=False)

if ui_toolkit == 'qt3':
    if not utils.canEnterGUIMode():
        log.error("%s GUI mode requires GUI support (try running with --qt4). Entering interactive mode." % __mod__)
        mode = INTERACTIVE_MODE
else:
    if not utils.canEnterGUIMode4():
        log.error("%s GUI mode requires GUI support (try running with --qt3). Entering interactive mode." % __mod__)
        mode = INTERACTIVE_MODE


if mode == GUI_MODE:
    if ui_toolkit == 'qt3':
        log.set_module("hp-fab(qt3)")
        try:
            from qt import *
            from ui.faxaddrbookform import FaxAddrBookForm
        except ImportError:
            log.error("Unable to load Qt3 support. Is it installed?")
            sys.exit(1)

        app = None
        addrbook = None
        # create the main application object
        app = QApplication(sys.argv)

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

        addrbook = FaxAddrBookForm()
        addrbook.show()
        app.setMainWidget(addrbook)

        try:
            log.debug("Starting GUI loop...")
            app.exec_loop()
        except KeyboardInterrupt:
            pass

        sys.exit(0)

    else: # qt4

        QApplication, ui_package = utils.import_dialog(ui_toolkit)
        ui = import_module(ui_package + ".fabwindow")


        log.set_module("hp-fab(qt4)")

        if 1:
            app = QApplication(sys.argv)
            fab = ui.FABWindow(None)
            fab.show()

            try:
                log.debug("Starting GUI loop...")
                app.exec_()
            except KeyboardInterrupt:
                sys.exit(0)



else: # INTERACTIVE_MODE
    try:
        from fax import fax
    except ImportError:
        # This can fail on Python < 2.3 due to the datetime module
        log.error("Fax address book disabled - Python 2.3+ required.")
        sys.exit(1)

    console = Console()

    try:
        console.cmdloop()
    except KeyboardInterrupt:
        log.error("User exit.")

    log.info("")
    log.info("Done.")

