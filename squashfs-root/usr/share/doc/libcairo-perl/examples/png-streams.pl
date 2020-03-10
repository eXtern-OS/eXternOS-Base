#!/usr/bin/perl

# $Id$

use strict;
use warnings;
use Cairo;

my $filename = $ARGV[0];
unless (-e $filename && -f $filename) {
  die "`$filename´ doesn't seem to be a file";
}

open my $rfh, '<', $filename;

my $surface = Cairo::ImageSurface->create_from_png_stream (sub {
  my ($closure, $length) = @_;
  my $buffer;

  if ($length != sysread ($rfh, $buffer, $length)) {
    die 'read-error';
  }

  return $buffer;
});

warn "status: " . $surface->status;

close $rfh;

open my $wfh, '>', $filename . '.bak';

$surface->write_to_png_stream (sub {
  my ($closure, $data) = @_;
  if (!syswrite ($wfh, $data)) {
    die 'write-error';
  }
});

close $wfh;

warn "status: " . $surface->status;
