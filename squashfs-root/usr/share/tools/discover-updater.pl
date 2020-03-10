#! /usr/bin/perl

# Horrible hacky script in lead up to deadline. Please sort out!

# We don't use an XML parser as we want to minimize diffs. We rely on the
# textual structure of the discover.xml files. This is probably a bug, too,
# but not as big a bug as screwing with the entire file's format.

my %args;
my %mods;
my $name;

sub dev_attrs {
  local $_=shift;
  %args=();
  while(s!(\w+)\=['"](.*?)["']!!) {
    $args{$1}=$2;
  }
}

sub make_name {
  my $v=$args{'vendor'};
  my $d=$args{'model'};
  my $sv=$args{'subvendor'};
  my $sd=$args{'subdevice'};
  $sv='x' unless defined $sv;
  $sd='x' unless defined $sd;
  $name = "$v:$d:$sv:$sd";
}

sub short_tag {
  my ($attrs)=@_;
  dev_attrs($attrs);
  make_name();
}

sub open_tag {
  my ($attrs)=@_;
  dev_attrs($attrs);
}

sub close_tag {
  %args=();
}

# Read modules file
open(PCILST,"$ARGV[0]") || die "Cannot open $ARGV[0]";
while(<PCILST>) {
  /^(\S+)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)/;
  my ($name,$v,$d,$sv,$sd)=($1,$2,$3,$4,$5);
  $v =~ s/^0000//;
  $d =~ s/^0000//;
  $sv =~ s/^0000//;
  $sd =~ s/^0000//;
  $sv='x' if($sv eq "ffffffff");
  $sd='x' if($sd eq "ffffffff");
  # Avoid some entries we do not want.  'generic' seem to be some
  # hardware independent driver, and i810-tco make the machine reboot
  # after a minute.
  next if ($name =~ m/^generic$|^i810-tco$/);
  $mods{"$v:$d:$sv:$sd"}=$name;
}
close PCILST;

# Read discover config file
while(<STDIN>) {
  if(m!<device([^>]*?)/>!) {
    short_tag($1);
    make_name();
    if($mods{$name}) {
      print STDERR "Device $name has module $mods{$name}\n";
      s!/>!>!;
      $_.=<<"EOF";
    <data class='linux'>
      <data version='[2.6,inf)' class="module">
        <data class='name'>$mods{$name}</data>
      </data>
    </data>
  </device>
EOF
    }
  } elsif(m!<device(.*?)>!) {
    open_tag($1);
  } elsif(m!</device>!) {
    close_tag();
  }
  print;
}
