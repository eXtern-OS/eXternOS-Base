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
                xmlns:str="http://exslt.org/strings"
                xmlns:msg="http://projects.gnome.org/yelp/gettext/"
                exclude-result-prefixes="db str msg"
                version="1.0">

<!--!!==========================================================================
DocBook Common
:Requires: l10n

This stylesheet module provides utility templates for DocBook that are
independant of the target format.
-->


<!--++==========================================================================
db.id.key
Get an element from the #{id} attribute.
:Revision:version="3.4" date="2012-01-26" status="final"

This key returns any element based on the #{id} attribute, or the #{xml:id}
attribute in DocBook 5.
-->
<xsl:key name="db.id.key" match="*" use="@id | @xml:id"/>


<!--++==========================================================================
db.biblio.abbrev.key
Get a #{biblioentry} or #{bibliomixed} element from its #{abbrev}.
:Revision:version="3.18" date="2015-07-23" status="final"

This key returns #{biblioentry} and #{bibliomixed} elements based on their child
#{abbrev} elements. The #{abbrev} element must be the first child element of the
#{biblioentry} or #{bibliomixed} element. This key only returns elements that
have an #{id} attribute for DocBook 4 or an #{xml:id} attribute for DocBook 5.
-->
<xsl:key name="db.biblio.abbrev.key"
         match="biblioentry[@id and *[1]/self::abbrev] |
                bibliomixed[@id and *[1]/self::abbrev] |
                db:biblioentry[@xml:id and *[1]/self::db:abbrev] |
                db:bibliomixed[@xml:id and *[1]/self::db:abbrev]"
         use="string(*[1])"/>


<!--++==========================================================================
db.biblio.label.key
Get a #{biblioentry} or #{bibliomixed} element from its #{xreflabel}.
:Revision:version="3.18" date="2015-07-23" status="final"

This key returns #{biblioentry} and #{bibliomixed} elements based on their
#{xreflabel} attributes. It only returns elements that have an #{id} attribute
for DocBook 4 or an #{xml:id} attribute for DocBook 5.
-->
<xsl:key name="db.biblio.label.key"
         match="biblioentry[@id and @xreflabel] |
                bibliomixed[@id and @xreflabel] |
                db:biblioentry[@xml:id and @xreflabel] |
                db:bibliomixed[@xml:id and @xreflabel]"
         use="string(@xreflabel)"/>


<!--++==========================================================================
db.biblio.id.key
Get a #{biblioentry} or #{bibliomixed} element from its #{id}.
:Revision:version="3.18" date="2015-07-23" status="final"

This key returns #{biblioentry} and #{bibliomixed} elements based on their #{id}
or #{xml:id} attributes. The {#id} attribute is used for DocBook 4, and the
#{xml:id} attribute is used for DocBook 5.
-->
<xsl:key name="db.biblio.id.key"
         match="biblioentry[@id] | bibliomixed[@id]"
         use="string(@id)"/>
<xsl:key name="db.biblio.id.key"
         match="db:biblioentry[@xml:id] | db:bibliomixed[@xml:id]"
         use="string(@xml:id)"/>


<!--++==========================================================================
db.glossentry.key
Get a #{glossentry} element from its #{glossterm}.
:Revision:version="3.18" date="2015-07-22" status="final"

This key returns #{glossentry} elements based on the text in their #{glossterm}
child elements. It only returns #{glossentry} elements that have an #{id}
attribute in DocBook 4 or an #{xml:id} attribute in DocBook 5.
-->
<xsl:key name="db.glossentry.key"
         match="glossentry[@id]" use="string(glossterm)"/>
<xsl:key name="db.glossentry.key"
         match="db:glossentry[@xml:id]" use="string(db:glossterm)"/>


<!--**==========================================================================
db.copyright
Outputs copyright information
$node: The #{copyright} element to format

This template outputs copyright information from a #{copyright} elements.
It assembles the #{year} and #{holder} elements into a simple copyright
notice, beginning with the copyright symbol "©".
-->
<xsl:template name="db.copyright">
  <xsl:param name="node" select="."/>
  <xsl:call-template name="l10n.gettext">
    <xsl:with-param name="msgid" select="'copyright.format'"/>
    <xsl:with-param name="node" select="$node"/>
    <xsl:with-param name="format" select="true()"/>
  </xsl:call-template>
