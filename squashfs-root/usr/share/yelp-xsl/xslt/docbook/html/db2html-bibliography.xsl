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
DocBook to HTML - Bibliographies
:Revision:version="3.4" date="2011-11-14" status="final"

This module provides templates to process DocBook bibliograpies.
-->


<!--**==========================================================================
db2html.biblioentry.data
Output structured data for a bibliography entry.
:Revision:version="3.4" date="2011-11-14" status="final"
$node: The #{biblioentry} or #{biblioset} element to output data for.

This template outputs a bibliography entry, or part of a bibliography entry,
based on structured data found in a #{biblioentry} or #{biblioset} element.
-->
<xsl:template name="db2html.biblioentry.data">
  <xsl:param name="node" select="."/>
  <xsl:variable name="authors" select="$node/author | $node/authorgroup/author |
                                       $node/db:author | $node/db:authorgroup/db:author"/>
  <xsl:if test="$authors">
    <xsl:call-template name="db.personname.list">
      <xsl:with-param name="nodes" select="$authors"/>
    </xsl:call-template>
    <xsl:text>. </xsl:text>
  </xsl:if>
  <xsl:variable name="titles" select="$node/title | $node/citetitle |
                                      $node/db:title | $node/db:citetitle"/>
  <xsl:if test="$titles">
    <xsl:apply-templates mode="db2html.biblioentry.mode" select="$titles[1]"/>
    <xsl:if test="$node/volumenum or $node/db:volumenum">
      <xsl:text>, </xsl:text>
      <xsl:apply-templates mode="db2html.biblioentry.mode"
                           select="($node/volumenum | $node/db:volumenum)[1]"/>
    </xsl:if>
    <xsl:if test="$node/issuenum or $node/db:issuenum">
      <xsl:text>, </xsl:text>
      <xsl:apply-templates mode="db2html.biblioentry.mode"
                           select="($node/issuenum | $node/db:issuenum)[1]"/>
    </xsl:if>
    <xsl:if test="$node/pagenums or $node/db:pagenums">
      <xsl:text>, </xsl:text>
      <xsl:apply-templates mode="db2html.biblioentry.mode"
                           select="($node/pagenums | $node/db:pagenums)[1]"/>
    </xsl:if>
    <xsl:if test="$node/artpagenums or $node/db:artpagenums">
      <xsl:text>, </xsl:text>
      <xsl:apply-templates mode="db2html.biblioentry.mode"
                           select="($node/artpagenums | $node/db:artpagenums)[1]"/>
    </xsl:if>
    <xsl:text>. </xsl:text>
  </xsl:if>
  <xsl:variable name="publisher" select="$node/publisher | $node/publishername |
                                         $node/db:publisher | $node/db:publishername"/>
  <xsl:if test="$publisher">
    <xsl:apply-templates mode="db2html.biblioentry.mode" select="$publisher[1]"/>
    <xsl:text>. </xsl:text>
  </xsl:if>
  <xsl:if test="$node/copyright or $node/db:copyright">
    <xsl:for-each select="$node/copyright | $node/db:copyright">
      <xsl:apply-templates mode="db2html.biblioentry.mode" select="."/>
      <xsl:if test="position() != 1">
        <xsl:call-template name="l10n.gettext">
          <xsl:with-param name="msgid" select="', '"/>
        </xsl:call-template>
      </xsl:if>
    </xsl:for-each>
    <xsl:text>. </xsl:text>
  </xsl:if>
  <xsl:for-each select="$node/isbn | $node/issn | $node/pubsnumber | $node/biblioid | $node/db:biblioid">
    <xsl:apply-templates mode="db2html.biblioentry.mode" select="."/>
    <xsl:text>. </xsl:text>
  </xsl:for-each>
  <xsl:for-each select="$node/date | $node/pubdate | $node/db:date | $node/db:pubdate">
    <xsl:apply-templates mode="db2html.biblioentry.mode" select="."/>
    <xsl:text>. </xsl:text>
  </xsl:for-each>
  <xsl:for-each select="$node/biblioset | $node/db:biblioset">
    <xsl:call-template name="db2html.biblioentry.data"/>
  </xsl:for-each>
</xsl:template>


<!--**==========================================================================
db2html.biblioentry.label
Output the label for a bibliography entry.
:Revision:version="3.4" date="2011-11-14" status="final"
$node: The #{biblioentry} or #{bibliomixed} element to generate a label for.

