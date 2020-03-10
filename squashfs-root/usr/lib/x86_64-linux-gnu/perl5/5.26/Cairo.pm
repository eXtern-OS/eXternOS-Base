#
# Copyright (c) 2004-2013 by the cairo perl team (see the file README)
#
# Licensed under the LGPL, see LICENSE file for more information.
#
# $Id$
#

package Cairo;

use strict;
use warnings;
use DynaLoader;

our @ISA = qw/DynaLoader/;

our $VERSION = '1.106';

sub dl_load_flags { $^O eq 'darwin' ? 0x00 : 0x01 }

Cairo->bootstrap ($VERSION);

# Our Cairo::VERSION used to be a simple wrapper around CAIRO_VERSION.  But a
# package's VERSION sub is supposed to do Perl version checking so that things
# like 'use Cairo 1.00' work.  To not break backwards-compatibility, we
# dispatch according to the number of arguments passed in.
sub VERSION {
  if (scalar @_ == 2) {
    shift->SUPER::VERSION (@_);
  } else {
    Cairo::LIB_VERSION (@_);
  }
}

1;

__END__

=head1 NAME

Cairo - Perl interface to the cairo 2d vector graphics library

=head1 SYNOPSIS

  use Cairo;

  my $surface = Cairo::ImageSurface->create ('argb32', 100, 100);
  my $cr = Cairo::Context->create ($surface);

  $cr->rectangle (10, 10, 40, 40);
  $cr->set_source_rgb (0, 0, 0);
  $cr->fill;

  $cr->rectangle (50, 50, 40, 40);
  $cr->set_source_rgb (1, 1, 1);
  $cr->fill;

  $cr->show_page;

  $surface->write_to_png ('output.png');

=head1 ABSTRACT

Cairo provides Perl bindings for the vector graphics library cairo.  It
supports multiple output targets, including PNG, PDF and SVG.  Cairo produces
identical output on all those targets.

=head1 API DOCUMENTATION

This is a listing of the API Cairo provides.  For more verbose information,
refer to the cairo manual at L<http://cairographics.org/manual/>.

=head2 Drawing

=head3 Cairo::Context -- The cairo drawing context

I<Cairo::Context> is the main object used when drawing with Cairo. To draw with
Cairo, you create a I<Cairo::Context>, set the target surface, and drawing
options for the I<Cairo::Context>, create shapes with methods like
C<$cr-E<gt>move_to> and C<$cr-E<gt>line_to>, and then draw shapes with
C<$cr-E<gt>stroke> or C<$cr-E<gt>fill>.

I<Cairo::Context>'s can be pushed to a stack via C<$cr-E<gt>save>. They may
then safely be changed, without loosing the current state. Use
C<$cr-E<gt>restore> to restore to the saved state.

=over

=item $cr = Cairo::Context->create ($surface)

=over

=item $surface: I<Cairo::Surface>

=back

=item $cr-E<gt>save

=item $cr->restore

=item $status = $cr->status

=item $surface = $cr->get_target

=item $cr->push_group [1.2]

=item $cr->push_group_with_content ($content) [1.2]

=over

=item $content: I<Cairo::Content>

=back

=item $pattern = $cr->pop_group [1.2]

=item $cr->pop_group_to_source [1.2]

=item $surface = $cr->get_group_target [1.2]

=item $cr->set_source_rgb ($red, $green, $blue)

=over

=item $red: double

=item $green: double

=item $blue: double

=back

=item $cr->set_source_rgba ($red, $green, $blue, $alpha)

=over

=item $red: double

=item $green: double

=item $blue: double

=item $alpha: double

=back

=item $cr->set_source ($source)

=over

=item $source: I<Cairo::Pattern>

=back

=item $cr->set_source_surface ($surface, $x, $y)

=over

=item $surface: I<Cairo::Surface>

=item $x: double

=item $y: double

=back

=item $source = $cr->get_source

=item $cr->set_antialias ($antialias)

=over

=item $antialias: I<Cairo::Antialias>

=back

=item $antialias = $cr->get_antialias

=item $cr->set_dash ($offset, ...)

=over

=item $offset: double

=item ...: list of doubles

=back

=item $cr->set_fill_rule ($fill_rule)

=over

=item $fill_rule: I<Cairo::FillRule>

