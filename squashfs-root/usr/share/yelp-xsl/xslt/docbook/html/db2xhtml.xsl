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
                xmlns="http://www.w3.org/1999/xhtml"
                version="1.0">

<!--!!==========================================================================
DocBook to XHTML
Transform DocBook to XHTML.
:Revision:version="3.8" date="2012-11-05" status="final"

This top-level stylesheet includes all the necessary stylesheets to transform
DocBook documents into XHTML. This stylesheet sets the parameter
@{db.chunk.extension}.
-->

<xsl:import href="../../common/l10n.xsl"/>
<xsl:import href="../../common/color.xsl"/>
<xsl:import href="../../common/icons.xsl"/>
<xsl:import href="../../common/html.xsl"/>
<xsl:import href="../../common/utils.xsl"/>

<xsl:import href="../common/db-chunk.xsl"/>
<xsl:import href="../common/db-common.xsl"/>
<xsl:import href="../common/db-profile.xsl"/>
<xsl:import href="../common/db-title.xsl"/>
<xsl:import href="../common/db-xref.xsl"/>

<xsl:param name="db.chunk.extension" select="$html.extension"/>
<xsl:param name="db.profile.outputformat" select="'html;xhtml'"/>

<xsl:include href="db2html-bibliography.xsl"/>
<xsl:include href="db2html-block.xsl"/>
<xsl:include href="db2html-callout.xsl"/>
<xsl:include href="db2html-classsynopsis.xsl"/>
<xsl:include href="db2html-cmdsynopsis.xsl"/>
<xsl:include href="db2html-css.xsl"/>
<xsl:include href="db2html-division.xsl"/>
<xsl:include href="db2html-ebnf.xsl"/>
<xsl:include href="db2html-funcsynopsis.xsl"/>
<xsl:include href="db2html-index.xsl"/>
<xsl:include href="db2html-inline.xsl"/>
<xsl:include href="db2html-links.xsl"/>
<xsl:include href="db2html-math.xsl"/>
<xsl:include href="db2html-media.xsl"/>
<xsl:include href="db2html-list.xsl"/>
<xsl:include href="db2html-refentry.xsl"/>
<xsl:include href="db2html-suppressed.xsl"/>
<xsl:include href="db2html-table.xsl"/>
<xsl:include href="db2html-xref.xsl"/>
<xsl:include href="db2html-footnote.xsl"/>

<!--#! db2html-suppressed -->

</xsl:stylesheet>
