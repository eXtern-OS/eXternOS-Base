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

<xsl:param name="html.basename" select="'//index'"/>

<xsl:param name="linktrail" select="''"/>

<xsl:template mode="html.title.mode" match="Man">
  <xsl:value-of select="header/title"/>
</xsl:template>

<xsl:template mode="html.body.mode" match="Man">
  <!-- Invisible div that we use to calculate the indent width. -->
  <xsl:element name="div">
    <xsl:attribute name="id">invisible-char</xsl:attribute>
    <xsl:attribute name="style">
      position: absolute;
      font-family: monospace;
      visibility: hidden;
      height: auto;
      width: auto;
    </xsl:attribute>
    <xsl:text>X</xsl:text>
  </xsl:element>
  <xsl:apply-templates select="header"/>
  <xsl:apply-templates select="section"/>
</xsl:template>

<!-- ======================================================================= -->

<xsl:template match="header">
  <div class="hgroup">
    <h1 class="title">
      <xsl:value-of select="title"/>
      <xsl:text> (</xsl:text>
      <xsl:value-of select="section"/>
      <xsl:text>)</xsl:text>
    </h1>
    <h3 style="text-align: right;">
      <xsl:value-of select="collection"/>
    </h3>
    <xsl:if test="@version or @date">
      <p style="text-align: right">
        <xsl:if test="@version">
          Version: <xsl:value-of select="@version"/>
        </xsl:if>
        <xsl:if test="@version and @date"><br/></xsl:if>
        <xsl:if test="@date">
          Date: <xsl:value-of select="@date"/>
        </xsl:if>
      </p>
    </xsl:if>
  </div>
</xsl:template>

<xsl:template match="br">
  <br/>
</xsl:template>

<xsl:template match="section">
  <div class="section" style="padding-top: 1em;">
    <h2>
      <xsl:value-of select="title"/>
    </h2>

    <div class="section-contents" style="font-family: monospace;">
      <xsl:apply-templates select="sheet"/>
    </div>
  </div>
</xsl:template>

<xsl:template match="sheet">
  <xsl:element name="div">
    <xsl:attribute name="style">
      margin-bottom: 0px;
      margin-top: <xsl:value-of select="@jump"/>em;
      margin-left: <xsl:value-of select="@indent"/>ex;
    </xsl:attribute>
    <xsl:attribute name="class">sheet</xsl:attribute>
    <p><xsl:apply-templates select="span|br|a"/></p>
  </xsl:element>
</xsl:template>

<xsl:template match="span">
  <xsl:element name="span">
    <xsl:choose>
      <xsl:when test="@class = 'B'">
        <xsl:attribute name="style">
          font-weight: 700;
        </xsl:attribute>
      </xsl:when>
      <xsl:when test="@class = 'I'">
        <xsl:attribute name="style">
          font-style: italic;
        </xsl:attribute>
      </xsl:when>
    </xsl:choose>

    <xsl:value-of select="."/>
  </xsl:element>
</xsl:template>

<xsl:template match="a">
  <xsl:element name="a">
    <xsl:attribute name="href">
      <xsl:value-of select="@href"/>
    </xsl:attribute>

    <xsl:apply-templates select="span|br"/>
  </xsl:element>
</xsl:template>

<xsl:template name="html.head.custom">
<!--
  The following javascript function fixes up the indent of sheets
  correctly. The indent should be some number of character widths, but
  you can't do that in CSS, so we have something like "7ex" as a
  stand-in (but ex is too thin here). There's an invisible div with
  the correct styling and a single character which we measure the
  width of and update each sheet as required.
-->
<script type="text/javascript" language="javascript">
<xsl:text>
$(document).ready (function () {
  var div = document.getElementById("invisible-char");
  var width = div.clientWidth;

  var all_divs = document.getElementsByTagName("div");
  for (var i=0; i &lt; all_divs.length; i++) {
    var elt = all_divs[i];
    if (elt.getAttribute("class") == "sheet") {
      var indent_str = elt.style.marginLeft;
      var indent = indent_str.substr (0, indent_str.length - 2);

      elt.style.marginLeft = width * indent + "px";
    }
  }
});
</xsl:text>
</script>
</xsl:template>


</xsl:stylesheet>
