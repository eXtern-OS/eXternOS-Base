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
                exclude-result-prefixes="db"
                version="1.0">

<!--
If you add a template to this stylesheet, put it under an appropriate header
that states why this element is suppressed.  Some elements are simply not
supported, while other elements are expected only to be processed in certain
modes because of the DocBook content model.
-->

<!-- Not rendered directly -->
<xsl:template match="subtitle | db:subtitle"/>
<xsl:template match="titleabbrev | db:titleabbrev"/>

<!-- Not yet supported -->
<xsl:template match="remark | db:remark"/>

<!-- Suppressed by processing expectations -->
<xsl:template match="screeninfo | db:screeninfo"/>

<!-- Not supported -->
<xsl:template match="alt | db:alt"/>
<xsl:template match="beginpage"/>
<xsl:template match="bibliocoverage | db:bibliocoverage"/>

<!-- Explicitly matched by parent -->
<xsl:template match="listitem | db:listitem"/>
<xsl:template match="sbr | db:sbr"/>

<!-- Index elements, not yet supported -->
<xsl:template match="indexterm | db:indexterm"/>
<xsl:template match="primary | db:primary"/>
<xsl:template match="primaryie | db:primaryie"/>
<xsl:template match="secondary | db:secondary"/>
<xsl:template match="secondaryie | db:secondaryie"/>
<xsl:template match="see | db:see"/>
<xsl:template match="seeie | db:seeie"/>
<xsl:template match="seealso | db:seealso"/>
<xsl:template match="seealsoie | db:seealsoie"/>
<xsl:template match="tertiary | db:tertiary"/>
<xsl:template match="tertiaryie | db:tertiaryie"/>

<!-- Unmatched info elements, supported indirectly -->
<xsl:template match="appendixinfo | db:appendix/db:info"/>
<xsl:template match="blockinfo |
                     db:info[not(contains(local-name(..), 'object'))]"/>
<xsl:template match="articleinfo | db:article/db:info"/>
<xsl:template match="bibliographyinfo | db:bibliography/db:info"/>
<xsl:template match="bookinfo | db:book/db:info"/>
<xsl:template match="chapterinfo | db:chapter/db:info"/>
<xsl:template match="glossaryinfo | db:glossary/db:info"/>
<xsl:template match="partinfo | db:part/db:info"/>
<xsl:template match="prefaceinfo | db:preface/db:info"/>
<xsl:template match="refentryinfo | db:refentry/db:info"/>
<xsl:template match="referenceinfo | db:reference/db:info"/>
<xsl:template match="refmeta | db:refmeta"/>
<xsl:template match="refmiscinfo | db:refmiscinfo"/>
<xsl:template match="refsynopsisdivinfo | db:refsynopsisdiv/db:info"/>
<xsl:template match="sect1info | db:sect1/db:info"/>
<xsl:template match="sect2info | db:sect2/db:info"/>
<xsl:template match="sect3info | db:sect3/db:info"/>
<xsl:template match="sect4info | db:sect4/db:info"/>
<xsl:template match="sect5info | db:sect5/db:info"/>
<xsl:template match="sectioninfo | db:section/db:info"/>

<!-- Handled specially, so we can apply-templates -->
<xsl:template match="label | db:label"/>

</xsl:stylesheet>
