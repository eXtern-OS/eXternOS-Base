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
           "Hypertext",
          ]

#------------------------------------------------------------------------------

class Hypertext(interface):
        """
        An interface used for objects which implement linking between
        multiple resource or content locations, or multiple 'markers'
        within a single document. A Hypertext instance is associated
        with one or more Hyperlinks, which are associated with particular
        offsets within the Hypertext's included content.
        """

        def getLink(self, index):
                """
                Get one of the Hyperlinks associated with this Hypertext object,
                by index.
                @param : linkIndex
                an integer from 0 to getNLinks() - 1. 
                @return the Hyperlink in this Hypertext object.
                """
                return Atspi.Hypertext.get_link(self.obj, index)

        def getLinkIndex(self, character_index):
                """
                Get the hyperlink index, if any, associated with a particular
                character offset in the Hypertext object. For Hypertext implementors
                without textual content, all hyperlinks are associated with character
                offset '0'.
                @return the index of the Hyperlink associated with character
                offset characterIndex, or -1 if no Hyperlink is associated with
                that character offset.
                """
                return Atspi.Hypertext.get_link_index(self.obj, character_index)

        def getNLinks(self):
                """
                Query the hypertext object for the number of Hyperlinks it contains.
                @return the number of Hyperlinks associated with this Hypertext
                object, as a long integer.
                """
                return Atspi.Hypertext.get_n_links(self.obj)

#END----------------------------------------------------------------------------
