<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

<xsl:template match="book">
<table-of-contents>
<xsl:apply-templates select="chapter"/>
</table-of-contents>
</xsl:template>

<xsl:template match="chapter">
<chapter>
<title><xsl:value-of select="title"/></title>
<anchor><xsl:value-of select="@id"/></anchor>
<xsl:apply-templates select="sect1"/>
</chapter>
</xsl:template>

<xsl:template match="sect1">
<section>
<title><xsl:value-of select="title"/></title>
<anchor><xsl:value-of select="@id"/></anchor>
</section>
</xsl:template>

</xsl:stylesheet>
