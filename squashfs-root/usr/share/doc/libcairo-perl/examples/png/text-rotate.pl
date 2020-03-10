#!/usr/bin/perl

use strict;
use warnings;
use Cairo;

use constant
{
	WIDTH => 450,
	HEIGHT => 900,
	NUM_STRINGS => 3,
	M_PI => 4 * atan2(1, 1),
};

{
	my $surface = Cairo::ImageSurface->create ('argb32', WIDTH, HEIGHT);
	my $cr = Cairo::Context->create ($surface);

	$cr->set_source_rgb (0.0, 0.0, 0.0);

	$cr->translate (40, 40);

	$cr->select_font_face ('mono', 'normal', 'normal');
	$cr->set_font_size (12);
	$cr->show_text ('+CTM rotation');

	$cr->save;
	$cr->select_font_face ('serif', 'normal', 'normal');
	$cr->set_font_size (40);
	for (my $i = 0; $i < NUM_STRINGS; $i++) {
		my $angle = $i * 0.5 * M_PI / (NUM_STRINGS - 1);
		$cr->save;
		$cr->rotate ($angle);
		$cr->move_to (100, 0);
		$cr->show_text ("Text");
		$cr->restore;
	}
	$cr->restore;

	$cr->translate (0, HEIGHT / 3);

	$cr->move_to (0, 0);
	$cr->show_text ('+CTM rotation');
	$cr->rel_move_to (0, 12);
	$cr->show_text ('-font rotation');

	$cr->save;
	$cr->select_font_face ('serif', 'normal', 'normal');
	$cr->set_font_size (40);
	for (my $i = 0; $i < NUM_STRINGS; $i++) {
		my $angle = $i * 0.5 * M_PI / (NUM_STRINGS - 1);
		$cr->save;
		$cr->rotate ($angle);
		my $matrix = Cairo::Matrix->init_identity;
		$matrix->scale (40, 40);
		$matrix->rotate (-$angle);
		$cr->set_font_matrix ($matrix);
		$cr->move_to (100, 0);
		$cr->show_text ('Text');
		$cr->restore;
	}
	$cr->restore;

	$cr->translate (0, HEIGHT / 3);

	$cr->move_to (0, 0);
	$cr->show_text ('+CTM rotation');
	$cr->rel_move_to (0, 12);
	$cr->show_text ('-CTM rotation');

	$cr->save;
	$cr->select_font_face ('serif', 'normal', 'normal');
	$cr->set_font_size (40);
	for (my $i = 0; $i < NUM_STRINGS; $i++) {
		my $angle = $i * 0.5 * M_PI / (NUM_STRINGS - 1);
		$cr->save;
		$cr->rotate ($angle);
		$cr->move_to (100, 0);
		$cr->rotate (-$angle);
		$cr->show_text ('Text');
		$cr->restore;
	}
	$cr->restore;

	$surface->write_to_png ('text-rotate.png');
}
