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
                xmlns:mal="http://projectmallard.org/1.0/"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal"
                version="1.0">


<!--!!==========================================================================
Mallard to XHTML
Transform Mallard to XHTML.
:Revision:version="3.8" date="2012-11-05" status="final"

This top-level stylesheet includes all the necessary stylesheets to transform
Mallard documents into XHTML. This stylesheet sets the parameters
@{mal.if.target}, @{mal.if.features}, @{mal.if.maybe}, @{mal.link.extension},
and @{ttml.features}.
-->

<xsl:import href="../../common/l10n.xsl"/>
<xsl:import href="../../common/color.xsl"/>
<xsl:import href="../../common/icons.xsl"/>
<xsl:import href="../../common/html.xsl"/>
<xsl:import href="../../common/ttml.xsl"/>
<xsl:import href="../../common/utils.xsl"/>

<xsl:import href="../common/mal-gloss.xsl"/>
<xsl:import href="../common/mal-if.xsl"/>
<xsl:import href="../common/mal-link.xsl"/>

<xsl:param name="ttml.features" select="'
http://www.w3.org/ns/ttml/feature/#content
http://www.w3.org/ns/ttml/feature/#core
http://www.w3.org/ns/ttml/feature/#nested-div
http://www.w3.org/ns/ttml/feature/#nested-span
http://www.w3.org/ns/ttml/feature/#presentation
http://www.w3.org/ns/ttml/feature/#profile
http://www.w3.org/ns/ttml/feature/#structure
http://www.w3.org/ns/ttml/feature/#time-offset
http://www.w3.org/ns/ttml/feature/#timing
'"/>
<xsl:param name="mal.if.target" select="'target:html target:xhtml'"/>
<xsl:param name="mal.if.features" select="concat('
mallard:1.0
', $ttml.features)"/>
<xsl:param name="mal.if.maybe" select="'target:mobile'"/>
<xsl:param name="mal.link.extension" select="$html.extension"/>

<xsl:include href="mal2html-api.xsl"/>
<xsl:include href="mal2html-block.xsl"/>
<xsl:include href="mal2html-facets.xsl"/>
<xsl:include href="mal2html-gloss.xsl"/>
<xsl:include href="mal2html-inline.xsl"/>
<xsl:include href="mal2html-links.xsl"/>
<xsl:include href="mal2html-list.xsl"/>
<xsl:include href="mal2html-math.xsl"/>
<xsl:include href="mal2html-media.xsl"/>
<xsl:include href="mal2html-page.xsl"/>
<xsl:include href="mal2html-svg.xsl"/>
<xsl:include href="mal2html-table.xsl"/>
<xsl:include href="mal2html-ui.xsl"/>


</xsl:stylesheet>
