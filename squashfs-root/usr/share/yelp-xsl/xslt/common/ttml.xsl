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
along with this program; see the file COPYING.LGPL. If not, see <http://www.gnu.org/licenses/>.
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:tt="http://www.w3.org/ns/ttml"
                xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
                xmlns:exsl="http://exslt.org/common"
                xmlns:str="http://exslt.org/strings"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="tt ttp"
                extension-element-prefixes="exsl str"
                version="1.0">

<!--!!==========================================================================
TTML Utilities
Common templates to help with processing TTML documents.
:Revision:version="3.4" date="2012-03-01" status="final"

This stylesheet contains common utilities for working with TTML documents.
It contains templates for checking profiles and processing timing data.
-->


<!--@@==========================================================================
ttml.features
The supported features and extensions for TTML documents.
:Revision:version="3.4" date="2012-03-01" status="final"

This parameter lists the fully-qualified URIs of TTML features and extensions
supported by the stylesheets. The values are in the form of a space-separated
list, which MUST have both a leading and a trailing space.

The default value for this parameter is empty. Importing stylesheets should
set this to an appropriate value.
-->
<xsl:param name="ttml.features" select="''"/>


<!--**==========================================================================
ttml.time.range
Return the absolute begin and end times for a timed element.
:Revision: version="3.4" date="2012-03-02" status="final"
$node: The element containing timing attributes.
$range: The absolute range for the parent element.
$begin: The value of the #{begin} attribute.
$end: The value of the #{end} attribute.
$dur: The value of the #{dur} attribute.

This template returns the start and end time for a TTML element, based on the
#{begin}, #{end}, and #{dur} attributes. It returns each of them as numbers
of seconds, as returned by *{ttml.time.seconds}, separated by a comma. Begin
and end times are returned as absolute times, relative to the computed range
of the parent element. The parent range may be passed in the ${range} parameter.
If the parameter is empty, the parent range is computed automatically by calling
this template on the nearest ancestor of ${node} with a #{begin} attribute.

If both ${end} and ${dur} are provided, the end times for each are calculated,
and the one that results in the shortest duration is used.

If there is no end time for the element, the string #{∞} is used as the end time.
-->
<xsl:template name="ttml.time.range">
  <xsl:param name="node" select="."/>
  <xsl:param name="range"/>
  <xsl:param name="begin" select="$node/@begin"/>
  <xsl:param name="end" select="$node/@end"/>
  <xsl:param name="dur" select="$node/@dur"/>
  <xsl:variable name="range_">
    <xsl:choose>
      <xsl:when test="$range != ''">
        <xsl:value-of select="$range"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="par" select="$node/ancestor::tt:*[@begin][1]"/>
        <xsl:choose>
          <xsl:when test="$par">
            <xsl:for-each select="$par">
              <xsl:call-template name="ttml.time.range"/>
            </xsl:for-each>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="'0,∞'"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="begin_s">
    <xsl:call-template name="ttml.time.seconds">
      <xsl:with-param name="time" select="$begin"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:value-of select="number(substring-before($range_, ',')) + number($begin_s)"/>
  <xsl:text>,</xsl:text>
  <xsl:variable name="end_dur">
    <xsl:choose>
      <xsl:when test="$dur">
        <xsl:variable name="dur_s">
          <xsl:call-template name="ttml.time.seconds">
            <xsl:with-param name="time" select="$dur"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="number($dur_s) + number(substring-before($range_, ',')) + number($begin_s)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="'∞'"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="end_end">
    <xsl:choose>
      <xsl:when test="$end">
        <xsl:variable name="end_s">
          <xsl:call-template name="ttml.time.seconds">
            <xsl:with-param name="time" select="$end"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="end_ss" select="number(substring-before($range_, ',')) + number($end_s)"/>
        <xsl:choose>
          <xsl:when test="substring-after($range_, ',') = '∞'">
            <xsl:value-of select="$end_ss"/>
          </xsl:when>
          <xsl:when test="number(substring-after($range_, ',')) &lt; $end_ss">
            <xsl:value-of select="substring-after($range_, ',')"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$end_ss"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="substring-after($range_, ',')"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$end_end = '∞'">
      <xsl:value-of select="$end_dur"/>
    </xsl:when>
    <xsl:when test="$end_dur = '∞'">
      <xsl:value-of select="$end_end"/>
    </xsl:when>
    <xsl:when test="number($end_end) &lt; number($end_dur)">
      <xsl:value-of select="$end_end"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$end_dur"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
