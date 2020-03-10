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
                xmlns:xl="http://www.w3.org/1999/xlink"
                xmlns="http://www.w3.org/1999/xhtml"
                exclude-result-prefixes="db xl msg"
                version="1.0">

<!--!!==========================================================================
DocBook to HTML - Inline Elements
:Requires: db-common db2html-xref l10n

REMARK: Describe this module
-->
<!--#% l10n.format.mode -->

<!--**==========================================================================
db2html.inline.children
Renders the children of an inline element.
$node: The element to render
$children: The child elements to process

REMARK: Document this template
-->
<xsl:template name="db2html.inline.children">
  <xsl:param name="node" select="."/>
  <xsl:param name="children" select="false()"/>

  <xsl:choose>
    <xsl:when test="$children">
      <xsl:apply-templates select="$children"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="db2html.inline.content.mode" select="$node"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
db2html.inline
Renders an inline element as an HTML #{span} element
$node: The element to render
$children: The child elements to process
$class: The value of the #{class} attribute on the #{span} tag
$lang: The locale of the text in ${node}
$name-class: The class to use for the name of the element

REMARK: Document this template

This template handles conditional processing.
-->
<xsl:template name="db2html.inline">
  <xsl:param name="node" select="."/>
  <xsl:param name="children" select="false()"/>
  <xsl:param name="class" select="''"/>
  <xsl:param name="lang" select="$node/@lang|$node/@xml:lang"/>
  <xsl:param name="name-class" select="local-name($node)"/>
  <xsl:variable name="xlink" select="$node/@xl:href"/>
  <xsl:variable name="linkend" select="$node/@linkend"/>

  <xsl:variable name="if">
    <xsl:call-template name="db.profile.test">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
  </xsl:variable>
  <xsl:if test="$if != ''">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="node" select="$node"/>
      <xsl:with-param name="class" select="concat($class, ' ', $name-class)"/>
    </xsl:call-template>
    <xsl:call-template name="html.lang.attrs">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor">
      <xsl:with-param name="node" select="$node"/>
    </xsl:call-template>
    <xsl:choose>
      <xsl:when test="$xlink or $linkend">
        <xsl:call-template name="db2html.xlink">
          <xsl:with-param name="node" select="$node"/>
          <xsl:with-param name="content">
            <xsl:call-template name="db2html.inline.children">
              <xsl:with-param name="node" select="$node"/>
              <xsl:with-param name="children" select="$children"/>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:call-template name="db2html.inline.children">
          <xsl:with-param name="node" select="$node"/>
          <xsl:with-param name="children" select="$children"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </span>
  </xsl:if>
</xsl:template>


<!--%%===========================================================================
db2html.inline.content.mode
FIXME

FIXME
-->
<xsl:template mode="db2html.inline.content.mode" match="*">
  <xsl:apply-templates/>
</xsl:template>


<!-- == Matched Templates == -->

<!-- = abbrev = -->
<xsl:template match="abbrev | db:abbrev">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = accel = -->
<xsl:template match="accel | db:accel">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = acronym = -->
<xsl:template match="acronym | db:acronym">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = action = -->
<xsl:template match="action">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = artpagenums = -->
<xsl:template match="artpagenums | db:artpagenums">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = application = -->
<xsl:template match="application | db:application">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'app'"/>
  </xsl:call-template>
</xsl:template>

<!-- = author = -->
<xsl:template match="author | db:author">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = author % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="author | db:author">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = authorinitials = -->
<xsl:template match="authorinitials | db:authorinitials">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = biblioid = -->
<xsl:template match="db:biblioid">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = citation = -->
<xsl:template match="citation | db:citation">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = citation % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="citation | db:citation">
  <xsl:call-template name="l10n.gettext">
    <xsl:with-param name="msgid" select="'citation.label'"/>
    <xsl:with-param name="node" select="."/>
    <xsl:with-param name="format" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = citation % l10n.format.mode = -->
