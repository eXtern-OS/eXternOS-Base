#Copyright (C) 2008 Codethink Ltd
#Copyright (c) 2012 SUSE LINUX Products GmbH, Nuernberg, Germany.

#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License version 2 as published by the Free Software Foundation.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU Lesser General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from gi.repository import Atspi
from pyatspi.utils import *
from pyatspi.interface import *

__all__ = [
           "Table",
          ]

#------------------------------------------------------------------------------

class Table(interface):
        """
        An interface used by containers whose contained data is arranged
        in a "tabular" (i.e. row-column) fashion. Tables may resemble
        a two-dimensional grid, as in a spreadsheet, or may feature objects
        which span multiple rows and/or columns, but whose bounds are
        aligned on a row/column matrix. Thus, the Table interface may
        be used to represent "spreadsheets" as well as "frames".
        Objects within tables are children of the Table instance, and
        they may be referenced either via a child index or via a row/column
        pair. Their role may be ROLE_TABLE_CELL, but table 'cells' may
        have other roles as well. These 'cells' may implement other interfaces,
        such as Text, Action, Image, and Component, and should do so
        as appropriate to their onscreen representation and/or behavior.
        """

        def addColumnSelection(self, column):
                """
                Select the specified column, adding it to the current column
                selection, if the table's selection model permits it.
                @param : column
                @return True if the specified column was successfully selected,
                False if not.
                """
                return Atspi.Table.add_column_selection(self.obj, column)

        def addRowSelection(self, row):
                """
                Select the specified row, adding it to the current row selection,
                if the table's selection model permits it.
                @param : row
                @return True if the specified row was successfully selected,
                False if not.
                """
                return Atspi.Table.add_row_selection(self.obj, row)

        def getAccessibleAt(self, row, column):
                """
                Get the table cell at the specified row and column indices. 
                @param : row
                the specified table row, zero-indexed. 
                @param : column
                the specified table column, zero-indexed.
                @return an Accessible object representing the specified table
                cell.
                """
                return Atspi.Table.get_accessible_at(self.obj, row, column)

        def getColumnAtIndex(self, index):
                """
                Get the table column index occupied by the child at a particular
                1-D child index.
                @param : index
                the specified child index, zero-indexed.
                @return a long integer indicating the first column spanned by
                the child of a table, at the specified 1-D (zero-offset) index.
                """
                return Atspi.Table.get_column_at_index(self.obj, index);

        def getColumnDescription(self, column):
                """
                Get a text description of a particular table column. This differs
                from AccessibleTable_getColumnHeader, which returns an Accessible.
                @param : column
                the specified table column, zero-indexed.
                @return a UTF-8 string describing the specified table column,
                if available.
                """
                return Atspi.Table.get_column_description(self.obj, column)

        def getColumnExtentAt(self, row, column):
                """
                Get the number of columns spanned by the table cell at the specific
                row and column. (some tables can have cells which span multiple
                rows and/or columns).
                @param : row
                the specified table row, zero-indexed. 
                @param : column
                the specified table column, zero-indexed.
                @return a long integer indicating the number of columns spanned
                by the specified cell.
                """
                return Atspi.Table.get_column_extent_at(self.obj, row, column)

        def getColumnHeader(self, index):
                """
                Get the header associated with a table column, if available,
                as an instance of Accessible. This differs from getColumnDescription,
                which returns a string.
                @param : column
                the specified table column, zero-indexed.
                @return an Accessible representatin of the specified table column,
                if available.
                """
                return Atspi.Table.get_column_header(self.obj, index)

        def getIndexAt(self, row, column):
                """
                Get the 1-D child index corresponding to the specified 2-D row
                and column indices. 
                @param : row
                the specified table row, zero-indexed. 
                @param : column
                the specified table column, zero-indexed.
                @return a long integer which serves as the index of a specified
                cell in the table, in a form usable by Accessible::getChildAtIndex.
                """
                return Atspi.Table.get_index_at(self.obj, row, column)

        def getRowAtIndex(self, index):
                """
                Get the table row index occupied by the child at a particular
                1-D child index.
                @param : index
                the specified child index, zero-indexed.
                @return a long integer indicating the first row spanned by the
                child of a table, at the specified 1-D (zero-offset) index.
                """
                return Atspi.Table.get_row_at_index(self.obj, index)

        def getRowColumnExtentsAtIndex(self, index):
                """
                Given a child index, determine the row and column indices and
                extents, and whether the cell is currently selected. If the child
                at index is not a cell (for instance, if it is a summary, caption,
                etc.), False is returned.
                @param : index
                the index of the Table child whose row/column extents are requested.
                @param : row
                back-filled with the first table row associated with the cell
                with child index index. 
                @param : col
                back-filled with the first table column associated with the cell
                with child index index. 
                @param : row_extents
                back-filled with the number of table rows across which child
                i extends. 
                @param : col_extents
                back-filled with the number of table columns across which child
                i extends. 
                @param : is_selected
                a boolean which is back-filled with True if the child at index
                i corresponds to a selected table cell, False otherwise.
                Example: If the Table child at index '6' extends across columns
                5 and 6 of row 2 of a Table instance, and is currently selected,
                then retval=table::getRowColumnExtentsAtIndex(6,row,col,
                row_extents,
                col_extents,
                is_selected);
                 will return True, and after the call row, col, row_extents,
                col_extents, and is_selected will contain 2, 5, 1, 2, and True,
                respectively.
                @return True if the index is associated with a valid table cell,
                False if the index does not correspond to a cell. If False is
                returned, the values of the out parameters are undefined.
                """
                return Atspi.Table.get_row_column_extents_at_index(self.obj, index)

        def getRowDescription(self, index):
                """
                Get a text description of a particular table row. This differs
                from AccessibleTable_getRowHeader, which returns an Accessible.
                @param : row
                the specified table row, zero-indexed.
                @return a UTF-8 string describing the specified table row, if
                available.
                """
                return Atspi.Table.get_row_description(self.obj, index)

        def getRowExtentAt(self, row, column):
                """
                Get the number of rows spanned by the table cell at the specific
                row and column. (some tables can have cells which span multiple
                rows and/or columns).
                @param : row
                the specified table row, zero-indexed. 
                @param : column
                the specified table column, zero-indexed.
                @return a long integer indicating the number of rows spanned
                by the specified cell.
                """
                return Atspi.Table.get_row_extent_at(self.obj, row, column)

        def getRowHeader(self, row):
                """
                Get the header associated with a table row, if available. This
                differs from getRowDescription, which returns a string.
                @param : row
                the specified table row, zero-indexed.
                @return an Accessible representatin of the specified table row,
                if available.
                """
                return Atspi.Table.get_row_header(self.obj, row)

        def getSelectedColumns(self):
                """
                Obtain the indices of all columns which are currently selected.
                @return a sequence of integers comprising the indices of columns
                currently selected.
                """
                return Atspi.Table.get_selected_columns(self.obj)

        def getSelectedRows(self):
                """
                Obtain the indices of all rows which are currently selected.
                @return a sequence of integers comprising the indices of rows
                currently selected.
                """
                return Atspi.Table.get_selected_rows(self.obj)

        def isColumnSelected(self, column):
                """
                Determine whether a table column is selected. 
                @param : column
                the column being queried.
                @return True if the specified column is currently selected, False
                if not.
                """
                return Atspi.Table.is_column_selected(self.obj, column)

        def isRowSelected(self, row):
                """
                Determine whether a table row is selected. 
                @param : row
                the row being queried.
                @return True if the specified row is currently selected, False
                if not.
                """
                return Atspi.Table.is_row_selected(self.obj, row)

        def isSelected(self, row, column):
                """
                Determine whether the cell at a specific row and column is selected.
                @param : row
                a row occupied by the cell whose state is being queried. 
                @param : column
                a column occupied by the cell whose state is being queried.
                @return True if the specified cell is currently selected, False
                if not.
                """
                return Atspi.Table.is_selected(self.obj, row, column)

        def removeColumnSelection(self, column):
                """
                Remove the specified column from current column selection, if
                the table's selection model permits it.
                @param : column
                @return True if the specified column was successfully de-selected,
                False if not.
                """
                return Atspi.Table.remove_column_selection(self.obj, column)

        def removeRowSelection(self, row):
                """
                Remove the specified row from current row selection, if the table's
                selection model permits it.
                @param : row
                @return True if the specified row was successfully de-selected,
                False if not.
                """
                return Atspi.Table.remove_row_selection(self.obj, row)

        def get_caption(self):
                return Atspi.Table.get_caption(self.obj)
        _captionDoc = \
                """
                An Accessible which represents of a caption for a Table.
                """
        caption = property(fget=get_caption, doc=_captionDoc)

        def get_nColumns(self):
                return Atspi.Table.get_n_columns(self.obj)
        _nColumnsDoc = \
                """
                The total number of columns in this table (including empty columns),
                exclusive of columns which are programmatically hidden. Columns
                which are scrolled out of view or clipped by the current viewport
                are included.
                """
        nColumns = property(fget=get_nColumns, doc=_nColumnsDoc)

        def get_nRows(self):
                return Atspi.Table.get_n_rows(self.obj)
        _nRowsDoc = \
                """
                The total number of rows in this table (including empty rows),
                exclusive of any rows which are programmatically hidden. Rows
                which are merely scrolled out of view are included.
                """
        nRows = property(fget=get_nRows, doc=_nRowsDoc)

        def get_nSelectedColumns(self):
                return Atspi.Table.get_n_selected_columns(self.obj)
        _nSelectedColumnsDoc = \
                """
                The number of columns currently selected. A selected column is
                one in which all included cells are selected.
                """
        nSelectedColumns = property(fget=get_nSelectedColumns, doc=_nSelectedColumnsDoc)

        def get_nSelectedRows(self):
                return Atspi.Table.get_n_selected_rows(self.obj)
        _nSelectedRowsDoc = \
                """
                The number of rows currently selected. A selected row is one
                in which all included cells are selected.
                """
        nSelectedRows = property(fget=get_nSelectedRows, doc=_nSelectedRowsDoc)

        def get_summary(self):
                return Atspi.Table.get_summary(self.obj)
        _summaryDoc = \
                """
                An accessible object which summarizes the contents of a Table.
                This object is frequently itself a Table instance, albeit a simplified
                one.
                """
        summary = property(fget=get_summary, doc=_summaryDoc)

#END----------------------------------------------------------------------------
