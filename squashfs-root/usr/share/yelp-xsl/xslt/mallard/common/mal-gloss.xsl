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
                xmlns:cache="http://projectmallard.org/cache/1.0/"
                xmlns:gloss="http://projectmallard.org/experimental/gloss/"
                xmlns:exsl="http://exslt.org/common"
                xmlns:str="http://exslt.org/strings"
                exclude-result-prefixes="mal cache gloss exsl str"
                version="1.0">

<!--!!==========================================================================
Mallard Glossaries
Common templates for the Mallard Glossary extension.

This stylesheet contains utility templates for locating and linking to terms
with the Mallard Glossary extension.
-->


<!--++==========================================================================
mal.gloss.key
Get a #{gloss:term} element from its #{id} attribute.

This key returns #{gloss:term} elements based on their #{id} attribute. This
key only applies to elements inside a cache file. Make sure to make the cache
file the context document before calling this key.
-->
<xsl:key name="mal.gloss.key"
         match="/cache:cache//mal:info/gloss:term[@id]"
         use="@id"/>


<!--**==========================================================================
mal.gloss.match
Determine whether a glossary term matches a criterion.
$match: A #{gloss:match} element containing criteria.
$term: A #{gloss:term} element to attempt to match.

This template determines whether a glossary term matches a condition, as given
by a #{gloss:match} element. If the term matches, an empty string is output.
Otherwise, a non-empty string is output.

To determine if a term matches a set of matches, call this template for each
#{gloss:match} element, then check if the concatenated result is empty.
-->
<xsl:template name="mal.gloss.match">
  <xsl:param name="match"/>
  <xsl:param name="term"/>
  <xsl:if test="$match/@tags and not(str:split($match/@tags) = str:split($term/@tags))">
    <xsl:text>x</xsl:text>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
mal.gloss.terms
Output the glossary terms for a page or section.
$node: The glossary #{page} or #{section} to output terms for.

This template outputs the terms that should be displayed for ${node}.This output
is a result tree fragment. To use these results, call #{exsl:node-set} on them.
This template locates all terms throughout all pages and filters them based on
any #{gloss:match} elements in the #{info} child of ${node}, and also excludes
terms that are matched by child sections of ${node}.

The filtered terms are then grouped by matching ID. For each unique ID, this
template outputs a #{gloss:term} element with the corresponding #{id} attribute.
Each of these elements contains #{title} elements reflecting the titles in the
actual term definitions. These titles have duplicates removed, compared by the
space-normalized string value, and are sorted.

These #{gloss:term} elements then contain further #{gloss:term} elements, which
are copies of the actual terms with the same ID. These elements have an #{xref}
attribute added containing the ID of the containing page.

The top-level #{gloss:term} elements and the #{gloss:term} elements they contain
are not sorted. Only the #{title} elements in the top-level #{gloss:term}
elements are sorted.
-->
<xsl:template name="mal.gloss.terms">
  <xsl:param name="node" select="."/>
  <xsl:variable name="allterms_">
    <xsl:for-each select="$mal.cache//mal:info/gloss:term[@id]">
      <xsl:variable name="term" select="."/>
      <xsl:variable name="exclude">
        <xsl:for-each select="$node/ancestor-or-self::*/mal:info/gloss:match">
          <xsl:call-template name="mal.gloss.match">
            <xsl:with-param name="match" select="."/>
            <xsl:with-param name="term" select="$term"/>
          </xsl:call-template>
        </xsl:for-each>
        <xsl:for-each select="$node/mal:section/mal:info/gloss:match">
          <xsl:variable name="secmatch">
            <xsl:call-template name="mal.gloss.match">
              <xsl:with-param name="match" select="."/>
              <xsl:with-param name="term" select="$term"/>
            </xsl:call-template>
          </xsl:variable>
          <xsl:if test="$secmatch = ''">
            <xsl:text>x</xsl:text>
          </xsl:if>
        </xsl:for-each>
      </xsl:variable>
      <xsl:if test="$exclude = ''">
        <xsl:copy>
          <xsl:attribute name="xref">
            <xsl:value-of select="ancestor::mal:page[1]/@id"/>
          </xsl:attribute>
          <xsl:for-each select="@*[name() != 'xref'] | *">
            <xsl:choose>
              <xsl:when test="self::mal:title">
                <xsl:copy>
                  <xsl:attribute name="title">
                    <xsl:value-of select="normalize-space(.)"/>
                  </xsl:attribute>
                  <xsl:copy-of select="node()"/>
                </xsl:copy>
              </xsl:when>
              <xsl:otherwise>
                <xsl:copy-of select="."/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:copy>
      </xsl:if>
    </xsl:for-each>
  </xsl:variable>
  <xsl:variable name="allterms" select="exsl:node-set($allterms_)/gloss:term"/>
  <xsl:for-each select="$allterms">
    <xsl:if test="not(@id = preceding-sibling::gloss:term/@id)">
      <xsl:variable name="id" select="@id"/>
      <gloss:term id="{$id}">
        <xsl:variable name="entries" select="$allterms/self::gloss:term[@id = $id]"/>
        <xsl:variable name="titles_">
          <xsl:for-each select="$entries/mal:title">
            <xsl:copy-of select="."/>
          </xsl:for-each>
        </xsl:variable>
        <xsl:variable name="titles" select="exsl:node-set($titles_)/mal:title"/>
        <xsl:for-each select="$titles">
          <xsl:sort select="string(.)"/>
          <xsl:if test="not(@title = preceding-sibling::mal:title/@title)">
            <xsl:copy-of select="."/>
          </xsl:if>
        </xsl:for-each>
        <xsl:copy-of select="$entries"/>
      </gloss:term>
    </xsl:if>
  </xsl:for-each>
</xsl:template>

</xsl:stylesheet>