<xsl:template mode="l10n.format.mode" match="msg:citation.label">
  <xsl:param name="node"/>
  <xsl:for-each select="$node[1]">
    <xsl:variable name="entry_abbrev"
                  select="key('db.biblio.abbrev.key', string($node))"/>
    <xsl:choose>
      <xsl:when test="$entry_abbrev">
        <xsl:call-template name="db2html.xref">
          <xsl:with-param name="linkend" select="$entry_abbrev/@id | $entry_abbrev/@xml:id"/>
          <xsl:with-param name="target" select="$entry_abbrev"/>
          <xsl:with-param name="content">
            <xsl:apply-templates select="node()"/>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="entry_label"
                      select="key('db.biblio.label.key', string($node))"/>
        <xsl:choose>
          <xsl:when test="$entry_label">
            <xsl:call-template name="db2html.xref">
              <xsl:with-param name="linkend" select="$entry_label/@id | $entry_label/@xml:id"/>
              <xsl:with-param name="target" select="$entry_label"/>
              <xsl:with-param name="content">
                <xsl:apply-templates select="node()"/>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:variable name="entry_id"
                          select="key('db.biblio.id.key', string($node))"/>
            <xsl:choose>
              <xsl:when test="$entry_id">
                <xsl:call-template name="db2html.xref">
                  <xsl:with-param name="linkend" select="$entry_id/@id | $entry_id/@xml:id"/>
                  <xsl:with-param name="target" select="$entry_id"/>
                  <xsl:with-param name="content">
                    <xsl:apply-templates select="node()"/>
                  </xsl:with-param>
                </xsl:call-template>
              </xsl:when>
              <xsl:otherwise>
                <xsl:apply-templates select="node()"/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:for-each>
</xsl:template>

<!-- = citetitle = -->
<xsl:template match="citetitle | db:citetitle">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = city = -->
<xsl:template match="city | db:city">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = classname = -->
<xsl:template match="classname | db:classname">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = code = -->
<xsl:template match="code | db:code">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = collab = -->
<xsl:template match="collab | db:collab">
  <xsl:apply-templates select="collabname |
                               db:org | db:orgname | db:person | db:personname"/>
</xsl:template>

<!-- = collabname = -->
<xsl:template match="collabname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = command = -->
<xsl:template match="command | db:command">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'cmd'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = computeroutput = -->
<xsl:template match="computeroutput | db:computeroutput">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'output'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = constant = -->
<xsl:template match="constant | db:constant">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = corpauthor = -->
<xsl:template match="corpauthor">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = corpcredit = -->
<xsl:template match="corpcredit">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = country = -->
<xsl:template match="country | db:country">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = database = -->
<xsl:template match="database | db:database">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'sys'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = date = -->
<xsl:template match="date | db:date">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = edition = -->
<xsl:template match="edition | db:edition">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = editor = -->
<xsl:template match="editor | db:editor">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = editor % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="editor | db:editor">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = email = -->
<xsl:template match="email | db:email">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = email % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="email | db:email">
  <xsl:text>&lt;</xsl:text>
  <a>
    <xsl:attribute name="href">
      <xsl:text>mailto:</xsl:text>
      <xsl:value-of select="string(.)"/>
    </xsl:attribute>
    <xsl:attribute name="title">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'email.tooltip'"/>
        <xsl:with-param name="node" select="."/>
        <xsl:with-param name="string" select="string(.)"/>
        <xsl:with-param name="format" select="true()"/>
      </xsl:call-template>
    </xsl:attribute>
    <xsl:apply-templates/>
  </a>
  <xsl:text>&gt;</xsl:text>
</xsl:template>

<!-- = emphasis = -->
<xsl:template match="emphasis | db:emphasis">
  <xsl:variable name="bold" select="@role = 'bold' or @role = 'strong'"/>
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class">
      <xsl:text>em</xsl:text>
      <xsl:if test="$bold">
        <xsl:text> em-bold</xsl:text>
      </xsl:if>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!-- = envar = -->
