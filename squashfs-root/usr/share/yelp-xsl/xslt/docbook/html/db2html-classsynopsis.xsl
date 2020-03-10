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
DocBook to HTML - Class Synopses
:Requires: db2html-xref html
:Revision:version="1.0" date="2011-05-16" status="final"

This module handles the DocBook #{classsynopsis} and related elements. The
contents of the class-modeling elements are processed in a mode depending on
the programming language to format the synopsis correctly.
-->

<xsl:variable name="db2html.classsynopsis.tab"
              select="'&#x00A0;&#x00A0;&#x00A0;&#x00A0;'"/>


<!--@@==========================================================================
db2html.classsynopsis.language
The default programming language used to format #{classsynopsis} elements.
:Revision:version="1.0" date="2011-05-16" status="final"

This parameter sets the default value for the #{language} attribute of elements
like #{classsynopsis}. Templates in this module will always use the #{language}
attribute if present. Otherwise, they fall back to this value. This parameter
can be set with the #{db2html.classsynopsis.language} processing instruction
at the root of a DocBook document.
-->
<xsl:param name="db2html.classsynopsis.language">
  <xsl:choose>
    <xsl:when test="/processing-instruction('db2html.classsynopsis.language')">
      <xsl:value-of
       select="/processing-instruction('db2html.classsynopsis.language')"/>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="'cpp'"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:param>


<!-- == Matched Templates == -->

<!-- = *synopsis = -->
<xsl:template match="
              classsynopsis     | constructorsynopsis    | fieldsynopsis |
              methodsynopsis    | destructorsynopsis     |
              db:classsynopsis  | db:constructorsynopsis | db:fieldsynopsis |
              db:methodsynopsis | db:destructorsynopsis  |">
  <xsl:variable name="if"><xsl:call-template name="db.profile.test"/></xsl:variable>
  <xsl:if test="$if != ''">
  <xsl:variable name="language">
    <xsl:choose>
      <xsl:when test="@language">
        <xsl:value-of select="@language"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$db2html.classsynopsis.language"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <div>
    <xsl:call-template name="html.lang.attrs"/>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class">
        <xsl:text>synopsis </xsl:text>
        <xsl:value-of select="local-name(.)"/>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:call-template name="db2html.anchor"/>
    <pre class="contents {local-name(.)} classsynopsis-{$language}">
      <xsl:choose>
        <xsl:when test="$language = 'cpp'">
          <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
        </xsl:when>
        <xsl:when test="$language = 'python'">
          <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:message>
            <xsl:text>No information about the language '</xsl:text>
            <xsl:value-of select="$language"/>
            <xsl:text>' for classsynopsis.</xsl:text>
          </xsl:message>
        </xsl:otherwise>
      </xsl:choose>
    </pre>
  </div>
  </xsl:if>
</xsl:template>

<!-- = classsynopsisinfo = -->
<xsl:template match="classsynopsisinfo | db:classsynopsisinfo">
  <xsl:apply-templates/>
  <!-- FIXME? -->
  <xsl:text>&#x000A;</xsl:text>
</xsl:template>

<!-- = methodparam = -->
<xsl:template match="methodparam | db:methodparam">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'methodparam'"/>
    </xsl:call-template>
    <xsl:for-each select="*">
      <xsl:if test="position() != 1">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates select="."/>
    </xsl:for-each>
  </span>
</xsl:template>

