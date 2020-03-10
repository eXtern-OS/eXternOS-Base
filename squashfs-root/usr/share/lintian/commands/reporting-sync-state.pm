#!/usr/bin/perl -w
#
# reporting-sync-state
#
# This program is free software.  It is distributed under the terms of
# the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any
# later version.
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

use strict;
use warnings;
use autodie;

use Getopt::Long();
use File::Basename qw(basename);
use YAML::XS ();
use MIME::Base64 qw(encode_base64);

use Lintian::Lab;
use Lintian::Relation::Version qw(versions_comparator);
use Lintian::Util qw(
  find_backlog
  load_state_cache
  open_gz
  save_state_cache
  strip
  visit_dpkg_paragraph
);

my $DEFAULT_CHECKSUM = 'sha256';
my (%KNOWN_MEMBERS, %ACTIVE_GROUPS);
my $CONFIG;
my %OPT;
my %OPT_HASH= (
    'reporting-config=s'=> \$OPT{'reporting-config'},
    'desired-version=s' => \$OPT{'desired-version'},
    'reschedule-all'    => \$OPT{'reschedule-all'},
    'help|h'            => \&usage,
    'debug|d'           => \$OPT{'debug'},
    'dry-run'           => \$OPT{'dry-run'},
);

sub check_parameters {
    for my $parameter (qw(reporting-config desired-version)) {
        if (not defined($OPT{$parameter})) {
            die(    "Missing required parameter \"--${parameter}\""
                  . "(use --help for more info)\n");
        }
    }
    if (not $OPT{'reporting-config'} or not -f $OPT{'reporting-config'}) {
        die("The --reporting-config parameter must point to an existing file\n"
        );
    }
    return;
}

sub required_cfg_value {
    my (@keys) = @_;
    my $v = $CONFIG;
    for my $key (@keys) {
        if (not exists($v->{$key})) {
            my $k = join('.', @keys);
            die("Missing required config parameter: ${k}\n");
        }
        $v = $v->{$key};
    }
    return $v;
}

sub required_cfg_non_empty_list_value {
    my (@keys) = @_;
    my $v = required_cfg_value(@keys);
    if (not defined($v) or ref($v) ne 'ARRAY' or scalar(@{$v}) < 1) {
        my $k = join('.', @keys);
        die("Invalid configuration: ${k} must be a non-empty list\n");
    }
    return $v;
}

sub main {
    my ($state_dir, $state, $archives);
    STDOUT->autoflush;
    Getopt::Long::config('bundling', 'no_getopt_compat', 'no_auto_abbrev');
    Getopt::Long::GetOptions(%OPT_HASH) or die("error parsing options\n");
    check_parameters();
    $CONFIG = YAML::XS::LoadFile($OPT{'reporting-config'});
    $state_dir = required_cfg_value('storage', 'state-cache');
    $state = load_state_cache($state_dir);

    if (upgrade_state_cache_if_needed($state)) {
        log_debug('Updated the state cache');
    }
    log_debug('Initial state had '
          . (scalar(keys(%{$state->{'groups'}})))
          . ' groups');
    $archives = required_cfg_value('archives');
    for my $archive (sort(keys(%{$archives}))) {
        log_debug("Processing archive $archive");
        my $path = required_cfg_value('archives', $archive, 'base-dir');
        my $archs = required_cfg_non_empty_list_value('archives', $archive,
            'architectures');
        my $components
          = required_cfg_non_empty_list_value('archives', $archive,
            'components');
        my $distributions
          = required_cfg_non_empty_list_value('archives', $archive,
            'distributions');
        local_mirror_manifests($state, $path, $distributions, $components,
            $archs);
    }

    cleanup_state($state);
    if (not $OPT{'dry-run'}) {
        save_state_cache($state_dir, $state);
    }
    exit(0);
}

# State:
#  group-id => {
#    'last-processed-by' => <version or undef>,
#    'out-of-date'  => <0|1>, (# if omitted => 0, unless "last-processed-by" is omitted as well)
#    'members' => {
#       $member_id => {
#          'sha1'  => <sha1>,
#          'path'  => <path/relative/to/mirror>,
#       }
#    },

