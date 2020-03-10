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
DocBook to HTML - Reference Pages
:Requires: db-chunk db-title db2html-inline db2html-division db2html-xref l10n

REMARK: Describe this module. Talk about refenty and friends
-->

<!--#% db2html.division.div.content.mode -->


<!-- == Matched Templates == -->

<!-- = citerefentry = -->
<xsl:template match="citerefentry | db:citerefentry">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>
<xsl:template match="citerefentry/refentrytitle | db:citerefentry/db:refentrytitle">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = manvolnum = -->
<xsl:template match="manvolnum | db:manvolnum">
  <xsl:text>(</xsl:text>
  <xsl:apply-templates select="node()"/>
  <xsl:text>)</xsl:text>
</xsl:template>

<!-- = refentry = -->
<xsl:template match="refentry | db:refentry">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions"
                    select="refsynopsisdiv | refsection | refsect1 |
                            db:refsynopsisdiv | db:refsection | db:refsect1"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = refentry % db2html.division.div.content.mode = -->
<xsl:template mode="db2html.division.div.content.mode" match="refentry |
                                                              db:refentry">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <div class="refnamedivs">
    <xsl:apply-templates select="refnamediv | db:refnamediv">
      <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk + 1"/>
      <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    </xsl:apply-templates>
  </div>
</xsl:template>

<!-- = refdescriptor = -->
<xsl:template match="refdescriptor | db:refdescriptor">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = refname = -->
<xsl:template match="refname | db:refname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = refnamediv = -->
<xsl:template match="refnamediv | db:refnamediv">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'refnamediv'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:choose>
      <xsl:when test="refdescriptor">
        <xsl:apply-templates select="refdescriptor"/>
      </xsl:when>
      <xsl:when test="db:refdescriptor">
        <xsl:apply-templates select="db:refdescriptor"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="refname | db:refname">
          <xsl:if test="position() != 1">
            <xsl:call-template name="l10n.gettext">
              <xsl:with-param name="msgid" select="', '"/>
            </xsl:call-template>
          </xsl:if>
          <xsl:apply-templates select="."/>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:call-template name="l10n.gettext">
      <xsl:with-param name="msgid" select="' — '"/>
    </xsl:call-template>
    <xsl:apply-templates select="refpurpose | db:refpurpose"/>
  </div>
  </xsl:if>
  <!-- FIXME: what to do with refclass? -->
</xsl:template>

<!-- = refpurpose = -->
<xsl:template match="refpurpose | db:refpurpose">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = refsect1 = -->
<xsl:template match="refsect1 | db:refsect1">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="refsect2 | db:refsect2"/>
    <xsl:with-param name="info" select="refsect1info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="chunk_divisions" select="false()"/>
  </xsl:call-template>
</xsl:template>

<!-- = refsect2 = -->
<xsl:template match="refsect2 | db:refsect2">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="refsect3 | db:refsect3"/>
    <xsl:with-param name="info" select="refsect2info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="chunk_divisions" select="false()"/>
  </xsl:call-template>
</xsl:template>

<!-- = refsect3 = -->
<xsl:template match="refsect3 | db:refsect3">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="/false"/>
    <xsl:with-param name="info" select="refsect3info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="chunk_divisions" select="false()"/>
  </xsl:call-template>
</xsl:template>

<!-- = refsection = -->
<xsl:template match="refsection | db:refsection">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="refsection | db:refsection"/>
    <xsl:with-param name="info" select="refsectioninfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="chunk_divisions" select="false()"/>
  </xsl:call-template>
</xsl:template>

<!-- = refsynopsisdiv = -->
<xsl:template match="refsynopsisdiv | db:refsynopsisdiv">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

</xsl:stylesheet>
