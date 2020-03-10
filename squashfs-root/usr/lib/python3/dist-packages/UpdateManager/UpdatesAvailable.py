# UpdatesAvailable.py
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-
#
#  Copyright (c) 2004-2013 Canonical
#                2004 Michiel Sikkes
#                2005 Martin Willemoes Hansen
#                2010 Mohamed Amine IL Idrissi
#
#  Author: Michiel Sikkes <michiel@eyesopened.nl>
#          Michael Vogt <mvo@debian.org>
#          Martin Willemoes Hansen <mwh@sysrq.dk>
#          Mohamed Amine IL Idrissi <ilidrissiamine@gmail.com>
#          Alex Launi <alex.launi@canonical.com>
#          Michael Terry <michael.terry@canonical.com>
#          Dylan McCall <dylanmccall@ubuntu.com>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

from __future__ import absolute_import, print_function

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import Pango

import warnings
warnings.filterwarnings("ignore", "Accessed deprecated property",
                        DeprecationWarning)

import apt_pkg

import os
import re
import logging
import time
import threading

from gettext import gettext as _
from gettext import ngettext

from .Core.utils import humanize_size
from .Core.AlertWatcher import AlertWatcher
from .Core.UpdateList import UpdateSystemGroup
from .Dialogs import InternalDialog

from DistUpgrade.DistUpgradeCache import NotEnoughFreeSpaceError

from .ChangelogViewer import ChangelogViewer
from .UnitySupport import UnitySupport


#import pdb

# FIXME:
# - kill "all_changes" and move the changes into the "Update" class
# - screen reader does not read update toggle state
# - screen reader does not say "Downloaded" for downloaded updates

# list constants
(LIST_NAME, LIST_UPDATE_DATA, LIST_SIZE, LIST_TOGGLE_ACTIVE) = range(4)

# NetworkManager enums
from .Core.roam import NetworkManagerHelper


class UpdateData():
    def __init__(self, groups, group, item):
        self.groups = groups if groups else []
        self.group = group
        self.item = item


class CellAreaPackage(Gtk.CellAreaBox):
    """This CellArea lays our package cells side by side, without allocating
       width for a cell if it isn't present (like icons for header labels).
       We assume that the last cell should be expanded to fill remaining space,
       and other cells have a fixed width.
    """

    def __init__(self, indent_toplevel=False):
        Gtk.CellAreaBox.__init__(self)
        self.indent_toplevel = indent_toplevel
        self.column = None
        self.cached_cell_size = {}

    def do_foreach_alloc(self, context, widget, cell_area_in, bg_area_in,
                         callback):
        cells = []

        def gather(cell, data):
            cells.append(cell)

        self.foreach(gather, None)

        cell_is_hidden = {}

        # Record the space required by each cell
        for cell_number, cell in enumerate(cells):
            # Detect if this cell should be allocated space
            if isinstance(cell, Gtk.CellRendererPixbuf):
                gicon = cell.get_property("gicon")
                hide_cell = gicon is None
            else:
                hide_cell = False
            cell_is_hidden[cell_number] = hide_cell

            if not hide_cell and cell_number not in self.cached_cell_size:
                min_size, natural_size = cell.get_preferred_width(widget)
                self.cached_cell_size[cell_number] = natural_size

        cell_area = cell_area_in.copy()
        bg_area = bg_area_in.copy()
        spacing = self.get_property("spacing")
        cell_start = self.get_cell_start(widget)
        orig_end = cell_area.width + cell_area.x
        cur_path = self.get_current_path_string()
        depth = Gtk.TreePath.new_from_string(cur_path).get_depth()

        # And finally, start handling each cell
        extra_cell_width = 0
        cell_area.x = cell_start
        cell_area.width = 0

        last_cell_number = len(cells) - 1
        for cell_number, cell in enumerate(cells):
            is_last_cell = cell_number == last_cell_number
            cell_size = self.cached_cell_size.get(cell_number, 0)

            if cell_area.width > 0 and extra_cell_width == 0:
                cell_area.x += cell_area.width + spacing

            if cell_number == 0:
                # The first cell is affected by its depth in the tree
                if not cell_is_hidden[1] and self.indent_toplevel:
                    # if not a header, align with header rows
                    depth += 1
                if depth > 1:
                    indent = max(0, depth - 1)
                    indent_size = cell_size * indent
                    if depth == 2:
                        indent_extra = spacing
                    elif depth == 3:
                        indent_extra = spacing + 1
                    else:
                        indent_extra = spacing * indent
                    cell_area.x += indent_size + indent_extra

            if is_last_cell:
                cell_size = max(cell_size, orig_end - cell_area.x)
            if not cell_is_hidden[cell_number]:
                cell_area.width = cell_size + extra_cell_width
                extra_cell_width = 0
            else:
                cell_area.width = 0
                extra_cell_width = cell_size + spacing

            if callback(cell, cell_area.copy(), bg_area.copy()):
                return

    def do_event(self, context, widget, event, cell_area, flags):
        # This override is just to trick our parent implementation into
        # allowing clicks on toggle cells when they are where the expanders
        # usually are.  It doesn't expect that, so we expand the cell_area
        # here to be equivalent to bg_area.
        cell_start = self.get_cell_start(widget)
        cell_area.width = cell_area.width + cell_area.x - cell_start
        cell_area.x = cell_start
        return Gtk.CellAreaBox.do_event(self, context, widget, event,
                                        cell_area, flags)

    def get_cell_start(self, widget):
        if not self.column:
            return 0
        else:
            val = GObject.Value()
            val.init(int)
            widget.style_get_property("horizontal-separator", val)
            h_sep = val.get_int()
            widget.style_get_property("grid-line-width", val)
            line_width = val.get_int()
            cell_start = self.column.get_x_offset() - h_sep - line_width
            if not self.indent_toplevel:  # i.e. if no headers
                widget.style_get_property("expander-size", val)
                spacing = self.get_property("spacing")
                # Hardcode 4 because GTK+ hardcodes 4 internally
                cell_start = cell_start + val.get_int() + 4 + spacing
            return cell_start