<xsl:template match="envar | db:envar">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'sys'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = errorcode = -->
<xsl:template match="errorcode | db:errorcode">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'error'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = errorname = -->
<xsl:template match="errorname | db:errorname">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'error'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = errortext = -->
<xsl:template match="errortext | db:errortext">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'error'"/>
  </xsl:call-template>
</xsl:template>

<!-- = errortype = -->
<xsl:template match="errortype | db:errortype">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'error'"/>
  </xsl:call-template>
</xsl:template>

<!-- = exceptionname = -->
<xsl:template match="exceptionname | db:exceptionname">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = fax = -->
<xsl:template match="fax | db:fax">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = filename = -->
<xsl:template match="filename | db:filename">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'file'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = firstname = -->
<xsl:template match="firstname | db:firstname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = firstterm = -->
<xsl:template match="firstterm | db:firstterm">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = firstterm % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="firstterm | db:firstterm">
  <xsl:choose>
    <xsl:when test="@linkend">
      <xsl:call-template name="db2html.xref">
        <xsl:with-param name="linkend" select="@linkend"/>
        <xsl:with-param name="content">
          <xsl:apply-templates/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = foreignphrase = -->
<xsl:template match="foreignphrase | db:foreignphrase">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = function = -->
<xsl:template match="function | db:function">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
  </xsl:call-template>
</xsl:template>

<!-- = glossterm = -->
<xsl:template match="glossterm | db:glossterm">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = glossterm % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="glossterm | db:glossterm">
  <xsl:choose>
    <xsl:when test="@linkend">
      <xsl:call-template name="db2html.xref">
        <xsl:with-param name="linkend" select="@linkend"/>
        <xsl:with-param name="content">
          <xsl:apply-templates/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:when>
    <xsl:when test="not(../self::glossentry) and not(../self::db:glossentry)">
      <xsl:variable name="glossentry" select="key('db.glossentry.key', string(.))"/>
      <xsl:choose>
        <xsl:when test="$glossentry">
          <xsl:call-template name="db2html.xref">
            <xsl:with-param name="linkend" select="$glossentry/@id | $glossentry/@xml:id"/>
            <xsl:with-param name="target" select="$glossentry"/>
            <xsl:with-param name="content">
              <xsl:apply-templates/>
            </xsl:with-param>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = guibutton = -->
<xsl:template match="guibutton | db:guibutton">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = guiicon = -->
<xsl:template match="guiicon | db:guiicon">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = guilabel = -->
<xsl:template match="guilabel | db:guilabel">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = guimenu = -->
<xsl:template match="guimenu | db:guimenu">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = guimenuitem = -->
<xsl:template match="guimenuitem | db:guimenuitem">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = guisubmenu = -->
<xsl:template match="guisubmenu | db:guisubmenu">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = hardware = -->
<xsl:template match="hardware | db:hardware">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = holder = -->
<xsl:template match="holder | db:holder">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = honorific = -->
<xsl:template match="honorific | db:honorific">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = inlineequation = -->
<xsl:template match="inlineequation | db:inlineequation">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = interface = -->
<xsl:template match="interface | db:interface">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'gui'"/>
  </xsl:call-template>
</xsl:template>

<!-- = interfacename = -->
<xsl:template match="interfacename | db:interfacename">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = isbn = -->
<xsl:template match="isbn | db:biblioid[@class = 'isbn']">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="name-class" select="'isbn'"/>
  </xsl:call-template>
</xsl:template>

<!-- = issn = -->
<xsl:template match="issn | db:biblioid[@class = 'issn']">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="name-class" select="'issn'"/>
  </xsl:call-template>
</xsl:template>

