# Copyright (C) 2011 Niels Thykier <niels@thykier.net>
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

## Represents a Lintian profile
package Lintian::Profile;

use parent qw(Class::Accessor::Fast);

use strict;
use warnings;
use autodie qw(opendir closedir);

use Carp qw(croak);

use Dpkg::Vendor qw(get_current_vendor get_vendor_info);

use Lintian::CheckScript;
use Lintian::Tags;
use Lintian::Util qw(parse_boolean read_dpkg_control_utf8 strip);

=head1 NAME

Lintian::Profile - Profile parser for Lintian

=head1 SYNOPSIS

 # Load the debian profile (if available)
 my $profile = Lintian::Profile->new ('debian');
 # Load the debian profile using an explicit search path
 $profile = Lintian::Profile->new ('debian',
    ['/path/to/alt/root', $ENV{'LINTIAN_ROOT'}]);
 # Load the "default" profile for the current vendor
 $profile = Lintian::Profile->new;
 foreach my $tag ($profile->tags) {
     print "Enabled tag: $tag\n";
 }
 # ...

=head1 DESCRIPTION

Lintian::Profile handles finding, parsing and implementation of
Lintian Profiles as well as loading the relevant Lintian checks.

=head1 CLASS METHODS

=over 4

=cut

# map of known valid severity allowed by profiles
my %SEVERITIES = map { $_ => 1} @Lintian::Tags::SEVERITIES;

# List of fields in the main profile paragraph
my %MAIN_FIELDS = (
    'profile'                 => 1,
    'extends'                 => 1,
    'enable-tags-from-check'  => 1,
    'disable-tags-from-check' => 1,
    'enable-tags'             => 1,
    'disable-tags'            => 1,
);

# List of fields in secondary profile paragraphs
my %SEC_FIELDS = (
    'tags'        => 1,
    'overridable' => 1,
    'severity'    => 1,
);

=item Lintian::Profile->new ([$profname[, $ipath[, $extra]]])

Creates a new profile from the profile.  $profname is the name of the
profile and $ipath is a list reference containing the path
to one (or more) Lintian "roots".

If $profname is C<undef>, the default vendor will be loaded based on
Dpkg::Vendor::get_current_vendor.

If $ipath is not given, a default one will be used.

=cut

sub new {
    my ($type, $name, $ipath, $extra) = @_;
    my ($profile, @full_inc_path);
    if (!defined $ipath) {
        # Temporary fix (see _safe_include_path)
        @full_inc_path = (_default_inc_path());
        if (defined $ENV{'LINTIAN_ROOT'}) {
            $ipath = [$ENV{'LINTIAN_ROOT'}];
        } else {
            $ipath = ['/usr/share/lintian'];
        }
    }

    if (defined $extra) {
        if (exists($extra->{'restricted-search-dirs'})) {
            @full_inc_path = @{ $extra->{'restricted-search-dirs'} };
        }
    }
    push @full_inc_path, @$ipath;

    my $self = {
        'parent-map'           => {},
        'profile_list'         => [],
        'include-path'         => \@full_inc_path,
        'safe-include-path'    => $ipath,
        # "set" of tags enabled (value is largely ignored)
        'enabled-tags'         => {},
        # maps script to the number of tags enabled (0 if disabled)
        'enabled-checks'       => {},
        'non-overridable-tags' => {},
        # maps script name to Lintian::CheckScript
        'check-scripts'        => {},
        # maps tag name to Lintian::Tag::Info
        'known-tags'           => {},
    };
    $self = bless $self, $type;
    if (not defined $name) {
        ($profile, $name) = $self->_find_vendor_profile;
    } else {
        croak "Illegal profile name \"$name\""
          if $name =~ m,^/,o
          or $name =~ m/\./o;
        ($profile, undef) = $self->_find_vendor_profile($name);
    }
    croak "Cannot find profile $name (in "
      . join(', ', map { "$_/profiles" } @$ipath).')'
      unless $profile;

    # Implementation detail: Ensure that the "lintian" check is always
    # loaded to avoid "attempt to emit unknown tags" caused by
    # the frontend or L::Tags.  Also default to enabling the Lintian
    # tags as they are helpful (e.g. for debugging overrides files)
    my $c = $self->_load_check($self->name, 'lintian');
    $self->enable_tags($c->tags);

    $self->_read_profile($profile);
    return $self;
}

=item $prof->profile_list

Returns a list ref of the (normalized) names of the profile and its
parents.  The last element of the list is the name of the profile
itself, the second last is its parent and so on.