This template outputs a label to be placed inline at the beginning of a bibliography
entry. Labels are created for both #{biblioentry} and #{bibliomixed} elements.
The label is typically an abbreviation of the authors' names and the year of
publication. In DocBook, it is usually provided with a leading #{abbrev}
element. Without a leading #{abbrev} element, this template will instead
use the #{xreflabel} or #{id} attribute.
-->
<xsl:template name="db2html.biblioentry.label">
  <xsl:param name="node" select="."/>
  <xsl:if test="$node/*[1]/self::abbrev or $node/@xreflabel or $node/@id or
                $node/*[1]/self::db:abbrev or $node/@xml:id">
    <span class="bibliolabel">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'biblioentry.label'"/>
        <xsl:with-param name="node" select="."/>
        <xsl:with-param name="format" select="true()"/>
      </xsl:call-template>
    </span>
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>

<!--#% l10n.format.mode % msg:biblioentry.label -->
<xsl:template mode="l10n.format.mode" match="msg:biblioentry.label">
  <xsl:param name="node"/>
  <xsl:choose>
    <xsl:when test="$node/*[1]/self::abbrev">
      <xsl:apply-templates select="$node/abbrev[1]"/>
    </xsl:when>
    <xsl:when test="$node/*[1]/self::db:abbrev">
      <xsl:apply-templates select="$node/db:abbrev[1]"/>
    </xsl:when>
    <xsl:when test="$node/@xreflabel">
      <xsl:value-of select="$node/@xreflabel"/>
    </xsl:when>
    <xsl:when test="$node/@id">
      <xsl:value-of select="$node/@id"/>
    </xsl:when>
    <xsl:when test="$node/@xml:id">
      <xsl:value-of select="$node/@xml:id"/>
    </xsl:when>
  </xsl:choose>
</xsl:template>


<!--%%==========================================================================
db2html.biblioentry.mode
Format elements inside a #{biblioentry} or #{bibliomixed} element.
:Revision:version="3.4" date="2011-11-14" status="final"

This mode is used when processing the child elements of a #{biblioentry} or a
#{bibliomixed} element. Some elements are treated differently when they appear
inside a bibliography entry.
-->
<xsl:template mode="db2html.biblioentry.mode" match="*">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="local-name(.)"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates mode="db2html.biblioentry.mode"/>
  </span>
</xsl:template>

<!-- = abstract % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="abstract | db:abstract"/>

<!-- = affiliation % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="affiliation | db:affiliation"/>

<!-- = author % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="author | db:author">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = authorblurb % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="authorblurb"/>

<!-- = authorgroup % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="authorgroup | db:authorgroup">
  <xsl:call-template name="db.personname.list">
    <xsl:with-param name="nodes" select="*"/>
  </xsl:call-template>
</xsl:template>

<!-- = biblioset % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="biblioset | db:biblioset">
  <xsl:call-template name="db2html.biblioentry.data"/>
</xsl:template>

<!-- = citerefentry % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="citerefentry | db:citerefentry">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = collab % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="collab | db:collab">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = copyright % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="copyright | db:copyright">
  <xsl:call-template name="db.copyright"/>
</xsl:template>

<!-- = cover % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="db:cover"/>

<!-- = editor % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="editor | db:editor">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = footnote % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="footnote | footnoteref | db:footnote | db:footnoteref">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = glossterm % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="glossterm | db:glossterm">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = indexterm % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="indexterm | db:indexterm"/>

<!-- = legalnotice % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="legalnotice | db:legalnotice"/>

<!-- = mediaobject % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="mediaobject | db:mediaobject">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = org % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="db:org">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = othercredit % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="othercredit | db:othercredit">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = person % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="db:person">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = personname % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="personname | db:personname">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = personblurb % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="personblurb | db:personblurb"/>

<!-- = publisher % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="publisher | db:publisher">
  <xsl:apply-templates mode="db2html.biblioentry.mode"
                       select="publishername | db:publishername"/>
</xsl:template>

<!-- = printhistory % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="printhistory | db:printhistory"/>

<!-- = subscript % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="subscript | db:subscript">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = superscript % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="superscript | db:superscript">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = revhistory % db2html.biblioentry.mode = -->
<xsl:template mode="db2html.biblioentry.mode" match="revhistory | db:revhistory"/>


<!-- == Matched Templates == -->

<!-- = bibliography = -->
<xsl:template match="bibliography | db:bibliography">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="info" select="bibliographyinfo | db:info"/>
    <xsl:with-param name="divisions" select="bibliodiv | db:bibliodiv"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = bibliodiv = -->
<xsl:template match="bibliodiv | db:bibliodiv">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="info" select="db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = biblioentry = -->
<xsl:template match="biblioentry | db:biblioentry">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'biblioentry'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:call-template name="db2html.biblioentry.label"/>
    <xsl:call-template name="db2html.biblioentry.data"/>
  </div>
  </xsl:if>
</xsl:template>

<!-- = bibliomixed = -->
<xsl:template match="bibliomixed | db:bibliomixed">
  <xsl:variable name="node" select="."/>
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'biblimixed'"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:call-template name="db2html.biblioentry.label"/>
    <xsl:apply-templates mode="db2html.biblioentry.mode"
                         select="node()[not(set:has-same-node(., $node/*[1]/self::abbrev | $node/*[1]/self::db:abbrev))]"/>
  </div>
  </xsl:if>
</xsl:template>

<!-- = bibliolist = -->
<xsl:template match="bibliolist | db:bibliolist">
  <xsl:call-template name="db2html.block.formal">
    <xsl:with-param name="class" select="'list'"/>
  </xsl:call-template>
</xsl:template>

</xsl:stylesheet>