=back

=item $fill_rule = $cr->get_fill_rule

=item $cr->set_line_cap ($line_cap)

=over

=item $line_cap: I<Cairo::LineCap>

=back

=item $line_cap = $cr->get_line_cap

=item $cr->set_line_join ($line_join)

=over

=item $line_join: I<Cairo::LineJoin>

=back

=item $line_join = $cr->get_line_join

=item $cr->set_line_width ($width)

=over

=item $width: double

=back

=item $width = $cr->get_line_width

=item $cr->set_miter_limit ($limit)

=over

=item $limit: double

=back

=item ($offset, @dashes) = $cr->get_dash [1.4]

=item $limit = $cr->get_miter_limit

=item $cr->set_operator ($op)

=over

=item $op: I<Cairo::Operator>

=back

=item $op = $cr->get_operator

=item $cr->set_tolerance ($tolerance)

=over

=item $tolerance: double

=back

=item $tolerance = $cr->get_tolerance

=item $cr->clip

=item $cr->clip_preserve

=item ($x1, $y1, $x2, $y2) = $cr->clip_extents [1.4]

=item $bool = $cr->in_clip ($x, $y) [1.10]

=over

=item $x: double

=item $y: double

=back

=item @rectangles = $cr->copy_clip_rectangle_list [1.4]

=item $cr->reset_clip

=item $cr->fill

=item $cr->fill_preserve

=item ($x1, $y1, $x2, $y2) = $cr->fill_extents

=item $bool = $cr->in_fill ($x, $y)

=over

=item $x: double

=item $y: double

=back

=item $cr->mask ($pattern)

=over

=item $pattern: I<Cairo::Pattern>

=back

=item $cr->mask_surface ($surface, $surface_x, $surface_y)

=over

=item $surface: I<Cairo::Surface>

=item $surface_x: double

=item $surface_y: double

=back

=item $cr->paint

=item $cr->paint_with_alpha ($alpha)

=over

=item $alpha: double

=back

=item $cr->stroke

=item $cr->stroke_preserve

=item ($x1, $y1, $x2, $y2) = $cr->stroke_extents

=item $bool = $cr->in_stroke ($x, $y)

=over

=item $x: double

=item $y: double

=back

=item $cr->copy_page

=item $cr->show_page

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Paths -- Creating paths and manipulating path data

  $path = [
    { type => "move-to", points => [[1, 2]] },
    { type => "line-to", points => [[3, 4]] },
    { type => "curve-to", points => [[5, 6], [7, 8], [9, 10]] },
    ...
    { type => "close-path", points => [] },
  ];

I<Cairo::Path> is a data structure for holding a path. This data structure
serves as the return value for C<$cr-E<gt>copy_path> and
C<$cr-E<gt>copy_path_flat> as well the input value for
C<$cr-E<gt>append_path>.

I<Cairo::Path> is represented as an array reference that contains path
elements, represented by hash references with two keys: I<type> and I<points>.
The value for I<type> can be either of the following:

=over

=item C<move-to>

=item C<line-to>

=item C<curve-to>

=item C<close-path>

=back

The value for I<points> is an array reference which contains zero or more
points.  Points are represented as array references that contain two doubles:
I<x> and I<y>.  The necessary number of points depends on the I<type> of the
path element:

=over

=item C<move-to>: 1 point

=item C<line_to>: 1 point

=item C<curve-to>: 3 points

=item C<close-path>: 0 points

=back

The semantics and ordering of the coordinate values are consistent with
C<$cr-E<gt>move_to>, C<$cr-E<gt>line_to>, C<$cr-E<gt>curve_to>, and
C<$cr-E<gt>close_path>.

Note that the paths returned by Cairo are implemented as tied array references
which do B<not> support adding, removing or shuffling of path segments.  For
these operations, you need to make a shallow copy first:

  my @path_clone = @{$path};
  # now you can alter @path_clone which ever way you want

The points of a single path element can be changed directly, however, without
the need for a shallow copy:

  $path->[$i]{points} = [[3, 4], [5, 6], [7, 8]];

=over

=item $path = $cr->copy_path

=item $path = $cr->copy_path_flat

=item $cr->append_path ($path)

=over

=item $path: I<Cairo::Path>

=back

