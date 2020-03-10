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
from pyatspi.atspienum import *
from pyatspi.utils import *
from pyatspi.interface import *


__all__ = [
           "Text",
           "TEXT_BOUNDARY_TYPE",
           "TEXT_BOUNDARY_CHAR",
           "TEXT_BOUNDARY_WORD_START",
           "TEXT_BOUNDARY_WORD_END",
           "TEXT_BOUNDARY_SENTENCE_START",
           "TEXT_BOUNDARY_SENTENCE_END",
           "TEXT_BOUNDARY_LINE_START",
           "TEXT_BOUNDARY_LINE_END",
           "TEXT_CLIP_TYPE",
           "TEXT_CLIP_NONE",
           "TEXT_CLIP_MIN",
           "TEXT_CLIP_MAX",
           "TEXT_CLIP_BOTH",
           "TEXT_GRANULARITY_CHAR",
           "TEXT_GRANULARITY_WORD",
           "TEXT_GRANULARITY_SENTENCE",
           "TEXT_GRANULARITY_LINE",
           "TEXT_GRANULARITY_PARAGRAPH",
          ]

#------------------------------------------------------------------------------

class TEXT_BOUNDARY_TYPE(AtspiEnum):
        _enum_lookup = {
                0:'TEXT_BOUNDARY_CHAR',
                1:'TEXT_BOUNDARY_WORD_START',
                2:'TEXT_BOUNDARY_WORD_END',
                3:'TEXT_BOUNDARY_SENTENCE_START',
                4:'TEXT_BOUNDARY_SENTENCE_END',
                5:'TEXT_BOUNDARY_LINE_START',
                6:'TEXT_BOUNDARY_LINE_END',
        }

TEXT_BOUNDARY_CHAR = TEXT_BOUNDARY_TYPE(0)
TEXT_BOUNDARY_LINE_END = TEXT_BOUNDARY_TYPE(6)
TEXT_BOUNDARY_LINE_START = TEXT_BOUNDARY_TYPE(5)
TEXT_BOUNDARY_SENTENCE_END = TEXT_BOUNDARY_TYPE(4)
TEXT_BOUNDARY_SENTENCE_START = TEXT_BOUNDARY_TYPE(3)
TEXT_BOUNDARY_WORD_END = TEXT_BOUNDARY_TYPE(2)
TEXT_BOUNDARY_WORD_START = TEXT_BOUNDARY_TYPE(1)

#------------------------------------------------------------------------------

class TEXT_CLIP_TYPE(AtspiEnum):
        _enum_lookup = {
                0:'TEXT_CLIP_NONE',
                1:'TEXT_CLIP_MIN',
                2:'TEXT_CLIP_MAX',
                3:'TEXT_CLIP_BOTH',
        }

TEXT_CLIP_BOTH = TEXT_CLIP_TYPE(3)
TEXT_CLIP_MAX = TEXT_CLIP_TYPE(2)
TEXT_CLIP_MIN = TEXT_CLIP_TYPE(1)
TEXT_CLIP_NONE = TEXT_CLIP_TYPE(0)

#------------------------------------------------------------------------------

class TEXT_GRANULARITY_TYPE(AtspiEnum):
        _enum_lookup = {
                0:'TEXT_GRANULARITY_CHAR',
                1:'TEXT_GRANULARITY_WORD',
                2:'TEXT_GRANULARITY_SENTENCE',
                3:'TEXT_GRANULARITY_LINE',
                4:'TEXT_GRANULARITY_PARAGRAPH',
        }

TEXT_GRANULARITY_CHAR = TEXT_GRANULARITY_TYPE(0)
TEXT_GRANULARITY_WORD = TEXT_GRANULARITY_TYPE(1)
TEXT_GRANULARITY_SENTENCE = TEXT_GRANULARITY_TYPE(2)
TEXT_GRANULARITY_LINE = TEXT_GRANULARITY_TYPE(3)
TEXT_GRANULARITY_PARAGRAPH = TEXT_GRANULARITY_TYPE(4)

