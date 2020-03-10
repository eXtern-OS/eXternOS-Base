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
#from pyatspi.component import *

__all__ = [
	   "interface"
]

class interface(object):
	def __init__(self, obj):
		self.obj = obj

	def __eq__(a, b):
		return (a.__class__ == b.__class__ and a.obj == b.obj)
