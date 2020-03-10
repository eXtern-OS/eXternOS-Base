#!/usr/bin/perl -w
#
# Lintian HTML reporting tool -- Create Lintian web reports
#
# Copyright (C) 1998 Christian Schwarz and Richard Braakman
# Copyright (C) 2007 Russ Allbery
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

use Getopt::Long;
use POSIX qw(strftime);
use File::Copy qw(copy);
use Fcntl qw(SEEK_SET);
use List::Util qw(first);
use List::MoreUtils qw(uniq);
use URI::Escape;
use Text::Template ();
use YAML::XS ();

use Lintian::Command qw(safe_qx);
use Lintian::Data;
use Lintian::Internal::FrontendUtil qw(split_tag);
use Lintian::Profile;
use Lintian::Relation::Version qw(versions_comparator);
use Lintian::Reporting::ResourceManager;
use Lintian::Util qw(read_dpkg_control slurp_entire_file load_state_cache
  find_backlog copy_dir delete_dir run_cmd check_path);

my $CONFIG;
my %OPT;
my %OPT_HASH = ('reporting-config=s'=> \$OPT{'reporting-config'},);

# ------------------------------
# Global variables and configuration

# Some globals initialised in init_global()
my (
    $RESOURCE_MANAGER, $LINTIAN_VERSION, $timestamp,
    $TEMPLATE_CONFIG_VARS,$HARNESS_STATE_DIR, $HISTORY_DIR,
    $HISTORY, $GRAPHS, $LINTIAN_ROOT,
    $HTML_TMP_DIR, $SCOUR_ENABLED,
);
# FIXME: Should become obsolete if gnuplot is replaced by R like piuparts.d.o /
# reproducible.d.n is using
my $GRAPHS_RANGE_DAYS = 366;

# ------------------------------
# Initialize templates

# This only has to be done once, so do it at the start and then reuse the same
# templates throughout.
our %templates;

# %statistics accumulates global statistics.  For tags: errors, warnings,
# experimental, overridden, and info are the keys holding the count of tags of
# that sort.  For packages: binary, udeb, and source are the number of
# packages of each type with Lintian errors or warnings.  For maintainers:
# maintainers is the number of maintainers with Lintian errors or warnings.
#
# %tag_statistics holds a hash of tag-specific statistics.  Each tag name is a
# key, and its value is a hash with the following keys: count and overrides
# (number of times the tag has been detected and overridden, respectively), and
# packages (number of packages with at least one such tag).
my (%statistics, %tag_statistics);

# %by_maint holds a hash of maintainer names to packages and tags.  Each
# maintainer is a key.  The value is a hash of package names to hashes.  Each
# package hash is in turn a hash of versions to an anonymous array of hashes,
# with each hash having keys code, package, type, tag, severity, certainty,
# extra, and xref.  xref gets the partial URL of the maintainer page for that
# source package.
#
# In other words, the lintian output line:
#
#     W: gnubg source: substvar-source-version-is-deprecated gnubg-data
#
# for gnubg 0.15~20061120-1 maintained by Russ Allbery <rra@debian.org> is
# turned into the following structure:
#
# { 'gnubg' => {
#       '0.15~20061120-1' => [
#           { code      => 'W', # Either 'O' or same as $tag_info->code
#             pkg_info  => {
#                            package   => 'gnubg',
#                            version   => '0.15~20061120-1',
#                            component => 'main',
#                            type      => 'source',
#                            anchor    => 'gnubg_0.15~20061120-1',
#                            xref      => 'rra@debian.org.html#gnubg_0.15~20061120-1'
#             },
#             tag_info  => $tag_info,  # an instance of Lintian::Tag::Info
#             extra     => 'gnubg-data'
#           } ] } }
#
# and then stored under the key 'Russ Allbery <rra@debian.org>'
#
# %by_uploader holds the same thing except for packages for which the person
# is only an uploader.
#
# %by_tag is a hash of tag names to an anonymous array of tag information
# hashes just like the inside-most data structure above.
my (%by_maint, %by_uploader, %by_tag, %maintainer_table, %delta);
my @attrs = qw(maintainers source-packages binary-packages udeb-packages
  errors warnings info experimental pedantic overridden groups-known
  groups-backlog classifications groups-with-errors);

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

# ------------------------------
# Main routine

sub main {
    my $profile = init_globals();

    setup_output_dir(
        'output_dir'       => $HTML_TMP_DIR,
        'lintian_manual'   => "${LINTIAN_ROOT}/doc/lintian.html",
        'lintian_api_docs' => "${LINTIAN_ROOT}/doc/api.html",
        'lintian_log_file' => $ARGV[0],
        'resource_dirs'    =>
          [map { "${LINTIAN_ROOT}/reporting/$_"} qw(images resources)],
    );

    load_templates("$LINTIAN_ROOT/reporting/templates");

    # Create lintian.css from a template, install the output file as a resource
    # and discard the original output file.  We do this after installing all
    # resources, so the .css file can refer to resources.
    output_template(
        'lintian.css',
        $templates{'lintian.css'},
        { 'path_prefix' => '../' });
    $RESOURCE_MANAGER->install_resource("$HTML_TMP_DIR/lintian.css");

    my $state_cache = load_state_cache($HARNESS_STATE_DIR);

    print "Parsing lintian log...\n";
    parse_lintian_log($profile, $state_cache);

    process_data($profile, $state_cache);
    exit(0);
}

