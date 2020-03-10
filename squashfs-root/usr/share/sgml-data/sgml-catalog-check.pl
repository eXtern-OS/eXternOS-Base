#!/usr/bin/perl
# sgml-catalog-check.pl -- check sgml catalog file
#
#Author: apharris@onshore.com (A. P. Harris)
#$Date: 2004/01/11 05:53:25 $
#$Revision: 1.20 $
#
#Todo:
#	cross check the links/dtds and make sure they all appear in the
#	  SGML catalog
#	convert to use perl sgml stuff instead of hand-rolling?
#	make a nice lintian script from this
#	deal with declation and notation files

use Getopt::Long;

$Verbose = 1;			# verboseness, 1 == chatty, 2 == loud
$SGMLdir = "debian/tmp/usr/share/sgml"; # default dir for link making etc
$Catalog = "sgml.catalog";	# default SGML catalog file
$ChopEN = 1;			# whether to chop off //EN[//.*] language specifiers

$Usage = "Usage: $0 [-d <SGML dir>] [-v #] [-e] [<SGML catalog file>]
Check SGML catalog file, create the links as documented in the SGML
sub-policy, and also ensure that the files referenced from the catalog
file actually exists.
   -d <SGML dir>        base dir, default is $SGMLdir
   -v <number>		verbosity amount, 0=silent, 1=default, 2=debug
   -e                   don't omit the trailing EN language specifier (//EN)
   -l                   legacy argument, ignored
   <SGML catalog file>  default is $Catalog
";

$warnings = $errors = 0;	# error and warning count

&GetOptions('e', 'h', 'l', 'v=i', 'd=s');

if ( $opt_h ) 
{
    print $Usage;
    $opt_h && exit;		# shut up -w
}
elsif ( $opt_d == 1 ) {
    die "option '-d' must have an argument\n$Usage";
} 
elsif ( $opt_d ) {
    $SGMLdir = $opt_d;
}

if ( defined($opt_v) ) {
    $Verbose = $opt_v;
}

if ( $opt_l ) {
    $opt_l = $opt_l;            # shut up, -w
    warn("symlinks under /usr/share/sgml no longer desired or created, ignoring -l\n");
}

if ( $opt_e ) {
    $opt_e = $opt_e;            # shut up, -w
    $ChopEN = 0;
}

if ( $#ARGV > 0 ) {
    die "too many arguments\n$Usage";
} elsif ( $#ARGV == 0 ) {
    $Catalog = $ARGV[0];
}

( -f $Catalog ) or
    die "catalog file $Catalog does not exist\n$Usage";
( -d $SGMLdir ) or
    die "SGML directory $SGMLdir does not exist\n$Usage";

open(CAT, "<$Catalog") or
    die "cannot read $Catalog: $!\n";

## when checking for system ids, we need to check relative to the
## catalog file location, so figure out the relative dir of the
## catalog file, possibly removing a prepended SGMLdir

$CatDir = `dirname $Catalog`;
chomp($CatDir);
$CatDir =~ s/^$SGMLdir\/?//;

while (<CAT>) {
    chomp;
    # FIXME: add another line if next line starts with whitespace
    # D: skipped catalog line:
    #  PUBLIC "-//OASIS//DTD DocBook V4.2//EN"
    # D: skipped catalog line:
    #    "docbook.dtd"

    if ( m/^PUBLIC\s+\"([^\"]+)\"\s+\"?([^\s\"]+)\"?/ ) {
	( $id, $file ) = ( $1, $2 );
	debug("found public identifier \"$id\"");
	debug("system identifier is $file");
	if ( -f "$SGMLdir/$CatDir/$file" ) {
            $file = "$CatDir/$file";
        } elsif ( ! -f "$SGMLdir/$file" ) {
	    error("referenced-file-does-not-exist $SGMLdir/$CatDir/$file of $SGMLdir/$file");
	    next;
	}
	
	if ( $id =~ m!^(.+)//(?:([^/]+)//)?(ELEMENTS|DOCUMENT|ENTITIES|DTD)\s+([^/]+)//(.+)$! ) {
	    ( $reg, $vendor, $type, $name, $misc ) = ( $1, $2, $3, $4, $5 );

	    if ( $type eq "ENTITIES" ) {
                                # AOK, no checking for location
	    } 
	    elsif ( $type eq "DTD" || $type eq "ELEMENTS" ) {
                                # AOK, no checking for location
	    }
	    elsif ( $type eq "DOCUMENT" ) {
		( $file =~ m!^dtd/! || $file =~ m!^entities! ) &&
		    error("DOCUMENT-in-dtd-or-entities-dir $file");
	    }
	    else {
		error("identifier-type-not-recognized $type on FPI $id");
	    }
	    
	    # would be nice to check that the DTD file is reasonable
	    # oh well...

            # quieten warnings
            $name = $name;
            $misc = $misc;
            $reg = $reg;
            $vendor = $vendor;
	}
	else {
	    error("SGML-identifier-not-in-recognized-form $id");
	    next;
	}
    }
    else {
	debug("skipped catalog line:\n   $_");
	next;
    }
}

if ( $errors ) {
    exit(1);
}
exit(0);

sub debug {
    local($msg) = @_;
    ( $Verbose > 1 ) && warn("D: $msg\n");
}

sub inform {
    local($msg) = @_;
    ( $Verbose ) && warn("N: $msg\n");
}

sub warning {
    local($msg) = @_;
    $warnings++;
    warn("W: $msg\n");
}

sub error {
    local($msg) = @_;
    $errors++;
    warn("E: $msg\n");
}

