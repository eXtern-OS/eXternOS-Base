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
                xmlns:ui="http://projectmallard.org/ui/1.0/"
                xmlns:uix="http://projectmallard.org/experimental/ui/"
                xmlns:msg="http://projects.gnome.org/yelp/gettext/"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal if ui uix msg"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - Blocks
Handle simple Mallard block elements.
:Revision:version="1.0" date="2010-06-03" status="final"

This stylesheet contains templates for handling most Mallard block elements,
except the list and table elements.
-->


<!--**==========================================================================
mal2html.pre
Output an HTML #{pre} element.
:Revision:version="3.12" date="2013-11-02" status="final"
$node: The source element to output a #{pre} for.

This template outputs an HTML #{pre} element along with a wrapper #{div} element
for CSS styling. It should be called for verbatim block elements. It will
automatically strip leading and trailing newlines using *{utils.strip_newlines}.

If @{html.syntax.highlight} is #{true}, this template automatically outputs
syntax highlighting support based on the #{mime} attribute of ${node}, using
*{html.syntax.class} to determine the correct highlighter.
-->
<xsl:template name="mal2html.pre">
  <xsl:param name="node" select="."/>
  <xsl:param name="numbered" select="contains(concat(' ', @style, ' '), 'numbered')"/>
  <xsl:variable name="if">
    <xsl:call-template name="mal.if.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <xsl:variable name="first" select="$node/node()[1]/self::text()"/>
  <xsl:variable name="last" select="$node/node()[last()]/self::text()"/>
  <div>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class">
        <xsl:value-of select="local-name($node)"/>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:if test="$numbered">
      <pre class="numbered"><xsl:call-template name="utils.linenumbering">
        <xsl:with-param name="node" select="$node"/>
      </xsl:call-template></pre>
    </xsl:if>
    <pre>
      <xsl:attribute name="class">
        <xsl:text>contents </xsl:text>
        <xsl:if test="$html.syntax.highlight and $node/@mime">
          <xsl:call-template name="html.syntax.class">
            <xsl:with-param name="node" select="$node"/>
          </xsl:call-template>
        </xsl:if>
      </xsl:attribute>
      <xsl:if test="$first">
        <xsl:call-template name="utils.strip_newlines">
          <xsl:with-param name="string" select="$first"/>
          <xsl:with-param name="leading" select="true()"/>
          <xsl:with-param name="trailing" select="count(node()) = 1"/>
        </xsl:call-template>
      </xsl:if>
      <xsl:apply-templates mode="mal2html.inline.mode"
                           select="node()[not(self::text() and (position() = 1 or position() = last()))]"/>
      <xsl:if test="$last and (count(node()) != 1)">
        <xsl:call-template name="utils.strip_newlines">
          <xsl:with-param name="string" select="$last"/>
          <xsl:with-param name="leading" select="false()"/>
          <xsl:with-param name="trailing" select="true()"/>
        </xsl:call-template>
      </xsl:if>
    </pre>
  </div>
</xsl:if>
</xsl:template>


<!--%%==========================================================================
mal2html.block.mode
Process Mallard elements in block mode.
:Revision:version="1.0" date="2010-06-03" status="final"
$restricted: Whether this is restricted block mode.

This mode is applied to elements in block context. It should be called by
templates for pages, sections, and block container elements. Certain elements
may appear in both block an inline mode, and the processing expectations for
those elements is different depending on context.

Implementations of this mode should generally output a wrapper div and process
the child elements, either in %{mal2html.block.mode} or %{mal2html.inline.mode},
or using special processing for particular content models.

