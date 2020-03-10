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
                xmlns:str="http://exslt.org/strings"
                exclude-result-prefixes="str"
                version="1.0">

<!--!!==========================================================================
DocBook Profiling
Support for DocBook effectivity attributes
:Revision:version="3.10" date="2013-08-12" status="final"

This stylesheet contains utilities for handling conditional processing
in DocBook documents.
-->


<!--@@==========================================================================
db.profile.arch
The list of architectures for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{arch} attribute for conditional processing.
-->
<xsl:param name="db.profile.arch" select="''"/>


<!--@@==========================================================================
db.profile.audience
The list of audiences for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{audience} attribute for conditional processing.
-->
<xsl:param name="db.profile.audience" select="''"/>


<!--@@==========================================================================
db.profile.condition
The list of application-specific conditions for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{condition} attribute for conditional processing.
-->
<xsl:param name="db.profile.condition" select="''"/>


<!--@@==========================================================================
db.profile.conformance
The list of conformance characteristics for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{conformance} attribute for conditional processing.
-->
<xsl:param name="db.profile.conformance" select="''"/>


<!--@@==========================================================================
db.profile.os
The list of operating systems for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{os} attribute for conditional processing.
-->
<xsl:param name="db.profile.os" select="''"/>


<!--@@==========================================================================
db.profile.outputformat
The list of output formats for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{outputformat} attribute for conditional processing.
-->
<xsl:param name="db.profile.os" select="''"/>


<!--@@==========================================================================
db.profile.revision
The list of editorial revisions for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{revision} attribute for conditional processing.
-->
<xsl:param name="db.profile.revision" select="''"/>


<!--@@==========================================================================
db.profile.security
The list of security levels for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{security} attribute for conditional processing.
-->
<xsl:param name="db.profile.security" select="''"/>


<!--@@==========================================================================
db.profile.userlevel
The list of user experience levels for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{userlevel} attribute for conditional processing.
-->
<xsl:param name="db.profile.userlevel" select="''"/>


<!--@@==========================================================================
db.profile.vendor
The list of vendors for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{vendor} attribute for conditional processing.
-->
<xsl:param name="db.profile.vendor" select="''"/>


<!--@@==========================================================================
db.profile.wordsize
The list of word sizes for conditional processing.
:Revision:version="3.10" date="2013-08-12" status="final"

This parameter takes a semicolon-separated list of values to match against the
#{wordsize} attribute for conditional processing.
-->
<xsl:param name="db.profile.wordsize" select="''"/>


<!--**==========================================================================
db.profile.test
Test if an element should be shown based on profiling attributes.
:Revision:version="3.10" date="2013-08-12" status="final"
$node: The element to check the condition for.

This template looks at all the profiling attributes of the element ${node}:
#{arch}, #{audience}, #{condition}, #{conformance}, #{os}, #{outputformat},
#{revision}, #{security}, #{userlevel}, #{vendor}, and #{wordsize}. It returns
the string #{"true"} if all attributes present match the corresponding parameter
in this stylesheet. Attributes and parameters can both be lists, separated by
semicolons. An attribute matches a parameter if there is at least one value in
common between the two.
-->
<xsl:template name="db.profile.test">
  <xsl:param name="node" select="."/>

  <xsl:variable name="testnot">
    <xsl:if test="$node/@arch != '' and $db.profile.arch != ''">
      <xsl:variable name="testarch">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@arch"/>
          <xsl:with-param name="value" select="$db.profile.arch"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testarch = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@audience != '' and $db.profile.audience != ''">
      <xsl:variable name="testaudience">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@audience"/>
          <xsl:with-param name="value" select="$db.profile.audience"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testaudience = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@condition != '' and $db.profile.condition != ''">
      <xsl:variable name="testcondition">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@condition"/>
          <xsl:with-param name="value" select="$db.profile.condition"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testcondition = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@conformance != '' and $db.profile.conformance != ''">
      <xsl:variable name="testconformance">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@conformance"/>
          <xsl:with-param name="value" select="$db.profile.conformance"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testconformance = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@os != '' and $db.profile.os != ''">
      <xsl:variable name="testos">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@os"/>
          <xsl:with-param name="value" select="$db.profile.os"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testos = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@outputformat != '' and $db.profile.outputformat != ''">
      <xsl:variable name="testoutputformat">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@outputformat"/>
          <xsl:with-param name="value" select="$db.profile.outputformat"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testoutputformat = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@revision != '' and $db.profile.revision != ''">
      <xsl:variable name="testrevision">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@revision"/>
          <xsl:with-param name="value" select="$db.profile.revision"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testrevision = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@security != '' and $db.profile.security != ''">
      <xsl:variable name="testsecurity">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@security"/>
          <xsl:with-param name="value" select="$db.profile.security"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testsecurity = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@userlevel != '' and $db.profile.userlevel != ''">
      <xsl:variable name="testuserlevel">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@userlevel"/>
          <xsl:with-param name="value" select="$db.profile.userlevel"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testuserlevel = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@vendor != '' and $db.profile.vendor != ''">
      <xsl:variable name="testvendor">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@vendor"/>
          <xsl:with-param name="value" select="$db.profile.vendor"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testvendor = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$node/@wordsize != '' and $db.profile.wordsize != ''">
      <xsl:variable name="testwordsize">
        <xsl:call-template name="_db.profile.test.compare">
          <xsl:with-param name="attr" select="$node/@wordsize"/>
          <xsl:with-param name="value" select="$db.profile.wordsize"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:if test="$testwordsize = ''">
        <xsl:text>x</xsl:text>
      </xsl:if>
    </xsl:if>
  </xsl:variable>

  <xsl:if test="$testnot = ''">
    <xsl:text>true</xsl:text>
  </xsl:if>
</xsl:template>

<!--#* _db.profile.test.compare -->
<xsl:template name="_db.profile.test.compare">
  <xsl:param name="attr"/>
  <xsl:param name="value"/>
  <xsl:variable name="attr_" select="concat(';', $attr, ';')"/>
  <xsl:for-each select="str:split($value, ';')">
    <xsl:if test="contains($attr_, concat(';', ., ';'))">
      <xsl:text>1</xsl:text>
    </xsl:if>
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>
