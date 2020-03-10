#!/usr/bin/perl

# Overwrite a bunch of randomly chosen windows on the screen with
# random-colored rectangles. You might want to learn about the
# "xrefresh" program before trying this one.

# Demonstrates the use of "robust_req"

use X11::Protocol;

$X = X11::Protocol->new;

my $gc = $X->new_rsrc;
$X->req('CreateGC', $gc, $X->root);

for (1 .. 2500) {
    my $client = rand(50);
    my $client_id = rand(200);
    my $id = $client << 21 | $client_id;
    printf "XID %x ", $id;
    my($result,) = $X->robust_req('GetGeometry', $id);
    my %geom;
    if (ref $result) {
	print "exists\n";
	%geom = @$result;
    } else {
	print "does not exist\n";
	next;
    }
    # Make sure we've got a Window rather than a Pixmap, since overwriting
    # Pixmaps is more permanent and therefore less amusing.
    next unless ref $X->robust_req('GetWindowAttributes', $id);
    $X->req('ChangeGC', $gc, 'foreground' => rand(2**32));
    my($result,) = $X->robust_req('PolyFillRectangle', $id, $gc,
				  [5, 5, $geom{width}-10, $geom{height}-10]);
    if (not ref $result) {
	print "Ignoring $result error\n";
    }
}
