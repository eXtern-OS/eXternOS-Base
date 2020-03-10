#!/usr/bin/perl

use strict;
use warnings;
use Cairo;

use constant
{
	WIDTH => 750,
	HEIGHT => 500,
};

{
	my $surf = Cairo::ImageSurface->create ('argb32', WIDTH, HEIGHT);
	my $cr = Cairo::Context->create ($surf);

	$0 =~ /(.*)\.pl/;
	my $out = "$1.png";

	$cr->rectangle (0, 0, WIDTH, HEIGHT);
	$cr->set_source_rgb (1, 1, 1);
	$cr->fill;

	draw_outlines ($cr, WIDTH, HEIGHT);

	$cr->show_page;

	$surf->write_to_png ($out);
}

sub create_gradient
{
	my ($cr, $width, $height) = @_;

	my $gradient = Cairo::LinearGradient->create (0, 0, $width, 0);

	$gradient->add_color_stop_rgb (0.0, 0., 0., 0.);
	$gradient->add_color_stop_rgb (0.5, 1., 1., 1.);
	$gradient->add_color_stop_rgb (1.0, 0., 0., 0.);

	return $gradient;
}

sub draw_outlines
{
	my ($cr, $surface_width, $surface_height) = @_;

	my $gradient;
	my ($width, $height, $pad);

	$width = $surface_width / 4.0;
	$pad = ($surface_width - (3 * $width)) / 2.0;
	$height = $surface_height;

	$gradient = create_gradient ($cr, $width, $height);

	$cr->set_source ($gradient);
	draw_flat ($cr, $width, $height);

	$cr->translate ($width + $pad, 0);
	$cr->set_source ($gradient);
	draw_tent ($cr, $width, $height);

	$cr->translate ($width + $pad, 0);
	$cr->set_source ($gradient);
	draw_cylinder ($cr, $width, $height);

	$cr->restore;
}

sub draw_flat
{
	my ($cr, $width, $height) = @_;

	my $hwidth = $width / 2.0;

	$cr->rectangle (0, $hwidth, $width, $height - $hwidth);

	$cr->fill;
}

sub draw_tent
{
	my ($cr, $width, $height) = @_;

	my $hwidth = $width / 2.0;

	$cr->move_to     (       0,  $hwidth);
	$cr->rel_line_to ( $hwidth, -$hwidth);
	$cr->rel_line_to ( $hwidth,  $hwidth);
	$cr->rel_line_to (       0,  $height - $hwidth);
	$cr->rel_line_to (-$hwidth, -$hwidth);
	$cr->rel_line_to (-$hwidth,  $hwidth);
	$cr->close_path;

	$cr->fill;
}

sub draw_cylinder
{
	my ($cr, $width, $height) = @_;

	my $hwidth = $width / 2.0;

	$cr->move_to (0, $hwidth);
	$cr->rel_curve_to (0, -$hwidth, $width, -$hwidth, $width, 0);
	$cr->rel_line_to (0, $height - $hwidth);
	$cr->rel_curve_to (0, -$hwidth, -$width, -$hwidth, -$width, 0);
	$cr->close_path;

	$cr->fill;
}
