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
                xmlns:set="http://exslt.org/sets"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db set"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Links
:Revision:version="3.4" date="2011-11-08" status="final"

This stylesheet contains templates to handle implicit automatic links.
-->


<!--**==========================================================================
db2html.links.linktrail
Generate links to pages from ancestor elements.
:Revision:version="3.20" date="2015-09-15" status="final"
$node: The element to generate links for.

This template outputs a trail of links for the ancestor pages of ${node}. If
${node} has no ancestors, then it calls *{html.linktrails.empty} instead. This
template calls *{html.linktrails.prefix} before the first link, passing ${node}
as that template's #{node} parameter.
-->
<xsl:template name="db2html.links.linktrail">
  <xsl:param name="node" select="."/>
  <xsl:variable name="direction">
    <xsl:call-template name="l10n.direction"/>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$node/ancestor::*">
    <div class="trails" role="navigation">
      <div class="trail">
        <xsl:call-template name="html.linktrails.prefix">
          <xsl:with-param name="node" select="$node"/>
        </xsl:call-template>
        <!-- The parens put the nodes back in document order -->
        <xsl:for-each select="($node/ancestor::*)">
          <a class="trail">
            <xsl:attribute name="href">
              <xsl:call-template name="db.xref.target">
                <xsl:with-param name="linkend" select="@id | @xml:id"/>
                <xsl:with-param name="target" select="."/>
                <xsl:with-param name="is_chunk" select="true()"/>
              </xsl:call-template>
            </xsl:attribute>
            <xsl:attribute name="title">
              <xsl:call-template name="db.xref.tooltip">
                <xsl:with-param name="linkend" select="@id | @xml:id"/>
                <xsl:with-param name="target" select="."/>
              </xsl:call-template>
            </xsl:attribute>
            <xsl:call-template name="db.titleabbrev">
              <xsl:with-param name="node" select="."/>
            </xsl:call-template>
          </a>
          <xsl:choose>
            <xsl:when test="$direction = 'rtl'">
              <xsl:text>&#x200F;&#x00A0;» &#x200F;</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:text>&#x00A0;» </xsl:text>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:for-each>
      </div>
    </div>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="html.linktrails.empty">
        <xsl:with-param name="node" select="$node"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db2html.links.next
Output links to the previous and next pages.
:Revision:version="3.4" date="2011-11-08" status="final"
$node: The element to generate links for.
$depth_of_chunk: The depth of the containing chunk in the document.

This template outputs links to the previous and next pages, if they exist. It
calls *{db.chunk.chunk-id.axis} to find the previous and next pages. The block
containing the links is end-floated by default. The links use the text "Previous"
and "Next", although the actual page titles are used for tooltips.
-->
<xsl:template name="db2html.links.next">
  <xsl:param name="node" select="."/>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:param>
  <xsl:variable name="prev_id">
    <xsl:choose>
      <xsl:when test="$depth_of_chunk = 0"/>
      <xsl:otherwise>
        <xsl:call-template name="db.chunk.chunk-id.axis">
          <xsl:with-param name="node" select="$node"/>
          <xsl:with-param name="axis" select="'previous'"/>
          <xsl:with-param name="depth_in_chunk" select="0"/>
          <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="next_id">
    <xsl:call-template name="db.chunk.chunk-id.axis">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="axis" select="'next'"/>
      <xsl:with-param name="depth_in_chunk" select="0"/>
      <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:variable name="prev_node" select="key('db.id.key', $prev_id)"/>
  <xsl:variable name="next_node" select="key('db.id.key', $next_id)"/>
  <div class="links nextlinks">
    <xsl:if test="$prev_id != ''">
      <a class="nextlinks-prev">
        <xsl:attribute name="href">
          <xsl:call-template name="db.xref.target">
            <xsl:with-param name="linkend" select="$prev_id"/>
            <xsl:with-param name="target" select="$prev_node"/>
            <xsl:with-param name="is_chunk" select="true()"/>
          </xsl:call-template>
        </xsl:attribute>
        <xsl:attribute name="title">
          <xsl:call-template name="db.xref.tooltip">
            <xsl:with-param name="linkend" select="$prev_id"/>
            <xsl:with-param name="target" select="$prev_node"/>
          </xsl:call-template>
        </xsl:attribute>
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="'Previous'"/>
        </xsl:call-template>
      </a>
    </xsl:if>
    <xsl:if test="$next_id != ''">
      <a class="nextlinks-next">
        <xsl:attribute name="href">
          <xsl:call-template name="db.xref.target">
            <xsl:with-param name="linkend" select="$next_id"/>
            <xsl:with-param name="is_chunk" select="true()"/>
          </xsl:call-template>
        </xsl:attribute>
        <xsl:attribute name="title">
          <xsl:call-template name="db.xref.tooltip">
            <xsl:with-param name="linkend" select="$next_id"/>
            <xsl:with-param name="target"  select="$next_node"/>
          </xsl:call-template>
        </xsl:attribute>
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="'Next'"/>
        </xsl:call-template>
      </a>
    </xsl:if>
  </div>
</xsl:template>


<!--**==========================================================================
db2html.links.section
Output links to subsections.
:Revision:version="3.4" date="2011-11-08" status="final"
$node: The element to generate links for.
$divisions: The division-level child elements of ${node} to link to.

This template outputs links to the child division-level elements of ${node},
whether or not they are chunked.
-->
<xsl:template name="db2html.links.section">
  <xsl:param name="node" select="."/>
  <xsl:param name="divisions" select="/false"/>
  <xsl:if test="$divisions">
    <div class="links sectionlinks" role="navigation">
      <ul>
        <xsl:for-each select="$divisions">
          <li class="links">
            <xsl:call-template name="db2html.xref">
              <xsl:with-param name="linkend" select="@id | @xml:id"/>
              <xsl:with-param name="target" select="."/>
              <xsl:with-param name="xrefstyle" select="'role:titleabbrev'"/>
            </xsl:call-template>
          </li>
        </xsl:for-each>
      </ul>
    </div>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