When this mode encounters unknown content, templates in the same mode are
applied to the children, but the ${restricted} parameter is set to #{true}.
When ${restricted} is #{true}, unknown block elements are ignored. This is
in accordance with the Mallard specification on fallback block content.
-->
<xsl:template mode="mal2html.block.mode" match="*">
  <xsl:param name="restricted" select="false()"/>
  <xsl:if test="not($restricted)">
    <xsl:message>
      <xsl:text>Unmatched block element: </xsl:text>
      <xsl:value-of select="local-name(.)"/>
    </xsl:message>
    <xsl:apply-templates mode="mal2html.block.mode">
      <xsl:with-param name="restricted" select="true()"/>
    </xsl:apply-templates>
  </xsl:if>
</xsl:template>

<xsl:template mode="mal2html.block.mode" match="text()"/>


<!-- = desc = -->
<xsl:template mode="mal2html.block.mode" match="mal:desc">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>desc</xsl:text>
        <xsl:if test="contains(concat(' ', @style, ' '), ' center ')">
          <xsl:text> center</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates mode="mal2html.inline.mode"/>
  </div>
</xsl:template>

<!-- = code = -->
<xsl:template mode="mal2html.block.mode" match="mal:code">
  <xsl:call-template name="mal2html.pre"/>
</xsl:template>

<!-- = comment = -->
<xsl:template mode="mal2html.block.mode" match="mal:comment">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:if test="$mal2html.editor_mode
                or processing-instruction('mal2html.show_comment')">
    <div>
      <xsl:call-template name="html.lang.attrs"/>
      <xsl:call-template name="html.class.attr">
        <xsl:with-param name="class">
          <xsl:text>comment</xsl:text>
          <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
            <xsl:text> ui-expander</xsl:text>
          </xsl:if>
          <xsl:if test="$if != 'true'">
            <xsl:text> if-if </xsl:text>
            <xsl:value-of select="$if"/>
          </xsl:if>
        </xsl:with-param>
      </xsl:call-template>
      <xsl:call-template name="mal2html.ui.expander.data"/>
      <div class="inner">
        <xsl:apply-templates mode="mal2html.block.mode" select="mal:title"/>
        <div class="region">
          <xsl:apply-templates mode="mal2html.block.mode" select="mal:cite"/>
          <div class="contents">
            <xsl:for-each select="*[not(self::mal:title or self::mal:cite)]">
              <xsl:apply-templates mode="mal2html.block.mode" select="."/>
            </xsl:for-each>
          </div>
        </div>
      </div>
    </div>
  </xsl:if>
</xsl:if>
</xsl:template>

<!-- = comment/cite = -->
<xsl:template mode="mal2html.block.mode" match="mal:comment/mal:cite">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'cite cite-comment'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:choose>
      <xsl:when test="@date">
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="'comment.name-date'"/>
          <xsl:with-param name="node" select="."/>
          <xsl:with-param name="format" select="true()"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="'comment.name'"/>
          <xsl:with-param name="node" select="."/>
          <xsl:with-param name="format" select="true()"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </div>
</xsl:template>

<xsl:template mode="l10n.format.mode" match="msg:comment.name">
  <xsl:param name="node"/>
  <xsl:choose>
    <xsl:when test="$node/@href">
      <a href="{$node/@href}">
        <xsl:apply-templates mode="mal2html.inline.mode" select="$node/node()"/>
      </a>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="mal2html.inline.mode" select="$node/node()"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template mode="l10n.format.mode" match="msg:comment.date">
  <xsl:param name="node"/>
  <xsl:value-of select="$node/@date"/>
</xsl:template>

<!-- = example = -->
<xsl:template mode="mal2html.block.mode" match="mal:example">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>example</xsl:text>
        <xsl:if test="mal:title and @ui:expanded">
          <xsl:text> ui-expander</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title[1]"/>
      <div class="region">
        <xsl:apply-templates mode="mal2html.block.mode" select="mal:desc[1]"/>
        <div class="contents">
          <xsl:for-each select="*[not(self::mal:title or self::mal:desc)]">
            <xsl:apply-templates mode="mal2html.block.mode" select="."/>
          </xsl:for-each>
        </div>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = figure = -->
