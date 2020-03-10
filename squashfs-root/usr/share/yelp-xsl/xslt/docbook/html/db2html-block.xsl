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
                xmlns:set="http://exslt.org/sets"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db msg set"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Block Elements
:Revision:version="3.4" date="2011-11-12" status="final"

This stylesheet handles most simple block-level elements, turning them into
the appropriate HTML tags. It does not handle tables, lists, and various other
complex block-level elements.
-->


<!--**==========================================================================
db2html.block
Output an HTML #{div} element for a block-level element.
:Revision:version="3.10" date="2013-08-09" status="final"
$node: The block-level element to render.
$class: The value of the HTML #{class} attribute.

This template creates an HTML #{div} element for the given DocBook element.
It passes the ${class} parameter to *{html.class.attr}.
If the ${class} parameter is not provided, it uses the local name of ${node}.

This template handles conditional processing.
-->
<xsl:template name="db2html.block">
  <xsl:param name="node" select="."/>
  <xsl:param name="class" select="local-name($node)"/>
  <xsl:variable name="if">
    <xsl:call-template name="db.profile.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="$class"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:apply-templates select="$node/node()"/>
  </div>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
db2html.block.formal
Output HTML for a block-level element with an optional title and caption.
:Revision:version="3.10" date="2013-08-09" status="final"
$node: The block-level element to render.
$class: The value of the HTML #{class} attribute.
$title: An element to use for the title.
$caption: An element to use for the caption.
$titleattr: An optional value for the HTML #{title} attribute.

This template outputs HTML for a formal DocBook element, one that can have
a title or caption. It passes the ${class} parameter to *{html.class.attr}.
If the ${class} parameter is not provided, it uses the
local name of ${node}. Even if ${title} and ${caption} are both empty, this
template still outputs the extra wrapper elements for formal elements. If
${titleattr} is provided, it is used for the value of the HTML #{title}
attribute on the outermost #{div} element.

This template handles conditional processing.
-->
<xsl:template name="db2html.block.formal">
  <xsl:param name="node" select="."/>
  <xsl:param name="class" select="local-name($node)"/>
  <xsl:param name="title" select="$node/title | $node/blockinfo/title |
                                  $node/db:title | $node/db:info/db:title"/>
  <xsl:param name="caption" select="$node/caption | $node/db:caption"/>
  <xsl:param name="titleattr" select="''"/>

  <xsl:variable name="if">
    <xsl:call-template name="db.profile.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="$class"/>
    </xsl:call-template>
    <xsl:if test="$titleattr != ''">
      <xsl:attribute name="title">
        <xsl:value-of select="$titleattr"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <div class="inner">
      <xsl:if test="$node/self::figure or $node/self::db:figure">
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
      </xsl:if>
      <xsl:if test="$title">
        <xsl:call-template name="db2html.block.title">
          <xsl:with-param name="node" select="$node"/>
          <xsl:with-param name="title" select="$title"/>
        </xsl:call-template>
      </xsl:if>
      <div class="region">
        <div class="contents">
          <xsl:apply-templates select="$node/node()[not(set:has-same-node(., $title | $caption))]"/>
        </div>
        <xsl:apply-templates select="$caption"/>
      </div>
    </div>
  </div>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
db2html.block.title
Output a formal title for a block-level element.
:Revision:version="3.4" date="2011-11-12" status="final"
$node: The block-level element being processed.
$title: The element containing the title.

This template formats the contents of ${title} as a title for a block-level
element.  It is called by *{db2html.block.formal}.
-->
<xsl:template name="db2html.block.title">
  <xsl:param name="node" select="."/>
	<xsl:param name="title" select="$node/title | $node/db:title"/>
  <xsl:variable name="depth">
    <xsl:call-template name="db.chunk.depth-in-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:variable name="depth_">
    <xsl:choose>
      <xsl:when test="number($depth) &lt; 6">
        <xsl:value-of select="number($depth) + 1"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="6"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$title"/>
      <xsl:with-param name="class" select="'title'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$title"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$title"/>
    </xsl:call-template>
    <xsl:element name="{concat('h', $depth_)}" namespace="{$html.namespace}">
      <span class="title">
        <xsl:apply-templates select="$title/node()"/>
      </span>
    </xsl:element>
  </div>
</xsl:template>


<!--**==========================================================================
db2html.blockquote
Output an HTML #{blockquote} element.
:Revision:version="3.10" date="2013-08-09" status="final"
$node: The DocBook element ot render as a quote.

This template creates an HTML #{blockquote} element for the given DocBook
element. It's used for the DocBook #{blockquote} and #{epigraph} elements.

This template handles conditional processing.
-->
<xsl:template name="db2html.blockquote">
  <xsl:param name="node" select="."/>
  <xsl:variable name="if">
    <xsl:call-template name="db.profile.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class">
        <xsl:text>quote </xsl:text>
        <xsl:value-of select="local-name($node)"/>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <div class="inner">
      <xsl:apply-templates select="$node/title | $node/db:title |
                                   $node/db:info/db:title"/>
      <div class="region">
        <blockquote class="{local-name($node)}">
          <xsl:apply-templates select="$node/node()[not(self::title) and not(self::attribution) and
                                                    not(self::db:title) and not(self::db:attribution)]"/>
        </blockquote>
        <xsl:apply-templates select="$node/attribution | $node/db:attribution"/>
      </div>
    </div>
  </div>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
