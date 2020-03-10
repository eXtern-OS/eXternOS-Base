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
<!DOCTYPE xsl:stylesheet [
<!ENTITY % selectors SYSTEM "../common/db-selectors.mod">
%selectors;
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:db="http://docbook.org/ns/docbook"
                xmlns:set="http://exslt.org/sets"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db set"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Divisions
Handle division-level DocBook elements.
:Revision:version="3.8" date="2012-11-05" status="final"

This stylesheet contains templates to process top-level and sectioning elements
in DocBook. It handles chunking and implements the interfaces provided by the
common !{html} stylesheet.
-->


<!--%# html.title.mode -->
<xsl:template mode="html.title.mode" match="*">
  <xsl:variable name="title">
    <xsl:call-template name="db.title">
      <xsl:with-param name="node" select="."/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:value-of select="normalize-space($title)"/>
</xsl:template>

<!--%# html.header.mode -->
<xsl:template mode="html.header.mode" match="*">
  <xsl:call-template name="db2html.links.linktrail"/>
</xsl:template>

<!--%# html.footer.mode -->
<xsl:template mode="html.footer.mode" match="*">
  <xsl:call-template name="db2html.division.about"/>
</xsl:template>

<!--%# html.body.mode -->
<xsl:template mode="html.body.mode" match="*">
  <xsl:call-template name="db2html.links.next"/>
  <xsl:apply-templates select=".">
    <xsl:with-param name="depth_in_chunk" select="0"/>
  </xsl:apply-templates>
  <xsl:call-template name="db2html.links.next"/>
  <div class="clear"/>
</xsl:template>

<!--%# html.output.after.mode -->
<xsl:template mode="html.output.after.mode" match="*">
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:if test="count(ancestor::*) &lt; $db.chunk.max_depth">
    <xsl:for-each select="appendix     | db:appendix     | article    | db:article    |
                          bibliography | db:bibliography | bibliodiv  | db:bibliodiv  |
                          book         | db:book         | chapter    | db:chapter    |
                          colophon     | db:colophon     | dedication | db:dedication |
                          glossary     | db:glossary     | glossdiv   | db:glossdiv   |
                          index        | db:index        | lot        | db:lot        |
                          part         | db:part         | preface    | db:preface    |
                          refentry     | db:refentry     | reference  | db:reference  |
                          sect1    | sect2    | sect3    | sect4    | sect5    | section    |
                          db:sect1 | db:sect2 | db:sect3 | db:sect4 | db:sect5 | db:section |
                          setindex     | db:setindex     | simplesect | db:simplesect |
                          toc          | db:toc          ">
      <xsl:call-template name="html.output">
        <xsl:with-param name="node" select="."/>
      </xsl:call-template>
    </xsl:for-each>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
db2html.division.div
Renders the content of a division element, chunking children if necessary
$node: The element to render the content of
$info: The info child element of ${node}
$entries: The entry-style child elements
$divisions: The division-level child elements
$depth_in_chunk: The depth of ${node} in the containing chunk
$depth_of_chunk: The depth of the containing chunk in the document
$chunk_divisions: Whether to create new documents for ${divisions}

REMARK: Talk about some of the parameters
-->
<xsl:template name="db2html.division.div">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="/false"/>
  <xsl:param name="entries" select="/false"/>
  <xsl:param name="divisions" select="/false"/>
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:param>
  <!-- FIXME: these two parameters don't make much sense now -->
  <xsl:param name="chunk_divisions"
             select="($depth_in_chunk = 0) and
                     ($depth_of_chunk &lt; $db.chunk.max_depth)"/>
  <xsl:choose>
    <xsl:when test="$depth_in_chunk != 0">
      <div>
        <xsl:call-template name="html.lang.attrs">
          <xsl:with-param name="node" select="$node"/>
        </xsl:call-template>
        <xsl:call-template name="html.class.attr">
          <xsl:with-param name="node" select="$node"/>
          <xsl:with-param name="class">
            <xsl:value-of select="local-name($node)"/>
            <xsl:text> sect</xsl:text>
          </xsl:with-param>
        </xsl:call-template>
        <xsl:if test="$node/@id">
          <xsl:attribute name="id">
            <xsl:value-of select="$node/@id"/>
          </xsl:attribute>
        </xsl:if>
        <div class="inner">
          <xsl:call-template name="_db2html.division.div.inner">
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="info" select="$info"/>
            <xsl:with-param name="entries" select="$entries"/>
            <xsl:with-param name="divisions" select="$divisions"/>
            <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
            <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
            <xsl:with-param name="chunk_divisions" select="$chunk_divisions"/>
          </xsl:call-template>
        </div>
      </div>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="_db2html.division.div.inner">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="info" select="$info"/>
        <xsl:with-param name="entries" select="$entries"/>
        <xsl:with-param name="divisions" select="$divisions"/>
        <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
        <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
        <xsl:with-param name="chunk_divisions" select="$chunk_divisions"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!--#* _db2html.division.div.inner -->
<xsl:template name="_db2html.division.div.inner">
  <xsl:param name="node"/>
  <xsl:param name="info"/>
  <xsl:param name="entries"/>
  <xsl:param name="divisions"/>
  <xsl:param name="depth_in_chunk"/>
  <xsl:param name="depth_of_chunk"/>
  <xsl:param name="chunk_divisions"/>
  <xsl:call-template name="db2html.hgroup">
    <xsl:with-param name="node" select="$node"/>
    <xsl:with-param name="info" select="$info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
  </xsl:call-template>
  <div class="region">
    <div class="contents">
      <xsl:apply-templates mode="db2html.division.div.content.mode" select="$node">
        <xsl:with-param name="info" select="$info"/>
        <xsl:with-param name="entries" select="$entries"/>
        <xsl:with-param name="divisions" select="$divisions"/>
        <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
        <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
      </xsl:apply-templates>
    </div>
    <xsl:if test="$depth_in_chunk = 0 and
                  not($node/processing-instruction('db2html.no_sectionlinks'))">
      <xsl:call-template name="db2html.links.section">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="divisions" select="$divisions"/>
      </xsl:call-template>
    </xsl:if>
    <xsl:for-each select="$divisions">
      <xsl:if test="not($chunk_divisions) or not(self::&db_chunks;)">
        <xsl:apply-templates select=".">
          <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk + 1"/>
          <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
        </xsl:apply-templates>
      </xsl:if>
    </xsl:for-each>
    <xsl:if test="$depth_in_chunk = 0">
      <xsl:call-template name="db2html.footnote.footer">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
      </xsl:call-template>
    </xsl:if>
  </div>
</xsl:template>


<!--%%==========================================================================
db2html.division.div.content.mode
Renders the block-level content of a division element
$depth_in_chunk: The depth of the context element in the containing chunk
$depth_of_chunk: The depth of the containing chunk in the document

REMARK: Talk about how this works with #{callback}
-->
<xsl:template mode="db2html.division.div.content.mode" match="*">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="/false"/>
  <xsl:param name="entries" select="/false"/>
  <xsl:param name="divisions" select="/false"/>
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:param>
  <xsl:variable name="nots" select="$divisions | $entries |
                                    title | db:title | titleabbrev | db:titleabbrev | subtitle | db:subtitle"/>
  <xsl:apply-templates select="set:difference(*, $nots)">
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk + 1"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:apply-templates>
  <xsl:if test="$entries">
    <div>
      <dl class="{local-name($node)}">
        <xsl:apply-templates select="$entries">
          <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk + 1"/>
          <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
        </xsl:apply-templates>
      </dl>
    </div>
  </xsl:if>
</xsl:template>


<!--**==========================================================================
db2html.hgroup
Output the title and subtitle for an element.
$node: The element containing the title.
$info: FIXME.
$depth_in_chunk: The depth of ${node} in the containing chunk.

REMARK: Talk about the different kinds of title blocks
-->
<xsl:template name="db2html.hgroup">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="/false"/>
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:param>
  <xsl:variable name="title" select="($node/title | $info/title | $node/db:title | $info/db:title)[1]"/>
  <xsl:variable name="subtitle" select="($node/subtitle | $info/subtitle | $node/db:subtitle | $info/db:subtitle)[1]"/>
  <xsl:variable name="title_h">
    <xsl:choose>
      <xsl:when test="$depth_in_chunk &lt; 6">
        <xsl:value-of select="concat('h', $depth_in_chunk + 1)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>h6</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:variable name="subtitle_h">
    <xsl:choose>
      <xsl:when test="$depth_in_chunk &lt; 5">
        <xsl:value-of select="concat('h', $depth_in_chunk + 2)"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>h6</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <div class="hgroup">
    <xsl:element name="{$title_h}" namespace="{$html.namespace}">
      <xsl:attribute name="class">
        <xsl:text>title</xsl:text>
      </xsl:attribute>
      <xsl:if test="$title">
        <xsl:call-template name="db2html.anchor">
          <xsl:with-param name="node" select="$title"/>
        </xsl:call-template>
      </xsl:if>
      <xsl:choose>
        <xsl:when test="$title">
          <xsl:apply-templates select="$title/node()"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="db.title">
            <xsl:with-param name="node" select="$node"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:element>
    <xsl:if test="$subtitle">
      <xsl:element name="{$subtitle_h}" namespace="{$html.namespace}">
        <xsl:attribute name="class">
          <xsl:text>subtitle</xsl:text>
        </xsl:attribute>
        <xsl:apply-templates select="$subtitle/node()"/>
      </xsl:element>
    </xsl:if>
  </div>
</xsl:template>


<!--**==========================================================================
db2html.division.about
Output the copyrights, credits, and license information at the bottom of a page.
:Revision:version="3.8" date="2012-11-05" status="final"
$node: A division-level element a page is being created for.
$info: The info child element of ${node}

This template outputs copyright information, credits, and license information for
the division. By default it is called by the %{html.footer.mode} implementation.
-->
<xsl:template name="db2html.division.about">
  <xsl:param name="node" select="."/>
  <xsl:param name="info" select="
    $node/appendixinfo | $node/articleinfo  | $node/bibliographyinfo | $node/bookinfo |
    $node/chapterinfo  | $node/glossaryinfo | $node/indexinfo        | $node/partinfo |
    $node/prefaceinfo  | $node/refentryinfo | $node/referenceinfo    | $node/refsect1info |
    $node/refsect2info | $node/refsect3info | $node/refsectioninfo   | $node/sect1info |
    $node/sect2info    | $node/sect3info    | $node/sect4info        | $node/sect5info |
    $node/sectioninfo  | $node/setindexinfo | $node/db:info "/>
  <xsl:variable name="copyrights" select="$info/copyright | $info/db:copyright"/>
  <xsl:variable name="authors" select="
    $info/author     | $info/authorgroup/author       |
    $info/corpauthor | $info/authorgroup/corpauthor   |
    $info/db:author  | $info/db:authorgroup/db:author"/>
  <xsl:variable name="editors" select="
    $info/editor    | $info/authorgroup/editor |
    $info/db:editor | $info/db:authorgroup/db:editor"/>
  <xsl:variable name="translators" select="
    $info/corpcredit[@role = 'translator']               |
    $info/othercredit[@role = 'translator']              |
    $info/authorgroup/corpcredit[@role = 'translator']   |
    $info/authorgroup/othercredit[@role = 'translator']  |
    $info/db:othercredit[@class = 'translator']          |
    $info/db:authorgroup/db:othercredit[@class = 'translator']"/>
  <xsl:variable name="publishers" select="$info/publisher | $info/db:publisher"/>
  <xsl:variable name="othercredits" select="set:difference(
    $info/collab | $info/authorgroup/collab | $info/db:collab |
    $info/corpcredit     | $info/authorgroup/corpcredit  |
    $info/othercredit    | $info/authorgroup/othercredit |
    $info/db:othercredit | $info/db:authorgroup/db:othercredit,
    ($authors | $editors | $translators))"/>
  <xsl:variable name="legal" select="$info/legalnotice | $info/db:legalnotice"/>
  <xsl:if test="$copyrights or $authors or $editors or $translators or $publishers or $othercredits or $legal">
    <div class="sect about ui-expander" role="contentinfo">
      <div class="yelp-data yelp-data-ui-expander" data-yelp-expanded="false"/>
      <div class="inner">
      <div class="hgroup">
        <h2>
          <span class="title">
            <xsl:call-template name="l10n.gettext">
              <xsl:with-param name="msgid" select="'About'"/>
            </xsl:call-template>
          </span>
        </h2>
      </div>
      <div class="region">
        <div class="contents">
          <xsl:if test="$copyrights">
            <div class="copyrights">
              <xsl:for-each  select="$copyrights">
                <div class="copyright">
                  <xsl:call-template name="db.copyright"/>
                </div>
              </xsl:for-each>
            </div>
          </xsl:if>
          <xsl:if test="$authors">
            <div class="aboutblurb authors">
              <div class="title">
                <span class="title">
                  <xsl:call-template name="l10n.gettext">
                    <xsl:with-param name="msgid" select="'Written By'"/>
                  </xsl:call-template>
                </span>
              </div>
              <ul class="credits">
                <xsl:for-each select="$authors">
                  <li>
                    <xsl:apply-templates select="."/>
                  </li>
                </xsl:for-each>
              </ul>
            </div>
          </xsl:if>
          <xsl:if test="$editors">
            <div class="aboutblurb editors">
              <div class="title">
                <span class="title">
                  <xsl:call-template name="l10n.gettext">
                    <xsl:with-param name="msgid" select="'Edited By'"/>
                  </xsl:call-template>
                </span>
              </div>
              <ul class="credits">
                <xsl:for-each select="$editors">
                  <li>
                    <xsl:apply-templates select="."/>
                  </li>
                </xsl:for-each>
              </ul>
            </div>
          </xsl:if>
          <xsl:if test="$translators">
            <div class="aboutblurb translators">
              <div class="title">
                <span class="title">
                  <xsl:call-template name="l10n.gettext">
                    <xsl:with-param name="msgid" select="'Translated By'"/>
                  </xsl:call-template>
                </span>
              </div>
              <ul class="credits">
                <xsl:for-each select="$translators">
                  <li>
                    <xsl:apply-templates select="."/>
                  </li>
                </xsl:for-each>
              </ul>
            </div>
          </xsl:if>
          <xsl:if test="$publishers">
            <div class="aboutblurb publishers">
              <div class="title">
                <span class="title">
                  <xsl:call-template name="l10n.gettext">
                    <xsl:with-param name="msgid" select="'Published By'"/>
                  </xsl:call-template>
                </span>
              </div>
              <ul class="credits">
                <xsl:for-each select="$publishers">
                  <li>
                    <xsl:apply-templates select="."/>
                  </li>
                </xsl:for-each>
              </ul>
            </div>
          </xsl:if>
          <xsl:if test="$othercredits">
            <div class="aboutblurb othercredits">
              <div class="title">
                <span class="title">
                  <xsl:call-template name="l10n.gettext">
                    <xsl:with-param name="msgid" select="'Other Credits'"/>
                  </xsl:call-template>
                </span>
              </div>
              <ul class="credits">
                <xsl:for-each select="$othercredits">
                  <li>
                    <xsl:apply-templates select="."/>
                  </li>
                </xsl:for-each>
              </ul>
            </div>
          </xsl:if>
          <xsl:for-each select="$legal">
            <div class="aboutblurb license">
              <div class="title">
                <span class="title">
                  <xsl:choose>
                    <xsl:when test="title">
                      <xsl:apply-templates select="title/node()"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:call-template name="l10n.gettext">
                        <xsl:with-param name="msgid" select="'Legal'"/>
                      </xsl:call-template>
                    </xsl:otherwise>
                  </xsl:choose>
                </span>
              </div>
              <div class="contents">
                <xsl:apply-templates select="*[not(self::title or self::db:title or
                                             self::blockinfo or self::db:info or self::db:titleabbrev)]"/>
              </div>
            </div>
          </xsl:for-each>
        </div>
      </div>
      </div>
    </div>
  </xsl:if>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = appendix = -->