<!-- = issuenum = -->
<xsl:template match="issuenum | db:issuenum">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = jobtitle = -->
<xsl:template match="jobtitle | db:jobtitle">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = keycap = -->
<xsl:template match="keycap | db:keycap">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'key'"/>
  </xsl:call-template>
</xsl:template>

<!-- = keycap % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="keycap | db:keycap">
  <kbd>
    <xsl:if test=". = 'Fn'">
      <xsl:attribute name="class">
        <xsl:text>key-Fn</xsl:text>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates/>
  </kbd>
</xsl:template>

<!-- = keycode = -->
<xsl:template match="keycode | db:keycode">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = keycombo = -->
<xsl:template match="keycombo | db:keycombo">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'keyseq'"/>
  </xsl:call-template>
</xsl:template>

<!-- = keycombo % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="keycombo | db:keycombo">
  <xsl:variable name="joinchar">
    <xsl:choose>
      <xsl:when test="@action = 'seq'"><xsl:text> </xsl:text></xsl:when>
      <xsl:when test="@action = 'simul'">+</xsl:when>
      <xsl:when test="@action = 'press'">-</xsl:when>
      <xsl:when test="@action = 'click'">-</xsl:when>
      <xsl:when test="@action = 'double-click'">-</xsl:when>
      <xsl:when test="@action = 'other'">+</xsl:when>
      <xsl:otherwise>+</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:for-each select="*">
    <xsl:if test="position() != 1">
      <xsl:value-of select="$joinchar"/>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>

<!-- = keysym = -->
<xsl:template match="keysym | db:keysym">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = lineage = -->
<xsl:template match="lineage | db:lineage">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = lineannotation = -->
<xsl:template match="lineannotation | db:lineannotation">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = literal = -->
<xsl:template match="literal | db:literal">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = markup = -->
<xsl:template match="markup | db:markup">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = mathphrase = -->
<xsl:template match="mathphrase | db:mathphrase">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = medialabel = -->
<xsl:template match="medialabel">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = menuchoice = -->
<xsl:template match="menuchoice | db:menuchoice">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'guiseq'"/>
  </xsl:call-template>
</xsl:template>

<!-- = menuchoice % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="menuchoice | db:menuchoice">
  <xsl:variable name="arrow">
    <xsl:variable name="ltr">
      <xsl:call-template name="l10n.direction"/>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$ltr = 'rtl'">
        <xsl:text>&#x25C2;</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>&#x25B8;</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <xsl:for-each select="*[not(self::shortcut) and not(self::db:shortcut)]">
    <xsl:if test="position() != 1">
      <xsl:value-of select="concat('&#x00A0;', $arrow, ' ')"/>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
  <xsl:if test="shortcut or db:shortcut">
    <xsl:text> </xsl:text>
    <xsl:apply-templates select="shortcut | db:shortcut"/>
  </xsl:if>
</xsl:template>

<!-- = methodname = -->
<xsl:template match="methodname | db:methodname">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = mousebutton = -->
<xsl:template match="mousebutton | db:mousebutton">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = option = -->
<xsl:template match="option | db:option">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'cmd'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = optional = -->
<xsl:template match="optional | db:optional">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = optional % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="optional | db:optional">
  <xsl:text>[</xsl:text>
  <xsl:apply-templates/>
  <xsl:text>]</xsl:text>
</xsl:template>

<!-- = org = -->
<xsl:template match="db:org">
  <xsl:apply-templates select="db:orgname"/>
</xsl:template>

<!-- = orgdiv = -->
<xsl:template match="orgdiv | db:orgdiv">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = orgname = -->
<xsl:template match="orgname | db:orgname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = othercredit = -->
<xsl:template match="othercredit | db:othercredit">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = othercredit % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="othercredit | db:othercredit">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = othername = -->
<xsl:template match="othername | db:othername">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = package = -->
<xsl:template match="package | db:package">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'sys'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = pagenums = -->
<xsl:template match="pagenums | db:pagenums">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = parameter = -->
<xsl:template match="parameter | db:parameter">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class">
      <xsl:choose>
        <xsl:when test="@class = 'function'">
          <xsl:text>code</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>cmd</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = person = -->
