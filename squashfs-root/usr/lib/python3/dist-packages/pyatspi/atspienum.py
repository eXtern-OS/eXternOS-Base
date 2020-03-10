#Copyright (C) 2008 Codethink Ltd

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

__all__ = [
           "AtspiEnum",
          ]

#------------------------------------------------------------------------------

class AtspiEnum(int):
        def __str__(self):
                return self._enum_lookup[int(self)]

        def __eq__(self, other):
                if other is None:
                        return False
                try:
                        if int(self) == int(other):
                                return True
                        else:
                                return False
                except ValueError:
                        return False

        def __hash__(self):
                return int(self)

#END---------------------------------------------------------------------------