#------------------------------------------------------------------------------

class Text(interface):
        """
        The text interface should be implemented by objects which place
        textual information onscreen as character strings or glyphs.
        The text interface allows access to textual content, including
        display attributes and semantic hints associated with runs of
        text, and access to bounding box information for glyphs and substrings.
        It also allows portions of textual content to be selected, if
        the object's StateSet includes STATE_SELECTABLE_TEXT.
        In some cases a Text object may have, as its content, an empty
        string. In particular this can occur in the case of Hypertext
        objects which do not display explicitly textual information onscreen,
        as Hypertext is derived from the Text interface. 
        Typographic and semantic attributes of onscreen textual content,
        for instance typeface, weight, language, and such qualities as
        'emphasis' or 'blockquote', are represented as text attributes.
        Contiguous sequences of characters over which these attributes
        are unchanged are referred to as "attribute runs", and are available
        via Text::getAttributeRun. Where possible, implementing clients
        will report textual attributes which are the same over the entire
        text object, for instance those inherited from a default or document-scope
        style, via getDefaultAttributes instead of reporting them explicitly
        for each character. Therefore, for any span of text, the attributes
        in effect are the union of the set returned by Text::getDefaultAttributes,
        and the set returned at a particular character offset via Text::getAttributeRun.
        """

        def addSelection(self, index):
                """
                The result of calling addSelection on objects which already have
                one selection present, and which do not include STATE_MULTISELECTABLE,
                is undefined, other than the return value. 
                @return True of the selection was successfully added, False otherwise.
                Selection may fail if the object does not support selection of
                text (see STATE_SELECTABLE_TEXT), if the object does not support
                multiple selections and a selection is already defined, or for
                other reasons (for instance if the user does not have permission
                to copy the text into the relevant selection buffer).
                """
                return Atspi.Text.add_selection(self.obj, index)

        def getAttributeRun(self, offset, includeDefaults=True):
                """
                Query a particular text object for the text attributes defined
                at a given offset, obtaining the start and end of the "attribute
                run" over which these attributes are currently invariant. Text
                attributes are those presentational, typographic, or semantic
                attributes or qualitites which apply to a range of text specifyable
                by starting and ending offsets. Attributes relevant to localization
                should be provided in accordance with the w3c "Internationalization
                and Localization Markup Requirements", http://www.w3.org/TR/2005/WD-itsreq-20051122/
                Other text attributes should choose their names and value semantics
                in accordance with relevant standards such as CSS level 2 (http://www.w3.org/TR/1998/REC-CSS2-19980512),
                XHTML 1.0 (http://www.w3.org/TR/2002/REC-xhtml1-20020801), and
                WICD (http://www.w3.org/TR/2005/WD-WICD-20051121/). Those attributes
                from the aforementioned specifications and recommendations which
                do not concern typographic, presentational, or semantic aspects
                of text should be exposed via the more general Accessible::getAttributes()
                API (if at all).
                For example, CSS attributes which should be exposed on text (either
                as default attributes, or as explicitly-set attributes when non-default
                values are specified in the content view) include the Font attributes
                (i.e. "css2:font-weight", "css2:font-style"), the "css2:color"
                and "css2:background-color" attributes, and "css2:text-decoration"
                attribute.
                If includeDefaults is TRUE, then this AttributeSet should include
                the default attributes as well as those which are explicitly
                assigned to the attribute run in question. startOffset and endOffset
                will be back-filled to indicate the start and end of the attribute
                run which contains 'offset' - an attribute run is a contiguous
                section of text whose attributes are homogeneous. 
                @param : offset
                the offset of the character whose attributes will be reported.
                @param : startOffset
                backfilled with the starting offset of the character range over
                which all text attributes match those of offset, i.e. the start
                of the homogeneous attribute run including offset. 
                @param : endOffset
                backfilled with the offset of the first character past the character
                range over which all text attributes match those of offset, i.e.
                the character immediately after the homogeneous attribute run
                including offset. 
                @param : includeDefaults
                if False, the call should only return those attributes which
                are explicitly set on the current attribute run, omitting any
                attributes which are inherited from the default values. See also
                Text::getDefaultAttributes.
                @return the AttributeSet defined at offset, optionally including
                the 'default' attributes.
                """
                [attrs, startOffset, endOffset] = Atspi.Text.get_attribute_run(self.obj, offset, includeDefaults)
                dict = [key + ':' + value for key, value in attrs.items()]
                return [dict, startOffset, endOffset]

        def getAttributeValue(self, offset, attributeName):
                """
                Get the string value of a named attribute at a given offset,
                if defined. 
                @param : offset
                the offset of the character for which the attribute run is to
                be obtained. 
                @param : attributeName
                the name of the attribute for which the value is to be returned,
                if defined. 
                @param : startOffset
                back-filled with the offset of the first character in the attribute
                run containing the character at offset. 
                @param : endOffset
                back-filled with the offset of the first character past the end
                of the attribute run containing the character at offset. 
                @param : defined
                back-filled with True if the attributeName has a defined value
                at offset, False otherwise. 
                @return the value of attribute (name-value pair) corresponding
                to "name", if defined.
                """
                return Atspi.Text.get_text_attribute_value(self.obj, offset, attributeName)

        def getAttributes(self, offset):
                """
                getAttributes is deprecated in favor of getAttributeRun. 
                @return the attributes at offset, as a semicolon-delimited set
                of colon-delimited name-value pairs.
                """
                [attrs, startOffset, endOffset] = Atspi.Text.get_text_attributes(self.obj, offset)
                arr = [key + ':' + value for key, value in attrs.items()]
                str = ';'.join (arr)
                return [str, startOffset, endOffset]

        def getBoundedRanges(self, x, y, width, height, coordType, xClipType, yClipType):
                """
                Return the text content within a bounding box, as a list of Range
                structures. Depending on the TEXT_CLIP_TYPE parameters, glyphs
                which are clipped by the bounding box (i.e. which lie partially
                inside and partially outside it) may or may not be included in
                the ranges returned. 
                @param : x
                the minimum x ( i.e. leftmost) coordinate of the bounding box.
                @param : y
                the minimum y coordinate of the bounding box. 
                @param : width
                the horizontal size of the bounding box. The rightmost bound
                of the bounding box is (x + width); 
                @param : height
                the vertical size of the bounding box. The maximum y value of
                the bounding box is (y + height); 
                @param : coordType
                If 0, the above coordinates are interpreted as pixels relative
                to corner of the screen; if 1, the coordinates are interpreted
                as pixels relative to the corner of the containing toplevel window.
                @param : xClipType
                determines whether text which intersects the bounding box in
                the x direction is included. 
                @param : yClipType
                determines whether text which intersects the bounding box in
                the y direction is included.
                """
                return Atspi.Text.get_bounded_ranges(self.obj, x, y, width, height, coordType, xClipType, yClipType)

        def getCharacterAtOffset(self, offset):
                """
                @param : offset
                position
                @return an unsigned long integer whose value corresponds to the
                UCS-4 representation of the character at the specified text offset,
                or 0 if offset is out of range.
                """
                return Atspi.Text.get_character_at_offset(self.obj, offset)

        def getCharacterExtents(self, offset, coordType):
                """
                Obtain a the bounding box, as x, y, width, and height, of the
                character or glyph at a particular character offset in this object's
                text content. The coordinate system in which the results are
                reported is specified by coordType. If an onscreen glyph corresponds
                to multiple character offsets, for instance if the glyph is a
                ligature, the bounding box reported will include the entire glyph
                and therefore may apply to more than one character offset. 
                @param : offset
                the character offset of the character or glyph being queried.
                @param : coordType
                If 0, the results will be reported in screen coordinates, i.e.
                in pixels relative to the upper-left corner of the screen, with
                the x axis pointing right and the y axis pointing down. If 1,
                the results will be reported relative to the containing toplevel
                window, with the x axis pointing right and the y axis pointing
                down.
                """
                ret = Atspi.Text.get_character_extents(self.obj, offset, coordType)
                return rectToList(ret)

        def getDefaultAttributeSet(self):
                """
                Return an AttributeSet containing the text attributes which apply
                to all text in the object by virtue of the default settings of
                the document, view, or user agent; e.g. those attributes which
                are implied rather than explicitly applied to the text object.
                For instance, an object whose entire text content has been explicitly
                marked as 'bold' will report the 'bold' attribute via getAttributeRun(),
                whereas an object whose text weight is inspecified may report
                the default or implied text weight in the default AttributeSet.
                """
                return Atspi.Text.get_default_attributes(self.obj)

                ret = Atspi.Text.get_default_attribute_set(self.obj)
                return [key + ':' + value for key, value in ret.values()]

        def getDefaultAttributes(self):
                """
                Deprecated in favor of getDefaultAttributeSet. 
                @return the attributes which apply to the entire text content,
                but which were not explicitly specified by the content creator.
                """
                ret = Atspi.Text.get_default_attributes(self.obj)
                return ';'.join([key + ':' + value for key, value in ret.items()])

        def getNSelections(self):
                """
                Obtain the number of separate, contiguous selections in the current
                Text object. Text objects which do not implement selection of
                discontiguous text regions will always return '0' or '1'. Note
                that "contiguous" is defined by continuity of the offsets, i.e.
                a text 'selection' is defined by a start/end offset pair. In
                the case of bidirectional text, this means that a continguous
                selection may appear visually discontiguous, and vice-versa.
                @return the number of contiguous selections in the current Text
                object.
                """
                return Atspi.Text.get_n_selections(self.obj)

        def getOffsetAtPoint(self, x, y, coordType):
                """
                Get the offset of the character at a given onscreen coordinate.
                The coordinate system used to interpret x and y is determined
                by parameter coordType. 
                @param : x
                @param : y
                @param : coordType
                if 0, the input coordinates are interpreted relative to the entire
                screen, if 1, they are relative to the toplevel window containing
                this Text object. 
                @return the text offset (as an offset into the character array)
                of the glyph whose onscreen bounds contain the point x,y, or
                -1 if the point is outside the bounds of any glyph.
                """
                return Atspi.Text.get_offset_at_point(self.obj, x, y, coordType)

        def getRangeExtents(self, startOffset, endOffset, coordType):
                """
                Obtain the bounding box which entirely contains a given text
                range. Negative values may be returned for the bounding box parameters
                in the event that all or part of the text range is offscreen
                or not mapped to the screen. 
                @param : startOffset
                the offset of the first character in the specified range. 
                @param : endOffset
                the offset of the character immediately after the last character
                in the specified range. 
                @param : x
                an integer parameter which is back-filled with the minimum horizontal
                coordinate of the resulting bounding box. 
                @param : y
                an integer parameter which is back-filled with the minimum vertical
                coordinate of the resulting bounding box. 
                @param : width
                an integer parameter which is back-filled with the horizontal
                extent of the bounding box. 
                @param : height
                an integer parameter which is back-filled with the vertical extent
                of the bounding box. 
                @param : coordType
                If 0, the above coordinates are reported in pixels relative to
                corner of the screen; if 1, the coordinates are reported relative
                to the corner of the containing toplevel window.
                """
                ret = Atspi.Text.get_range_extents(self.obj, startOffset, endOffset, coordType)
                return rectToList(ret)

        def getSelection(self, selectionNum):
                """
                The result of calling getSelection with an out-of-range selectionNum
                (i.e. for a selection which does not exist) is not strictly defined,
                but should set endOffset equal to startOffset.
                @param : selectionNum
                indicates which of a set of non-contiguous selections to modify.
                @param : startOffset
                back-filled with the starting offset of the resulting substring,
                if one exists. 
                @param : endOffset
                back-filled with the offset of the character immediately following
                the resulting substring, if one exists. 
                """
                ret = Atspi.Text.get_selection(self.obj, selectionNum)
                return rangeToList(ret)

        def getText(self, startOffset, endOffset):
                """
                Obtain all or part of the onscreen textual content of a Text
                object. If endOffset is specified as "-1", then this method will
                return the entire onscreen textual contents of the Text object.
                @param : startOffset
                back-filled with the starting offset of the resulting substring,
                if one exists. 
                @param : endOffset
                back-filled with the offset of the character immediately following
                the resulting substring, if one exists. 
                @return the textual content of the current Text object beginning
                startOffset (inclusive) up to but not including the character
                at endOffset.
                """
                return Atspi.Text.get_text(self.obj, startOffset, endOffset)

        def getTextAfterOffset(self, offset, type):
                """
                Deprecated in favor of getStringAtOffset.
                Obtain a subset of the text content of an object which entirely
                follows offset, delimited by character, word, line, or sentence
                boundaries as specified by type. The starting and ending offsets
                of the resulting substring are returned in startOffset and endOffset.
                By definition, if such a substring exists, startOffset must be
                greater than offset. 
                @param : offset
                the offset from which the substring search begins, and which
                must lie before the returned substring. 
                @param : type
                the text-boundary delimiter which determines whether the returned
                text constitures a character, word, line, or sentence (and possibly
                attendant whitespace), and whether the start or ending of such
                a substring forms the boundary condition. 
                @param : startOffset
                back-filled with the starting offset of the resulting substring,
                if one exists. 
                @param : endOffset
                back-filled with the offset of the character immediately following
                the resulting substring, if one exists. 
                @return a string which is a substring of the text content of
                the object, delimited by the specified boundary condition.
                """
                ret = Atspi.Text.get_text_after_offset(self.obj, offset, type)
                return textRangeToList(ret)

        def getTextAtOffset(self, offset, type):
                """
                Deprecated in favor of getStringAtOffset.
                Obtain a subset of the text content of an object which includes
                the specified offset, delimited by character, word, line, or
                sentence boundaries as specified by type. The starting and ending
                offsets of the resulting substring are returned in startOffset
                and endOffset. 
                @param : offset
                the offset from which the substring search begins, and which
                must lie within the returned substring. 
                @param : type
                the text-boundary delimiter which determines whether the returned
                text constitures a character, word, line, or sentence (and possibly
                attendant whitespace), and whether the start or ending of such
                a substring forms the boundary condition. 
                @param : startOffset
                back-filled with the starting offset of the resulting substring,
                if one exists. 
                @param : endOffset
                back-filled with the offset of the character immediately following
                the resulting substring, if one exists. 
                @return a string which is a substring of the text content of
                the object, delimited by the specified boundary condition.
                """
                ret = Atspi.Text.get_text_at_offset(self.obj, offset, type)
                return textRangeToList(ret)

        def getTextBeforeOffset(self, offset, type):
                """
                Deprecated in favor of getStringAtOffset.
                Obtain a subset of the text content of an object which entirely
                precedes offset, delimited by character, word, line, or sentence
                boundaries as specified by type. The starting and ending offsets
                of the resulting substring are returned in startOffset and endOffset.
                By definition, if such a substring exists, endOffset is less
                than or equal to offset. 
                @param : offset
                the offset from which the substring search begins. 
                @param : type
                the text-boundary delimiter which determines whether the returned
                text constitures a character, word, line, or sentence (and possibly
                attendant whitespace), and whether the start or ending of such
                a substring forms the boundary condition. 
                @param : startOffset
                back-filled with the starting offset of the resulting substring,
                if one exists. 
                @param : endOffset
                back-filled with the offset of the character immediately following
                the resulting substring, if one exists. 
                @return a string which is a substring of the text content of
                the object, delimited by the specified boundary condition.
                """
                ret = Atspi.Text.get_text_before_offset(self.obj, offset, type)
                return textRangeToList(ret)

        def getStringAtOffset(self, offset, type):
                """
                Obtain a subset of the text content of an object which includes
                the specified offset, delimited by character, word, line, sentence
                or paragraph granularity as specified by type. The starting and ending
                offsets of the resulting substring are returned in startOffset
                and endOffset.
                @param : offset
                the offset from which the substring search begins, and which
                must lie within the returned substring.
                @param : type
                the text granularity which determines whether the  returned text
                constitures a character, word, line, sentence or paragraph (and
                possibly attendant  whitespace). For all of those cases, boundaries
                will always be defined from the start of the current substring to
                the start of the following one for the same granularity.
                @param : startOffset
                back-filled with the starting offset of the resulting substring,
                if one exists.
                @param : endOffset
                back-filled with the offset of the character immediately following
                the resulting substring, if one exists.
                @return a string which is a substring of the text content of
                the object, delimited by the specified text granularity.
                """
                ret = Atspi.Text.get_string_at_offset(self.obj, offset, type)
                return textRangeToList(ret)

        def removeSelection(self, selectionNum):
                """
                Deselect the text contained in the specified selectionNum, if
                such a selection exists, otherwise do nothing. Removal of a non-existant
                selectionNum has no effect. 
                @param : selectionNum
                indicates which of a set of non-contiguous selections to modify.
                @return True if the selection was successfully removed, False
                otherwise.
                """
                return Atspi.Text.remove_selection(self.obj, selectionNum)

        def setCaretOffset(self, offset):
                """
                Programmatically move the text caret (visible or virtual, as
                above) to a given position. 
                @param : offset
                a long int indicating the desired character offset. Not all implementations
                of Text will honor setCaretOffset requests, so the return value
                below should be checked by the client. 
                @return TRUE if the request was carried out, or FALSE if the
                caret could not be moved to the requested position.
                """
                return Atspi.Text.set_caret_offset(self.obj, offset)

        def setSelection(self, selectionNum, startOffset, endOffset):
                """
                Modify an existing selection's start or ending offset.
                Calling setSelection for a selectionNum that is not already defined
                has no effect. The result of calling setSelection with a selectionNum
                greater than 0 for objects that do not include STATE_MULTISELECTABLE
                is undefined. 
                @param : selectionNum
                indicates which of a set of non-contiguous selections to modify.
                @param : startOffset
                the new starting offset for the selection 
                @param : endOffset
                the new ending offset for the selection 
                @return True if the selection corresponding to selectionNum is
                successfully modified, False otherwise.
                """
                return Atspi.Text.set_selection(self.obj, selectionNum, startOffset, endOffset)

        def get_caretOffset(self):
                return Atspi.Text.get_caret_offset(self.obj)
        _caretOffsetDoc = \
                """
                The current offset of the text caret in the Text object. This
                caret may be virtual, e.g. non-visual and notional-only, but
                if an onscreen representation of the caret position is visible,
                it will correspond to this offset. The caret offset is given
                as a character offset, as opposed to a byte offset into a text
                buffer or a column offset.
                """
        caretOffset = property(fget=get_caretOffset, doc=_caretOffsetDoc)

        def get_characterCount(self):
                return Atspi.Text.get_character_count(self.obj)
        _characterCountDoc = \
                """
                The total current number of characters in the Text object, including
                whitespace and non-spacing characters.
                """
        characterCount = property(fget=get_characterCount, doc=_characterCountDoc)

def rangeToList(r):
        return (r.start_offset, r.end_offset)

def textRangeToList(r):
        return (r.content, r.start_offset, r.end_offset)
