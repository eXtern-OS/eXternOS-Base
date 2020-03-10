<?xml version='1.0' encoding='UTF-8'?><!-- -*- indent-tabs-mode: nil -*- -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:mal="http://www.gnome.org/~shaunm/mallard"
                xmlns:yelp="http://www.gnome.org/yelp/ns"
                xmlns="http://www.w3.org/1999/xhtml"
                extension-element-prefixes="yelp"
                version="1.0">

<xsl:import href="/usr/share/yelp-xsl/xslt/mallard/html/mal2xhtml.xsl"/>

<xsl:import href="yelp-common.xsl"/>

<xsl:param name="yelp.stub" select="false()"/>

<xsl:param name="mal2html.editor_mode" select="$yelp.editor_mode"/>

<xsl:param name="mal.cache" select="yelp:input()"/>

<xsl:param name="mal.link.prefix" select="'xref:'"/>
<xsl:param name="mal.link.extension" select="''"/>

<xsl:template name="mal.link.target.custom">
  <xsl:param name="node" select="."/>
  <xsl:param name="action" select="$node/@action"/>
  <xsl:param name="xref" select="$node/@xref"/>
  <xsl:choose>
    <xsl:when test="starts-with($action, 'install:')">
      <xsl:value-of select="$action"/>
    </xsl:when>
    <xsl:when test="starts-with($xref, 'ghelp:') or starts-with($xref, 'help:')">
      <xsl:value-of select="$xref"/>
    </xsl:when>
  </xsl:choose>
</xsl:template>

<xsl:template name="mal.link.content.custom">
  <xsl:param name="node" select="."/>
  <xsl:param name="action" select="$node/@action"/>
  <xsl:param name="xref" select="$node/@xref"/>
  <xsl:choose>
    <xsl:when test="starts-with($action, 'install:')">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="domain" select="'yelp'"/>
        <xsl:with-param name="msgid" select="'install.tooltip'"/>
        <xsl:with-param name="string" select="substring($action, 9)"/>
        <xsl:with-param name="format" select="true()"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="starts-with($xref, 'ghelp:') or starts-with($xref, 'help:')">
      <xsl:value-of select="$xref"/>
    </xsl:when>
  </xsl:choose>
</xsl:template>

<xsl:template name="mal.link.tooltip.custom">
  <xsl:param name="node" select="."/>
  <xsl:param name="action" select="$node/@action"/>
  <xsl:param name="xref" select="$node/@xref"/>
  <xsl:choose>
    <xsl:when test="starts-with($action, 'install:')">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="domain" select="'yelp'"/>
        <xsl:with-param name="msgid" select="'install.tooltip'"/>
        <xsl:with-param name="string" select="substring($action, 9)"/>
        <xsl:with-param name="format" select="true()"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="starts-with($xref, 'ghelp:') or starts-with($xref, 'help:')">
      <xsl:value-of select="$xref"/>
    </xsl:when>
  </xsl:choose>
</xsl:template>

<xsl:template name="yelp.css.custom">
<xsl:text>
a.linkdiv:hover {
  outline: solid 1px </xsl:text>
    <xsl:value-of select="$color.blue_background"/><xsl:text>;
  background: -webkit-gradient(linear, left top, left 80, from(</xsl:text>
    <xsl:value-of select="$color.blue_background"/><xsl:text>), to(</xsl:text>
    <xsl:value-of select="$color.background"/><xsl:text>));
}
a.fullsearch {
  display: block;
  text-align: center;
  max-width: 20em;
  margin: 0 auto 1em auto;
  pading: 0.2em;
  background-color: </xsl:text>
    <xsl:value-of select="$color.yellow_background"/><xsl:text>;
  border: solid 1px </xsl:text>
    <xsl:value-of select="$color.yellow_border"/><xsl:text>;
}
a.fullsearch:hover {
  text-decoration: none;
  border: solid 1px </xsl:text>
    <xsl:value-of select="$color.blue_border"/><xsl:text>;
}
</xsl:text>
<xsl:if test="$yelp.editor_mode">
<xsl:text>
div.version {
  margin: -1em -12px 1em -12px;
  padding: 0.5em 12px 0.5em 12px;
  position: relative;
  left: auto; right: auto;
  opacity: 1.0;
  max-width: none;
  border: none;
  border-bottom: solid 1px </xsl:text>
    <xsl:value-of select="$color.gray_border"/><xsl:text>;
  background-color: </xsl:text>
    <xsl:value-of select="$color.yellow_background"/><xsl:text>;
}
div.version:hover { opacity: 1.0; }
</xsl:text>
<xsl:if test="$yelp.stub">
<xsl:text>
body, div.body {
  background-color: </xsl:text>
    <xsl:value-of select="$color.red_background"/><xsl:text>;
}
</xsl:text>
</xsl:if>
</xsl:if>
</xsl:template>

</xsl:stylesheet>