=item $bool = $cr->has_current_point [1.6]

=item ($x, $y) = $cr->get_current_point

=item $cr->new_path

=item $cr->new_sub_path [1.2]

=item $cr->close_path

=item ($x1, $y1, $x2, $y2) = $cr->path_extents [1.6]

=item $cr->arc ($xc, $yc, $radius, $angle1, $angle2)

=over

=item $xc: double

=item $yc: double

=item $radius: double

=item $angle1: double

=item $angle2: double

=back

=item $cr->arc_negative ($xc, $yc, $radius, $angle1, $angle2)

=over

=item $xc: double

=item $yc: double

=item $radius: double

=item $angle1: double

=item $angle2: double

=back

=item $cr->curve_to ($x1, $y1, $x2, $y2, $x3, $y3)

=over

=item $x1: double

=item $y1: double

=item $x2: double

=item $y2: double

=item $x3: double

=item $y3: double

=back

=item $cr->line_to ($x, $y)

=over

=item $x: double

=item $y: double

=back

=item $cr->move_to ($x, $y)

=over

=item $x: double

=item $y: double

=back

=item $cr->rectangle ($x, $y, $width, $height)

=over

=item $x: double

=item $y: double

=item $width: double

=item $height: double

=back

=item $cr->glyph_path (...)

=over

=item ...: list of I<Cairo::Glyph>'s

=back

=item $cr->text_path ($utf8)

=over

=item $utf8: string in utf8 encoding

=back

=item $cr->rel_curve_to ($dx1, $dy1, $dx2, $dy2, $dx3, $dy3)

=over

=item $dx1: double

=item $dy1: double

=item $dx2: double

=item $dy2: double

=item $dx3: double

=item $dy3: double

=back

=item $cr->rel_line_to ($dx, $dy)

=over

=item $dx: double

=item $dy: double

=back

=item $cr->rel_move_to ($dx, $dy)

=over

=item $dx: double

=item $dy: double

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Patterns -- Gradients and filtered sources

=over

=item $status = $pattern->status

=item $type = $pattern->get_type [1.2]

=item $pattern->set_extend ($extend)

=over

=item $extend: I<Cairo::Extend>

=back

=item $extend = $pattern->get_extend

=item $pattern->set_filter ($filter)

=over

=item $filter: I<Cairo::Filter>

=back

=item $filter = $pattern->get_filter

=item $pattern->set_matrix ($matrix)

=over

=item $matrix: I<Cairo::Matrix>

=back

=item $matrix = $pattern->get_matrix

=item $pattern = Cairo::SolidPattern->create_rgb ($red, $green, $blue)

=over

=item $red: double

=item $green: double

=item $blue: double

=back

=item $pattern = Cairo::SolidPattern->create_rgba ($red, $green, $blue, $alpha)

=over

=item $red: double

=item $green: double

=item $blue: double

=item $alpha: double

=back

=item ($r, $g, $b, $a) = $pattern->get_rgba [1.4]

=item $pattern = Cairo::SurfacePattern->create ($surface)

=over

=item $surface: I<Cairo::Surface>

=back

=item $surface = $pattern->get_surface [1.4]

=item $pattern = Cairo::LinearGradient->create ($x0, $y0, $x1, $y1)

=over

=item $x0: double

=item $y0: double

=item $x1: double

=item $y1: double

=back

=item ($x0, $y0, $x1, $y1) = $pattern->get_points [1.4]

=item $pattern = Cairo::RadialGradient->create ($cx0, $cy0, $radius0, $cx1, $cy1, $radius1)

=over

=item $cx0: double

=item $cy0: double

=item $radius0: double

=item $cx1: double

=item $cy1: double

=item $radius1: double

=back

=item ($x0, $y0, $r0, $x1, $y1, $r1) = $pattern->get_circles [1.4]

=item $pattern->add_color_stop_rgb ($offset, $red, $green, $blue)

=over

=item $offset: double

=item $red: double

=item $green: double

=item $blue: double

=back

=item $pattern->add_color_stop_rgba ($offset, $red, $green, $blue, $alpha)

=over

=item $offset: double

=item $red: double

=item $green: double

=item $blue: double

=item $alpha: double

=back

=item @stops = $pattern->get_color_stops [1.4]

