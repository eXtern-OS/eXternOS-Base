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
                xmlns:tt="http://www.w3.org/ns/ttml"
                xmlns:ttp="http://www.w3.org/ns/ttml#parameter"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal tt ttp"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - Media Elements
Handle Mallard media elements.
:Revision:version="3.8" date="2012-11-05" status="final"

This stylesheet contains templates for handling Mallard #{media} elements.
It also handles TTML inside block audio and video #{media} elements.
-->


<!--**==========================================================================
mal2html.media.image
Output an #{img} element for an image.
:Revision:version="3.8" date="2012-11-05" status="final"
$node: The Mallard #{media} element.
$inline: Whether ${node} is inline.

This template outputs an HTML #{img} element for a Mallard #{media} element
with the #{type} attribute set to #{"image"} (or with no #{type} attribute).
If ${node} has fallback content, it is used for the #{alt} attribute.
-->
<xsl:template name="mal2html.media.image">
  <xsl:param name="node" select="."/>
  <xsl:param name="inline" select="false()"/>
  <img src="{$node/@src}">
    <xsl:copy-of select="@height"/>
    <xsl:copy-of select="@width"/>
    <xsl:attribute name="class">
      <xsl:text>media </xsl:text>
      <xsl:choose>
        <xsl:when test="$inline">
          <xsl:text>media-inline</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>media-block</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
    <xsl:attribute name="alt">
      <xsl:choose>
        <xsl:when test="$inline">
          <xsl:variable name="alt">
            <xsl:apply-templates mode="mal2html.inline.mode" select="$node/node()"/>
          </xsl:variable>
          <xsl:value-of select="normalize-space($alt)"/>
        </xsl:when>
        <xsl:otherwise>
          <!-- FIXME: This is not ideal.  Nested block container elements
               will introduce lots of garbage whitespace.  But then, XML
               processors are supposed to normalize whitespace in attribute
               values anyway.  Ideally, we'd have a set of modes for text
               conversion.  That'd probably be best handled in a set of
               mal2text stylesheets.
          -->
          <xsl:for-each select="$node/mal:*">
            <xsl:if test="position() &gt; 1">
              <xsl:text>&#x000A;</xsl:text>
            </xsl:if>
            <xsl:value-of select="string(.)"/>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
  </img>
</xsl:template>


<!--**==========================================================================
mal2html.media.video
Output a #{video} element for a video.
:Revision:version="3.8" date="2012-11-05" status="final"
$node: The Mallard #{media} element.
$inline: Whether ${node} is inline.

This template outputs an HTML #{video} element for a Mallard #{media} element
with the #{type} attribute set to #{"video"}. It converts any fallback content
in the source to the #{video} element's fallback content. If ${inline} is
#{false}, this template will process TTML child content.

If ${node} has a child image #{media} element with the #{style} attribute set
to #{"poster"}, that image will be used for the #{poster} attribute on the
HTML #{video} element.
-->
<xsl:template name="mal2html.media.video">
  <xsl:param name="node" select="."/>
  <xsl:param name="inline" select="false()"/>
  <video src="{$node/@src}" preload="auto" controls="controls">
    <xsl:attribute name="class">
      <xsl:text>media </xsl:text>
      <xsl:choose>
        <xsl:when test="$inline">
          <xsl:text>media-inline</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>media-block</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
    <xsl:copy-of select="$node/@height"/>
    <xsl:copy-of select="$node/@width"/>
    <xsl:variable name="poster"
                  select="$node/mal:media[not(@type) or @type = 'image'][@style = 'poster']"/>
    <xsl:if test="$poster">
      <xsl:attribute name="poster">
        <xsl:value-of select="$poster[1]/@src"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:attribute name="data-play-label">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Play'"/>
      </xsl:call-template>
    </xsl:attribute>
    <xsl:attribute name="data-pause-label">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Pause'"/>
      </xsl:call-template>
    </xsl:attribute>
    <xsl:choose>
      <xsl:when test="$inline">
        <xsl:apply-templates mode="mal2html.inline.mode" select="$node/node()"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="mal2html.block.mode" select="$node/node()"/>
      </xsl:otherwise>
    </xsl:choose>
  </video>
  <xsl:if test="not($inline)">
    <xsl:apply-templates mode="mal2html.ttml.mode" select="tt:tt[1]"/>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