# ------------------------------
# Utility functions

sub init_globals {
    Getopt::Long::config('bundling', 'no_getopt_compat', 'no_auto_abbrev');
    Getopt::Long::GetOptions(%OPT_HASH) or die("error parsing options\n");

    if (not $OPT{'reporting-config'} or not -f $OPT{'reporting-config'}) {
        die("The --reporting-config parameter must point to an existing file\n"
        );
    }
    $LINTIAN_ROOT = $ENV{'LINTIAN_ROOT'};

    $CONFIG = YAML::XS::LoadFile($OPT{'reporting-config'});
    $HARNESS_STATE_DIR = required_cfg_value('storage', 'state-cache');
    $HTML_TMP_DIR = required_cfg_value('storage', 'reports-work-dir');
    my $history_key = 'storage.historical-data-dir';
    if (exists($CONFIG->{'storage'}{'historical-data-dir'})) {
        $HISTORY = 1;
        $HISTORY_DIR = required_cfg_value('storage', 'historical-data-dir');
        print "Enabling history tracking as ${history_key} is set\n";
        if (check_path('gnuplot')) {
            $GRAPHS = 1;
            print "Enabling graphs (gnuplot is in PATH)\n";
        } else {
            $GRAPHS = 0;
            print "No graphs as \"gnuplot\" is not in PATH\n";
        }
        if ($GRAPHS) {
            if (check_path('scour')) {
                $SCOUR_ENABLED = 1;
                print "Minimizing generated SVG files (scour is in PATH)\n";
            } else {
                $SCOUR_ENABLED = 0;
                print 'No minimization of generated SVG files'
                  . " as \"scour\" is not in PATH\n";
            }
        }
    } else {
        $HISTORY = 0;
        $GRAPHS = 0;
        print "History tracking is disabled (${history_key} is unset)\n";
        print "Without history tracking, there will be no graphs\n";
    }

    if (exists($CONFIG->{'template-variables'})) {
        $TEMPLATE_CONFIG_VARS = $CONFIG->{'template-variables'};
    } else {
        $TEMPLATE_CONFIG_VARS = {};
    }
    # Provide a default URL for the source code.  It might not be correct for
    # the given installation, but it is better than nothing.
    $TEMPLATE_CONFIG_VARS->{'LINTIAN_SOURCE'}
      //= 'https://anonscm.debian.org/git/lintian/lintian.git';

    my $profile = dplint::load_profile();

    Lintian::Data->set_vendor($profile);

    $LINTIAN_VERSION = dplint::lintian_version();
    $timestamp = safe_qx(qw(date -u --rfc-822));
    chomp($LINTIAN_VERSION, $timestamp);

    $RESOURCE_MANAGER
      = Lintian::Reporting::ResourceManager->new('html_dir' => $HTML_TMP_DIR,);
    return $profile;
}

sub load_templates {
    my ($template_dir) = @_;
    for my $template (
        qw/head foot clean index maintainer maintainers packages tag
        tags tags-severity tag-not-seen tags-all/
      ) {
        open(my $fd, '<:encoding(UTF-8)', "${template_dir}/$template.tmpl");
        my %options = (TYPE => 'FILEHANDLE', SOURCE => $fd);
        $templates{$template} = Text::Template->new(%options)
          or die "cannot load template $template: $Text::Template::ERROR\n";
        close($fd);
    }

    open(my $fd, '<:encoding(UTF-8)', "${template_dir}/lintian.css.tmpl");
    $templates{'lintian.css'} = Text::Template->new(
        TYPE => 'FILEHANDLE',
        SOURCE => $fd,
        DELIMITERS => ['{{{', '}}}'],
      )
      or die("cannot load template for lintian.css: $Text::Template::ERROR\n");
    close($fd);
    return;
}