A color stop is represented as an array reference with five elements: offset,
red, green, blue, and alpha.

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Regions -- Representing a pixel-aligned area

=over

=item $region = Cairo::Region->create (...) [1.10]

=over

=item ...: zero or more I<Cairo::RectangleInt>

=back

=item $status = $region->status [1.10]

=item $num = $region->num_rectangles [1.10]

=item $rect = $region->get_rectangle ($i) [1.10]

=over

=item $i: integer

=back

=item $bool = $region->is_empty [1.10]

=item $bool = $region->contains_point ($x, $y) [1.10]

=over

=item $x: integer

=item $y: integer

=back

=item $bool = $region_one->equal ($region_two) [1.10]

=over

=item $region_two: I<Cairo::Region>

=back

=item $region->translate ($dx, $dy) [1.10]

=over

=item $dx: integer

=item $dy: integer

=back

=item $status = $dst->intersect ($other) [1.10]

=item $status = $dst->intersect_rectangle ($rect) [1.10]

=item $status = $dst->subtract ($other) [1.10]

=item $status = $dst->subtract_rectangle ($rect) [1.10]

=item $status = $dst->union ($other) [1.10]

=item $status = $dst->union_rectangle ($rect) [1.10]

=item $status = $dst->xor ($other) [1.10]

=item $status = $dst->xor_rectangle ($rect) [1.10]

=over

=item $other: I<Cairo::Region>

=item $rect: I<Cairo::RectangleInt>

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Transformations -- Manipulating the current transformation matrix

=over

=item $cr->translate ($tx, $ty)

=over

=item $tx: double

=item $ty: double

=back

=item $cr->scale ($sx, $sy)

=over

=item $sx: double

=item $sy: double

=back

=item $cr->rotate ($angle)

=over

=item $angle: double

=back

=item $cr->transform ($matrix)

=over

=item $matrix: I<Cairo::Matrix>

=back

=item $cr->set_matrix ($matrix)

=over

=item $matrix: I<Cairo::Matrix>

=back

=item $matrix = $cr->get_matrix

=item $cr->identity_matrix

=item ($x, $y) = $cr->user_to_device ($x, $y)

=over

=item $x: double

=item $y: double

=back

=item ($dx, $dy) = $cr->user_to_device_distance ($dx, $dy)

=over

=item $dx: double

=item $dy: double

=back

=item ($x, $y) = $cr->device_to_user ($x, $y)

=over

=item $x: double

=item $y: double

=back

=item ($dx, $dy) = $cr->device_to_user_distance ($dx, $dy)

=over

=item $dx: double

=item $dy: double

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Text -- Rendering text and sets of glyphs

Glyphs are represented as anonymous hash references with three keys: I<index>,
I<x> and I<y>.  Example:

  my @glyphs = ({ index => 1, x => 2, y => 3 },
                { index => 2, x => 3, y => 4 },
                { index => 3, x => 4, y => 5 });

=over

=item $cr->select_font_face ($family, $slant, $weight)

=over

=item $family: string

=item $slant: I<Cairo::FontSlant>

=item $weight: I<Cairo::FontWeight>

=back

=item $cr->set_font_size ($size)

=over

=item $size: double

=back

=item $cr->set_font_matrix ($matrix)

=over

=item $matrix: I<Cairo::Matrix>

=back

=item $matrix = $cr->get_font_matrix

=item $cr->set_font_options ($options)

=over

=item $options: I<Cairo::FontOptions>

=back

=item $options = $cr->get_font_options

=item $cr->set_scaled_font ($scaled_font) [1.2]

=over

=item $scaled_font: I<Cairo::ScaledFont>

=back

=item $scaled_font = $cr->get_scaled_font [1.4]

=item $cr->show_text ($utf8)

=over

=item $utf8: string

=back

=item $cr->show_glyphs (...)

=over

=item ...: list of glyphs

=back

=item $cr->show_text_glyphs ($utf8, $glyphs, $clusters, $cluster_flags) [1.8]

=over

=item $utf8: string

=item $glyphs: array ref of glyphs

=item $clusters: array ref of clusters

=item $cluster_flags: I<Cairo::TextClusterFlags>

=back

=item $face = $cr->get_font_face

=item $extents = $cr->font_extents

