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
from pyatspi.atspienum import *
from pyatspi.utils import *
from pyatspi.interface import *

__all__ = [
           "CoordType",
           "XY_SCREEN",
           "XY_WINDOW",
           "ComponentLayer",
           "Component",
           "LAYER_BACKGROUND",
           "LAYER_CANVAS",
           "LAYER_INVALID",
           "LAYER_LAST_DEFINED",
           "LAYER_MDI",
           "LAYER_OVERLAY",
           "LAYER_POPUP",
           "LAYER_WIDGET",
           "LAYER_WINDOW",
          ]

#------------------------------------------------------------------------------

class CoordType(AtspiEnum):
        _enum_lookup = {
                0:'XY_SCREEN',
                1:'XY_WINDOW',
        }

XY_SCREEN = CoordType(0)
XY_WINDOW = CoordType(1)

#------------------------------------------------------------------------------

class ComponentLayer(AtspiEnum):
        _enum_lookup = {
                0:'LAYER_INVALID',
                1:'LAYER_BACKGROUND',
                2:'LAYER_CANVAS',
                3:'LAYER_WIDGET',
                4:'LAYER_MDI',
                5:'LAYER_POPUP',
                6:'LAYER_OVERLAY',
                7:'LAYER_WINDOW',
                8:'LAYER_LAST_DEFINED',
        }

LAYER_BACKGROUND = ComponentLayer(1)
LAYER_CANVAS = ComponentLayer(2)
LAYER_INVALID = ComponentLayer(0)
LAYER_LAST_DEFINED = ComponentLayer(8)
LAYER_MDI = ComponentLayer(4)
LAYER_OVERLAY = ComponentLayer(6)
LAYER_POPUP = ComponentLayer(5)
LAYER_WIDGET = ComponentLayer(3)
LAYER_WINDOW = ComponentLayer(7)

#------------------------------------------------------------------------------

class Component(interface):
        """
        The Component interface is implemented by objects which occupy
        on-screen space, e.g. objects which have onscreen visual representations.
        The methods in Component allow clients to identify where the
        objects lie in the onscreen coordinate system, their relative
        size, stacking order, and position. It also provides a mechanism
        whereby keyboard focus may be transferred to specific user interface
        elements programmatically. This is a 2D API, coordinates of 3D
        objects are projected into the 2-dimensional screen view for
        purposes of this interface.
        """

        def contains(self, x, y, coord_type):
                """
                @return True if the specified point lies within the Component's
                bounding box, False otherwise.
                """
                return Atspi.Component.contains(self.obj, x, y, coord_type)

        def getAccessibleAtPoint(self, x, y, coord_type):
                """
                @return the Accessible child whose bounding box contains the
                specified point.
                """
                return Atspi.Component.get_accessible_at_point(self.obj, x, y, coord_type)

        def getAlpha(self):
                """
                Obtain the alpha value of the component. An alpha value of 1.0
                or greater indicates that the object is fully opaque, and an
                alpha value of 0.0 indicates that the object is fully transparent.
                Negative alpha values have no defined meaning at this time.
                """
                return Atspi.Component.get_alpha(self.obj)

        def getExtents(self, coord_type):
                """
                Obtain the Component's bounding box, in pixels, relative to the
                specified coordinate system. 
                @param coord_type
                @return a BoundingBox which entirely contains the object's onscreen
                visual representation.
                """
                return getBoundingBox(Atspi.Component.get_extents(self.obj, coord_type))

        def getLayer(self):
                """
                @return the ComponentLayer in which this object resides.
                """
                return Atspi.Component.get_layer(self.obj)

        def getMDIZOrder(self):
                """
                Obtain the relative stacking order (i.e. 'Z' order) of an object.
                Larger values indicate that an object is on "top" of the stack,
                therefore objects with smaller MDIZOrder may be obscured by objects
                with a larger MDIZOrder, but not vice-versa. 
                @return an integer indicating the object's place in the stacking
                order.
                """
                return Atspi.Component.get_mdi_z_order(self.obj)

        def getPosition(self, coord_type):
                """
                Obtain the position of the current component in the coordinate
                system specified by coord_type. 
                @param : coord_type
                @param : x
                an out parameter which will be back-filled with the returned
                x coordinate. 
                @param : y
                an out parameter which will be back-filled with the returned
                y coordinate.
                """
                return pointToList(Atspi.Component.get_position(self.obj, coord_type))

        def getSize(self):
                """
                Obtain the size, in the coordinate system specified by coord_type,
                of the rectangular area which fully contains the object's visual
                representation, without accounting for viewport clipping. 
                @param : width
                the object's horizontal extents in the specified coordinate system.
                @param : height
                the object's vertical extents in the specified coordinate system.
                """
                return pointToList(Atspi.Component.get_size(self.obj))

        def grabFocus(self):
                """
                Request that the object obtain keyboard focus.
                @return True if keyboard focus was successfully transferred to
                the Component.
                """
                return Atspi.Component.grab_focus(self.obj)

#END----------------------------------------------------------------------------
