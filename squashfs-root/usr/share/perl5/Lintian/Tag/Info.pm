# -*- perl -*-
# Lintian::Tag::Info -- interface to tag metadata

# Copyright (C) 1998 Christian Schwarz and Richard Braakman
# Copyright (C) 2009 Russ Allbery
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

package Lintian::Tag::Info;

use strict;
use warnings;

use Carp qw(croak);

use Lintian::Data;
use Lintian::Tag::TextUtil
  qw(dtml_to_html dtml_to_text split_paragraphs wrap_paragraphs);
use Lintian::Tags qw();

# The URL to a web man page service.  NAME is replaced by the man page
# name and SECTION with the section to form a valid URL.  This is used
# when formatting references to manual pages into HTML to provide a link
# to the manual page.
our $MANURL
  = 'https://manpages.debian.org/cgi-bin/man.cgi?query=NAME&amp;sektion=SECTION';

# Stores the parsed manual reference data.  Loaded the first time info()
# is called.
our $MANUALS
  = Lintian::Data->new('output/manual-references', qr/::/,\&_load_manual_data);

# Map severity/certainty levels to tag codes.
our %CODES = (
    classification => { 'wild-guess' => 'C', possible => 'C', certain => 'C' },
    pedantic  => { 'wild-guess' => 'P', possible => 'P', certain => 'P' },
    wishlist  => { 'wild-guess' => 'I', possible => 'I', certain => 'I' },
    minor     => { 'wild-guess' => 'I', possible => 'I', certain => 'W' },
    normal    => { 'wild-guess' => 'I', possible => 'W', certain => 'W' },
    important => { 'wild-guess' => 'W', possible => 'E', certain => 'E' },
    serious   => { 'wild-guess' => 'E', possible => 'E', certain => 'E' },
);

=head1 NAME

Lintian::Tag::Info - Lintian interface to tag metadata

=head1 SYNOPSIS

    my $cs = Lintian::CheckScript->new ("$ENV{'LINTIAN_ROOT'}/checks/",
                                        'files');
    my $tag_info = $cs->get_tag ('some-tag');
    print "Tag info is:\n";
    print $tag_info->description('text', '   ');
    print "\nTag info in HTML is:\n";
    print $tag_info->description('html', '   ');

=head1 DESCRIPTION

This module provides an interface to tag metadata as gleaned from the
*.desc files describing the checks.  It can be used to retrieve specific
metadata elements or to format the tag description.

=head1 CLASS METHODS

=over 4

=item new(HASH, SCRIPT_NAME, SCRIPT_TYPE)

Creates a new Lintian::Tag:Info.

=cut

sub new {
    my ($class, $tag, $sn, $st) = @_;
    my %copy;
    my $self;
    my $tagname;
    croak 'no tag specified' unless $tag;
    %copy = %$tag;
    $self = \%copy;
    croak 'Missing Tag field' unless $self->{'tag'};
    $tagname = $self->{'tag'};
    croak "Missing Severity field for $tagname" unless $self->{'severity'};
    croak "Missing Certainty field for $tagname" unless $self->{'certainty'};
    croak "Tag $tagname has invalid severity ($self->{'severity'}):"
      . ' Must be one of '
      . join(', ', @Lintian::Tags::SEVERITIES)
      unless exists $CODES{$self->{'severity'}};
    croak "Tag $tagname has invalid certainty ($self->{'certainty'}):"
      . ' Must be one of '
      . join(', ', @Lintian::Tags::CERTAINTIES)
      unless exists $CODES{$self->{'severity'}}{$self->{'certainty'}};
    $self->{'info'} = '' unless $self->{'info'};
    $self->{'script'} = $sn;
    $self->{'script-type'} = $st;
    $self->{'effective-severity'} = $self->{severity};

    bless $self, $class;

    return $self;
}

=back

=head1 INSTANCE METHODS

=over 4

=item certainty()

Returns the certainty of the tag.

=cut

sub certainty {
    my ($self) = @_;
    return $self->{certainty};
}

=item code()

Returns the one-letter code for the tag.  This will be a letter chosen
from C<E>, C<W>, C<I>, or C<P>, based on the tag severity, certainty, and
other attributes (such as whether experimental is set).  This code will
never be C<O> or C<X>; overrides and experimental tags are handled
separately.