=item $cr->set_font_face ($font_face)

=over

=item $font_face: I<Cairo::FontFace>

=back

=item $cr->set_scaled_font ($scaled_font)

=over

=item $scaled_font: I<Cairo::ScaledFont>

=back

=item $extents = $cr->text_extents ($utf8)

=over

=item $utf8: string

=back

=item $extents = $cr->glyph_extents (...)

=over

=item ...: list of glyphs

=back

=item $face = Cairo::ToyFontFace->create ($family, $slant, $weight) [1.8]

=over

=item $family: string

=item $slant: I<Cairo::FontSlant>

=item $weight: I<Cairo::FontWeight>

=back

=item $family = $face->get_family [1.8]

=item $slang = $face->get_slant [1.8]

=item $weight = $face->get_weight [1.8]

=back

=cut

# --------------------------------------------------------------------------- #

=head2 Fonts

=head3 Cairo::FontFace -- Base class for fonts

=over

=item $status = $font_face->status

=item $type = $font_face->get_type [1.2]

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Scaled Fonts -- Caching metrics for a particular font size

=over

=item $scaled_font = Cairo::ScaledFont->create ($font_face, $font_matrix, $ctm, $options)

=over

=item $font_face: I<Cairo::FontFace>

=item $font_matrix: I<Cairo::Matrix>

=item $ctm: I<Cairo::Matrix>

=item $options: I<Cairo::FontOptions>

=back

=item $status = $scaled_font->status

=item $extents = $scaled_font->extents

=item $extents = $scaled_font->text_extents ($utf8) [1.2]

=over

=item $utf8: string

=back

=item $extents = $scaled_font->glyph_extents (...)

=over

=item ...: list of glyphs

=back

=item ($status, $glyphs, $clusters, $cluster_flags) = $scaled_font->text_to_glyphs ($x, $y, $utf8) [1.8]

=over

=item $x: double

=item $y: double

=item $utf8: string

=back

=item $font_face = $scaled_font->get_font_face [1.2]

=item $options = $scaled_font->get_font_options [1.2]

=item $font_matrix = $scaled_font->get_font_matrix [1.2]

=item $ctm = $scaled_font->get_ctm [1.2]

=item $scale_matrix = $scaled_font->get_scale_matrix [1.8]

=item $type = $scaled_font->get_type [1.2]

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Font Options -- How a font should be rendered

=over

=item $font_options = Cairo::FontOptions->create

=item $status = $font_options->status

=item $font_options->merge ($other)

=over

=item $other: I<Cairo::FontOptions>

=back

=item $hash = $font_options->hash

=item $bools = $font_options->equal ($other)

=over

=item $other: I<Cairo::FontOptions>

=back

=item $font_options->set_antialias ($antialias)

=over

=item $antialias: I<Cairo::AntiAlias>

=back

=item $antialias = $font_options->get_antialias

=item $font_options->set_subpixel_order ($subpixel_order)

=over

=item $subpixel_order: I<Cairo::SubpixelOrder>

=back

=item $subpixel_order = $font_options->get_subpixel_order

=item $font_options->set_hint_style ($hint_style)

=over

=item $hint_style: I<Cairo::HintStyle>

=back

=item $hint_style = $font_options->get_hint_style

=item $font_options->set_hint_metrics ($hint_metrics)

=over

=item $hint_metrics: I<Cairo::HintMetrics>

=back

=item $hint_metrics = $font_options->get_hint_metrics

=back

=cut

# --------------------------------------------------------------------------- #

=head3 FreeType Fonts -- Font support for FreeType

If your cairo library supports it, the FreeType integration allows you to load
font faces from font files.  You can query for this capability with
C<Cairo::HAS_FT_FONT>.  To actually use this, you'll need the L<Font::FreeType>
module.

=over

=item my $face = Cairo::FtFontFace->create ($ft_face, $load_flags=0)

=over

=item $ft_face: I<Font::FreeType::Face>

=item $load_flags: integer

=back

This method allows you to create a I<Cairo::FontFace> from a
I<Font::FreeType::Face>.  To obtain the latter, you can for example load it
from a file:

  my $file = '/usr/share/fonts/truetype/ttf-bitstream-vera/Vera.ttf';
  my $ft_face = Font::FreeType->new->face ($file);
  my $face = Cairo::FtFontFace->create ($ft_face);