sub upgrade_state_cache_if_needed {
    my ($state) = @_;
    if (exists($state->{'groups'})) {
        my $updated = 0;
        my $groups = $state->{'groups'};
        for my $group (sort(keys(%{$groups}))) {
            my $group_data = $groups->{$group};
            if (   exists($group_data->{'mirror-metadata'})
                && exists($group_data->{'mirror-metadata'}{'area'})) {
                if (not exists($group_data->{'mirror-metadata'}{'component'})){
                    $group_data->{'mirror-metadata'}{'component'}
                      = $group_data->{'mirror-metadata'}{'area'};
                    delete($group_data->{'mirror-metadata'}{'area'});
                    $updated = 1;
                }
            }
        }
        return $updated;
    }
    # Migrate the "last-processed-by" version.
    my $groups = $state->{'groups'} = {};
    for my $key (sort(keys(%${state}))) {
        next if $key eq 'group';
        if (exists($state->{$key}{'last-processed-by'})) {
            my $last_version = $state->{$key}{'last-processed-by'};
            delete($state->{$key});
            $groups->{$key}{'last-processed-by'} = $last_version;
        }
    }
    return 1;
}

sub add_member_to_group {
    my ($state, $group_id, $member_id, $member_data, $group_metadata) = @_;
    # Fetch members before group_data (relying on autovivification)
    my $members = $state->{'groups'}{$group_id}{'members'};
    my $group_data = $state->{'groups'}{$group_id};
    my $member;
    my $new_group = 0;
    if (not defined($members)) {
        $group_data->{'members'} = $members = {};
        log_debug(
            "${group_id} is out-of-date: New group (triggered by ${member_id})"
        );
        $new_group = 1;
    }

    $member = $members->{$member_id};
    if (not defined($member)) {
        $members->{$member_id} = $member = {};
    }

    # Update of path is not sufficient to consider the member out of date
    # (mirror restructuring happens - although extremely rarely)
    $member->{'path'} = $member_data->{'path'};
    if ($member_data->{'mirror-metadata'}
        && keys(%{$member_data->{'mirror-metadata'}})) {
        $member->{'mirror-metadata'} = $member_data->{'mirror-metadata'};
    }
    if (not exists($group_data->{'mirror-metadata'})) {
        $group_data->{'mirror-metadata'}= $group_metadata->{'mirror-metadata'};
    } else {
        for my $key (keys(%{$group_metadata->{'mirror-metadata'}})) {
            $group_data->{'mirror-metadata'}{$key}
              = $group_metadata->{'mirror-metadata'}{$key};
        }
    }
    $KNOWN_MEMBERS{"${group_id} ${member_id}"} = 1;
    $ACTIVE_GROUPS{$group_id} = 1;

    if (!exists($member->{$DEFAULT_CHECKSUM})
        || $member->{$DEFAULT_CHECKSUM} ne $member_data->{$DEFAULT_CHECKSUM}) {
        if (exists($member->{$DEFAULT_CHECKSUM})) {
            # This seems worth a note even if the group is already out of date
            log_debug(
                "${group_id} is out-of-date: ${member_id} checksum mismatch"
                  . " ($member->{$DEFAULT_CHECKSUM} != $member_data->{$DEFAULT_CHECKSUM})"
            );
        } elsif (not $group_data->{'out-of-date'} and not $new_group) {
            log_debug("${group_id} is out-of-date: New member (${member_id})");
        }
        $group_data->{'out-of-date'} = 1;
        $member->{$DEFAULT_CHECKSUM} = $member_data->{$DEFAULT_CHECKSUM};
    }
    delete($member->{'sha1'});

    return;
}

sub cleanup_state {
    my ($state) = @_;
    my %backlog
      = map { $_ => 1 } find_backlog($OPT{'desired-version'}, $state);

    # Empty 'members-to-groups' to prune "dead links".  It will be
    # recreated by cleanup_group_state below.
    $state->{'members-to-groups'} = {};

    for my $group_id (sort(keys(%{$state->{'groups'}}))) {
        cleanup_group_state($state, $group_id, \%backlog);
    }
    return;
}

sub remove_if_empty {
    my ($hash_ref, $key) = @_;
    my ($val, $empty);
    return if not exists($hash_ref->{$key});
    $val = $hash_ref->{$key};
    if (defined($val)) {
        $empty = 1 if (ref($val) eq 'HASH' and not keys(%${val}));
        $empty = 1 if (ref($val) eq 'ARRAY' and not scalar(@${val}));
    } else {
        $empty = 1;
    }
    delete($hash_ref->{$key}) if $empty;
    return;
}

