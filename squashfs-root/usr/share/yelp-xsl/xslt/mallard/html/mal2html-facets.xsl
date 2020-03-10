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
                xmlns:facet="http://projectmallard.org/facet/1.0/"
                xmlns:exsl="http://exslt.org/common"
                xmlns:str="http://exslt.org/strings"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="mal cache facet exsl str"
                version="1.0">

<!--!!==========================================================================
Mallard to HTML - Facets
Support the Mallard Facets extension.

This stylesheet contains templates and supporting JavaScript for the Mallard
Facets extension.
-->

<!--**==========================================================================
mal2html.facets.controls
Output the controls to filter faceted links.
$node: The facets #{page} or #{section} to generate controls for.

REMARK: Describe this template
-->
<xsl:template name="mal2html.facets.controls">
  <xsl:param name="node" select="."/>
  <xsl:variable name="choices" select="$node/mal:info/facet:choice"/>
  <xsl:if test="count($choices) &gt; 0">
    <div class="facets">
      <xsl:for-each select="$choices">
        <div class="facet">
          <div class="title">
            <xsl:apply-templates mode="mal2html.inline.mode" select="facet:title/node()"/>
          </div>
          <ul>
            <xsl:for-each select="facet:case">
              <li>
                <label>
                  <input type="checkbox" checked="checked" class="facet">
                    <xsl:attribute name="data-facet-key">
                      <xsl:value-of select="../@key"/>
                    </xsl:attribute>
                    <xsl:attribute name="data-facet-values">
                      <xsl:value-of select="@values"/>
                    </xsl:attribute>
                  </input>
                  <xsl:text> </xsl:text>
                  <span>
                    <xsl:apply-templates mode="mal2html.inline.mode"/>
                  </span>
                </label>
              </li>
            </xsl:for-each>
          </ul>
        </div>
      </xsl:for-each>
    </div>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
mal2html.facets.links
Output the links for a facets node.
:Revision:version="1.0" date="2010-12-16" status="final"
$node: The facets #{page} or #{section} element to generate links for.

This template outputs links for a facets node. It gets the links from
*{mal.link.facetlinks}, sorts them, and outputs HTML #{a} elements for each
link. Each #{a} element has data attribute for each facet tag in ${node} in
the form of #{data-facet-KEY="VALUES"}, where #{KEY} is the key of the facet
tag and VALUES is the values.
-->
<xsl:template name="mal2html.facets.links">
  <xsl:param name="node" select="."/>
  <xsl:variable name="facetlinks">
    <xsl:call-template name="mal.link.facetlinks">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:variable name="links">
    <xsl:for-each select="exsl:node-set($facetlinks)/mal:link">
      <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:attribute name="class">
          <xsl:value-of select="'facet-link'"/>
        </xsl:attribute>
        <xsl:for-each select="facet:tag">
          <xsl:attribute name="data-facet-{@key}">
            <xsl:value-of select="@values"/>
          </xsl:attribute>
        </xsl:for-each>
      </xsl:copy>
    </xsl:for-each>
  </xsl:variable>
  <xsl:call-template name="mal2html.links.links">
    <xsl:with-param name="node" select="($node | $node/mal:links[@type='facet'])[last()]"/>
    <xsl:with-param name="links" select="exsl:node-set($links)/mal:link"/>
    <xsl:with-param name="role" select="'facet'"/>
    <xsl:with-param name="divs" select="true()"/>
  </xsl:call-template>
</xsl:template>


<!--**==========================================================================
mal2html.facets.js

REMARK: FIXME
-->
<xsl:template name="mal2html.facets.js">
<xsl:text><![CDATA[
$(document).ready(function () {
  $('input.facet').change(function () {
    var control = $(this);
    var content = control.closest('div.body,div.sect');
    content.find('.facet-link').each(function () {
      var link = $(this);
      var facets = link.parents('div.body,div.sect').children('div.region').children('div.contents').children('div.facets').children('div.facet');
      var visible = true;
      for (var i = 0; i < facets.length; i++) {
        var facet = facets.slice(i, i + 1);
        var facetvis = false;
        var inputs = facet.find('input.facet:checked');
        for (var j = 0; j < inputs.length; j++) {
          var input = inputs.slice(j, j + 1);
          var inputvis = false;
          var key = input.attr('data-facet-key');
          var values = input.attr('data-facet-values').split(' ');
          for (var k = 0; k < values.length; k++) {
            if (link.is('*[data-facet-' + key + ' ~= "' + values[k] + '"]')) {
              inputvis = true;
              break;
            }
          }
          if (inputvis) {
            facetvis = true;
            break;
          }
        }
        if (!facetvis) {
          visible = false;
          break;
        }
      }
      if (!visible)
        link.hide('fast');
      else
        link.show('fast');
    });
  });
});
]]></xsl:text>
</xsl:template>

</xsl:stylesheet>
