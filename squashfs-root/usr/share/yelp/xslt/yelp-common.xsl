<?xml version='1.0' encoding='UTF-8'?><!-- -*- indent-tabs-mode: nil -*- -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:yelp="http://www.gnome.org/yelp/ns"
                xmlns:set="http://exslt.org/sets"
                xmlns:mml="http://www.w3.org/1998/Math/MathML"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="yelp set mml"
                extension-element-prefixes="yelp"
                version="1.0">

<xsl:param name="yelp.editor_mode" select="false()"/>

<xsl:param name="html.extension" select="''"/>

<xsl:param name="html.syntax.highlight" select="true()"/>
<xsl:param name="html.js.root" select="'file:///usr/share/yelp-xsl/js/'"/>

<xsl:template name="html.js.mathjax">
  <xsl:param name="node" select="."/>
  <xsl:if test="$node//mml:*[1]">
    <script type="text/javascript">
      <xsl:attribute name="src">
        <xsl:text>file:///usr/share/yelp/mathjax/MathJax.js?config=yelp</xsl:text>
      </xsl:attribute>
    </script>
  </xsl:if>
</xsl:template>

<!-- == html.output == -->
<xsl:template name="html.output">
  <xsl:param name="node" select="."/>
  <xsl:param name="href">
    <xsl:choose>
      <xsl:when test="$node/@xml:id">
        <xsl:value-of select="$node/@xml:id"/>
      </xsl:when>
      <xsl:when test="$node/@id">
        <xsl:value-of select="$node/@id"/>
      </xsl:when>
      <xsl:when test="set:has-same-node($node, /*)">
        <xsl:value-of select="$html.basename"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="generate-id()"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:param>
  <yelp:document href="{$href}">
    <xsl:call-template name="html.page">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </yelp:document>
  <xsl:apply-templates mode="html.output.after.mode" select="$node"/>
</xsl:template>

<!-- == html.css.custom == -->
<xsl:template name="html.css.custom">
  <xsl:param name="direction"/>
  <xsl:param name="left"/>
  <xsl:param name="right"/>
<xsl:text>
html {
  height: 100%;
}
body {
  padding: 0;
  background-color: </xsl:text><xsl:value-of select="$color.background"/><xsl:text>;
  max-width: 100%;
}
div.page {
  border: none;
  margin: 0;
  width: 100%;
  max-width: 100%;
}
div.header {
  max-width: 100%;
  width: 100%;
  padding: 0;
  margin: 0 auto 1em auto;
}
div.body, div.footer {
  margin: 0;
  max-width: 60em;
}
div.code {
  -webkit-box-shadow: 0px 0px 4px </xsl:text><xsl:value-of select="$color.gray_border"/><xsl:text>;
}
div.code:hover {
  -webkit-box-shadow: 0px 0px 4px </xsl:text><xsl:value-of select="$color.blue_border"/><xsl:text>;
}
div.synopsis div.code, div.synopsis div.code:hover { -webkit-box-shadow: none; }
div.trails {
  margin: 0;
  padding: 0.2em 12px 0 12px;
  background-color: </xsl:text>
    <xsl:value-of select="$color.gray_background"/><xsl:text>;
  border-bottom: solid 1px </xsl:text>
    <xsl:value-of select="$color.gray_border"/><xsl:text>;
}
div.trail {
  font-size: 1em;
  margin: 0 1em 0.2em 1em;
  padding: 0;
}
@media only screen and (max-width: 400px) {
  div.trails {
    padding-left: 6px;
    padding-right: 6px;
  }
}
a.trail { color:  </xsl:text>
  <xsl:value-of select="$color.text_light"/><xsl:text>; }
a.trail:hover { text-decoration: none; color:  </xsl:text>
  <xsl:value-of select="$color.link"/><xsl:text>; }
.current-location-hash div.hgroup {
  background-color: </xsl:text><xsl:value-of select="$color.gray_background"/><xsl:text>
}
</xsl:text>
<xsl:call-template name="yelp.css.custom"/>
</xsl:template>

<xsl:template name="yelp.css.custom"/>

</xsl:stylesheet>
