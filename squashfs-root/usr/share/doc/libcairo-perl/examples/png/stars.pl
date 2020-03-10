#!/usr/bin/perl

use strict;
use warnings;
use Cairo;

use constant
{
	WIDTH => 600,
	HEIGHT => 275,
	M_PI => 3.14159265,
};

{
	my $surf = Cairo::ImageSurface->create ('argb32', WIDTH, HEIGHT);
	my $cr = Cairo::Context->create ($surf);

	$0 =~ /(.*)\.pl/;
	my $out = "$1.png";

	$cr->rectangle (0, 0, WIDTH, HEIGHT);
	$cr->set_source_rgb (1, 1, 1);
	$cr->fill;

	draw_stars ($cr, WIDTH, HEIGHT);

	$cr->show_page;

	$surf->write_to_png ($out);
}

sub star_path
{
	my ($cr) = @_;

	my $theta = 4 * M_PI / 5.0;

	$cr->move_to (0, 0);
	for (my $i = 0; $i < 4; $i++)
	{
		$cr->rel_line_to (1.0, 0);
		$cr->rotate ($theta);
	}
	$cr->close_path;
}

sub draw_stars
{
	my ($cr, $width, $height) = @_;

	$cr->set_source_rgb (0, 0, 0);

	$cr->save;
	{
		$cr->translate (5, $height / 2.6);
		$cr->scale ($height, $height);
		star_path ($cr);
		$cr->set_fill_rule ('winding');
		$cr->fill;
	}
	$cr->restore;

	$cr->save;
	{
		$cr->translate ($width - $height - 5, $height / 2.6);
		$cr->scale ($height, $height);
		star_path ($cr);
		$cr->set_fill_rule ('even-odd');
		$cr->fill;
	}
	$cr->restore;
}
