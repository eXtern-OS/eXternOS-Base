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
                xmlns:str="http://exslt.org/strings"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db msg str"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Lists
:Requires: db-common db2html-inline db2html-xref l10n html

REMARK: Describe this module
-->


<!-- == Matched Templates == -->

<!-- = glosslist = -->
<xsl:template match="glosslist | db:glosslist">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'list glosslist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="title | db:title | db:info/db:title"/>
    <dl class="glosslist">
      <xsl:apply-templates select="glossentry | db:glossentry"/>
    </dl>
  </div>
  </xsl:if>
</xsl:template>

<!-- = glossdef = -->
<xsl:template match="glossdef | db:glossdef">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <dd>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'glossdef'"/>
    </xsl:call-template>
    <xsl:apply-templates select="*[not(self::glossseealso) and not(self::db:glossseealso)]"/>
  </dd>
  <xsl:apply-templates select="glossseealso[1] | db:glossseealso[1]"/>
  </xsl:if>
</xsl:template>

<!-- = glossentry = -->
<xsl:template match="glossentry | db:glossentry">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <dt>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'glossterm'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="glossterm | db:glossterm"/>
    <xsl:if test="acronym or abbrev or db:acronym or db:abbrev">
      <xsl:text> (</xsl:text>
      <xsl:apply-templates select="(acronym | abbrev | db:acronym | db:abbrev)[1]"/>
      <xsl:text>)</xsl:text>
    </xsl:if>
  </dt>
  <xsl:apply-templates select="glossdef | glosssee[1] | db:glossdef | db:glosssee[1]"/>
  </xsl:if>
</xsl:template>

<!-- = glosssee(also) = -->
<xsl:template match="glosssee | glossseealso | db:glosssee | db:glossseealso">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <dd>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="local-name(.)"/>
    </xsl:call-template>
    <p>
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="concat(local-name(.), '.format')"/>
        <xsl:with-param name="node" select="."/>
        <xsl:with-param name="format" select="true()"/>
      </xsl:call-template>
    </p>
  </dd>
  </xsl:if>
</xsl:template>

<!--#% l10n.format.mode -->
<xsl:template mode="l10n.format.mode" match="msg:glosssee">
  <xsl:param name="node"/>
  <xsl:for-each select="$node |
                        $node/following-sibling::*[name(.) = name($node)]">
    <xsl:if test="position() != 1">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="', '"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:choose>
      <xsl:when test="@otherterm">
        <a>
          <xsl:attribute name="href">
            <xsl:call-template name="db.xref.target">
              <xsl:with-param name="linkend" select="@otherterm"/>
            </xsl:call-template>
          </xsl:attribute>
          <xsl:attribute name="title">
            <xsl:call-template name="db.xref.tooltip">
              <xsl:with-param name="linkend" select="@otherterm"/>
            </xsl:call-template>
          </xsl:attribute>
          <xsl:choose>
            <xsl:when test="normalize-space(.) != ''">
              <xsl:apply-templates/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:call-template name="db.xref.content">
                <xsl:with-param name="linkend" select="@otherterm"/>
                <xsl:with-param name="role" select="'glosssee'"/>
              </xsl:call-template>
            </xsl:otherwise>
          </xsl:choose>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:for-each>
</xsl:template>

<!-- = itemizedlist = -->
<xsl:template match="itemizedlist | db:itemizedlist">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'list itemizedlist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="db:info/db:title"/>
    <xsl:apply-templates select="*[not(self::listitem) and not(self::db:listitem)]"/>
    <ul>
      <xsl:attribute name="class">
        <xsl:text>list itemizedlist</xsl:text>
        <xsl:if test="@spacing = 'compact'">
          <xsl:text> compact</xsl:text>
        </xsl:if>
      </xsl:attribute>
      <xsl:if test="@mark">
        <xsl:attribute name="style">
          <xsl:text>list-style-type: </xsl:text>
          <xsl:choose>
            <xsl:when test="@mark = 'bullet'">disc</xsl:when>
            <xsl:when test="@mark = 'box'">square</xsl:when>
            <xsl:otherwise><xsl:value-of select="@mark"/></xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates select="listitem | db:listitem"/>
    </ul>
  </div>
  </xsl:if>
