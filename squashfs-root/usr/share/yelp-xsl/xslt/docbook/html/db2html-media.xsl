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
                xmlns:mml="http://www.w3.org/1998/Math/MathML"
                xmlns:str="http://exslt.org/strings"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db mml str"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Images and Media
Handle DocBook media elements.
:Revision:version="3.8" date="2012-11-13" status="final"

This stylesheet contains templates for handling DocBook #{mediaobject} and
#{inlinemediaobject} elements, as well as the various #{object} and #{data}
elements found in these elements. This stylesheet also handles the deprecated
DocBook 4 #{graphic} and #{inlinegraphic} elements.
-->


<!--**==========================================================================
db2html.audiodata
Output an HTML #{audio} element for a #{audiodata} element.
:Revision:version="3.8" date="2012-11-12" status="final"
$node: The #{audiodata} element.

This template creates an #{audio} element in the HTML output. This template
calls *{db2html.mediaobject.fallback} for the contents of the #{audio} element.
-->
<xsl:template name="db2html.audiodata">
  <xsl:param name="node" select="."/>
  <xsl:variable name="media" select="($node/ancestor::mediaobject[1] |
                                      $node/ancestor::inlinemediaobject[1] |
                                      $node/ancestor::db:mediaobject[1] |
                                      $node/ancestor::db:inlinemediaobject[1]
                                     )[last()]"/>
  <audio preload="auto" controls="controls">
    <xsl:attribute name="src">
      <xsl:choose>
        <xsl:when test="$node/@fileref">
          <xsl:value-of select="$node/@fileref"/>
        </xsl:when>
        <xsl:when test="$node/@entityref">
          <xsl:value-of select="unparsed-entity-uri($node/@entityref)"/>
        </xsl:when>
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
    <xsl:call-template name="db2html.mediaobject.fallback">
      <xsl:with-param name="node" select="$media"/>
    </xsl:call-template>
  </audio>
</xsl:template>


<!--**==========================================================================
db2html.imagedata
Output an HTML #{img} element for a #{imagedata} element.
:Revision:version="3.10" date="2013-08-11" status="final"
$node: The #{imagedata} or other graphic element.

This template creates an #{img} element in the HTML output.  This template
is called not only for #{imagedata} elements, but also for #{graphic} and
#{inlinegraphic} elements.  Note that #{graphic} and #{inlinegraphic} are
deprecated and should not be used in any newly-written DocBook files.  Use
#{mediaobject} instead.

This template looks for a #{textobject} with a #{phrase} child in an ancestor
#{mediaobject} or #{inlinemediaobject} element. It uses the first available,
taking conditional processing into consideration.
-->
<xsl:template name="db2html.imagedata">
  <xsl:param name="node" select="."/>
  <img>
    <xsl:attribute name="src">
      <xsl:choose>
        <xsl:when test="$node/@fileref">
          <xsl:value-of select="$node/@fileref"/>
        </xsl:when>
        <xsl:when test="$node/@entityref">
          <xsl:value-of select="unparsed-entity-uri($node/@entityref)"/>
        </xsl:when>
      </xsl:choose>
    </xsl:attribute>
    <xsl:if test="$node/@contentwidth">
      <xsl:attribute name="width">
        <xsl:value-of select="$node/@contentwidth"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="$node/@contentdepth">
      <xsl:attribute name="height">
        <xsl:value-of select="$node/@contentdepth"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:variable name="media" select="(self::imagedata/ancestor::mediaobject[1] |
                                        self::imagedata/ancestor::inlinemediaobject[1] |
                                        self::db:imagedata/ancestor::db:mediaobject[1] |
                                        self::db:imagedata/ancestor::db:inlinemediaobject[1]
                                       )[last()]"/>
    <xsl:variable name="alt" select="$media/textobject[phrase] | $media/db:textobject[db:phrase]"/>
    <xsl:variable name="altpos">
      <xsl:for-each select="$alt">
        <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
        <xsl:if test="$if != ''">
          <xsl:value-of select="concat(',', position())"/>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:if test="$altpos != ''">
      <xsl:attribute name="alt">
        <xsl:variable name="obj" select="$alt[position() = number(str:split($altpos, ',')[1])]"/>
        <xsl:value-of select="$obj/phrase | $obj/db:phrase"/>
      </xsl:attribute>
    </xsl:if>
  </img>
</xsl:template>


<!--**==========================================================================
db2html.videodata
Output an HTML #{video} element for a #{videodata} element.
:Revision:version="3.8" date="2012-11-12" status="final"
$node: The #{videodata} element.