=cut

sub code {
    my ($self) = @_;
    return $CODES{$self->{'effective-severity'}}{$self->{certainty}};
}

=item description([FORMAT [, INDENT]])

Returns the formatted description (the Info field) for a tag.  FORMAT must
be either C<text> or C<html> and defaults to C<text> if no format is
specified.  If C<text>, returns wrapped paragraphs formatted in plain text
with a right margin matching the Text::Wrap default, preserving as
verbatim paragraphs that begin with whitespace.  If C<html>, return
paragraphs formatted in HTML.

If INDENT is specified, the string INDENT is prepended to each line of the
formatted output.

=cut

# Parse manual reference data from the data file.
sub _load_manual_data {
    my ($key, $rawvalue, $pval) = @_;
    my ($section, $title, $url) = split m/::/, $rawvalue, 3;
    my $ret;
    if (not defined $pval) {
        $ret = $pval = {};
    }
    $pval->{$section}{title} = $title;
    $pval->{$section}{url} = $url;
    return $ret;
}

# Format a reference to a manual in the HTML that Lintian uses internally
# for tag descriptions and return the result.  Takes the name of the
# manual and the name of the section.  Returns an empty string if the
# argument isn't a known manual.
sub _manual_reference {
    my ($manual, $section) = @_;
    return '' unless $MANUALS->known($manual);

    my $man = $MANUALS->value($manual);
    # Start with the reference to the overall manual.
    my $title = $man->{''}{title};
    my $url   = $man->{''}{url};
    my $text  = $url ? qq(<a href="$url">$title</a>) : $title;

    # Add the section information, if present, and a direct link to that
    # section of the manual where possible.
    if ($section and $section =~ /^[A-Z]+$/) {
        $text .= " appendix $section";
    } elsif ($section and $section =~ /^\d+$/) {
        $text .= " chapter $section";
    } elsif ($section and $section =~ /^[A-Z\d.]+$/) {
        $text .= " section $section";
    }
    if ($section and exists $man->{$section}) {
        my $sec_title = $man->{$section}{title};
        my $sec_url   = $man->{$section}{url};
        $text.=
          $sec_url
          ? qq[ (<a href="$sec_url">$sec_title</a>)]
          : qq[ ($sec_title)];
    }

    return $text;
}

