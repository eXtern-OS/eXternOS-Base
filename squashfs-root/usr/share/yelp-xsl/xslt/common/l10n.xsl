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
along with this program; see the file COPYING.LGPL.  If not, see
<http://www.gnu.org/licenses/>.
-->

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:msg="http://projects.gnome.org/yelp/gettext/"
                xmlns:str="http://exslt.org/strings"
                exclude-result-prefixes="msg str"
                version="1.0">

<!--!!==========================================================================
Localized Strings
Templates for translated strings, with format strings and plural forms.
:Revision:version="3.18" date="2015-07-24" status="final"

This stylesheet contains templates for getting localized strings, including
format strings and plural forms. Format strings are important for proper
localization, as constructing sentences from concatenation often produces
poor results in many languages.

By default, the templates in this stylesheet work on the translations shipped
with yelp-xsl, but the templates can be reused by yelp-xsl extensions (or even
entirely separate stylesheets) by installing XML files with the translations
under the domains subdirectory of the directory holding this file. The format
of the file is designed to work well with itstool's join mode.
-->


<!--++==========================================================================
l10n.msgstr.key
Get a translated message from an ID and a language.
:Revision:version="3.4" date="2012-01-26" status="final"

This key indexes all message translations in a message catalog file. The elements
are indexed by the concatenation of the message id, the string #{__LC__}, and the
#{xml:lang} attribute converted to lowercase.
-->
<xsl:key name="l10n.msgstr.key" match="msg:msg/msg:msgstr"
         use="concat(../@id, '__LC__',
              translate(@xml:lang,
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        'abcdefghijklmnopqrstuvwxyz'))"/>


<!--@@==========================================================================
l10n.locale
The top-level locale of the document.
:Revision:version="3.18" date="2015-08-13" status="final"

This parameter provides the top-level locale of the document, taken from either
the #{xml:lang} or the #{lang} parameter of the root element. It holds the
locale exactly as specified in the document, with no normalization.
-->
<xsl:param name="l10n.locale">
  <xsl:choose>
    <xsl:when test="/*/@xml:lang">
      <xsl:value-of select="/*/@xml:lang"/>
    </xsl:when>
    <xsl:when test="/*/@lang">
      <xsl:value-of select="/*/@lang"/>
    </xsl:when>
  </xsl:choose>
</xsl:param>


<!--**==========================================================================
l10n.gettext
Look up the translation for a string.
:Revision:version="3.18" date="2015-07-29" status="final"
$domain: The domain to look up the string in.
$msgid: The id of the string to look up, often the string in the C locale.
$lang: The locale to use when looking up the translated string.
$number: The cardinality for plural-form lookups.
$form: The form name for plural-form lookups.
$format: Whether to treat the result as a format string.
$node: A context node to pass to %{l10n.format.mode}.
$string: A string to pass to %{l10n.format.mode} for #{msg:string} elements.

This template extracts a translated version of a source string. In simple cases,
the source string is exactly the string in ${msgid}, though in more complex
cases, the ${msgid} parameter is a separate unique identifier.

This template looks up the translation in a message catalog file based on the
${domain} parameter. The file must be in a #{domains} subdirectory relative to
the directory holding this stylesheet and be named the same as ${domain} with
the suffix #{.xml}. This template will fail if no such file is found. By
default, the domain is #{yelp-xsl} to reference the translations shipped with
these stylesheets. Extensions and third-party stylesheets, however, can use
this template by installing a file and passing the ${domain} parameter.

The message catalog file format is designed to work with the XML/PO translation
tool #{itstool}, using its join mode to create a single polylingual file. There
is no tool to automatically extract messages from XSLT files. You must add
messages to the source catalog file when adding translatable strings.

The message catalog file contains a set of #{msg} elements, one for each string
that needs translation. Each #{msg} element has an #{id} attribute. It is this
attribute that is matched against the ${msgid} parameter. Each #{msg} element
then has one or more #{msgstr} elements, each with an #{xml:lang} attribute.
This template tries to find a best match language with the ${lang} parameter,
falling back to a #{msgstr} element with no #{xml:lang} attribute.