</xsl:template>

<!-- = itemizedlist/listitem = -->
<xsl:template match="itemizedlist/listitem | db:itemizedlist/db:listitem">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <li>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'list itemizedlist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:if test="@override">
      <xsl:attribute name="style">
        <xsl:text>list-style-type: </xsl:text>
        <xsl:choose>
          <xsl:when test="@override = 'bullet'">disc</xsl:when>
          <xsl:when test="@override = 'box'">square</xsl:when>
          <xsl:otherwise><xsl:value-of select="@override"/></xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
    </xsl:if>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates/>
  </li>
  </xsl:if>
</xsl:template>

<!-- = member = -->
<xsl:template match="member | db:member">
  <!-- Do something trivial, and rely on simplelist to do the rest -->
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = orderedlist = -->
<xsl:template match="orderedlist | db:orderedlist">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <xsl:variable name="start">
    <xsl:choose>
      <xsl:when test="@continuation = 'continues'">
        <xsl:call-template name="db.orderedlist.start"/>
      </xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <!-- FIXME: auto-numeration for nested lists -->
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'list orderedlist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="db:info/db:title"/>
    <xsl:apply-templates select="*[not(self::listitem) and not(self::db:listitem)]"/>
    <ol>
      <xsl:attribute name="class">
        <xsl:text>list orderedlist</xsl:text>
        <xsl:if test="@spacing = 'compact'">
          <xsl:text> compact</xsl:text>
        </xsl:if>
      </xsl:attribute>
      <xsl:if test="@numeration">
        <xsl:attribute name="type">
          <xsl:choose>
            <xsl:when test="@numeration = 'arabic'">1</xsl:when>
            <xsl:when test="@numeration = 'loweralpha'">a</xsl:when>
            <xsl:when test="@numeration = 'lowerroman'">i</xsl:when>
            <xsl:when test="@numeration = 'upperalpha'">A</xsl:when>
            <xsl:when test="@numeration = 'upperroman'">I</xsl:when>
            <xsl:otherwise>1</xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="$start != '1'">
        <xsl:attribute name="start">
          <xsl:value-of select="$start"/>
        </xsl:attribute>
      </xsl:if>
      <!-- FIXME: @inheritnum -->
      <xsl:apply-templates select="listitem | db:listitem"/>
    </ol>
  </div>
  </xsl:if>
</xsl:template>

<!-- = orderedlist/listitem = -->
<xsl:template match="orderedlist/listitem | db:orderedlist/db:listitem">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <li>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'list orderedlist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:if test="@override">
      <xsl:attribute name="value">
        <xsl:value-of select="@override"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates/>
  </li>
  </xsl:if>
</xsl:template>

<!-- = procedure = -->
<xsl:template match="procedure | db:procedure">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'steps'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <div class="inner">
    <xsl:apply-templates select="db:info/db:title"/>
    <xsl:apply-templates select="*[not(self::step) and not(self::db:step)]"/>
    <xsl:choose>
      <xsl:when test="(count(step) + count(db:step)) = 1">
        <ul class="steps">
          <xsl:apply-templates select="step | db:step"/>
        </ul>
      </xsl:when>
      <xsl:otherwise>
        <ol class="steps">
          <xsl:apply-templates select="step | db:step"/>
        </ol>
      </xsl:otherwise>
    </xsl:choose>
    </div>
  </div>
  </xsl:if>
</xsl:template>

<!-- = answer = -->
<xsl:template match="answer | db:answer">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <dd>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'answer'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:choose>
      <xsl:when test="label | db:label">
        <div class="qanda-label">
          <xsl:apply-templates select="label/node() | db:label/node()"/>
        </div>
      </xsl:when>
      <xsl:when test="ancestor::qandaset/@defaultlabel = 'qanda' or
                      ancestor::db:qandaset/@defaultlabel = 'qanda'">
        <div class="qanda-label">
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="msgid" select="'A:'"/>
          </xsl:call-template>
        </div>
      </xsl:when>
    </xsl:choose>
    <xsl:apply-templates/>
  </dd>
  </xsl:if>