Note: This list reference and its contents should not be modified.

=item $prof->name

Returns the name of the profile, which may differ from the name used
to create this instance of the profile (e.g. due to symlinks).

=cut

Lintian::Profile->mk_ro_accessors(qw(profile_list name));

=item $prof->tags([$known])

Returns the list of tags in this profile.  If $known is given
and it is a truth value, the list of known tags is returned.
Otherwise only the enabled tags will be returned.

Note: The contents of this list should not be modified.

=cut

sub tags {
    my ($self, $known) = @_;
    return keys %{ $self->{'known-tags'} } if $known;
    return keys %{ $self->{'enabled-tags'} };
}

=item $prof->scripts ([$known])

Returns the list of Check-Scripts in this profile.  If $known
is given and it is a truth value, the list of known Check-Scripts
is returned.  Otherwise only checks with an enabled tag will be
enabled.

=cut

sub scripts {
    my ($self, $known) = @_;
    return keys %{ $self->{'check-scripts'} } if $known;
    return keys %{ $self->{'enabled-checks'} };
}

=item $prof->is_overridable ($tag)

Returns a false value if the tag has been marked as
"non-overridable".  Otherwise it returns a truth value.

=cut

sub is_overridable {
    my ($self, $tag) = @_;
    return !exists $self->{'non-overridable-tags'}{$tag};
}

=item $prof->get_tag ($tag[, $known])

Returns the Lintian::Tag::Info for $tag if it is enabled for the
profile (or just a "known tag" if $known is given and a truth value).
Otherwise it returns undef.

=cut

sub get_tag {
    my ($self, $tag, $known) = @_;
    return unless $known || exists $self->{'enabled-tags'}{$tag};
    return $self->{'known-tags'}{$tag};
}

=item $prof->get_script ($script[, $known])

Returns the Lintian::CheckScript for $script if it is enabled for the
profile (or just a "known script" if $known is given and a truth value).
Otherwise it returns undef.

Note: A script is enabled as long as at least one of the tags it
provides are enabled.

=cut

sub get_script {
    my ($self, $script, $known) = @_;
    return unless $known || exists $self->{'enabled-checks'}{$script};
    return $self->{'check-scripts'}{$script};
}

=item $prof->enable_tags (@tags)

Enables all tags named in @tags.  Croaks if an unknown tag is found.

=cut

sub enable_tags {
    my ($self, @tags) = @_;
    for my $tag (@tags) {
        my $ti = $self->{'known-tags'}{$tag};
        croak "Unknown tag $tag" unless $ti;
        next if exists $self->{'enabled-tags'}{$tag};
        $self->{'enabled-tags'}{$tag} = 1;
        $self->{'enabled-checks'}{$ti->script}++;
    }
    return;
}

=item $prof->disable_tags (@tags)

Disable all tags named in @tags.  Croaks if an unknown tag is found.

=cut

sub disable_tags {
    my ($self, @tags) = @_;
    for my $tag (@tags) {
        my $ti = $self->{'known-tags'}{$tag};
        croak "Unknown tag $tag" unless $ti;
        next unless exists $self->{'enabled-tags'}{$tag};
        delete $self->{'enabled-tags'}{$tag};
        delete $self->{'enabled-checks'}{$ti->script}
          unless --$self->{'enabled-checks'}{$ti->script};
    }
    return;
}

=item $prof->include_path ([$path])

Returns an array of paths to the (partial) Lintian roots, which are
used by this profile.  The paths are ordered from "highest" to
"lowest" priority (i.e. items in the earlier paths should shadow those
in later ones).

If $path is given, the array will contain the paths to the path in
these roots denoted by $path.

Paths returned are not guaranteed to exists.

=cut

sub include_path {
    my ($self, $path) = @_;
    unless (defined $path) {
        return @{ $self->{'include-path'} };
    }
    return map { "$_/$path" } @{ $self->{'include-path'} };
}

# Temporary until aptdaemon (etc.) has been upgraded to handle
# Lintian loading code from user dirs.
# LP: #1162947
sub _safe_include_path {
    my ($self, $path) = @_;
    unless (defined $path) {
        return @{ $self->{'safe-include-path'} };
    }
    return map { "$_/$path" } @{ $self->{'safe-include-path'} };
}

# $prof->_find_profile ($pname)
#
# Finds a profile called $pname in the search directories and returns
# the path to it.  If $pname does not contain a slash, then it will look
# for a profile called "$pname/main" instead of $pname.
#
# Returns a non-truth value if the profile could not be found.  $pname
# cannot contain any dots.

