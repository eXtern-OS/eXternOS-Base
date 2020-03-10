#Copyright (C) 210 Novell, Inc.

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

__version__ = (1, 9, 0)

import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

from pyatspi.Accessibility import *

#This is a re-creation of the namespace pollution implemented
#by PyORBit.
import sys
import pyatspi.Accessibility as Accessibility
sys.modules['Accessibility'] = Accessibility
