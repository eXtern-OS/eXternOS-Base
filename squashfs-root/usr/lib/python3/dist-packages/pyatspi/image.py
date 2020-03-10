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

__all__ = [
           "Image",
          ]

#------------------------------------------------------------------------------

class Image:
        """
        An interface implemented by objects which render image data or
        pictorial information to the screen. When onscreen components
        include graphical information that is not purely intended to
        enhance "3d effect" or visual layout, but which conveys some
        semantic or informational content to the sighted user, they should
        implement Image, and that semantic content should be conveyed
        textually to the extent possible via the image description, as
        well as the Accessible::name and Accessible::description properties.
        """

        def __init__(self, obj):
                self.obj = obj

        def getImageExtents(self, coordType):
                """
                Obtain a bounding box which entirely contains the image contents,
                as displayed on screen. The bounds returned do not account for
                any viewport clipping or the fact that the image may be partially
                or wholly obscured by other onscreen content. 
                @param : coordType
                If 0, the returned bounding box position is returned relative
                to the screen; if 1, the bounding box position is returned relative
                to the containing window. 
                @return a BoundingBox enclosing the image's onscreen representation.
                """
                return getBoundingBox(Atspi.Image.get_image_extents(self.obj, coordType))

        def getImagePosition(self, coord_type):
                """
                Get the coordinates of the current image position on screen.
                @param : x
                Back-filled with the x coordinate of the onscreen image (i.e.
                the minimum x coordinate) 
                @param : y
                Back-filled with the y coordinate of the onscreen image (i.e.
                the minimum y coordinate) 
                @param : coordType
                If 0, the returned x and y coordinates are returned relative
                to the screen; if 1, they are returned relative to the containing
                window.
                """
                return pointToList(Atspi.Image.get_image_position(self.obj, coord_type))

        def getImageSize(self):
                """
                Obtain the width and height of the current onscreen view of the
                image. The extents returned do not account for any viewport clipping
                or the fact that the image may be partially or wholly obscured
                by other onscreen content. 
                @param : width
                Back-filled with the x extents of the onscreen image (i.e. the
                image width in pixels) 
                @param : height
                Back-filled with the y extents of the onscreen image (i.e. the
                image height in pixels)
                """
                return pointToList(Atspi.Image.get_image_size(self.obj))

        def get_imageDescription(self):
                return Atspi.Image.get_image_description(self.obj)
        _imageDescriptionDoc = \
                """
                A UTF-8 string providing a textual description of what is visually
                depicted in the image.
                """
        imageDescription = property(fget=get_imageDescription, doc=_imageDescriptionDoc)

        def get_imageLocale(self):
                return Atspi.Image.get_image_local(self.obj)
        _imageLocaleDoc = \
                """
                A string corresponding to the POSIX LC_MESSAGES locale used by
                the imageDescription.
                """
        imageLocale = property(fget=get_imageLocale, doc=_imageLocaleDoc)

#END----------------------------------------------------------------------------
