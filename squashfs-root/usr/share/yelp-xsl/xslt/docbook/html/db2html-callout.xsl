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
                xmlns:db="http://docbook.org/ns/docbook"
                xmlns:str="http://exslt.org/strings"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db str"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Callouts
:Requires: db2html-block db2html-xref html
:Revision:version="1.0" date="2011-05-16" status="final"

This modules handles simple DocBook callouts using the #{co} and #{callout}
elements. Currently, only callouts to #{co} elements are supported. The
#{area} element is not supported.
-->


<!--**==========================================================================
db2html.callout.label
Create a callout label for a #{co} element.
:Revision:version="1.0" date="2011-05-16" status="final"
$node: The #{co} element to create a callout label for.

This template creates a label for a callout, taking a #{co} element as the
${node} parameter. The label is numbered according to the position of the #{co}
element in the document. To create the corresponding label for a #{callout}
element, locate the corresponding #{co} element and call this template on it.
-->
<xsl:template name="db2html.callout.label">
  <xsl:param name="node" select="."/>
  <span class="co">
    <xsl:value-of select="count($node/preceding::co) + count($node/preceding::db:co) + 1"/>
  </span>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = co = -->
<xsl:template match="co | db:co">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
    <xsl:call-template name="db2html.callout.label"/>
  </xsl:if>
</xsl:template>

<!-- = calloutlist = -->
<xsl:template match="calloutlist | db:calloutlist">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = callout == -->
<xsl:template match="callout | db:callout">
  <xsl:variable name="node" select="."/>
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'callout'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <div class="co">
      <xsl:for-each select="str:split(@arearefs)">
        <xsl:variable name="arearef" select="string(.)"/>
        <xsl:for-each select="$node">
          <xsl:variable name="co" select="key('db.id.key', $arearef)"/>
          <xsl:if test="$co/self::co or $co/self::db:co">
            <xsl:call-template name="db2html.callout.label">
              <xsl:with-param name="node" select="$co"/>
            </xsl:call-template>
          </xsl:if>
        </xsl:for-each>
      </xsl:for-each>
    </div>
    <xsl:apply-templates/>
  </div>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
