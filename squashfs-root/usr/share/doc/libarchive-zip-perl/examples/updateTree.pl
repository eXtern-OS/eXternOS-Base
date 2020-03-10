#!/usr/bin/perl
# Shows how to update a Zip in place using a temp file.
#
# usage:
# 	perl [-m] examples/updateTree.pl zipfile.zip dirname
#
# -m means to mirror
#
# $Id: updateTree.pl,v 1.2 2003/11/27 17:03:51 ned Exp $
#
use Archive::Zip qw(:ERROR_CODES);

my $mirror = 0;
if ($ARGV[0] eq '-m') { shift; $mirror = 1; }

my $zipName = shift || die 'must provide a zip name';
my $dirName = shift || die 'must provide a directory name';

# Read the zip
my $zip = Archive::Zip->new();

if (-f $zipName) {
    die "can't read $zipName\n" unless $zip->read($zipName) == AZ_OK;

    # Update the zip
    $zip->updateTree($dirName, undef, undef, $mirror);

    # Now the zip is updated. Write it back via a temp file.
    exit($zip->overwrite());
} else    # new zip
{
    $zip->addTree($dirName);
    exit($zip->writeToFileNamed($zipName));
}