This template creates a #{video} element in the HTML output. If the containing
#{mediaobject} or #{inlinemediaobject} element has an #{imageobject} with the
#{role} attribute set to #{"poster"}, that image will be used for the #{poster}
attribute on the HTML #{video} element. This template calls
*{db2html.mediaobject.fallback} for the contents of the #{video} element.
-->
<xsl:template name="db2html.videodata">
  <xsl:param name="node" select="."/>
  <xsl:variable name="media" select="($node/ancestor::mediaobject[1] |
                                      $node/ancestor::inlinemediaobject[1] |
                                      $node/ancestor::db:mediaobject[1] |
                                      $node/ancestor::db:inlinemediaobject[1]
                                     )[last()]"/>
  <video preload="auto" controls="controls">
    <xsl:attribute name="src">
      <xsl:choose>
        <xsl:when test="$node/@fileref">
          <xsl:value-of select="$node/@fileref"/>
        </xsl:when>
        <xsl:when test="$node/@entityref">
          <xsl:value-of select="unparsed-entity-uri($node/@entityref)"/>
        </xsl:when>
      </xsl:choose>
    </xsl:attribute>
    <xsl:if test="$node/@contentwidth">
      <xsl:attribute name="width">
        <xsl:value-of select="$node/@contentwidth"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="$node/@contentdepth">
      <xsl:attribute name="height">
        <xsl:value-of select="$node/@contentdepth"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:variable name="poster"
                  select="$media/imageobject[@role = 'poster']/imagedata |
                          $media/db:imageobject[@role = 'poster']/db:imagedata"/>
    <xsl:if test="$poster">
      <xsl:attribute name="poster">
        <xsl:choose>
          <xsl:when test="$poster/@fileref">
            <xsl:value-of select="$poster/@fileref"/>
          </xsl:when>
          <xsl:when test="$poster/@entityref">
            <xsl:value-of select="unparsed-entity-uri($poster/@entityref)"/>
          </xsl:when>
        </xsl:choose>
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
    <xsl:call-template name="db2html.mediaobject.fallback">
      <xsl:with-param name="node" select="$media"/>
    </xsl:call-template>
  </video>
</xsl:template>


<!--**==========================================================================
db2html.mediaobject
Outputs HTML for a #{mediaobject} element.
:Revision:version="3.10" date="2013-08-11" status="final"
$node: The #{mediaobject} element.

This template processes a #{mediaobject} element and outputs the appropriate
HTML. DocBook allows multiple objects to be listed in a #{mediaobject} element.
Processing tools are expected to choose the earliest suitable object. This
template will select the first audio, image, or video object it can handle,
filtering out images in non-web formats, and taking conditional processing
into consideration. If no suitable non-text objects are found, this template
calls *{db2html.mediaobject.fallback}.

This template also detects MathML embedded in a DocBook 5 #{imagedata} element
with the #{format} attribute #{"mathml"}, and passes it to the templates in
!{db2html-math}.
-->
<xsl:template name="db2html.mediaobject">
  <xsl:param name="node" select="."/>
  <xsl:variable name="objs" select="
    $node/audioobject | $node/db:audioobject |
    $node/videoobject | $node/db:videoobject |
    $node/imageobject[imagedata[
      @format = 'GIF'  or @format = 'GIF87a' or @format = 'GIF89a' or
      @format = 'JPEG' or @format = 'JPG'    or @format = 'PNG'    or
      not(@format)]] |
    $node/imageobjectco[imageobject/imagedata[
      @format = 'GIF'  or @format = 'GIF87a' or @format = 'GIF89a' or
      @format = 'JPEG' or @format = 'JPG'    or @format = 'PNG'    or
      not(@format)]] |
    $node/db:imageobject[db:imagedata[
      @format = 'GIF'  or @format = 'GIF87a' or @format = 'GIF89a' or
      @format = 'JPEG' or @format = 'JPG'    or @format = 'PNG'    or
      not(@format)]] |
    $node/db:imageobject[db:imagedata[@format = 'mathml'][mml:math]] |
    $node/db:imageobjectco[db:imageobject/db:imagedata[
      @format = 'GIF'  or @format = 'GIF87a' or @format = 'GIF89a' or
      @format = 'JPEG' or @format = 'JPG'    or @format = 'PNG'    or
      not(@format)]] "/>
  <xsl:variable name="objspos">
    <xsl:for-each select="$objs">
      <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
      <xsl:if test="$if != ''">
        <xsl:value-of select="concat(',', position())"/>
      </xsl:if>
    </xsl:for-each>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$objspos != ''">
      <xsl:apply-templates select="$objs[position() = number(str:split($objspos, ',')[1])]"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="db2html.mediaobject.fallback">
        <xsl:with-param name="node" select="$node"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db2html.mediaobject.fallback
Outputs fallback HTML for a #{mediaobject} element.
:Revision:version="3.10" date="2013-08-11" status="final"
$node: The #{mediaobject} element.

