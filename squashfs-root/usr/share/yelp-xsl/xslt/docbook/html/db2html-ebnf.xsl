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
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - EBNF Elements
:Requires: db2html-xref

REMARK: Describe this module
-->

<!-- FIXME: rhs/sbr -->

<!-- == Matched Templates == -->

<!-- = constraint = -->

<!-- = constraintdef = -->

<!-- = lhs = -->

<!-- = nonterminal = -->

<!-- = production = -->

<!-- = productionrecap = -->

<!-- = productionset = -->
<xsl:template match="productionset | db:productionset">
  <div>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'productionset'"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates select="title | db:title | db:info/db:title"/>
    <table class="productionset">
      <xsl:apply-templates select="production    | productionrecap |
                                   db:production | db:productionrecap"/>
    </table>
  </div>
</xsl:template>

<!-- = productionset/title = -->
<!-- FIXME
<xsl:template match="productionset/title">
  <xsl:call-template name="db2html.title.simple"/>
</xsl:template>
-->

<!-- = rhs = -->

</xsl:stylesheet>
