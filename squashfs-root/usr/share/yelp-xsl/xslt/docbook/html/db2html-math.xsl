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
                xmlns:db="http://docbook.org/ns/docbook"
                xmlns:mml="http://www.w3.org/1998/Math/MathML"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db mml xlink"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - MathML
Handle MathML in DocBook documents.
:Revision: version="3.8" date="2012-11-13" status="final"

This stylesheet matches embedded MathML and processes it in %{db2html.math.mode}.
The matched templates for the #{mml:math} element automatically set the #{display}
attribute based on whether the element is in block or inline context.
-->


<!--**==========================================================================
db2html.math.div
Output an HTML #{div} element and block-level MathML.
:Revision:version="3.8" date="2012-11-13" status="final"
$node: The #{mml:math} element to render.

This template creates an HTML #{div} element for a MathML #{mml:math} element,
then outputs MathML content. It sets the #{display} attribute on the output to
#{"block"} and applies %{db2html.math.mode} to the child content.
-->
<xsl:template name="db2html.math.div">
  <xsl:param name="node" select="."/>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="'math'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:element name="math" namespace="{$html.mathml.namespace}">
      <xsl:for-each select="$node/@*[name(.) != 'display']">
        <xsl:copy-of select="."/>
      </xsl:for-each>
      <xsl:attribute name="display">
        <xsl:value-of select="'block'"/>
      </xsl:attribute>
      <xsl:apply-templates mode="db2html.math.mode" select="$node/node()"/>
    </xsl:element>
  </div>
</xsl:template>


<!--**==========================================================================
db2html.math.span
Output an HTML #{span} element and inline MathML.
:Revision:version="3.8" date="2012-11-13" status="final"
$node: The #{mml:math} element to render.

This template creates an HTML #{span} element for a MathML #{mml:math} element,
then outputs MathML content. It sets the #{display} attribute on the output to
#{"inline"} and applies %{db2html.math.mode} to the child content.
-->
<xsl:template name="db2html.math.span">
  <xsl:param name="node" select="."/>
  <span class="math">
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:element name="math" namespace="{$html.mathml.namespace}">
      <xsl:for-each select="$node/@*[name(.) != 'display']">
        <xsl:copy-of select="."/>
      </xsl:for-each>
      <xsl:attribute name="display">
        <xsl:value-of select="'inline'"/>
      </xsl:attribute>
      <xsl:apply-templates mode="db2html.math.mode" select="$node/node()"/>
    </xsl:element>
  </span>
</xsl:template>


<!--%%==========================================================================
db2html.math.mode
Output MathML and handle Mallard extension.
:Revision: version="3.8" date="2012-11-13" status="final"

This mode is used for processing MathML embedded into DocBook documents. For
most types of MathML content, it simply copies the input directly, except it
outputs the MathML in a way that allows the namespace to stripped for non-XML
output. It converts #{xlink:href} attributes from MathML 2 to #{href} attributes
for MathML 3.
-->
<xsl:template mode="db2html.math.mode" match="mml:*">
  <xsl:element name="{local-name(.)}" namespace="{$html.mathml.namespace}">
    <xsl:for-each select="@*[name(.) != 'href']">
      <xsl:copy-of select="."/>
    </xsl:for-each>
    <xsl:choose>
      <xsl:when test="@href">
        <xsl:copy-of select="@href"/>
      </xsl:when>
      <xsl:when test="@xlink:href">
        <xsl:attribute name="href">
          <xsl:value-of select="@xlink:href"/>
        </xsl:attribute>
      </xsl:when>
    </xsl:choose>
    <xsl:apply-templates mode="db2html.math.mode"/>
  </xsl:element>
</xsl:template>

<xsl:template mode="db2html.math.mode" match="text()">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template mode="db2html.math.mode" match="*"/>


<!-- == Matched Templates == -->

<xsl:template match="equation/mml:math | informalequation/mml:math |
                     db:equation/mml:math | db:informalequation/mml:math">
  <xsl:call-template name="db2html.math.div"/>
</xsl:template>

<xsl:template match="inlineequation/mml:math | db:inlineequation/mml:math">
  <xsl:call-template name="db2html.math.span"/>
</xsl:template>

<xsl:template match="db:imagedata[@format='mathml']/mml:math">
  <xsl:variable name="media" select="(ancestor::db:mediaobject[1] |
                                      ancestor::db:inlinemediaobject[1]
                                     )[last()]"/>
  <xsl:choose>
    <xsl:when test="local-name($media) = 'inlinemediaobject'">
      <xsl:call-template name="db2html.math.span"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="db2html.math.div"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
