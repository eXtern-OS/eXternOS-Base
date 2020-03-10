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

<xsl:stylesheet xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
                xmlns:mal='http://projectmallard.org/1.0/'
                xmlns:cache='http://projectmallard.org/cache/1.0/'
                xmlns:site='http://projectmallard.org/site/1.0/'
                xmlns='http://projectmallard.org/1.0/'
                version='1.0'>

<!--!!==========================================================================
Mallard Cache Files
Generate Mallard cache files from cache input files.

FIXME
-->

<xsl:output omit-xml-declaration="yes"/>

<xsl:include href="../common/mal-link.xsl"/>


<!--**==========================================================================
mal.cache.id
-->
<xsl:template name="mal.cache.id">
  <xsl:param name="node" select="."/>
  <xsl:param name="node_in"/>
  <xsl:attribute name="id">
    <xsl:call-template name="mal.link.linkid">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:attribute>
</xsl:template>


<!--**==========================================================================
mal.cache.info
-->
<xsl:template name="mal.cache.info">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="$node/mal:info"/>
  <xsl:param name="node_in"/>
  <info>
    <xsl:for-each select="$info/*">
      <xsl:copy-of select="."/>
    </xsl:for-each>
  </info>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = /cache:cache = -->
<xsl:template match='/cache:cache'>
  <cache:cache>
    <xsl:for-each select="mal:page">
      <xsl:apply-templates select="document(@cache:href)/*">
        <xsl:with-param name="node_in" select="."/>
      </xsl:apply-templates>
    </xsl:for-each>
  </cache:cache>
</xsl:template>

<!-- = mal:page = -->
<xsl:template match="mal:page">
  <xsl:param name="node_in"/>
  <page>
    <xsl:copy-of select="@*"/>
    <xsl:copy-of select="$node_in/@cache:*"/>
    <xsl:copy-of select="$node_in/@site:*"/>
    <xsl:call-template name="mal.cache.id">
      <xsl:with-param name="node_in" select="$node_in"/>
    </xsl:call-template>
    <xsl:call-template name="mal.cache.info">
      <xsl:with-param name="node_in" select="$node_in"/>
    </xsl:call-template>
    <xsl:apply-templates>
      <xsl:with-param name="node_in" select="$node_in"/>
    </xsl:apply-templates>
  </page>
</xsl:template>

<!-- = mal:section = -->
<xsl:template match="mal:section">
  <xsl:param name="node_in"/>
  <section>
    <xsl:copy-of select="@*"/>
    <xsl:call-template name="mal.cache.id">
      <xsl:with-param name="node_in" select="$node_in"/>
    </xsl:call-template>
    <xsl:call-template name="mal.cache.info">
      <xsl:with-param name="node_in" select="$node_in"/>
    </xsl:call-template>
    <xsl:apply-templates>
      <xsl:with-param name="node_in" select="$node_in"/>
    </xsl:apply-templates>
  </section>
</xsl:template>

<!-- = mal:title = -->
<xsl:template match="mal:title">
  <xsl:copy-of select="."/>
</xsl:template>

<xsl:template match="node() | text()"/>

</xsl:stylesheet>
