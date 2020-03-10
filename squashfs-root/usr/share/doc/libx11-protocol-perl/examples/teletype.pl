#!/usr/bin/perl

# Put up windows on two displays, and echo input from one on the other.

use X11::Protocol;
use X11::Keysyms '%keysyms';
%keysyms_name = reverse %keysyms;

use IO::Select;

die "usage: $0 display display\n" unless @ARGV == 2;

$x1 = X11::Protocol->new($ARGV[0]);
$x2 = X11::Protocol->new($ARGV[1]);

$win1 = $x1->new_rsrc;
$win2 = $x2->new_rsrc;

$x1->CreateWindow($win1, $x1->root, 'InputOutput', $x1->root_depth,
		  'CopyFromParent', (0,0), 200, 200, 1,
#		  'backing_store' => 'Always',
		  'background_pixel' => $x1->white_pixel,
		  'event_mask' => $x1->pack_event_mask('KeyPress', 'Exposure',
						       'ButtonPress'));
$x2->CreateWindow($win2, $x2->root, 'InputOutput', $x2->root_depth,
		  'CopyFromParent', (0,0), 200, 200, 1,
#		  'backing_store' => 'Always',
		  'background_pixel' => $x2->white_pixel,
		  'event_mask' => $x2->pack_event_mask('KeyPress', 'Exposure',
						       'ButtonPress'));

$x1->ChangeProperty($win1, $x1->atom("WM_NAME"), $x1->atom("STRING"), 8,
		    'Replace', "Window #1");
$x2->ChangeProperty($win2, $x2->atom("WM_NAME"), $x2->atom("STRING"), 8,
		    'Replace', "Window #2");

$x1->MapWindow($win1);
$x2->MapWindow($win2);

$fnt1 = $x1->new_rsrc;
$fnt2 = $x2->new_rsrc;

$x1->OpenFont($fnt1, 'fixed');
$x2->OpenFont($fnt2, 'fixed');

$gc1 = $x1->new_rsrc;
$gc2 = $x2->new_rsrc;

$x1->CreateGC($gc1, $win1, 'foreground' => $x1->black_pixel, 'font' => $fnt1,
	      'graphics_exposures' => 0);
$x2->CreateGC($gc2, $win2, 'foreground' => $x2->black_pixel, 'font' => $fnt2,
	      'graphics_exposures' => 0);

$i = $x1->min_keycode;
for $ar ($x1->GetKeyboardMapping($x1->min_keycode,
				 $x1->max_keycode - $x1->min_keycode + 1)) {
    $table[0][$i++] = [map($keysyms_name{$_}, @$ar)];
}

$i = $x2->min_keycode;
for $ar ($x2->GetKeyboardMapping($x2->min_keycode,
				 $x2->max_keycode - $x2->min_keycode + 1)) {
    $table[1][$i++] = [map($keysyms_name{$_}, @$ar)];
}

sub print_event {
    my($disp, $win, $gc, $font, $t, %e) = @_;
    if ($e{name} eq "KeyPress") {
	my($key) = $t->[$e{detail}][0];
	exit if $key eq "q" or $key eq "Q";
	$disp->PolyText8($win, $gc, ($e{event_x}, $e{event_y}), [0, $key]);
	(my $key16 = $key) =~ s/(.)/\0$1/g;;	
	my $dx = {$disp->QueryTextExtents($font, $key16)}->{'overall_width'};
	$disp->WarpPointer(0, 0, 0, 0, 0, 0, $dx, 0);
    } elsif ($e{name} eq "ButtonPress") {
	$disp->PolyPoint($win, $gc, 'Origin', ($e{event_x}, $e{event_y}));
    } elsif ($e{name} eq "Expose") {
	$disp->PolyRectangle($win, $gc, [($e{'x'}, $e{'y'}), $e{width},
			     $e{height}]);
    }
}

$x1->event_handler(sub {print_event($x2, $win2, $gc2, $fnt2, $table[1], @_)});
$x2->event_handler(sub {print_event($x1, $win1, $gc1, $fnt1, $table[0], @_)});

$sel = IO::Select->new($x1->connection->fh, $x2->connection->fh);

for (;;) {
    for $fh ($sel->can_read) {
	$x1->handle_input if $fh == $x1->connection->fh;
	$x2->handle_input if $fh == $x2->connection->fh;
    }
}
