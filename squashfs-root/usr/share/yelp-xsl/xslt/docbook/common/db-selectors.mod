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

<!--
This file contains a set of selectors for DocBook content. The selectors reflect
the logical groupings used by the yelp-xsl stylesheets, and may not be suitable
for other uses. The selectors are all of the form *[predicate]. This allows axes
to be prepended and predicates to be appended.
-->

<!-- ===========================================================================
db_chunks
-->
<!ENTITY db_chunks "*[
local-name(.) = 'appendix' or
local-name(.) = 'article' or
local-name(.) = 'bibliography' or
local-name(.) = 'bibliodiv' or
local-name(.) = 'book' or
local-name(.) = 'chapter' or
local-name(.) = 'colophon' or
local-name(.) = 'dedication' or
local-name(.) = 'glossary' or
local-name(.) = 'glossdiv' or
local-name(.) = 'index' or
local-name(.) = 'lot' or
local-name(.) = 'part' or
local-name(.) = 'preface' or
local-name(.) = 'refentry' or
local-name(.) = 'reference' or
local-name(.) = 'sect1' or
local-name(.) = 'sect2' or
local-name(.) = 'sect3' or
local-name(.) = 'sect4' or
local-name(.) = 'sect5' or
local-name(.) = 'section' or
local-name(.) = 'setindex' or
local-name(.) = 'simplesect' or
local-name(.) = 'toc'
]">