</xsl:template>

<!-- = qandaentry = -->
<xsl:template match="qandaentry | db:qandaentry">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
    <xsl:apply-templates/>
  </xsl:if>
</xsl:template>

<!-- = question = -->
<xsl:template match="question | db:question">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <dt>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'question'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:choose>
      <xsl:when test="label | db:label">
        <div class="qanda-label">
          <xsl:apply-templates select="label/node() | db:label/node()"/>
        </div>
      </xsl:when>
      <xsl:when test="ancestor::qandaset/@defaultlabel = 'qanda' or
                      ancestor::db:qandaset/@defaultlabel = 'qanda'">
        <div class="qanda-label">
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="msgid" select="'Q:'"/>
          </xsl:call-template>
        </div>
      </xsl:when>
    </xsl:choose>
    <xsl:apply-templates/>
  </dt>
  </xsl:if>
</xsl:template>

<!-- = seg = -->
<xsl:template match="seg | db:seg">
  <xsl:variable name="position"
                select="count(preceding-sibling::seg) +
                        count(preceding-sibling::db:seg) + 1"/>
  <p>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'seg'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates select="../../segtitle[position() = $position] |
                                 ../../db:segtitle[position() = $position]"/>
    <xsl:apply-templates/>
  </p>
</xsl:template>

<!-- = seglistitem = -->
<xsl:template match="seglistitem | db:seglistitem">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'seglistitem'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="seg | db:seg"/>
  </div>
  </xsl:if>
</xsl:template>

<!-- FIXME: Implement tabular segmentedlists -->
<!-- = segmentedlist = -->
<xsl:template match="segmentedlist | db:segmentedlist">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'list segmentedlist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="title | db:title | db:info/db:title"/>
    <xsl:apply-templates select="seglistitem | db:seglistitem"/>
  </div>
  </xsl:if>
</xsl:template>

<!-- = segtitle = -->
<xsl:template match="segtitle | db:segtitle">
  <!-- FIXME: no style tags -->
  <b>
    <xsl:call-template name="html.class.attr"/>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates/>
    <!-- FIXME: i18n -->
    <xsl:text>: </xsl:text>
  </b>
</xsl:template>

<!-- = simplelist = -->
<xsl:template match="simplelist | db:simplelist">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <xsl:variable name="columns">
    <xsl:choose>
      <xsl:when test="@columns">
        <xsl:value-of select="@columns"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="1"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="allmembers" select="member | db:member"/>
  <xsl:variable name="memberpos">
    <xsl:for-each select="member | db:member">
      <xsl:variable name="memberif">
        <xsl:call-template name="db.profile.test"/>
      </xsl:variable>
      <xsl:if test="$memberif != ''">
        <xsl:value-of select="concat(',', position())"/>
      </xsl:if>
    </xsl:for-each>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="@type = 'inline'">
      <span>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="class" select="'simplelist'"/>
        </xsl:call-template>
        <xsl:call-template name="html.lang.attrs"/>
        <xsl:call-template name="db2html.anchor"/>
        <xsl:for-each select="str:split($memberpos, ',')">
          <xsl:if test="position() != 1">
            <xsl:call-template name="l10n.gettext">
              <xsl:with-param name="msgid" select="', '"/>
            </xsl:call-template>
          </xsl:if>
          <xsl:variable name="pos" select="number(.)"/>
          <xsl:apply-templates select="$allmembers[$pos]"/>
        </xsl:for-each>
      </span>
    </xsl:when>
    <xsl:when test="@type = 'horiz'">
      <div>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="class" select="'list simplelist'"/>
        </xsl:call-template>
        <xsl:call-template name="html.lang.attrs"/>
        <xsl:call-template name="db2html.anchor"/>
        <table class="simplelist">
          <xsl:for-each select="str:split($memberpos, ',')[$columns = 1 or position() mod $columns = 1]">
            <xsl:variable name="pos" select="number(.)"/>
            <tr>
              <td>
                <xsl:apply-templates select="$allmembers[$pos]"/>
              </td>
              <xsl:for-each select="following-sibling::*[position() &lt; $columns]">
                <xsl:variable name="fpos" select="number(.)"/>
                <td>
                  <xsl:apply-templates select="$allmembers[$fpos]"/>
                </td>
              </xsl:for-each>
              <xsl:variable name="fcount" select="count(following-sibling::*)"/>
              <xsl:if test="$fcount &lt; ($columns - 1)">
                <td colspan="{$columns - $fcount - 1}"/>
              </xsl:if>
            </tr>
          </xsl:for-each>
        </table>
      </div>
    </xsl:when>
    <xsl:otherwise>
      <div>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="class" select="'list simplelist'"/>
        </xsl:call-template>
        <xsl:call-template name="html.lang.attrs"/>
        <xsl:call-template name="db2html.anchor"/>
        <xsl:variable name="rows"
                      select="ceiling(count(str:split($memberpos, ',')) div $columns)"/>
        <table class="simplelist">
          <xsl:for-each select="str:split($memberpos, ',')[position() &lt;= $rows]">
            <xsl:variable name="pos" select="number(.)"/>
            <tr>
              <td>
                <xsl:apply-templates select="$allmembers[$pos]"/>
              </td>
              <xsl:for-each select="following-sibling::*[position() mod $rows = 0]">
                <xsl:variable name="fpos" select="number(.)"/>
                <td>
                  <xsl:apply-templates select="$allmembers[$fpos]"/>
                </td>
              </xsl:for-each>
              <xsl:variable name="fcount"
                            select="count(following-sibling::*[position() mod $rows = 0])"/>
              <xsl:if test="$fcount &lt; ($columns - 1)">
                <td/>
              </xsl:if>
            </tr>
          </xsl:for-each>
        </table>
      </div>
    </xsl:otherwise>
  </xsl:choose>
  </xsl:if>
