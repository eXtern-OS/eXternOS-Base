use X11::Protocol;

my $opt_g = 0;
my $opt_v = 0;
my $do_root = 1;

# This is a fudge factor relating to how the X server allocates resource IDs.
# 21 seems to be the right value for XFree86 4.2.
my $client_shift = 21;

$x = new X11::Protocol;

sub get_prop {
    my($win, $name) = @_;
    return ($x->GetProperty($win, $x->atom($name),
			    $x->atom("STRING"), 0, 65535, 0))[0];
}

sub pre_walk {
    my $win = shift;
    my($root, $dad, @kids) = $x->QueryTree($win);

    my @argv = split(/\0/, get_prop($win, "WM_COMMAND"));
    my $cmd = $argv[0];
    $cmd =~ s[^.*/][];
    $cmd_name{$win >> $client_shift} = $cmd if $cmd ne "";
    map(pre_walk($_), @kids);
}

sub tree {
    my $win = shift;
    my($root, $dad, @kids) = $x->QueryTree($win);

    my $client = $win >> $client_shift;
    my $dad_client = $dad >> $client_shift;
    $id = $win & 0xfffff;

    my $name = "";
    if ($client != $dad_client) {
	my $client_id = sprintf "%x", $client;
	$client_id = "$cmd_name{$client}:$client_id"
	  if exists $cmd_name{$client};
	$name = "($client_id)";
    }
    $name .= sprintf("%x", $id);

    if ($opt_g) {
	my %geo = $x->GetGeometry($win);
	$name .= "($geo{width}x$geo{height}+$geo{x}+$geo{y})";
    }

    my $title = get_prop($win, "WM_ICON_NAME") || get_prop($win, "WM_NAME");

    $name .= "`" . $title ."'" if $title;


    if (not @kids) {
        return "-$name\n";
    }
    my @lines;
    for my $kid (@kids) {
        push @lines, tree($kid);
    }
    my $i;
    for ($i = $#lines; substr($lines[$i], 0, 1) ne "-"; $i--) {
        $lines[$i] = " " . $lines[$i];
    }
    if ($i > 0) {
        $lines[$i] = "`" . $lines[$i];
        $lines[$i] = "|" . $lines[$i] while $i-- > 1;
        $lines[$i] = "+" . $lines[$i];
    } else {
        $lines[0] = "-" . $lines[0];
    }
    return("-$name-" . shift @lines,
           map(" " x (length($name) + 2) . $_, @lines));
}

sub vt_ify {
    my @x = @_;
    for my $l (@x) {
	if ($opt_v) {
	    $l =~ s/\|-/\cNtq\cO/g;
	    $l =~ s/\| /\cNx\cO /g;
	    $l =~ s/`-/\cNmq\cO/g; #`;
	    $l =~ s/---/\cNqqq\cO/g;
	    $l =~ s/-\+-/\cNqwq\cO/g;
	}
    }
    return @x;
}

pre_walk($x->root);

foreach my $arg (@ARGV) {
    if ($arg eq "-g") {
	$opt_g = 1;
    } elsif ($arg eq "-v") {
	$opt_v = 1;
    } else {
	$do_root = 0;
	print tree(hex $arg);
    }
}

print tree($x->root) if $do_root;

