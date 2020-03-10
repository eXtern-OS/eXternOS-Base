<?xml version='1.0' encoding='UTF-8'?><!-- -*- indent-tabs-mode: nil -*- -->
<!--
This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License
along with this program; see the file COPYING.LGPL.  If not, see <http://www.gnu.org/licenses/>.
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

<!--!!==========================================================================
Icons
Specify common named icons to style output.
:Requires: l10n
:Revision:version="1.0" date="2010-05-25" status="final"

This stylesheet provides a common interface to specify icons for transformations
to presentation-oreinted formats. This allows similar output for different
types of input documents.
-->


<!--@@==========================================================================
icons.base_url
The default URL prefix for all icons.
:Revision:version="1.0" date="2010-01-26" status="final"

This parameter provides a default URL prefix. All icon locations in this
stylesheet reference files directly under this URL prefix by default. If
you override the individual icon parameters in this stylesheet, this parameter
has no effect. This parameter should end with a trailing slash.
-->
<xsl:param name="icons.base_url" select="''"/>


<!--@@==========================================================================
icons.size.note
The size of the note icons.
:Revision:version="1.0" date="2010-03-05" status="final"

This parameter specifies the size of the note icons. Use an integer giving
the width of the image files in pixels. Icons are assumed to be square, and
all note icons are assumed to have the same size.
-->
<xsl:param name="icons.size.note" select="24"/>


<!--@@==========================================================================
icons.note
The URL for the note icon.
:Revision:version="1.0" date="2010-05-03" status="final"

This parameter specifies the URL for the icon used for regular notes.
-->
<xsl:param name="icons.note"
           select="concat($icons.base_url, 'yelp-note.png')"/>


<!--@@==========================================================================
icons.note.bug
The URL for the bug note icon.
:Revision:version="1.0" date="2010-05-03" status="final"

This parameter specifies the URL for the icon used for bug notes.
-->
<xsl:param name="icons.note.bug"
           select="concat($icons.base_url, 'yelp-note-bug.png')"/>


<!--@@==========================================================================
icons.note.important
The URL for the important note icon.
:Revision:version="1.0" date="2010-05-03" status="final"

This parameter specifies the URL for the icon used for important notes.
-->
<xsl:param name="icons.note.important"
           select="concat($icons.base_url, 'yelp-note-important.png')"/>


<!--@@==========================================================================
icons.note.tip
The URL for the tip note icon.
:Revision:version="1.0" date="2010-05-03" status="final"

This parameter specifies the URL for the icon used for tip notes.
-->
<xsl:param name="icons.note.tip"
           select="concat($icons.base_url, 'yelp-note-tip.png')"/>


<!--@@==========================================================================
icons.note.warning
The URL for the warning note icon.
:Revision:version="1.0" date="2010-05-03" status="final"

This parameter specifies the URL for the icon used for warning notes.
-->
<xsl:param name="icons.note.warning"
           select="concat($icons.base_url, 'yelp-note-warning.png')"/>


<!--@@==========================================================================
icons.size.quote
The size of the quote icons.
:Revision:version="3.8" date="2012-09-29" status="final"

This parameter specifies the size of the block quote icon. Use an integer giving
the width of the image files in pixels. Icons are assumed to be square, and all
quote icons are assumed to have the same size.

As of version 3.8, there is no longer an actual image file for the quote icon.
Instead, a language-appropriate quotation character is placed in the margin.
This parameters still affects the size of that character.
-->
<xsl:param name="icons.size.quote" select="48"/>


</xsl:stylesheet>
