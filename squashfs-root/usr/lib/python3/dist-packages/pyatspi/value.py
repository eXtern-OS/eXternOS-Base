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
           "Value",
          ]

#------------------------------------------------------------------------------

class Value(interface):
        """
        An interface supporting controls which allow a one-dimensional,
        scalar quantity to be modified or which reflect a scalar quantity.
        (If STATE_EDITABLE is not present, the valuator is treated as
        "read only".
        """

        def get_currentValue(self):
                return Atspi.Value.get_current_value(self.obj)
        def set_currentValue(self, value):
                Atspi.Value.set_current_value(self.obj, value)
        _currentValueDoc = \
                """
                The current value of the valuator.
                """
        currentValue = property(fget=get_currentValue, fset=set_currentValue, doc=_currentValueDoc)

        def get_maximumValue(self):
                return Atspi.Value.get_maximum_value(self.obj)
        _maximumValueDoc = \
                """
                The maximum value allowed by this valuator.
                """
        maximumValue = property(fget=get_maximumValue, doc=_maximumValueDoc)

        def get_minimumIncrement(self):
                return Atspi.Value.get_minimum_increment(self.obj)
        _minimumIncrementDoc = \
                """
                The smallest incremental change which this valuator allows. If
                0, the incremental changes to the valuator are limited only by
                the precision of a double precision value on the platform.
                """
        minimumIncrement = property(fget=get_minimumIncrement, doc=_minimumIncrementDoc)

        def get_minimumValue(self):
                return Atspi.Value.get_minimum_value(self.obj)
        _minimumValueDoc = \
                """
                The minimum value allowed by this valuator.
                """
        minimumValue = property(fget=get_minimumValue, doc=_minimumValueDoc)

#END----------------------------------------------------------------------------
