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
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Footnotes

FIXME: Describe this module
-->


<!--**==========================================================================
db2html.footnote.link
Output a link to a footnote.
:Revision:version="3.4" date="2011-11-10" status="final"
$node: The #{footnote} element to process.

This templates outputs an inline link to the footnote displayed at the bottom
of the page.
-->
<xsl:template  match="footnote | db:footnote" name="db2html.footnote.link">
  <xsl:param name="node" select="."/>
  <xsl:variable name="anchor">
    <xsl:text>-noteref-</xsl:text>
    <xsl:choose>
      <xsl:when test="$node/@id">
        <xsl:value-of select="$node/@id"/>
      </xsl:when>
      <xsl:when test="$node/@xml:id">
        <xsl:value-of select="$node/@xml:id"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="generate-id($node)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="href">
    <xsl:text>#</xsl:text>
    <xsl:choose>
      <xsl:when test="$node/@id">
        <xsl:value-of select="$node/@id"/>
      </xsl:when>
      <xsl:when test="$node/@xml:id">
        <xsl:value-of select="$node/@xml:id"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>-note-</xsl:text>
        <xsl:value-of select="generate-id($node)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <sup class="footnote">
    <a class="footnote" href="{$href}" id="{$anchor}">
      <xsl:value-of select="count($node/preceding::footnote | $node/preceding::db:footnote) + 1"/>
    </a>
  </sup>
</xsl:template>


<!--**==========================================================================
db2html.footnote.note
Output a footnote.
:Revision:version="3.4" date="2011-11-10" status="final"
$node: The #{footnote} element to process.

This templates outputs the actual text of a footnote as a block-level element.
-->
<xsl:template name="db2html.footnote.note">
  <xsl:param name="node" select="."/>
  <xsl:variable name="anchor">
    <xsl:choose>
      <xsl:when test="$node/@id">
        <xsl:value-of select="$node/@id"/>
      </xsl:when>
      <xsl:when test="$node/@xml:id">
        <xsl:value-of select="$node/@xml:id"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>-note-</xsl:text>
        <xsl:value-of select="generate-id($node)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="href">
    <xsl:text>#</xsl:text>
    <xsl:text>-noteref-</xsl:text>
    <xsl:choose>
      <xsl:when test="$node/@id">
        <xsl:value-of select="$node/@id"/>
      </xsl:when>
      <xsl:when test="$node/@xml:id">
        <xsl:value-of select="$node/@xml:id"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="generate-id($node)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div id="{$anchor}">
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="'footnote'"/>
    </xsl:call-template>
    <a class="footnote" href="{$href}">
      <xsl:value-of select="count($node/preceding::footnote | $node/preceding::db:footnote) + 1"/>
    </a>
    <xsl:apply-templates select="$node/node()"/>
  </div>
</xsl:template>


<!--**==========================================================================
db2html.footnote.footer
Output all footnotes for a page.
:Revision:version="3.4" date="2011-11-10" status="final"
$node: The division-level element containing footnotes
$depth_of_chunk: The depth of the containing chunk in the document.

This template collects all #{footnote} elements under ${node} and outputs them
with *{db2html.footnote.note}. It checks if each footnote would be displayed on
a separate page by a child division-level element, and if so, it doesn't output
that footnote.
-->
<xsl:template name="db2html.footnote.footer">
  <xsl:param name="node" select="."/>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:variable name="notes" select="$node//footnote | $node//db:footnote" />
  <xsl:variable name="include">
    <xsl:for-each select="$notes">
      <xsl:variable name="depth">
        <xsl:call-template name="db.chunk.depth-of-chunk"/>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$depth = $depth_of_chunk">
          <xsl:text>y</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>x</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
  </xsl:variable>
  <xsl:if test="contains($include, 'y')">
    <div class="footnotes">
      <xsl:for-each select="$notes">
        <xsl:if test="substring($include, position(), 1) = 'y'">
          <xsl:call-template name="db2html.footnote.note">
            <xsl:with-param name="node" select="."/>
          </xsl:call-template>
        </xsl:if>
      </xsl:for-each>
    </div>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
