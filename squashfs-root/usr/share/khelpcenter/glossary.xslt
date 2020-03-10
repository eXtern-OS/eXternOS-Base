<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

<xsl:template match="glossary">
<glossary>
	<xsl:apply-templates select="glossdiv"/>
</glossary>
</xsl:template>

<xsl:template match="glossdiv">
<section>
	<xsl:attribute name="title"><xsl:value-of select="title"/></xsl:attribute>
	<xsl:apply-templates select="glossentry"/>
</section>
</xsl:template>

<xsl:template match="glossentry">
<entry>
	<xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
	<term><xsl:value-of select="glossterm"/></term>
	<definition><xsl:value-of select="glossdef/*[not(name()='glossseealso')]"/></definition>
	<references><xsl:apply-templates select="glossdef/glossseealso"/></references>
</entry>
</xsl:template>

<xsl:template match="glossseealso">
<reference>
	<xsl:attribute name="term"><xsl:value-of select="."/></xsl:attribute>
	<xsl:attribute name="id"><xsl:value-of select="@otherterm"/></xsl:attribute>
</reference>
</xsl:template>

</xsl:stylesheet>