sub process_data {
    my ($profile, $state_cache) = @_;
    my @maintainers = sort(uniq(keys(%by_maint), keys(%by_uploader)));
    my $statistics_file = "$HARNESS_STATE_DIR/statistics";
    my ($old_statistics, $archives, @archive_info);

    {
        # Scoped to allow memory to be re-purposed.  The %qa and %sources
        # structures are only used for a very few isolated items.
        my (%qa, %sources);
        print "Collecting statistics...\n";
        $old_statistics
          = collect_statistics($profile, $state_cache, $statistics_file,
            \@maintainers,\%sources, \%qa);

        generate_lookup_tables(\%sources);

        write_qa_list(\%qa);

        generate_package_index_packages(\%sources);

        if ($HISTORY) {
            update_history_and_make_graphs(\@attrs, \%statistics,
                \%tag_statistics);
        }
    }

    # Build a hash of all maintainers, not just those with Lintian tags.  We
    # use this later to generate stub pages for maintainers whose packages are
    # all Lintian-clean.
    my %clean;
    for my $group_id (sort(keys(%{$state_cache->{'groups'}}))) {
        my $maintainer
          = $state_cache->{'groups'}{$group_id}{'mirror-metadata'}
          {'maintainer'};
        my $id;
        next if not $maintainer;
        $id = maintainer_url($maintainer);
        $clean{$id} = $maintainer;
    }

    # Now, walk through the tags by source package (sorted by maintainer).
    # Output a summary page of errors and warnings for each maintainer, output
    # a full page that includes info, experimental, and overridden tags, and
    # assemble the maintainer index and the QA package list as we go.

    for my $maintainer (@maintainers) {
        my $id = maintainer_url($maintainer);
        delete $clean{$id};

        # Determine if the maintainer's page is clean.  Check all packages for
        # which they're either maintainer or uploader and set $error_clean if
        # they have no errors or warnings.
        #
        # Also take this opportunity to sort the tags so that all similar tags
        # will be grouped, which produces better HTML output.
        my $error_clean = 1;
        for my $source (
            keys %{ $by_maint{$maintainer} },
            keys %{ $by_uploader{$maintainer} }
          ) {
            my $versions = $by_maint{$maintainer}{$source}
              || $by_uploader{$maintainer}{$source};
            for my $version (keys %$versions) {
                $versions->{$version}
                  = [sort by_tag @{ $versions->{$version} }];
                next if not $error_clean;
                my $tags = $versions->{$version};
                for my $tag (@$tags) {
                    if ($tag->{code} eq 'E' or $tag->{code} eq 'W') {
                        $error_clean = 0;
                        last;
                    }
                }
            }
        }

        # Determine the parts of the maintainer and the file name for the
        # maintainer page.
        my ($name, $email) = extract_name_and_email($maintainer);

        my $regular = "maintainer/$id";
        my $full = "full/$id";

        # Create the regular maintainer page (only errors and warnings) and the
        # full maintainer page (all tags, including overrides and info tags).
        print "Generating page for $id\n";
        my $q_name = html_quote($name);
        my %data = (
            email      => html_quote(uri_escape($email)),
            errors     => 1,
            id         => $id,
            maintainer => html_quote($maintainer),
            name       => $q_name,
            packages   => $by_maint{$maintainer},
            uploads    => $by_uploader{$maintainer},
        );
        my $template;
        if ($error_clean) {
            $template = $templates{clean};
        } else {
            $template = $templates{maintainer};
        }
        output_template($regular, $template, \%data);
        $template = $templates{maintainer};
        $data{errors} = 0;
        output_template($full, $template, \%data);

        my %index_data = (url => $id, name => $q_name);
        # Add this maintainer to the hash of maintainer to URL mappings.
        $maintainer_table{$maintainer} = \%index_data;
    }
    undef(@maintainers);

    # Write out the maintainer index.
    my %data = (maintainers => \%maintainer_table,);
    output_template('maintainers.html', $templates{maintainers}, \%data);

    # Now, generate stub pages for every maintainer who has only clean
    # packages.
    for my $id (keys %clean) {
        my $maintainer = $clean{$id};
        my ($name, $email) = extract_name_and_email($maintainer);
        my %maint_data = (
            id         => $id,
            email      => html_quote(uri_escape($email)),
            maintainer => html_quote($maintainer),
            name       => html_quote($name),
            clean      => 1,
        );
        print "Generating clean page for $id\n";
        output_template("maintainer/$id", $templates{clean}, \%maint_data);
        output_template("full/$id", $templates{clean}, \%maint_data);
    }

    # Create the pages for each tag.  Each page shows the extended description
    # for the tag and all the packages for which that tag was issued.
    for my $tag (sort $profile->tags(1)) {
        my $info = $profile->get_tag($tag, 1);
        my $description = $info->description('html', '    ');
        my ($count, $overrides) = (0, 0);
        my $tmpl = 'tag-not-seen';
        my $shown_count = 0;
        my $tag_list = $by_tag{$tag};
        my $tag_limit_total = 1024;
        my $tag_limit_per_package = 3;

        if (exists $by_tag{$tag}) {
            $tmpl = 'tag';
            $count = $tag_statistics{$tag}{'count'};
            $overrides = $tag_statistics{$tag}{'overrides'};
            $shown_count = $count + $overrides;
        }
        if ($shown_count > $tag_limit_total) {
            my (@replacement_list, %seen);
            for my $orig_info (
                sort { $a->{pkg_info}{package} cmp $b->{pkg_info}{package} }
                @{$tag_list}) {
                my $pkg_info = $orig_info->{pkg_info};
                my $key
                  = "$pkg_info->{package} $pkg_info->{type} $pkg_info->{version}";
                next if ++$seen{$key} > $tag_limit_per_package;
                push(@replacement_list, $orig_info);
                last if @replacement_list >= $tag_limit_total;
            }
            $tag_list = \@replacement_list;
            $shown_count = scalar(@replacement_list);
        }

        my %maint_data = (
            description => $description,
            tag         => $tag,
            code        => $info->code,
            tags        => $tag_list,
            shown_count => $shown_count,
            tag_limit_per_package => $tag_limit_per_package,
            graphs      => $GRAPHS,
            graphs_days => $GRAPHS_RANGE_DAYS,
            statistics  => {
                count       => $count,
                overrides   => $overrides,
                total       => $count + $overrides,
            },
        );
        output_template("tags/$tag.html", $templates{$tmpl}, \%maint_data);
    }

    # Create the general tag indices.
    %data = (
        tags       => \%by_tag,
        stats      => \%tag_statistics,
        profile    => \$profile,
    );
    output_template('tags.html', $templates{tags}, \%data);
    output_template('tags-severity.html', $templates{'tags-severity'}, \%data);
    output_template('tags-all.html', $templates{'tags-all'}, \%data);

    # Update the statistics file.
    open(my $stats_fd, '>', $statistics_file);
    print {$stats_fd} "last-updated: $timestamp\n";
    for my $attr (@attrs) {
        print {$stats_fd} "$attr: $statistics{$attr}\n";
    }
    print {$stats_fd} "lintian-version: $LINTIAN_VERSION\n";
    close($stats_fd);

    $archives = required_cfg_value('archives');
    for my $archive (sort(keys(%{$archives}))) {
        my $architectures
          = required_cfg_non_empty_list_value('archives', $archive,
            'architectures');
        my $components
          = required_cfg_non_empty_list_value('archives', $archive,
            'components');
        my $distributions
          = required_cfg_non_empty_list_value('archives', $archive,
            'distributions');
        my $path = required_cfg_value('archives', $archive, 'base-dir');
        my $trace_basename
          = required_cfg_value('archives', $archive, 'tracefile');

        # The path to the mirror timestamp.
        my $trace_file= "${path}/project/trace/${trace_basename}";
        my $mirror_timestamp = slurp_entire_file($trace_file);
        $mirror_timestamp =~ s/\n.*//s;
        $mirror_timestamp
          = safe_qx('date', '-u', '--rfc-822', '-d', $mirror_timestamp);
        my %info = (
            'name' => $archive,
            'architectures' => $architectures,
            'components'    => $components,
            'distributions' => $distributions,
            'timestamp'     => $mirror_timestamp,
        );
        push(@archive_info, \%info);
    }

    # Finally, we can start creating the index page.
    %data = (
        delta        => \%delta,
        archives     => \@archive_info,
        previous     => $old_statistics->{'last-updated'},
        graphs       => $GRAPHS,
        graphs_days  => $GRAPHS_RANGE_DAYS,
    );
    output_template('index.html', $templates{index}, \%data);
    return;
}

