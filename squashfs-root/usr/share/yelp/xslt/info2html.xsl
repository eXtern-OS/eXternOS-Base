<?xml version='1.0' encoding='UTF-8'?><!-- -*- indent-tabs-mode: nil -*- -->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:yelp="http://www.gnome.org/yelp/ns"
                xmlns="http://www.w3.org/1999/xhtml"
                extension-element-prefixes="yelp"
                version="1.0">

<xsl:import href="/usr/share/yelp-xsl/xslt/common/color.xsl"/>
<xsl:import href="/usr/share/yelp-xsl/xslt/common/icons.xsl"/>
<xsl:import href="/usr/share/yelp-xsl/xslt/common/html.xsl"/>
<xsl:import href="/usr/share/yelp-xsl/xslt/common/l10n.xsl"/>
<xsl:include href="yelp-common.xsl"/>

<xsl:template name="linktrails">
  <xsl:param name="up" select="@up"/>
  <xsl:variable name="upnode" select="/Info//Section[@id = $up]"/>
  <xsl:if test="$upnode/@up">
    <xsl:call-template name="linktrails">
      <xsl:with-param name="up" select="$upnode/@up"/>
    </xsl:call-template>
  </xsl:if>
  <a href="xref:{$upnode/@id}">
    <xsl:value-of select="$upnode/@name"/>
  </a>
  <xsl:text>&#x00A0;» </xsl:text>
</xsl:template>

<xsl:template match="/">
  <xsl:for-each select="/Info/Section">
    <xsl:call-template name="html.output"/>
  </xsl:for-each>
</xsl:template>

<xsl:template mode="html.output.after.mode" match="Section">
  <xsl:for-each select="Section">
    <xsl:call-template name="html.output"/>
  </xsl:for-each>
</xsl:template>

<xsl:template mode="html.title.mode" match="Section">
  <xsl:value-of select="@name"/>
</xsl:template>

<xsl:template mode="html.css.mode" match="Section">
  <xsl:param name="direction"/>
  <xsl:param name="left"/>
  <xsl:param name="right"/>
  <xsl:text>
div.body { font-family: monospace; }
span.fixed { white-space: pre; }
<!-- navbar from mal2html, possibly move to html.xsl -->
div.navbar {
  margin: 0 0 1em 0;
  text-align: right;
  font-family: sans-serif;
}
a.navbar-prev::before {
  content: '</xsl:text><xsl:choose>
  <xsl:when test="$left = 'left'"><xsl:text>&#x25C0;&#x00A0;&#x00A0;</xsl:text></xsl:when>
  <xsl:otherwise><xsl:text>&#x25B6;&#x00A0;&#x00A0;</xsl:text></xsl:otherwise>
  </xsl:choose><xsl:text>';
  color: </xsl:text><xsl:value-of select="$color.text_light"/><xsl:text>;
}
a.navbar-next::after {
  content: '</xsl:text><xsl:choose>
  <xsl:when test="$left = 'left'"><xsl:text>&#x00A0;&#x00A0;&#x25B6;</xsl:text></xsl:when>
  <xsl:otherwise><xsl:text>&#x00A0;&#x00A0;&#x25C0;</xsl:text></xsl:otherwise>
  </xsl:choose><xsl:text>';
  color: </xsl:text><xsl:value-of select="$color.text_light"/><xsl:text>;
}
</xsl:text>
</xsl:template>

<xsl:template mode="html.header.mode" match="Section">
  <xsl:if test="@up">
    <div class="trails">
      <div class="trail">
        <xsl:call-template name="linktrails"/>
      </div>
    </div>
  </xsl:if>
</xsl:template>

<xsl:template mode="html.body.mode" match="Section">
  <div class="navbar">
    <xsl:variable name="preceding" select="(parent::Section[1] | preceding::Section[1])[last()]"/>
    <xsl:variable name="following" select="(Section[1] | following::Section[1])[1]"/>
    <xsl:if test="$preceding">
      <a class="navbar-prev" href="xref:{$preceding/@id}">
        <xsl:value-of select="$preceding/@name"/>
      </a>
    </xsl:if>
    <xsl:if test="$preceding and $following">
      <xsl:text>&#x00A0;&#x00A0;|&#x00A0;&#x00A0;</xsl:text>
    </xsl:if>
    <xsl:if test="$following">
      <a class="navbar-next" href="xref:{$following/@id}">
        <xsl:value-of select="$following/@name"/>
      </a>
    </xsl:if>
  </div>
  <xsl:apply-templates select="node()[not(self::Section)]"/>
</xsl:template>


<!-- = Normal Matches = -->

<xsl:template match="para">
  <p>
    <span class="fixed">
      <!-- Apply templates for <a> tags and copy text straight through. -->
      <xsl:apply-templates select="./text()|*"/>
    </span>
  </p>
</xsl:template>

<xsl:template match="para1">
  <span class="fixed">
    <xsl:value-of select="node()"/>
  </span>
</xsl:template>

<xsl:template match="header">
  <xsl:choose>
    <xsl:when test='@level = 1'>
      <h1><xsl:value-of select="node()"/></h1>
    </xsl:when>
    <xsl:when test='@level = 2'>
      <h2><xsl:value-of select="node()"/></h2>
    </xsl:when>
    <xsl:when test='@level = 3'>
      <h3><xsl:value-of select="node()"/></h3>
    </xsl:when>
    <xsl:otherwise>
      <h1>(Unknown heading level) <xsl:value-of select="node()"/></h1>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template match="spacing">
  <xsl:value-of select="node()"/>
</xsl:template>

<xsl:template match="a">
  <xsl:element name="a">
    <xsl:attribute name="href">
      <xsl:value-of select="@href"/>
    </xsl:attribute>
    <xsl:value-of select="node()"/>
  </xsl:element>
</xsl:template>

<xsl:template match="img">
  <xsl:element name="a">
    <xsl:attribute name="href">
      <xsl:value-of select="@src"/>
    </xsl:attribute>
    <xsl:element name="img">
      <xsl:attribute name="src"> <xsl:value-of select="@src"/></xsl:attribute>
    </xsl:element>
  </xsl:element>
</xsl:template>

<xsl:template match="menu">
  <xsl:element name="p">Menu:</xsl:element>
  <xsl:element name="ul">
    <xsl:apply-templates />
  </xsl:element>
</xsl:template>

<xsl:template match="menuholder">
  <xsl:element name="li">
    <xsl:apply-templates />
  </xsl:element>
</xsl:template>

</xsl:stylesheet>
