# menu format -- lintian check script -*- perl -*-

# Copyright (C) 1998 by Joey Hess
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

# This script also checks desktop entries, since they share quite a bit of
# code.  At some point, it would make sense to try to refactor this so that
# shared code is in libraries.
#
# Further things that the desktop file validation should be checking:
#
#  - Encoding of the file should be UTF-8.
#  - Additional Categories should be associated with Main Categories.
#  - List entries (MimeType, Categories) should end with a semicolon.
#  - Check for GNOME/GTK/X11/etc. dependencies and require the relevant
#    Additional Category to be present.
#  - Check all the escape characters supported by Exec.
#  - Review desktop-file-validate to see what else we're missing.

package Lintian::menu_format;
use strict;
use warnings;
use autodie;

use File::Basename;
use List::MoreUtils qw(any);

use Lintian::Data;
use Lintian::Tags qw(tag);

# This is a list of all tags that should be in every menu item.
my @req_tags = qw(needs section title command);

# This is a list of all known tags.
my @known_tags = qw(
  needs
  section
  title
  sort
  command
  longtitle
  icon
  icon16x16
  icon32x32
  description
  hotkey
  hints
);

# These 'needs' tags are always valid, no matter the context, and no other
# values are valid outside the Window Managers context (don't include wm here,
# in other words).  It's case insensitive, use lower case here.
my @needs_tag_vals = qw(x11 text vc);

sub _menu_sections {
    my ($key, $val, $cur) = @_;
    my $ret;
    $ret = $cur = {} unless defined $cur;
    # $val is empty if this is just a root section
    $cur->{$val} = 1 if $val;
    return $ret;
}

my $MENU_SECTIONS
  = Lintian::Data->new('menu-format/menu-sections',qr|/|, \&_menu_sections);

# Authoritative source of desktop keys:
# https://specifications.freedesktop.org/desktop-entry-spec/1.1/
#
# This is a list of all keys that should be in every desktop entry.
my @req_desktop_keys = qw(Type Name);

# This is a list of all known keys.
my $KNOWN_DESKTOP_KEYS =  Lintian::Data->new('menu-format/known-desktop-keys');

my $DEPRECATED_DESKTOP_KEYS
  = Lintian::Data->new('menu-format/deprecated-desktop-keys');

# KDE uses some additional keys that should start with X-KDE but don't for
# historical reasons.
my $KDE_DESKTOP_KEYS = Lintian::Data->new('menu-format/kde-desktop-keys');

# Known types of desktop entries.
# https://specifications.freedesktop.org/desktop-entry-spec/1.1/ar01s05.html
my %known_desktop_types = map { $_ => 1 } qw(
  Application
  Link
  Directory
);

# Authoritative source of desktop categories:
# https://specifications.freedesktop.org/menu-spec/1.1/apa.html

# This is a list of all Main Categories for .desktop files.  Application is
# added as an exception; it's not listed in the standard, but it's widely used
# and used as an example in the GNOME documentation.  GNUstep is added as an
# exception since it's used by GNUstep packages.
my %main_categories = map { $_ => 1 } qw(
  AudioVideo
  Audio
  Video
  Development
  Education
  Game
  Graphics
  Network
  Office
  Science
  Settings
  System
  Utility
  Application
  GNUstep
);

# This is a list of all Additional Categories for .desktop files.  Ideally we
# should be checking to be sure the associated Main Categories are present,
# but we don't have support for that yet.
my $ADD_CATEGORIES = Lintian::Data->new('menu-format/add-categories');

# This is a list of Reserved Categories for .desktop files.  To use one of
# these, the desktop entry must also have an OnlyShowIn key limiting the
# environment to one that supports this category.
my %reserved_categories = map { $_ => 1 } qw(
  Screensaver
  TrayIcon
  Applet
  Shell
);

# Path in which to search for binaries referenced in menu entries.  These must
# not have leading slashes.
my @path = qw(usr/local/bin/ usr/bin/ bin/ usr/games/);

my %known_tags_hash = map { $_ => 1 } @known_tags;
my %needs_tag_vals_hash = map { $_ => 1 } @needs_tag_vals;

# -----------------------------------