db2html.para
Output an HTML #{p} element for a block-level element.
:Revision:version="3.10" date="2013-08-09" status="final"
$node: The block-level element to render.
$class: The value of the HTML #{class} attribute.

This template creates an HTML #{p} element for the given DocBook element.
It passes the ${class} parameter to *{html.class.attr}.
If the ${class} parameter is not provided, it uses the local name of ${node}.

This template handles conditional processing.
-->
<xsl:template name="db2html.para">
  <xsl:param name="node" select="."/>
  <xsl:param name="class" select="local-name($node)"/>
  <xsl:variable name="if">
    <xsl:call-template name="db.profile.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <p>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class">
        <xsl:value-of select="$class"/>
        <xsl:if test="contains(concat(' ', $node/@role, ' '), ' lead ')">
          <xsl:text> lead</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:apply-templates select="$node/node()"/>
  </p>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
db2html.pre
Output an HTML #{pre} element for a block-level element.
:Revision:version="3.12" date="2013-11-02" status="final"
$node: The block-level element to render.
$class: The value of the HTML #{class} attribute.
$children: The child elements to process.

This template creates an HTML #{pre} element for the given DocBook element.
It passes the ${class} parameter to *{html.class.attr}.
If the ${class} parameter is not provided, it uses the local name of ${node}.

If ${node} has the #{linenumbering} attribute set to #{"numbered"}, then this
template will create line numbers for each line, using the *{utils.linenumbering}
template.

By default, this template applies templates to all child nodes. Pass child
nodes in the ${children} parameter to override this behavior.

If @{html.syntax.highlight} is #{true}, this template automatically outputs
syntax highlighting support based on the #{language} attribute of ${node},
using *{html.syntax.class} to determine the correct highlighter.

This template handles conditional processing.
-->
<xsl:template name="db2html.pre">
  <xsl:param name="node" select="."/>
  <xsl:param name="class" select="local-name($node)"/>
  <xsl:param name="children" select="$node/node()"/>
  <xsl:variable name="if">
    <xsl:call-template name="db.profile.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="$class"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:if test="$node/@linenumbering = 'numbered'">
      <xsl:variable name="number">
        <xsl:choose>
          <xsl:when test="@startinglinenumber">
            <xsl:value-of select="@startinglinenumber"/>
          </xsl:when>
          <xsl:when test="@continuation">
            <xsl:call-template name="db.linenumbering.start">
              <xsl:with-param name="node" select="$node"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>1</xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <pre class="numbered"><xsl:call-template name="utils.linenumbering">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="number" select="$number"/>
      </xsl:call-template></pre>
    </xsl:if>
    <pre>
      <xsl:attribute name="class">
        <xsl:text>contents </xsl:text>
        <xsl:if test="$html.syntax.highlight and $node/@language">
          <xsl:call-template name="html.syntax.class">
            <xsl:with-param name="node" select="$node"/>
          </xsl:call-template>
        </xsl:if>
      </xsl:attribute>
      <!-- Strip off a leading newline -->
      <xsl:if test="$children[1]/self::text()">
        <xsl:choose>
          <xsl:when test="starts-with($node/text()[1], '&#x000A;')">
            <xsl:value-of select="substring-after($node/text()[1], '&#x000A;')"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$node/text()[1]"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:apply-templates select="$children[not(position() = 1 and self::text())]"/>
    </pre>
  </div>
  </xsl:if>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = abstract = -->
<xsl:template match="abstract | db:abstract">
  <xsl:call-template name="db2html.block"/>
</xsl:template>

<!-- = ackno = -->
<xsl:template match="ackno">
  <xsl:call-template name="db2html.para"/>
</xsl:template>

<!-- = acknowledgements = -->
<xsl:template match="db:acknowledgements">
  <xsl:call-template name="db2html.block"/>
</xsl:template>

<!-- = address = -->
<xsl:template match="address | db:address">
  <xsl:call-template name="db2html.block"/>
</xsl:template>

<!-- = attribution = -->
<xsl:template match="attribution | db:attribution">
  <xsl:call-template name="db2html.block">
    <xsl:with-param name="class" select="'cite'"/>
  </xsl:call-template>
</xsl:template>

<!-- = blockquote = -->
<xsl:template match="blockquote | db:blockquote">
  <xsl:call-template name="db2html.blockquote"/>
</xsl:template>

<!-- == bridgehead = -->
<xsl:template match="bridgehead | db:bridgehead">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <xsl:variable name="render">
    <xsl:choose>
      <xsl:when test="starts-with(@renderas, 'sect')">
        <xsl:value-of select="substring-after(@renderas, 'sect')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>6</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="level" select="number($depth_in_chunk) + number($render) - 1"/>
  <xsl:variable name="title_h">
    <xsl:choose>
      <xsl:when test="$depth_in_chunk &lt; 6">
        <xsl:value-of select="concat('h', $level)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>h6</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'hgroup bridgehead'"/>
    </xsl:call-template>
    <xsl:element name="{$title_h}" namespace="{$html.namespace}">
      <xsl:apply-templates/>
    </xsl:element>
  </div>
  </xsl:if>