<!--#* db2html.class.cpp.modifier -->
<xsl:template name="db2html.class.cpp.modifier">
  <!-- For C++, we expect the first modifier to be the visibility -->
  <xsl:variable name="prec" select="self::*[../self::classsynopsis]/preceding-sibling::constructorsynopsis |
                                    self::*[../self::classsynopsis]/preceding-sibling::destructorsynopsis  |
                                    self::*[../self::classsynopsis]/preceding-sibling::fieldsynopsis       |
                                    self::*[../self::classsynopsis]/preceding-sibling::methodsynopsis      |
                                    self::*[../self::db:classsynopsis]/preceding-sibling::db:constructorsynopsis |
                                    self::*[../self::db:classsynopsis]/preceding-sibling::db:destructorsynopsis  |
                                    self::*[../self::db:classsynopsis]/preceding-sibling::db:fieldsynopsis       |
                                    self::*[../self::db:classsynopsis]/preceding-sibling::db:methodsynopsis      "/>
  <xsl:choose>
    <xsl:when test="not($prec[modifier][last()][modifier[1] = current()/modifier[1]]) and
                    not($prec[db:modifier][last()][db:modifier[1] = current()/db:modifier[1]])">
      <xsl:if test="$prec"><xsl:text>&#x000A;</xsl:text></xsl:if>
      <xsl:apply-templates select="(modifier | db:modifier)[1]"/>
      <xsl:text>:&#x000A;</xsl:text>
    </xsl:when>
    <xsl:when test="$prec and (name($prec[last()]) != name(.))">
      <xsl:text>&#x000A;</xsl:text>
    </xsl:when>
  </xsl:choose>
</xsl:template>


<!--%%==========================================================================
db2html.class.cpp.mode
Process a C++ synopsis.
:Revision:version="1.0" date="2011-05-16" status="final"

This mode is applied to child elements for synopsis elements for the C++
programming language. In C++ synopses, the first #{modifier} element for
methods is expected to mark the visibility, such as #{public} or #{private}.
-->
<xsl:template mode="db2html.class.cpp.mode" match="*">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = classsynopsis % db2html.class.cpp.mode = -->
<xsl:template mode="db2html.class.cpp.mode"
              match="classsynopsis | db:classsynopsis">
  <!-- classsynopsis = element classsynopsis {
         attribute language { ... }?,
         attribute class { ... }?,
         ooclass+,
         (classsynopsisinfo  | constructorsynopsis |
          destructorsynopsis | fieldsynopsis       |
          methodsynopsis     )
       }
  -->
  <xsl:if test="@class = 'class' or not(@class)">
    <span class="ooclass">
      <xsl:for-each select="ooclass[1]/modifier | db:ooclass[1]/db:modifier">
        <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
        <xsl:text> </xsl:text>
      </xsl:for-each>
      <xsl:text>class </xsl:text>
      <xsl:apply-templates mode="db2html.class.cpp.mode"
                           select="ooclass[1]/classname |
                                   db:ooclass[1]/db:classname"/>
    </span>
    <xsl:if test="ooclass[2] or db:ooclass[2]">
      <xsl:text> : </xsl:text>
      <xsl:for-each select="ooclass[position() != 1] |
                            db:ooclass[position() != 1]">
        <xsl:if test="position() != 1">
          <xsl:text>, </xsl:text>
        </xsl:if>
        <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
      </xsl:for-each>
    </xsl:if>
    <xsl:text>&#x000A;{&#x000A;</xsl:text>
    <xsl:apply-templates mode="db2html.class.cpp.mode"
                         select="
                           classsynopsisinfo      |
                           constructorsynopsis    | destructorsynopsis    |
                           fieldsynopsis          | methodsynopsis        |
                           db:classsynopsisinfo   |
                           db:constructorsynopsis | db:destructorsynopsis |
                           db:fieldsynopsis       | db:methodsynopsis     "/>
    <xsl:text>}&#x000A;</xsl:text>
  </xsl:if>
</xsl:template>

