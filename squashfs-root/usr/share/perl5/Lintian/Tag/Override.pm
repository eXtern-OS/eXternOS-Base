# -*- perl -*-
# Lintian::Tag::Override -- Interface to Lintian overrides

# Copyright (C) 2011 Niels Thykier
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

package Lintian::Tag::Override;

use strict;
use warnings;

use parent qw(Class::Accessor::Fast);
use Lintian::Data;

=head1 NAME

Lintian::Tag::Override -- Representation of a Lintian Override

=head1 SYNOPSIS

 use Lintian::Tag::Override;
 
 my $data = {
    'comments' => ['some', 'multi-line', 'comments']
 };
 my $override = Lintian::Tag::Override->new('unused-override', $data);
 my $comments = $override->comments;
 if ($override->overrides("some extra") ) {
     # do something
 }

=head1 DESCRIPTION

Represents a Lintian Override.

=head1 METHODS

=over 4

=item Lintian::Tag::Override->new($tag, $data)

Creates a new override for $tag.  $data should be a hashref with the
following fields.

=over 4

=item arch

Architectures this override applies too (not really used).

=item comments

A list of comments (each item is a separate line)

=item extra

The extra part of the override.  If it contains a "*" is will
considered a pattern.

=back

=cut

# renamed tag list
my $RENAMED_TAGS = Lintian::Data->new('override/renamed-tags',qr/\s*=>\s*/);

sub new {
    my ($type, $tag, $data) = @_;
    $data = {} unless defined $data;

    if($RENAMED_TAGS->known($tag)) {
        $tag = $RENAMED_TAGS->value($tag);
    }

    my $self = {
        'arch'     => $data->{'arch'},
        'comments' => $data->{'comments'},
        'extra'    => $data->{'extra'}//'',
        'tag'      => $tag,
    };
    $self->{'arch'} = 'any' unless $self->{'arch'};
    bless $self, $type;
    $self->_init;
    return $self;
}

=item $override->tag

Returns the name of the tag.

=item $override->arch

Returns the architecture this tag applies to.

=item $override->comments

Returns a list of lines that makes up the comments for this override.

Do not modify the contents of this list.

=item $override->extra

Returns the extra of this tag (or the empty string, if there is no
extra).

=item $override->is_pattern

Returns a truth value if the extra is a pattern.

=cut

Lintian::Tag::Override->mk_ro_accessors(
    qw(tag arch comments extra is_pattern));

=item $override->overrides($extra)

Returns a truth value if this override applies to this extra.

=cut

sub overrides {
    my ($self, $textra) = @_;
    my $extra = $self->{'extra'}//'';
    # No extra => applies to all tags
    return 1 unless $extra;
    return 1 if $extra eq $textra;
    if ($self->{'is_pattern'}) {
        my $pat = $self->{'pattern'};
        if ($textra =~ m/^$pat\z/){
            return 1;
        }
    }
    return 0;
}

# Internal initialization method
sub _init  {
    my ($self) = @_;
    my $extra = $self->{'extra'};
    if ($extra && $extra =~ m/\*/o) {
        # It is a pattern, pre-compute it
        my $pattern = $extra;
        my $end = ''; # Trailing "match anything" (if any)
        my $pat = ''; # The rest of the pattern
        # Split does not help us if $pattern ends with *
        # so we deal with that now
        if ($pattern =~ s/\Q*\E+\z//o){
            $end = '.*';
        }
        # Are there any * left (after the above)?
        if ($pattern =~ m/\Q*\E/o) {
            # this works even if $text starts with a *, since
            # that is split as '', <text>
            my @pargs = split(m/\Q*\E++/o, $pattern);
            $pat = join('.*', map { quotemeta($_) } @pargs);
        } else {
            $pat = $pattern;
        }
        $self->{'is_pattern'} = 1;
        $self->{'pattern'} = qr/$pat$end/;
    } else {
        $self->{'is_pattern'} = 0;
    }
    return;
}

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1)

L<Lintian::Tags>

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