</xsl:template>

<xsl:template mode="l10n.format.mode" match="msg:copyright.years">
  <xsl:param name="node"/>
  <xsl:for-each select="$node/year | $node/db:year">
    <xsl:if test="position() != 1">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="', '"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>

<xsl:template mode="l10n.format.mode" match="msg:copyright.name">
  <xsl:param name="node"/>
  <xsl:for-each select="$node/holder | $node/db:holder">
    <xsl:if test="position() != 1">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="', '"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>


<!--**==========================================================================
db.linenumbering.start
Determines the starting line number for a verbatim element
$node: The verbatim element to determine the starting line number for

This template determines the starting line number for a verbatim element using
the #{continuation} attribute.  The template finds the first preceding element
of the same name, counts its lines, and handles any #{startinglinenumber} or
#{continuation} element it finds on that element.
-->
<xsl:template name="db.linenumbering.start">
  <xsl:param name="node" select="."/>
  <xsl:choose>
    <xsl:when test="$node/@startinglinenumber">
      <xsl:value-of select="$node/@startinglinenumber"/>
    </xsl:when>
    <xsl:when test="$node/@continuation">
      <xsl:variable name="prev" select="$node/preceding::*[name(.) = name($node)][1]"/>
      <xsl:choose>
        <xsl:when test="count($prev) = 0">1</xsl:when>
        <xsl:otherwise>
          <xsl:variable name="prevcount">
            <xsl:value-of select="count(str:split(string($prev), '&#x000A;'))"/>
          </xsl:variable>
          <xsl:variable name="prevstart">
            <xsl:call-template name="db.linenumbering.start">
              <xsl:with-param name="node" select="$prev"/>
            </xsl:call-template>
          </xsl:variable>
          <xsl:value-of select="$prevstart + $prevcount"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>1</xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db.orderedlist.start
Determine the number to use for the first #{listitem} in an #{orderedlist}.
:Revision:version="3.10" date="2013-08-12" status="final"
$node: The #{orderedlist} element to use.
$continuation: The value of the #{continuation} attribute.

This template determines the starting number for an #{orderedlist} element using
the #{continuation} attribute.  The template finds the first preceding #{orderedlist}
element and counts its list items.  If that element also uses the #{continuation}
attribute, this template calls itself recursively to add that element's starting
line number to its list item count.

This template uses conditional processing when looking at preceding ordered lists
and their child list items.

The ${continuation} parameter is automatically set based on the #{continuation}
attribute of ${node}. It exists as a parameter to allow this template to force
continuation when it calls itself recursively for conditional processing.
-->
<xsl:template name="db.orderedlist.start">
  <xsl:param name="node" select="."/>
  <xsl:param name="continuation" select="$node/@continuation"/>
  <xsl:choose>
    <xsl:when test="$continuation != 'continues'">1</xsl:when>
    <xsl:otherwise>
      <xsl:variable name="prevlist"
                    select="($node/preceding::orderedlist[1] | $node/preceding::db:orderedlist[1])[last()]"/>
      <xsl:choose>
        <xsl:when test="count($prevlist) = 0">1</xsl:when>
        <xsl:otherwise>
          <xsl:variable name="prevlistif">
            <xsl:call-template name="db.profile.test">
              <xsl:with-param name="node" select="$prevlist"/>
            </xsl:call-template>
          </xsl:variable>
          <xsl:choose>
            <xsl:when test="$prevlistif = ''">
              <xsl:call-template name="db.orderedlist.start">
                <xsl:with-param name="node" select="$prevlist"/>
                <xsl:with-param name="continuation" select="'continues'"/>
              </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
              <xsl:variable name="prevlength">
                <xsl:for-each select="$prevlist/listitem | $prevlist/db:listitem">
                  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
                  <xsl:if test="$if != ''">
                    <xsl:text>x</xsl:text>
                  </xsl:if>
                </xsl:for-each>
              </xsl:variable>
              <xsl:variable name="prevstart">
                <xsl:call-template name="db.orderedlist.start">
                  <xsl:with-param name="node" select="$prevlist"/>
                </xsl:call-template>
              </xsl:variable>
              <xsl:value-of select="$prevstart + string-length($prevlength)"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db.personname
