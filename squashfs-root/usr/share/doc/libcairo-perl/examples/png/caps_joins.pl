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

	draw_caps_joins ($cr, WIDTH, HEIGHT);

	$cr->show_page;

	$surf->write_to_png ($out);
}

sub stroke_v_twice
{
	my ($cr, $width, $height) = @_;

	$cr->move_to (0, 0);
	$cr->rel_line_to ($width / 2, $height / 2);
	$cr->rel_line_to ($width / 2, - $height / 2);

	$cr->save;
	$cr->stroke;
	$cr->restore;

	$cr->save;
	{
		$cr->set_line_width (2.0);
		$cr->set_line_cap ('butt');
		$cr->set_source_rgb (1, 1, 1);
		$cr->stroke;
	}
	$cr->restore;

	$cr->new_path;
}

sub draw_caps_joins
{
	my ($cr, $width, $height) = @_;

	my $line_width = $height / 12 & (~1);

	$cr->set_line_width ($line_width);
	$cr->set_source_rgb (0, 0, 0);

	$cr->translate ($line_width, $line_width);
	$width -= 2 * $line_width;

	$cr->set_line_join ('bevel');
	$cr->set_line_cap ('butt');
	stroke_v_twice ($cr, $width, $height);

	$cr->translate (0, $height / 4 - $line_width);
	$cr->set_line_join ('miter');
	$cr->set_line_cap ('square');
	stroke_v_twice ($cr, $width, $height);

	$cr->translate (0, $height / 4 - $line_width);
	$cr->set_line_join ('round');
	$cr->set_line_cap ('round');
	stroke_v_twice ($cr, $width, $height);
}
