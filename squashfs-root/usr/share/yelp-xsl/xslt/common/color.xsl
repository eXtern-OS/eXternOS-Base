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
Colors
Specify common named colors to style output.
:Revision:version="1.0" date="2010-05-25" status="final"

This stylesheet provides a common interface to specify custom colors for
transformations to presentation-oreinted formats.  This allows similar
output for different types of input documents.
-->


<!--@@==========================================================================
color.background
The background color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the default background color.  Foreground colors
should be legible on this color.
-->
<xsl:param name="color.background" select="'#ffffff'"/>


<!--@@==========================================================================
color.link
The color of links.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the color for unvisited links.  It should be
legible on all background colors.
-->
<xsl:param name="color.link" select="'#204a87'"/>


<!--@@==========================================================================
color.link_visited
The color of visited links.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the color for visited links.  It should be
legible on all background colors.
-->
<xsl:param name="color.link_visited" select="'#5c3566'"/>


<!--@@==========================================================================
color.text
The normal text color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the default color for normal text.  It should be
legible on all background colors.
-->
<xsl:param name="color.text" select="'#000000'"/>


<!--@@==========================================================================
color.text_light
The light text color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the color for light text.  The light text
color is used to make bold headings and certain parenthetical text
less intense.  It should be legible on all background colors.
-->
<xsl:param name="color.text_light" select="'#2e3436'"/>


<!--@@==========================================================================
color.text_error
The error text color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the color for error text.  The error text
color is used to style error messages from command line sessions.
It should be legible on all background colors.
-->
<xsl:param name="color.text_error" select="'#a40000'"/>


<!--@@==========================================================================
color.blue_background
The blue background color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the blue background color.  The blue
background color may be used by certain types of block elements.
Foreground colors should be legible on this color.
-->
<xsl:param name="color.blue_background" select="'#e6f2ff'"/>


<!--@@==========================================================================
color.blue_border
The blue border color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the blue border color.  The blue
border color may be used by certain types of block elements.
-->
<xsl:param name="color.blue_border" select="'#729fcf'"/>


<!--@@==========================================================================
color.gray_background
The gray background color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the gray background color.  The gray
background color may be used by certain types of block elements.
Foreground colors should be legible on this color.
-->
<xsl:param name="color.gray_background" select="'#f3f3f0'"/>


<!--@@==========================================================================
color.dark_background
The dark gray background color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the dark gray background color.  The dark
gray background color may be used by certain types of block elements.
Foreground colors should be legible on this color.
-->
<xsl:param name="color.dark_background" select="'#e5e5e3'"/>


<!--@@==========================================================================
color.gray_border
The gray border color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the gray border color.  The gray
border color may be used by certain types of block elements.
-->
<xsl:param name="color.gray_border" select="'#babdb6'"/>


<!--@@==========================================================================
color.red_background
The red background color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the red background color.  The red
background color may be used by certain types of block elements.
Foreground colors should be legible on this color.
-->
<xsl:param name="color.red_background" select="'#ffdede'"/>


<!--@@==========================================================================
color.red_border
The red border color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the red border color.  The red
border color may be used by certain types of block elements.
-->
<xsl:param name="color.red_border" select="'#ef2929'"/>


<!--@@==========================================================================
color.yellow_background
The yellow background color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the yellow background color.  The yellow
background color may be used by certain types of block elements.
Foreground colors should be legible on this color.
-->
<xsl:param name="color.yellow_background" select="'#fffacc'"/>


<!--@@==========================================================================
color.yellow_border
The yellow border color.
:Revision:version="1.0" date="2010-05-25" status="final"

This parameter specifies the yellow border color.  The yellow
border color may be used by certain types of block elements.
-->
<xsl:param name="color.yellow_border" select="'#edd400'"/>


</xsl:stylesheet>