<xsl:template mode="mal2html.block.mode" match="mal:figure">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>figure</xsl:text>
        <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
          <xsl:text> ui-expander</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <a href="#" class="zoom">
        <xsl:attribute name="data-zoom-in-title">
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="msgid" select="'View images at normal size'"/>
          </xsl:call-template>
        </xsl:attribute>
        <xsl:attribute name="data-zoom-out-title">
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="msgid" select="'Scale images down'"/>
          </xsl:call-template>
        </xsl:attribute>
      </a>
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title[1]"/>
      <div class="region">
        <div class="contents">
          <xsl:for-each select="*[not(self::mal:title or self::mal:desc)]">
            <xsl:apply-templates mode="mal2html.block.mode" select="."/>
          </xsl:for-each>
        </div>
        <xsl:apply-templates mode="mal2html.block.mode" select="mal:desc[1]"/>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = listing = -->
<xsl:template mode="mal2html.block.mode" match="mal:listing">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>listing</xsl:text>
        <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
          <xsl:text> ui-expander</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title[1]"/>
      <div class="region">
        <xsl:apply-templates mode="mal2html.block.mode" select="mal:desc[1]"/>
        <div class="contents">
          <xsl:for-each select="*[not(self::mal:title or self::mal:desc)]">
            <xsl:apply-templates mode="mal2html.block.mode" select="."/>
          </xsl:for-each>
        </div>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = note = -->
<xsl:template mode="mal2html.block.mode" match="mal:note">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:variable name="notestyle">
    <xsl:choose>
      <xsl:when test="contains(concat(' ', @style, ' '), ' advanced ')">
        <xsl:text>Advanced</xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' bug ')">
        <xsl:text>Bug</xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' important ')">
        <xsl:text>Important</xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' plain ')">
        <xsl:text>plain</xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' sidebar ')">
        <xsl:text>Sidebar</xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' tip ')">
        <xsl:text>Tip</xsl:text>
      </xsl:when>
      <xsl:when test="contains(concat(' ', @style, ' '), ' warning ')">
        <xsl:text>Warning</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>Note</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>note</xsl:text>
        <xsl:if test="$notestyle != 'Note'">
          <xsl:value-of select="concat(' note-', translate($notestyle, 'ABISTW', 'abistw'))"/>
        </xsl:if>
        <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
          <xsl:text> ui-expander</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:if test="$notestyle != 'plain'">
      <xsl:attribute name="title">
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="$notestyle"/>
        </xsl:call-template>
      </xsl:attribute>
    </xsl:if>
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title"/>
      <div class="region">
        <div class="contents">
          <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
            <xsl:attribute name="id">
              <xsl:value-of select="concat('-yelp-', generate-id(.))"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:apply-templates mode="mal2html.block.mode" select="*[not(self::mal:title)]"/>
        </div>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = info = -->
<xsl:template mode="mal2html.block.mode" match="mal:info"/>

<!-- = p = -->
<xsl:template mode="mal2html.block.mode" match="mal:p">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <p>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>p</xsl:text>
        <xsl:if test="contains(concat(' ', @style, ' '), ' lead ')">
          <xsl:text> lead</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates mode="mal2html.inline.mode"/>
  </p>
</xsl:if>
</xsl:template>

<!-- = quote = -->
<xsl:template mode="mal2html.block.mode" match="mal:quote">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>quote</xsl:text>
        <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
          <xsl:text> ui-expander</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title"/>
      <div class="region">
        <blockquote class="contents">
          <xsl:for-each select="*[not(self::mal:title or self::mal:cite)]">
            <xsl:apply-templates mode="mal2html.block.mode" select="."/>
          </xsl:for-each>
        </blockquote>
        <xsl:apply-templates mode="mal2html.block.mode" select="mal:cite"/>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = quote/cite = -->