ttml.time.seconds
Return the number of seconds for a time expression.
:Revision: version="3.4" date="2012-03-02" status="final"
$time: A TTML time expression.

This template takes a time expression as used by the #{begin}, #{end}, and #{dur}
attributes and returns the number of seconds that expression respresents. Time
expressions may be any number parsable by the XPath #{number} function followed
by one of the units #{ms} (milliseconds), #{s} (seconds), #{m} (minutes), or #{h}
(hours). It returns #{0} if the time expression is invalid.

This template provides support only for the #{#time-offset} TTML feature. It
does not support other methods of specifying times.
-->
<xsl:template name="ttml.time.seconds">
  <xsl:param name="time" select="0"/>
  <xsl:variable name="time_" select="normalize-space($time)"/>
  <xsl:choose>
    <xsl:when test="substring($time_, string-length($time_) - 1) = 'ms'">
      <xsl:variable name="ms">
        <xsl:value-of select="substring($time_, 1, string-length($time_) - 2)"/>
      </xsl:variable>
      <xsl:value-of select="number($ms) div 1000"/>
    </xsl:when>
    <xsl:when test="substring($time_, string-length($time_)) = 's'">
      <xsl:value-of select="substring($time_, 1, string-length($time_) - 1)"/>
    </xsl:when>
    <xsl:when test="substring($time_, string-length($time_)) = 'm'">
      <xsl:value-of select="60 * number(substring($time_, 1, string-length($time_) - 1))"/>
    </xsl:when>
    <xsl:when test="substring($time_, string-length($time_)) = 'h'">
      <xsl:value-of select="3600 * number(substring($time_, 1, string-length($time_) - 1))"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="0"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
ttml.profile
Check whether the stylesheets conform to a #{ttp:profile} element.
:Revision: version="3.4" date="2012-03-01" status="final"
$node: The #{ttp:profile} element to check.

This template takes a #{ttp:profile} element in the ${node} parameter and
determines whether or not the stylesheets meet all required features and
extensions, per section 5.2 of the TTML 1.0 recommendation. This template
uses the @{ttml.features} stylesheet parameter to determine which features
are supported by the stylesheet. It returns the string #{"true"} if all
required features are supported, #{"false"} otherwise.
-->
<xsl:template name="ttml.profile">
  <xsl:param name="node" select="."/>
  <xsl:variable name="features">
    <xsl:if test="$node/@use">
      <xsl:variable name="uri">
        <xsl:if test="not(contains($node/@use, ':'))">
          <xsl:text>http://www.w3.org/ns/ttml/profile/</xsl:text>
        </xsl:if>
        <xsl:value-of select="$node/@use"/>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$uri = 'http://www.w3.org/ns/ttml/profile/dfxp-presentation'">
          <xsl:for-each select="str:split($ttml.features.dfxp_presentation)">
            <ttp:feature value="required">
              <xsl:value-of select="."/>
            </ttp:feature>
          </xsl:for-each>
        </xsl:when>
        <xsl:when test="$uri = 'http://www.w3.org/ns/ttml/profile/dfxp-transformation'">
          <xsl:for-each select="str:split($ttml.features.dfxp_transformation)">
            <ttp:feature value="required">
              <xsl:value-of select="."/>
            </ttp:feature>
          </xsl:for-each>
        </xsl:when>
        <xsl:when test="$uri = 'http://www.w3.org/ns/ttml/profile/dfxp-full'">
          <xsl:for-each select="str:split($ttml.features.dfxp_full)">
            <ttp:feature value="required">
              <xsl:value-of select="."/>
            </ttp:feature>
          </xsl:for-each>
        </xsl:when>
        <xsl:otherwise>
          <xsl:variable name="use_profile" select="document($uri, $node)/ttp:profile"/>
          <xsl:for-each select="$use_profile/ttp:features/ttp:feature |
                                $use_profile/ttp:extensions/ttp:extension">
            <ttp:feature value="{@value}">
              <xsl:if test="not(contains(., ':'))">
                <xsl:value-of select="ancestor-or-self::*[@xml:base][1]/@xml:base"/>
              </xsl:if>
              <xsl:value-of select="normalize-space(.)"/>
            </ttp:feature>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:for-each select="$node/ttp:features/ttp:feature | $node/ttp:extensions/ttp:extension">
      <ttp:feature value="{@value}">
        <xsl:if test="not(contains(., ':'))">
          <xsl:value-of select="ancestor-or-self::*[@xml:base][1]/@xml:base"/>
        </xsl:if>
        <xsl:value-of select="normalize-space(.)"/>
      </ttp:feature>
    </xsl:for-each>
  </xsl:variable>
  <xsl:variable name="ok">
    <xsl:for-each select="exsl:node-set($features)/ttp:feature">
      <xsl:if test="@value != 'optional'">
        <xsl:variable name="feature" select="string(.)"/>
        <xsl:if test="not(following-sibling::ttp:feature[string(.) = $feature][@value = 'optional'])">
          <xsl:if test="not(contains($ttml.features, concat(' ', $feature, ' ')))">
            <xsl:text>x</xsl:text>
          </xsl:if>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$ok = ''">
      <xsl:text>true</xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>false</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
