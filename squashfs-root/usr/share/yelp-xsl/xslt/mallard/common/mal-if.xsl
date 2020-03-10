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
                xmlns:if="http://projectmallard.org/if/1.0/"
                xmlns:str="http://exslt.org/strings"
                exclude-result-prefixes="mal if str"
                version="1.0">

<!--!!==========================================================================
Mallard Conditionals
Support for run-time conditional processing.
:Revision:version="3.8" date="2012-11-05" status="final"

This stylesheet contains utilities for handling conditional processing
in Mallard documents.
-->


<!--@@==========================================================================
mal.if.target
The list of supported target tokens.
:Revision:version="3.8" date="2012-11-05" status="final"

This parameter takes a space-separated list of tokens to enable for conditional
processing. It is used by the template *{mal.if.test}. This parameter is meant
to hold tokens starting with #{target:}. It should usually be set by the primary
importing stylesheet.
-->
<xsl:param name="mal.if.target" select="''"/>


<!--@@==========================================================================
mal.if.platform
The list of supported platform tokens.
:Revision:version="3.8" date="2012-11-05" status="final"

This parameter takes a space-separated list of tokens to enable for conditional
processing. It is used by the template *{mal.if.test}. This parameter is meant
to hold tokens starting with #{platform:}. It should usually be set by hand or
by a customization stylesheet.
-->
<xsl:param name="mal.if.platform" select="''"/>


<!--@@==========================================================================
mal.if.features
The list of supported feature tokens.
:Revision:version="3.8" date="2012-11-05" status="final"

This parameter takes a space-separated list of tokens to enable for conditional
processing. It is used by the template *{mal.if.test}. This parameter is meant
to hold tokens that specify the capabilities of these stylesheets. It should
usually be set by the primary importing stylesheet.
-->
<xsl:param name="mal.if.features" select="'
mallard:1.0
'"/>


<!--@@==========================================================================
mal.if.custom
A custom list of supported tokens.
:Revision:version="3.8" date="2012-11-05" status="final"

This parameter takes a space-separated list of tokens to enable for conditional
processing. It is used by the template *{mal.if.test}. This parameter is meant
to hold extra values enabled by hand or by a customization stylesheet.
-->
<xsl:param name="mal.if.custom" select="''"/>


<!--@@==========================================================================
mal.if.maybe
A list of tokens that may be true.
:Revision:version="3.8" date="2012-11-05" status="final"

This parameter takes a space-separated list of tokens that may be true. The
template *{mal.if.test} returns special flags when a condition may be true,
allowing conditional processing to be deferred (for example, to CSS media
selectors). This parameter should usually be set by the primary importing
stylesheet.
-->
<xsl:param name="mal.if.maybe" select="''"/>


<xsl:variable name="_mal.if.tokens" select="concat(' ', $mal.if.target,
                                                   ' ', $mal.if.platform,
                                                   ' ', $mal.if.features,
                                                   ' ', $mal.if.custom,
                                                   ' ')"/>
<xsl:variable name="_mal.if.maybe" select="concat(' ', $mal.if.maybe, ' ')"/>


<!--**==========================================================================
mal.if.test
Test if a condition is true.
:Revision:version="3.8" date="2012-11-05" status="final"
$node: The element to check the condition for.
$test: The test expression.

This template evaluates the test expression ${test}, which is taken automatically
from the #{test} or #{if:test} attribute of $node. It splits the expression on
commas into subexpressions, then splits each subexpression on spaces into tokens.
A token is taken to be true if it's in one of the space-separated lists from
@{mal.if.target}, @{mal.if.platform}, @{mal.if.features}, or @{mal.if.custom}.
If the token starts with an exclamation point, the exclamation point is stripped
and the resulting truth value is negated.

A subexpression is true if all its tokens is true. The full test expression is
true if any subexpression is true. If the test expression is true, the literal
string #{'true'} is returned. If the test expression is false, the empty
string is returned.

This template can handle "maybe" values: tokens that may or may not be true,
and whose truth values are deferred to post-transform time. A token is maybe
if it appears in the space-separated list @{mal.if.maybe}. If a subexpression
contains a maybe value and does not contain any false tokens, its truth value
is a special string constructed from the maybe tokens and starting with the
string #{if__}. If any subexpressions are maybe and none of the subexpressions
are false, the return value is a space-separated list of the maybe strings.

