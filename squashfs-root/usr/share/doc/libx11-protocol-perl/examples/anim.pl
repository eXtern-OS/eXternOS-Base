#!/usr/bin/perl

use X11::Protocol;
use IO::Select;

$pi = 3.1415926535898;
$r = 1;
$theta = 0;
$size = 250;

$x = X11::Protocol->new;
$win = $x->new_rsrc;
$x->CreateWindow($win, $x->root, 'InputOutput', $x->root_depth,
		 'CopyFromParent', (0, 0), 2 * $size, 2 * $size, 1,
#		 'backing_store' => 'Always',
		 'background_pixel' => $x->white_pixel);
$x->ChangeProperty($win, $x->atom('WM_NAME'), $x->atom('STRING'), 8,
		   'Replace', "Animation test");
$x->MapWindow($win);
$pm = $x->new_rsrc;
$x->CreatePixmap($pm, $win, $x->root_depth, 2 * $size, 2 * $size);
$gc = $x->new_rsrc;
$x->CreateGC($gc, $pm, 'foreground' => $x->black_pixel,
	     'graphics_exposures' => 0);
$egc = $x->new_rsrc;
$x->CreateGC($egc, $pm, 'foreground' => $x->white_pixel,
	     'graphics_exposures' => 0);
$x->PolyFillRectangle($pm, $egc, [(0, 0), 2 * $size, 2 * $size]);

$sel = IO::Select->new($x->connection->fh);

sub r2p {
    my($x, $y) = @_;
    $x -= .5;
    $x *= .75;
    $y -= .5;
    return [-atan2($y, $x), sqrt($x*$x + $y*$y)];
}

$P = [[['Simple', $gc],
       [r2p(0, 0),
	r2p(.75, 0),
	r2p(1, .25),
	r2p(.75, .5),
	r2p(.15, .5),
	r2p(.15, 1),
	r2p(0, 1)]],
      [['Convex', $egc],
       [r2p(.15, .15),
	r2p(.75, .15),
	r2p(.85, .25),
	r2p(.75, .35),
	r2p(.15, .35)]]];

$E = [[['Simple', $gc],
       [r2p(0, 0),
	r2p(1, 0),
	r2p(1, .2),
	r2p(.2, .2),
	r2p(.2, .4),
	r2p(.75, .4),
	r2p(.75, .6),
	r2p(.2, .6),
	r2p(.2, .8),
	r2p(1, .8),
	r2p(1, 1),
	r2p(0, 1)]]];

$R = [[['Simple', $gc],
       [r2p(0, 0),
	r2p(.75, 0),
	r2p(1, .25),
	r2p(.75, .5),
	r2p(1, 1),
	r2p(.85, 1),
	r2p(.6, .5),
	r2p(.15, .5),
	r2p(.15, 1),
	r2p(0, 1)]],
      [['Convex', $egc],
       [r2p(.15, .15),
	r2p(.75, .15),
	r2p(.85, .25),
	r2p(.75, .35),
	r2p(.15, .35)]]];

$L = [[['Simple', $gc],
       [r2p(0, 0),
	r2p(.2, 0),
	r2p(.2, .8),
	r2p(1, .8),
	r2p(1, 1),
	r2p(0, 1)]]];

for (;;) {
    for $img ($P, $E, $R, $L) {
	$r = 5;
	while ($r < 6.25 * $size) {
	    @polys = ();
	    for $poly (@$img) {
		@a = ($poly->[0]);
		for $p (@{$poly->[1]}) {
		    push @{$a[1]}, $size +
			$r * $p->[1] * sin($theta + $p->[0]);
		    push @{$a[1]}, $size +
			$r * $p->[1] * cos($theta + $p->[0]);
		}
		push @polys, [@a];
	    }
	    for $poly (@old_polys) {
		$x->FillPoly($pm, $egc, $poly->[0][0], 'Origin', @{$poly->[1]})
		    if $poly->[0][1] != $egc;
	    }
	    for $poly (@polys) {
		$x->FillPoly($pm, $poly->[0][1], $poly->[0][0], 'Origin',
			     @{$poly->[1]});
	    }
	    $x->CopyArea($pm, $win, $gc, (0, 0), 2 * $size, 2 * $size, (0, 0));

	    # On my Linux/x86 2.0, anything less than 1/100 sec causes
	    # other things (e.g., mouse tracking) to slow down terribly. 
	    $x->flush();
	    select(undef, undef, undef, 1/99);

	    @old_polys = @polys;
	    $r *= 1.05;
	    $theta += .1;
	    $x->handle_input if $sel->can_read(0);
	}
    }
}

