#!/usr/bin/perl

use X11::Protocol;
use X11::Protocol::Constants qw(InputOutput CopyFromParent Replace Exposure_m);

use IO::Select;
use strict;

$| = 1;

my $big_size = 1000;
my $small_wd = 50;
my $small_ht = 20;

my $X = X11::Protocol->new;

my $cmap = $X->default_colormap;
my($bg_pixel,) = $X->AllocColor($cmap, (0xdddd, 0xdddd, 0xdddd));

my $main_win = $X->new_rsrc;
$X->CreateWindow($main_win, $X->root, InputOutput, CopyFromParent,
		 CopyFromParent, (0, 0), $big_size, $big_size, 0,
		 'background_pixel' => $bg_pixel);

$X->ChangeProperty($main_win, $X->atom('WM_ICON_NAME'), $X->atom('STRING'),
                   8, Replace, "long run");
$X->ChangeProperty($main_win, $X->atom('WM_NAME'), $X->atom('STRING'), 8,
                   Replace, "Long-running X11::Protocol test");
$X->ChangeProperty($main_win, $X->atom('WM_CLASS'), $X->atom('STRING'), 8,
                   Replace, "longrun\0LongRun");
$X->ChangeProperty($main_win, $X->atom('WM_NORMAL_HINTS'),
                   $X->atom('WM_SIZE_HINTS'), 32, Replace,
                   pack("Lx16llx16llllllx4", 8|16|128|256,
			$big_size, $big_size,
                        1, 1, 1, 1, $big_size, $big_size));
$X->ChangeProperty($main_win, $X->atom('WM_HINTS'), $X->atom('WM_HINTS'),
                   32, Replace, pack("LLLx24", 1|2, 1, 1));
my $delete_atom = $X->atom('WM_DELETE_WINDOW');
$X->ChangeProperty($main_win, $X->atom('WM_PROTOCOLS'), $X->atom('ATOM'),
                   32, Replace, pack("L", $delete_atom));

my $text_gc = $X->new_rsrc;
my($text_pixel,) = $X->AllocColor($cmap, (0x0000, 0x0000, 0x0000));
my $font = $X->new_rsrc;
$X->OpenFont($font, "fixed");
$X->CreateGC($text_gc, $main_win, 'foreground' => $text_pixel,
	     'font' => $font);

$X->MapWindow($main_win);

my $fds = IO::Select->new($X->connection->fh);

my $num_cols = $big_size / $small_wd;
my @cols;

my %visible;

sub label {
    my($win) = @_;
    $X->PolyText8($win, $text_gc, 4, ($small_ht + 10) / 2,
		  [0, sprintf("%x", $win)]);
}

sub handle_event {
    my(%e) = @_;
    if ($e{'name'} eq "Expose") {
	my $win = $e{'window'};
	label($win) if $visible{$win};
    }
}

$X->{'event_handler'} = \&handle_event;

my $last_id;
for (;;) {
    while ($fds->can_read(0)) {
	$X->handle_input;
    }
    for (my $x = 0; $x < $big_size; $x += $small_wd) {
	my @column;
	for (my $y = 0; $y < $big_size; $y += $small_ht) {
#  	    my($rand_pixel,) =
#  	      $X->AllocColor($cmap, (rand(65536), rand(65535), rand(65535)));
	    my $rand_pixel = rand(2**32);
	    my $win = $X->new_rsrc;
	    if ($win != $last_id + 1) {
		print "x";
	    }
	    $last_id = $win;
	    $X->CreateWindow($win, $main_win, InputOutput, CopyFromParent,
			     CopyFromParent, ($x, $y), $small_wd, $small_ht,
			     1, 'background_pixel' => $rand_pixel,
			     'event_mask' => Exposure_m);
	    if (rand() < 0.001) {
		$X->MapWindow($win);
		push @column, $win if rand() < 0.9;
		$visible{$win} = 1;
		label($win);
	    } else {
		$X->DestroyWindow($win);
	    }
	}
	push @cols, [@column];
	if (@cols >= $num_cols) {
	    for my $win (@{shift @cols}) {
		delete $visible{$win};
		$X->DestroyWindow($win);
	    }
	}
    }
    print ".";
}