In a source message catalog file, put the string to be translated inside a
singleton #{msgstr} element in each #{msg} element, without an #{xml:lang}
parameter. Add this element even if it is the same as the #{id} attribute of
the #{msg} element. These #{msgstr} elements are what #{itstool} uses to create
a PO file, and it provides the fallback string when no language matches.

The #{xml:lang} attribute should contain an RFC 3066 language identifier, which
is different from the POSIX locale identifiers used by gettext. To accommodate
this difference, this stylesheet converts all identifiers to lowercase and
replaces the characters #{_}, #{@}, and #{.} with the character #{-}. If it
cannot find an exact match, it strips the part after the last #{-} and looks
again. It repeats this as long as the identifier contains a #{-} character.
If there is still no matching #{msgstr} element, it looks for one with no
#{xml:lang} attribute.

Sometimes you have to provide different versions of a string for different
cardinalities. While English and many other languages have singular and plural,
some languages have no plural forms, while others have as many as six. These
stylesheets use a numeric index for plural forms, similarly to gettext. To get
the string for a plural, pass the cardinality in the ${number} parameter. This
template gets an index for that number by calling *{l10n.plural.form}. The
plural form index is in the ${form} parameter. You do not have to pass this
parameter. It will be computed automatically based on the ${number} parameter.

There is currently no support for editing plural forms using the standard PO
syntax. Instead, plurals are defined with an XML snippet. Instead of putting
the single translated message in the #{msgstr} element, plural messages have
#{msgstr} child elements of the #{msgstr} element with the #{xml:lang}
attribute. Each of these child #{msgstr} elements has a #{form} attribute that
holds the numeric index returned by *{l10n.plural.form}. Translators must adapt
the XML snippet according to the plural rules and forms defined in this
stylesheet for their language.

Some translations aren't simple strings, but are instead format strings where
certain values are inserted. This template can handle format strings with XML
marker elements to signal where values should be substituted. These values
cat be the result of applying templates.

To enable format strings, pass set the ${format} parameter to #{true()}.
Instead of just returning the translated string, this template will instead
apply templates in the mode %{l10n.format.mode} to the fragment contained in
the #{msgstr} element.

The ${node} and ${string} parameters are passed to templates in
%{l10n.format.mode}. This stylesheet contains matches in %{l10n.format.mode}
for the marker elements #{<string/>} and #{<node/>}. The element #{<string/>}
will be replaced by the string value of ${string}. The element #{<node/>} will
apply templates without a mode to ${node}. Text nodes are copied to the result
in %{l10n.format.mode}.

If you need any other behavior, add elements with any name of your choosing to
the format string, then match on those elements in %{l10n.format.mode}. You will
be able to use the ${node} and ${string} parameters in your template. Try to
use a name that is unique.
-->
<xsl:template name="l10n.gettext">
  <xsl:param name="domain" select="'yelp-xsl'"/>
  <xsl:param name="msgid"/>
  <xsl:param name="lang" select="(ancestor-or-self::*[@lang][1]/@lang |
                                  ancestor-or-self::*[@xml:lang][1]/@xml:lang)
                                 [last()]"/>
  <xsl:param name="number"/>
  <xsl:param name="form">
    <xsl:if test="$number">
      <xsl:call-template name="l10n.plural.form">
        <xsl:with-param name="number" select="$number"/>
        <xsl:with-param name="lang" select="$lang"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:param>
  <xsl:param name="format" select="false()"/>
  <xsl:param name="node" select="."/>
  <xsl:param name="string"/>

  <xsl:variable name="source" select="."/>
  <xsl:variable name="normlang" select="translate($lang,
                                        '_@.ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                                        '---abcdefghijklmnopqrstuvwxyz')"/>
  <xsl:for-each select="document(concat('domains/', $domain, '.xml'))">
    <xsl:variable name="msg" select="key('l10n.msgstr.key',
                                         concat($msgid, '__LC__', $normlang))"/>
    <xsl:choose>
      <xsl:when test="$msg">
        <xsl:for-each select="$source">
          <xsl:call-template name="l10n.gettext.msg">
            <xsl:with-param name="msg" select="$msg"/>
            <xsl:with-param name="form" select="$form"/>
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="string" select="$string"/>
            <xsl:with-param name="format" select="$format"/>
          </xsl:call-template>
        </xsl:for-each>
      </xsl:when>
      <xsl:when test="contains($normlang, '-')">
        <xsl:variable name="newlang">
          <xsl:for-each select="str:split($normlang, '-')[position() != last()]">
            <xsl:if test="position() != 1">
              <xsl:text>-</xsl:text>
            </xsl:if>
            <xsl:value-of select="."/>
          </xsl:for-each>
        </xsl:variable>
        <xsl:for-each select="$source">
          <xsl:call-template name="l10n.gettext">
            <xsl:with-param name="domain" select="$domain"/>
            <xsl:with-param name="msgid" select="$msgid"/>
            <xsl:with-param name="lang" select="$newlang"/>
            <xsl:with-param name="number" select="$number"/>
            <xsl:with-param name="form" select="$form"/>
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="string" select="$string"/>
            <xsl:with-param name="format" select="$format"/>
          </xsl:call-template>
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="cmsg" select="key('l10n.msgstr.key',
                                              concat($msgid, '__LC__'))"/>
        <xsl:choose>
          <xsl:when test="$cmsg">
            <xsl:for-each select="$source">
              <xsl:call-template name="l10n.gettext.msg">
                <xsl:with-param name="msg" select="$cmsg"/>
                <xsl:with-param name="form" select="$form"/>
                <xsl:with-param name="node" select="$node"/>
                <xsl:with-param name="string" select="$string"/>
                <xsl:with-param name="format" select="$format"/>
              </xsl:call-template>
            </xsl:for-each>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$msgid"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:for-each>
