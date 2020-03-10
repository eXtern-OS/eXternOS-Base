#
# Copyright (c) 2011 by the cairo perl team (see the file README)
#
# Licensed under the LGPL, see LICENSE file for more information.
#
# $Id$
#

package Cairo::GObject;

use strict;
use warnings;

use Cairo;
use Glib;

use XSLoader;

our $VERSION = '1.004';
XSLoader::load ('Cairo::GObject', $VERSION);

1;

__END__

=head1 NAME

Cairo::GObject - Integrate Cairo into the Glib type system

=head1 SYNOPSIS

  use Cairo::GObject;

  # Cairo and Glib are now loaded and the Cairo types are registed with
  # Glib's type machinery.  This allows you to correctly use Cairo types
  # in signals and properties.

=head1 ABSTRACT

Cairo::GObject registers Cairo's types (C<Cairo::Context>, C<Cairo::Surface>,
etc.) with Glib's type systems so that they can be used normally in signals and
properties.  If you have encountered an error akin to this:

  GType CairoContext (15497280) is not registered with gperl

-- then you need to use Cairo::GObject.

=head1 AUTHORS

=over

=item Torsten Schoenfeld E<lt>kaffeetisch at gmx dot deE<gt>

=back

=head1 COPYRIGHT

Copyright (C) 2011 by the cairo perl team

=cut