</xsl:template>

<!-- = caption = -->
<xsl:template match="caption | db:caption">
  <xsl:call-template name="db2html.block">
    <xsl:with-param name="class" select="'desc'"/>
  </xsl:call-template>
</xsl:template>

<!-- = caution = -->
<xsl:template match="caution | db:caution">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'note note-warning'"/>
    <xsl:with-param name="titleattr">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Warning'"/>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = epigraph = -->
<xsl:template match="epigraph | db:epigraph">
  <xsl:call-template name="db2html.blockquote"/>
</xsl:template>

<!-- = equation = -->
<xsl:template match="equation | db:equation">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = example = -->
<xsl:template match="example | db:example">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = figure = -->
<xsl:template match="figure | informalfigure | db:figure | db:informalfigure">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'figure'"/>
    <!-- When a figure contains only a single mediaobject, it eats the caption -->
    <xsl:with-param name="caption"
                    select="*[not(self::blockinfo) and not(self::title) and not(self::titleabbrev)]
														[last() = 1]/self::mediaobject/caption |
														*[not(self::db:info) and not(self::db:title) and not(self::db:titleabbrev)]
                            [last() = 1]/self::db:mediaobject/db:caption"/>
  </xsl:call-template>
</xsl:template>

<!-- = formalpara = -->
<xsl:template match="formalpara | db:formalpara">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = highlights = -->
<xsl:template match="highlights">
  <xsl:call-template name="db2html.block"/>
</xsl:template>

<!-- = important = -->
<xsl:template match="important | db:important">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'note note-important'"/>
    <xsl:with-param name="titleattr">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Important'"/>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = informalequation = -->
<xsl:template match="informalequation | db:informalequation">
  <xsl:call-template name="db2html.block"/>
</xsl:template>

<!-- = informalexample = -->
<xsl:template match="informalexample | db:informalexample">
  <xsl:call-template name="db2html.block">
    <xsl:with-param name="class" select="'example informalexample'"/>
  </xsl:call-template>
</xsl:template>

<!-- = literallayout = -->
<xsl:template match="literallayout | db:literallayout">
  <xsl:choose>
    <xsl:when test="@class = 'monospaced'">
      <xsl:call-template name="db2html.pre"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="db2html.block"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = note = -->
<xsl:template match="note | db:note">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class">
      <xsl:text>note</xsl:text>
      <xsl:if test="@role = 'bug'">
        <xsl:text> note-bug</xsl:text>
      </xsl:if>
    </xsl:with-param>
    <xsl:with-param name="titleattr">
      <xsl:choose>
        <xsl:when test="@role = 'bug'">
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="msgid" select="'Bug'"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="msgid" select="'Note'"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = para = -->
<xsl:template match="para | db:para">
  <xsl:call-template name="db2html.para"/>
</xsl:template>

<!-- = programlisting = -->
<xsl:template match="programlisting | db:programlisting">
  <xsl:call-template name="db2html.pre">
    <xsl:with-param name="class" select="'code'"/>
  </xsl:call-template>
</xsl:template>

<!-- = screen = -->
<xsl:template match="screen | db:screen">
  <xsl:call-template name="db2html.pre"/>
</xsl:template>

<!-- = screenshot = -->
<xsl:template match="screenshot | db:screenshot">
  <xsl:call-template name="db2html.block"/>
</xsl:template>

<!-- = sidebar = -->
<xsl:template match="sidebar | db:sidebar">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'note note-sidebar'"/>
    <xsl:with-param name="titleattr">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Sidebar'"/>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = simpara = -->
<xsl:template match="simpara | db:simpara">
  <xsl:call-template name="db2html.para"/>
</xsl:template>

<!-- = synopsis = -->
<xsl:template match="synopsis | db:synopsis">
  <xsl:call-template name="db2html.pre"/>
</xsl:template>

<!-- = task = -->
<xsl:template match="task | db:task">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = taskprerequisites = -->
<xsl:template match="taskprerequisites | db:taskprerequisites">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = taskrelated = -->
<xsl:template match="taskrelated | db:taskrelated">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = tasksummary = -->
<xsl:template match="tasksummary | db:tasksummary">
  <xsl:call-template name="db2html.block.formal"/>
</xsl:template>

<!-- = tip = -->
<xsl:template match="tip | db:tip">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'note note-tip'"/>
    <xsl:with-param name="titleattr">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Tip'"/>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = title = -->
<xsl:template match="title | db:title">
  <xsl:call-template name="db2html.block.title">
    <xsl:with-param name="node" select=".."/>
    <xsl:with-param name="title" select="."/>
  </xsl:call-template>
</xsl:template>

<!-- = warning = -->
<xsl:template match="warning | db:warning">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'note note-warning'"/>
    <xsl:with-param name="titleattr">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'Warning'"/>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

</xsl:stylesheet>