</xsl:template>

<!-- FIXME: a bit of docs -->
<!--#* l10n.gettext.msg -->
<xsl:template name="l10n.gettext.msg">
  <xsl:param name="msg"/>
  <xsl:param name="form" select="''"/>
  <xsl:param name="node" select="."/>
  <xsl:param name="string"/>
  <xsl:param name="format" select="false()"/>
  <xsl:choose>
    <xsl:when test="not($msg/msg:msgstr)">
      <xsl:call-template name="l10n.gettext.msgstr">
        <xsl:with-param name="msgstr" select="$msg"/>
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="string" select="$string"/>
        <xsl:with-param name="format" select="$format"/>
      </xsl:call-template>
    </xsl:when>
    <!-- FIXME: OPTIMIZE: this needs to be faster -->
    <!-- FIXME: simplify -->
    <xsl:when test="$form != ''">
      <xsl:choose>
        <xsl:when test="$msg/msg:msgstr[@form = $form]">
          <xsl:call-template name="l10n.gettext.msgstr">
            <xsl:with-param name="msgstr"
                            select="$msg/msg:msgstr[@form = $form][1]"/>
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="string" select="$string"/>
            <xsl:with-param name="format" select="$format"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:when test="$msg/msg:msgstr[not(@form)]">
          <xsl:call-template name="l10n.gettext.msgstr">
            <xsl:with-param name="msgstr"
                            select="$msg/msg:msgstr[not(@form)][1]"/>
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="string" select="$string"/>
            <xsl:with-param name="format" select="$format"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="l10n.gettext.msgstr">
            <xsl:with-param name="msgstr" select="$msg/msg:msgstr[1]"/>
            <xsl:with-param name="node" select="$node"/>
            <xsl:with-param name="string" select="$string"/>
            <xsl:with-param name="format" select="$format"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>
    <xsl:otherwise>
      <xsl:call-template name="l10n.gettext.msgstr">
        <xsl:with-param name="msgstr" select="$msg/msg:msgstr[1]"/>
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="string" select="$string"/>
        <xsl:with-param name="format" select="$format"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<!--#* l10n.gettext.msgstr -->
<xsl:template name="l10n.gettext.msgstr">
  <xsl:param name="msgstr"/>
  <xsl:param name="node" select="."/>
  <xsl:param name="string"/>
  <xsl:param name="format" select="false()"/>
  <xsl:choose>
    <xsl:when test="$format">
      <xsl:apply-templates mode="l10n.format.mode" select="$msgstr/node()">
        <xsl:with-param name="node" select="$node"/>
        <xsl:with-param name="string" select="$string"/>
      </xsl:apply-templates>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$msgstr"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