Maybe tokens usually must be handled specifically by the importing stylesheet.
It's usually not sufficient to just add a token to @{mal.if.maybe}. This
template will handle any maybe token, but it does not handle the actual logic
of dynamically showing or hiding content based on those tokens.
-->
<xsl:template name="mal.if.test">
  <xsl:param name="node" select="."/>
  <xsl:param name="test" select="($node/self::if:if/@test |
                                  $node/self::if:when/@test |
                                  $node/@if:test)[1]"/>
  <xsl:choose>
    <xsl:when test="$test != ''">
      <xsl:variable name="ret">
        <xsl:for-each select="str:split($test, ',')">
          <xsl:text> </xsl:text>
          <xsl:variable name="subexpr">
            <xsl:for-each select="str:tokenize(., ' ')">
              <xsl:text> </xsl:text>
              <xsl:choose>
                <xsl:when test="starts-with(., '!')">
                  <xsl:variable name="tmp">
                    <xsl:call-template name="_mal.if.test.check_token">
                      <xsl:with-param name="node" select="$node"/>
                      <xsl:with-param name="token" select="substring(., 2)"/>
                    </xsl:call-template>
                  </xsl:variable>
                  <xsl:choose>
                    <xsl:when test="$tmp = '1'">
                      <xsl:text>0</xsl:text>
                    </xsl:when>
                    <xsl:when test="$tmp = '0'">
                      <xsl:text>1</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="concat('not-', $tmp)"/>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:call-template name="_mal.if.test.check_token">
                    <xsl:with-param name="node" select="$node"/>
                    <xsl:with-param name="token" select="."/>
                  </xsl:call-template>
                </xsl:otherwise>
              </xsl:choose>
              <xsl:text> </xsl:text>
            </xsl:for-each>
          </xsl:variable>
          <xsl:choose>
            <xsl:when test="contains($subexpr, ' 0 ')">
              <xsl:text></xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:variable name="subcond">
                <xsl:for-each select="str:tokenize($subexpr, ' ')[.!='1']">
                  <xsl:if test="position != 1">
                    <xsl:text>__</xsl:text>
                  </xsl:if>
                  <xsl:value-of select="."/>
                </xsl:for-each>
              </xsl:variable>
              <xsl:choose>
                <xsl:when test="$subcond != ''">
                  <xsl:text>if__</xsl:text>
                  <xsl:value-of select="$subcond"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>true</xsl:text>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:for-each>
        <xsl:text> </xsl:text>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="contains($ret, ' true ')">
          <xsl:text>true</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:for-each select="str:split($ret, ' ')[. != 'true']">
            <xsl:value-of select="."/>
            <xsl:text> </xsl:text>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>true</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!--#* _mal.if.test.check_token -->
<xsl:template name="_mal.if.test.check_token">
  <xsl:param name="node"/>
  <xsl:param name="token"/>
  <xsl:choose>
    <xsl:when test="$token = 'lang:C' or $token = 'lang:c'">
      <xsl:choose>
        <xsl:when test="not(ancestor-or-self::*/@xml:lang)">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>0</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:when test="starts-with($token, 'lang:')">
      <xsl:for-each select="$node">
        <xsl:choose>
          <xsl:when test="lang(substring($token, 6))">
            <xsl:text>1</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>0</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:for-each>
    </xsl:when>
    <xsl:when test="contains($_mal.if.tokens, concat(' ', $token, ' '))">
      <xsl:text>1</xsl:text>
    </xsl:when>
    <xsl:when test="contains($_mal.if.maybe, concat(' ', $token, ' '))">
      <xsl:call-template name="_mal.if.test.flatten_token">
        <xsl:with-param name="token" select="$token"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>0</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!--#* _mal.if.test.flatten_token -->
<xsl:template name="_mal.if.test.flatten_token">
  <xsl:param name="token"/>
  <xsl:for-each select="str:split($token, '')">
    <xsl:choose>
      <xsl:when test="contains('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_', .)">
        <xsl:value-of select="."/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>-</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>
