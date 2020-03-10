#!/usr/bin/env perl

use strict;
use warnings;
use utf8;
use Cairo;

use constant
{
	WIDTH => 250,
	HEIGHT => 200,
	NUM_GLYPHS => 10,
	TEXT => 'abcdefghij',
};

my $surface = Cairo::PdfSurface->create ('glyph-text.pdf', WIDTH, HEIGHT);
my $cr = Cairo::Context->create ($surface);

$cr->select_font_face ('sans', 'normal', 'normal');
$cr->set_font_size (40);

my @glyphs = ();
my $dx = 0;
my $dy = 0;
foreach (0 .. NUM_GLYPHS - 1) {
	# This selects the first few glyphs defined in the font,
	# usually C<< !"#$%&'()* >>.
	my $glyph = { index => $_ + 4, x => $dx, y => $dy };
	my $extents = $cr->glyph_extents ($glyph);
	$dx += $extents->{x_advance};
	$dy += $extents->{y_advance};
	push @glyphs, $glyph;
}

# One-to-one mapping between glyphs and bytes in a string.  This relies on the
# utf8 represenation of the letters in TEXT being one byte long.
my @clusters = map { {num_bytes => 1, num_glyphs => 1} } (1 .. NUM_GLYPHS);

my $height = $cr->font_extents->{height};

# Display the glyphs normally
$cr->translate (0, $height);
$cr->show_glyphs (@glyphs);

# Display the glyphs such that when you select and copy them, you actually get
# reverse of TEXT, i.e. 'jihgfedcba'.
$cr->translate (0, $height);
$cr->show_text_glyphs (TEXT, \@glyphs, \@clusters, 'backward');

$cr->show_page;