sub setup_output_dir {
    my (%args) = @_;
    my $output_dir = $args{'output_dir'};
    my $lintian_manual = $args{'lintian_manual'};
    my $lintian_api = $args{'lintian_api_docs'};
    my $resource_dirs = $args{'resource_dirs'} // [];
    my $lintian_log_file = $args{'lintian_log_file'};

    # Create output directories.
    mkdir($output_dir, 0777);
    mkdir("$output_dir/full", 0777);
    mkdir("$output_dir/maintainer", 0777);
    mkdir("$output_dir/tags", 0777);
    symlink('.', "$output_dir/reports");
    copy_dir($lintian_manual, "$output_dir/manual");
    copy_dir($lintian_api, "$output_dir/library-api");

    if ($lintian_log_file) {
        my %opts = (
            'in'  => $lintian_log_file,
            'out' => "$output_dir/lintian.log.gz",
        );
        run_cmd(\%opts, 'gzip', '-9nc');
        $RESOURCE_MANAGER->install_resource("$output_dir/lintian.log.gz");
        symlink($RESOURCE_MANAGER->resource_URL('lintian.log.gz'),
            "$output_dir/lintian.log.gz");
    }

    for my $dir (@{$resource_dirs}) {
        next if not -d $dir;
        opendir(my $dirfd, $dir);
        for my $resname (readdir($dirfd)) {
            next if $resname eq '.' or $resname eq '..';
            $RESOURCE_MANAGER->install_resource("$dir/$resname",
                { install_method => 'copy' });
        }
        closedir($dirfd);
    }
    return;
}

sub collect_statistics {
    my ($profile, $state_cache, $statistics_file, $maintainers_ref,
        $sources_ref, $qa_list_ref)
      = @_;
    my $old_statistics;

    # For each of this maintainer's packages, add statistical information
    # about the number of each type of tag to the QA data and build the
    # packages hash used for the package index.  We only do this for the
    # maintainer packages, not the uploader packages, to avoid
    # double-counting.
    for my $maintainer (@{$maintainers_ref}) {
        for my $source (keys %{ $by_maint{$maintainer} }) {
            my %count;
            for my $version (
                sort versions_comparator
                keys %{ $by_maint{$maintainer}{$source} }){
                my $tags = $by_maint{$maintainer}{$source}{$version};
                for my $tag (@{$tags}) {
                    $count{$tag->{code}}++;
                }
                if (@$tags) {
                    $sources_ref->{$source}{$version}
                      = $tags->[0]{pkg_info}{xref};
                }
            }
            $qa_list_ref->{$source} = \%count;
        }
    }

    for my $tag ($profile->tags(1)) {
        my ($count, $overrides) = (0, 0);
        my %seen_tags;
        next if (not exists($by_tag{$tag}));
        foreach (@{$by_tag{$tag}}) {
            if ($_->{code} ne 'O') {
                $count++;
                $seen_tags{$_->{pkg_info}{xref}}++;
            } else {
                $overrides++;
            }
        }
        $tag_statistics{$tag}{'count'} = $count;
        $tag_statistics{$tag}{'overrides'} = $overrides;
        $tag_statistics{$tag}{'packages'} = scalar(keys(%seen_tags));
    }

    # Read in the old statistics file so that we can calculate deltas for
    # all of our statistics.

    if (-f $statistics_file) {
        ($old_statistics) = read_dpkg_control($statistics_file);
    }
    $statistics{'groups-known'} = scalar(keys(%{$state_cache->{'groups'}}));
    $statistics{'groups-backlog'}
      = scalar(find_backlog($LINTIAN_VERSION,$state_cache));
    my $pkgs_w_errors = 0;
    for my $group_data (values(%{$state_cache->{'groups'}})) {
        $pkgs_w_errors++
          if exists($group_data->{'processing-errors'})
          and $group_data->{'processing-errors'};
    }
    $statistics{'groups-with-errors'} = $pkgs_w_errors;

    for my $attr (@attrs) {
        my $old = $old_statistics->{$attr} || 0;
        $statistics{$attr} ||= 0;
        $delta{$attr}
          = sprintf('%d (%+d)', $statistics{$attr},$statistics{$attr} - $old);
    }

    return $old_statistics;
}

