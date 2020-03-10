#!/usr/bin/perl
use strict;
use warnings;
use Cairo;

unless (Cairo::HAS_FT_FONT && eval 'use Font::FreeType; 1;') {
	die 'need Cairo with FreeType support and Font::FreeType';
}

# my $file = '/usr/share/fonts/truetype/ttf-inconsolata/Inconsolata.otf';
my $file = '/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf';
unless (-r $file) {
	die 'Can\'t find font file';
}

my $ft_face = Font::FreeType->new->face ($file);
my $cr_face = Cairo::FtFontFace->create ($ft_face);

my $surface = Cairo::ImageSurface->create ('argb32', 200, 40);

my $cr = Cairo::Context->create ($surface);
$cr->set_font_face ($cr_face);
$cr->set_font_size (23);
$cr->move_to (20, 25);
$cr->show_text ('Hello, world!');
$cr->show_page;

$surface->write_to_png ('freetype-font.png');