</xsl:template>

<!-- FIXME: Do something with @performance -->
<!-- = step = -->
<xsl:template match="step | db:step">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <li>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'steps'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:apply-templates/>
  </li>
  </xsl:if>
</xsl:template>

<!-- FIXME: Do something with @performance -->
<!-- = substeps = -->
<xsl:template match="substeps | db:substeps">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <xsl:variable name="depth" select="count(ancestor::substeps | ancestor::db:substeps)"/>
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'steps substeps'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <ol class="steps substeps">
      <xsl:attribute name="type">
        <xsl:choose>
          <xsl:when test="$depth mod 3 = 0">a</xsl:when>
          <xsl:when test="$depth mod 3 = 1">i</xsl:when>
          <xsl:when test="$depth mod 3 = 2">1</xsl:when>
        </xsl:choose>
      </xsl:attribute>
      <xsl:apply-templates/>
    </ol>
  </div>
  </xsl:if>
</xsl:template>

<!-- = term = -->
<xsl:template match="term | db:term">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <dt>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'terms'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:if test="(../varlistentry/@id and not(preceding-sibling::term)) or
                  (../db:varlistentry/@xml:id and not(preceding-sibling::db:term))">
      <xsl:call-template name="db2html.anchor">
        <xsl:with-param name="node" select=".."/>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="db:info/db:title"/>
    <xsl:apply-templates/>
  </dt>
  </xsl:if>
</xsl:template>

<!-- = variablelist = -->
<xsl:template match="variablelist | db:variablelist">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'terms variablelist'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="db:info/db:title"/>
    <xsl:apply-templates select="*[not(self::varlistentry) and
                                   not(self::db:varlistentry)]"/>
    <dl class="terms variablelist">
      <xsl:apply-templates select="varlistentry |db:varlistentry"/>
    </dl>
  </div>
  </xsl:if>
</xsl:template>

<!-- = varlistentry = -->
<xsl:template match="varlistentry | db:varlistentry">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
    <xsl:apply-templates select="term | db:term"/>
    <xsl:apply-templates select="listitem | db:listitem"/>
  </xsl:if>
</xsl:template>

<!-- = varlistentry/listitem = -->
<xsl:template match="varlistentry/listitem | db:varlistentry/db:listitem">
  <dd>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'terms'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates/>
  </dd>
</xsl:template>

</xsl:stylesheet>