sub extract_name_and_email {
    my ($maintainer) = @_;
    my ($name, $email) = ($maintainer =~ /^(.*) <([^>]+)>/);
    $name = 'Unknown Maintainer' unless $name;
    $email = 'unknown' unless $email;
    return ($name, $email);
}

# Generate the package lists.  These are huge, so we break them into four
# separate pages.
#
# FIXME: Does anyone actually use these pages?  They're basically unreadable.
sub generate_package_index_packages {
    my ($sources_ref) = @_;

    my %list = (
        '0-9, A-F' => [],
        'G-L'      => [],
        'M-R'      => [],
        'S-Z'      => [],
    );
    for my $package (sort(keys(%{$sources_ref}))) {
        my $first = uc(substr($package, 0, 1));
        if    ($first le 'F') { push(@{ $list{'0-9, A-F'} }, $package) }
        elsif ($first le 'L') { push(@{ $list{'G-L'} },      $package) }
        elsif ($first le 'R') { push(@{ $list{'M-R'} },      $package) }
        else                  { push(@{ $list{'S-Z'} },      $package) }
    }
    my %data = (sources => $sources_ref);
    my $i = 1;
    for my $section (sort(keys(%list))) {
        $data{section} = $section;
        $data{list} = $list{$section};
        output_template("packages_$i.html", $templates{packages}, \%data);
        $i++;
    }
    return;
}

sub run_scour {
    my ($input_file, $output_file) = @_;
    run_cmd('scour', '-i',$input_file, '-o',$output_file, '-q',
        '--enable-id-stripping', '--enable-comment-stripping',
        '--shorten-ids', '--indent=none');
    return 1;
}

sub update_history_and_make_graphs {
    my ($attrs_ref, $statistics_ref, $tag_statistics_ref) = @_;
    # Update history.
    my %versions;
    my $graph_dir = "$HTML_TMP_DIR/graphs";
    my $commonf = "$graph_dir/common.gpi";
    my $unix_time = time();
    mkdir("$HISTORY_DIR")
      if (not -d "$HISTORY_DIR");
    mkdir("$HISTORY_DIR/tags")
      if (not -d "$HISTORY_DIR/tags");

    my $history_file = "$HISTORY_DIR/statistics.dat";
    my $stats = '';
    for my $attr (@{$attrs_ref}) {
        $stats .= ' ' . $statistics_ref->{$attr};
    }
    open(my $hist_fd, '+>>', $history_file);
    print {$hist_fd} "$unix_time $LINTIAN_VERSION$stats\n";

    if ($GRAPHS) {
        seek($hist_fd, 0, SEEK_SET);
        while (<$hist_fd>) {
            my @fields = split();
            $versions{$fields[1]} = $fields[0]
              if not exists $versions{$fields[1]};
        }
    }
    close($hist_fd);

    if ($GRAPHS) {
        mkdir("$graph_dir", 0777);
        mkdir("$graph_dir/tags", 0777);

        my $date_min
          = strftime('%s',
            localtime($unix_time - 3600 * 24 * $GRAPHS_RANGE_DAYS));
        my $date_max = strftime('%s', localtime($unix_time));

       # Generate loadable Gnuplot file with common variables and labels/arrows
       # for Lintian versions.
        open(my $common, '>', $commonf);
        print {$common} "history_dir='$HISTORY_DIR'\n";
        print {$common} "graph_dir='$graph_dir'\n";
        print {$common} "date_min='$date_min'\n";
        print {$common} "date_max='$date_max'\n";
        my $last_version = 0;
        for my $v (sort { $versions{$a} <=> $versions{$b} } keys %versions) {
            next unless $versions{$v} > $date_min;

            print {$common} "set arrow from '$versions{$v}',graph 0 to ",
              "'$versions{$v}',graph 1 nohead lw 0.4\n";

            # Skip label if previous release is too close; graphs can't display
            # more than ~32 labels.
            my $min_spacing = 3600 * 24 * $GRAPHS_RANGE_DAYS / 32;
            if ($versions{$v} - $last_version > $min_spacing) {
                (my $label = $v) =~ s/\-[\w\d]+$//;
                print {$common} "set label '$label' at '$versions{$v}',graph ",
                  "1.04 rotate by 90 font ',8'\n";

                $last_version = $versions{$v};
            }
        }
        close($common);

        print "Plotting global statistics...\n";
        run_cmd({ 'chdir' => $graph_dir},
            'gnuplot',"$LINTIAN_ROOT/reporting/graphs/statistics.gpi");

        if ($SCOUR_ENABLED) {
            # Do a little "rename" dance to ensure that we keep the
            # "statistics.svg"-basename without having to use a
            # subdirectory.
            rename(
                "${graph_dir}/statistics.svg",
                "${graph_dir}/_statistics-orig.svg"
            );
            run_scour(
                "${graph_dir}/_statistics-orig.svg",
                "${graph_dir}/statistics.svg"
            );
        }
        $RESOURCE_MANAGER->install_resource("${graph_dir}/statistics.svg");
    }

    my $gnuplot_fd;
    if ($GRAPHS) {
        open($gnuplot_fd, '>', "$graph_dir/call.gpi");
    }

    for my $tag (sort(keys(%{$tag_statistics_ref}))) {
        $history_file = "$HISTORY_DIR/tags/$tag.dat";
        $stats = $tag_statistics_ref->{$tag};
        open(my $tag_fd, '>>', $history_file);
        print {$tag_fd} "$unix_time $stats->{'count'} $stats->{'overrides'} "
          ."$stats->{'packages'}\n";
        close($tag_fd);
        if ($GRAPHS) {
            print {$gnuplot_fd} qq{print 'Plotting $tag statistics...'\n};
            print {$gnuplot_fd}
              qq{call '$LINTIAN_ROOT/reporting/graphs/tags.gpi' '$tag'\n};
            print {$gnuplot_fd} qq{reset\n};
        }
    }

    if ($GRAPHS) {
        my $svg_dir = "${graph_dir}/tags";
        close($gnuplot_fd);
        run_cmd({'chdir' => $graph_dir}, 'gnuplot', 'call.gpi');
        unlink($commonf);
        if ($SCOUR_ENABLED) {
            # Obvious optimization potential; run scour in parallel
            my $optimized_dir = "${graph_dir}/tags-optimized";
            mkdir($optimized_dir);
            print "Minimizing tag graphs; this may take a while ...\n";
            for my $tag (sort(keys(%{$tag_statistics_ref}))) {
                run_scour("${svg_dir}/${tag}.svg",
                    "${optimized_dir}/${tag}.svg");
            }
            $svg_dir = $optimized_dir;
        }
        for my $tag (sort(keys(%{$tag_statistics_ref}))) {
            my $graph_file = "${svg_dir}/${tag}.svg";
            $RESOURCE_MANAGER->install_resource($graph_file);
        }
        delete_dir($graph_dir);
    }
    return;
}