mal2html.media.audio
Output an #{audio} element for an audio object.
:Revision:version="3.8" date="2012-11-05" status="final"
$node: The Mallard #{media} element.
$inline: Whether ${node} is inline.

This template outputs an HTML #{audio} element for a Mallard #{media} element
with the #{type} attribute set to #{"audio"}. It converts any fallback content
in the source to the #{audio} element's fallback content. If ${inline} is
#{false}, this template will process TTML child content.
-->
<xsl:template name="mal2html.media.audio">
  <xsl:param name="node" select="."/>
  <xsl:param name="inline" select="false()"/>
  <audio src="{$node/@src}" preload="auto" controls="controls">
    <xsl:attribute name="class">
      <xsl:text>media </xsl:text>
      <xsl:choose>
        <xsl:when test="$inline">
          <xsl:text>media-inline</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>media-block</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
    <xsl:attribute name="data-play-label">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Play'"/>
      </xsl:call-template>
    </xsl:attribute>
    <xsl:attribute name="data-pause-label">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Pause'"/>
      </xsl:call-template>
    </xsl:attribute>
    <xsl:choose>
      <xsl:when test="$inline">
        <xsl:apply-templates mode="mal2html.inline.mode" select="$node/node()"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="mal2html.block.mode" select="$node/node()"/>
      </xsl:otherwise>
    </xsl:choose>
  </audio>
  <xsl:if test="not($inline)">
    <xsl:apply-templates mode="mal2html.ttml.mode" select="tt:tt[1]"/>
  </xsl:if>
</xsl:template>


<!-- == TTML == -->

<xsl:template mode="mal2html.block.mode" match="tt:*"/>

<!--%%==========================================================================
mal2html.ttml.mode
Process TTML subtitles in a Mallard #{media} element.
:Revision:version="3.8" date="2012-11-05" status="final"

This mode is applied to TTML elements inside block audio and video elements.
It outputs HTML elements that are hidden by default and shown dynamically as
the parent media element is played.
-->
<xsl:template mode="mal2html.ttml.mode" match="tt:tt">
  <xsl:variable name="profile">
    <xsl:choose>
      <xsl:when test="tt:head/ttp:profile">
        <xsl:for-each select="tt:head/ttp:profile">
          <xsl:call-template name="ttml.profile"/>
        </xsl:for-each>
      </xsl:when>
      <xsl:when test="@profile">
        <xsl:call-template name="ttml.profile.attr"/>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="not(contains($profile, 'false'))">
      <xsl:variable name="if">
        <xsl:call-template name="mal.if.test"/>
      </xsl:variable>
      <xsl:choose>
        <xsl:when test="$if = 'true'">
          <xsl:apply-templates mode="mal2html.ttml.mode" select="tt:body"/>
        </xsl:when>
        <xsl:when test="$if != ''">
          <div class="if-if {$if}">
            <xsl:apply-templates mode="mal2html.ttml.mode" select="tt:body"/>
          </div>
        </xsl:when>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="mal2html.ttml.mode"
                           select="following-sibling::tt:tt[1]"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template mode="mal2html.ttml.mode" match="tt:body">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>media-ttml</xsl:text>
        <xsl:choose>
          <xsl:when test="@xml:space">
            <xsl:if test="@xml:space='preserve'">
              <xsl:text> media-ttml-pre</xsl:text>
            </xsl:if>
            <xsl:if test="@xml:space='default'">
              <xsl:text> media-ttml-nopre</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:otherwise>
            <xsl:if test="../@xml:space='preserve'">
              <xsl:text> media-ttml-pre</xsl:text>
            </xsl:if>
            <xsl:if test="../@xml:space='default'">
              <xsl:text> media-ttml-nopre</xsl:text>
            </xsl:if>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="parent" select="../self::tt:tt"/>
    </xsl:call-template>
    <xsl:apply-templates mode="mal2html.ttml.mode" select="tt:div">
      <xsl:with-param name="range">
        <xsl:call-template name="ttml.time.range"/>
      </xsl:with-param>
    </xsl:apply-templates>
  </div>
