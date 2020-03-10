#!/usr/bin/perl

use strict;
use warnings;
use Cairo;

use constant
{
	WIDTH => 600,
	HEIGHT => 600,
};

{
	my $surf = Cairo::ImageSurface->create ('argb32', WIDTH, HEIGHT);
	my $cr = Cairo::Context->create ($surf);

	$0 =~ /(.*)\.pl/;
	my $out = "$1.png";

	$cr->rectangle (0, 0, WIDTH, HEIGHT);
	$cr->set_source_rgb (1, 1, 1);
	$cr->fill;

	draw_spiral ($cr, WIDTH, HEIGHT);

	$cr->show_page;

	$surf->write_to_png ($out);
}

sub draw_spiral
{
	my ($cr, $width, $height) = @_;

	my $wd = .02 * $width;
	my $hd = .02 * $height;

	$width -= 2;
	$height -= 2;

	$cr->move_to ($width + 1, 1 - $hd);
	for (my $i=0; $i < 9; $i++)
	{
		$cr->rel_line_to (0, $height - $hd * (2 * $i - 1));
		$cr->rel_line_to (- ($width - $wd * (2 * $i)), 0);
		$cr->rel_line_to (0, - ($height - $hd * (2 * $i)));
		$cr->rel_line_to ($width - $wd * (2 * $i + 1), 0);
	}

	$cr->set_source_rgb (0, 0, 1);
	$cr->stroke;
}