<!-- = constructorsynopsis % db2html.class.cpp.mode = -->
<xsl:template mode="db2html.class.cpp.mode"
              match="constructorsynopsis | db:constructorsynopsis">
  <!-- constructorsynopsis = element constructorsynopsis {
         attribute language { ... }?,
         modifier+,
         methodname?,
         (methodparam+ | void?)
       }
  -->
  <xsl:call-template name="db2html.class.cpp.modifier"/>
  <xsl:value-of select="$db2html.classsynopsis.tab"/>
  <xsl:for-each select="modifier[position() != 1] | db:modifier[position() != 1]">
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
    <xsl:text> </xsl:text>
  </xsl:for-each>
  <xsl:choose>
    <xsl:when test="methodname or db:methodname">
      <xsl:apply-templates mode="db2html.class.cpp.mode"
                           select="methodname | db:methodname"/>
    </xsl:when>
    <xsl:when test="../self::classsynopsis[ooclass]">
      <span class="methodname">
        <xsl:value-of select="../ooclass/classname"/>
      </span>
    </xsl:when>
    <xsl:when test="../self::db:classsynopsis[db:ooclass]">
      <span class="methodname">
        <xsl:value-of select="../db:ooclass/db:classname"/>
      </span>
    </xsl:when>
  </xsl:choose>
  <xsl:text>(</xsl:text>
  <xsl:for-each select="methodparam | db:methodparam">
    <xsl:if test="position() != 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
  </xsl:for-each>
  <xsl:text>);&#x000A;</xsl:text>
</xsl:template>

<!-- = destructorsynopsis % db2html.class.cpp.mode = -->
<xsl:template mode="db2html.class.cpp.mode"
              match="destructorsynopsis | db:destructorsynopsis">
  <!-- destructorsynopsis = element destructorsynopsis {
         attribute language { ... }?,
         modifier+,
         methodname?,
         (methodparam+ | void?)
       }
  -->
  <xsl:call-template name="db2html.class.cpp.modifier"/>
  <xsl:value-of select="$db2html.classsynopsis.tab"/>
  <xsl:for-each select="modifier[position() != 1] | db:modifier[position() != 1]">
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
    <xsl:text> </xsl:text>
  </xsl:for-each>
  <xsl:choose>
    <xsl:when test="methodname">
      <xsl:apply-templates mode="db2html.class.cpp.mode"
                           select="methodname | db:methodname"/>
    </xsl:when>
    <xsl:when test="../self::classsynopsis[ooclass]">
      <span class="methodname">
        <xsl:text>~</xsl:text>
        <xsl:value-of select="../ooclass/classname"/>
      </span>
    </xsl:when>
    <xsl:when test="../self::db:classsynopsis[db:ooclass]">
      <span class="methodname">
        <xsl:value-of select="../db:ooclass/db:classname"/>
      </span>
    </xsl:when>
  </xsl:choose>
  <xsl:text>(</xsl:text>
  <xsl:for-each select="methodparam | db:methodparam">
    <!-- FIXME: should we do each methodparam on its own line? -->
    <xsl:if test="position() != 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
  </xsl:for-each>
  <xsl:text>);&#x000A;</xsl:text>
</xsl:template>

<!-- = fieldsynopsis % db2html.class.cpp.mode = -->
<xsl:template mode="db2html.class.cpp.mode"
              match="fieldsynopsis | db:fieldsynopsis">
  <!-- fieldsynopsis = element fieldsynopsis {
         attribute language { ... }?,
         modifier+,
         type,
         varname,
         initializer?
       }
  -->
  <xsl:call-template name="db2html.class.cpp.modifier"/>
  <xsl:value-of select="$db2html.classsynopsis.tab"/>
  <xsl:for-each select="modifier[position() != 1] | db:modifier[position() != 1]">
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
    <xsl:text> </xsl:text>
  </xsl:for-each>
  <xsl:if test="type or db:type">
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="type | db:type"/>
    <xsl:text> </xsl:text>
  </xsl:if>
  <xsl:apply-templates mode="db2html.class.cpp.mode"
                       select="varname | db:varname"/>
  <xsl:if test="initializer or db:initializer">
    <xsl:text> = </xsl:text>
    <xsl:apply-templates mode="db2html.class.cpp.mode"
                         select="initializer | db:initializer"/>
  </xsl:if>
  <xsl:text>;&#x000A;</xsl:text>
</xsl:template>