sub _find_profile {
    my ($self, $pname) = @_;
    my $pfile;
    croak "\"$pname\" is not a valid profile name" if $pname =~ m/\./o;
    # $vendor is short for $vendor/main
    $pname = "$pname/main" unless $pname =~ m,/,o;
    $pfile = "$pname.profile";
    foreach my $path ($self->include_path('profiles')) {
        return "$path/$pfile" if -e "$path/$pfile";
    }
    return '';
}

# $self->_read_profile($pfile)
#
# Parses the profile stored in the file $pfile; if this method returns
# normally, the profile will have been parsed successfully.
sub _read_profile {
    my ($self, $pfile) = @_;
    my @pdata;
    my $pheader;
    my $pmap = $self->{'parent-map'};
    my $pname;
    my $plist = $self->{'profile_list'};
    @pdata = read_dpkg_control_utf8($pfile, 0);
    $pheader = shift @pdata;
    croak "Profile field is missing from $pfile"
      unless defined $pheader && $pheader->{'profile'};
    $pname = $pheader->{'profile'};
    croak "Invalid Profile field in $pfile"
      if $pname =~ m,^/,o
      or $pname =~ m/\./o;

    # Normalize the profile name
    $pname .= '/main' unless $pname =~m,/,;

    croak "Recursive definition of $pname"
      if exists $pmap->{$pname};
    $pmap->{$pname} = 0; # Mark as being loaded.
    $self->{'name'} = $pname unless exists $self->{'name'};
    if (exists $pheader->{'extends'}){
        my $parent = $pheader->{'extends'};
        my $parentf;
        croak "Invalid Extends field in $pfile"
          unless $parent && $parent !~ m/\./o;
        ($parentf, undef) = $self->_find_vendor_profile($parent);
        croak "Cannot find $parent, which $pname extends"
          unless $parentf;
        $self->_read_profile($parentf);
    }

    # Add the profile to the "chain" after loading its parent (if
    # any).
    push @$plist, $pname;

    $self->_read_profile_tags($pname, $pheader);
    if (@pdata){
        my $i = 2; # section counter
        foreach my $psection (@pdata){
            $self->_read_profile_section($pname, $psection, $i++);
        }
    }
    return;
}

# $self->_read_profile_section($pname, $section, $sno)
#
# Parses and applies the effects of $section (a paragraph
# in the profile). $pname is the name of the profile and
# $no is section number (both of these are only used for
# error reporting).
sub _read_profile_section {
    my ($self, $pname, $section, $sno) = @_;
    my @tags = $self->_split_comma_sep_field($section->{'tags'});
    my $overridable
      = $self->_parse_boolean($section->{'overridable'}, -1, $pname, $sno);
    my $severity = $section->{'severity'}//'';
    my $noover = $self->{'non-overridable-tags'};
    $self->_check_for_invalid_fields($section, \%SEC_FIELDS, $pname,
        "section $sno");
    croak(
        join(q{ },
            qq{Profile "$pname" is missing Tags field},
            "(or it is empty) in section $sno")) unless @tags;
    croak(
        join(q{ },
            qq{Profile "$pname" contains invalid severity},
            qq{"$severity" in section $sno}))

      if $severity
      && (!$SEVERITIES{$severity} || $severity eq 'classification');

    foreach my $tag (@tags) {
        croak "Unknown check $tag in $pname (section $sno)"
          unless $self->{'known-tags'}{$tag};
        if ($severity) {
            my $t = $self->{'known-tags'}{$tag};
            if ($t->severity(1) eq 'classification') {
                croak(
                    join(q{ },
                        qq{${tag} is a classification tag},
                        q{and cannot not be assigned a severity},
                        qq{(profile "$pname", section $sno)}));
            }
            $t->set_severity($severity);
        }
        if ($overridable != -1) {
            if ($overridable) {
                delete $noover->{$tag};
            } else {
                $noover->{$tag} = 1;
            }
        }
    }
    return;
}

