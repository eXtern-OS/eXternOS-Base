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
                xmlns:e="http://projectmallard.org/experimental/"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal e"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - Inlines
Handle simple Mallard inline elements.
:Revision:version="3.8" date="2012-11-13" status="final"

This stylesheet contains templates to handle most Mallard inline elements.
It also maps %{mal.link.content.mode} to %{mal2html.inline.mode}.
-->

<xsl:template mode="mal.link.content.mode" match="*">
  <xsl:apply-templates mode="mal2html.inline.mode" select="."/>
</xsl:template>


<!--%%==========================================================================
mal2html.inline.mode
Process Mallard elements in inline mode.
:Revision:version="3.8" date="2012-11-13" status="final"

This mode is applied to elements in inline context. It is be called by certain
block elements and inline elements to process child content. Certain elements
may appear in both block and inline mode, and the processing expectations for
those elements is different depending on context.

Implementations of this mode should handle ubiquitous linking, text directionality,
and other common inline features. Note that the *{mal2html.span} template handles
these things automatically, and is suitable for most inline elements. You can use
the %{mal2html.inline.content.mode} to output special content for the child
elements.
-->
<xsl:template mode="mal2html.inline.mode" match="*">
  <xsl:message>
    <xsl:text>Unmatched inline element: </xsl:text>
    <xsl:value-of select="local-name(.)"/>
  </xsl:message>
  <xsl:apply-templates mode="mal2html.inline.mode"/>
</xsl:template>


<!--%%==========================================================================
mal2html.inline.content.mode
Output the contents of an inline element.
:Revision:version="1.0" date="2010-06-03" status="final"

This template outputs the contents of the inline element it matches. It is
usually called by *{mal2html.span} to allow elements like #{guiseq}, #{keyseq},
and #{link} output special inner contents while still using the generic wrapper
template.
-->
<xsl:template mode="mal2html.inline.content.mode" match="node()">
  <xsl:apply-templates mode="mal2html.inline.mode"/>
</xsl:template>


<!--**==========================================================================
mal2html.span
Output an HTML #{span} element.
:Revision:version="3.10" date="2013-07-10" status="final"
$node: The source element to output a #{span} for.
$class: An additional string to prepend to the #{class} attribute.

This template outputs an HTML #{span} element for a source element. It creates
a #{class} attribute automatically by passing the local name of ${node} and the
${class} parameter to *{html.class.attr}. To output the contents of ${node}, it
applies the mode %{mal2html.inline.content.mode} to ${node}.

This template automatically handles ubiquitous linking if ${node} contains
an #{xref} or #{href} attribute.
-->
<xsl:template name="mal2html.span">
  <xsl:param name="node" select="."/>
  <xsl:param name="class" select="''"/>
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="concat($class, ' ', local-name($node))"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:variable name="href">
      <xsl:if test="$node/@action | $node/@xref | $node/@href">
        <xsl:call-template name="mal.link.target">
          <xsl:with-param name="node" select="$node"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="normalize-space($href) != ''">
        <a>
          <xsl:attribute name="href">
            <xsl:value-of select="$href"/>
          </xsl:attribute>
          <xsl:attribute name="title">
            <xsl:call-template name="mal.link.tooltip">
              <xsl:with-param name="node" select="$node"/>
              <xsl:with-param name="role" select="$node/@role"/>
            </xsl:call-template>
          </xsl:attribute>
          <xsl:apply-templates mode="mal2html.inline.content.mode" select="$node"/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="mal2html.inline.content.mode" select="$node"/>
      </xsl:otherwise>
    </xsl:choose>
  </span>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = app = -->
<xsl:template mode="mal2html.inline.mode" match="mal:app">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = cmd = -->
<xsl:template mode="mal2html.inline.mode" match="mal:cmd">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = code = -->
<xsl:template mode="mal2html.inline.mode" match="mal:code">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = date = -->
<xsl:template mode="mal2html.inline.mode" match="mal:date">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = em = -->
<xsl:template mode="mal2html.inline.mode" match="mal:em">
  <xsl:call-template name="mal2html.span">
    <xsl:with-param name="class">
      <xsl:if test="contains(concat(' ', @style, ' '), ' strong ')">
        <xsl:text>em-bold</xsl:text>
      </xsl:if>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = file = -->
