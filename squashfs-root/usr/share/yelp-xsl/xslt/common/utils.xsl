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
                version="1.0">

<!--!!==========================================================================
Utilities
Common XSLT Utilities.
:Revision:version="1.0" date="2010-05-25" status="final"

This stylesheet contains various useful utilities that are used throughout
the Yelp stylesheets.
-->


<!--**==========================================================================
utils.repeat_string
Repeat a string a given number of times.
:Revision:version="1.0" date="2011-08-24" status="final"
$string: The string to repeat.
$number: The number of times to repeat ${string}.

This template repeats the ${string} argument ${number} times.
-->
<xsl:template name="utils.repeat_string">
  <xsl:param name="string" select="''"/>
  <xsl:param name="number" select="0"/>
  <xsl:if test="$number &gt; 0">
    <xsl:value-of select="$string"/>
    <xsl:call-template name="utils.repeat_string">
      <xsl:with-param name="string" select="$string"/>
      <xsl:with-param name="number" select="$number - 1"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
utils.strip_newlines
Strip leading or trailing newlines from a string.
:Revision:version="1.0" date="2010-05-25" status="final"
$string: The string to strip newlines from.
$leading: Whether to strip leading newlines.
$trailing: Whether to strip trailing newlines.

This template strips at most one leading and one trailing newline from
${string}.  This is useful for preformatted block elements where leading and
trailing newlines are ignored to make source formatting easier for authors.
-->
<xsl:template name="utils.strip_newlines">
  <xsl:param name="string"/>
  <xsl:param name="leading" select="false()"/>
  <xsl:param name="trailing" select="false()"/>
  <xsl:choose>
    <xsl:when test="$leading">
      <xsl:variable name="new">
        <xsl:choose>
          <xsl:when test="starts-with($string, '&#x000A;')">
            <xsl:value-of select="substring($string, 2)"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$string"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$trailing">
          <xsl:call-template name="utils.strip_newlines">
            <xsl:with-param name="string" select="$new"/>
            <xsl:with-param name="leading" select="false()"/>
            <xsl:with-param name="trailing" select="true()"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$new"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:when test="$trailing">
      <xsl:choose>
        <xsl:when test="substring($string, string-length($string)) = '&#x000A;'">
          <xsl:value-of select="substring($string, 1, string-length($string) - 1 )"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$string"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
utils.linenumbering
Number each line in a verbatim environment.
:Revision:version="1.0" date="2010-12-03" status="final"
$node: The verbatim element to create the line numbering for.
$number: The starting line number.

This template outputs a string with line numbers for each line in a verbatim
elements.  Each line number is on its own line, allowing the output string to
be placed to the side of the verbatim output.
-->
<xsl:template name="utils.linenumbering">
  <xsl:param name="node" select="."/>
  <xsl:param name="number" select="1"/>
  <xsl:param name="string">
    <xsl:choose>
      <xsl:when test="$node/node()[1]/self::text() and starts-with($node/node()[1], '&#x000A;')">
        <xsl:value-of select="substring-after(string($node), '&#x000A;')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="string($node)"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:param>
  <xsl:choose>
    <xsl:when test="contains($string, '&#x000A;')">
      <xsl:number value="$number"/>
      <xsl:text>&#x000A;</xsl:text>
      <xsl:call-template name="utils.linenumbering">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="number" select="$number + 1"/>
        <xsl:with-param name="string"
                        select="substring-after($string, '&#x000A;')"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="string-length($string) != 0">
      <xsl:number value="$number"/>
      <xsl:text>&#x000A;</xsl:text>
    </xsl:when>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
utils.email_address
Get an email address from a mailto URL.
:Revision:version="3.4" date="2012-01-18" status="final"
$href: The mailto URL.

This template takes a mailto URL and returns an email address, stripping the
URL scheme as well as any query string.
-->
<xsl:template name="utils.email_address">
  <xsl:param name="url"/>
  <xsl:variable name="addy">
    <xsl:value-of select="substring-after($url, 'mailto:')"/>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="contains($addy, '?')">
      <xsl:value-of select="substring-before($addy, '?')"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$addy"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
