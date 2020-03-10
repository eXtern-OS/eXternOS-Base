#Copyright (C) 2008 Codethink Ltd
#Copyright (C) 2010 Novell, Inc.

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
           "Document",
          ]

#------------------------------------------------------------------------------

class Document(interface):
        """
        Primarily a 'tagging' interface which indicates the start of
        document content in the Accessibility hierarchy. Accessible objects
        below the node implementing Document are normally assumed to
        be part of the document content. Attributes of Document are those
        attributes associated with the document as a whole. Objects that
        implement Document are normally expected to implement Collection
        as well.
        """

        def getAttributeValue(self, key):
                """
                Gets the value of a single attribute, if specified for the document
                as a whole.
                @param : attributename
                a string indicating the name of a specific attribute (name-value
                pair) being queried.
                @return a string corresponding to the value of the specified
                attribute, or an empty string if the attribute is unspecified
                for the object.
                """
                return Atspi.Document.get_document_attribute_value(self.obj, key)

        def getAttributes(self):
                """
                Gets all attributes specified for a document as a whole. For
                attributes which change within the document content, see Accessibility::Text::getAttributes
                instead.
                @return an AttributeSet containing the attributes of the document,
                as name-value pairs.
                """
                ret = Atspi.Document.get_document_attributes(self.obj)
                return [key + ':' + value for key, value in ret.items()]

        def getLocale(self):
                """
                Gets the locale associated with the document's content. e.g.
                the locale for LOCALE_TYPE_MESSAGES.
                @return a string compliant with the POSIX standard for locale
                description.
                """
                return Atspi.Document.get_locale(self.obj)

        def getCurrentPageNumber(self):
                """
                Gets the current page number associated with the document.
                @return a integer with the current page number. -1 if error
                or unknown.
                """
                return Atspi.Document.get_current_page_number(self.obj)

        def getPageCount(self):
                """
                Gets the page count of the document.
                @return a integer with the page count of the document.
                -1 if error or unknown.
                """
                return Atspi.Document.get_page_count(self.obj)

#END----------------------------------------------------------------------------