This template outputs HTML for the first suitable #{textobject} child element
of ${node}. If ${node} is an #{inlinemediaobject}, it looks for a #{textobject}
that contains a #{phrase} element. Otherwise, it looks for a #{textobject} with
normal block content. It also handles conditional processing on the #{textobject}
elements.
-->
<xsl:template name="db2html.mediaobject.fallback">
  <xsl:param name="node" select="."/>
  <xsl:choose>
    <xsl:when test="local-name($node) = 'inlinemediaobject'">
      <xsl:variable name="alt" select="$node/textobject[phrase] | $node/db:textobject[db:phrase]"/>
      <xsl:variable name="altpos">
        <xsl:for-each select="$alt">
          <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
          <xsl:if test="$if != ''">
            <xsl:value-of select="concat(',', position())"/>
          </xsl:if>
        </xsl:for-each>
      </xsl:variable>
      <xsl:if test="$altpos != ''">
        <xsl:variable name="obj" select="$alt[position() = number(str:split($altpos, ',')[1])]"/>
        <xsl:apply-templates select="$obj/phrase | $obj/db:phrase"/>
      </xsl:if>
    </xsl:when>
    <xsl:otherwise>
      <xsl:variable name="alt" select="$node/textobject[not(phrase or textdata)] |
                                       $node/db:textobject[not(db:phrase or db:textdata)]"/>
      <xsl:variable name="altpos">
        <xsl:for-each select="$alt">
          <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
          <xsl:if test="$if != ''">
            <xsl:value-of select="concat(',', position())"/>
          </xsl:if>
        </xsl:for-each>
      </xsl:variable>
      <xsl:if test="$altpos != ''">
        <xsl:apply-templates select="$alt[position() = number(str:split($altpos, ',')[1])]/*"/>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = audiodata = -->
<xsl:template match="mediaobject/audioobject/audiodata |
                     db:mediaobject/db:audioobject/db:audiodata">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'media media-audio'"/>
    </xsl:call-template>
    <div class="inner">
      <xsl:call-template name="db2html.audiodata">
        <xsl:with-param name="inline" select="false()"/>
      </xsl:call-template>
    </div>
  </div>
</xsl:template>
<xsl:template match="inlinemediaobject/audioobject/audiodata |
                     db:inlinemediaobject/db:audioobject/db:audiodata">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'media media-audio'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.audiodata"/>
  </span>
</xsl:template>

<!-- = audioobject = -->
<xsl:template match="audioobject | db:audioobject">
  <xsl:apply-templates select="audiodata | db:audiodata"/>
</xsl:template>

<!-- = graphic = -->
<xsl:template match="graphic">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'graphic'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:call-template name="db2html.imagedata"/>
  </div>
</xsl:template>

<!-- = imagedata = -->
<xsl:template match="imagedata | db:imagedata">
  <xsl:choose>
    <xsl:when test="@format = 'mathml' and mml:math">
      <xsl:apply-templates select="mml:math"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="db2html.imagedata"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = imageobject = -->
<xsl:template match="imageobject | db:imageobject">
  <xsl:apply-templates select="imagedata | db:imagedata"/>
</xsl:template>

<!-- = inlinegraphic = -->
<xsl:template match="inlinegraphic">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'inlinegraphic'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:call-template name="db2html.imagedata"/>
  </span>
</xsl:template>

<!-- = inlinemediaobject = -->
<xsl:template match="inlinemediaobject | db:inlinemediaobject">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'inlinemediaobject'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:call-template name="db2html.mediaobject"/>
  </span>
  </xsl:if>
</xsl:template>

<!-- = mediaojbect = -->
<xsl:template match="mediaobject | db:mediaobject">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'mediaobject'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:call-template name="db2html.mediaobject"/>
    <!-- When a figure contains only a single mediaobject, it eats the caption -->
    <xsl:if test="not(../self::figure or ../self::informalfigure or
                      ../self::db:figure or ../self::db:informalfigure) or
                  ../*[not(self::blockinfo) and not(self::title) and
                       not(self::db:info) and not(self::db:title) and
                       not(self::titleabbrev) and not(self::db:titleabbrev) and
                       not(. = current()) ]">
      <xsl:apply-templates select="caption | db:caption"/>
    </xsl:if>
  </div>
  </xsl:if>
</xsl:template>

<!-- = videodata = -->
<xsl:template match="mediaobject/videoobject/videodata |
                     db:mediaobject/db:videoobject/db:videodata">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'media media-video'"/>
    </xsl:call-template>
    <div class="inner">
      <xsl:call-template name="db2html.videodata">
        <xsl:with-param name="inline" select="false()"/>
      </xsl:call-template>
    </div>
  </div>
</xsl:template>
<xsl:template match="inlinemediaobject/videoobject/videodata |
                     db:inlinemediaobject/db:videoobject/db:videodata">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'media media-video'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.videodata"/>
  </span>
</xsl:template>

<!-- = videoobject = -->
<xsl:template match="videoobject | db:videoobject">
  <xsl:apply-templates select="videodata | db:videodata"/>
</xsl:template>

</xsl:stylesheet>