sub cleanup_group_state {
    my ($state, $group_id, $backlog) = @_;
    my ($members);
    my $group_data = $state->{'groups'}{$group_id};
    $members = $group_data->{'members'};
    if (not exists($ACTIVE_GROUPS{$group_id}) or not $members) {
        # No members left, remove the group entirely
        delete($state->{'groups'}{$group_id});
        if (not exists($ACTIVE_GROUPS{$group_id})) {
            log_debug("Group ${group_id} dropped: It is not an active group");
        } else {
            log_debug("Group ${group_id} dropped: No members left (early)");
        }

        return;
    }

    for my $member_id (sort(keys(%{$members}))) {
        if (not exists($KNOWN_MEMBERS{"${group_id} ${member_id}"})) {
            delete($members->{$member_id});
            if (not $group_data->{'out-of-date'}) {
                $group_data->{'out-of-date'} = 1;
                log_debug(
                    "${group_id} is out-of-date: ${member_id} disappeared");
            }
        } else {
            my $member_data = $members->{$member_id};
            # Create "member_id to group_data" link
            $state->{'members-to-groups'}{$member_id} = $group_data;
            delete($member_data->{'mirror-metadata'}{'component'})
              if exists($member_data->{'mirror-metadata'});
            remove_if_empty($member_data, 'mirror-metadata');
        }
    }

    # Add the "out-of-date" flag if it is in the backlog OR we were asked
    # to reschedule all
    if (not $group_data->{'out-of-date'}) {
        if ($OPT{'reschedule-all'} or $backlog->{$group_id}) {
            $group_data->{'out-of-date'} = 1;
            log_debug("Marking ${group_id} as out of date: In backlog")
              if $backlog->{$group_id};
        }
    }
    # Check for and possible clear the error counters
    if (
        exists($group_data->{'processing-errors'})
        and (not exists($group_data->{'last-error-by'})
            or $group_data->{'last-error-by'} ne $OPT{'desired-version'})
      ) {
        log_debug(
            "Clearing error-counter for ${group_id}: New version of lintian");
        delete($group_data->{'processing-errors'});
        # Leave "last-error-by" as we can use that to tell if the previous
        # version triggered errors.
    }

    if (not %{$members}) {
        # No members left, remove the group entirely.  This should not happen
        # as the ACTIVE_GROUPS check above ought to have caught this.
        delete($state->{$group_id});
        log_debug("Group ${group_id} dropped: No members left (late)");
    } else {
        # remove redundant fields
        remove_if_empty($group_data, 'out-of-date');
        for my $metadata_field (qw(component maintainer uploaders)) {
            remove_if_empty($group_data->{'mirror-metadata'}, $metadata_field);
        }
        remove_if_empty($group_data, 'mirror-metadata');
    }

    return;
}

# Helper for local_mirror_manifests - it parses a paragraph from Sources file
sub _parse_srcs_pg {
    my ($state, $extra_metadata, $paragraph) = @_;
    my $dir = $paragraph->{'directory'}//'';
    my $group_id = $paragraph->{'package'} . '/' . $paragraph->{'version'};
    my $member_id = "source:${group_id}";
    my (%data, %group_metadata, $group_mirror_md);
    # only include the source if it has any binaries to be checked.
    # - Otherwise we may end up checking a source with no binaries
    #   (happens if the architecture is "behind" in building)
    return unless $ACTIVE_GROUPS{$group_id};
    $dir .= '/' if $dir;
    foreach my $f (split m/\n/, $paragraph->{"checksums-${DEFAULT_CHECKSUM}"}){
        strip($f);
        next unless $f && $f =~ m/\.dsc$/;
        my ($checksum, undef, $basename) = split(m/\s++/, $f);
        my $b64_checksum = encode_base64(pack('H*', $checksum));
        # $dir should end with a slash if it is non-empty.
        $data{$DEFAULT_CHECKSUM} = $b64_checksum;
        $data{'path'} = $extra_metadata->{'mirror-dir'}  . "/$dir" . $basename;
        last;
    }

    $group_mirror_md = $group_metadata{'mirror-metadata'} = {};
    $group_mirror_md->{'component'} = $extra_metadata->{'component'};
    $group_mirror_md->{'maintainer'} = $paragraph->{'maintainer'};
    if (my $uploaders = $paragraph->{'uploaders'}) {
        my @ulist = split(/>\K\s*,\s*/, $uploaders);
        $group_mirror_md->{'uploaders'} = \@ulist;
    }

    add_member_to_group($state, $group_id, $member_id, \%data,
        \%group_metadata);
    return;
}

