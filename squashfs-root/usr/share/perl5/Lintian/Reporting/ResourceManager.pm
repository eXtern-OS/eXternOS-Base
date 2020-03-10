# Copyright (C) 2014 Niels Thykier <niels@thykier.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, you can find it on the World Wide
# Web at http://www.gnu.org/copyleft/gpl.html, or write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston,
# MA 02110-1301, USA.

# A simple resource manager for html_reports
package Lintian::Reporting::ResourceManager;

use strict;
use warnings;
use autodie;

use Carp qw(croak);
use File::Basename qw(basename);
use File::Copy qw(copy);

use Lintian::Util qw(get_file_digest);

=head1 NAME

Lintian::Reporting::ResourceManager -- A simple resource manager for html_reports

=head1 SYNOPSIS

 use Lintian::Reporting::ResourceManager;
 
 my $resMan = Lintian::Reporting::ResourceManager->new(
    'html_dir' => 'path/to/HTML-root',
 );
 # Copy the resource
 $resMan->install_resource('path/to/my-image.png', { install_method => 'copy'} );
 # Move the resource
 $resMan->install_resource('path/to/generated-styles.css');
 print 'Image: ' . $resMan->resource_URL('my-image.png'), "\n";
 print 'CSS: ' . $resMan->resource_URL('generated-styles.css'), "\n";

=head1 DESCRIPTION

A simple resource manager for Lintian's reporting tool,
B<html_reports>.


=head1 CLASS METHODS

=over 4

=item new(TYPE, OPTS)

Instantiates a new resource manager.

OPTS is a key-value list, which must contain the key "html_dir" set to
the root of the HTML path.  It is beneath this path that all resources
will be installed

=cut

sub new {
    my ($class, %opts) = @_;
    my $self = {%opts,};
    croak('Missing required parameter html_dir (or it is undef)')
      if not defined $opts{'html_dir'};
    $self->{'_resource_cache'} = {};
    $self->{'_resource_integrity'} = {};
    return bless($self, $class);
}

=back

=head1 INSTANCE METHODS

=over 4

=item install_resource(RESOURCE[, OPT])

Installs RESOURCE into the html root.  The resource may be renamed
(based on content etc.).

Note that the basename of RESOURCE must be unique between all
resources installed.  See L</resource_URL(RESOURCE_NAME)>.

If OPT is given, it must be a hashref with 0 or more of the following
keys (and values).

=over 4

=item install_method

Can be "copy" or "move" (default).  If set to "move", the original file
will be renamed into its new location.  Otherwise, a copy is done and
the original file is left in place.

=item source_file

By default, the path denoted by RESOURCE is both the resource name and
the source file.  This option can be used to install a given file as
RESOURCE regardless of the basename of the source file.

If this is passed, RESOURCE must be a basename (i.e. without any
slashes).

=back

=cut

sub install_resource {
    my ($self, $resource_name, $opt) = @_;
    my $resource_root = $self->{'html_dir'} . '/resources';
    my $method = 'move';
    my ($basename, $install_name, $resource, $digest, $b64digest);
    $method = $opt->{'install_method'}
      if $opt && exists($opt->{'install_method'});
    if ($opt && exists($opt->{'source_file'})) {
        $basename = $resource_name;
        $resource = $opt->{'source_file'};
        if (index($basename, '/') > -1) {
            croak(
                join(' ',
                    qq(Resource "${resource_name}" must not contain "/"),
                    'when source_file is given'));
        }
    } else {
        $basename = basename($resource_name);
        $resource = $resource_name;
    }
    $digest = get_file_digest('sha256', $resource);
    $install_name = $digest->clone->hexdigest;
    $b64digest = $digest->b64digest;

    while (length($b64digest) % 4) {
        $b64digest .= '=';
    }

    croak("Resource name ${basename} already in use")
      if defined($self->{'_resource_cache'}{$basename});
    if ($basename =~ m/^.+(\.[^\.]+)$/xsm) {
        my $ext = $1;
        $install_name .= $ext;
    }
    mkdir($resource_root, 0755) if not -d $resource_root;
    if ($method eq 'move') {
        rename($resource, "$resource_root/$install_name");
    } elsif ($method eq 'copy') {
        copy($resource, "$resource_root/$install_name")
          or
          croak("Cannot copy $resource to $resource_root/$install_name: $!");
    } else {
        croak(
            join(' ',
                "Unknown install method ${method}",
                '- please use "move" or "copy"'));
    }
    $self->{'_resource_cache'}{$basename} = "resources/$install_name";
    $self->{'_resource_integrity'}{$basename} = "sha256-${b64digest}";
    return;
}

=item resource_URL(RESOURCE_NAME)

Returns the path (relative to the HTML root) to a resource installed
via L</install_resource(RESOURCE)>, where RESOURCE_NAME is the
basename of the path given to install_resource.

=cut

sub resource_URL {
    my ($self, $resource_name) = @_;
    croak("Unknown resource $resource_name")
      if not defined($self->{'_resource_cache'}{$resource_name});
    return $self->{'_resource_cache'}{$resource_name};
}

=item resource_integrity_value(RESOURCE_NAME)

Return a string that is valid in the "integrity" field of a C<< <link>
>> HTML tag.  (See https://www.w3.org/TR/SRI/)

=cut

sub resource_integrity_value {
    my ($self, $resource_name) = @_;
    croak("Unknown resource $resource_name")
      if not defined($self->{'_resource_integrity'}{$resource_name});
    return $self->{'_resource_integrity'}{$resource_name};
}

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
