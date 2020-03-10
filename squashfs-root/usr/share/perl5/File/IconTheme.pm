package File::IconTheme;
use strict;
use warnings FATAL => 'all';
use File::BaseDir qw(data_dirs);
require File::Spec;
use parent qw(Exporter);

our $VERSION   = '0.07';
our @EXPORT_OK = qw(xdg_icon_theme_search_dirs);

sub xdg_icon_theme_search_dirs {
    return grep {-d $_ && -r $_}
        File::Spec->catfile($ENV{HOME}, '.icons'),
        data_dirs('icons'),
        '/usr/share/pixmaps';
}

1;

__END__

=head1 NAME

File::IconTheme - find icon directories

=head1 VERSION

This document describes File::IconTheme.

=head1 SYNOPSIS

    use File::IconTheme qw(xdg_icon_theme_search_dirs);
    print join "\n", xdg_icon_theme_search_dirs;

=head1 DESCRIPTION

This module can be used to find directories as specified
by the Freedesktop.org Icon Theme Specification. Currently only a tiny
(but most useful) part of the specification is implemented.

In case you want to B<store> an icon theme, use the directory returned by:

    use File::BaseDir qw(data_dirs);
    print scalar data_dirs('icons');

=head1 INTERFACE

=over

=item C<xdg_icon_theme_search_dirs>

Returns a list of the base directories of icon themes.

=back

=head1 EXPORTS

None by default, but the method can be exported on demand.

=head1 CONFIGURATION AND ENVIRONMENT

C<$XDG_DATA_HOME>, C<$XDG_DATA_DIRS>

=head1 SEE ALSO

L<http://standards.freedesktop.org/icon-theme-spec/>