class UpdatesAvailable(InternalDialog):
    APP_INSTALL_ICONS_PATH = "/usr/share/app-install/icons"

    def __init__(self, window_main, header=None, desc=None,
                 need_reboot=False):
        InternalDialog.__init__(self, window_main)

        self.window_main = window_main
        self.datadir = window_main.datadir
        self.cache = window_main.cache

        self.custom_header = header
        self.custom_desc = desc
        self.need_reboot = need_reboot

        content_ui_path = os.path.join(self.datadir,
                                       "gtkbuilder/UpdateManager.ui")
        self._load_ui(content_ui_path, "pane_updates_available")
        self.set_content_widget(self.pane_updates_available)

        self.dl_size = 0
        self.connected = True

        # Used for inhibiting power management
        self.sleep_cookie = None

        self.settings = Gio.Settings.new("com.ubuntu.update-manager")

        # Special icon theme for looking up app-install-data icons
        self.app_icons = Gtk.IconTheme.get_default()
        self.app_icons.append_search_path(self.APP_INSTALL_ICONS_PATH)

        # Create Unity launcher quicklist
        # FIXME: instead of passing parent we really should just send signals
        self.unity = UnitySupport(parent=self)

        # setup the help viewer and disable the help button if there
        # is no viewer available
        #self.help_viewer = HelpViewer("update-manager")
        #if self.help_viewer.check() == False:
        #    self.button_help.set_sensitive(False)

        self.add_settings_button()
        self.button_close = self.add_button(Gtk.STOCK_CANCEL,
                                            self.window_main.close)
        self.button_install = self.add_button(_("Install Now"),
                                              self.on_button_install_clicked)
        self.focus_button = self.button_install

        # create text view
        self.textview_changes = ChangelogViewer()
        self.textview_changes.show()
        self.scrolledwindow_changes.add(self.textview_changes)
        changes_buffer = self.textview_changes.get_buffer()
        changes_buffer.create_tag("versiontag", weight=Pango.Weight.BOLD)

        # the treeview (move into it's own code!)
        self.store = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT, str, bool)
        self.treeview_update.set_model(None)

        self.image_restart.set_from_gicon(self.get_restart_icon(),
                                          Gtk.IconSize.BUTTON)

        restart_icon_renderer = Gtk.CellRendererPixbuf()
        restart_icon_renderer.set_property("xpad", 4)
        restart_icon_renderer.set_property("ypad", 2)
        restart_icon_renderer.set_property("stock-size", Gtk.IconSize.MENU)
        restart_icon_renderer.set_property("follow-state", True)
        restart_column = Gtk.TreeViewColumn(None, restart_icon_renderer)
        restart_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        restart_column.set_fixed_width(20)
        self.treeview_update.append_column(restart_column)
        restart_column.set_cell_data_func(restart_icon_renderer,
                                          self.restart_icon_renderer_data_func)

        self.pkg_cell_area = CellAreaPackage(False)
        pkg_column = Gtk.TreeViewColumn.new_with_area(self.pkg_cell_area)
        self.pkg_cell_area.column = pkg_column
        pkg_column.set_title(_("Install or remove"))
        pkg_column.set_property("spacing", 4)
        pkg_column.set_expand(True)
        self.treeview_update.append_column(pkg_column)

        pkg_toggle_renderer = Gtk.CellRendererToggle()
        pkg_toggle_renderer.set_property("ypad", 2)
        pkg_toggle_renderer.connect("toggled", self.on_update_toggled)
        pkg_column.pack_start(pkg_toggle_renderer, False)
        pkg_column.add_attribute(pkg_toggle_renderer,
                                 'active', LIST_TOGGLE_ACTIVE)
        pkg_column.set_cell_data_func(pkg_toggle_renderer,
                                      self.pkg_toggle_renderer_data_func)

        pkg_icon_renderer = Gtk.CellRendererPixbuf()
        pkg_icon_renderer.set_property("ypad", 2)
        pkg_icon_renderer.set_property("stock-size", Gtk.IconSize.MENU)
        pkg_column.pack_start(pkg_icon_renderer, False)
        pkg_column.set_cell_data_func(pkg_icon_renderer,
                                      self.pkg_icon_renderer_data_func)

        pkg_label_renderer = Gtk.CellRendererText()
        pkg_label_renderer.set_property("ypad", 2)
        pkg_label_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        pkg_column.pack_start(pkg_label_renderer, True)
        pkg_column.set_cell_data_func(pkg_label_renderer,
                                      self.pkg_label_renderer_data_func)

        size_renderer = Gtk.CellRendererText()
        size_renderer.set_property("xpad", 6)
        size_renderer.set_property("ypad", 0)
        size_renderer.set_property("xalign", 1)
        # 1.0/1.2 == PANGO.Scale.SMALL. Constant is not (yet) introspected.
        size_renderer.set_property("scale", 1.0 / 1.2)
        size_column = Gtk.TreeViewColumn(_("Download"), size_renderer,
                                         text=LIST_SIZE)
        size_column.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        self.treeview_update.append_column(size_column)

        self.treeview_update.set_headers_visible(True)
        self.treeview_update.set_headers_clickable(False)
        self.treeview_update.set_direction(Gtk.TextDirection.LTR)
        self.treeview_update.set_fixed_height_mode(False)
        self.treeview_update.set_expander_column(pkg_column)
        self.treeview_update.set_search_column(LIST_NAME)
        self.treeview_update.connect("button-press-event",
                                     self.on_treeview_button_press)

        # init show version
        self.show_versions = self.settings.get_boolean("show-versions")
        # init summary_before_name
        self.summary_before_name = self.settings.get_boolean(
            "summary-before-name")

        # expander
        self.expander_details.set_expanded(
            self.settings.get_boolean("show-details"))
        self.expander_details.connect("activate", self.pre_activate_details)
        self.expander_details.connect("notify::expanded",
                                      self.activate_details)
        self.expander_desc.connect("notify::expanded", self.activate_desc)

        # If auto-updates are on, change cancel label
        self.notifier_settings = Gio.Settings.new("com.ubuntu.update-notifier")
        self.notifier_settings.connect(
            "changed::auto-launch",
            lambda s, p: self.update_close_button())
        self.update_close_button()

        # Alert watcher
        self.alert_watcher = AlertWatcher()
        self.alert_watcher.connect("network-alert", self._on_network_alert)
        self.alert_watcher.connect("battery-alert", self._on_battery_alert)
        self.alert_watcher.connect("network-3g-alert",
                                   self._on_network_3g_alert)

    def stop(self):
        InternalDialog.stop(self)
        self._save_state()

    def start(self):
        InternalDialog.start(self)
        self.set_update_list(self.window_main.update_list)
        self.alert_watcher.check_alert_state()
        self._restore_state()

    def is_auto_update(self):
        update_days = apt_pkg.config.find_i(
            "APT::Periodic::Update-Package-Lists")
        return update_days >= 1

    def update_close_button(self):
        if self.is_auto_update():
            self.button_close.set_label(_("_Remind Me Later"))
            self.button_close.set_use_stock(False)
            self.button_close.set_use_underline(True)
        else:
            self.button_close.set_label(Gtk.STOCK_CANCEL)
            self.button_close.set_use_stock(True)
            self.button_close.set_use_underline(False)

    def install_all_updates(self, menu, menuitem, data):
        self.select_all_upgrades(None)
        self.on_button_install_clicked()

    def pkg_requires_restart(self, pkg):
        if pkg is None or pkg.candidate is None:
            return False
        restart_condition = pkg.candidate.record.get('Restart-Required')
        return restart_condition == 'system'

    def get_restart_icon(self):
        # FIXME: Non-standard, incorrect icon name (from app category).
        # Theme support for what we want seems to be lacking.
        restart_icon_names = ['view-refresh-symbolic',
                              'system-restart',
                              'system-reboot']
        return Gio.ThemedIcon.new_from_names(restart_icon_names)

    def restart_icon_renderer_data_func(self, cell_layout, renderer, model,
                                        iter, user_data):
        data = model.get_value(iter, LIST_UPDATE_DATA)
        path = model.get_path(iter)

        requires_restart = False
        if data.item and data.item.pkg:
            requires_restart = self.pkg_requires_restart(data.item.pkg)
        elif data.group:
            if not self.treeview_update.row_expanded(path):
                # A package in the group requires restart
                for group_item in data.group.items:
                    if group_item.pkg and self.pkg_requires_restart(
                            group_item.pkg):
                        requires_restart = True
                        break

        if requires_restart:
            gicon = self.get_restart_icon()
        else:
            gicon = None
        renderer.set_property("gicon", gicon)

    def pkg_toggle_renderer_data_func(self, cell_layout, renderer, model,
                                      iter, user_data):
        data = model.get_value(iter, LIST_UPDATE_DATA)

        activatable = False
        inconsistent = False
        if data.item:
            activatable = data.item.pkg.name not in self.list.held_back
            inconsistent = False
        elif data.group:
            activatable = True
            inconsistent = data.group.selection_is_inconsistent()
        elif data.groups:
            activatable = True
            inconsistent = False
            saw_install = None
            for group in data.groups:
                for item in group.items:
                    this_install = item.is_selected()
                    if saw_install is not None and saw_install != this_install:
                        inconsistent = True
                        break
                    saw_install = this_install
                if inconsistent:
                    break

        # The "active" attribute is already set via LIST_TOGGLE_ACTIVE in the
        # tree model, so we don't set it here.
        renderer.set_property("activatable", activatable)
        renderer.set_property("inconsistent", inconsistent)

    def pkg_icon_renderer_data_func(self, cell_layout, renderer, model,
                                    iter, user_data):
        data = model.get_value(iter, LIST_UPDATE_DATA)

        gicon = None
        if data.group:
            gicon = self.get_app_install_icon(data.group.icon)
        elif data.item:
            gicon = self.get_app_install_icon(data.item.icon)

        renderer.set_property("gicon", gicon)

    def get_app_install_icon(self, icon):
        """Any application icon is coming from app-install-data's desktop
           files, which refer to icons from app-install-data's icon directory.
           So we look them up here."""

        if not isinstance(icon, Gio.ThemedIcon):
            return icon  # shouldn't happen

        info = self.app_icons.choose_icon(icon.get_names(), 16,
                                          Gtk.IconLookupFlags.FORCE_SIZE)
        if info is not None:
            return Gio.FileIcon.new(Gio.File.new_for_path(info.get_filename()))
        else:
            return icon  # Assume it's in one of the user's themes

    def pkg_label_renderer_data_func(self, cell_layout, renderer, model,
                                     iter, user_data):
        data = model.get_value(iter, LIST_UPDATE_DATA)
        name = GLib.markup_escape_text(model.get_value(iter, LIST_NAME))

        if data.group:
            markup = name
        elif data.item:
            markup = name
        else:  # header
            markup = "<b>%s</b>" % name

        renderer.set_property("markup", markup)

    def set_changes_buffer(self, changes_buffer, text, name, srcpkg):
        changes_buffer.set_text("")
        lines = text.split("\n")
        if len(lines) == 1:
            changes_buffer.set_text(text)
            return

        for line in lines:
            end_iter = changes_buffer.get_end_iter()
            version_match = re.match(
                r'^%s \((.*)\)(.*)\;.*$' % re.escape(srcpkg), line)
            #bullet_match = re.match("^.*[\*-]", line)
            author_match = re.match("^.*--.*<.*@.*>.*$", line)
            if version_match:
                version = version_match.group(1)
                #upload_archive = version_match.group(2).strip()
                version_text = _("Version %s: \n") % version
                changes_buffer.insert_with_tags_by_name(end_iter, version_text,
                                                        "versiontag")
            elif (author_match):
                pass
            else:
                changes_buffer.insert(end_iter, line + "\n")

    def on_treeview_update_cursor_changed(self, widget):
        path = widget.get_cursor()[0]
        # check if we have a path at all
        if path is None:
            return
        model = widget.get_model()
        iter = model.get_iter(path)

        # set descr
        data = model.get_value(iter, LIST_UPDATE_DATA)
        item = data.item
        if (item is None and data.group is not None and
                data.group.core_item is not None):
            item = data.group.core_item
        if (item is None or item.pkg is None or
                item.pkg.candidate is None or
                item.pkg.candidate.description is None):
            changes_buffer = self.textview_changes.get_buffer()
            changes_buffer.set_text("")
            desc_buffer = self.textview_descr.get_buffer()
            desc_buffer.set_text("")
            self.notebook_details.set_sensitive(False)
            return
        long_desc = item.pkg.candidate.description
        self.notebook_details.set_sensitive(True)
        # do some regular expression magic on the description
        # Add a newline before each bullet
        p = re.compile(r'^(\s|\t)*(\*|0|-)', re.MULTILINE)
        long_desc = p.sub('\n*', long_desc)
        # replace all newlines by spaces
        p = re.compile(r'\n', re.MULTILINE)
        long_desc = p.sub(" ", long_desc)
        # replace all multiple spaces by newlines
        p = re.compile(r'\s\s+', re.MULTILINE)
        long_desc = p.sub("\n", long_desc)

        desc_buffer = self.textview_descr.get_buffer()
        desc_buffer.set_text(long_desc)

        # now do the changelog
        name = item.pkg.name
        if name is None:
            return

        changes_buffer = self.textview_changes.get_buffer()

        # check if we have the changes already and if so, display them
        # (even if currently disconnected)
        if name in self.cache.all_changes:
            changes = self.cache.all_changes[name]
            srcpkg = self.cache[name].candidate.source_name
            self.set_changes_buffer(changes_buffer, changes, name, srcpkg)
        # if not connected, do not even attempt to get the changes
        elif not self.connected:
            changes_buffer.set_text(
                _("No network connection detected, you can not download "
                  "changelog information."))
        # else, get it from the entwork
        elif self.expander_details.get_expanded():
            lock = threading.Lock()
            lock.acquire()
            changelog_thread = threading.Thread(
                target=self.cache.get_news_and_changelog, args=(name, lock))
            changelog_thread.start()
            changes_buffer.set_text("%s\n" %
                                    _("Downloading list of changes..."))
            iter = changes_buffer.get_iter_at_line(1)
            anchor = changes_buffer.create_child_anchor(iter)
            button = Gtk.Button(stock="gtk-cancel")
            self.textview_changes.add_child_at_anchor(button, anchor)
            button.show()
            id = button.connect("clicked",
                                lambda w, lock: lock.release(), lock)
            # wait for the dl-thread
            while lock.locked():
                time.sleep(0.01)
                while Gtk.events_pending():
                    Gtk.main_iteration()
            # download finished (or canceld, or time-out)
            button.hide()
            if button.handler_is_connected(id):
                button.disconnect(id)
        # check if we still are in the right pkg (the download may have taken
        # some time and the user may have clicked on a new pkg)
        now_path = widget.get_cursor()[0]
        if now_path is None:
            return
        if path != now_path:
            return
        # display NEWS.Debian first, then the changelog
        changes = ""
        srcpkg = self.cache[name].candidate.source_name
        if name in self.cache.all_news:
            changes += self.cache.all_news[name]
        if name in self.cache.all_changes:
            changes += self.cache.all_changes[name]
        if changes:
            self.set_changes_buffer(changes_buffer, changes, name, srcpkg)

    def on_treeview_button_press(self, widget, event):
        """
        Show a context menu if a right click was performed on an update entry
        """
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            # need to keep a reference here of menu, otherwise it gets
            # deleted when it goes out of scope and no menu is visible
            # (bug #806949)
            self.menu = menu = Gtk.Menu()
            item_select_none = \
                Gtk.MenuItem.new_with_mnemonic(_("_Deselect All"))
            item_select_none.connect("activate", self.select_none_upgrades)
            menu.append(item_select_none)
            num_updates = self.cache.install_count
            if num_updates == 0:
                item_select_none.set_property("sensitive", False)
            item_select_all = Gtk.MenuItem.new_with_mnemonic(_("Select _All"))
            item_select_all.connect("activate", self.select_all_upgrades)
            menu.append(item_select_all)
            menu.show_all()
            menu.popup_for_device(
                None, None, None, None, None, event.button, event.time)
            menu.show()
            return True

    # we need this for select all/unselect all
    def _toggle_group_headers(self, new_selection_value):
        """ small helper that will set/unset the group headers
        """
        model = self.treeview_update.get_model()
        for row in model:
            data = model.get_value(row.iter, LIST_UPDATE_DATA)
            if data.groups is not None or data.group is not None:
                model.set_value(row.iter, LIST_TOGGLE_ACTIVE,
                                new_selection_value)

    def select_all_upgrades(self, widget):
        """
        Select all updates
        """
        self.setBusy(True)
        self.cache.saveDistUpgrade()
        self._toggle_group_headers(True)
        self.treeview_update.queue_draw()
        self.updates_changed()
        self.setBusy(False)

    def select_none_upgrades(self, widget):
        """
        Select none updates
        """
        self.setBusy(True)
        self.cache.clear()
        self._toggle_group_headers(False)
        self.treeview_update.queue_draw()
        self.updates_changed()
        self.setBusy(False)

    def setBusy(self, flag):
        """ Show a watch cursor if the app is busy for more than 0.3 sec.
        Furthermore provide a loop to handle user interface events """
        if self.window_main.get_window() is None:
            return
        if flag:
            self.window_main.get_window().set_cursor(
                Gdk.Cursor.new(Gdk.CursorType.WATCH))
        else:
            self.window_main.get_window().set_cursor(None)
        while Gtk.events_pending():
            Gtk.main_iteration()

    def _mark_selected_updates(self):
        def foreach_cb(model, path, iter, data):
            data = model.get_value(iter, LIST_UPDATE_DATA)
            active = False
            if data.item:
                active = data.item.is_selected()
            elif data.group:
                active = data.group.packages_are_selected()
            elif data.groups:
                active = any([g.packages_are_selected() for g in data.groups])
            model.set_value(iter, LIST_TOGGLE_ACTIVE, active)
        self.store.foreach(foreach_cb, None)

    def _check_for_required_restart(self):
        requires_restart = False

        def foreach_cb(model, path, iter, data):
            data = model.get_value(iter, LIST_UPDATE_DATA)
            active = model.get_value(iter, LIST_TOGGLE_ACTIVE)
            if not active:
                return
            pkg = None
            if data.item:
                pkg = data.item.pkg
            elif data.group and data.group.core_item:
                pkg = data.group.core_item.pkg
            if pkg and self.pkg_requires_restart(pkg):
                nonlocal requires_restart
                requires_restart = True

        self.store.foreach(foreach_cb, None)
        self.hbox_restart.set_visible(requires_restart)

    def _refresh_updates_count(self):
        self.button_install.set_sensitive(self.cache.install_count)
        try:
            inst_count = self.cache.install_count
            self.dl_size = self.cache.required_download
            download_str = ""
            if self.dl_size != 0:
                download_str = _("%s will be downloaded.") % (
                    humanize_size(self.dl_size))
                self.image_downsize.set_sensitive(True)
                # do not set the buttons to sensitive/insensitive until NM
                # can deal with dialup connections properly
                #if self.alert_watcher.network_state != NM_STATE_CONNECTED:
                #    self.button_install.set_sensitive(False)
                #else:
                #    self.button_install.set_sensitive(True)
                self.button_install.set_sensitive(True)
                self.unity.set_install_menuitem_visible(True)
            else:
                if inst_count > 0:
                    download_str = ngettext(
                        "The update has already been downloaded.",
                        "The updates have already been downloaded.",
                        inst_count)
                    self.button_install.set_sensitive(True)
                    self.unity.set_install_menuitem_visible(True)
                else:
                    download_str = _("There are no updates to install.")
                    self.button_install.set_sensitive(False)
                    self.unity.set_install_menuitem_visible(False)
                self.image_downsize.set_sensitive(False)
            self.label_downsize.set_text(download_str)
            self.hbox_downsize.show()
            self.vbox_alerts.show()
        except SystemError as e:
            print("required_download could not be calculated: %s" % e)
            self.label_downsize.set_markup(_("Unknown download size."))
            self.image_downsize.set_sensitive(False)
            self.hbox_downsize.show()
            self.vbox_alerts.show()

    def updates_changed(self):
        self._mark_selected_updates()
        self._check_for_required_restart()
        self._refresh_updates_count()

    def update_count(self):
        """activate or disable widgets and show dialog texts corresponding to
           the number of available updates"""
        self.updates_changed()

        text_header = None
        text_desc = None

        if self.custom_header is not None:
            text_header = self.custom_header
        if self.custom_desc is not None:
            text_desc = self.custom_desc

        # show different text on first run (UX team suggestion)
        elif self.settings.get_boolean("first-run"):
            flavor = self.window_main.meta_release.flavor_name
            version = self.window_main.meta_release.current_dist_version
            text_header = _("Updated software has been issued since %s %s "
                            "was released. Do you want to install "
                            "it now?") % (flavor, version)
            self.settings.set_boolean("first-run", False)
        else:
            text_header = _("Updated software is available for this "
                            "computer. Do you want to install it now?")
            if not self.hbox_restart.get_visible() and self.need_reboot:
                text_desc = _("The computer also needs to restart "
                              "to finish installing previous updates.")

        self.notebook_details.set_sensitive(True)
        self.treeview_update.set_sensitive(True)
        self.set_header(text_header)
        self.set_desc(text_desc)

        return True

    # Before we shrink the window, capture the size
    def pre_activate_details(self, expander):
        expanded = self.expander_details.get_expanded()
        if expanded:
            self._save_state()

    def activate_details(self, expander, data):
        expanded = self.expander_details.get_expanded()
        self.settings.set_boolean("show-details", expanded)
        if expanded:
            self.on_treeview_update_cursor_changed(self.treeview_update)
        self._restore_state()

    def activate_desc(self, expander, data):
        expanded = self.expander_desc.get_expanded()
        self.expander_desc.set_vexpand(expanded)

    def on_button_install_clicked(self):
        self.unity.set_install_menuitem_visible(False)
        # print("on_button_install_clicked")
        err_sum = _("Not enough free disk space")
        err_msg = _("The upgrade needs a total of %s free space on "
                    "disk '%s'. "
                    "Please free at least an additional %s of disk "
                    "space on '%s'. %s")
        # specific ways to resolve lack of free space
        remedy_archivedir = _("Remove temporary packages of former "
                              "installations using 'sudo apt clean'.")
        remedy_boot = _("You can remove old kernels using "
                        "'sudo apt autoremove', and you could also "
                        "set COMPRESS=xz in "
                        "/etc/initramfs-tools/initramfs.conf to "
                        "reduce the size of your initramfs.")
        remedy_root = _("Empty your trash and remove temporary "
                        "packages of former installations using "
                        "'sudo apt clean'.")
        remedy_tmp = _("Reboot to clean up files in /tmp.")
        remedy_usr = _("")
        # check free space and error if its not enough
        try:
            self.cache.checkFreeSpace()
        except NotEnoughFreeSpaceError as e:
            # CheckFreeSpace examines where packages are cached
            archivedir = apt_pkg.config.find_dir("Dir::Cache::archives")
            err_long = ""
            for req in e.free_space_required_list:
                if err_long != "":
                    err_long += " "
                if req.dir == archivedir:
                    err_long += err_msg % (req.size_total, req.dir,
                                           req.size_needed, req.dir,
                                           remedy_archivedir)
                elif req.dir == "/boot":
                    err_long += err_msg % (req.size_total, req.dir,
                                           req.size_needed, req.dir,
                                           remedy_boot)
                elif req.dir == "/":
                    err_long += err_msg % (req.size_total, req.dir,
                                           req.size_needed, req.dir,
                                           remedy_root)
                elif req.dir == "/tmp":
                    err_long += err_msg % (req.size_total, req.dir,
                                           req.size_needed, req.dir,
                                           remedy_tmp)
                elif req.dir == "/usr":
                    err_long += err_msg % (req.size_total, req.dir,
                                           req.size_needed, req.dir,
                                           remedy_usr)
            self.window_main.start_error(False, err_sum, err_long)
            return
        except SystemError as e:
            logging.exception("free space check failed")
        self.window_main.start_install()

    def _on_network_alert(self, watcher, state):
        # do not set the buttons to sensitive/insensitive until NM
        # can deal with dialup connections properly
        if state in NetworkManagerHelper.NM_STATE_CONNECTING_LIST:
            self.label_offline.set_text(_("Connecting..."))
            self.updates_changed()
            self.hbox_offline.show()
            self.vbox_alerts.show()
            self.connected = False
        # in doubt (STATE_UNKNOWN), assume connected
        elif (state in NetworkManagerHelper.NM_STATE_CONNECTED_LIST or
              state == NetworkManagerHelper.NM_STATE_UNKNOWN):
            self.updates_changed()
            self.hbox_offline.hide()
            self.connected = True
            # trigger re-showing the current app to get changelog info (if
            # needed)
            self.on_treeview_update_cursor_changed(self.treeview_update)
        else:
            self.connected = False
            self.label_offline.set_text(_("You may not be able to check for "
                                          "updates or download new updates."))
            self.updates_changed()
            self.hbox_offline.show()
            self.vbox_alerts.show()

    def _on_battery_alert(self, watcher, on_battery):
        if on_battery:
            self.hbox_battery.show()
            self.vbox_alerts.show()
        else:
            self.hbox_battery.hide()

    def _on_network_3g_alert(self, watcher, on_3g, is_roaming):
        #print("on 3g: %s; roaming: %s" % (on_3g, is_roaming))
        if is_roaming:
            self.hbox_roaming.show()
            self.hbox_on_3g.hide()
        elif on_3g:
            self.hbox_on_3g.show()
            self.hbox_roaming.hide()
        else:
            self.hbox_on_3g.hide()
            self.hbox_roaming.hide()

    def on_update_toggled(self, renderer, path):
        """ a toggle button in the listview was toggled """
        iter = self.store.get_iter(path)
        data = self.store.get_value(iter, LIST_UPDATE_DATA)
        # make sure that we don't allow to toggle deactivated updates
        # this is needed for the call by the row activation callback
        if data.groups:
            self.toggle_from_items([item for group in data.groups
                                    for item in group.items])
        elif data.group:
            self.toggle_from_items(data.group.items)
        else:
            self.toggle_from_items([data.item])

    def on_treeview_update_row_activated(self, treeview, path, column, *args):
        """
        If an update row was activated (by pressing space), toggle the
        install check box
        """
        self.on_update_toggled(None, path)

    def toggle_from_items(self, items):
        self.setBusy(True)
        actiongroup = apt_pkg.ActionGroup(self.cache._depcache)

        # Deselect all updates if any are selected
        keep_packages = any([item.is_selected() for item in items])
        for item in items:
            try:
                if keep_packages:
                    item.pkg.mark_keep()
                elif item.pkg.name not in self.list.held_back:
                    if not item.to_remove:
                        item.pkg.mark_install()
                    else:
                        item.pkg.mark_delete()
            except SystemError:
                pass

        # check if we left breakage
        if self.cache._depcache.broken_count:
            Fix = apt_pkg.ProblemResolver(self.cache._depcache)
            Fix.resolve_by_keep()
        self.updates_changed()
        self.treeview_update.queue_draw()
        del actiongroup
        self.setBusy(False)

    def _save_state(self):
        """ save the state  (window-size for now) """
        if self.expander_details.get_expanded():
            (w, h) = self.window_main.get_size()
            self.settings.set_int("window-width", w)
            self.settings.set_int("window-height", h)

    def _restore_state(self):
        """ restore the state (window-size for now) """
        w = self.settings.get_int("window-width")
        h = self.settings.get_int("window-height")
        expanded = self.expander_details.get_expanded()
        if expanded:
            self.window_main.begin_user_resizable(w, h)
        else:
            self.window_main.end_user_resizable()
        return False

    def _add_header(self, name, groups):
        total_size = 0
        for group in groups:
            total_size = total_size + group.get_total_size()
        header_row = [
            name,
            UpdateData(groups, None, None),
            humanize_size(total_size),
            True
        ]
        return self.store.append(None, header_row)

    def _add_groups(self, groups):
        # Each row contains:
        #  row label (for screen reader),
        #  update data tuple (is_toplevel, group object, package object),
        #  update size,
        #  update selection state
        for group in groups:
            if not group.items:
                continue

            group_is_item = None
            if not isinstance(group, UpdateSystemGroup) and \
                    len(group.items) == 1:
                group_is_item = group.items[0]

            group_row = [
                group.name,
                UpdateData(None, group, group_is_item),
                humanize_size(group.get_total_size()),
                True
            ]
            group_iter = self.store.append(None, group_row)

            if group_is_item:
                continue
            for item in group.items:
                item_row = [
                    item.name,
                    UpdateData(None, None, item),
                    humanize_size(getattr(item.pkg.candidate, "size", 0)),
                    True
                ]
                self.store.append(group_iter, item_row)

    def set_update_list(self, update_list):
        self.list = update_list

        # use the watch cursor
        self.setBusy(True)
        # disconnect the view first
        self.treeview_update.set_model(None)
        self.store.clear()
        # clean most objects
        self.dl_size = 0

        self.scrolledwindow_update.show()

        # add security and update groups to self.store
        if self.list.security_groups:
            self._add_header(_("Security updates"), self.list.security_groups)
            self._add_groups(self.list.security_groups)
        if self.list.security_groups and self.list.update_groups:
            self._add_header(_("Other updates"), self.list.update_groups)
        elif self.list.update_groups and self.list.kernel_autoremove_groups:
            self._add_header(_("Updates"), self.list.update_groups)
        if self.list.update_groups:
            self._add_groups(self.list.update_groups)
        if self.list.kernel_autoremove_groups:
            self._add_header(
                _("Unused kernel updates to be removed"),
                self.list.kernel_autoremove_groups)
            self._add_groups(self.list.kernel_autoremove_groups)

        self.treeview_update.set_model(self.store)
        self.pkg_cell_area.indent_toplevel = (
            bool(self.list.security_groups) or
            bool(self.list.kernel_autoremove_groups))
        self.update_close_button()
        self.update_count()
        self.setBusy(False)
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.updates_changed()
        return False
