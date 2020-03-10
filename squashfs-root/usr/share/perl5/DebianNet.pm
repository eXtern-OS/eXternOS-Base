# DebianNet.pm: a perl module to add entries to the /etc/inetd.conf file
#
# Copyright (C) 1995, 1996 Peter Tobias <tobias@et-inf.fho-emden.de>
#                          Ian Jackson <iwj10@cus.cam.ac.uk>
# Copyright (C) 2009-2012  Serafeim Zanikolas <sez@debian.org>
#
#
# DebianNet::add_service($newentry, $group);
# DebianNet::disable_service($service, $pattern);
# DebianNet::enable_service($service, $pattern);
# DebianNet::remove_service($entry);
#

package DebianNet;

require 5.6.1;

use Debconf::Client::ConfModule ':all';

BEGIN {
    eval 'use File::Temp qw/ tempfile /';
    if ($@) {
        # If perl-base and perl-modules are out of sync, fall back to the
        # external 'tempfile' command.  In this case we don't bother trying
        # to mangle the template we're given into something that tempfile
        # can understand.
        sub tempfile {
            open my $tempfile_fh, '-|', 'tempfile'
                or die "Error running tempfile: $!";
            chomp (my $tempfile_name = <$tempfile_fh>);
            unless (length $tempfile_name) {
                die "tempfile did not return a temporary file name";
            }
            unless (close $tempfile_fh) {
                if ($!) {
                    die "Error closing tempfile pipe: $!";
                } else {
                    die "tempfile returned exit status $?";
                }
            }
            open my $fh, '+<', $tempfile_name
                or die "Error opening temporary file $tempfile_name: $!";
            return ($fh, $tempfile_name);
        }
    }

    eval 'use File::Copy qw/ move /';
    if ($@) {
        # If perl-base and perl-modules are out of sync, fall back to the
        # external 'mv' command.
        sub move {
            my ($from, $to) = @_;
            return system('mv', $from, $to) == 0;
        }
    }
}

$inetdcf="/etc/inetd.conf";
$sep = "#<off># ";
$version = "1.12";
$called_wakeup_inetd = 0;

