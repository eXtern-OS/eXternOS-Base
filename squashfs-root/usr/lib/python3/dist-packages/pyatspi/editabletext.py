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

from pyatspi.text import *
from gi.repository import Atspi
from pyatspi.utils import *

__all__ = [
           "EditableText",
          ]

#------------------------------------------------------------------------------

class EditableText(Text):
        """
        Derived from interface Text, EditableText provides methods for
        modifying textual content of components which support editing.
        EditableText also interacts with the system clipboard via copyText,
        cutText, and pasteText.
        """

        def copyText(self, start, end):
                """
                Copy a range of text into the system clipboard. 
                @param : startPos
                the character offset of the first character in the range of text
                being copied. 
                @param : endPos
                the offset of the first character past the end of the range of
                text being copied.
                """
                return Atspi.EditableText.copy_text(self.obj, start, end)

        def cutText(self, start, end):
                """
                Excise a range of text from a Text object, copying it into the
                system clipboard. 
                @param : startPos
                the character offset of the first character in the range of text
                being cut. 
                @param : endPos
                the offset of the first character past the end of the range of
                text being cut. 
                @return True if the text was successfully cut, False otherwise.
                """
                return Atspi.EditableText.cut_text(self.obj, start, end)

        def deleteText(self, start, end):
                """
                Excise a range of text from a Text object without copying it
                into the system clipboard. 
                @param : startPos
                the character offset of the first character in the range of text
                being deleted. 
                @param : endPos
                the offset of the first character past the end of the range of
                text being deleted. 
                @return True if the text was successfully deleted, False otherwise.
                """
                return Atspi.EditableText.delete_text(self.obj, start, end)

        def insertText(self, position, text, length):
                """
                Insert new text contents into an existing text object at a given
                location, while retaining the old contents. 
                @param : position
                the character offset into the Text implementor's content at which
                the new content will be inserted. 
                @param : text
                a UTF-8 string of which length characters will be inserted into
                the text object's text buffer. 
                @param : length
                the number of characters of text to insert. If the character
                count of text is less than or equal to length, the entire contents
                of text will be inserted.
                @return True if the text content was successfully inserted, False
                otherwise.
                """
                return Atspi.EditableText.insert_text(self.obj, position, text, length)

        def pasteText(self, position):
                """
                Copy the text contents of the system clipboard, if any, into
                a Text object, inserting it at a particular character offset.
                @param : position
                the character offset before which the text will be inserted.
                @return True if the text was successfully pasted into the Text
                object, False otherwise.
                """
                return Atspi.EditableText.paste_text(self.obj, position)

        def setTextContents(self, contents):
                """
                Replace the text contents with a new string, discarding the old
                contents.
                @param : newContents
                a UTF-8 string with which the text object's contents will be
                replaced. 
                @return True if the text content was successfully changed, False
                otherwise.
                """
                return Atspi.EditableText.set_text_contents(self.obj, contents)

#END----------------------------------------------------------------------------