# Format the contents of the Ref attribute of a tag.  Handles manual
# references in the form <keyword> <section>, manpage references in the
# form <manpage>(<section>), and URLs.
sub _format_reference {
    my ($field) = @_;
    my @refs;
    for my $ref (split(/,\s*/, $field)) {
        my $text;
        if ($ref =~ /^([\w-]+)\s+(.+)$/) {
            $text = _manual_reference($1, $2);
        } elsif ($ref =~ /^([\w.-]+)\((\d\w*)\)$/) {
            my ($name, $section) = ($1, $2);
            my $url = $MANURL;
            $url =~ s/NAME/$name/g;
            $url =~ s/SECTION/$section/g;
            $text = qq(the <a href="$url">$ref</a> manual page);
        } elsif ($ref =~ m,^(ftp|https?)://,) {
            $text = qq(<a href="$ref">$ref</a>);
        } elsif ($ref =~ m,^/,) {
            $text = qq(<a href="file://$ref">$ref</a>);
        } elsif ($ref =~ m,^#(\d+)$,) {
            my $url = qq(https://bugs.debian.org/$1);
            $text = qq(<a href="$url">$url</a>);
        }
        push(@refs, $text) if $text;
    }

    # Now build an English list of the results with appropriate commas and
    # conjunctions.
    my $text = '';
    if ($#refs >= 2) {
        $text = join(', ', splice(@refs, 0, $#refs));
        $text = "Refer to $text, and @refs for details.";
    } elsif ($#refs >= 0) {
        $text = 'Refer to ' . join(' and ', @refs) . ' for details.';
    }
    return $text;
}

# Returns the formatted tag description.
sub description {
    my ($self, $format, $indent) = @_;
    $indent = '' unless defined($indent);
    $format = 'text' unless defined($format);
    if ($format ne 'text' and $format ne 'html') {
        croak("unknown output format $format");
    }

    # Build the tag description.
    my $info = $self->{info};
    $info =~ s/\n[ \t]/\n/g;
    my @text = split_paragraphs($info);
    my $severity = $self->severity;
    my $certainty = $self->certainty;

    if ($self->{ref}) {
        push(@text, '', _format_reference($self->{ref}));
    }
    push(@text, '', "Severity: $severity, Certainty: $certainty");
    if ($self->{script} and $self->{'script-type'}){
        my $script = $self->{script};
        my $stype = $self->{'script-type'};
        push(@text, '', "Check: $script, Type: $stype");
    }
    if ($self->experimental) {
        push(@text,
            '',
            'This tag is marked experimental, which means that the code that'
              . ' generates it is not as well-tested as the rest of Lintian'
              . ' and might still give surprising results.  Feel free to'
              . ' ignore experimental tags that do not seem to make sense,'
              . ' though of course bug reports are always welcome.');
    }
    if ($severity eq 'classification') {
        push(@text,
            '',
            'This tag intended as a classification'
              . '  and is <i>not</i> an issue in the package.');
    }

    # Format and return the output.
    if ($format eq 'text') {
        return wrap_paragraphs($indent, dtml_to_text(@text));
    } elsif ($format eq 'html') {
        return wrap_paragraphs('HTML', $indent, dtml_to_html(@text));
    }
}

=item experimental()

Returns true if this tag is experimental, false otherwise.

=cut

sub experimental {
    my ($self) = @_;
    return ($self->{experimental} and $self->{experimental} eq 'yes');
}

=item severity([$real])

Returns the severity of the tag; if $real is a truth value
the real (original) severity is returned, otherwise the
effective severity is returned.

See set_severity()

=cut

sub severity {
    my ($self, $real) = @_;
    return $self->{'effective-severity'} unless $real;
    return $self->{severity};
}

=item set_severity($severity)

Modifies the effective severity of the tag.

=cut

sub set_severity{
    my ($self, $sev) = @_;
    croak "Unknown severity $sev" unless exists $CODES{$sev};
    $self->{'effective-severity'} = $sev;
    return;
}

=item script()

Returns the check script corresponding to this tag.

=cut

sub script {
    my ($self) = @_;
    return $self->{script};
}

=item sources()

Returns, as a list, the keywords for the sources of this tag from the
references header.  This is only the top-level source, not any
more-specific section or chapter.

=cut

sub sources {
    my ($self) = @_;
    return unless $self->{ref};
    my @refs = split(',', $self->{ref});
    @refs = map { s/^([\w-]+)\s.*/$1/; s/\(\S+\)$//; $_ } @refs;
    return @refs;
}

=item tag()

Returns the tag name.

=cut

sub tag {
    my ($self) = @_;
    return $self->{tag};
}

=back

=head1 DIAGNOSTICS

The following exceptions may be thrown:

=over 4

=item no tag specified

The Lintian::Tag::Info::new constructor was called without passing a tag
as an argument.

=item unknown output format %s

An unknown output format was passed as the FORMAT argument of
description().  FORMAT must be either C<text> or C<html>.

=back

The following fatal internal errors may be reported:

=over 4

=item can't open %s: %s

The specified file, which should be part of the standard Lintian data
files, could not be opened.  The file may be missing or have the wrong
permissions.

=item missing Check-Script field in %s

The specified check description file has no Check-Script field in its
header section.  This probably indicates the file doesn't exist or has
some significant formatting error.

=item missing Tag field in %s

The specified check description file has a tag section that has no Tag
field.

=back

=head1 FILES

=over 4

=item LINTIAN_ROOT/checks/*.desc

The tag description files, from which tag metadata is read.  All files
matching this shell glob expression will be read looking for tag data.

=item LINTIAN_ROOT/data/output/manual-references

Information about manual references.  Each non-comment, non-empty line of
this file contains four fields separated by C<::>.  The first field is the
name of the manual, the second field is the section or empty for data
about the whole manual, the third field is the title, and the fourth field
is the URL.  The URL is optional.

=back

=head1 ENVIRONMENT

=over 4

=item LINTIAN_ROOT

This variable specifies Lintian's root directory.  It defaults to
F</usr/share/lintian> if not set.  The B<lintian> program normally takes
care of setting it.

=back

=head1 AUTHOR

Originally written by Russ Allbery <rra@debian.org> for Lintian.

=head1 SEE ALSO

lintian(1)

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
