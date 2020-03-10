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
Mallard to HTML - Table Elements

REMARK: Describe this module
-->


<!-- == Matched Templates == -->

<!-- = table = -->
<xsl:template mode="mal2html.block.mode" match="mal:table">
  <xsl:variable name="if"><xsl:call-template name="mal.if.test"/></xsl:variable><xsl:if test="$if != ''">
  <xsl:variable name="cols" select="mal:col | mal:colgroup/mal:col"/>
  <xsl:variable name="style">
    <xsl:if test="@frame and @frame != 'none'">
      <xsl:choose>
        <xsl:when test="@frame = 'all'">
          <xsl:text>border-style: solid;</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:for-each select="str:split(@frame)">
            <xsl:choose>
              <xsl:when test=". = 'top'">
                <xsl:text>border-top-style: solid;</xsl:text>
              </xsl:when>
              <xsl:when test=". = 'bottom'">
                <xsl:text>border-bottom-style: solid;</xsl:text>
              </xsl:when>
              <xsl:when test=". = 'left'">
                <xsl:text>border-left-style: solid;</xsl:text>
              </xsl:when>
              <xsl:when test=". = 'right'">
                <xsl:text>border-right-style: solid;</xsl:text>
              </xsl:when>
            </xsl:choose>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:variable>
  <xsl:variable name="rowrules">
    <xsl:choose>
      <xsl:when test="not(@rules) or @rules = 'none'">
        <xsl:text>none</xsl:text>
      </xsl:when>
      <xsl:when test="@rules = 'all'">
        <xsl:text>all</xsl:text>
      </xsl:when>
      <xsl:when test="@rules = 'groups'">
        <xsl:text>groups</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="str:split(@rules)">
          <xsl:choose>
            <xsl:when test=". = 'rows'">
              <xsl:text>all</xsl:text>
            </xsl:when>
            <xsl:when test=". = 'rowgroups'">
              <xsl:text>groups</xsl:text>
            </xsl:when>
          </xsl:choose>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="colrules">
    <xsl:choose>
      <xsl:when test="not(@rules) or @rules = 'none'">
        <xsl:text>none</xsl:text>
      </xsl:when>
      <xsl:when test="@rules = 'all'">
        <xsl:text>all</xsl:text>
      </xsl:when>
      <xsl:when test="@rules = 'groups'">
        <xsl:text>groups</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="str:split(@rules)">
          <xsl:choose>
            <xsl:when test=". = 'cols'">
              <xsl:text>all</xsl:text>
            </xsl:when>
            <xsl:when test=". = 'colgroups'">
              <xsl:text>groups</xsl:text>
            </xsl:when>
          </xsl:choose>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="rowshade">
    <xsl:choose>
      <xsl:when test="not(@shade) or @shade = 'none'">
        <xsl:text>none</xsl:text>
      </xsl:when>
      <xsl:when test="@shade = 'all'">
        <xsl:text>all</xsl:text>
      </xsl:when>
      <xsl:when test="@shade = 'groups'">
        <xsl:text>groups</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="str:split(@shade)">
          <xsl:choose>
            <xsl:when test=". = 'rows'">
              <xsl:text>all</xsl:text>
            </xsl:when>
            <xsl:when test=". = 'rowgroups'">
              <xsl:text>groups</xsl:text>
            </xsl:when>
          </xsl:choose>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="colshade">
    <xsl:choose>
      <xsl:when test="not(@shade) or @shade = 'none'">
        <xsl:text>none</xsl:text>
      </xsl:when>
      <xsl:when test="@shade = 'all'">
        <xsl:text>all</xsl:text>
      </xsl:when>
      <xsl:when test="@shade = 'groups'">
        <xsl:text>groups</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="str:split(@shade)">
          <xsl:choose>
            <xsl:when test=". = 'cols'">
              <xsl:text>all</xsl:text>
            </xsl:when>
            <xsl:when test=". = 'colgroups'">
              <xsl:text>groups</xsl:text>
            </xsl:when>
          </xsl:choose>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>table</xsl:text>
        <xsl:for-each select="str:tokenize(@style)">
          <xsl:value-of select="concat(' style-', .)"/>
        </xsl:for-each>
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
        <table class="table">
          <xsl:if test="$style != ''">
            <xsl:attribute name="style">
              <xsl:value-of select="$style"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:apply-templates select="mal:thead">
            <xsl:with-param name="cols" select="$cols"/>
            <xsl:with-param name="rowrules" select="$rowrules"/>
            <xsl:with-param name="colrules" select="$colrules"/>
            <xsl:with-param name="rowshade" select="$rowshade"/>
            <xsl:with-param name="colshade" select="$colshade"/>
          </xsl:apply-templates>
          <xsl:apply-templates select="mal:tfoot">
            <xsl:with-param name="cols" select="$cols"/>
            <xsl:with-param name="rowrules" select="$rowrules"/>
            <xsl:with-param name="colrules" select="$colrules"/>
            <xsl:with-param name="rowshade" select="$rowshade"/>
            <xsl:with-param name="colshade" select="$colshade"/>
          </xsl:apply-templates>
          <xsl:apply-templates select="mal:tr[1] | mal:tbody">
            <xsl:with-param name="cols" select="$cols"/>
            <xsl:with-param name="rowrules" select="$rowrules"/>
            <xsl:with-param name="colrules" select="$colrules"/>
            <xsl:with-param name="rowshade" select="$rowshade"/>
            <xsl:with-param name="colshade" select="$colshade"/>
          </xsl:apply-templates>
        </table>
      </div>
    </div>
  </div>