Outputs the name of a person
$node: The element containing tags such as #{firstname} and #{surname}

This template outputs the name of a person as modelled by the #{personname}
element.  The #{personname} element allows authors to mark up components of
a person's name, such as the person's first name and surname.  This template
assembles those into a string.
-->
<xsl:template name="db.personname">
  <xsl:param name="node" select="."/>
  <xsl:choose>
    <xsl:when test="$node/personname or $node/db:personname">
      <xsl:call-template name="db.personname">
        <xsl:with-param name="node" select="$node/personname | $node/db:personname"/>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="$node/db:orgname">
      <xsl:apply-templates select="$node/db:orgname"/>
    </xsl:when>
    <xsl:when test="$node/self::collab or $node/self::db:collab">
      <xsl:apply-templates select="$node/collabname |
                                   $node/db:org | $node/db:orgname | $node/db:person | $node/db:personname"/>
    </xsl:when>
    <xsl:when test="$node/self::corpauthor or $node/self::corpcredit">
      <xsl:apply-templates select="$node"/>
    </xsl:when>
    <xsl:when test="$node/self::db:personname and not($node/db:surname)">
      <xsl:apply-templates select="$node/node()"/>
    </xsl:when>
    <!-- family-given -->
    <xsl:when test="$node/@role = 'family-given'">
      <xsl:apply-templates select="($node/surname | $node/db:surname)[1]"/>
      <xsl:if test="$node/surname | $node/db:surname">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="($node/firstname | $node/db:firstname)[1]"/>
    </xsl:when>
    <!-- last-first -->
    <xsl:when test="$node/@role = 'last-first'">
      <xsl:apply-templates select="($node/surname | $node/db:surname)[1]"/>
      <xsl:if test="$node/surname | $node/db:surname">
        <xsl:text>, </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="($node/firstname | $node/db:firstname)[1]"/>
    </xsl:when>
    <!-- first-last -->
    <xsl:otherwise>
      <xsl:if test="$node/honorific or $node/db:honorific">
        <xsl:apply-templates select="($node/honorific | $node/db:honorific)[1]"/>
      </xsl:if>
      <xsl:if test="$node/firstname or $node/db:firstname">
        <xsl:if test="$node/honorific or $node/db:honorific">
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:apply-templates select="$node/firstname[1] |
                                     $node/db:firstname[1]"/>
      </xsl:if>
      <xsl:if test="$node/othername or $node/db:othername">
        <xsl:if test="$node/honorific or $node/firstname or
                      $node/db:honorific or $node/db:firstname">
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:apply-templates select="$node/othername[1] |
                                     $node/db:othername[1]"/>
      </xsl:if>
      <xsl:if test="$node/surname or $node/db:surname">
        <xsl:if test="$node/honorific or $node/firstname or $node/othername or
                      $node/db:honorific or $node/db:firstname or
                      $node/db:othername">
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:apply-templates select="$node/surname[1] | $node/db:surname[1]"/>
      </xsl:if>
      <xsl:if test="$node/lineage or $node/db:lineage">
        <xsl:text>, </xsl:text>
        <xsl:apply-templates select="$node/lineage[1] | $node/db:lineage[1]"/>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db.personname.list
Outputs a list of people's names
$nodes: The elements containing tags such as #{firstname} and #{surname}

This template outputs a list of names of people as modelled by the #{personname}
element.  The #{personname} element allows authors to mark up components of a
person's name, such as the person's first name and surname.
-->
<xsl:template name="db.personname.list">
  <xsl:param name="nodes"/>
  <xsl:for-each select="$nodes">
    <xsl:choose>
      <xsl:when test="position() = 1"/>
      <xsl:when test="last() = 2">
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="' and '"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:when test="position() = last()">
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="', and '"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="', '"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:call-template name="db.personname">
      <xsl:with-param name="node" select="."/>
    </xsl:call-template>
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>