l10n.plural.form
Extract the plural form index for a given cardinality.
:Revision: version="3.18" date="2015-07-29" status="final"
$number: The cardinality of the plural form.
$lang: The locale to use when looking up the translated string.

This template returns a numeric index of a plural form for a given language,
similarly to how indexes are used in gettext PO files. Different languages have
different rules for plurals. Some languages have no plurals at all, while others
have as many as six different forms. This plural form index is used by
*{l10n.gettext} to determine the correct string to use.

The rules in this template are hand-written. They are not taken from the PO
files. They are written by referencing the PO files in various GNOME modules,
as well as the plural rules in the Unicode CLDR.
-->
<xsl:template name="l10n.plural.form">
  <xsl:param name="number" select="1"/>
  <xsl:param name="lang" select="$l10n.locale"/>
  <xsl:variable name="normlang" select="concat(translate($lang,
                                        '_@.ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                                        '---abcdefghijklmnopqrstuvwxyz'),
                                        '-')"/>

  <xsl:choose>
    <!-- == pt_BR == -->
    <xsl:when test="starts-with($normlang, 'pt-br-')">
      <xsl:choose>
        <xsl:when test="$number &gt; 1">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>1</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == ar == -->
    <xsl:when test="starts-with($normlang, 'ar-')">
      <xsl:choose>
        <xsl:when test="$number = 1">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:when test="$number = 2">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:when test="$number &gt;= 3 and $number &lt; 10">
          <xsl:text>2</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>3</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == be bs cs ru sr uk == -->
    <xsl:when test="starts-with($normlang, 'be-') or starts-with($normlang, 'bs-') or
                    starts-with($normlang, 'cs-') or starts-with($normlang, 'ru-') or
                    starts-with($normlang, 'sr-') or starts-with($normlang, 'uk-') ">
      <xsl:choose>
        <xsl:when test="($number mod 10 = 1) and ($number mod 100 != 11)">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:when test="($number mod 10 &gt;= 2) and ($number mod 10 &lt;= 4) and
                        (($number mod 100 &lt; 10) or ($number mod 100 &gt;= 20))">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>2</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == cy == -->
    <xsl:when test="starts-with($normlang, 'cy-')">
      <xsl:choose>
        <xsl:when test="$number != 2">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>1</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == fa hu ja ko th tr vi zh == -->
    <xsl:when test="starts-with($normlang, 'ja-') or starts-with($normlang, 'ko-') or
                    starts-with($normlang, 'th-') or starts-with($normlang, 'tr-') or
                    starts-with($normlang, 'vi-') or starts-with($normlang, 'zh-') ">
      <xsl:text>0</xsl:text>
    </xsl:when>

    <!-- == fr nso wa == -->
    <xsl:when test="starts-with($normlang, 'fr-') or starts-with($normlang, 'nso-') or
                    starts-with($normlang, 'wa-') ">
      <xsl:choose>
        <xsl:when test="$number &gt; 1">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>0</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == ga == -->
    <xsl:when test="starts-with($normlang, 'ga-')">
      <xsl:choose>
        <xsl:when test="$number = 1">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:when test="$number = 2">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>2</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == sk == -->
    <xsl:when test="starts-with($normlang, 'sk-')">
      <xsl:choose>
        <xsl:when test="$number = 1">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:when test="($number &gt;= 2) and ($number &lt;= 4)">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>2</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == sl == -->
    <xsl:when test="starts-with($normlang, 'sl-')">
      <xsl:choose>
        <xsl:when test="$number mod 100 = 1">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:when test="$number mod 100 = 2">
          <xsl:text>1</xsl:text>
        </xsl:when>
        <xsl:when test="($number mod 100 = 3) or ($number mod 100 = 4)">
          <xsl:text>2</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>3</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:when>

    <!-- == C == -->
    <xsl:otherwise>
      <xsl:choose>
        <xsl:when test="$number = 1">
          <xsl:text>0</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>1</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
l10n.direction
Determine the text direction for a language.
:Revision: version="3.18" date="2015-08-13" status="final"
$lang: The locale to use to determine the text direction.

This template returns the text direction for the language ${lang}. It returns
#{"ltr"} for left-to-right languages and #{"rtl"} for right-to-left languages.
If ${lang} is not provided, it defaults to ${l10n.locale}, the top-level locale
of the document.