<xsl:template match="db:person">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = person % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="db:person">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = personname = -->
<xsl:template match="personname | db:personname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = personname % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="personname | db:personname">
  <xsl:call-template name="db.personname"/>
</xsl:template>

<!-- = phone = -->
<xsl:template match="phone | db:phone">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = phrase = -->
<xsl:template match="phrase | db:phrase">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = pob = -->
<xsl:template match="pob | db:pob">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = postcode = -->
<xsl:template match="postcode | db:postcode">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = productname = -->
<xsl:template match="productname | db:productname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = productname % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="productname | db:productname">
  <xsl:apply-templates/>
  <xsl:choose>
    <xsl:when test="@class = 'copyright'">&#x00A9;</xsl:when>
    <xsl:when test="@class = 'registered'">&#x00AE;</xsl:when>
    <xsl:when test="@class = 'trade'">&#x2122;</xsl:when>
    <xsl:when test="@class = 'service'">&#x2120;</xsl:when>
  </xsl:choose>
</xsl:template>

<!-- = productnumber = -->
<xsl:template match="productnumber | db:productnumber">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = prompt = -->
<xsl:template match="prompt | db:prompt">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'output'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = property = -->
<xsl:template match="property | db:property">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'sys'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = pubdate = -->
<xsl:template match="pubdate | db:pubdate">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = publisher = -->
<xsl:template match="publisher | db:publisher">
  <xsl:apply-templates select="publishername | db:publishername"/>
</xsl:template>

<!-- = publishername = -->
<xsl:template match="publishername | db:publishername">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = ooclass = -->
<xsl:template match="ooclass | db:ooclass">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = ooclass % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="ooclass | db:ooclass">
  <xsl:for-each select="*">
    <xsl:if test="position() != 1">
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>

<!-- = ooexception = -->
<xsl:template match="ooexception | db:ooexception">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = ooexception % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="ooexception | db:ooexception">
  <xsl:for-each select="*">
    <xsl:if test="position() != 1">
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>

<!-- = oointerface = -->
<xsl:template match="oointerface | db:oointerface">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = oointerface % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="oointerface | db:oointerface">
  <xsl:for-each select="*">
    <xsl:if test="position() != 1">
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates select="."/>
  </xsl:for-each>
</xsl:template>

<!-- = quote = -->
<xsl:template match="quote | db:quote">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = quote % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="quote | db:quote">
  <xsl:call-template name="l10n.gettext">
    <xsl:with-param name="msgid">
      <xsl:choose>
        <xsl:when test="(count(ancestor::quote) mod 2) = 0">
          <xsl:text>quote.format</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>quote.inner.format</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
    <xsl:with-param name="node" select="."/>
    <xsl:with-param name="format" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = replaceable = -->
<xsl:template match="replaceable | db:replaceable">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'var'"/>
  </xsl:call-template>
</xsl:template>