=back

=cut

# --------------------------------------------------------------------------- #

=head2 Surfaces

=head3 I<Cairo::Surface> -- Base class for surfaces

=over

=item $similar = Cairo::Surface->create_similar ($other, $content, $width, $height)

=over

=item $other: I<Cairo::Surface>

=item $content: I<Cairo::Content>

=item $width: integer

=item $height: integer

=back

For hysterical reasons, you can also use the following syntax:

  $similar = $other->create_similar ($content, $width, $height)

=item $new = Cairo::Surface->create_for_rectangle ($target, $x, $y, $width, $height) [1.10]

=over

=item $target: I<Cairo::Surface>

=item $x: double

=item $y: double

=item $width: double

=item $height: double

=back

=item $status = $surface->status

=item $surface->finish

=item $surface->flush

=item $font_options = $surface->get_font_options

=item $content = $surface->get_content [1.2]

=item $surface->mark_dirty

=item $surface->mark_dirty_rectangle ($x, $y, $width, $height)

=over

=item $x: integer

=item $y: integer

=item $width: integer

=item $height: integer

=back

=item $surface->set_device_offset ($x_offset, $y_offset)

=over

=item $x_offset: integer

=item $y_offset: integer

=back

=item ($x_offset, $y_offset) = $surface->get_device_offset [1.2]

=item $surface->set_fallback_resolution ($x_pixels_per_inch, $y_pixels_per_inch) [1.2]

=over

=item $x_pixels_per_inch: double

=item $y_pixels_per_inch: double

=back

=item ($x_pixels_per_inch, $y_pixels_per_inch) = $surface->get_fallback_resolution [1.8]

=item $type = $surface->get_type [1.2]

=item $status = $surface->copy_page [1.6]

=over

=item $status: I<Cairo::Status>

=back

=item $status = $surface->show_page [1.6]

=over

=item $status: I<Cairo::Status>

=back

=item $boolean = $surface->has_show_text_glyphs [1.8]

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Image Surfaces -- Rendering to memory buffers

=over

=item $surface = Cairo::ImageSurface->create ($format, $width, $height)

=over

=item $format: I<Cairo::Format>

=item $width: integer

=item $height: integer

=back

=item $surface = Cairo::ImageSurface->create_for_data ($data, $format, $width, $height, $stride)

=over

=item $data: image data

=item $format: I<Cairo::Format>

=item $width: integer

=item $height: integer

=item $stride: integer

=back

=item $data = $surface->get_data [1.2]

=item $format = $surface->get_format [1.2]

=item $width = $surface->get_width

=item $height = $surface->get_height

=item $stride = $surface->get_stride [1.2]

=item $stride = Cairo::Format::stride_for_width ($format, $width) [1.6]

=over

=item $format: I<Cairo::Format>

=item $width: integer

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head3 PDF Surfaces -- Rendering PDF documents

=over

=item $surface = Cairo::PdfSurface->create ($filename, $width_in_points, $height_in_points) [1.2]

=over

=item $filename: string

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface = Cairo::PdfSurface->create_for_stream ($callback, $callback_data, $width_in_points, $height_in_points) [1.2]

=over

=item $callback: I<Cairo::WriteFunc>

=item $callback_data: scalar

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface->set_size ($width_in_points, $height_in_points) [1.2]

=over

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface->restrict_to_version ($version) [1.10]

=over

=item $version: I<Cairo::PdfVersion>

=back

=item @versions = Cairo::PdfSurface::get_versions [1.10]

=item $string = Cairo::PdfSurface::version_to_string ($version) [1.10]

=over

=item $version: I<Cairo::PdfVersion>

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head3 PNG Support -- Reading and writing PNG images

=over

=item $surface = Cairo::ImageSurface->create_from_png ($filename)

=over

=item $filename: string

=back

=item Cairo::ReadFunc: $data = sub { my ($callback_data, $length) = @_; }

=over

=item $data: binary image data, of length $length

=item $callback_data: scalar, user data

=item $length: integer, bytes to read

=back

=item $surface = Cairo::ImageSurface->create_from_png_stream ($callback, $callback_data)

=over

=item $callback: I<Cairo::ReadFunc>

=item $callback_data: scalar

