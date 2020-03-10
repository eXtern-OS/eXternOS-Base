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
                xmlns:cache="http://projectmallard.org/cache/1.0/"
                xmlns:mal="http://projectmallard.org/1.0/"
                xmlns:exsl="http://exslt.org/common"
                extension-element-prefixes="exsl"
                exclude-result-prefixes="mal"
                version="1.0">

<!--!!==========================================================================
Mallard Topological Sort
Sort a Mallard document.
:Requires: mal-link
:Revision:version="1.0" date="2010-07-08"

This stylesheet contains utilities for sorting the pages in a Mallard
document based on their informational links.
-->


<!--**==========================================================================
mal.sort.tsort
Sort pages based on topic and next links.
:Revision:version="1.0" date="2010-07-08"
$node: The current #{page} in the Mallard cache file.

This template outputs links to pages sorted according to their topic and
next links. Pages occur after the first guide that references them, in
their sort order for that guide. Page series constructed with next links
always appear in order at the sort position of their first page.

This template outputs #{link} elements with #{xref} attributes pointing to
the target page. The output is a result tree fragment.  To use these results,
call #{exsl:node-set} on them.

You can specify a starting node with the ${node} parameter. By default, it
uses the node pointed to by @{mal.link.default_root}.

This template does not include any nodes that are not reachable through
topic or next links.
-->
<xsl:template name="mal.sort.tsort">
  <xsl:param name="node" select="key('mal.cache.key', $mal.link.default_root)"/>
  <xsl:variable name="sorted">
    <xsl:call-template name="_mal.sort.tsort.node">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:variable name="nodes" select="exsl:node-set($sorted)/mal:link"/>
  <xsl:for-each select="$nodes">
    <xsl:variable name="xref" select="@xref"/>
    <xsl:if test="not(preceding::*[string(@xref) = $xref]) and not(contains($xref, '#'))">
      <xsl:copy-of select="."/>
    </xsl:if>
  </xsl:for-each>
</xsl:template>

<!--#* _mal.sort.tsort.node -->
<xsl:template name="_mal.sort.tsort.node">
  <xsl:param name="node" select="key('mal.cache.key', $mal.link.default_root)"/>
  <xsl:param name="done" select="''"/>
  <xsl:variable name="linkid">
    <xsl:call-template name="mal.link.linkid">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>

  <mal:link xref="{$linkid}"/>

  <xsl:variable name="next" select="$node/mal:info/mal:link[@type = 'next']"/>
  <xsl:if test="$next">
    <xsl:variable name="linklinkid">
      <xsl:call-template name="mal.link.xref.linkid">
        <xsl:with-param name="node" select="$next"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$linklinkid != '' and not(contains($done, concat(' ', $linklinkid, ' ')))">
      <xsl:variable name="nextnode" select="key('mal.cache.key', $linklinkid)"/>
      <xsl:call-template name="_mal.sort.tsort.node">
        <xsl:with-param name="node" select="$nextnode"/>
        <xsl:with-param name="done" select="concat($done, ' ', $linkid, ' ')"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:if>

  <xsl:variable name="page" select="document($node/@cache:href)"/>

  <xsl:variable name="topics">
    <xsl:for-each select="$node | $node//mal:section">
      <xsl:variable name="positionsort" select="position()"/>
      <xsl:variable name="groups">
        <xsl:choose>
          <xsl:when test="self::mal:page">
            <xsl:call-template name="_mal.sort.getgroups">
              <xsl:with-param name="node" select="$page/mal:page"/>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="sectid">
              <xsl:value-of select="substring-after(@id, '#')"/>
            </xsl:variable>
            <xsl:call-template name="_mal.sort.getgroups">
              <xsl:with-param name="node" select="$page//mal:section[@id = $sectid]"/>
            </xsl:call-template>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>
      <xsl:variable name="subtopics">
        <xsl:call-template name="mal.link.topiclinks">
          <xsl:with-param name="node" select="."/>
          <xsl:with-param name="groups" select="$groups"/>
        </xsl:call-template>
      </xsl:variable>
      <xsl:for-each select="exsl:node-set($subtopics)/*">
        <xsl:copy>
          <xsl:attribute name="positionsort">
            <xsl:value-of select="$positionsort"/>
          </xsl:attribute>
          <xsl:for-each select="@* | node()">
            <xsl:copy-of select="."/>
          </xsl:for-each>
        </xsl:copy>
      </xsl:for-each>
    </xsl:for-each>
  </xsl:variable>
  <xsl:variable name="topicnodes" select="exsl:node-set($topics)/*"/>
  <xsl:variable name="newdone">
    <xsl:value-of select="$done"/>
    <xsl:for-each select="$topicnodes">
      <xsl:variable name="linklinkid">
        <xsl:call-template name="mal.link.xref.linkid"/>
      </xsl:variable>
      <xsl:if test="$linklinkid != ''">
        <xsl:value-of select="concat(' ', $linklinkid)"/>
      </xsl:if>
    </xsl:for-each>
    <xsl:text> </xsl:text>
  </xsl:variable>
  <xsl:for-each select="$topicnodes">
    <xsl:sort data-type="number" select="@positionsort"/>
    <xsl:sort data-type="number" select="@groupsort"/>
    <xsl:sort select="mal:title[@type = 'sort']"/>
    <xsl:variable name="linklinkid">
      <xsl:call-template name="mal.link.xref.linkid"/>
    </xsl:variable>
    <xsl:if test="$linklinkid != '' and not(contains($done, concat(' ', $linklinkid, ' ')))">
      <xsl:for-each select="$mal.cache">
      <xsl:variable name="topic" select="key('mal.cache.key', $linklinkid)"/>
      <xsl:if test="$topic">
        <xsl:call-template name="_mal.sort.tsort.node">
          <xsl:with-param name="node" select="$topic"/>
          <xsl:with-param name="done" select="$newdone"/>
        </xsl:call-template>
      </xsl:if>
      </xsl:for-each>
    </xsl:if>
  </xsl:for-each>
</xsl:template>

<!--#* _mal.sort.getgroups -->
<xsl:template name="_mal.sort.getgroups">
  <xsl:param name="node" select="."/>
  <xsl:variable name="groups">
    <xsl:text> </xsl:text>
    <xsl:choose>
      <xsl:when test="$node/mal:links[@type = 'topic']">
        <xsl:for-each select="$node/mal:links[@type = 'topic']">
          <xsl:text> </xsl:text>
          <xsl:value-of select="@groups"/>
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$node/@groups"/>
      </xsl:otherwise>
    </xsl:choose>
    <xsl:text> </xsl:text>
  </xsl:variable>
  <xsl:if test="not(contains($groups, ' #first '))">
    <xsl:text> #first </xsl:text>
  </xsl:if>
  <xsl:value-of select="$groups"/>
  <xsl:if test="not(contains($groups, ' #default '))">
    <xsl:text> #default </xsl:text>
  </xsl:if>
  <xsl:if test="not(contains($groups, ' #last '))">
    <xsl:text> #last </xsl:text>
  </xsl:if>
</xsl:template>

</xsl:stylesheet>