</xsl:template>

<xsl:template mode="mal2html.ttml.mode" match="tt:div">
  <xsl:param name="range"/>
  <xsl:variable name="beginend">
    <xsl:call-template name="ttml.time.range">
      <xsl:with-param name="range" select="$range"/>
    </xsl:call-template>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>media-ttml-node media-ttml-div</xsl:text>
        <xsl:if test="@xml:space='preserve'">
          <xsl:text> media-ttml-pre</xsl:text>
        </xsl:if>
        <xsl:if test="@xml:space='default'">
          <xsl:text> media-ttml-nopre</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:copy-of select="@xml:space"/>
    <xsl:attribute name="data-ttml-begin">
      <xsl:value-of select="substring-before($beginend, ',')"/>
    </xsl:attribute>
    <xsl:variable name="end" select="substring-after($beginend, ',')"/>
    <xsl:if test="$end != '∞'">
      <xsl:attribute name="data-ttml-end">
        <xsl:value-of select="$end"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:for-each select="*">
      <xsl:choose>
        <xsl:when test="self::tt:*">
          <xsl:apply-templates mode="mal2html.ttml.mode" select=".">
            <xsl:with-param name="range" select="$beginend"/>
          </xsl:apply-templates>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates mode="mal2html.block.mode" select="."/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
  </div>
</xsl:template>

<xsl:template mode="mal2html.ttml.mode" match="tt:p">
  <xsl:param name="range"/>
  <xsl:variable name="beginend">
    <xsl:call-template name="ttml.time.range">
      <xsl:with-param name="range" select="$range"/>
    </xsl:call-template>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>media-ttml-node media-ttml-p</xsl:text>
        <xsl:if test="@xml:space='preserve'">
          <xsl:text> media-ttml-pre</xsl:text>
        </xsl:if>
        <xsl:if test="@xml:space='default'">
          <xsl:text> media-ttml-nopre</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:attribute name="data-ttml-begin">
      <xsl:value-of select="substring-before($beginend, ',')"/>
    </xsl:attribute>
    <xsl:variable name="end" select="substring-after($beginend, ',')"/>
    <xsl:if test="$end != '∞'">
      <xsl:attribute name="data-ttml-end">
        <xsl:value-of select="$end"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates mode="mal2html.inline.mode">
      <xsl:with-param name="range" select="$beginend"/>
    </xsl:apply-templates>
  </div>
</xsl:template>

<xsl:template mode="mal2html.inline.mode" match="tt:span">
  <xsl:param name="range"/>
  <xsl:variable name="beginend">
    <xsl:call-template name="ttml.time.range">
      <xsl:with-param name="range" select="$range"/>
    </xsl:call-template>
  </xsl:variable>
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>media-ttml-node media-ttml-span</xsl:text>
        <xsl:if test="@xml:space='preserve'">
          <xsl:text> media-ttml-pre</xsl:text>
        </xsl:if>
        <xsl:if test="@xml:space='default'">
          <xsl:text> media-ttml-nopre</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:attribute name="data-ttml-begin">
      <xsl:value-of select="substring-before($beginend, ',')"/>
    </xsl:attribute>
    <xsl:variable name="end" select="substring-after($beginend, ',')"/>
    <xsl:if test="$end != '∞'">
      <xsl:attribute name="data-ttml-end">
        <xsl:value-of select="substring-after($beginend, ',')"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates mode="mal2html.inline.mode"/>
  </span>