<!-- = methodparam % db2html.class.cpp.mode = -->
<xsl:template mode="db2html.class.cpp.mode"
              match="methodparam | db:methodparam">
  <span>
    <xsl:call-template name="html.class.attr">
      <xsl:with-param name="class" select="'methodparam'"/>
    </xsl:call-template>
    <xsl:for-each select="*">
      <xsl:if test="position() != 1">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:if test="self::initializer or self::db:initializer">
        <xsl:text>= </xsl:text>
      </xsl:if>
      <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
    </xsl:for-each>
  </span>
</xsl:template>

<!-- = methodsynopsis % db2html.class.cpp.mode = -->
<xsl:template mode="db2html.class.cpp.mode"
              match="methodsynopsis | db:methodsynopsis">
  <!-- methodsynopsis = element methodsynopsis {
         attribute language { ... }?,
         modifier+,
         (type | void),
         methodname,
         (methodparam+ | void?)
       }
  -->
  <xsl:call-template name="db2html.class.cpp.modifier"/>
  <xsl:value-of select="$db2html.classsynopsis.tab"/>
  <!-- Parens for document order -->
  <xsl:for-each select="(methodname/preceding-sibling::modifier |
                         db:methodname/preceding-sibling::db:modifier)[position() != 1]">
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
    <xsl:text> </xsl:text>
  </xsl:for-each>
  <xsl:apply-templates mode="db2html.class.cpp.mode"
                       select="type | methodname/preceding-sibling::void |
                               db:type | db:methodname/preceding-sibling::db:void"/>
  <xsl:text> </xsl:text>
  <xsl:apply-templates mode="db2html.class.cpp.mode"
                       select="methodname | db:methodname"/>
  <xsl:text>(</xsl:text>
  <xsl:for-each select="methodparam | db:methodparam">
    <xsl:if test="position() != 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
  </xsl:for-each>
  <xsl:text>)</xsl:text>
  <xsl:for-each select="methodname/following-sibling::modifier |
                        db:methodname/following-sibling::db:modifier">
    <xsl:text> </xsl:text>
    <xsl:apply-templates mode="db2html.class.cpp.mode" select="."/>
  </xsl:for-each>
  <xsl:text>;&#x000A;</xsl:text>
</xsl:template>


<!--%%==========================================================================
db2html.class.python.mode
Process a Python synopsis.
:Revision:version="1.0" date="2011-05-16" status="final"

This mode is applied to child elements for synopsis elements for the Python
programming language.
-->
<xsl:template mode="db2html.class.python.mode" match="*">
  <xsl:apply-templates select="."/>
</xsl:template>

<!-- = classsynopsis % db2html.class.python.mode = -->
<xsl:template mode="db2html.class.python.mode"
              match="classsynopsis | db:classsynopsis">
  <!-- classsynopsis = element classsynopsis {
         attribute language { ... }?,
         attribute class { ... }?,
         ooclass+,
         (classsynopsisinfo  | constructorsynopsis |
          destructorsynopsis | fieldsynopsis       |
          methodsynopsis     )
       }
  -->
  <xsl:if test="@class = 'class' or not(@class)">
    <xsl:text>class </xsl:text>
    <xsl:apply-templates mode="db2html.class.python.mode"
                         select="ooclass[1] | db:ooclass[1]"/>
    <xsl:if test="ooclass[2] or db:ooclass[2]">
      <xsl:text>(</xsl:text>
      <xsl:for-each select="(ooclass | db:ooclass)[position() != 1]">
        <xsl:if test="position() != 1">
          <xsl:text>, </xsl:text>
        </xsl:if>
        <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
      </xsl:for-each>
      <xsl:text>)</xsl:text>
    </xsl:if>
    <xsl:text>:&#x000A;</xsl:text>
    <xsl:for-each select="classsynopsisinfo     | constructorsynopsis    |
                          destructorsynopsis    | fieldsynopsis          |
                          methodsynopsis        |
                          db:classsynopsisinfo  | db:constructorsynopsis |
                          db:destructorsynopsis | db:fieldsynopsis       |
                          db:methodsynopsis     ">
      <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
      <xsl:if test="position() != last() and local-name(following-sibling::*[1]) != local-name(.)">
        <xsl:text>&#x000A;</xsl:text>
      </xsl:if>
    </xsl:for-each>
  </xsl:if>