<xsl:template mode="mal2html.block.mode" match="mal:quote/mal:cite">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'cite cite-quote'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:choose>
      <xsl:when test="@href">
        <a href="{@href}">
          <xsl:apply-templates mode="mal2html.inline.mode"/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="mal2html.inline.mode"/>
      </xsl:otherwise>
    </xsl:choose>
    <!-- FIXME: i18n -->
    <xsl:if test="@date">
      <xsl:text> (</xsl:text>
      <xsl:value-of select="@date"/>
      <xsl:text>)</xsl:text>
    </xsl:if>
  </div>
</xsl:template>

<!-- = screen = -->
<xsl:template mode="mal2html.block.mode" match="mal:screen">
  <xsl:call-template name="mal2html.pre"/>
</xsl:template>

<!-- = synopsis = -->
<xsl:template mode="mal2html.block.mode" match="mal:synopsis">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>synopsis</xsl:text>
        <xsl:if test="mal:title and (@ui:expanded or @uix:expanded)">
          <xsl:text> ui-expander</xsl:text>
        </xsl:if>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title[1]"/>
      <div class="region">
        <xsl:apply-templates mode="mal2html.block.mode" select="mal:desc[1]"/>
        <div class="contents">
          <xsl:for-each select="*[not(self::mal:title or self::mal:desc)]">
            <xsl:apply-templates mode="mal2html.block.mode" select="."/>
          </xsl:for-each>
        </div>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = title = -->
<xsl:template mode="mal2html.block.mode" match="mal:title">
  <xsl:param name="depth" select="count(ancestor::mal:section) + 2"/>
  <xsl:variable name="depth_">
    <xsl:choose>
      <xsl:when test="$depth &lt; 6">
        <xsl:value-of select="$depth"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="6"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="style" select="concat(' ', @style, ' ')"/>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>title title-</xsl:text>
        <xsl:value-of select="local-name(..)"/>
        <xsl:if test="contains($style, ' heading ')">
          <xsl:text> title-heading</xsl:text>
        </xsl:if>
        <xsl:if test="contains($style, ' center ')">
          <xsl:text> center</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:element name="{concat('h', $depth_)}" namespace="{$html.namespace}">
      <span class="title">
        <xsl:apply-templates mode="mal2html.inline.mode"/>
      </span>
    </xsl:element>
  </div>
</xsl:template>

<!-- = if:choose = -->
<xsl:template mode="mal2html.block.mode" match="if:choose">
  <xsl:apply-templates mode="_mal2html.choose.mode" select="if:when[1]"/>
</xsl:template>

<!-- = if:if = -->
<xsl:template mode="mal2html.block.mode" match="if:if">
  <xsl:variable name="if">
    <xsl:call-template name="mal.if.test"/>
  </xsl:variable>
  <xsl:if test="$if != ''">
    <xsl:choose>
      <xsl:when test="$if != 'true'">
        <div class="if-if {$if}">
          <xsl:apply-templates mode="mal2html.block.mode"/>
        </div>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="mal2html.block.mode"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:if>
</xsl:template>

<!--#% _mal2html.choose.mode -->
<xsl:template mode="_mal2html.choose.mode" match="if:when">
  <xsl:variable name="if">
    <xsl:call-template name="mal.if.test"/>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$if = 'true'">
      <xsl:apply-templates mode="mal2html.block.mode"/>
    </xsl:when>
    <xsl:when test="$if != ''">
      <div class="if-choose {$if}">
        <div class="if-when">
          <xsl:apply-templates mode="mal2html.block.mode"/>
        </div>
        <div class="if-else">
          <xsl:apply-templates mode="_mal2html.choose.mode" select="following-sibling::*[1]"/>
        </div>
      </div>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="_mal2html.choose.mode" select="following-sibling::*[1]"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template mode="_mal2html.choose.mode" match="if:else">
  <xsl:apply-templates mode="mal2html.block.mode"/>
</xsl:template>

<xsl:template mode="_mal2html.choose.mode" match="*">
  <xsl:apply-templates mode="mal2html.block.mode" select=". | following-sibling::*"/>
</xsl:template>

</xsl:stylesheet>
