#Copyright (c) 2013 SUSE LLC.

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
           "TableCell",
          ]

#------------------------------------------------------------------------------

class TableCell(interface):
        """
        An interface used by cells in a table.
        """

        def get_columnSpan(self):
                return Atspi.TableCell.get_column_span(self.obj)
        _columnSpanDoc = \
                """
                Get the number of columns occupied by this cell.
                """
        columnSpan = property(fget=get_columnSpan, doc=_columnSpanDoc)

        def get_columnHeaderCells(self):
                return Atspi.TableCell.get_column_header_cells(self.obj)
        _columnHeaderCellsDoc = \
                """
                Get the column headers as an array of cell accessibles.
                """
        columnHeaderCells = property(fget=get_columnHeaderCells, doc=_columnHeaderCellsDoc)

        def get_rowSpan(self):
                return Atspi.TableCell.get_row_span(self.obj)
        _rowSpanDoc = \
                """
                Get the number of rows occupied by this cell.
                """
        rowSpan = property(fget=get_rowSpan, doc=_rowSpanDoc)

        def get_rowHeaderCells(self):
                return Atspi.TableCell.get_row_header_cells(self.obj)
        _rowHeaderCellsDoc = \
                """
                Get the row headers as an array of cell accessibles.
                """
        rowHeaderCells = property(fget=get_rowHeaderCells, doc=_rowHeaderCellsDoc)

        def get_position(self):
                return Atspi.TableCell.get_position(self.obj)
        _positionDoc = \
                """
                Returns the tabular position of this accessible.
                """
        position = property(fget=get_position, doc=_positionDoc)

        def getRowColumnSpan(self):
                """
                determine the row and column indices and span of the given cell.
                """
                return Atspi.TableCell.get_row_column_span(self.obj)

        def get_table(self):
                return Atspi.TableCell.get_table(self.obj)
        _tableDoc = \
                """
                Returns a reference to the accessible of the containing table.
                """
        table = property(fget=get_table, doc=_tableDoc)

#END----------------------------------------------------------------------------