</xsl:template>

<!-- = constructorsynopsis % db2html.class.python.mode = -->
<xsl:template mode="db2html.class.python.mode"
              match="constructorsynopsis | db:constructorsynopsis">
  <!-- constructorsynopsis = element constructorsynopsis {
         attribute language { ... }?,
         modifier+,
         methodname?,
         (methodparam+ | void?)
       }
  -->
  <xsl:variable name="tab">
    <xsl:if test="../self::classsynopsis or ../self::db:classsynopsis">
      <xsl:value-of select="$db2html.classsynopsis.tab"/>
    </xsl:if>
  </xsl:variable>
  <xsl:for-each select="modifier | db:modifier">
    <xsl:value-of select="$tab"/>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
    <xsl:text>&#x000A;</xsl:text>
  </xsl:for-each>
  <xsl:value-of select="$tab"/>
  <xsl:choose>
    <xsl:when test="methodname">
      <xsl:apply-templates mode="db2html.class.python.mode" select="methodname"/>
    </xsl:when>
    <xsl:when test="db:methodname">
      <xsl:apply-templates mode="db2html.class.python.mode" select="db:methodname"/>
    </xsl:when>
    <xsl:when test="../self::classsynopsis[ooclass]">
      <span class="methodname">
        <xsl:value-of select="../ooclass/classname"/>
      </span>
    </xsl:when>
    <xsl:when test="../self::db:classsynopsis[db:ooclass]">
      <span class="methodname">
        <xsl:value-of select="../db:ooclass/db:classname"/>
      </span>
    </xsl:when>
  </xsl:choose>
  <xsl:text>(</xsl:text>
  <xsl:for-each select="methodparam | db:methodparam">
    <xsl:if test="position() != 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
  </xsl:for-each>
  <xsl:text>)</xsl:text>
  <xsl:if test="type or db:type">
    <xsl:text> -&gt; </xsl:text>
    <xsl:apply-templates mode="db2html.class.python.mode" select="type | db:type"/>
  </xsl:if>
  <xsl:text>&#x000A;</xsl:text>
</xsl:template>

<!-- = destructorsynopsis % db2html.class.python.mode = -->
<xsl:template mode="db2html.class.python.mode"
              match="destructorsynopsis | db:destructorsynopsis">
  <!-- destructorsynopsis = element destructorsynopsis {
         attribute language { ... }?,
         modifier+,
         methodname?,
         (methodparam+ | void?)
       }
  -->
  <xsl:variable name="tab">
    <xsl:if test="../self::classsynopsis or ../self::db:classsynopsis">
      <xsl:value-of select="$db2html.classsynopsis.tab"/>
    </xsl:if>
  </xsl:variable>
  <xsl:for-each select="modifier | db:modifier">
    <xsl:value-of select="$tab"/>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
    <xsl:text>&#x000A;</xsl:text>
  </xsl:for-each>
  <xsl:value-of select="$tab"/>
  <xsl:choose>
    <xsl:when test="methodname">
      <xsl:apply-templates mode="db2html.class.python.mode" select="methodname"/>
    </xsl:when>
    <xsl:when test="db:methodname">
      <xsl:apply-templates mode="db2html.class.python.mode" select="db:methodname"/>
    </xsl:when>
    <xsl:otherwise>
      <span class="methodname">
        <xsl:text>__del__</xsl:text>
      </span>
    </xsl:otherwise>
  </xsl:choose>
  <xsl:text>(</xsl:text>
  <xsl:for-each select="methodparam | db:methodparam">
    <xsl:if test="position() != 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
  </xsl:for-each>
  <xsl:text>)</xsl:text>
  <xsl:if test="type or db:type">
    <xsl:text> -&gt; </xsl:text>
    <xsl:apply-templates mode="db2html.class.python.mode" select="type | db:type"/>
  </xsl:if>
  <xsl:text>&#x000A;</xsl:text>