</xsl:if>
</xsl:template>

<!-- = tbody = -->
<xsl:template match="mal:tbody">
  <xsl:param name="cols"/>
  <xsl:param name="rowrules"/>
  <xsl:param name="colrules"/>
  <xsl:param name="rowshade"/>
  <xsl:param name="colshade"/>
  <tbody>
    <xsl:call-template name="html.class.attr"/>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates select="mal:tr[1]">
      <xsl:with-param name="cols" select="$cols"/>
      <xsl:with-param name="rowrules" select="$rowrules"/>
      <xsl:with-param name="colrules" select="$colrules"/>
      <xsl:with-param name="rowshade" select="$rowshade"/>
      <xsl:with-param name="colshade" select="$colshade"/>
    </xsl:apply-templates>
  </tbody>
</xsl:template>

<!-- = thead = -->
<xsl:template match="mal:thead">
  <xsl:param name="cols"/>
  <xsl:param name="rowrules"/>
  <xsl:param name="colrules"/>
  <xsl:param name="rowshade"/>
  <xsl:param name="colshade"/>
  <thead>
    <xsl:call-template name="html.class.attr"/>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates select="mal:tr[1]">
      <xsl:with-param name="cols" select="$cols"/>
      <xsl:with-param name="rowrules" select="$rowrules"/>
      <xsl:with-param name="colrules" select="$colrules"/>
      <xsl:with-param name="rowshade" select="$rowshade"/>
      <xsl:with-param name="colshade" select="$colshade"/>
    </xsl:apply-templates>
  </thead>
</xsl:template>

<!-- = tfoot = -->
<xsl:template match="mal:tfoot">
  <xsl:param name="cols"/>
  <xsl:param name="rowrules"/>
  <xsl:param name="colrules"/>
  <xsl:param name="rowshade"/>
  <xsl:param name="colshade"/>
  <tfoot>
    <xsl:call-template name="html.class.attr"/>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates select="mal:tr[1]">
      <xsl:with-param name="cols" select="$cols"/>
      <xsl:with-param name="rowrules" select="$rowrules"/>
      <xsl:with-param name="colrules" select="$colrules"/>
      <xsl:with-param name="rowshade" select="$rowshade"/>
      <xsl:with-param name="colshade" select="$colshade"/>
    </xsl:apply-templates>
  </tfoot>
</xsl:template>