<xsl:template match="appendix | db:appendix">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot | refentry |
                    sect1        | section  | simplesect | toc |
                    db:bibliography | db:glossary | db:index   |
                    db:refentry     | db:sect1    | db:section |
                    db:simplesect   | db:toc"/>
    <xsl:with-param name="info" select="appendixinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = article = -->
<xsl:template match="article | db:article">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    appendix | bibliography | glossary | index      | lot |
                    refentry | sect1        | section  | simplesect | toc |
                    colophon | db:colophon |
                    db:appendix   | db:bibliography | db:glossary | db:index |
                    db:refentry   | db:sect1        | db:section  |
                    db:simplesect | db:toc "/>
    <xsl:with-param name="info" select="articleinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = book = -->
<xsl:template match="book | db:book">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    appendix | article    | bibliography | chapter   |
                    colophon | dedication | glossary     | index     |
                    lot      | part       | preface      | reference |
                    setindex | toc        |
                    db:acknowledgements | db:appendix | db:article   |
                    db:bibliography     | db:chapter  | db:colophon  |
                    db:dedication       | db:glossary | db:index     |
                    db:part             | db:preface  | db:reference |
                    db:toc"/>
    <xsl:with-param name="info" select="bookinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="autotoc_depth" select="2"/>
  </xsl:call-template>