=back

=item $status = $surface->write_to_png ($filename)

=over

=item $filename: string

=back

=item Cairo::WriteFunc: sub { my ($callback_data, $data) = @_; }

=over

=item $callback_data: scalar, user data

=item $data: binary image data, to be written

=back

=item $status = $surface->write_to_png_stream ($callback, $callback_data)

=over

=item $callback: I<Cairo::WriteFunc>

=item $callback_data: scalar

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head3 PostScript Surfaces -- Rendering PostScript documents

=over

=item $surface = Cairo::PsSurface->create ($filename, $width_in_points, $height_in_points) [1.2]

=over

=item $filename: string

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface = Cairo::PsSurface->create_for_stream ($callback, $callback_data, $width_in_points, $height_in_points) [1.2]

=over

=item $callback: I<Cairo::WriteFunc>

=item $callback_data: scalar

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface->set_size ($width_in_points, $height_in_points) [1.2]

=over

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface->dsc_begin_setup [1.2]

=item $surface->dsc_begin_page_setup [1.2]

=item $surface->dsc_comment ($comment) [1.2]

=over

=item $comment: string

=back

=item $surface->restrict_to_level ($level) [1.6]

=over

=item $level: I<Cairo::PsLevel>

=back

=item @levels = Cairo::PsSurface::get_levels [1.6]

=item $string = Cairo::PsSurface::level_to_string ($level) [1.6]

=over

=item $level: I<Cairo::PsLevel>

=back

=item $surface->set_eps ($eps) [1.6]

=over

=item $eps: boolean

=back

=item $eps = $surface->get_eps [1.6]

=back

=cut

# --------------------------------------------------------------------------- #

=head3 Recording Surfaces -- Records all drawing operations

=over

=item $surface = Cairo::RecordingSurface->create ($content, $extents) [1.10]

=over

=item $content: I<Cairo::Content>

=item $extents: I<Cairo::Rectangle>

=back

=item ($x0, $y0, $width, $height) = $surface->ink_extents [1.10]

=back

=cut

# --------------------------------------------------------------------------- #

=head3 SVG Surfaces -- Rendering SVG documents

=over

=item $surface = Cairo::SvgSurface->create ($filename, $width_in_points, $height_in_points) [1.2]

=over

=item $filename: string

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface = Cairo::SvgSurface->create_for_stream ($callback, $callback_data, $width_in_points, $height_in_points) [1.2]

=over

=item $callback: I<Cairo::WriteFunc>

=item $callback_data: scalar

=item $width_in_points: double

=item $height_in_points: double

=back

=item $surface->restrict_to_version ($version) [1.2]

=over

=item $version: I<Cairo::SvgVersion>

=back

=item @versions = Cairo::SvgSurface::get_versions [1.2]

=item $string = Cairo::SvgSurface::version_to_string ($version) [1.2]

=over

=item $version: I<Cairo::SvgVersion>

=back

=back

=cut

# --------------------------------------------------------------------------- #

=head2 Utilities

=head3 Version Information -- Run-time and compile-time version checks.

=over

=item $version_code = Cairo->lib_version

=item $version_string = Cairo->lib_version_string

These two functions return the version of libcairo that the program is
currently running against.

=item $version_code = Cairo->LIB_VERSION

Returns the version of libcairo that Cairo was compiled against.

=item $version_code = Cairo->LIB_VERSION_ENCODE ($major, $minor, $micro)

=over

=item $major: integer

=item $minor: integer

=item $micro: integer

=back

Encodes the version C<$major.$minor.$micro> as an integer suitable for
comparison against C<< Cairo->lib_version >> and C<< Cairo->LIB_VERSION >>.

=back

=cut

# --------------------------------------------------------------------------- #

=head1 SEE ALSO

=over

=item L<http://cairographics.org/documentation>

Lists many available resources including tutorials and examples

=item L<http://cairographics.org/manual/>

Contains the reference manual

=back

=head1 AUTHORS

=over

=item Ross McFarland E<lt>rwmcfa1 at neces dot comE<gt>

=item Torsten Schoenfeld E<lt>kaffeetisch at gmx dot deE<gt>

=back

=head1 COPYRIGHT

Copyright (C) 2004-2013 by the cairo perl team

=cut