sub add_service {
    local($newentry, $group) = @_;
    local($service, $searchentry, @inetd, $inetdconf, $found, $success);
    unless (defined($newentry)) { return(-1) };
    chomp($newentry);
    if (defined $group) {
        chomp($group);
    } else {
        $group = "OTHER";
    }
    $group =~ tr/a-z/A-Z/;
    $newentry =~ s/\\t/\t/g;
    ($service = $newentry) =~ s/(\W*\w+)\s+.*/$1/;
    ($sservice = $service) =~ s/^#([A-Za-z].*)/$1/;
    ($searchentry = $newentry) =~ s/^$sep//;
    $searchentry =~ s/^#([A-Za-z].*)/$1/;

    # strip parameter from entry (e.g. -s /tftpboot)
    # example:          service dgram udp     wait    root    /tcpd /prg   -s /tftpboot";
    $searchentry =~ s/^(\w\S+\W+\w+\W+\w\S+\W+\w\S+\W+\w\S+\W+\S+\W+\S+).*/$1/;
    $searchentry =~ s/[ \t]+/ /g;
    $searchentry =~ s/ /\\s+/g;
    $searchentry =~ s@\\s\+/\S+\\s\+/\S+@\\s\+\\S\+\\s\+\\S\+@g;

    if (open(INETDCONF,"$inetdcf")) {
        @inetd=<INETDCONF>;
        close(INETDCONF);
        if (grep(m/^$sep$sservice\s+/,@inetd)) {
            &enable_service($sservice);
        } else {
            if (grep(m/^$sservice\s+/,@inetd)) {
                if (grep(m/^$sservice\s+/,@inetd) > 1) {
                    set("update-inetd/ask-several-entries", "true");
                    fset("update-inetd/ask-several-entries", "seen", "false");
                    settitle("update-inetd/title");
                    subst("update-inetd/ask-several-entries", "service", "$sservice");
                    subst("update-inetd/ask-several-entries", "sservice", "$sservice");
                    subst("update-inetd/ask-several-entries", "inetdcf", "$inetdcf");
                    input("high", "update-inetd/ask-several-entries");
                    @ret = go();
                    if ($ret[0] == 0) {
                        @ret = get("update-inetd/ask-several-entries");
                        exit(1) if ($ret[1] !~ m/true/i);
                    }
                } elsif (!grep(m:^#?.*$searchentry.*:, @inetd)) {
                    set("update-inetd/ask-entry-present", "true");
                    fset("update-inetd/ask-entry-present", "seen", "false");
                    settitle("update-inetd/title");
                    subst("update-inetd/ask-entry-present", "service", "$sservice");
                    subst("update-inetd/ask-entry-present", "newentry", "$newentry");
                    subst("update-inetd/ask-entry-present", "sservice", "$sservice");
                    subst("update-inetd/ask-entry-present", "inetdcf", "$inetdcf");
                    my $lookslike = (grep(m/^$sservice\s+/,@inetd))[0];
                    $lookslike =~ s/\n//g;
                    subst("update-inetd/ask-entry-present", "lookslike", "$lookslike");
                    input("high", "update-inetd/ask-entry-present");
                    @ret = go();
                    if ($ret[0] == 0) {
                        @ret = get("update-inetd/ask-entry-present");
                        exit(1) if ($ret[1] !~ m/true/i);
                    }
                }
            } elsif (grep(m/^#\s*$sservice\s+/, @inetd) >= 1 or
              (($service =~ s/^#//) and grep(m/^$service\s+/, @inetd)>=1)) {
                print STDERR "Processing service \`$service' ... not enabled"
                      . " (entry is commented out by user)\n";
            } else {
                &printv("Processing service \`$sservice' ... added\n");
                $inetdconf=1;
            }
        }
        if ($inetdconf) {
            my $init_svc_count = &scan_entries();
            &printv("Number of currently enabled services: $init_svc_count\n");
            my ($ICWRITE, $new_inetdcf) = tempfile("/tmp/inetdcfXXXXX", UNLINK => 0);
            unless (defined($ICWRITE)) { die "Error creating temporary file: $!\n" }
            &printv("Using tempfile $new_inetdcf\n");
            open(ICREAD, "$inetdcf");
            while(<ICREAD>) {
                chomp;
                if (/^#:$group:/) {
                    $found = 1;
                };
                if ($found and !(/[a-zA-Z#]/)) {
                    print ($ICWRITE "$newentry\n")
                        || die "Error writing to $new_inetdcf: $!\n";
                    $found = 0;
                    $success = 1;
                }
                print $ICWRITE "$_\n";
            }
            close(ICREAD);
            unless ($success) {
                print ($ICWRITE "$newentry\n")
                    || die "Error writing to $new_inetdcf: $!\n";
                $success = 1;
            }
            close($ICWRITE) || die "Error closing $new_inetdcf: $!\n";

            if ($success) {
                move("$new_inetdcf","$inetdcf") ||
                    die "Error installing $new_inetdcf to $inetdcf: $!\n";
                chmod(0644, "$inetdcf");
                &wakeup_inetd(0,$init_svc_count);
                &printv("New service(s) added\n");
            } else {
                &printv("No service(s) added\n");
                unlink("$new_inetdcf")
                    || die "Error removing $new_inetdcf: $!\n";
            }
        } else {
            &printv("No service(s) added\n");
        }
    }

    return(1);
}

sub remove_service {
    my($service, $pattern) = @_;
    chomp($service);
    my $nlines_removed = 0;
    if($service eq "") {
         print STDERR "DebianNet::remove_service called with empty argument\n";
         return(-1);
    }
    unless (defined($pattern)) { $pattern = ''; }

    if (((&scan_entries("$service", $pattern) > 1) or (&scan_entries("$sep$service", $pattern) > 1))
        and (not defined($multi))) {
        set("update-inetd/ask-remove-entries", "false");
        fset("update-inetd/ask-remove-entries", "seen", "false");
            settitle("update-inetd/title");
        subst("update-inetd/ask-remove-entries", "service", "$service");
        subst("update-inetd/ask-remove-entries", "inetdcf", "$inetdcf");
        input("high", "update-inetd/ask-remove-entries");
        @ret = go();
        if ($ret[0] == 0) {
            @ret = get("update-inetd/ask-remove-entries");
            return(1) if ($ret[1] =~ /false/i);
        }
    }

    my ($ICWRITE, $new_inetdcf) = tempfile("/tmp/inetdcfXXXXX", UNLINK => 0);
    unless (defined($ICWRITE)) { die "Error creating temporary file: $!\n" }
    &printv("Using tempfile $new_inetdcf\n");
    open(ICREAD, "$inetdcf");
    RLOOP: while(<ICREAD>) {
        chomp;
        if (not((/^$service\s+/ or /^$sep$service\s+/) and /$pattern/)) {
            print $ICWRITE "$_\n";
        } else {
            &printv("Removing line: \`$_'\n");
            $nlines_removed += 1;
        }
    }
    close(ICREAD);
    close($ICWRITE);

    if ($nlines_removed > 0) {
        move("$new_inetdcf", "$inetdcf") ||
            die "Error installing $new_inetdcf to $inetdcf: $!\n";
        chmod(0644, "$inetdcf");
        wakeup_inetd(1);
        &printv("Number of service entries removed: $nlines_removed\n");
    } else {
        &printv("No service entries were removed\n");
        unlink("$new_inetdcf") || die "Error removing $new_inetdcf: $!\n";
    }

    return(1);
}

sub disable_service {
    my($service, $pattern) = @_;
    unless (defined($service)) { return(-1) };
    unless (defined($pattern)) { $pattern = ''; }
    chomp($service);
    my $nlines_disabled = 0;

    if ((&scan_entries("$service", $pattern) > 1) and (not defined($multi))) {
        set("update-inetd/ask-disable-entries", "false");
        fset("update-inetd/ask-disable-entries", "seen", "false");
            settitle("update-inetd/title");
        subst("update-inetd/ask-disable-entries", "service", "$service");
        subst("update-inetd/ask-disable-entries", "inetdcf", "$inetdcf");
        input("high", "update-inetd/ask-disable-entries");
        @ret = go();
        if ($ret[0] == 0) {
            @ret = get("update-inetd/ask-disable-entries");
            return(1) if ($ret[1] =~ /false/i);
        }
    }

    my ($ICWRITE, $new_inetdcf) = tempfile("/tmp/inetdcfXXXXX", UNLINK => 0);
    unless (defined($ICWRITE)) { die "Error creating temporary file: $!\n" }
    &printv("Using tempfile $new_inetdcf\n");
    open(ICREAD, "$inetdcf");
    DLOOP: while(<ICREAD>) {
      chomp;
      if (/^$service\s+\w+\s+/ and /$pattern/) {
          &printv("Processing service \`$service' ... disabled\n");
          $_ =~ s/^(.+)$/$sep$1/;
          $nlines_disabled += 1;
      }
      print $ICWRITE "$_\n";
    }
    close(ICREAD);
    close($ICWRITE) || die "Error closing $new_inetdcf: $!\n";

    if ($nlines_disabled > 0) {
        move("$new_inetdcf","$inetdcf") ||
            die "Error installing new $inetdcf: $!\n";
        chmod(0644, "$inetdcf");
        wakeup_inetd(1);
        &printv("Number of service entries disabled: $nlines_disabled\n");
    } else {
        &printv("No service entries were disabled\n");
        unlink("$new_inetdcf") || die "Error removing $new_inetdcf: $!\n";
    }

    return(1);
}

sub enable_service {
    my($service, $pattern) = @_;
    unless (defined($service)) { return(-1) };
    unless (defined($pattern)) { $pattern = ''; }
    my $init_svc_count = &scan_entries();
    my $nlines_enabled = 0;
    chomp($service);
    my ($ICWRITE, $new_inetdcf) = tempfile("/tmp/inetdXXXXX", UNLINK => 0);
    unless (defined($ICWRITE)) { die "Error creating temporary file: $!\n" }
    &printv("Using tempfile $new_inetdcf\n");
    open(ICREAD, "$inetdcf");
    while(<ICREAD>) {
      chomp;
      if (/^$sep$service\s+\w+\s+/ and /$pattern/) {
          &printv("Processing service \`$service' ... enabled\n");
          $_ =~ s/^$sep//;
          $nlines_enabled += 1;
      }
      print $ICWRITE "$_\n";
    }
    close(ICREAD);
    close($ICWRITE) || die "Error closing $new_inetdcf: $!\n";

    if ($nlines_enabled > 0) {
        move("$new_inetdcf","$inetdcf") ||
            die "Error installing $new_inetdcf to $inetdcf: $!\n";
        chmod(0644, "$inetdcf");
        &wakeup_inetd(0,$init_svc_count);
        &printv("Number of service entries enabled: $nlines_enabled\n");
    } else {
        &printv("No service entries were enabled\n");
        unlink("$new_inetdcf") || die "Error removing $new_inetdcf: $!\n";
    }

    return(1);
}

sub wakeup_inetd {
    my($removal,$init_svc_count) = @_;
    my($pid);
    my($action);

    $called_wakeup_inetd = 1;

    if ($removal) {
        $action = 'force-reload';
    } elsif ( defined($init_svc_count) and $init_svc_count == 0 ) {
        $action = 'start';
    } else {
        $action = 'restart';
    }

    $fake_invocation = defined($ENV{"UPDATE_INETD_FAKE_IT"});
    if (open(P,"/var/run/inetd.pid")) {
        $pid=<P>;
        chomp($pid);
        if (open(C,sprintf("/proc/%d/stat",$pid))) {
            $_=<C>;
            if (m/^\d+ \((rl|inetutils-)?inetd\)/) {
                &printv("About to send SIGHUP to inetd (pid: $pid)\n");
                unless ($fake_invocation) {
                    kill(1,$pid);
                }
            } else {
                print STDERR "/var/run/inetd.pid does not have a valid pid!";
                print STDERR "Please investigate and restart inetd manually.";
            }
            close(C);
        }
        close(P);
    } else {
        $_ = glob "/etc/init.d/*inetd";
        if (m/\/etc\/init\.d\/(.*inetd)/ or $fake_invocation) {
            &printv("About to $action inetd via invoke-rc.d\n");
            my $service = $1;
            unless ($fake_invocation) {
                 # If we were called by a shell script that also uses
                 # debconf, the pipe to the debconf frontend is fd 3 as
                 # well as fd 1 (stdout).  Ensure that fd 3 is not
                 # inherited by invoke-rc.d and inetd, as that will
                 # cause debconf to hang (bug #589487).  Don't let them
                 # confuse debconf via stdout either.
                 system("invoke-rc.d $service $action >/dev/null 3>&-");
            }
        }
    }
    return(1);
}

sub scan_entries {
    my ($service, $pattern) = @_;
    unless (defined($service)) { $service = '[^#\s]+'; }
    unless (defined($pattern)) { $pattern = ''; }
    my $counter = 0;

    open(ICREAD, "$inetdcf");
    SLOOP: while (<ICREAD>) {
        $counter++ if (/^$service\s+/ and /$pattern/);
    }
    close(ICREAD);
    return($counter);
}

sub printv {
    print STDERR @_ if (defined($verbose));
}

1;