<xsl:template mode="mal2html.inline.mode" match="mal:file">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = gui = -->
<xsl:template mode="mal2html.inline.mode" match="mal:gui">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = guiseq = -->
<xsl:template mode="mal2html.inline.mode" match="mal:guiseq">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = guiseq % mal2html.inline.content.mode = -->
<xsl:template mode="mal2html.inline.content.mode" match="mal:guiseq">
  <xsl:variable name="arrow">
    <xsl:variable name="dir">
      <xsl:call-template name="l10n.direction">
        <xsl:with-param name="lang" select="ancestor-or-self::*[@xml:lang][1]/@xml:lang"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$dir = 'rtl'">
        <xsl:text>&#x00A0;&#x25C2; </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>&#x00A0;&#x25B8; </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:for-each select="mal:gui | text()[normalize-space(.) != '']">
    <xsl:if test="position() != 1">
      <xsl:value-of select="$arrow"/>
    </xsl:if>
    <xsl:apply-templates mode="mal2html.inline.mode" select="."/>
  </xsl:for-each>
</xsl:template>

<!-- = input = -->
<xsl:template mode="mal2html.inline.mode" match="mal:input">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = hi = -->
<xsl:template mode="mal2html.inline.mode" match="e:hi">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = key = -->
<xsl:template mode="mal2html.inline.mode" match="mal:key">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = key % mal2html.inline.content.mode = -->
<xsl:template mode="mal2html.inline.content.mode" match="mal:key">
  <kbd>
    <xsl:if test=". = 'Fn'">
      <xsl:attribute name="class">
        <xsl:text>key-Fn</xsl:text>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates mode="mal2html.inline.mode"/>
  </kbd>
</xsl:template>

<!-- = keyseq = -->
<xsl:template mode="mal2html.inline.mode" match="mal:keyseq">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = keyseq % mal2html.inline.content.mode = -->
<xsl:template mode="mal2html.inline.content.mode" match="mal:keyseq">
  <xsl:variable name="joinchar">
    <xsl:choose>
      <xsl:when test="@type = 'sequence'">
        <xsl:text> </xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' hyphen ')">
        <xsl:text>-</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>+</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:for-each select="* | text()[normalize-space(.) != '']">
    <xsl:if test="position() != 1">
      <xsl:value-of select="$joinchar"/>
    </xsl:if>
    <xsl:choose>
      <xsl:when test="./self::text()">
        <xsl:value-of select="normalize-space(.)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="mal2html.inline.mode" select="."/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:for-each>
</xsl:template>

<!-- = link = -->
<xsl:template mode="mal2html.inline.mode" match="mal:link">
  <xsl:call-template name="mal2html.span">
    <xsl:with-param name="class">
      <xsl:if test="contains(concat(' ', @style, ' '), ' button ')">
        <xsl:text>link-button</xsl:text>
      </xsl:if>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = link % mal2html.inline.content.mode = -->
<xsl:template mode="mal2html.inline.content.mode" match="mal:link">
  <xsl:choose>
    <xsl:when test="* or normalize-space(.) != ''">
      <xsl:apply-templates mode="mal2html.inline.mode"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="mal.link.content">
        <xsl:with-param name="role" select="@role"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = output = -->
<xsl:template mode="mal2html.inline.mode" match="mal:output">
  <xsl:variable name="style" select="concat(' ', @style, ' ')"/>
  <xsl:call-template name="mal2html.span">
    <xsl:with-param name="class">
      <xsl:choose>
        <xsl:when test="contains($style, ' error ')">
          <xsl:text>error</xsl:text>
        </xsl:when>
        <xsl:when test="contains($style, ' prompt ')">
          <xsl:text>prompt</xsl:text>
        </xsl:when>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = span = -->
<xsl:template mode="mal2html.inline.mode" match="mal:span">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = sys = -->
<xsl:template mode="mal2html.inline.mode" match="mal:sys">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = var = -->
<xsl:template mode="mal2html.inline.mode" match="mal:var">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<!-- = text() = -->
<xsl:template mode="mal2html.inline.mode" match="text()">
  <xsl:value-of select="."/>
</xsl:template>

</xsl:stylesheet>