sub run {
    my ($pkg, $type, $info, $proc, $group) = @_;
    my (@menufiles, %desktop_cmds);
    for my $dirname (qw(usr/share/menu/ usr/lib/menu/)) {
        if (my $dir = $info->index_resolved_path($dirname)) {
            push(@menufiles, $dir->children);
        }
    }

    # Find the desktop files in the package for verification.
    my @desktop_files;
    for my $subdir (qw(applications xsessions)) {
        if (my $dir = $info->index("usr/share/$subdir/")) {
            for my $file ($dir->children) {
                next unless $file->is_file;
                next unless $file->basename =~ m/\.desktop$/;
                if ($file->is_executable) {
                    tag 'executable-desktop-file',
                      sprintf('%s %04o',$file, $file->operm);
                }
                if (index($file, 'template') == -1) {
                    push(@desktop_files, $file);
                }
            }
        }
    }

    # Verify all the desktop files.
    for my $desktop_file (@desktop_files) {
        verify_desktop_file($desktop_file, $pkg, $info, \%desktop_cmds);
    }

    # Now all the menu files.
    foreach my $menufile (@menufiles) {
        # Do not try to parse executables
        next if $menufile->is_executable or not $menufile->is_open_ok;

        my $fullname = $menufile->name;

        # README is a special case
        next if $menufile->basename eq 'README';
        my $menufile_line ='';
        my $fd = $menufile->open;
        # line below is commented out in favour of the while loop
        # do { $_=<IN>; } while defined && (m/^\s* \#/ || m/^\s*$/);
        while (<$fd>) {
            if (m/^\s*\#/ || m/^\s*$/) {
                next;
            } else {
                $menufile_line = $_;
                last;
            }
        }

        # Check first line of file to see if it matches the old menu
        # file format.
        if ($menufile_line =~ m/^(?!\?package\(.*\)).* .* .* .* "?.*"? .*$/o) {
            tag 'old-format-menu-file', $fullname;
            close($fd);
            next;
        } elsif ($menufile_line =~ m/^!C\s*menu-2/o) {
            # we can't parse that yet
            close($fd);
            next;
        }

        # Parse entire file as a new format menu file.
        my $line='';
        my $lc=0;
        do {
            $lc++;

            # Ignore lines that are comments.
            if ($menufile_line =~ m/^\s*\#/o) {
                next;
            }
            $line .= $menufile_line;
            # Note that I allow whitespace after the continuation character.
            # This is caught by verify_line().
            if (!($menufile_line =~ m/\\\s*?$/)) {
                verify_line(
                    $pkg, $info, $proc, $group,
                    $type,$menufile, $fullname, $line,
                    $lc,\%desktop_cmds
                );
                $line='';
            }
        } while ($menufile_line = <$fd>);
        verify_line(
            $pkg, $info, $proc, $group,
            $type,$menufile, $fullname, $line,
            $lc,\%desktop_cmds
        );

        close($fd);
    }

    return;
}

# -----------------------------------

