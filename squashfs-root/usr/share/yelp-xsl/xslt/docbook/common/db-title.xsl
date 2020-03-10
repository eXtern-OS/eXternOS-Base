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
								xmlns:msg="http://projects.gnome.org/yelp/gettext/"
                exclude-result-prefixes="db msg"
                version="1.0">

<!--!!==========================================================================
DocBook Titles
Support for DocBook title, titleabbrev, and subtitle elements.
:Revision:version="3.4" date="2011-11-10" status="final"

This stylesheet contains templates for outputting titles based on title,
titleabbrev, or subtitle elements. It supports automatic titles for certain
elements with optional titles.
-->


<!--**==========================================================================
db.title
Output a title for an element.
:Revision:version="3.4" date="2011-11-10" status="final"
$node: The element to output the title of.
$info: The info child element of ${node}.

This template outputs the title of the element ${node} as it might be used for
a heading or for link text. For certain types of elements, this templates will
use a localized automatic title if no explicit title is provided.
-->
<xsl:template name="db.title">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="
    $node/appendixinfo   | $node/articleinfo        | $node/bibliographyinfo | $node/blockinfo    |
    $node/bookinfo       | $node/chapterinfo        | $node/glossaryinfo     | $node/indexinfo    |
    $node/objectinfo     | $node/partinfo           | $node/prefaceinfo      | $node/refentryinfo |
    $node/referenceinfo  | $node/refsect1info       | $node/refsect2info     | $node/refsect3info |
    $node/refsectioninfo | $node/refsynopsisdivinfo | $node/sect1info        | $node/sect2info    |
    $node/sect3infof     | $node/sect4info          | $node/sect5info        | $node/sectioninfo  |
    $node/setindexinfo   | $node/db:info "/>
  <xsl:choose>
    <xsl:when test="$node/self::anchor or $node/self::db:anchor">
      <xsl:variable name="target_chunk_id">
        <xsl:call-template name="db.chunk.chunk-id">
          <xsl:with-param name="node" select="."/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:variable name="target_chunk" select="key('db.id.key', $target_chunk_id)"/>
      <xsl:call-template name="db.title">
        <xsl:with-param name="node" select="$target_chunk"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::refentry/refmeta/refentrytitle or
                    $node/self::db:refentry/db:refmeta/db:refentrytitle">
      <xsl:apply-templates select="($node/refmeta/refentrytitle | $node/db:refmeta/db:refentrytitle)[1]/node()"/>
      <xsl:if test="$node/refmeta/manvolnum | $node/db:refmeta/db:manvolnum">
        <xsl:text>(</xsl:text>
        <xsl:apply-templates select="($node/refmeta/manvolnum | $node/db:refmeta/db:manvolnum)[1]/node()"/>
        <xsl:text>)</xsl:text>
      </xsl:if>
    </xsl:when>
    <xsl:when test="$node/title or $node/db:title">
      <xsl:apply-templates select="$node/title/node() | $node/db:title/node()"/>
    </xsl:when>
    <xsl:when test="$info/title or $info/db:title">
      <xsl:apply-templates select="$info/title/node() | $info/db:title/node()"/>
    </xsl:when>
    <xsl:when test="$node/self::bibliography or $node/self::db:bibliography">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Bibliography'"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::colophon or $node/self::db:colophon">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Colophon'"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::dedication or $node/self::db:dedication">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Dedication'"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::glossary or $node/self::db:glossary">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Glossary'"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::glossentry or $node/self::db:glossentry">
      <xsl:apply-templates select="$node/glossterm/node() | $node/db:glossterm/node()"/>
    </xsl:when>
    <xsl:when test="$node/self::index or $node/self::db:index or
                    $node/self::setindex or $node/self::db:setindex">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Index'"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::qandaentry or $node/self::db:qandaentry">
      <xsl:call-template name="db.title">
        <xsl:with-param name="node" select="question | db:question"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/self::question or $node/self::db:question">
      <xsl:apply-templates select="($node//para | $node//db:para)[1]/node()"/>
    </xsl:when>
    <xsl:when test="$node/self::refentry or $node/self::db:refentry">
      <xsl:apply-templates select="($node/refnamediv/refname | $node/db:refnamediv/db:refname)[1]/node()"/>
    </xsl:when>
    <xsl:when test="$node/self::refsynopsisdiv or $node/self::db:refsynopsisdiv">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Synopsis'"/>
      </xsl:call-template>
    </xsl:when>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db.titleabbrev
Output an abbreviated title for an element.
:Revision:version="3.4" date="2011-11-10" status="final"
$node: The element to output the abbreviated title of.
$info: The info child element of ${node}.

This template outputs the abbreviated title of the element ${node}, which is
sometimes used for link text. If no explicit #{titleabbrev} element is found,
this template just calls *{db.title}.
-->
<xsl:template name="db.titleabbrev">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="
    $node/appendixinfo   | $node/articleinfo        | $node/bibliographyinfo | $node/blockinfo    |
    $node/bookinfo       | $node/chapterinfo        | $node/glossaryinfo     | $node/indexinfo    |
    $node/objectinfo     | $node/partinfo           | $node/prefaceinfo      | $node/refentryinfo |
    $node/referenceinfo  | $node/refsect1info       | $node/refsect2info     | $node/refsect3info |
    $node/refsectioninfo | $node/refsynopsisdivinfo | $node/sect1info        | $node/sect2info    |
    $node/sect3infof     | $node/sect4info          | $node/sect5info        | $node/sectioninfo  |
    $node/setindexinfo   | $node/db:info "/>
  <xsl:variable name="titleabbrev" select="
    $node/titleabbrev | $node/db:titleabbrev | $info/titleabbrev | $info/db:titleabbrev"/>
  <xsl:choose>
    <xsl:when test="$titleabbrev">
      <xsl:apply-templates select="$titleabbrev[1]/node()"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="db.title">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="info" select="$info"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db.subtitle
Output a subtitle for an element.
:Revision:version="3.4" date="2011-11-10" status="final"
$node: The element to output the subtitle of.
$info: The info child element of ${node}.

This template outputs the subtitle of the element ${node}, which is sometimes
used for link text. If no explicit #{titleabbrev} element is found, this template
just calls *{db.title}. This template is not suitable for determining whehter a
subtitle should be placed in a heading, as it will always return the title if
a subtitle is not found.
-->
<xsl:template name="db.subtitle">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="
    $node/appendixinfo   | $node/articleinfo        | $node/bibliographyinfo | $node/blockinfo    |
    $node/bookinfo       | $node/chapterinfo        | $node/glossaryinfo     | $node/indexinfo    |
    $node/objectinfo     | $node/partinfo           | $node/prefaceinfo      | $node/refentryinfo |
    $node/referenceinfo  | $node/refsect1info       | $node/refsect2info     | $node/refsect3info |
    $node/refsectioninfo | $node/refsynopsisdivinfo | $node/sect1info        | $node/sect2info    |
    $node/sect3infof     | $node/sect4info          | $node/sect5info        | $node/sectioninfo  |
    $node/setindexinfo   | $node/db:info "/>
  <xsl:variable name="subtitle" select="
    $node/subtitle | $node/db:subtitle | $info/subtitle | $info/db:subtitle"/>
  <xsl:choose>
    <xsl:when test="$subtitle">
      <xsl:apply-templates select="$subtitle[1]/node()"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="db.title">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="info" select="$info"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

</xsl:stylesheet>
