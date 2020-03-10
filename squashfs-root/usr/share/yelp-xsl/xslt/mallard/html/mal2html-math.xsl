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
                xmlns:mml="http://www.w3.org/1998/Math/MathML"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal mml xlink"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - MathML
Handle MathML in Mallard documents.
:Revision: version="3.8" date="2012-11-13" status="final"

This stylesheet matches embedded MathML in %{mal2html.block.mode} and
%{mal2html.inline.mode} and processes it in %{mal2html.math.mode}. The
matched templates for the #{mml:math} element automatically set the
#{display} attribute based on whether the element is in block or inline
context.
-->


<!--%%==========================================================================
mal2html.math.mode
Output MathML and handle Mallard extensions.
:Revision: version="3.8" date="2012-11-13" status="final"

This mode is used for processing MathML embedded into Mallard documents. For
most types of MathML content, it simply copies the input directly, except it
outputs the MathML in a way that allows the namespace to stripped for non-XML
output. It checks for Mallard linking using the #{mal:xref} attribute and
transforms this to a MathML #{href} attribute. It also converts #{xlink:href}
attributes from MathML 2 to #{href} attributes for MathML 3.
-->
<xsl:template mode="mal2html.math.mode" match="mml:*">
  <xsl:element name="{local-name(.)}" namespace="{$html.mathml.namespace}">
    <xsl:for-each select="@*[name(.) != 'href']">
      <xsl:copy-of select="."/>
    </xsl:for-each>
    <xsl:choose>
      <xsl:when test="@mal:xref">
        <xsl:attribute name="href">
          <xsl:call-template name="mal.link.target">
            <xsl:with-param name="node" select="."/>
            <xsl:with-param name="xref" select="@mal:xref"/>
          </xsl:call-template>
        </xsl:attribute>
      </xsl:when>
      <xsl:when test="@href">
        <xsl:copy-of select="@href"/>
      </xsl:when>
      <xsl:when test="@xlink:href">
        <xsl:attribute name="href">
          <xsl:value-of select="@xlink:href"/>
        </xsl:attribute>
      </xsl:when>
    </xsl:choose>
    <xsl:apply-templates mode="mal2html.math.mode"/>
  </xsl:element>
</xsl:template>

<xsl:template mode="mal2html.math.mode" match="text()">
  <xsl:value-of select="."/>
</xsl:template>

<xsl:template mode="mal2html.math.mode" match="*"/>

<xsl:template mode="mal2html.block.mode" match="mml:math">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:attribute name="class">
      <xsl:text>math</xsl:text>
      <xsl:if test="$if != 'true'">
        <xsl:text> if-if </xsl:text>
        <xsl:value-of select="$if"/>
      </xsl:if>
    </xsl:attribute>
    <xsl:element name="math" namespace="{$html.mathml.namespace}">
      <xsl:for-each select="@*[name(.) != 'display']
                              [not(starts-with(namespace-uri(.), 'http://projectmallard.org/'))]">
        <xsl:copy-of select="."/>
      </xsl:for-each>
      <xsl:attribute name="display">
        <xsl:value-of select="'block'"/>
      </xsl:attribute>
      <xsl:apply-templates mode="mal2html.math.mode"/>
    </xsl:element>
  </div>
</xsl:if>
</xsl:template>

<xsl:template mode="mal2html.inline.mode" match="mml:math">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'math'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:element name="math" namespace="{$html.mathml.namespace}">
      <xsl:for-each select="@*[name(.) != 'display']
                              [not(starts-with(namespace-uri(.), 'http://projectmallard.org/'))]">
        <xsl:copy-of select="."/>
      </xsl:for-each>
      <xsl:attribute name="display">
        <xsl:value-of select="'inline'"/>
      </xsl:attribute>
      <xsl:apply-templates mode="mal2html.math.mode"/>
    </xsl:element>
  </span>
</xsl:template>

</xsl:stylesheet>