# $self->_read_profile_tags($pname, $pheader)
#
# Interprets the {dis,en}able-tags{,-from-check} fields from
# the profile header $pheader.  $pname is the name of the
# profile (used for error reporting).
#
# If it returns, the enabled tags will be updated to reflect
#  the tags enabled/disabled by this profile (but not its
#  parents).
sub _read_profile_tags{
    my ($self, $pname, $pheader) = @_;
    $self->_check_for_invalid_fields($pheader, \%MAIN_FIELDS, $pname,
        'profile header');
    $self->_check_duplicates($pname, $pheader, 'load-checks',
        'enable-tags-from-check', 'disable-tags-from-check');
    $self->_check_duplicates($pname, $pheader, 'enable-tags', 'disable-tags');
    my $tags_from_check_sub = sub {
        my ($field, $check) = @_;

        unless (exists $self->{'check-scripts'}{$check}) {
            $self->_load_check($pname, $check);
        }
        return $self->{'check-scripts'}{$check}->tags;
    };
    my $tag_sub = sub {
        my ($field, $tag) = @_;
        unless (exists $self->{'known-tags'}{$tag}) {
            $self->_load_checks;
            croak "Unknown tag \"$tag\" in profile \"$pname\""
              unless exists $self->{'known-tags'}{$tag};
        }
        return $tag;
    };
    if ($pheader->{'load-checks'}) {
        for
          my $check ($self->_split_comma_sep_field($pheader->{'load-checks'})){
            $self->_load_check($pname, $check)
              unless exists $self->{'check-scripts'}{$check};
        }
    }
    $self->_enable_tags_from_field($pname, $pheader, 'enable-tags-from-check',
        $tags_from_check_sub, 1);
    $self->_enable_tags_from_field($pname, $pheader, 'disable-tags-from-check',
        $tags_from_check_sub, 0);
    $self->_enable_tags_from_field($pname, $pheader, 'enable-tags', $tag_sub,
        1);
    $self->_enable_tags_from_field($pname, $pheader, 'disable-tags', $tag_sub,
        0);
    return;
}

# $self->_enable_tags_from_field($pname, $pheader, $field, $code, $enable)
#
# Parse $field in $pheader as a comma separated list of items; these items are then
# passed to $code, that must returns a list of tags.  If $enable is a truth value
# these tags are enabled in the profile, otherwise they are disabled.
sub _enable_tags_from_field {
    my ($self, $pname, $pheader, $field, $code, $enable) = @_;
    my $method = \&enable_tags;
    my @tags;
    $method = \&disable_tags unless $enable;
    return unless $pheader->{$field};
    @tags = map { $code->($field, $_) }
      $self->_split_comma_sep_field($pheader->{$field});
    $self->$method(@tags);
    return;
}

# $self->_check_duplicates($name, $map, @fields)
#
# Checks the @fields in $map for duplicate values.  The
# values are parsed as comma-separated lists.  The same
# entry in these lists are not allowed twice, regardless
# of they appear twice in the same field or once in two
# different fields of @fields.
#
#
sub _check_duplicates{
    my ($self, $name, $map, @fields) = @_;
    my %dupmap;
    foreach my $field (@fields) {
        next unless exists $map->{$field};
        foreach my $element (split m/\s*+,\s*+/o, $map->{$field}){
            if (exists $dupmap{$element}){
                my $other = $dupmap{$element};
                croak(
                    join(q{ },
                        qq{"$element" appears in both "$field"},
                        qq{and "$other" in profile "$name"})
                ) unless $other eq $field;
                croak(
                    join(q{ },
                        qq{"$element" appears twice in the field},
                        qq{"$field" in profile "$name"}));
            }
            $dupmap{$element} = $field;
        }
    }
    return;
}

# $self->_parse_boolean($bool, $def, $pname, $sno);
#
# Parse $bool as a string representing a bool; if undefined return $def.
# $pname and $sno are the Profile name and section number - used for
# error reporting.
sub _parse_boolean {
    my ($self, $bool, $def, $pname, $sno) = @_;
    my $val;
    return $def unless defined $bool;
    eval { $val = parse_boolean($bool); };
    croak "\"$bool\" is not a boolean value in $pname (section $sno)"
      if $@;
    return $val;
}

# $self->_split_comma_sep_field($data)
#
# Split $data as a comma-separated list of items (whitespace will
# be ignored).
sub _split_comma_sep_field {
    my ($self, $data) = @_;
    return () unless defined $data;
    return split m/\s*,\s*/o, strip($data);
}

# $self->_check_for_invalid_fields($para, $known, $pname, $paraname)
#
# Check $para for unknown fields (e.g. fields not in $known).
# If an unknown field is found, croak using $pname and $paraname
# to identify the profile name and paragraph (respectively)
sub _check_for_invalid_fields {
    my ($self, $para, $known, $pname, $paraname) = @_;
    foreach my $field (keys %$para) {
        next if exists $known->{$field};
        croak "Unknown field \"$field\" in $pname ($paraname)";
    }
    return;
}