This template calls *{l10n.gettext} with the string #{default:LTR} in the domain
#{yelp-xsl}. The language is right-to-left if the string #{default:RTL} is
returned. Otherwise, it is left-to-right. (This particular string is used to
match the string used in GTK+, enabling translation memory.)
-->
<xsl:template name="l10n.direction">
  <xsl:param name="lang" select="$l10n.locale"/>
  <xsl:variable name="direction">
    <xsl:for-each select="/*">
      <xsl:call-template name="l10n.gettext">
        <xsl:with-param name="msgid" select="'default:LTR'"/>
        <xsl:with-param name="lang" select="$lang"/>
      </xsl:call-template>
    </xsl:for-each>
  </xsl:variable>
  <xsl:choose>
    <xsl:when test="$direction = 'default:RTL'">
      <xsl:text>rtl</xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>ltr</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
l10n.align.start
Determine the start alignment.
:Revision: version="3.18" date="2015-07-27" status="final"
$direction: The text direction.

This template returns the string #{left} for left-to-right languages and the
string #{right} for right-to-left languages. The result is suitable for
substituting in CSS rules that are direction-dependent. If you do not pass
the ${direction} parameter, it defaults to calling *{l10n.direction} using
the default locale defined in @{l10n.locale}.
-->
<xsl:template name="l10n.align.start">
  <xsl:param name="direction">
    <xsl:call-template name="l10n.direction"/>
  </xsl:param>
  <xsl:choose>
    <xsl:when test="$direction = 'rtl'">
      <xsl:text>right</xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>left</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--**==========================================================================
l10n.align.end
Determine the end alignment.
:Revision: version="3.18" date="2015-07-27" status="final"
$direction: The text direction.

This template returns the string #{right} for left-to-right languages and the
string #{left} for right-to-left languages. The result is suitable for
substituting in CSS rules that are direction-dependent. If you do not pass
the ${direction} parameter, it defaults to calling *{l10n.direction} using
the default locale defined in @{l10n.locale}.
-->
<xsl:template name="l10n.align.end">
  <xsl:param name="direction">
    <xsl:call-template name="l10n.direction"/>
  </xsl:param>
  <xsl:choose>
    <xsl:when test="$direction = 'rtl'">
      <xsl:text>left</xsl:text>
    </xsl:when>
    <xsl:otherwise>
      <xsl:text>right</xsl:text>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!--%%==========================================================================
l10n.format.mode
Process format strings from *{l10n.gettext}.
:Revision: version="3.18" date="2015-08-13" status="final"
$node: The node being processed in the original document.
$string: String content to use for certain message format nodes.

This mode is called by *{l10n.gettext} when its #{format} parameter is set to
true. It is applied to the elements and text children of the translated message
that *{l10n.gettext} finds. This allows you to insert content in format strings,
rather than concatenating multiple translations to create a translated message.

By default, this stylesheet provides matching templates in this mode for the
elements #{node} and #{string}. The template for #{node} applies templates with
no mode to the ${node} parameters passed to *{l10n.gettext}. The template for
#{string} copies the text in the ${string} parameter passed to *{l10n.gettext}.
Both parameters are passed to templates in this mode. Templates matching this
mode should pass those parameters to child content if they process child
content in %{l10n.format.mode}.

To use format strings in your own translations, use elements with names of
your choosing in your message. You can use the #{node} and #{string} elements
without further implementation, if they fit your needs. Otherwise, take care
to use element names that are unlikely to conflict with other templates using
this mode.
-->
<xsl:template mode="l10n.format.mode" match="*">
  <xsl:param name="node"/>
  <xsl:apply-templates mode="l10n.format.mode">
    <xsl:with-param name="node" select="$node"/>
  </xsl:apply-templates>
</xsl:template>

<!-- = l10n.format.mode % msg:node = -->
<xsl:template mode="l10n.format.mode" match="msg:node">
  <xsl:param name="node"/>
  <xsl:apply-templates select="$node/node()"/>
</xsl:template>

<!-- = l10n.format.mode % msg:string = -->
<xsl:template mode="l10n.format.mode" match="msg:string">
  <xsl:param name="string"/>
  <xsl:value-of select="$string"/>
</xsl:template>

</xsl:stylesheet>
