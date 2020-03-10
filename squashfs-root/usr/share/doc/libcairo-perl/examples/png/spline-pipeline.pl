#!/usr/bin/perl

use strict;
use warnings;
use Cairo;

use constant
{
	LINE_WIDTH => 13,
};

sub spline_path
{
	my ($cr) = @_;

	$cr->save;
	{
		$cr->translate (-106.0988385, -235.84433);
		$cr->move_to (49.517857, 235.84433);
		$cr->curve_to (86.544809, 175.18401,
		               130.19603, 301.40165,
		               162.67982, 240.42946);
	}
	$cr->restore;
}

sub source_path
{
	my ($cr) = @_;
	spline_path ($cr);
	$cr->set_line_width (1);
	$cr->stroke;
}

sub stroke
{
	my ($cr) = @_;
	spline_path ($cr);
	$cr->set_line_width (LINE_WIDTH);
	$cr->stroke;
}

sub scale_both_set_line_width_stroke
{
	my ($cr) = @_;
	$cr->scale (0.5, 0.5);
	spline_path ($cr);
	$cr->set_line_width (LINE_WIDTH);
	$cr->stroke;
}

sub scale_both_set_line_width_double_stroke
{
	my ($cr) = @_;
	$cr->scale (0.5, 0.5);
	spline_path ($cr);
	$cr->set_line_width (2 * LINE_WIDTH);
	$cr->stroke;
}

sub save_scale_path_restore_set_line_width_stroke
{
	my ($cr) = @_;
	$cr->save;
	{
		$cr->scale (0.5, 1.0);
		spline_path ($cr);
	}
	$cr->restore;

	$cr->set_line_width (LINE_WIDTH);
	$cr->stroke;
}

# XXX: Ouch. It looks like there's an API bug in the implemented semantics for
# cairo_set_line_width. I believe the following function
# (set_line_width_scale_path_stroke_BUGGY) should result in a figure identical
# to the version above it (save_scale_path_restore_set_line_width_stroke), but
# it's currently giving the same result as the one beloe
# (scale_path_set_line_width_stroke).
sub set_line_width_scale_path_stroke_BUGGY
{
	my ($cr) = @_;
	$cr->set_line_width (LINE_WIDTH);
	$cr->scale (0.5, 1.0);
	spline_path ($cr);
	$cr->stroke;
}

sub scale_path_set_line_width_stroke
{
	my ($cr) = @_;
	$cr->scale (0.5, 1.0);
	$cr->set_line_width (LINE_WIDTH);
	spline_path ($cr);
	$cr->stroke;
}

{
	my @pipelines = (
		\&source_path,
		\&stroke,
		\&scale_both_set_line_width_stroke,
		\&scale_both_set_line_width_double_stroke,
		\&save_scale_path_restore_set_line_width_stroke,
		\&scale_path_set_line_width_stroke,
	);
	my $width = 140;
	my $height = 68.833 * scalar @pipelines;

	my $surface = Cairo::ImageSurface->create ('argb32', $width, $height);
	my $cr = Cairo::Context->create ($surface);

	foreach (0 .. $#pipelines) {
		$cr->save;
		{
			$cr->translate ($width/2, ($_+0.5)*($height/scalar @pipelines));
			$pipelines[$_]->($cr);
		}
		$cr->restore;
		if ($cr->status ne 'success') {
			warn "Cairo is unhappy after pipeline #$_: " . $cr->status . "\n";
			exit 1;
		}
	}

	$surface->write_to_png ('spline-pipeline.png');
}

