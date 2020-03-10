#    Gedit snippets plugin
#    Copyright (C) 2005-2006  Jesse van den Kieboom <jesse@icecrew.nl>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import tempfile
import shutil

from gi.repository import Gtk, Gio, Gdk, GObject

from .snippet import Snippet
from . import helper
from .library import Library
from .importer import Importer
from .exporter import Exporter
from .languagemanager import get_language_manager

try:
    import gettext
    gettext.bindtextdomain('gedit')
    gettext.textdomain('gedit')
    _ = gettext.gettext
except:
    _ = lambda s: s

class Manager(Gtk.Window, Gtk.Buildable):
    NAME_COLUMN = 0
    SORT_COLUMN = 1
    LANG_COLUMN = 2
    SNIPPET_COLUMN = 3
    TARGET_URI = 105

    __gtype_name__ = "GeditSnippetsManager"

    model = None
    drag_icons = ('gnome-mime-application-x-tarz', 'gnome-package', 'package')
    default_export_name = _('Snippets archive') + '.tar.gz'
    dragging = False

    def __init__(self):
        self.snippet = None
        self._temp_export = None
        self._size = (0, 0)

        self.key_press_id = 0
        self.dnd_target_list = Gtk.TargetList.new([])
        self.dnd_target_list.add(Gdk.atom_intern("text/uri-list", True), 0, self.TARGET_URI)

    def get_final_size(self):
        return self._size

    def get_language_snippets(self, path, name = None):
        library = Library()

        name = self.get_language(path)
        nodes = library.get_snippets(name)

        return nodes

    def add_new_snippet_node(self, parent):
        return self.model.append(parent, ('<i>' + _('Add a new snippet…') + \
                '</i>', '', None, None))

    def fill_language(self, piter, expand=True):
        # Remove all children
        child = self.model.iter_children(piter)

        while child and self.model.remove(child):
            True

        path = self.model.get_path(piter)
        nodes = self.get_language_snippets(path)
        language = self.get_language(path)

        Library().ref(language)

        if nodes:
            for node in nodes:
                self.add_snippet(piter, node)
        else:
            # Add node that tells there are no snippets currently
            self.add_new_snippet_node(piter)

        if expand:
            self.tree_view.expand_row(path, False)

    def build_model(self, force_reload = False):
        window = Gio.Application.get_default().get_active_window()
        if window:
            view = window.get_active_view()

            if not view:
                current_lang = None
            else:
                current_lang = view.get_buffer().get_language()
        else:
            current_lang = None

        tree_view = self['tree_view_snippets']
        expand = None

        if not self.model or force_reload:
            self.model = Gtk.TreeStore(str, str, GObject.Object, object)
            self.model.set_sort_column_id(self.SORT_COLUMN, Gtk.SortType.ASCENDING)

            manager = get_language_manager()

            langs = [manager.get_language(x) for x in manager.get_language_ids()]
            langs.sort(key=lambda x: x.get_name())

            piter = self.model.append(None, (_('Global'), '', None, None))

            # Add dummy node
            self.model.append(piter, ('', '', None, None))

            nm = None

            if current_lang:
                nm = current_lang.get_name()

            for lang in langs:
                name = lang.get_name()
                parent = self.model.append(None, (name, name, lang, None))

                # Add dummy node
                self.model.append(parent, ('', '', None, None))

                if (nm == name):
                    expand = parent
        else:
            if current_lang:
                piter = self.model.get_iter_first()
                nm = current_lang.get_name()

                while piter:
                    lang = self.model.get_value(piter, \
                            self.SORT_COLUMN)

                    if lang == nm:
                        expand = piter
                        break;

                    piter = self.model.iter_next(piter)

        tree_view.set_model(self.model)

        if not expand:
            expand = self.model.get_iter_first()

        tree_view.expand_row(self.model.get_path(expand), False)
        self.select_iter(expand)

    def get_cell_data_pixbuf_cb(self, column, cell, model, iter, data):
        snippet = model.get_value(iter, self.SNIPPET_COLUMN)

        if snippet and not snippet.valid:
            cell.set_property('icon-name', 'dialog-error')
        else:
            cell.set_property('icon-name', None)

        cell.set_property('xalign', 1.0)

    def get_cell_data_cb(self, column, cell, model, iter, data):
        snippet = model.get_value(iter, self.SNIPPET_COLUMN)

        cell.set_property('editable', snippet != None)
        cell.set_property('markup', model.get_value(iter, self.NAME_COLUMN))

    def on_tree_view_drag_data_get(self, widget, context, selection_data, info, time):
        gfile = Gio.file_new_for_path(self._temp_export)
        selection_data.set_uris([gfile.get_uri()])

    def on_tree_view_drag_begin(self, widget, context):
        self.dragging = True

        if self._temp_export:
              shutil.rmtree(os.path.dirname(self._temp_export))
              self._temp_export = None

        if self.dnd_name:
            Gtk.drag_set_icon_name(context, self.dnd_name, 0, 0)

        dirname = tempfile.mkdtemp()
        filename = os.path.join(dirname, self.default_export_name)

        # Generate temporary file name
        self.export_snippets(filename, False)
        self._temp_export = filename

    def on_tree_view_drag_end(self, widget, context):
        self.dragging = False

    def on_tree_view_drag_data_received(self, widget, context, x, y, selection, info, timestamp):
        uris = selection.get_uris()

        files = [Gio.file_new_for_uri(u) for u in uris]

        self.import_snippets(files)

    def on_tree_view_drag_motion(self, widget, context, x, y, timestamp):
        # Return False if we are dragging
        if self.dragging:
            return False

        # Check uri target
        if not Gtk.targets_include_uri(context.targets):
            return False

        # Check action
        action = None
        if context.suggested_action == Gdk.DragAction.COPY:
            action = Gdk.DragAction.COPY
        else:
            for act in context.actions:
                if act == Gdk.DragAction.COPY:
                      action = Gdk.DragAction.COPY
                      break

        if action == Gdk.DragAction.COPY:
            context.drag_status(Gdk.DragAction.COPY, timestamp)
            return True
        else:
            return False

    def build_dnd(self):
        tv = self.tree_view

        # Set it as a drag source for exporting snippets
        tv.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, [], Gdk.DragAction.DEFAULT | Gdk.DragAction.COPY)
        tv.drag_source_set_target_list(self.dnd_target_list)

        # Set it as a drag destination for importing snippets
        tv.drag_dest_set(Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,
                 [], Gdk.DragAction.DEFAULT | Gdk.DragAction.COPY)

        tv.drag_dest_set_target_list(self.dnd_target_list)

        tv.connect('drag_data_get', self.on_tree_view_drag_data_get)
        tv.connect('drag_begin', self.on_tree_view_drag_begin)
        tv.connect('drag_end', self.on_tree_view_drag_end)
        tv.connect('drag_data_received', self.on_tree_view_drag_data_received)
        tv.connect('drag_motion', self.on_tree_view_drag_motion)

        theme = Gtk.IconTheme.get_for_screen(tv.get_screen())

        self.dnd_name = None
        for name in self.drag_icons:
            icon = theme.lookup_icon(name, Gtk.IconSize.DND, 0)

            if icon:
                self.dnd_name = name
                break

    def build_tree_view(self):
        self.tree_view = self['tree_view_snippets']

        self.column = Gtk.TreeViewColumn(None)

        self.renderer = Gtk.CellRendererText()
        self.column.pack_start(self.renderer, False)
        self.column.set_cell_data_func(self.renderer, self.get_cell_data_cb, None)

        renderer = Gtk.CellRendererPixbuf()
        self.column.pack_start(renderer, True)
        self.column.set_cell_data_func(renderer, self.get_cell_data_pixbuf_cb, None)

        self.tree_view.append_column(self.column)

        self.renderer.connect('edited', self.on_cell_edited)
        self.renderer.connect('editing-started', self.on_cell_editing_started)

        selection = self.tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        selection.connect('changed', self.on_tree_view_selection_changed)

        self.build_dnd()

    def do_parser_finished(self, builder):
        self.builder = builder

        handlers_dic = {
            'on_add_snippet_button_clicked': self.on_add_snippet_button_clicked,
            'on_remove_snippet_button_clicked': self.on_remove_snippet_button_clicked,
            'on_import_snippets_button_clicked': self.on_import_snippets_button_clicked,
            'on_export_snippets_button_clicked': self.on_export_snippets_button_clicked,
            'on_entry_tab_trigger_focus_out': self.on_entry_tab_trigger_focus_out,
            'on_entry_tab_trigger_changed': self.on_entry_tab_trigger_changed,
            'on_entry_accelerator_focus_out': self.on_entry_accelerator_focus_out,
            'on_entry_accelerator_focus_in': self.on_entry_accelerator_focus_in,
            'on_entry_accelerator_key_press': self.on_entry_accelerator_key_press,
            'on_source_view_snippet_focus_out': self.on_source_view_snippet_focus_out,
            'on_tree_view_snippets_row_expanded': self.on_tree_view_snippets_row_expanded,
            'on_tree_view_snippets_key_press': self.on_tree_view_snippets_key_press}

        self.builder.connect_signals(handlers_dic)

        self.build_tree_view()
        self.build_model()

        # join treeview and toolbar
        context = self['scrolled_window_snippets'].get_style_context()
        context.set_junction_sides(Gtk.JunctionSides.BOTTOM)
        context = self['toolbar'].get_style_context()
        context.set_junction_sides(Gtk.JunctionSides.TOP)
        context.set_junction_sides(Gtk.JunctionSides.BOTTOM)

        source_view = self['source_view_snippet']
        manager = get_language_manager()
        lang = manager.get_language('snippets')

        if lang:
            source_view.get_buffer().set_highlight_syntax(True)
            source_view.get_buffer().set_language(lang)

        combo = self['combo_drop_targets']

        entry = combo.get_child()
        entry.connect('focus-out-event', self.on_entry_drop_targets_focus_out)
        entry.connect('drag-data-received', self.on_entry_drop_targets_drag_data_received)

        lst = entry.drag_dest_get_target_list()
        lst.add_uri_targets(self.TARGET_URI)

    def do_configure_event(self, event):
        if self.get_realized():
            alloc = self.get_allocation()
            self._size = (alloc.width, alloc.height)

        return Gtk.Dialog.do_configure_event(self, event)

    def __getitem__(self, key):
        return self.builder.get_object(key)

    def is_filled(self, piter):
        if not self.model.iter_has_child(piter):
            return True

        child = self.model.iter_children(piter)
        nm = self.model.get_value(child, self.NAME_COLUMN)
        lang = self.model.get_value(child, self.LANG_COLUMN)
        snippet = self.model.get_value(child, self.SNIPPET_COLUMN)

        return (lang or snippet or nm)

    def fill_if_needed(self, piter, expand=True):
        if not self.is_filled(piter):
            self.fill_language(piter, expand)

    def find_iter(self, parent, snippet):
        self.fill_if_needed(parent)
        piter = self.model.iter_children(parent)

        while (piter):
            sn = self.model.get_value(piter, self.SNIPPET_COLUMN)

            if sn == snippet.data:
                return piter

            piter = self.model.iter_next(piter)

        return None

    def selected_snippets_state(self):
        snippets = self.selected_snippets(False)
        override = False
        remove = False
        system = False

        for snippet in snippets:
            if not snippet:
                continue

            if snippet.is_override():
                override = True
            elif snippet.can_modify():
                remove = True
            else:
                system = True

            # No need to continue if both are found
            if override and remove:
                break

        return (override, remove, system)

    def update_toolbar_buttons(self):
        button_add = self['add_snippet_button']
        button_remove = self['remove_snippet_button']

        button_add.set_sensitive(self.language_path != None)
        override, remove, system = self.selected_snippets_state()

        if not (override ^ remove) or system:
            button_remove.set_sensitive(False)
            button_remove.set_icon_name('list-remove-symbolic')
        else:
            button_remove.set_sensitive(True)

            if override:
                button_remove.set_icon_name('edit-undo-symbolic')
                tooltip = _('Revert selected snippet')
            else:
                button_remove.set_icon_name('list-remove-symbolic')
                tooltip = _('Delete selected snippet')

            button_remove.set_tooltip_text(tooltip)

    def snippet_changed(self, piter = None):
        if piter:
            node = self.model.get_value(piter, self.SNIPPET_COLUMN)
            s = Snippet(node)
        else:
            s = self.snippet
            piter = self.find_iter(self.model.get_iter(self.language_path), s)

        if piter:
            nm = s.display()

            self.model.set_value(piter, self.NAME_COLUMN, nm)
            self.model.set_value(piter, self.SORT_COLUMN, nm)
            self.update_toolbar_buttons()
            self.entry_tab_trigger_update_valid()

        return piter

    def add_snippet(self, parent, snippet):
        piter = self.model.append(parent, ('', '', None, snippet))

        return self.snippet_changed(piter)

    def snippet_from_iter(self, model, piter):
        parent = model.iter_parent(piter)

        if parent:
            return model.get_value(piter, self.SNIPPET_COLUMN)
        else:
            return None

    def language_snippets(self, model, parent, as_path=False):
        self.fill_if_needed(parent, False)
        piter = model.iter_children(parent)
        snippets = []

        if not piter:
            return snippets

        while piter:
            snippet = self.snippet_from_iter(model, piter)

            if snippet:
                if as_path:
                    snippets.append(model.get_path(piter))
                else:
                    snippets.append(snippet)

            piter = model.iter_next(piter)

        return snippets

    def selected_snippets(self, include_languages=True, as_path=False):
        selection = self.tree_view.get_selection()
        (model, paths) = selection.get_selected_rows()
        snippets = []

        if paths and len(paths) != 0:
            for p in paths:
                piter = model.get_iter(p)
                parent = model.iter_parent(piter)

                if not piter:
                    continue

                if parent:
                    snippet = self.snippet_from_iter(model, piter)

                    if not snippet:
                        continue

                    if as_path:
                        snippets.append(p)
                    else:
                        snippets.append(snippet)
                elif include_languages:
                    snippets += self.language_snippets(model, piter, as_path)

        return snippets

    def selected_snippet(self):
        selection = self.tree_view.get_selection()
        (model, paths) = selection.get_selected_rows()

        if len(paths) == 1:
            piter = model.get_iter(paths[0])
            parent = model.iter_parent(piter)
            snippet = self.snippet_from_iter(model, piter)

            return parent, piter, snippet
        else:
            return None, None, None

    def selection_changed(self):
        if not self.snippet:
            sens = False

            self['entry_tab_trigger'].set_text('')
            self['entry_accelerator'].set_text('')
            buf = self['source_view_snippet'].get_buffer()
            buf.begin_not_undoable_action()
            buf.set_text('')
            buf.end_not_undoable_action()
            self['combo_drop_targets'].get_child().set_text('')

        else:
            sens = True

            self['entry_tab_trigger'].set_text(self.snippet['tag'])
            self['entry_accelerator'].set_text( \
                    self.snippet.accelerator_display())
            self['combo_drop_targets'].get_child().set_text(', '.join(self.snippet['drop-targets']))

            buf = self['source_view_snippet'].get_buffer()
            buf.begin_not_undoable_action()
            buf.set_text(self.snippet['text'])
            buf.end_not_undoable_action()


        for name in ['source_view_snippet', 'label_tab_trigger',
                'entry_tab_trigger', 'label_accelerator',
                'entry_accelerator', 'label_drop_targets',
                'combo_drop_targets']:
            self[name].set_sensitive(sens)

        self.update_toolbar_buttons()

    def select_iter(self, piter, unselect=True):
        selection = self.tree_view.get_selection()

        if unselect:
            selection.unselect_all()

        selection.select_iter(piter)

        self.tree_view.scroll_to_cell(self.model.get_path(piter), None, \
            True, 0.5, 0.5)

    def get_language(self, path):
        if path.get_indices()[0] == 0:
            return None
        else:
            return self.model.get_value(self.model.get_iter(path),
                            self.LANG_COLUMN).get_id()

    def new_snippet(self, properties=None):
        if not self.language_path:
            return None

        snippet = Library().new_snippet(self.get_language(self.language_path), properties)

        return Snippet(snippet)

    def get_dummy(self, parent):
        if not self.model.iter_n_children(parent) == 1:
            return None

        dummy = self.model.iter_children(parent)

        if not self.model.get_value(dummy, self.SNIPPET_COLUMN):
            return dummy

        return None

    def unref_languages(self):
        piter = self.model.get_iter_first()
        library = Library()

        while piter:
            if self.is_filled(piter):
                language = self.get_language(self.model.get_path(piter))
                library.save(language)

                library.unref(language)

            piter = self.model.iter_next(piter)

    # Callbacks
    def do_destroy(self):
        Gtk.Dialog.do_destroy(self)

        if not self.model:
            return

        # Remove temporary drag export
        if self._temp_export:
              shutil.rmtree(os.path.dirname(self._temp_export))
              self._temp_export = None

        self.unref_languages()
        self.snippet = None
        self.model = None

    def on_cell_editing_started(self, renderer, editable, path):
        piter = self.model.get_iter(path)

        if not self.model.iter_parent(piter):
            renderer.stop_editing(True)
            editable.remove_widget()
        elif isinstance(editable, Gtk.Entry):
            if self.snippet:
                editable.set_text(self.snippet['description'])
            else:
                # This is the `Add a new snippet...` item
                editable.set_text('')

            editable.grab_focus()

    def on_cell_edited(self, cell, path, new_text):
        if new_text != '':
            piter = self.model.get_iter(path)
            node = self.model.get_value(piter, self.SNIPPET_COLUMN)

            if node:
                if node == self.snippet.data:
                    s = self.snippet
                else:
                    s = Snippet(node)

                s['description'] = new_text
                self.snippet_changed(piter)
                self.select_iter(piter)
            else:
                # This is the `Add a new snippet...` item
                # We create a new snippet
                snippet = self.new_snippet({'description': new_text})

                if snippet:
                    self.model.set_value(piter, self.SNIPPET_COLUMN, snippet.data)
                    self.snippet_changed(piter)
                    self.snippet = snippet
                    self.selection_changed()

    def on_entry_accelerator_focus_out(self, entry, event):
        if not self.snippet:
            return

        entry.set_text(self.snippet.accelerator_display())

    def entry_tab_trigger_update_valid(self):
        entry = self['entry_tab_trigger']
        text = entry.get_text()

        if text and not Library().valid_tab_trigger(text):
            img = self['image_tab_trigger']
            img.set_from_icon_name('dialog-error', Gtk.IconSize.BUTTON)
            img.show()

            #self['hbox_tab_trigger'].set_spacing(3)
            tip = _('This is not a valid Tab trigger. Triggers can either contain alphanumeric characters (or _, : and .) or a single (non-alphanumeric) character like: {, [, etc.')

            entry.set_tooltip_text(tip)
            img.set_tooltip_text(tip)
        else:
            self['image_tab_trigger'].hide()
            #self['hbox_tab_trigger'].set_spacing(0)
            entry.set_tooltip_text(_('Single word the snippet is activated with after pressing Tab'))

        return False

    def on_entry_tab_trigger_focus_out(self, entry, event):
        if not self.snippet:
            return

        text = entry.get_text()

        # save tag
        self.snippet['tag'] = text
        self.snippet_changed()

    def on_entry_drop_targets_focus_out(self, entry, event):
        if not self.snippet:
            return

        text = entry.get_text()

        # save drop targets
        self.snippet['drop-targets'] = text
        self.snippet_changed()

    def on_entry_tab_trigger_changed(self, entry):
        self.entry_tab_trigger_update_valid()

    def on_source_view_snippet_focus_out(self, source_view, event):
        if not self.snippet:
            return

        buf = source_view.get_buffer()
        text = buf.get_text(buf.get_start_iter(), \
               buf.get_end_iter(), False)

        self.snippet['text'] = text
        self.snippet_changed()

    def on_add_snippet_button_clicked(self, button):
        snippet = self.new_snippet()

        if not snippet:
            return

        parent = self.model.get_iter(self.language_path)
        path = self.model.get_path(parent)

        dummy = self.get_dummy(parent)

        if dummy:
            # Remove the dummy
            self.model.remove(dummy)

        # Add the snippet
        piter = self.add_snippet(parent, snippet.data)
        self.select_iter(piter)

        if not self.tree_view.row_expanded(path):
            self.tree_view.expand_row(path, False)
            self.select_iter(piter)

        self.tree_view.grab_focus()

        path = self.model.get_path(piter)
        self.tree_view.set_cursor(path, self.column, True)

    def file_filter(self, name, pattern):
        fil = Gtk.FileFilter()
        fil.set_name(name)

        for p in pattern:
            fil.add_pattern(p)

        return fil

    def import_snippets(self, files):
        success = True

        for gfile in files:
            if not gfile.has_uri_scheme('file'):
                continue

            # Remove file://
            filename = gfile.get_path()

            importer = Importer(filename)
            error = importer.run()

            if error:
                message = _('The following error occurred while importing: %s') % error
                success = False
                helper.message_dialog(self.get_toplevel(), Gtk.MessageType.ERROR, message)

        self.build_model(True)

        if success:
            message = _('Import successfully completed')
            helper.message_dialog(self.get_toplevel(), Gtk.MessageType.INFO, message)

    def on_import_response(self, dialog, response):
        if response == Gtk.ResponseType.CANCEL or response == Gtk.ResponseType.CLOSE:
            dialog.destroy()
            return

        f = dialog.get_files()
        dialog.destroy()

        self.import_snippets(f)

    def on_import_snippets_button_clicked(self, button):
        dlg = Gtk.FileChooserDialog(parent=self.get_toplevel(), title=_("Import snippets"),
                action=Gtk.FileChooserAction.OPEN,
                buttons=(_("_Cancel"), Gtk.ResponseType.CANCEL,
                     _("_Open"), Gtk.ResponseType.OK))

        dlg.add_filter(self.file_filter(_('All supported archives'), ('*.gz','*.bz2','*.tar', '*.xml')))
        dlg.add_filter(self.file_filter(_('Gzip compressed archive'), ('*.tar.gz',)))
        dlg.add_filter(self.file_filter(_('Bzip2 compressed archive'), ('*.tar.bz2',)))
        dlg.add_filter(self.file_filter(_('Single snippets file'), ('*.xml',)))
        dlg.add_filter(self.file_filter(_('All files'), '*'))

        dlg.connect('response', self.on_import_response)
        dlg.set_local_only(True)

        dlg.show()

    def export_snippets_real(self, filename, snippets, show_dialogs=True):
        export = Exporter(filename, snippets)
        error = export.run()

        if error:
            message = _('The following error occurred while exporting: %s') % error
            msgtype = Gtk.MessageType.ERROR
            retval = False
        else:
            message = _('Export successfully completed')
            msgtype = Gtk.MessageType.INFO
            retval = True

        if show_dialogs:
            helper.message_dialog(self.get_toplevel(), msgtype, message)

        return retval

    def on_export_response(self, dialog, response):
        filename = dialog.get_filename()
        snippets = dialog._export_snippets

        dialog.destroy()

        if response != Gtk.ResponseType.OK:
            return

        self.export_snippets_real(filename, snippets);

    def export_snippets(self, filename=None, show_dialogs=True):
        snippets = self.selected_snippets()

        if not snippets or len(snippets) == 0:
            return False

        usersnippets = []
        systemsnippets = []

        # Iterate through snippets and look for system snippets
        for snippet in snippets:
            if snippet.can_modify():
                usersnippets.append(snippet)
            else:
                systemsnippets.append(snippet)

        export_snippets = snippets

        if len(systemsnippets) != 0 and show_dialogs:
            # Ask if system snippets should also be exported
            message = _('Do you want to include selected <b>system</b> snippets in your export?')
            mes = Gtk.MessageDialog(flags=Gtk.DialogFlags.MODAL,
                    type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    message_format=message)
            mes.set_property('use-markup', True)
            resp = mes.run()
            mes.destroy()

            if resp == Gtk.ResponseType.NO:
                export_snippets = usersnippets
            elif resp != Gtk.ResponseType.YES:
                return False

        if len(export_snippets) == 0 and show_dialogs:
            message = _('There are no snippets selected to be exported')
            helper.message_dialog(self.get_toplevel(), Gtk.MessageType.QUESTION, message)
            return False

        if not filename:
            dlg = Gtk.FileChooserDialog(parent=self.get_toplevel(), title=_('Export snippets'),
                    action=Gtk.FileChooserAction.SAVE,
                    buttons=(_("_Cancel"), Gtk.ResponseType.CANCEL,
                         _("_Save"), Gtk.ResponseType.OK))

            dlg._export_snippets = export_snippets
            dlg.add_filter(self.file_filter(_('All supported archives'), ('*.gz','*.bz2','*.tar')))
            dlg.add_filter(self.file_filter(_('Gzip compressed archive'), ('*.tar.gz',)))
            dlg.add_filter(self.file_filter(_('Bzip2 compressed archive'), ('*.tar.bz2',)))

            dlg.add_filter(self.file_filter(_('All files'), '*'))
            dlg.set_do_overwrite_confirmation(True)
            dlg.set_current_name(self.default_export_name)

            dlg.connect('response', self.on_export_response)
            dlg.set_local_only(True)

            dlg.show()
            return True
        else:
            return self.export_snippets_real(filename, export_snippets, show_dialogs)

    def on_export_snippets_button_clicked(self, button):
        snippets = self.selected_snippets()

        if not snippets or len(snippets) == 0:
            return

        usersnippets = []
        systemsnippets = []

        # Iterate through snippets and look for system snippets
        for snippet in snippets:
            if snippet.can_modify():
                usersnippets.append(snippet)
            else:
                systemsnippets.append(snippet)

        dlg = Gtk.FileChooserDialog(parent=self.get_toplevel(), title=_('Export snippets'),
                action=Gtk.FileChooserAction.SAVE,
                buttons=(_('_Cancel'), Gtk.ResponseType.CANCEL,
                     _('_Save'), Gtk.ResponseType.OK))

        dlg._export_snippets = snippets

        if len(systemsnippets) != 0:
            # Ask if system snippets should also be exported
            message = _('Do you want to include selected <b>system</b> snippets in your export?')
            mes = Gtk.MessageDialog(flags=Gtk.DialogFlags.MODAL,
                    type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    message_format=message)
            mes.set_property('use-markup', True)
            resp = mes.run()
            mes.destroy()

            if resp == Gtk.ResponseType.NO:
                dlg._export_snippets = usersnippets
            elif resp != Gtk.ResponseType.YES:
                dlg.destroy()
                return

        if len(dlg._export_snippets) == 0:
            dlg.destroy()

            message = _('There are no snippets selected to be exported')
            helper.message_dialog(self.get_toplevel(), Gtk.MessageType.QUESTION, message)
            return

        dlg.add_filter(self.file_filter(_('All supported archives'), ('*.gz','*.bz2','*.tar')))
        dlg.add_filter(self.file_filter(_('Gzip compressed archive'), ('*.tar.gz',)))
        dlg.add_filter(self.file_filter(_('Bzip2 compressed archive'), ('*.tar.bz2',)))

        dlg.add_filter(self.file_filter(_('All files'), '*'))
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_name(self.default_export_name)

        dlg.connect('response', self.on_export_response)
        dlg.set_local_only(True)

        dlg.show()

    def remove_snippet_revert(self, path, piter):
        node = self.snippet_from_iter(self.model, piter)
        Library().revert_snippet(node)

        return piter

    def remove_snippet_delete(self, path, piter):
        node = self.snippet_from_iter(self.model, piter)
        parent = self.model.iter_parent(piter)

        Library().remove_snippet(node)
        idx = path.get_indices()

        if self.model.remove(piter):
            return piter
        elif idx[-1] != 0:
            self.select_iter(self.model.get_iter((idx[0], idx[1] - 1)))
        else:
            dummy = self.add_new_snippet_node(parent)
            self.tree_view.expand_row(self.model.get_path(parent), False)
            return dummy

    def on_remove_snippet_button_clicked(self, button):
        override, remove, system = self.selected_snippets_state()

        if not (override ^ remove) or system:
            return

        paths = self.selected_snippets(include_languages=False, as_path=True)

        if override:
            action = self.remove_snippet_revert
        else:
            action = self.remove_snippet_delete

        # Remove selection
        self.tree_view.get_selection().unselect_all()

        # Create tree row references
        references = []
        for path in paths:
            # FIXME: this should be fixed in pygobject or something
            references.append(Gtk.TreeRowReference.new(self.model, path))

        # Remove/revert snippets
        select = None
        for reference in references:
            path = reference.get_path()
            piter = self.model.get_iter(path)

            res = action(path, piter)

            if res:
                select = res

        if select:
            self.select_iter(select)

        self.selection_changed()

    def set_accelerator(self, keyval, mod):
        accelerator = Gtk.accelerator_name(keyval, mod)
        self.snippet['accelerator'] = accelerator

        return True

    def on_entry_accelerator_key_press(self, entry, event):
        if event.keyval == Gdk.keyval_from_name('Escape'):
            # Reset
            entry.set_text(self.snippet.accelerator_display())
            self.tree_view.grab_focus()

            return True
        elif event.keyval == Gdk.keyval_from_name('Delete') or \
                event.keyval == Gdk.keyval_from_name('BackSpace'):
            # Remove the accelerator
            entry.set_text('')
            self.snippet['accelerator'] = ''
            self.tree_view.grab_focus()

            self.snippet_changed()
            return True
        elif Library().valid_accelerator(event.keyval, event.get_state()):
            # New accelerator
            self.set_accelerator(event.keyval, \
                    event.get_state() & Gtk.accelerator_get_default_mod_mask())
            entry.set_text(self.snippet.accelerator_display())
            self.snippet_changed()
            self.tree_view.grab_focus()

        else:
            return True

    def on_entry_accelerator_focus_in(self, entry, event):
        if self.snippet['accelerator']:
            entry.set_text(_('Type a new shortcut, or press Backspace to clear'))
        else:
            entry.set_text(_('Type a new shortcut'))

    def update_language_path(self):
        model, paths = self.tree_view.get_selection().get_selected_rows()

        # Check if all have the same language parent
        current_parent = None

        for path in paths:
            piter = model.get_iter(path)
            parent = model.iter_parent(piter)

            if parent:
                path = model.get_path(parent)

            if current_parent != None and current_parent != path:
                current_parent = None
                break
            else:
                current_parent = path

        self.language_path = current_parent

    def on_tree_view_selection_changed(self, selection):
        parent, piter, node = self.selected_snippet()

        if self.snippet:
            self.on_entry_tab_trigger_focus_out(self['entry_tab_trigger'],
                    None)
            self.on_source_view_snippet_focus_out(self['source_view_snippet'],
                    None)
            self.on_entry_drop_targets_focus_out(self['combo_drop_targets'].get_child(),
                    None)

        self.update_language_path()

        if node:
            self.snippet = Snippet(node)
        else:
            self.snippet = None

        self.selection_changed()

    def iter_after(self, target, after):
        if not after:
            return True

        tp = self.model.get_path(target)
        ap = self.model.get_path(after)

        if tp[0] > ap[0] or (tp[0] == ap[0] and (len(ap) == 1 or tp[1] > ap[1])):
            return True

        return False

    def on_tree_view_snippets_key_press(self, treeview, event):
        if event.keyval == Gdk.keyval_from_name('Delete'):
            self.on_remove_snippet_button_clicked(None)
            return True

    def on_tree_view_snippets_row_expanded(self, treeview, piter, path):
        # Check if it is already filled
        self.fill_if_needed(piter)
        self.select_iter(piter)

    def on_entry_drop_targets_drag_data_received(self, entry, context, x, y, selection_data, info, timestamp):
        uris = helper.drop_get_uris(selection_data)
        if not uris:
            return

        text = entry.get_text()

        if text:
            mimes = [text]
        else:
            mimes = []

        for uri in uris:
            try:
                mime = Gio.content_type_guess(uri)
            except:
                mime = None

            if mime:
                mimes.append(mime)

        entry.set_text(', '.join(mimes))
        self.on_entry_drop_targets_focus_out(entry, None)
        context.finish(True, False, timestamp)

        entry.stop_emission('drag_data_received')

# ex:ts=4:et:
