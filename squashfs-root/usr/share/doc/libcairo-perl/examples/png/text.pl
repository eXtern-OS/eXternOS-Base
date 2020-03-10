#!/usr/bin/perl

use strict;
use warnings;
use utf8;
use Cairo;

use constant
{
	WIDTH => 450,
	HEIGHT => 600,
	TEXT => 'hëllø, wôrld',
	NUM_GLYPHS => 10,
	M_PI => 4 * atan2(1, 1),
};

sub box_text
{
	my ($cr, $utf8, $x, $y) = @_;

	$cr->save;

	my $extents = $cr->text_extents ($utf8);
	my $line_width = $cr->get_line_width;
	$cr->rectangle ($x + $extents->{x_bearing} - $line_width,
	                $y + $extents->{y_bearing} - $line_width,
	                $extents->{width} + 2 * $line_width,
	                $extents->{height} + 2 *$line_width);
	$cr->stroke;

	$cr->move_to ($x, $y);
	$cr->show_text ($utf8);
	$cr->move_to ($x, $y);
	$cr->text_path ($utf8);
	$cr->set_source_rgb (1, 0, 0);
	$cr->set_line_width (1.0);
	$cr->stroke;

	$cr->restore;
}

sub box_glyphs
{
	my ($cr, $x, $y, @glyphs) = @_;

	$cr->save;

	my $extents = $cr->glyph_extents (@glyphs);
	my $line_width = $cr->get_line_width;
	$cr->rectangle ($x + $extents->{x_bearing} - $line_width,
	                $y + $extents->{y_bearing} - $line_width,
	                $extents->{width} + 2 * $line_width,
	                $extents->{height} + 2 * $line_width);
	$cr->stroke;

	foreach my $glyph (@glyphs) {
		$glyph->{x} += $x;
		$glyph->{y} += $y;
	}
	$cr->show_glyphs (@glyphs);
	$cr->glyph_path (@glyphs);
	$cr->set_source_rgb (1, 0, 0);
	$cr->set_line_width (1.0);
	$cr->stroke;
	foreach my $glyph (@glyphs) {
		$glyph->{x} -= $x;
		$glyph->{y} -= $y;
	}

	$cr->restore;
}

{
	my $surface = Cairo::ImageSurface->create ('argb32', WIDTH, HEIGHT);
	my $cr = Cairo::Context->create ($surface);

	$cr->set_source_rgb (0, 0, 0);
	$cr->set_line_width (2.0);

	$cr->save;
	$cr->rectangle (0, 0, WIDTH, HEIGHT);
	$cr->set_source_rgba (0, 0, 0, 0);
	$cr->set_operator ('source');
	$cr->fill;
	$cr->restore;

	$cr->select_font_face ('sans', 'normal', 'normal');
	$cr->set_font_size (40);
	if (1) {
		my $matrix = Cairo::Matrix->init_scale (40, -40);
		$cr->set_font_matrix ($matrix);

		$cr->scale (1, -1);
		$cr->translate (0, - HEIGHT);
	}

	my $font_extents = $cr->font_extents;
	my $height = $font_extents->{height};

	my @glyphs = ();
	my $dx = 0;
	my $dy = 0;
	foreach (0 .. NUM_GLYPHS - 1) {
		my $glyph = { index => $_ + 4, x => $dx, y => $dy };
		my $extents = $cr->glyph_extents ($glyph);
		$dx += $extents->{x_advance};
		$dy += $extents->{y_advance};
		push @glyphs, $glyph;
	}

	box_text ($cr, TEXT, 10, $height);

	$cr->translate (0, $height);
	$cr->save;
	{
		$cr->translate (10, $height);
		$cr->rotate (10 * M_PI / 180);
		box_text ($cr, TEXT, 0, 0);
	}
	$cr->restore;

	$cr->translate (0, 2 * $height);
	$cr->save;
	{
		my $matrix = Cairo::Matrix->init_identity;
		$matrix->scale (40, -40);
		$matrix->rotate (-10 * M_PI / 180);
		$cr->set_font_matrix ($matrix);
		box_text ($cr, TEXT, 10, $height);
	}
	$cr->restore;

	$cr->translate (0, 2 * $height);
	box_glyphs ($cr, 10, $height, @glyphs);

	$cr->translate (10, 2 * $height);
	$cr->save;
	{
		$cr->rotate (10 * M_PI / 180);
		box_glyphs ($cr, 0, 0, @glyphs);
	}
	$cr->restore;

	$cr->translate (0, $height);
	foreach (0 .. NUM_GLYPHS - 1) {
		$glyphs[$_]->{y} += $_ * 5;
	}
	box_glyphs ($cr, 10, $height, @glyphs);

	$surface->write_to_png ('text.png');
}