<!-- = tr = -->
<xsl:template match="mal:tr">
  <xsl:param name="cols"/>
  <xsl:param name="rowrules"/>
  <xsl:param name="colrules"/>
  <xsl:param name="rowshade"/>
  <xsl:param name="colshade"/>
  <xsl:param name="rowspans">
    <xsl:for-each select="mal:td | mal:th">
      <xsl:text>0:</xsl:text>
      <xsl:if test="@colspan">
        <xsl:call-template name="utils.repeat_string">
          <xsl:with-param name="string" select="'0:'"/>
          <xsl:with-param name="number" select="number(@colspan) - 1"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:for-each>
  </xsl:param>
  <xsl:variable name="trpos" select="count(preceding-sibling::mal:tr) + 1"/>
  <xsl:variable name="shaderow">
    <xsl:choose>
      <xsl:when test="$rowshade = 'all'">
        <xsl:choose>
          <xsl:when test="../self::mal:table">
            <xsl:value-of select="($trpos + 1) mod 2"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="bodies"
                          select="../preceding-sibling::mal:tbody |
                                  ../preceding-sibling::mal:thead "/>
            <xsl:variable name="trcount" select="count($bodies/mal:tr) + $trpos"/>
            <xsl:value-of select="($trcount + 1) mod 2"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="$rowshade = 'groups'">
        <xsl:variable name="bodies"
                      select="../preceding-sibling::mal:tbody |
                              ../preceding-sibling::mal:thead "/>
        <xsl:value-of select="count($bodies) mod 2"/>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>
  <tr>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:if test="$shaderow = 1">
          <xsl:text>shade</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:apply-templates select="mal:td | mal:th">
      <xsl:with-param name="cols" select="$cols"/>
      <xsl:with-param name="rowrules" select="$rowrules"/>
      <xsl:with-param name="colrules" select="$colrules"/>
      <xsl:with-param name="rowshade" select="$rowshade"/>
      <xsl:with-param name="colshade" select="$colshade"/>
      <xsl:with-param name="rowspans" select="$rowspans"/>
    </xsl:apply-templates>
  </tr>
  <xsl:apply-templates select="following-sibling::mal:tr[1]">
    <xsl:with-param name="cols" select="$cols"/>
    <xsl:with-param name="rowrules" select="$rowrules"/>
    <xsl:with-param name="colrules" select="$colrules"/>
    <xsl:with-param name="rowshade" select="$rowshade"/>
    <xsl:with-param name="colshade" select="$colshade"/>
    <xsl:with-param name="rowspans">
      <xsl:call-template name="rowspans">
        <xsl:with-param name="spans" select="str:split($rowspans, ':')"/>
      </xsl:call-template>
    </xsl:with-param>
  </xsl:apply-templates>
</xsl:template>

<!--#* rowspans -->
<xsl:template name="rowspans">
  <xsl:param name="spans"/>
  <xsl:param name="pos" select="1"/>
  <xsl:param name="td" select="(mal:td | mal:th)[1]"/>
  <xsl:param name="times" select="1"/>
  <xsl:variable name="span" select="number($spans[$pos])"/>

  <xsl:choose>
    <xsl:when test="$span &gt; 1">
      <xsl:value-of select="$span - 1"/>
      <xsl:text>:</xsl:text>
      <xsl:if test="$pos &lt; count($spans)">
        <xsl:call-template name="rowspans">
          <xsl:with-param name="spans" select="$spans"/>
          <xsl:with-param name="pos" select="$pos + 1"/>
          <xsl:with-param name="td" select="$td"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:when>
    <xsl:otherwise>
      <xsl:variable name="rowspan">
        <xsl:choose>
          <xsl:when test="$td/@rowspan">
            <xsl:value-of select="number($td/@rowspan)"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="1"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:variable name="colspan">
        <xsl:choose>
          <xsl:when test="$td/@colspan">
            <xsl:value-of select="number($td/@colspan)"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="1"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:call-template name="utils.repeat_string">
        <xsl:with-param name="string">
          <xsl:value-of select="$rowspan - 1"/>
          <xsl:text>:</xsl:text>
        </xsl:with-param>
        <xsl:with-param name="number" select="$colspan"/>
      </xsl:call-template>
      <xsl:variable name="nextpos" select="$pos + $colspan"/>
      <xsl:if test="$nextpos &lt;= count($spans)">
        <xsl:call-template name="rowspans">
          <xsl:with-param name="spans" select="$spans"/>
          <xsl:with-param name="pos" select="$nextpos"/>
          <xsl:with-param name="td" select="($td/following-sibling::mal:td | $td/following-sibling::mal:th)[1]"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = td | th = -->