ttml.profile.attr
Check whether the stylesheets conform to a #{profile} attribute.
:Revision: version="3.4" date="2012-03-02" status="final"
$node: A #{tt:tt} element containing a #{profile} attribute.
$profile: The #{profile} attribute to check.

This template checks if the stylesheets comply with a profile as specified by
the #{profile} attribute on a #{tt:tt} element. If the profile is one of the
pre-defined profiles (#{dfxp-transformation}, #{dfxp-presentation}, and
#{dfxp-full}), this template contains built-in rules for quicly checking
feature compliance. Otherwise, it downloads the referenced profile and calls
*{ttml.profile} on it.

Like *{ttml.profile}, this template returns the string #{"true"} if all
required features are supported, #{"false"} otherwise.
-->
<xsl:template name="ttml.profile.attr">
  <xsl:param name="node" select="."/>
  <xsl:param name="profile" select="$node/@profile"/>
  <xsl:variable name="uri">
    <xsl:if test="not(contains($profile, ':'))">
      <xsl:text>http://www.w3.org/ns/ttml/profile/</xsl:text>
    </xsl:if>
    <xsl:value-of select="$profile"/>
  </xsl:variable>
  <xsl:variable name="features">
    <xsl:choose>
      <xsl:when test="$uri = 'http://www.w3.org/ns/ttml/profile/dfxp-presentation'">
        <xsl:value-of select="$ttml.features.dfxp_presentation"/>
      </xsl:when>
      <xsl:when test="$uri = 'http://www.w3.org/ns/ttml/profile/dfxp-transformation'">
        <xsl:value-of select="$ttml.features.dfxp_transformation"/>
      </xsl:when>
      <xsl:when test="$uri = 'http://www.w3.org/ns/ttml/profile/dfxp-full'">
        <xsl:value-of select="$ttml.features.dfxp_full"/>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$features != ''">
      <xsl:variable name="ok">
        <xsl:for-each select="str:split($features)">
          <xsl:if test="not(contains($ttml.features, concat(' ', ., ' ')))">
            <xsl:text>x</xsl:text>
          </xsl:if>
        </xsl:for-each>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$ok = ''">
          <xsl:text>true</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>false</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="ttml.profile">
        <xsl:with-param name="node" select="document($uri, $node)/ttp:profile"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- The required features for the dfxp-presentation profile -->
<xsl:variable name="ttml.features.dfxp_presentation" select="'
http://www.w3.org/ns/ttml/feature/#content
http://www.w3.org/ns/ttml/feature/#core
http://www.w3.org/ns/ttml/feature/#presentation
http://www.w3.org/ns/ttml/feature/#profile
http://www.w3.org/ns/ttml/feature/#structure
http://www.w3.org/ns/ttml/feature/#time-offset
http://www.w3.org/ns/ttml/feature/#timing
'"/>

<!-- The required features for the dfxp-transformation profile -->
<xsl:variable name="ttml.features.dfxp_transformation" select="'
http://www.w3.org/ns/ttml/feature/#content
http://www.w3.org/ns/ttml/feature/#core
http://www.w3.org/ns/ttml/feature/#profile
http://www.w3.org/ns/ttml/feature/#structure
http://www.w3.org/ns/ttml/feature/#time-offset
http://www.w3.org/ns/ttml/feature/#timing
http://www.w3.org/ns/ttml/feature/#transformation
'"/>

<!-- The required features for the dfxp-full profile -->
<xsl:variable name="ttml.features.dfxp_full" select="'
http://www.w3.org/ns/ttml/feature/#animation
http://www.w3.org/ns/ttml/feature/#backgroundColor-block
http://www.w3.org/ns/ttml/feature/#backgroundColor-inline
http://www.w3.org/ns/ttml/feature/#backgroundColor-region
http://www.w3.org/ns/ttml/feature/#backgroundColor
http://www.w3.org/ns/ttml/feature/#bidi
http://www.w3.org/ns/ttml/feature/#cellResolution
http://www.w3.org/ns/ttml/feature/#clockMode-gps
http://www.w3.org/ns/ttml/feature/#clockMode-local
http://www.w3.org/ns/ttml/feature/#clockMode-utc
http://www.w3.org/ns/ttml/feature/#clockMode
http://www.w3.org/ns/ttml/feature/#color
http://www.w3.org/ns/ttml/feature/#content
http://www.w3.org/ns/ttml/feature/#core
http://www.w3.org/ns/ttml/feature/#direction
http://www.w3.org/ns/ttml/feature/#display-block
http://www.w3.org/ns/ttml/feature/#display-inline
http://www.w3.org/ns/ttml/feature/#display-region
http://www.w3.org/ns/ttml/feature/#display
http://www.w3.org/ns/ttml/feature/#displayAlign
http://www.w3.org/ns/ttml/feature/#dropMode-dropNTSC
http://www.w3.org/ns/ttml/feature/#dropMode-dropPAL
http://www.w3.org/ns/ttml/feature/#dropMode-nonDrop
http://www.w3.org/ns/ttml/feature/#dropMode
http://www.w3.org/ns/ttml/feature/#extent-region
http://www.w3.org/ns/ttml/feature/#extent-root
http://www.w3.org/ns/ttml/feature/#extent
http://www.w3.org/ns/ttml/feature/#fontFamily-generic
http://www.w3.org/ns/ttml/feature/#fontFamily-non-generic
http://www.w3.org/ns/ttml/feature/#fontFamily
http://www.w3.org/ns/ttml/feature/#fontSize-anamorphic
http://www.w3.org/ns/ttml/feature/#fontSize-isomorphic
http://www.w3.org/ns/ttml/feature/#fontSize
http://www.w3.org/ns/ttml/feature/#fontStyle-italic
http://www.w3.org/ns/ttml/feature/#fontStyle-oblique
http://www.w3.org/ns/ttml/feature/#fontStyle
http://www.w3.org/ns/ttml/feature/#fontWeight-bold
http://www.w3.org/ns/ttml/feature/#fontWeight
http://www.w3.org/ns/ttml/feature/#frameRate
http://www.w3.org/ns/ttml/feature/#frameRateMultiplier
http://www.w3.org/ns/ttml/feature/#layout
http://www.w3.org/ns/ttml/feature/#length-cell
http://www.w3.org/ns/ttml/feature/#length-em
http://www.w3.org/ns/ttml/feature/#length-negative
http://www.w3.org/ns/ttml/feature/#length-percentage
http://www.w3.org/ns/ttml/feature/#length-pixel
http://www.w3.org/ns/ttml/feature/#length-positive
http://www.w3.org/ns/ttml/feature/#length-real
http://www.w3.org/ns/ttml/feature/#length
http://www.w3.org/ns/ttml/feature/#lineBreak-uax14
http://www.w3.org/ns/ttml/feature/#lineHeight
http://www.w3.org/ns/ttml/feature/#markerMode-continuous
http://www.w3.org/ns/ttml/feature/#markerMode-discontinuous
http://www.w3.org/ns/ttml/feature/#markerMode
http://www.w3.org/ns/ttml/feature/#metadata-foreign
http://www.w3.org/ns/ttml/feature/#metadata
http://www.w3.org/ns/ttml/feature/#nested-div
http://www.w3.org/ns/ttml/feature/#nested-span
http://www.w3.org/ns/ttml/feature/#opacity
http://www.w3.org/ns/ttml/feature/#origin
http://www.w3.org/ns/ttml/feature/#overflow-scroll
http://www.w3.org/ns/ttml/feature/#overflow-visible
http://www.w3.org/ns/ttml/feature/#overflow
http://www.w3.org/ns/ttml/feature/#padding-1
http://www.w3.org/ns/ttml/feature/#padding-2
http://www.w3.org/ns/ttml/feature/#padding-3
http://www.w3.org/ns/ttml/feature/#padding-4
http://www.w3.org/ns/ttml/feature/#padding
http://www.w3.org/ns/ttml/feature/#pixelAspectRatio
http://www.w3.org/ns/ttml/feature/#presentation
http://www.w3.org/ns/ttml/feature/#profile
http://www.w3.org/ns/ttml/feature/#showBackground
http://www.w3.org/ns/ttml/feature/#structure
http://www.w3.org/ns/ttml/feature/#styling-chained
http://www.w3.org/ns/ttml/feature/#styling-inheritance-content
http://www.w3.org/ns/ttml/feature/#styling-inheritance-region
http://www.w3.org/ns/ttml/feature/#styling-inline
http://www.w3.org/ns/ttml/feature/#styling-nested
http://www.w3.org/ns/ttml/feature/#styling-referential
http://www.w3.org/ns/ttml/feature/#styling
http://www.w3.org/ns/ttml/feature/#subFrameRate
http://www.w3.org/ns/ttml/feature/#textAlign-absolute
http://www.w3.org/ns/ttml/feature/#textAlign-relative
http://www.w3.org/ns/ttml/feature/#textAlign
http://www.w3.org/ns/ttml/feature/#textDecoration-over
http://www.w3.org/ns/ttml/feature/#textDecoration-through
http://www.w3.org/ns/ttml/feature/#textDecoration-under
http://www.w3.org/ns/ttml/feature/#textDecoration
http://www.w3.org/ns/ttml/feature/#textOutline-blurred
http://www.w3.org/ns/ttml/feature/#textOutline-unblurred
http://www.w3.org/ns/ttml/feature/#textOutline
http://www.w3.org/ns/ttml/feature/#tickRate
http://www.w3.org/ns/ttml/feature/#time-clock-with-frames
http://www.w3.org/ns/ttml/feature/#time-clock
http://www.w3.org/ns/ttml/feature/#time-offset-with-frames
http://www.w3.org/ns/ttml/feature/#time-offset-with-ticks
http://www.w3.org/ns/ttml/feature/#time-offset
http://www.w3.org/ns/ttml/feature/#timeBase-clock
http://www.w3.org/ns/ttml/feature/#timeBase-media
http://www.w3.org/ns/ttml/feature/#timeBase-smpte
http://www.w3.org/ns/ttml/feature/#timeContainer
http://www.w3.org/ns/ttml/feature/#timing
http://www.w3.org/ns/ttml/feature/#transformation
http://www.w3.org/ns/ttml/feature/#unicodeBidi
http://www.w3.org/ns/ttml/feature/#visibility-block
http://www.w3.org/ns/ttml/feature/#visibility-inline
http://www.w3.org/ns/ttml/feature/#visibility-region
http://www.w3.org/ns/ttml/feature/#visibility
http://www.w3.org/ns/ttml/feature/#wrapOption
http://www.w3.org/ns/ttml/feature/#writingMode-horizontal-lr
http://www.w3.org/ns/ttml/feature/#writingMode-horizontal-rl
http://www.w3.org/ns/ttml/feature/#writingMode-horizontal
http://www.w3.org/ns/ttml/feature/#writingMode-vertical
http://www.w3.org/ns/ttml/feature/#writingMode
http://www.w3.org/ns/ttml/feature/#zIndex
'"/>

</xsl:stylesheet>
