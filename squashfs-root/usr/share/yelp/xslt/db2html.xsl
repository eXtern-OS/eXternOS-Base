<?xml version='1.0' encoding='UTF-8'?><!-- -*- indent-tabs-mode: nil -*- -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:yelp="http://www.gnome.org/yelp/ns"
                xmlns="http://www.w3.org/1999/xhtml"
                extension-element-prefixes="yelp"
                version="1.0">

<xsl:import href="/usr/share/yelp-xsl/xslt/docbook/html/db2xhtml.xsl"/>

<xsl:include href="yelp-common.xsl"/>

<xsl:param name="db.chunk.info_basename"  select="'//about'"/>

<xsl:param name="db2html.navbar.top" select="false()"/>
<xsl:param name="db2html.sidenav" select="false()"/>

<!-- == db.xref.target == -->
<xsl:template name="db.xref.target">
  <xsl:param name="linkend"/>
  <xsl:param name="target" select="key('idkey', $linkend)"/>
  <xsl:param name="is_chunk" select="false()"/>
  <xsl:choose>
    <xsl:when test="$is_chunk">
      <xsl:value-of select="concat('xref:', $linkend)"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:variable name="target_chunk_id">
        <xsl:call-template name="db.chunk.chunk-id">
          <xsl:with-param name="node" select="$target"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:value-of select="concat('xref:', $target_chunk_id)"/>
      <xsl:if test="$target_chunk_id != $linkend">
        <xsl:value-of select="concat('#', $linkend)"/>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