sub _load_check {
    my ($self, $profile, $check) = @_;
    my $dir;
    foreach my $checkdir ($self->_safe_include_path('checks')) {
        my $cf = "$checkdir/${check}.desc";
        if (-f $cf) {
            $dir = $checkdir;
            last;
        }
    }
    croak "$profile references unknown $check" unless defined $dir;
    return $self->_parse_check($check, $dir);
}

sub _parse_check {
    my ($self, $gcname, $dir) = @_;
    # Have we already tried to load this before?  Possibly via an alias
    # or symlink
    return $self->{'check-scripts'}{$gcname}
      if exists $self->{'check-scripts'}{$gcname};
    my $c = Lintian::CheckScript->new($dir, $gcname);
    my $cname = $c->name;
    if (exists $self->{'check-scripts'}{$cname}) {
        # We have loaded the check under a different name
        $c = $self->{'check-scripts'}{$cname};
        # Record the alias so we don't have to parse the check file again.
        $self->{'check-scripts'}{$gcname} = $c;
        return $c;
    }
    $self->{'check-scripts'}{$cname} = $c;
    $self->{'check-scripts'}{$gcname} = $c if $gcname ne $cname;

    for my $tn ($c->tags) {
        if ($self->{'known-tags'}{$tn}) {
            my $ocn = $self->{'known-tags'}{$tn}->script;
            croak "$cname redefined tag $tn which was defined by $ocn";
        }
        $self->{'known-tags'}{$tn} = $c->get_tag($tn);
    }
    return $c;
}

sub _load_checks {
    my ($self) = @_;
    foreach my $checkdir ($self->_safe_include_path('checks')) {
        next unless -d $checkdir;
        opendir(my $dirfd, $checkdir);
        for my $desc (sort readdir $dirfd) {
            my $cname = $desc;
            next unless $cname =~ s/\.desc$//o;
            # _parse_check ignores duplicates, so we don't have to
            # check for it.
            $self->_parse_check($cname, $checkdir);
        }
        closedir($dirfd);
    }
    return;
}

sub _default_inc_path {
    my @path;
    push @path, "$ENV{'HOME'}/.lintian"
      if exists $ENV{'HOME'} and defined $ENV{'HOME'};
    push @path, '/etc/lintian';
    # ENV{LINTIAN_ROOT} replaces /usr/share/lintian if present.
    push @path, $ENV{'LINTIAN_ROOT'} if defined $ENV{'LINTIAN_ROOT'};
    push @path, '/usr/share/lintian' unless defined $ENV{'LINTIAN_ROOT'};
    return @path;
}

sub _find_vendor_profile {
    my ($self, $prof) = @_;
    my @vendors;

    if (defined $prof and $prof !~ m/[{}]/) {
        # no substitution required...
        return ($self->_find_profile($prof), $prof);
    } elsif (defined $prof) {
        my $cpy = $prof;
        # Check for unknown (or broken) subst.
        $cpy =~ s/\Q{VENDOR}\E//g;
        croak "Unknown substitution \"$1\" (in \"$prof\")"
          if $cpy =~ m/\{([^ \}]+)\}/;
        croak "Bad, broken or empty substitution marker in \"$prof\""
          if $cpy =~ m/[{}]/;
    }

    $prof //= '{VENDOR}/main';

    @vendors = @{ $self->{'_vendor_cache'} }
      if exists $self->{'_vendor_cache'};
    unless (@vendors) {
        my $vendor = Dpkg::Vendor::get_current_vendor();
        croak 'Could not determine the current vendor'
          unless $vendor;
        push @vendors, lc $vendor;
        while ($vendor) {
            my $info = Dpkg::Vendor::get_vendor_info($vendor);
            # Cannot happen atm, but in case Dpkg::Vendor changes its internals
            #  or our code changes
            croak "Could not look up the parent vendor of $vendor"
              unless $info;
            $vendor = $info->{'Parent'};
            push @vendors, lc $vendor if $vendor;
        }
        $self->{'_vendor_cache'} = \@vendors;
    }
    foreach my $vendor (@vendors) {
        my $file;
        my $profname = $prof;
        $profname =~ s/\Q{VENDOR}\E/$vendor/g;

        $file = $self->_find_profile($profname);

        return ($file, $profname) if $file;
    }
    croak(
        join(q{ },
            'Could not find a profile matching',
            qq{"$prof" for vendor $vendors[0]}));
}

=back

=head1 AUTHOR

Originally written by Niels Thykier <niels@thykier.net> for Lintian.

=head1 SEE ALSO

lintian(1)

=cut

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
