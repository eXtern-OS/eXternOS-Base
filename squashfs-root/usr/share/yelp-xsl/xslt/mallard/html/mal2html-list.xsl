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
                xmlns:ui="http://projectmallard.org/ui/1.0/"
                xmlns:uix="http://projectmallard.org/experimental/ui/"
                xmlns:str="http://exslt.org/strings"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal ui uix str"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - Lists
Handle Mallard list elements.
:Revision: version="1.0" date="2010-06-04" status="final"

This stylesheet contains templates for the #{list}, #{steps}, #{terms}, and
#{tree} elements in %{mal2html.block.mode}. It handles the parent list elements,
as well as any special processing for child #{item} elements.
-->

<!-- = list = -->
<xsl:template mode="mal2html.block.mode" match="mal:list">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:variable name="style" select="concat(' ', @style, ' ')"/>
  <xsl:variable name="el">
    <xsl:choose>
      <xsl:when test="not(@type) or (@type = 'none') or (@type = 'box')
                      or (@type = 'check') or (@type = 'circle') or (@type = 'diamond')
                      or (@type = 'disc') or (@type = 'hyphen') or (@type = 'square')">
        <xsl:text>ul</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>ol</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>list</xsl:text>
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
        <xsl:element name="{$el}" namespace="{$html.namespace}">
          <xsl:attribute name="class">
            <xsl:text>list</xsl:text>
            <xsl:if test="contains($style, ' compact ')">
              <xsl:text> compact</xsl:text>
            </xsl:if>
          </xsl:attribute>
          <xsl:if test="@type">
            <xsl:attribute name="style">
              <xsl:value-of select="concat('list-style-type:', @type)"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="contains(concat(' ', @style, ' '), ' continues ')">
            <xsl:attribute name="start">
              <xsl:call-template name="mal.list.start"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:apply-templates select="mal:item"/>
        </xsl:element>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = list/item = -->
<xsl:template match="mal:list/mal:item">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <li>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>list</xsl:text>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates mode="mal2html.block.mode"/>
  </li>
</xsl:if>
</xsl:template>

<!-- = steps = -->
<xsl:template mode="mal2html.block.mode" match="mal:steps">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>steps</xsl:text>
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
        <ol class="steps">
          <xsl:if test="contains(concat(' ', @style, ' '), ' continues ')">
            <xsl:attribute name="start">
              <xsl:call-template name="mal.list.start"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:apply-templates select="mal:item"/>
        </ol>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<xsl:template name="mal.list.start">
  <xsl:param name="node" select="."/>
  <xsl:choose>
    <xsl:when test="contains(concat(' ', $node/@style, ' '), ' continues ')">
      <xsl:variable name="prevlist"
                    select="$node/preceding::*[name(.) = name($node)]
                            [not(@type) and not($node/@type) or (@type = $node/@type)][1]"/>
      <xsl:choose>
        <xsl:when test="count($prevlist) = 0">1</xsl:when>
        <xsl:otherwise>
          <xsl:variable name="prevlength" select="count($prevlist/mal:item)"/>
          <xsl:variable name="prevstart">
            <xsl:call-template name="mal.list.start">
              <xsl:with-param name="node" select="$prevlist"/>
            </xsl:call-template>
          </xsl:variable>
          <xsl:value-of select="$prevstart + $prevlength"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>1</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = steps/item = -->
<xsl:template match="mal:steps/mal:item">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <li>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>steps</xsl:text>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates mode="mal2html.block.mode"/>
  </li>
</xsl:if>
</xsl:template>

<!-- = terms = -->
<xsl:template mode="mal2html.block.mode" match="mal:terms">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:variable name="style" select="concat(' ', @style, ' ')"/>
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>terms</xsl:text>
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
        <dl class="terms">
          <xsl:attribute name="class">
            <xsl:text>terms</xsl:text>
            <xsl:if test="contains($style, ' compact ')">
              <xsl:text> compact</xsl:text>
            </xsl:if>
          </xsl:attribute>
          <xsl:apply-templates select="mal:item"/>
        </dl>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = terms/item = -->
<xsl:template match="mal:terms/mal:item">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:for-each select="mal:title">
    <dt>
      <xsl:call-template name="html.class.attr">
        <xsl:with-param name="class">
          <xsl:text>terms</xsl:text>
          <xsl:if test="$if != 'true'">
            <xsl:text> if-if </xsl:text>
            <xsl:value-of select="$if"/>
          </xsl:if>
        </xsl:with-param>
      </xsl:call-template>
      <xsl:call-template name="html.lang.attrs">
        <xsl:with-param name="parent" select=".."/>
      </xsl:call-template>
      <xsl:apply-templates mode="mal2html.inline.mode"/>
    </dt>
  </xsl:for-each>
  <dd>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>terms</xsl:text>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates mode="mal2html.block.mode" select="*[not(self::mal:title)]"/>
  </dd>