</xsl:template>

<!-- = fieldsynopsis % db2html.class.python.mode = -->
<xsl:template mode="db2html.class.python.mode"
              match="fieldsynopsis | db:fieldsynopsis">
  <!-- fieldsynopsis = element fieldsynopsis {
         attribute language { ... }?,
         modifier+,
         type,
         varname,
         initializer?
       }
  -->
  <xsl:variable name="tab">
    <xsl:if test="../self::classsynopsis or ../self::db:classsynopsis">
      <xsl:value-of select="$db2html.classsynopsis.tab"/>
    </xsl:if>
  </xsl:variable>
  <xsl:for-each select="modifier | db:modifier">
    <xsl:value-of select="$tab"/>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
    <xsl:text>&#x000A;</xsl:text>
  </xsl:for-each>
  <xsl:value-of select="$tab"/>
  <xsl:apply-templates mode="db2html.class.python.mode"
                       select="varname | db:varname"/>
  <xsl:if test="initializer or db:initializer">
    <xsl:text>=</xsl:text>
    <xsl:apply-templates mode="db2html.class.python.mode"
                         select="initializer | db:initializer"/>
  </xsl:if>
  <xsl:text>&#x000A;</xsl:text>
</xsl:template>

<!-- = methodparam % db2html.class.python.mode = -->
<xsl:template mode="db2html.class.python.mode"
              match="methodparam | db:methodparam">
  <span class="methodparam">
    <xsl:apply-templates mode="db2html.class.python.mode"
                         select="parameter | db:parameter"/>
    <xsl:if test="modifier or type or db:modifier or db:type">
      <xsl:text>: </xsl:text>
      <xsl:apply-templates mode="db2html.class.python.mode"
                           select="(modifier | type | db:modifier | db:type)[1]"/>
      <xsl:if test="initializer or db:initializer">
        <xsl:text> </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:if test="initializer or db:initializer">
      <xsl:text>=</xsl:text>
      <xsl:if test="modifier or type or db:modifier or db:type">
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates mode="db2html.class.python.mode"
                           select="initializer | db:initializer"/>
    </xsl:if>
  </span>
</xsl:template>

<!-- = methodsynopsis % db2html.class.python.mode = -->
<xsl:template mode="db2html.class.python.mode"
              match="methodsynopsis | db:methodsynopsis">
  <!-- methodsynopsis = element methodsynopsis {
         attribute language { ... }?,
         modifier+,
         (type | void),
         methodname,
         (methodparam+ | void?)
       }
  -->
  <xsl:variable name="tab">
    <xsl:if test="../self::classsynopsis or ../self::db:classsynopsis">
      <xsl:value-of select="$db2html.classsynopsis.tab"/>
    </xsl:if>
  </xsl:variable>
  <xsl:for-each select="modifier | db:modifier">
    <xsl:value-of select="$tab"/>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
    <xsl:text>&#x000A;</xsl:text>
  </xsl:for-each>
  <xsl:value-of select="$tab"/>
  <xsl:text>def </xsl:text>
  <xsl:apply-templates mode="db2html.class.python.mode"
                       select="methodname | db:methodname"/>
  <xsl:text>(</xsl:text>
  <xsl:for-each select="methodparam | db:methodparam">
    <xsl:if test="position() != 1">
      <xsl:text>, </xsl:text>
    </xsl:if>
    <xsl:apply-templates mode="db2html.class.python.mode" select="."/>
  </xsl:for-each>
  <xsl:text>)</xsl:text>
  <xsl:if test="type or db:type">
    <xsl:text> -&gt; </xsl:text>
    <xsl:apply-templates mode="db2html.class.python.mode" select="type | db:type"/>
  </xsl:if>
  <xsl:text>&#x000A;</xsl:text>
</xsl:template>

</xsl:stylesheet>
