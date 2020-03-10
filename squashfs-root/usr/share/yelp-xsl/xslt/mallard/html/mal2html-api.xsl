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
                xmlns:mal="http://projectmallard.org/1.0/"
                xmlns:e="http://projectmallard.org/experimental/"
                xmlns:api="http://projectmallard.org/experimental/api/"
                xmlns:exsl="http://exslt.org/common"
                xmlns:math="http://exslt.org/math"
                xmlns:html="http://www.w3.org/1999/xhtml"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal e api exsl math html"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - API Extension
Support for Mallard API extension elements.

This stylesheet contains templates to support features from the Mallard API
extension.
-->


<!--**==========================================================================
mal2html.api.links.function
Output links as a synopsis of functions.
$node: A #{links} element to link from.
$links: A list of topic links already filtered by group.

This template outputs links as a synopsis according to the programming language
specified by the #{api:mime} attribute of ${node}. If #{api:mime} is recognized,
one of the language-specific templates in this stylesheet is called. Otherwise,
the links are passed to *{mal2html.links.ul}.

This template does not handle titles or other wrapper information for #{links}
elements. It should be called by an appropriate template that handles the
#{links} element.
-->
<xsl:template name="mal2html.api.links.function">
  <xsl:param name="node"/>
  <xsl:param name="links"/>
  <xsl:choose>
    <xsl:when test="$node/@api:mime = 'text/x-csrc' or $node/@api:mime = 'text/x-chdr'">
      <xsl:call-template name="mal2html.api.links.function.c">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="links" select="$links"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="mal2html.links.ul">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="links" select="$links"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
mal2html.api.links.function.c
Output links as a synopsis of C functions.
$node: A #{links} element to link from.
$links: A list of topic links already filtered by group.

This template outputs links as a synopsis of C functions. It is called by
*{mal2html.api.links.function} when the #{api:mime} attribute of ${node} is
#{text/x-csrc} or #{text/x-chdr}. The target nodes of ${links} are expected
to have at least an #{api:name} element. Any links whose target does not
have an #{api:name} element will be passed to *{mal2html.links.ul} after
the synopsis.
-->
<xsl:template name="mal2html.api.links.function.c">
  <xsl:param name="node"/>
  <xsl:param name="links"/>
  <xsl:variable name="out_">
    <xsl:for-each select="$links">
      <xsl:sort data-type="number" select="@groupsort"/>
      <xsl:sort select="mal:title[@type = 'sort']"/>
      <xsl:variable name="link" select="."/>
      <xsl:for-each select="$mal.cache">
        <xsl:variable name="target" select="key('mal.cache.key', $link/@xref)"/>
        <xsl:variable name="function" select="$target/mal:info/api:function"/>
        <xsl:choose>
          <xsl:when test="$function/api:name">
            <api:pre>
              <div class="{$link/@class}">
              <xsl:for-each select="$link/@*">
                <xsl:if test="starts-with(name(.), 'data-')">
                  <xsl:copy-of select="."/>
                </xsl:if>
              </xsl:for-each>
              <xsl:apply-templates mode="mal2html.inline.mode" select="$function/api:returns/api:type/node()"/>
              <xsl:variable name="tab" select="20 - string-length($function/api:returns/api:type)"/>
              <xsl:choose>
                <xsl:when test="$tab > 1">
                  <xsl:call-template name="utils.repeat_string">
                    <xsl:with-param name="string" select="' '"/>
                    <xsl:with-param name="number" select="$tab"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>&#x000A;</xsl:text>
                  <xsl:text>                    </xsl:text>
                </xsl:otherwise>
              </xsl:choose>
              <a>
                <xsl:attribute name="href">
                  <xsl:call-template name="mal.link.target">
                    <xsl:with-param name="node" select="$node"/>
                    <xsl:with-param name="xref" select="$link/@xref"/>
                  </xsl:call-template>
                </xsl:attribute>
                <xsl:attribute name="title">
                  <xsl:call-template name="mal.link.tooltip">
                    <xsl:with-param name="node" select="$node"/>
                    <xsl:with-param name="xref" select="$link/@xref"/>
                    <!-- FIXME: role -->
                  </xsl:call-template>
                </xsl:attribute>
                <xsl:value-of select="$function/api:name"/>
              </a>
              <xsl:variable name="paren" select="40 - string-length($function/api:name)"/>
              <xsl:choose>
                <xsl:when test="$paren > 1">
                  <xsl:call-template name="utils.repeat_string">
                    <xsl:with-param name="string" select="' '"/>
                    <xsl:with-param name="number" select="$paren"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>&#x000A;</xsl:text>
                  <xsl:text>                                                            </xsl:text>
                </xsl:otherwise>
              </xsl:choose>
              <xsl:text>(</xsl:text>
              <xsl:for-each select="$function/api:arg | $function/api:varargs">
                <xsl:if test="position() != 1">
                  <xsl:text>                                                             </xsl:text>
                </xsl:if>
                <xsl:choose>
                  <xsl:when test="self::api:varargs">
                    <xsl:text>...</xsl:text>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:apply-templates mode="mal2html.inline.mode" select="api:type/node()"/>
                    <xsl:if test="substring(api:type, string-length(api:type)) != '*'
                                  or not(contains(api:type, ' '))">
                      <xsl:text> </xsl:text>
                    </xsl:if>
                    <xsl:apply-templates mode="mal2html.inline.mode" select="api:name/node()"/>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:choose>
                  <xsl:when test="position() != last()">
                    <xsl:text>,</xsl:text>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:text>);</xsl:text>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:text>&#x000A;</xsl:text>
              </xsl:for-each>
              <xsl:if test="not($function/api:arg or $function/api:varargs)">
                <xsl:text>void);&#x000A;</xsl:text>
              </xsl:if>
              </div>
            </api:pre>
          </xsl:when>
          <xsl:otherwise>
            <xsl:copy-of select="$link"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </xsl:for-each>
  </xsl:variable>
  <xsl:variable name="out" select="exsl:node-set($out_)"/>
  <xsl:if test="$out/api:pre">
    <div class="synopsis">
      <pre class="contents">
        <xsl:copy-of select="$out/api:pre/*"/>
      </pre>
    </div>
  </xsl:if>
  <xsl:if test="$out/mal:link">
    <xsl:call-template name="mal2html.links.ul">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="links" select="$out/mal:link"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
