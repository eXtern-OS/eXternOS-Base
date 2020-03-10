#############################################################################
# Pod/UsageTrans.pm -- print translated usage messages for the running script.
#
# Copyright (C) 1996-2000 by Bradford Appleton. All rights reserved.
# Copyright (C) 2002 by SPI, inc.
# Copyright (C) 2005 by Frank Lichtenheld.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
#############################################################################

package Pod::UsageTrans;

use vars qw($VERSION);
$VERSION = 0.1;  ## Current version of this package
require  5.006;    ## requires this Perl version or later

=head1 NAME

Pod::UsageTrans, pod2usage() - print a usage message from embedded pod documentation

=head1 SYNOPSIS

  use Pod::UsageTrans
  use Locale::gettext;

  setlocale(LC_MESSAGES,'');
  textdomain('prog');

  my $message_text  = "This text precedes the usage message.";
  my $exit_status   = 2;          ## The exit status to use
  my $verbose_level = 0;          ## The verbose level to use
  my $filehandle    = \*STDERR;   ## The filehandle to write to
  my $textdomain    = 'prog-pod'; ## The gettext domain for the Pod documentation

  pod2usage($message_text);

  pod2usage($exit_status);

  pod2usage( { -message => gettext( $message_text ) ,
               -exitval => $exit_status  ,
               -verbose => $verbose_level,
               -output  => $filehandle,
               -textdomain => $textdomain } );

  pod2usage(   -msg     => $message_text ,
               -exitval => $exit_status  ,
               -verbose => $verbose_level,
               -output  => $filehandle,
               -textdomain => $textdomain );

=head1 DESCRIPTION

Pod::UsageTrans works exactly like Pod::Usage but allows you
to easily translate your messages. It was specifically written to
be compatible with the F<.po> files produced by po4a(7). If you
want to use any other method to produce your F<.po> files you
should probably take a look at the source of code of this module
to see which msgids you will need to use.

For documentation on calling pod2usage from your program see
Pod::Usage. Pod::UsageTrans additionally supports a C<-textdomain>
option where you can specify the gettext domain to use. If
C<-textdomain> isn't set, Pod::UsageTrans will behave exactly
like Pod::Usage.

=head1 BUGS

Pod::UsageTrans is currently in the state of a quickly hacked together
solution that was tested with exactly one use case. Expect bugs in
corner cases.

It specifically doesn't support many of the po4a options like charset
conversion between the POD input and the msgstr in the F<.pot> file.

=head1 SEE ALSO

po4a(7), Pod::Usage, gettext info documentation

=head1 AUTHOR

Frank Lichtenheld, E<lt>frank@lichtenheld.deE<gt>

Based on Pod::Usage by Brad Appleton E<lt>bradapp@enteract.comE<gt>
which is based on code for B<Pod::Text::pod2text()> written by
Tom Christiansen E<lt>tchrist@mox.perl.comE<gt>

Also based on Locale::Po4a::Pod, Locale::Po4a::Po and
Locale::Po4a::TransTractor by Martin Quinson and Denis Barbier.

=cut

#############################################################################

use strict;
#use diagnostics;
use Carp;
use Config;
use Exporter;
use File::Spec;
use Pod::Usage ();
use Locale::gettext;

use vars qw(@ISA @EXPORT);
@EXPORT = qw(&pod2usage);
@ISA = qw( Pod::Usage );

##---------------------------------------------------------------------------

##---------------------------------
## Function definitions begin here
##---------------------------------