</xsl:template>

<!-- = chapter = -->
<xsl:template match="chapter | db:chapter">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot | refentry |
                    sect1        | section  | simplesect | toc |
                    db:bibliography | db:glossary | db:index    |
                    db:refentry     | db:sect1    | db:section  |
                    db:simplesect   | db:toc"/>
    <xsl:with-param name="info" select="chapterinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = colophon = -->
<xsl:template match="colophon | db:colophon">
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

<!-- = dedication = -->
<xsl:template match="dedication | db:dedication">
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

<!-- = glossary = -->
<xsl:template match="glossary | db:glossary">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="entries" select="glossentry | db:glossentry"/>
    <xsl:with-param name="divisions" select="glossdiv | bibliography | db:glossdiv | db:bibliography"/>
    <xsl:with-param name="info" select="glossaryinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = glossdiv = -->
<xsl:template match="glossdiv | db:glossdiv">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="entries" select="glossentry | db:glossentry"/>
    <xsl:with-param name="divisions" select="bibliography | db:bibliography"/>
    <xsl:with-param name="info" select="db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = part = -->
<xsl:template match="part | db:part">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    appendix | article   | bibliography | chapter |
                    glossary | index     | lot          | preface |
                    refentry | reference | toc          | db:colophon |
                    db:appendix  | db:article   | db:bibliography |
                    db:chapter   | db:glossary  | db:index        |
                    db:preface   | db:refentry  | db:reference    |
                    db:toc"/>
    <xsl:with-param name="info" select="partinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = preface = -->
