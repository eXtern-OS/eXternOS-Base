/*
 * Copyright (c) 2004-2005, 2012 by the cairo perl team (see the file README)
 *
 * Licensed under the LGPL, see LICENSE file for more information.
 *
 * $Id$
 *
 */

#ifndef _CAIRO_PERL_H_
#define _CAIRO_PERL_H_

#include "EXTERN.h"
#include "perl.h"
#include "XSUB.h"

#include <cairo.h>

#ifdef CAIRO_HAS_PNG_SURFACE
# include <cairo-png.h>
#endif

#ifdef CAIRO_HAS_PS_SURFACE
# include <cairo-ps.h>
#endif

#ifdef CAIRO_HAS_PDF_SURFACE
# include <cairo-pdf.h>
#endif

#ifdef CAIRO_HAS_SVG_SURFACE
# include <cairo-svg.h>
#endif

#if CAIRO_HAS_FT_FONT
# include <cairo-ft.h>
#endif

#include <cairo-perl-auto.h>

/*
 * standard object and struct handling
 */
void *cairo_object_from_sv (SV *sv, const char *package);
SV *cairo_object_to_sv (void *object, const char *package);

void *cairo_struct_from_sv (SV *sv, const char *package);
SV *cairo_struct_to_sv (void *object, const char *package);

/*
 * custom struct handling
 */
SV * newSVCairoFontExtents (cairo_font_extents_t *extents);

SV * newSVCairoTextExtents (cairo_text_extents_t *extents);

SV * newSVCairoGlyph (cairo_glyph_t *glyph);
cairo_glyph_t * SvCairoGlyph (SV *sv);

#if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 8, 0)

SV * newSVCairoTextCluster (cairo_text_cluster_t *cluster);
cairo_text_cluster_t * SvCairoTextCluster (SV *sv);

#endif

SV * newSVCairoPath (cairo_path_t *path);
cairo_path_t * SvCairoPath (SV *sv);

#if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 4, 0)

#undef newSVCairoRectangle
#undef SvCairoRectangle
SV * newSVCairoRectangle (cairo_rectangle_t *rectangle);
cairo_rectangle_t * SvCairoRectangle (SV *sv);

#endif

#if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 10, 0)

#undef newSVCairoRectangleInt
#undef SvCairoRectangleInt
SV * newSVCairoRectangleInt (cairo_rectangle_int_t *rectangle);
cairo_rectangle_int_t * SvCairoRectangleInt (SV *sv);

#endif

/*
 * special treatment for surfaces
 */
SV * cairo_surface_to_sv (cairo_surface_t *surface);
#undef newSVCairoSurface
#undef newSVCairoSurface_noinc
#define newSVCairoSurface(object)	(cairo_surface_to_sv (cairo_surface_reference (object)))
#define newSVCairoSurface_noinc(object)	(cairo_surface_to_sv (object))

/*
 * special treatment for patterns
 */
SV * cairo_pattern_to_sv (cairo_pattern_t *surface);
#undef newSVCairoPattern
#undef newSVCairoPattern_noinc
#define newSVCairoPattern(object)	(cairo_pattern_to_sv (cairo_pattern_reference (object)))
#define newSVCairoPattern_noinc(object)	(cairo_pattern_to_sv (object))

/*
 * special treatment for font faces
 */
SV * cairo_font_face_to_sv (cairo_font_face_t *surface);
#undef newSVCairoFontFace
#undef newSVCairoFontFace_noinc
#define newSVCairoFontFace(object)		(cairo_font_face_to_sv (cairo_font_face_reference (object)))
#define newSVCairoFontFace_noinc(object)	(cairo_font_face_to_sv (object))

/*
 * Type aliases for the typemap
 */
typedef char char_utf8;

#endif /* _CAIRO_PERL_H_ */