<xsl:template match="mal:td | mal:th">
  <xsl:param name="cols"/>
  <xsl:param name="rowrules"/>
  <xsl:param name="colrules"/>
  <xsl:param name="rowshade"/>
  <xsl:param name="colshade"/>
  <xsl:param name="rowspans"/>
  <xsl:variable name="trpos" select="count(../preceding-sibling::mal:tr) + 1"/>
  <xsl:variable name="tdcnt" select="count(preceding-sibling::mal:td) + count(preceding-sibling::mal:th) + 1"/>
  <xsl:variable name="spans" select="str:split($rowspans, ':')"/>
  <xsl:variable name="tdstr">
    <xsl:for-each select="$spans[. = '0'][$tdcnt]/preceding-sibling::*[not(. = '0')]">
      <xsl:text>.</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="preceding-sibling::mal:td | preceding-sibling::mal:th">
      <xsl:text>.</xsl:text>
      <xsl:if test="@colspan">
        <xsl:call-template name="utils.repeat_string">
          <xsl:with-param name="string" select="'.'"/>
          <xsl:with-param name="number" select="number(@colspan) - 1"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:for-each>
  </xsl:variable>
  <xsl:variable name="tdpos" select="string-length($tdstr) + 1"/>
  <xsl:variable name="shadecol">
    <xsl:choose>
      <xsl:when test="$colshade = 'all'">
        <xsl:value-of select="($tdpos + 1) mod 2"/>
      </xsl:when>
      <xsl:when test="$colshade = 'groups'">
        <xsl:if test="count($cols) &gt;= $tdpos">
          <xsl:variable name="col" select="$cols[$tdpos]"/>
          <xsl:if test="$col/../self::mal:colgroup">
            <xsl:value-of
                select="count($col/../preceding-sibling::mal:colgroup) mod 2"/>
          </xsl:if>
        </xsl:if>
        <!-- FIXME -->
      </xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="style">
    <xsl:choose>
      <xsl:when test="$rowrules = 'all'">
        <xsl:choose>
          <xsl:when test="../../self::mal:table">
            <xsl:if test="$trpos != 1">
              <xsl:text>border-top-style: solid;</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:when test="$trpos != 1 or
                          ../../preceding-sibling::mal:thead or
                          ../../preceding-sibling::mal:tbody ">
            <xsl:text>border-top-style: solid;</xsl:text>
          </xsl:when>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="$rowrules = 'groups'">
        <xsl:if test="$trpos = 1">
          <xsl:choose>
            <xsl:when test="../../self::mal:tbody">
              <xsl:if test="../../../mal:thead | ../../preceding-sibling::mal:tbody">
                <xsl:text>border-top-style: solid;</xsl:text>
              </xsl:if>
            </xsl:when>
            <xsl:when test="../../self::mal:tfoot">
              <xsl:text>border-top-style: solid;</xsl:text>
            </xsl:when>
          </xsl:choose>
        </xsl:if>
      </xsl:when>
    </xsl:choose>
    <xsl:choose>
      <xsl:when test="$tdpos = 1"/>
      <xsl:when test="$colrules = 'all'">
        <xsl:text>border-left-style: solid;</xsl:text>
      </xsl:when>
      <xsl:when test="$colrules = 'groups'">
        <xsl:if test="count($cols) &gt;= $tdpos">
          <xsl:variable name="col" select="$cols[$tdpos]"/>
          <xsl:if test="$col/../self::mal:colgroup and
                        not($col/preceding-sibling::mal:col)">
            <xsl:text>border-left-style: solid;</xsl:text>
          </xsl:if>
        </xsl:if>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>
  <xsl:element name="{local-name(.)}" namespace="{$html.namespace}">
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:if test="$shadecol = 1">
          <xsl:text>shade</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:if test="$style != ''">
      <xsl:attribute name="style">
        <xsl:value-of select="$style"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@colspan">
      <xsl:attribute name="colspan">
        <xsl:value-of select="@colspan"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="@rowspan">
      <xsl:attribute name="rowspan">
        <xsl:value-of select="@rowspan"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates mode="mal2html.block.mode"/>
  </xsl:element>
</xsl:template>

</xsl:stylesheet>
