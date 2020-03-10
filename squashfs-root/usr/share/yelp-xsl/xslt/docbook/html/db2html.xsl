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
                xmlns:html="http://www.w3.org/1999/xhtml"
                xmlns:mml="http://www.w3.org/1998/Math/MathML"
                exclude-result-prefixes="html mml"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML
Transform DocBook to HTML.
:Revision:version="3.8" date="2012-11-05" status="final"

This top-level stylesheet includes all the necessary stylesheets to transform
DocBook documents into HTML. It imports !{db2xhtml}, overrides parameters, and
sets a namespace alias to output non-XML HTML. This stylesheet sets
@{html.xhtml} to #{false}.
-->

<xsl:import href="db2xhtml.xsl"><?pass?></xsl:import>

<xsl:param name="html.xhtml" select="false()"/>
<xsl:param name="db.profile.outputformat" select="'html'"/>

<xsl:namespace-alias stylesheet-prefix="html" result-prefix="#default"/>
<xsl:namespace-alias stylesheet-prefix="mml" result-prefix="#default"/>

</xsl:stylesheet>