# Write out the QA package list.  This is a space-delimited file that contains
# the package name and then the error count, warning count, info count,
# pedantic count, experimental count, and overridden tag count.
sub write_qa_list {
    my ($qa_data) = @_;

    open(my $qa_fd, '>', "$HTML_TMP_DIR/qa-list.txt");
    for my $source (sort(keys(%{$qa_data}))) {
        print {$qa_fd} $source;
        for my $code (qw/E W I P X O/) {
            my $count = $qa_data->{$source}{$code} || 0;
            print {$qa_fd} " $count";
        }
        print {$qa_fd} "\n";
    }
    close($qa_fd);
    return;
}

# Generate a "redirect" lookup table for the webserver to power the
# "<site>/source/<source>[/<version>]" redirects.
sub generate_lookup_tables {
    my ($sources_ref) = @_;
    mkdir("$HTML_TMP_DIR/lookup-tables");
    open(my $table, '>', "$HTML_TMP_DIR/lookup-tables/source-packages");

    foreach my $source (sort(keys(%{$sources_ref}))) {
        my $first = 1;
        for my $version (
            sort versions_comparator keys %{ $sources_ref->{$source} }) {
            my $xref = $sources_ref->{$source}{$version};
            print {$table} "$source full/$xref\n" if $first;
            print {$table} "$source/$version full/$xref\n";
            $first = 0;
        }
    }

    close($table);
    return;
}

# Determine the file name for the maintainer page given a maintainer.  It
# should be <email>.html where <email> is their email address with all
# characters other than a-z A-Z 0-9 - _ . @ = + replaced with _.  Don't change
# this without coordinating with QA.
sub maintainer_url {
    my ($maintainer) = @_;
    if ($maintainer =~ m/<([^>]+)>/) {
        my $id = $1;
        $id =~ tr/a-zA-Z0-9_.@=+-/_/c;
        return "$id.html";
    } else {
        return 'unsorted.html';
    }
}