# Pass this a line of a menu file, it sanitizes it and
# verifies that it is correct.
sub verify_line {
    my (
        $pkg, $info, $proc, $group, $type,
        $menufile, $fullname, $line, $linecount,$desktop_cmds
    ) = @_;

    my %vals;

    chomp $line;

    # Replace all line continuation characters with whitespace.
    # (do not remove them completely, because update-menus doesn't)
    $line =~ s/\\\n/ /mgo;

    # This is in here to fix a common mistake: whitespace after a '\'
    # character.
    if ($line =~ s/\\\s+\n/ /mgo) {
        tag 'whitespace-after-continuation-character', "$fullname:$linecount";
    }

    # Ignore lines that are all whitespace or empty.
    return if $line =~ m/^\s*$/o;

    # Ignore lines that are comments.
    return if $line =~ m/^\s*\#/o;

    # Start by testing the package check.
    if (not $line =~ m/^\?package\((.*?)\):/o) {
        tag 'bad-test-in-menu-item', "$fullname:$linecount";
        return;
    }
    my $pkg_test = $1;
    my %tested_packages = map { $_ => 1 } split(/\s*,\s*/, $pkg_test);
    my $tested_packages = scalar keys %tested_packages;
    unless (exists $tested_packages{$pkg}) {
        tag 'pkg-not-in-package-test', "$pkg_test $fullname";
    }
    $line =~ s/^\?package\(.*?\)://;

    # Now collect all the tag=value pairs. I've heavily commented
    # the killer regexp that's responsible.
    #
    # The basic idea here is we start at the beginning of the line.
    # Each loop pulls off one tag=value pair and advances to the next
    # when we have no more matches, there should be no text left on
    # the line - if there is, it's a parse error.
    while (
        $line =~ m/
           \s*?                 # allow whitespace between pairs
           (                    # capture what follows in $1, it's our tag
            [^\"\s=]            # a non-quote, non-whitespace, character
            *                   # match as many as we can
           )
           =
           (                    # capture what follows in $2, it's our value
            (?:
             \"                 # this is a quoted string
             (?:
              \\.               # any quoted character
              |                 # or
              [^\"]             # a non-quote character
             )
             *                  # repeat as many times as possible
             \"                 # end of the quoted value string
            )
            |                   # the other possibility is a non-quoted string
            (?:
             [^\"\s]            # a non-quote, non-whitespace character
             *                  # match as many times as we can
            )
           )
           /ogcx
      ) {
        my $tag = $1;
        my $value = $2;

        if (exists $vals{$tag}) {
            tag 'duplicated-tag-in-menu-item', "$fullname $1:$linecount";
        }

        # If the value was quoted, remove those quotes.
        if ($value =~ m/^\"(.*)\"$/) {
            $value = $1;
        } else {
            tag 'unquoted-string-in-menu-item', "$fullname $1:$linecount";
        }

        # If the value has escaped characters, remove the
        # escapes.
        $value =~ s/\\(.)/$1/g;

        $vals{$tag} = $value;
    }

    # This is not really a no-op. Note the use of the /c
    # switch - this makes perl keep track of the current
    # search position. Notice, we did it above in the loop,
    # too. (I have a /g here just so the /c takes affect.)
    # We use this below when we look at how far along in the
    # string we matched. So the point of this line is to allow
    # trailing whitespace on the end of a line.
    $line =~ m/\s*/ogc;

    # If that loop didn't match up to end of line, we have a
    # problem..
    if (pos($line) < length($line)) {
        tag 'unparsable-menu-item', "$fullname:$linecount";
        # Give up now, before things just blow up in our face.
        return;
    }

    # Now validate the data in the menu file.

    # Test for important tags.
    foreach my $tag (@req_tags) {
        unless (exists($vals{$tag}) && defined($vals{$tag})) {
            tag 'menu-item-missing-required-tag', "$tag $fullname:$linecount";
            # Just give up right away, if such an essential tag is missing,
            # chance is high the rest doesn't make sense either. And now all
            # following checks can assume those tags to be there
            return;
        }
    }

    # Make sure all tags are known.
    foreach my $tag (keys %vals) {
        if (!$known_tags_hash{$tag}) {
            tag 'menu-item-contains-unknown-tag', "$tag $fullname:$linecount";
        }
    }

    # Sanitize the section tag
    my $section = $vals{'section'};
    $section =~ tr:/:/:s;       # eliminate duplicate slashes. # Hallo emacs ;;
    $section =~ s:/$::          # remove trailing slash
      unless $section eq '/'; # - except if $section is '/'

    # Be sure the command is provided by the package.
    my ($okay, $command)
      = verify_cmd($fullname, $linecount, $vals{'command'},$pkg, $info);
    tag 'menu-command-not-in-package', "$fullname:$linecount $command"
      unless ($okay
        or not $command
        or ($tested_packages >= 2)
        or
        ($section =~ m:^(WindowManagers/Modules|FVWM Modules|Window Maker):));

    if (defined($command)) {
        $command =~ s@^(?:usr/)?s?bin/@@;
        if ($desktop_cmds->{$command}) {
            tag 'command-in-menu-file-and-desktop-file', $command,
              "${fullname}:${linecount}";
        }
    }

    if (exists($vals{'icon'})) {
        verify_icon($info, $proc, $group, $menufile, $fullname, $linecount,
            $vals{'icon'}, 32);
    }
    if (exists($vals{'icon32x32'})) {
        verify_icon($info, $proc, $group, $menufile, $fullname, $linecount,
            $vals{'icon32x32'}, 32);
    }
    if (exists($vals{'icon16x16'})) {
        verify_icon($info, $proc, $group, $menufile, $fullname, $linecount,
            $vals{'icon16x16'}, 16);
    }

    # Check the needs tag.
    my $needs = lc($vals{'needs'}); # needs is case insensitive.

    if ($section =~ m:^(WindowManagers/Modules|FVWM Modules|Window Maker):) {
        # WM/Modules: needs must not be the regular ones nor wm
        if ($needs_tag_vals_hash{$needs} or $needs eq 'wm') {
            tag 'non-wm-module-in-wm-modules-menu-section',
              "$needs $fullname:$linecount";
        }
    } elsif ($section =~ m:^Window ?Managers:) {
        # Other WM sections: needs must be wm
        if ($needs ne 'wm') {
            tag 'non-wm-in-windowmanager-menu-section',
              "$needs $fullname:$linecount";
        }
    } else {
        # Any other section: just only the general ones
        if ($needs eq 'dwww') {
            tag 'menu-item-needs-dwww', "$fullname:$linecount";
        } elsif (not $needs_tag_vals_hash{$needs}) {
            tag 'menu-item-needs-tag-has-unknown-value',
              "$needs $fullname:$linecount";
        }
    }

    # Check the section tag
    # Check for historical changes in the section tree.
    if ($section =~ m:^Apps/Games:) {
        tag 'menu-item-uses-apps-games-section', "$fullname:$linecount";
        $section =~ s:^Apps/::;
    }
    if ($section =~ m:^Apps/:) {
        tag 'menu-item-uses-apps-section', "$fullname:$linecount";
        $section =~ s:^Apps/:Applications/:;
    }
    if ($section =~ m:^WindowManagers:) {
        tag 'menu-item-uses-windowmanagers-section', "$fullname:$linecount";
        $section =~ s:^WindowManagers:Window Managers:;
    }

    # Check for Evil new root sections.
    my ($rootsec, $sect) = split m:/:, $section, 2;
    my $root_data = $MENU_SECTIONS->value($rootsec);
    if (not defined $root_data) {
        if (not $rootsec =~ m/$pkg/i) {
            tag 'menu-item-creates-new-root-section',
              "$rootsec $fullname:$linecount";
        }
    } else {
        my $ok = 1;
        if ($sect) {
            # Using unknown subsection of $rootsec?
            $ok = 0 if not exists $root_data->{$sect};
        } else {
            # Using root menu when a subsection exists?
            $ok = 0 if %$root_data;
        }
        unless ($ok) {
            tag 'menu-item-creates-new-section',
              "$vals{section} $fullname:$linecount";
        }
    }
    return;
}

sub verify_icon {
    my ($info, $proc, $group, $menufile, $fullname, $linecount, $icon, $size)
      = @_;

    if ($icon eq 'none') {
        tag 'menu-item-uses-icon-none', "$fullname:$linecount";
        return;
    }

    tag 'menu-icon-uses-relative-path', $icon
      unless $icon =~ m,^/,;

    $icon =~ s|^/*||og;

    if (not($icon =~ m/\.xpm$/i)) {
        tag 'menu-icon-not-in-xpm-format', $icon;
        return;
    }

    # Try the explicit location, and if that fails, try the standard path.
    my $iconfile = $info->index_resolved_path($icon);
    if (not $iconfile) {
        $iconfile = $info->index_resolved_path("usr/share/pixmaps/$icon");
        if (not $iconfile) {
            my $ginfo = $group->info;
            foreach my $depproc (@{ $ginfo->direct_dependencies($proc) }) {
                my $dinfo = $depproc->info;
                $iconfile = $dinfo->index_resolved_path($icon);
                last if $iconfile;
                $iconfile
                  = $dinfo->index_resolved_path("usr/share/pixmaps/$icon");
                last if $iconfile;
            }
        }
    }

    if (not $iconfile or not $iconfile->is_open_ok) {
        tag 'menu-icon-missing', $icon;
        return;
    }

    my $parse = 'XPM header';
    my $line;

    my $fd = $iconfile->open;

    do { defined($line = <$fd>) or goto parse_error; }
      until ($line =~ /\/\*\s*XPM\s*\*\//);

    $parse = 'size line';
    do { defined($line = <$fd>) or goto parse_error; }
      until ($line =~ /"\s*([0-9]+)\s*([0-9]+)\s*(?:[0-9]+)\s*(?:[0-9]+)\s*"/);
    my $width = $1 + 0;
    my $height = $2 + 0;

    if ($width > $size || $height > $size) {
        tag 'menu-icon-too-big', "$icon: ${width}x${height} > ${size}x${size}";
    }

    close($fd);
    return;

  parse_error:
    close($fd);
    tag 'menu-icon-cannot-be-parsed', "$icon: looking for $parse";
    return;
}

# Syntax-checks a .desktop file.
sub verify_desktop_file {
    my ($file, $pkg, $info, $desktop_cmds) = @_;
    my ($saw_first, $warned_cr, %vals, @pending);
    my $fd = $file->open;
    while (my $line = <$fd>) {
        chomp $line;
        next if ($line =~ m/^\s*\#/ or $line =~ m/^\s*$/);
        if ($line =~ s/\r//) {
            tag 'desktop-entry-file-has-crs', "$file:$." unless $warned_cr;
            $warned_cr = 1;
        }

        # Err on the side of caution for now.  If the first non-comment line
        # is not the required [Desktop Entry] group, ignore this file.  Also
        # ignore any keys in other groups.
        last if ($saw_first and $line =~ /^\[(.*)\]\s*$/);
        unless ($saw_first) {
            return unless $line =~ /^\[(KDE )?Desktop Entry\]\s*$/;
            $saw_first = 1;
            tag 'desktop-contains-deprecated-key', "$file:$."
              if ($line =~ /^\[KDE Desktop Entry\]\s*$/);
        }

        # Tag = Value.  For most errors, just add the error to pending rather
        # than warning on it immediately since we want to not warn on tag
        # errors if we didn't know the file type.
        #
        # TODO: We do not check for properly formatted localised values for
        # keys but might be worth checking if they are properly formatted (not
        # their value)
        if ($line =~ /^(.*?)\s*=\s*(.*)$/) {
            my ($tag, $value) = ($1, $2);
            my $basetag = $tag;
            $basetag =~ s/\[([^\]]+)\]$//;
            if (exists $vals{$tag}) {
                tag 'duplicated-key-in-desktop-entry', "$file:$. $tag";
            } elsif ($DEPRECATED_DESKTOP_KEYS->known($basetag)) {
                if ($basetag eq 'Encoding') {
                    push(
                        @pending,
                        [
                            'desktop-entry-contains-encoding-key',
                            "$file:$. $tag"
                        ]);
                } else {
                    push(
                        @pending,
                        [
                            'desktop-entry-contains-deprecated-key',
                            "$file:$. $tag"
                        ]);
                }
            } elsif (not $KNOWN_DESKTOP_KEYS->known($basetag)
                and not $KDE_DESKTOP_KEYS->known($basetag)
                and not $basetag =~ /^X-/) {
                push(@pending,
                    ['desktop-entry-contains-unknown-key', "$file:$. $tag"]);
            }
            $vals{$tag} = $value;
        }
    }
    close($fd);

    # Now validate the data in the desktop file, but only if it's a known type.
    return unless ($vals{'Type'} and $known_desktop_types{$vals{'Type'}});

    # Now we can issue any pending tags.
    for my $pending (@pending) {
        tag @$pending;
    }

    # Test for important keys.
    for my $tag (@req_desktop_keys) {
        unless (defined $vals{$tag}) {
            tag 'desktop-entry-missing-required-key', "$file $tag";
        }
    }

    # test if missing Keywords (only if NoDisplay is not set)
    if (!defined $vals{NoDisplay}) {
        if (!defined $vals{Icon}) {
            tag 'desktop-entry-lacks-icon-entry', $file;
        }
        if (!defined $vals{Keywords} && $vals{'Type'} eq 'Application') {
            tag 'desktop-entry-lacks-keywords-entry', $file;
        }
    }

    # Only test whether the binary is in the package if the desktop file is
    # directly under /usr/share/applications.  Too many applications use
    # desktop files for other purposes with custom paths.
    #
    # TODO:  Should check quoting and the check special field
    # codes in Exec for desktop files.
    if (    $file =~ m,^usr/share/applications/,
        and $vals{'Exec'}
        and $vals{'Exec'} =~ /\S/) {
        my ($okay, $command)
          = verify_cmd($file->name, undef, $vals{'Exec'}, $pkg,$info);
        tag 'desktop-command-not-in-package', $file, $command
          unless $okay
          or $command eq 'kcmshell';
        $command =~ s@^(?:usr/)?s?bin/@@;
        $desktop_cmds->{$command} = 1
          if $command !~ m/^(?:su-to-root|sux?|(?:gk|kde)su)$/;
    }

    # Check the Category tag.
    my $in_reserved;
    if (defined $vals{'Categories'}) {
        my @cats = split(';', $vals{'Categories'});
        my $saw_main;
        for my $cat (@cats) {
            next if $cat =~ /^X-/;
            if ($reserved_categories{$cat}) {
                tag 'desktop-entry-uses-reserved-category', "$cat $file"
                  unless $vals{'OnlyShowIn'};
                $saw_main = 1;
                $in_reserved = 1;
            } elsif (not $ADD_CATEGORIES->known($cat)
                and not $main_categories{$cat}) {
                tag 'desktop-entry-invalid-category', "$cat $file";
            } elsif ($main_categories{$cat}) {
                $saw_main = 1;
            }
        }
        unless ($saw_main) {
            tag 'desktop-entry-lacks-main-category', $file;
        }
    }

    # Check the OnlyShowIn tag.  If this is not an application in a reserved
    # category, warn about any desktop entry that specifies OnlyShowIn for
    # more than one environment.  In that case, the application probably
    # should be using NotShowIn instead.
    if (defined $vals{OnlyShowIn} and not $in_reserved) {
        my @envs = split(';', $vals{OnlyShowIn});
        if (@envs > 1) {
            tag 'desktop-entry-limited-to-environments', $file;
        }
    }

    # Check that the Exec tag specifies how to pass a filename if MimeType
    # tags are present.
    if ($file =~ m,^usr/share/applications/, and defined $vals{'MimeType'}) {
        unless(defined $vals{'Exec'}
            and $vals{'Exec'} =~ m,(?:^|[^%])%[fFuU],){
            tag 'desktop-mime-but-no-exec-code', $file;
        }
    }

    return;
}

# Verify whether a command is shipped as part of the package.  Takes the full
# path to the file being checked (for error reporting) and the binary.
# Returns a list whose first member is true if the command is present and
# false otherwise, and whose second member is the command (minus any leading
# su-to-root wrapper).  Shared between the desktop and menu code.
sub verify_cmd {
    my ($file, $line, $exec, $pkg, $info) = @_;
    my $location = ($line ? "$file:$line" : $file);

    # This routine handles su wrappers.  The option parsing here is ugly and
    # dead-simple, but it's hopefully good enough for what will show up in
    # desktop files.  su-to-root and sux require -c options, kdesu optionally
    # allows one, and gksu has the command at the end of its arguments.
    my @com = split(' ', $exec);
    my $cmd;
    if ($com[0] and $com[0] eq '/usr/sbin/su-to-root') {
        tag 'su-to-root-with-usr-sbin', $location;
    }
    if (    $com[0]
        and $com[0] =~ m,^(?:/usr/s?bin/)?(su-to-root|gksu|kdesu|sux)$,) {
        my $wrapper = $1;
        shift @com;
        while (@com) {
            unless ($com[0]) {
                shift @com;
                next;
            }
            if ($com[0] eq '-c') {
                $cmd = $com[1];
                last;
            } elsif ($com[0] =~ /^-[Dfmupi]|^--(user|description|message)/) {
                shift @com;
                shift @com;
            } elsif ($com[0] =~ /^-/) {
                shift @com;
            } else {
                last;
            }
        }
        if (!$cmd && $wrapper =~ /^(gk|kde)su$/) {
            if (@com) {
                $cmd = $com[0];
            } else {
                $cmd = $wrapper;
                undef $wrapper;
            }
        }
        tag 'su-wrapper-without--c', "$location $wrapper" unless $cmd;
        if ($wrapper && $wrapper !~ /su-to-root/ && $wrapper ne $pkg) {
            tag 'su-wrapper-not-su-to-root', "$location $wrapper";
        }
    } else {
        $cmd = $com[0];
    }
    my $cmd_file = $cmd;
    if ($cmd_file) {
        $cmd_file =~ s,^/,,;
    }
    my $okay = $cmd
      && ( $cmd =~ /^[\'\"]/
        || $info->index($cmd_file)
        || $cmd =~ m,^(/bin/)?sh,
        || $cmd =~ m,^(/usr/bin/)?sensible-(pager|editor|browser),
        || any { $info->index($_ . $cmd) } @path);
    return ($okay, $cmd_file);
}

1;

# Local Variables:
# indent-tabs-mode: nil
# cperl-indent-level: 4
# End:
# vim: syntax=perl sw=4 sts=4 sr et