# Helper for local_mirror_manifests - it parses a paragraph from Packages file
sub _parse_pkgs_pg {
    my ($state, $extra_metadata, $type, $paragraph) = @_;
    my ($group_id, $member_id, %data, %group_metadata, $b64_checksum);
    my $package = $paragraph->{'package'};
    my $version = $paragraph->{'version'};
    my $architecture = $paragraph->{'architecture'};
    if (not defined($paragraph->{'source'})) {
        $paragraph->{'source'} = $package;
    } elsif ($paragraph->{'source'} =~ /^([-+\.\w]+)\s+\((.+)\)$/) {
        $paragraph->{'source'} = $1;
        $paragraph->{'source-version'} = $2;
    }
    if (not defined($paragraph->{'source-version'})) {
        $paragraph->{'source-version'} = $paragraph->{'version'};
    }
    $group_id = $paragraph->{'source'} . '/' . $paragraph->{'source-version'};
    $member_id = "${type}:${package}/${version}/${architecture}";
    $data{'path'}
      = $extra_metadata->{'mirror-dir'} . '/' . $paragraph->{'filename'};
    $b64_checksum = encode_base64(pack('H*', $paragraph->{$DEFAULT_CHECKSUM}));
    $data{$DEFAULT_CHECKSUM} = $b64_checksum;

    $group_metadata{'mirror-metadata'}{'maintainer'}
      = $paragraph->{'maintainer'};
    if (my $uploaders = $paragraph->{'uploaders'}) {
        my @ulist = split(/>\K\s*,\s*/, $uploaders);
        $group_metadata{'mirror-metadata'}{'uploaders'} = \@ulist;
    }

    add_member_to_group($state, $group_id, $member_id, \%data,
        \%group_metadata);
    return;
}

# local_mirror_manifests ($mirdir, $dists, $components, $archs)
#
# Returns a list of manifests that represents what is on the local mirror
# at $mirdir.  3 manifests will be returned, one for "source", one for "binary"
# and one for "udeb" packages.  They are populated based on the "Sources" and
# "Packages" files.
#
# $mirdir - the path to the local mirror
# $dists  - listref of dists to consider (e.g. ['unstable'])
# $components  - listref of components to consider (e.g. ['main', 'contrib', 'non-free'])
# $archs  - listref of archs to consider (e.g. ['i386', 'amd64'])
#
sub local_mirror_manifests {
    my ($state, $mirdir, $dists, $components, $archs) = @_;
    foreach my $dist (@$dists) {
        foreach my $component (@{$components}) {
            my $srcs = "$mirdir/dists/$dist/$component/source/Sources";
            my ($srcfd, $srcsub);
            my %extra_metadata = (
                'component' => $component,
                'mirror-dir' => $mirdir,
            );
            # Binaries have a "per arch" file.
            # - we check those first and then include the source packages that
            #   are referred to by these binaries.
            my $dist_path = "$mirdir/dists/$dist/$component";
            foreach my $arch (@{$archs}) {
                my $pkgs = "${dist_path}/binary-$arch/Packages";
                my $upkgs
                  = "${dist_path}/debian-installer/binary-$arch/Packages";
                my $pkgfd = _open_data_file($pkgs);
                my $binsub = sub {
                    _parse_pkgs_pg($state, \%extra_metadata, 'binary', @_);
                };
                my $upkgfd;
                my $udebsub = sub {
                    _parse_pkgs_pg($state, \%extra_metadata, 'udeb', @_);
                };
                visit_dpkg_paragraph($binsub, $pkgfd);
                close($pkgfd);
                $upkgfd = _open_data_file($upkgs);
                visit_dpkg_paragraph($udebsub, $upkgfd);
                close($upkgfd);
            }
            $srcfd = _open_data_file($srcs);
            $srcsub = sub { _parse_srcs_pg($state, \%extra_metadata, @_) };
            visit_dpkg_paragraph($srcsub, $srcfd);
            close($srcfd);
        }
    }
    return;
}

# _open_data_file ($file)
#
# Opens $file if it exists, otherwise it tries common extensions (i.e. .gz) and opens
# that instead.  It may pipe the file through an external decompressor, so the returned
# file descriptor cannot be assumed to be a file.
#
# If $file does not exists and no common extensions are found, this dies.  It may also
# die if it finds a file, but is unable to open it.
sub _open_data_file {
    my ($file) = @_;
    if (-e $file) {
        open(my $fd, '<:encoding(UTF-8)', $file);
        return $fd;
    }
    if (-e "${file}.gz") {
        my $fd = open_gz("${file}.gz");
        binmode($fd, 'encoding(UTF-8)');
        return $fd;
    }
    if (-e "${file}.xz") {
        open(my $fd, '-|', 'xz', '-dc', "${file}.xz");
        binmode($fd, 'encoding(UTF-8)');
        return $fd;
    }
    die("Cannot find ${file}: file does not exist");
}

sub log_debug {
    if ($OPT{'debug'}) {
        print "$_[0]\n";
    }
    return;
}

sub usage {
    my $cmd = basename($0);
    my $me = "dplint $cmd";
    print <<EOF;
Internal command for the Lintian reporting framework
Usage: $me <args>

  --help                 Show this text and exit
  --debug                Show/log debugging output

  --reporting-config FILE
                         Path to the configuration file (listing the archive definitions) [!]
  --desired-version X    The desired "last-processed-by" Lintian version. [!]

Arguments marked with [!] are required for a successful run.

EOF

    exit(0);
}

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