<xsl:template match="preface | db:preface">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    refentry | simplesect | sect1    | section      | toc  |
                    lot      | index      | glossary | bibliography |
                    db:refentry | db:simplesect | db:sect1    | db:section |
                    db:toc      | db:index      | db:glossary |
                    db:bibliography "/>
    <xsl:with-param name="info" select="prefaceinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = qandadiv = -->
<xsl:template match="qandadiv | db:qandadiv">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="info" select="blockinfo | db:info"/>
    <xsl:with-param name="entries" select="qandaentry | db:qandaentry"/>
    <xsl:with-param name="divisions" select="qandadiv | db:qandadiv"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="chunk_divisions" select="false()"/>
    <xsl:with-param name="autotoc_divisions" select="false()"/>
  </xsl:call-template>
</xsl:template>

<!-- = qandaset = -->
<xsl:template match="qandaset | db:qandaset">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="info" select="blockinfo | db:info"/>
    <xsl:with-param name="entries" select="qandaentry | db:qandaentry"/>
    <xsl:with-param name="divisions" select="qandadiv | db:qandadiv"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
    <xsl:with-param name="chunk_divisions" select="false()"/>
    <xsl:with-param name="autotoc_divisions" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = reference = -->
<xsl:template match="reference | db:reference">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="refentry | db:refentry"/>
    <xsl:with-param name="info" select="referenceinfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = sect1 = -->