</xsl:template>

<xsl:template mode="mal2html.inline.mode" match="tt:br">
  <br>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'media-ttml-br'"/>
    </xsl:call-template>
  </br>
</xsl:template>



<!-- == Matched Templates == -->

<!-- = mal2html.block.mode % media = -->
<xsl:template mode="mal2html.block.mode" match="mal:media">
  <xsl:variable name="if">
    <xsl:call-template name="mal.if.test"/>
  </xsl:variable>
  <xsl:variable name="style" select="concat(' ', @style, ' ')"/>
  <xsl:variable name="class">
    <xsl:choose>
      <xsl:when test="contains($style, ' floatstart ')">
        <xsl:text> floatstart</xsl:text>
      </xsl:when>
      <xsl:when test="contains($style, ' floatend ')">
        <xsl:text> floatend</xsl:text>
      </xsl:when>
      <xsl:when test="contains($style, ' floatleft ')">
        <xsl:text> floatleft</xsl:text>
      </xsl:when>
      <xsl:when test="contains($style, ' floatright ')">
        <xsl:text> floatright</xsl:text>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$if = ''"/>
    <xsl:when test="@type = 'image' or not(@type)">
      <div>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="class">
            <xsl:text>media media-image</xsl:text>
            <xsl:value-of select="$class"/>
            <xsl:if test="$if != 'true'">
              <xsl:text> if-if </xsl:text>
              <xsl:value-of select="$if"/>
            </xsl:if>
          </xsl:with-param>
        </xsl:call-template>
        <div class="inner">
          <xsl:call-template name="mal2html.media.image"/>
        </div>
      </div>
    </xsl:when>
    <xsl:when test="@type = 'video'">
      <div>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="class">
            <xsl:text>media media-video</xsl:text>
            <xsl:value-of select="$class"/>
            <xsl:if test="$if != 'true'">
              <xsl:text> if-if </xsl:text>
              <xsl:value-of select="$if"/>
            </xsl:if>
          </xsl:with-param>
        </xsl:call-template>
        <div class="inner">
          <xsl:call-template name="mal2html.media.video"/>
        </div>
      </div>
    </xsl:when>
    <xsl:when test="@type = 'audio'">
      <div>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="class">
            <xsl:text>media media-audio</xsl:text>
            <xsl:value-of select="$class"/>
            <xsl:if test="$if != 'true'">
              <xsl:text> if-if </xsl:text>
              <xsl:value-of select="$if"/>
            </xsl:if>
          </xsl:with-param>
        </xsl:call-template>
        <div class="inner">
          <xsl:call-template name="mal2html.media.audio"/>
        </div>
      </div>
    </xsl:when>
    <xsl:otherwise>
      <xsl:for-each select="mal:*">
        <xsl:apply-templates mode="mal2html.block.mode" select="."/>
      </xsl:for-each>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = mal2html.inline.mode % media = -->
<xsl:template mode="mal2html.inline.mode" match="mal:media">
  <xsl:call-template name="mal2html.span"/>
</xsl:template>

<xsl:template mode="mal2html.inline.content.mode" match="mal:media">
  <xsl:choose>
    <xsl:when test="@type = 'image' or not(@type)">
      <span class="media media-image">
        <xsl:call-template name="mal2html.media.image">
          <xsl:with-param name="inline" select="true()"/>
        </xsl:call-template>
      </span>
    </xsl:when>
    <xsl:when test="@type = 'video'">
      <span class="media media-video">
        <xsl:call-template name="mal2html.media.video">
          <xsl:with-param name="inline" select="true()"/>
        </xsl:call-template>
      </span>
    </xsl:when>
    <xsl:when test="@type = 'audio'">
      <span class="media media-audio">
        <xsl:call-template name="mal2html.media.audio">
          <xsl:with-param name="inline" select="true()"/>
        </xsl:call-template>
      </span>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="mal2html.inline.mode"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
