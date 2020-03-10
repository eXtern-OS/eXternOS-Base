<?xml version='1.0'?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version='1.0'>

<!-- ********************************************************************
     Customization layer for building Debian Multi-Arch packages omitting
     the build-tile date!
     ******************************************************************** -->

<!-- ==================================================================== -->

<xsl:import href="docbook.xsl"/>

<xsl:template name="get.refentry.date">
  <xsl:value-of select="''"/>
</xsl:template>

</xsl:stylesheet>