# I had to copy the ENTIRE pod2usage just to make a one-line change
# s/Pod::Usage/Pod::UsageTrans/. Maybe I can convince upstream to allow
# more easy overriding?
sub pod2usage {
    local($_) = shift || "";
    my %opts;
    ## Collect arguments
    if (@_ > 0) {
        ## Too many arguments - assume that this is a hash and
        ## the user forgot to pass a reference to it.
        %opts = ($_, @_);
    }
    elsif (ref $_) {
        ## User passed a ref to a hash
        %opts = %{$_}  if (ref($_) eq 'HASH');
    }
    elsif (/^[-+]?\d+$/) {
        ## User passed in the exit value to use
        $opts{"-exitval"} =  $_;
    }
    else {
        ## User passed in a message to print before issuing usage.
        $_  and  $opts{"-message"} = $_;
    }

    ## Need this for backward compatibility since we formerly used
    ## options that were all uppercase words rather than ones that
    ## looked like Unix command-line options.
    ## to be uppercase keywords)
    %opts = map {
        my $val = $opts{$_};
        s/^(?=\w)/-/;
        /^-msg/i   and  $_ = '-message';
        /^-exit/i  and  $_ = '-exitval';
        lc($_) => $val;
    } (keys %opts);

    ## Now determine default -exitval and -verbose values to use
    if ((! defined $opts{"-exitval"}) && (! defined $opts{"-verbose"})) {
        $opts{"-exitval"} = 2;
        $opts{"-verbose"} = 0;
    }
    elsif (! defined $opts{"-exitval"}) {
        $opts{"-exitval"} = ($opts{"-verbose"} > 0) ? 1 : 2;
    }
    elsif (! defined $opts{"-verbose"}) {
        $opts{"-verbose"} = (lc($opts{"-exitval"}) eq "noexit" ||
                             $opts{"-exitval"} < 2);
    }

    ## Default the output file
    $opts{"-output"} = (lc($opts{"-exitval"}) eq "noexit" ||
                        $opts{"-exitval"} < 2) ? \*STDOUT : \*STDERR
            unless (defined $opts{"-output"});
    ## Default the input file
    $opts{"-input"} = $0  unless (defined $opts{"-input"});

    ## Look up input file in path if it doesnt exist.
    unless ((ref $opts{"-input"}) || (-e $opts{"-input"})) {
        my ($dirname, $basename) = ('', $opts{"-input"});
        my $pathsep = ($^O =~ /^(?:dos|os2|MSWin32)$/) ? ";"
                            : (($^O eq 'MacOS' || $^O eq 'VMS') ? ',' :  ":");
        my $pathspec = $opts{"-pathlist"} || $ENV{PATH} || $ENV{PERL5LIB};

        my @paths = (ref $pathspec) ? @$pathspec : split($pathsep, $pathspec);
        for $dirname (@paths) {
            $_ = File::Spec->catfile($dirname, $basename)  if length;
            last if (-e $_) && ($opts{"-input"} = $_);
        }
    }

    ## Now create a pod reader and constrain it to the desired sections.
    my $parser = new Pod::UsageTrans(USAGE_OPTIONS => \%opts);
    if ($opts{"-verbose"} == 0) {
        $parser->select("SYNOPSIS");
    }
    elsif ($opts{"-verbose"} == 1) {
        my $opt_re = '(?i)' .
                     '(?:OPTIONS|ARGUMENTS)' .
                     '(?:\s*(?:AND|\/)\s*(?:OPTIONS|ARGUMENTS))?';
        $parser->select( 'SYNOPSIS', $opt_re, "DESCRIPTION/$opt_re" );
    }
    elsif ($opts{"-verbose"} == 99) {
        $parser->select( $opts{"-sections"} );
        $opts{"-verbose"} = 1;
    }

    ## Now translate the pod document and then exit with the desired status
    if ( $opts{"-verbose"} >= 2 
             and  !ref($opts{"-input"})
             and  $opts{"-output"} == \*STDOUT )
    {
       ## spit out the entire PODs. Might as well invoke perldoc
       my $progpath = File::Spec->catfile($Config{scriptdir}, "perldoc");
       system($progpath, $opts{"-input"});
    }
    else {
       $parser->parse_from_file($opts{"-input"}, $opts{"-output"});
    }

    exit($opts{"-exitval"})  unless (lc($opts{"-exitval"}) eq 'noexit');
}

sub canonize {
    my $text=shift;
#    print STDERR "\ncanonize [$text]====" if $debug{'canonize'};
    $text =~ s/^ *//s;
    $text =~ s/^[ \t]+/  /gm;
    # if ($text eq "\n"), it messed up the first string (header)
    $text =~ s/\n/  /gm if ($text ne "\n");
    $text =~ s/([.)])  +/$1  /gm;
    $text =~ s/([^.)])  */$1 /gm;
    $text =~ s/ *$//s;
#    print STDERR ">$text<\n" if $debug{'canonize'};
    return $text;
}

##---------------------------------------------------------------------------

##-------------------------------
## Method definitions begin here
##-------------------------------

sub translate {
    my ($self, $string, %options) = @_;

    $string = canonize($string) if $options{wrap};

#    print "domain: $self->{USAGE_OPTIONS}->{-textdomain}, string:\"$string\"\n";
    return dgettext( $self->{USAGE_OPTIONS}->{"-textdomain"},
		     $string ) if $self->{USAGE_OPTIONS}->{"-textdomain"};
    return $string;
}

sub command {
    my ($self, $command, $paragraph, $line_num) = @_;
#    print STDOUT "cmd: '$command' '$paragraph' at $line_num\n";
    if ($command eq 'back'
	|| $command eq 'cut'
	|| $command eq 'pod'
	|| $command eq 'over') {
    } else {
	$paragraph=$self->translate($paragraph,
				    "wrap"=>1);
    }
    return $self->SUPER::command( $command, $paragraph, $line_num );
}

sub verbatim {
    my ($self, $paragraph, $line_num) = @_;
#    print "verb: '$paragraph' at $line_num\n";

    if ($paragraph eq "\n") {
	return;
    }
    $paragraph=$self->translate($paragraph);
    return $self->SUPER::verbatim( $paragraph, $line_num );
}

sub textblock {
    my ($self, $paragraph, $line_num) = @_;
#    print "text: '$paragraph' at $line_num\n";

    if ($paragraph eq "\n") {
	return;
    }
    if ($paragraph =~ m/^[ \t]/m) {
	$self->verbatim($paragraph, $line_num) ;
	return;
    }

    $paragraph=$self->translate($paragraph,
				"wrap"=>1);
    return $self->SUPER::textblock( $paragraph, $line_num );
}


1; # keep require happy