<xsl:template match="sect1 | db:sect1">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot |
                    refentry     | sect2    | simplesect | toc |
                    db:bibliography | db:glossary | db:index      |
                    db:refentry     | db:sect2    | db:simplesect |
                    db:toc "/>
    <xsl:with-param name="info" select="sect1info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = sect2 = -->
<xsl:template match="sect2 | db:sect2">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot |
                    refentry     | sect3    | simplesect | toc |
                    db:bibliography | db:glossary   | db:index | db:refentry |
                    db:sect3        | db:simplesect | db:toc "/>
    <xsl:with-param name="info" select="sect2info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = sect3 = -->
<xsl:template match="sect3 | db:sect3">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot |
                    refentry     | sect4    | simplesect | toc |
                    db:bibliography | db:glossary   | db:index | db:refentry |
                    db:sect4        | db:simplesect | db:toc "/>
    <xsl:with-param name="info" select="sect3info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = sect4 = -->
<xsl:template match="sect4 | db:sect4">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot |
                    refentry     | sect5    | simplesect | toc |
                    db:bibliography | db:glossary   | db:index | db:refentry |
                    db:sect5        | db:simplesect | db:toc "/>
    <xsl:with-param name="info" select="sect4info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = sect5 = -->
<xsl:template match="sect5 | db:sect5">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary   | index | lot |
                    refentry     | simplesect | toc   |
                    db:bibliography | db:glossary   | db:index |
                    db:refentry     | db:simplesect | db:toc   "/>
    <xsl:with-param name="info" select="sect5info | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = section = -->
<xsl:template match="section | db:section">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="divisions" select="
                    bibliography | glossary | index      | lot |
                    refentry     | section  | simplesect | toc |
                    db:bibliography | db:glossary   | db:index | db:refentry |
                    db:section      | db:simplesect | db:toc "/>
    <xsl:with-param name="info" select="sectioninfo | db:info"/>
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

<!-- = simplesect = -->
<xsl:template match="simplesect | db:simplesect">
  <xsl:param name="depth_in_chunk">
    <xsl:call-template name="db.chunk.depth-in-chunk"/>
  </xsl:param>
  <xsl:param name="depth_of_chunk">
    <xsl:call-template name="db.chunk.depth-of-chunk"/>
  </xsl:param>
  <xsl:call-template name="db2html.division.div">
    <xsl:with-param name="depth_in_chunk" select="$depth_in_chunk"/>
    <xsl:with-param name="depth_of_chunk" select="$depth_of_chunk"/>
  </xsl:call-template>
</xsl:template>

</xsl:stylesheet>