<!-- = returnvalue = -->
<xsl:template match="returnvalue | db:returnvalue">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = sgmltag = -->
<xsl:template match="sgmltag | db:tag">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="name-class">sgmltag</xsl:with-param>
    <xsl:with-param name="class">
      <xsl:text>code sgmltag</xsl:text>
      <xsl:choose>
        <xsl:when test="@class = 'comment'">
          <xsl:value-of select="' sgmltag-sgmlcomment'"/>
        </xsl:when>
        <xsl:when test="@class">
          <xsl:value-of select="concat(' sgmltag-', @class)"/>
        </xsl:when>
      </xsl:choose>
    </xsl:with-param>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = sgmltag % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="sgmltag | db:tag">
  <xsl:choose>
    <xsl:when test="@class = 'attribute'">
      <xsl:apply-templates/>
    </xsl:when>
    <xsl:when test="@class = 'attvalue'">
      <xsl:apply-templates/>
    </xsl:when>
    <xsl:when test="@class = 'element'">
      <xsl:apply-templates/>
    </xsl:when>
    <xsl:when test="@class = 'emptytag'">
      <xsl:text>&lt;</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>/&gt;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'endtag'">
      <xsl:text>&lt;/</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>&gt;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'genentity'">
      <xsl:text>&amp;</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'localname'">
      <xsl:apply-templates/>
    </xsl:when>
    <xsl:when test="@class = 'namespace'">
      <xsl:apply-templates/>
    </xsl:when>
    <xsl:when test="@class = 'numcharref'">
      <xsl:text>&amp;#</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'paramentity'">
      <xsl:text>%</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'pi'">
      <xsl:text>&lt;?</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>&gt;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'prefix'">
      <xsl:apply-templates/>
      <xsl:text>:</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'sgmlcomment' or @class = 'comment'">
      <xsl:text>&lt;!--</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>--&gt;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'starttag'">
      <xsl:text>&lt;</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>&gt;</xsl:text>
    </xsl:when>
    <xsl:when test="@class = 'xmlpi'">
      <xsl:text>&lt;?</xsl:text>
      <xsl:apply-templates/>
      <xsl:text>?&gt;</xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = shortcut = -->
<xsl:template match="shortcut | db:shortcut">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = shortcut % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="shortcut | db:shortcut">
  <xsl:text>(</xsl:text>
  <xsl:apply-templates/>
  <xsl:text>)</xsl:text>
</xsl:template>

<!-- = state = -->
<xsl:template match="state | db:state">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = street = -->
<xsl:template match="street | db:street">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = structfield = -->
<xsl:template match="structfield">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = structname = -->
<xsl:template match="structname">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = subscript = -->
<xsl:template match="subscript | db:subscript">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <sub class="subscript">
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates/>
  </sub>
  </xsl:if>
</xsl:template>

<!-- = superscript = -->
<xsl:template match="superscript | db:superscript">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <sup class="superscript">
    <xsl:call-template name="db2html.anchor"/>
    <xsl:apply-templates/>
  </sup>
  </xsl:if>
</xsl:template>

<!-- = surname = -->
<xsl:template match="surname | db:surname">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = symbol = -->
<xsl:template match="symbol | db:symbol">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = systemitem = -->
<xsl:template match="systemitem | db:systemitem">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'sys'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = token = -->
<xsl:template match="token | db:token">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = trademark = -->
<xsl:template match="trademark | db:trademark">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = trademark % db2html.inline.content.mode = -->
<xsl:template mode="db2html.inline.content.mode" match="trademark | db:trademark">
  <xsl:apply-templates/>
  <xsl:choose>
    <xsl:when test="@class = 'copyright'">&#x00A9;</xsl:when>
    <xsl:when test="@class = 'registered'">&#x00AE;</xsl:when>
    <xsl:when test="@class = 'service'">&#x2120;</xsl:when>
    <xsl:otherwise>&#x2122;</xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!-- = type = -->
<xsl:template match="type | db:type">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = uri = -->
<xsl:template match="uri | db:uri">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'sys'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = userinput = -->
<xsl:template match="userinput | db:userinput">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'input'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = varname = -->
<xsl:template match="varname | db:varname">
  <xsl:call-template name="db2html.inline">
    <xsl:with-param name="class" select="'code'"/>
    <xsl:with-param name="ltr" select="true()"/>
  </xsl:call-template>
</xsl:template>

<!-- = volumenum = -->
<xsl:template match="volumenum | db:volumenum">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = wordasword = -->
<xsl:template match="wordasword | db:wordasword">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>

<!-- = year = -->
<xsl:template match="year | db:year">
  <xsl:call-template name="db2html.inline"/>
</xsl:template>


</xsl:stylesheet>