</xsl:if>
</xsl:template>

<!-- = tree = -->
<xsl:template mode="mal2html.block.mode" match="mal:tree">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:variable name="lines" select="contains(concat(' ', @style, ' '), ' lines ')"/>
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>tree</xsl:text>
        <xsl:if test="$lines">
          <xsl:text> tree-lines</xsl:text>
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
    <xsl:call-template name="mal2html.ui.expander.data"/>
    <div class="inner">
      <xsl:apply-templates mode="mal2html.block.mode" select="mal:title"/>
      <div class="region">
        <ul class="tree">
          <xsl:apply-templates mode="mal2html.tree.mode" select="mal:item">
            <xsl:with-param name="lines" select="$lines"/>
          </xsl:apply-templates>
        </ul>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!--%%==========================================================================
mal2html.tree.mode
Process an #{item} element inside a #{tree}.
:Revision: version="1.0" date="2010-06-04" status="final"
$lines: Whether to draw lines indicating hierarchy.
$prefix: The line markers used by the parent #{item}.

This mode is used for processing #{item} elements in #{tree} elements. It is
applied by the template for #{tree} and recursively calls itself. If the parent
#{tree} has the style hint #{"lines"}, the ${lines} parameter will be #{true}.
In this case, this template calculates a prefix based on its position and
neighboring #{item} elements, and passes that prefix to child elements.
-->
<xsl:template mode="mal2html.tree.mode" match="mal:item">
  <xsl:param name="lines" select="false()"/>
  <xsl:param name="prefix" select="''"/>
  <xsl:variable name="if">
    <xsl:choose>
      <!-- We do the tests as we process children, to get lines right, and
           only apply-templates to what we have to. So if this is a deep
           item, don't spend the CPU cycles testing it again.
      -->
      <xsl:when test="parent::mal:item">
        <xsl:text>true</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="mal.if.test"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <li>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>tree</xsl:text>
        <xsl:if test="$if != 'true'">
          <xsl:text> if-if </xsl:text>
          <xsl:value-of select="$if"/>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <div>
      <xsl:if test="$lines">
        <xsl:value-of select="$prefix"/>
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates mode="mal2html.inline.mode"
                           select="node()[not(self::mal:item)]"/>
    </div>
    <xsl:variable name="items">
      <xsl:for-each select="mal:item">
        <xsl:variable name="itemif">
          <xsl:call-template name="mal.if.test"/>
        </xsl:variable>
        <xsl:if test="$itemif = 'true'">
          <xsl:value-of select="concat(position(), ':')"/>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>
    <xsl:if test="$items != ''">
      <ul class="tree">
        <xsl:variable name="node" select="."/>
        <xsl:for-each select="str:split($items, ':')">
          <xsl:variable name="itempos" select="number(.)"/>
          <xsl:variable name="item" select="$node/mal:item[position() = $itempos]"/>
          <xsl:apply-templates mode="mal2html.tree.mode" select="$item">
            <xsl:with-param name="lines" select="$lines"/>
            <xsl:with-param name="prefix">
              <xsl:if test="$lines">
                <xsl:variable name="dir">
                  <xsl:call-template name="l10n.direction">
                    <xsl:with-param name="lang" select="$item/ancestor-or-self::*[@xml:lang][1]/@xml:lang"/>
                  </xsl:call-template>
                </xsl:variable>
                <xsl:value-of select="translate(translate(translate(translate(
                                      $prefix,
                                      '&#x251C;', '&#x2502;'),
                                      '&#x2524;', '&#x2502;'),
                                      '&#x2514;', '&#x202F;'),
                                      '&#x2518;', '&#x202F;')"/>
                <xsl:text>&#x202F;&#x202F;&#x202F;&#x202F;</xsl:text>
                <xsl:choose>
                  <xsl:when test="position() != last()">
                    <xsl:choose>
                      <xsl:when test="$dir = 'rtl'">
                        <xsl:text>&#x2524;</xsl:text>
                      </xsl:when>
                      <xsl:otherwise>
                        <xsl:text>&#x251C;</xsl:text>
                      </xsl:otherwise>
                    </xsl:choose>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:choose>
                      <xsl:when test="$dir = 'rtl'">
                        <xsl:text>&#x2518;</xsl:text>
                      </xsl:when>
                      <xsl:otherwise>
                        <xsl:text>&#x2514;</xsl:text>
                      </xsl:otherwise>
                    </xsl:choose>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:if>
            </xsl:with-param>
          </xsl:apply-templates>
        </xsl:for-each>
      </ul>
    </xsl:if>
  </li>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>