sub parse_lintian_log {
    my ($profile, $state_cache) = @_;
    # We take a lintian log file on either standard input or as the
    # first argument.  This log file contains all the tags lintian
    # found, plus N: tags with informational messages.  Ignore all the
    # N: tags and load everything else into the hashes we use for all
    # web page generation.
    #
    # We keep track of a hash from maintainer page URLs to maintainer
    # values so that we don't have two maintainers who map to the same
    # page and overwrite each other's pages.  If we find two
    # maintainers who map to the same URL, just assume that the second
    # maintainer is the same as the first (but warn about it).
    #
    # The "last_*" are optimizations to avoid computing the same
    # things over and over again when a package have multiple tags.
    my (%seen, $last_info, $last_maintainer, %unknown_member_id, $info,
        $last_pi, %map_maint);
    my %expanded_code = (
        E => 'errors',
        W => 'warnings',
        I => 'info',
        X => 'experimental',
        O => 'overridden',
        P => 'pedantic',
        C => 'classifications',
    );
    while (<>) {
        my @parts;
        chomp;
        @parts = split_tag($_);
        next unless @parts;
        my ($code, $package, $type, $version, $arch, $tag, $extra) = @parts;
        $type = 'binary' unless (defined $type);
        next
          unless ($type eq 'source' || $type eq 'binary' || $type eq 'udeb');
        # Ignore unknown tags - happens if we removed a tag that is
        # still present in the log file.
        my $tag_info = $profile->get_tag($tag, 1);
        next if not $tag_info or $tag_info->severity eq 'classification';

        # Update statistics.
        my $key = $expanded_code{$code};
        $statistics{$key}++;
        unless ($seen{"$package $type"}) {
            $statistics{"$type-packages"}++;
            $seen{"$package $type"} = 1;
        }

        # Determine the source package for this package and warn if
        # there appears to be no source package in the archive.
        # Determine the maintainer, version, and archive component.  Work
        # around a missing source package by pulling information from
        # a binary package or udeb of the same name if there is any.
        my ($source, $component, $source_version, $maintainer, $uploaders);
        my $member_id
          = "${type}:${package}/${version}"
          . ($type ne 'source' ? "/$arch" : q{});
        my $state_data = $state_cache->{'members-to-groups'}{$member_id};
        next if exists($unknown_member_id{$member_id});
        if ($type eq 'source') {
            $source = $package;
            $source_version = $version;
            if (not defined($state_data)) {
                warn "Source package ${member_id} not found in state cache!\n";
                $unknown_member_id{$member_id} = 1;
            }
        } elsif (defined($state_data)) {
            my $src_member
              = first { s/^source:// } keys(%{$state_data->{'members'}});
            if ($src_member) {
                ($source, $source_version) = split(m{/}, $src_member, 2);
            }
        } elsif (not defined($state_data)) {
            warn "Package ${member_id} not found in state-cache!\n";
            $unknown_member_id{$member_id} = 1;
        }
        $state_data //= {};
        $component = $state_data->{'mirror-metadata'}{'component'} ||= 'main';
        $maintainer = $state_data->{'mirror-metadata'}{'maintainer'}
          ||= '(unknown)';
        $uploaders = $state_data->{'mirror-metadata'}{'uploaders'};
        $source ||= '';
        $version = 'unknown'
          unless (defined($version) and length($version) > 0);
        $source_version = $version
          unless (defined($source_version) and length($source_version) > 0);

        # Sanitize, just out of paranoia.
        $package =~ tr/a-zA-Z0-9.+-/_/c;
        $source =~ tr/a-zA-Z0-9.+-/_/c;
        $version =~ tr/a-zA-Z0-9.+:~-/_/c;
        $source_version =~ tr/a-zA-Z0-9.+:~-/_/c;

        # Conditionally call html_quote if needed.  On average, 11-13% of
        # all tags (emitted on lintian.d.o) have no "extra".  That would be
        # tags like "no-upstream-changelog".
        if (defined($extra)) {
            $extra = html_quote($extra);
        } else {
            $extra = '';
        }

        # Add the tag information to our hashes.  Share the data
        # between the hashes to save space (which means we can't later
        # do destructive tricks with it).
        if (   $last_info
            && $last_pi->{type} eq $type
            && $last_pi->{package} eq $package
            && $last_pi->{version} eq $version) {

            # There are something like 622k tags emitted on lintian.d.o,
            # but only "some" 90k unique package+version(+arch) pairs.
            # Therefore, we can conclude that the average package will
            # have ~6 tags and optimise for that case.  Indeed, this path
            # seems to be taken about 90% of the time (561k/624k).
            # - In fact, we see less than "90k" package+version(+arch)
            #   pairs here, since entries without tags never this far down
            #   in this loop (i.e. they are filtered out by split_tag
            #   above).

            # Copy the last info and then change the bits that can change
            $info = {%{$last_info}};
            # Code depends on whether the given tag was overridden or not
            $info->{code} = $code;
            $info->{extra} = $extra;
            if ($info->{tag_info}->tag ne $tag) {
                $info->{tag_info} = $tag_info;
            }
            # saves a map_maintainer call
            $maintainer = $last_maintainer;
        } else {

            my $anchor = "${source}_${source_version}";
            # Apparently "+" are not allowed in ids and I am guessing
            # ":" is not either
            if (index($anchor, '+') > -1 or index($anchor, ':') > -1) {
                $anchor =~ s/[+]/_x2b/g;
                $anchor =~ s/[:]/_x3a/g;
            }
            if (substr($maintainer, 0, 1) eq q{"}) {
                # Strip out ""-quotes, which is required in d/control for some
                # maintainers.
                $maintainer =~ s/^"(.*)" <(.*)>$/$1 <$2>/;
            }

            # Check if we've seen the URL for this maintainer before
            # and, if so, map them to the same person as the previous
            # one.

            $last_maintainer = $maintainer
              = map_maintainer(\%map_maint, $maintainer);

            # Update maintainer statistics.
            $statistics{maintainers}++ unless defined $by_maint{$maintainer};

            $last_info = $info = {
                # Tag instance specific data

                # split_tags ensures that $code is a single upper case letter
                code         => $code,
                tag_info     => $tag_info,
                # extra is unsafe in general, but we already quote it above.
                extra        => $extra,

                # Shareable data
                pkg_info     => {
                    package      => $package,
                    version      => $version,
                    # There is a check for type being in a fixed whitelist of
                    # HTML-safe keywords in the start of the loop.,
                    type         => $type,
                    component    => html_quote($component),
                    # should be safe
                    anchor       => $anchor,
                    xref         => maintainer_url($maintainer). "#${anchor}",
                    'state_data' => $state_data,
                },
            };
            $last_pi = $info->{pkg_info};
            if (!$by_maint{$maintainer}{$source}{$source_version}) {
                my $list_ref = [];
                $by_maint{$maintainer}{$source}{$source_version} = $list_ref;
                # If the package had uploaders listed, also add the
                # information to %by_uploaders (still sharing the data
                # between hashes).
                if ($uploaders) {
                    for my $uploader (@{$uploaders}) {
                        if (substr($uploader, 0, 1) eq q{"}) {
                            # Strip out ""-quotes, which is required in
                            # d/control for some uploaders.
                            $uploader =~ s/^"(.*)" <(.*)>$/$1 <$2>/;
                        }
                        $uploader = map_maintainer(\%map_maint, $uploader);
                        next if $uploader eq $maintainer;
                        $by_uploader{$uploader}{$source}{$source_version}
                          = $list_ref;
                    }
                }
            }
        }

        push(@{ $by_maint{$maintainer}{$source}{$source_version} }, $info);
        $by_tag{$tag} ||= [];
        push(@{ $by_tag{$tag} }, $info);

    }
    return;
}

# Deduplicate maintainers.  Maintains a cache of the maintainers we've seen
# with a given e-mail address and returns the maintainer string that we
# should use (which is whatever maintainer we saw first with that e-mail).
sub map_maintainer {
    my ($urlmap, $maintainer) = @_;
    my $url = maintainer_url($maintainer);
    if (defined(my $res = $urlmap->{$url})) {
        $maintainer = $res;
    } else {
        $urlmap->{$url} = $maintainer;
    }
    return $maintainer;
}

# Quote special characters for HTML output.
sub html_quote {
    my ($text) = @_;
    $text ||= '';
    # Use index to do a quick check before we bother requesting a
    # subst.  On average, this is cheaper than blindly s///'ing, since
    # we rarely subst (all) of the characters below.
    if (index($text, '&') > -1) {
        $text =~ s/&/\&amp;/g;
    }
    if (index($text, '<') > -1) {
        $text =~ s/</\&lt;/g;
    }
    if (index($text, '>') > -1) {
        $text =~ s/>/\&gt;/g;
    }
    return $text;
}

# Given a file name, a template, and a data hash, fill out the template with
# that data hash and output the results to the file.
sub output_template {
    my ($file, $template, $data) = @_;
    my $path_prefix = $data->{path_prefix};
    if (not defined($path_prefix)) {
        $path_prefix = '';
        if (index($file, '/') > -1) {
            $path_prefix = '../' x ($file =~ tr|/||);
        }
    }
    $data->{version} ||= $LINTIAN_VERSION;
    $data->{timestamp} ||= $timestamp;
    $data->{by_version} ||= \&versions_comparator;
    $data->{path_prefix} ||= $path_prefix;
    $data->{html_quote} ||= \&html_quote;
    $data->{resource_path} ||= sub {
        return $path_prefix . $RESOURCE_MANAGER->resource_URL($_[0]);
    };
    $data->{resource_integrity} ||= sub {
        return $RESOURCE_MANAGER->resource_integrity_value($_[0]);
    };
    $data->{head} ||= sub {
        $templates{head}->fill_in(
            HASH => {
                page_title => $_[0],
                config_vars => $TEMPLATE_CONFIG_VARS,
                %{$data},
            }) or die "Filling out head of $file: $Text::Template::ERROR\n";
    };
    $data->{foot} ||= sub {
        $templates{foot}->fill_in(
            HASH => {
                config_vars => $TEMPLATE_CONFIG_VARS,
                %{$data},
            }) or die "Filling out footer of $file: $Text::Template::ERROR\n";
    };
    $data->{config_vars} ||= $TEMPLATE_CONFIG_VARS;
    open(my $fd, '>:encoding(UTF-8)', "$HTML_TMP_DIR/$file");
    $template->fill_in(OUTPUT => $fd, HASH => $data)
      or die "filling out $file failed: $Text::Template::ERROR\n";
    close($fd);
    return;
}

# Sort function for sorting lists of tags.  Sort by package, version, component,
# type, tag, and then any extra data.  This will produce the best HTML output.
#
# Note that source tags must come before all other tags, hence the "unfair"
# priority for those.  This is because the first tags listed are assumed to
# be source package tags.
sub by_tag {
    my $a_pi = $a->{pkg_info};
    my $b_pi = $b->{pkg_info};
    if ($a_pi->{type} ne $b_pi->{type}) {
        return -1 if $a_pi->{type} eq 'source';
        return  1 if $b_pi->{type} eq 'source';
    }
    return
         $a_pi->{package}        cmp $b_pi->{package}
      || $a_pi->{version}        cmp $b_pi->{version}
      || $a_pi->{component}      cmp $b_pi->{component}
      || $a_pi->{type}           cmp $b_pi->{type}
      || $a->{tag_info}->tag     cmp $b->{tag_info}->tag
      || $a->{extra}             cmp $b->{extra};
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
