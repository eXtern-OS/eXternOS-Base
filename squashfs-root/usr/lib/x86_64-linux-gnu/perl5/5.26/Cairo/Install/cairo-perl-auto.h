/*
 * This file was automatically generated.  Do not edit.
 */

#include <cairo.h>

/* objects */

typedef cairo_font_face_t cairo_font_face_t_noinc;
typedef cairo_font_face_t cairo_font_face_t_ornull;
#define SvCairoFontFace(sv)			((cairo_font_face_t *) cairo_object_from_sv (sv, "Cairo::FontFace"))
#define SvCairoFontFace_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoFontFace(sv) : NULL)
#define newSVCairoFontFace(object)		(cairo_object_to_sv ((cairo_font_face_t *) cairo_font_face_reference (object), "Cairo::FontFace"))
#define newSVCairoFontFace_noinc(object)	(cairo_object_to_sv ((cairo_font_face_t *) object, "Cairo::FontFace"))
#define newSVCairoFontFace_ornull(object)	(((object) == NULL) ? &PL_sv_undef : newSVCairoFontFace(object))
typedef cairo_pattern_t cairo_pattern_t_noinc;
typedef cairo_pattern_t cairo_pattern_t_ornull;
#define SvCairoPattern(sv)			((cairo_pattern_t *) cairo_object_from_sv (sv, "Cairo::Pattern"))
#define SvCairoPattern_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoPattern(sv) : NULL)
#define newSVCairoPattern(object)		(cairo_object_to_sv ((cairo_pattern_t *) cairo_pattern_reference (object), "Cairo::Pattern"))
#define newSVCairoPattern_noinc(object)	(cairo_object_to_sv ((cairo_pattern_t *) object, "Cairo::Pattern"))
#define newSVCairoPattern_ornull(object)	(((object) == NULL) ? &PL_sv_undef : newSVCairoPattern(object))
#if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 10, 0)
typedef cairo_region_t cairo_region_t_noinc;
typedef cairo_region_t cairo_region_t_ornull;
#define SvCairoRegion(sv)			((cairo_region_t *) cairo_object_from_sv (sv, "Cairo::Region"))
#define SvCairoRegion_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoRegion(sv) : NULL)
#define newSVCairoRegion(object)		(cairo_object_to_sv ((cairo_region_t *) cairo_region_reference (object), "Cairo::Region"))
#define newSVCairoRegion_noinc(object)	(cairo_object_to_sv ((cairo_region_t *) object, "Cairo::Region"))
#define newSVCairoRegion_ornull(object)	(((object) == NULL) ? &PL_sv_undef : newSVCairoRegion(object))
#endif /* #if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 10, 0) */
typedef cairo_scaled_font_t cairo_scaled_font_t_noinc;
typedef cairo_scaled_font_t cairo_scaled_font_t_ornull;
#define SvCairoScaledFont(sv)			((cairo_scaled_font_t *) cairo_object_from_sv (sv, "Cairo::ScaledFont"))
#define SvCairoScaledFont_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoScaledFont(sv) : NULL)
#define newSVCairoScaledFont(object)		(cairo_object_to_sv ((cairo_scaled_font_t *) cairo_scaled_font_reference (object), "Cairo::ScaledFont"))
#define newSVCairoScaledFont_noinc(object)	(cairo_object_to_sv ((cairo_scaled_font_t *) object, "Cairo::ScaledFont"))
#define newSVCairoScaledFont_ornull(object)	(((object) == NULL) ? &PL_sv_undef : newSVCairoScaledFont(object))
typedef cairo_surface_t cairo_surface_t_noinc;
typedef cairo_surface_t cairo_surface_t_ornull;
#define SvCairoSurface(sv)			((cairo_surface_t *) cairo_object_from_sv (sv, "Cairo::Surface"))
#define SvCairoSurface_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoSurface(sv) : NULL)
#define newSVCairoSurface(object)		(cairo_object_to_sv ((cairo_surface_t *) cairo_surface_reference (object), "Cairo::Surface"))
#define newSVCairoSurface_noinc(object)	(cairo_object_to_sv ((cairo_surface_t *) object, "Cairo::Surface"))
#define newSVCairoSurface_ornull(object)	(((object) == NULL) ? &PL_sv_undef : newSVCairoSurface(object))
typedef cairo_t cairo_t_noinc;
typedef cairo_t cairo_t_ornull;
#define SvCairo(sv)			((cairo_t *) cairo_object_from_sv (sv, "Cairo::Context"))
#define SvCairo_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairo(sv) : NULL)
#define newSVCairo(object)		(cairo_object_to_sv ((cairo_t *) cairo_reference (object), "Cairo::Context"))
#define newSVCairo_noinc(object)	(cairo_object_to_sv ((cairo_t *) object, "Cairo::Context"))
#define newSVCairo_ornull(object)	(((object) == NULL) ? &PL_sv_undef : newSVCairo(object))

/* structs */

typedef cairo_font_options_t cairo_font_options_t_ornull;
#define SvCairoFontOptions(sv)			((cairo_font_options_t *) cairo_struct_from_sv (sv, "Cairo::FontOptions"))
#define SvCairoFontOptions_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoFontOptions(sv) : NULL)
#define newSVCairoFontOptions(struct_)		(cairo_struct_to_sv ((cairo_font_options_t *) struct_, "Cairo::FontOptions"))
#define newSVCairoFontOptions_ornull(struct_)	(((struct_) == NULL) ? &PL_sv_undef : newSVCairoFontOptions(struct_))
typedef cairo_matrix_t cairo_matrix_t_ornull;
#define SvCairoMatrix(sv)			((cairo_matrix_t *) cairo_struct_from_sv (sv, "Cairo::Matrix"))
#define SvCairoMatrix_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoMatrix(sv) : NULL)
#define newSVCairoMatrix(struct_)		(cairo_struct_to_sv ((cairo_matrix_t *) struct_, "Cairo::Matrix"))
#define newSVCairoMatrix_ornull(struct_)	(((struct_) == NULL) ? &PL_sv_undef : newSVCairoMatrix(struct_))
#if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 10, 0)
typedef cairo_rectangle_int_t cairo_rectangle_int_t_ornull;
#define SvCairoRectangleInt(sv)			((cairo_rectangle_int_t *) cairo_struct_from_sv (sv, "Cairo::RectangleInt"))
#define SvCairoRectangleInt_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoRectangleInt(sv) : NULL)
#define newSVCairoRectangleInt(struct_)		(cairo_struct_to_sv ((cairo_rectangle_int_t *) struct_, "Cairo::RectangleInt"))
#define newSVCairoRectangleInt_ornull(struct_)	(((struct_) == NULL) ? &PL_sv_undef : newSVCairoRectangleInt(struct_))
#endif /* #if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 10, 0) */
#if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 4, 0)
typedef cairo_rectangle_t cairo_rectangle_t_ornull;
#define SvCairoRectangle(sv)			((cairo_rectangle_t *) cairo_struct_from_sv (sv, "Cairo::Rectangle"))
#define SvCairoRectangle_ornull(sv)		(((sv) && SvOK (sv)) ? SvCairoRectangle(sv) : NULL)
#define newSVCairoRectangle(struct_)		(cairo_struct_to_sv ((cairo_rectangle_t *) struct_, "Cairo::Rectangle"))
#define newSVCairoRectangle_ornull(struct_)	(((struct_) == NULL) ? &PL_sv_undef : newSVCairoRectangle(struct_))
#endif /* #if CAIRO_VERSION >= CAIRO_VERSION_ENCODE(1, 4, 0) */

/* enums */

cairo_antialias_t cairo_antialias_from_sv (SV * antialias);
SV * cairo_antialias_to_sv (cairo_antialias_t val);
#define SvCairoAntialias(sv)		(cairo_antialias_from_sv (sv))
#define newSVCairoAntialias(val)	(cairo_antialias_to_sv (val))
cairo_content_t cairo_content_from_sv (SV * content);
SV * cairo_content_to_sv (cairo_content_t val);
#define SvCairoContent(sv)		(cairo_content_from_sv (sv))
#define newSVCairoContent(val)	(cairo_content_to_sv (val))
cairo_extend_t cairo_extend_from_sv (SV * extend);
SV * cairo_extend_to_sv (cairo_extend_t val);
#define SvCairoExtend(sv)		(cairo_extend_from_sv (sv))
#define newSVCairoExtend(val)	(cairo_extend_to_sv (val))
cairo_fill_rule_t cairo_fill_rule_from_sv (SV * fill_rule);
SV * cairo_fill_rule_to_sv (cairo_fill_rule_t val);
#define SvCairoFillRule(sv)		(cairo_fill_rule_from_sv (sv))
#define newSVCairoFillRule(val)	(cairo_fill_rule_to_sv (val))
cairo_filter_t cairo_filter_from_sv (SV * filter);
SV * cairo_filter_to_sv (cairo_filter_t val);
#define SvCairoFilter(sv)		(cairo_filter_from_sv (sv))
#define newSVCairoFilter(val)	(cairo_filter_to_sv (val))
cairo_font_slant_t cairo_font_slant_from_sv (SV * font_slant);
SV * cairo_font_slant_to_sv (cairo_font_slant_t val);
#define SvCairoFontSlant(sv)		(cairo_font_slant_from_sv (sv))
#define newSVCairoFontSlant(val)	(cairo_font_slant_to_sv (val))
cairo_font_type_t cairo_font_type_from_sv (SV * font_type);
SV * cairo_font_type_to_sv (cairo_font_type_t val);
#define SvCairoFontType(sv)		(cairo_font_type_from_sv (sv))
#define newSVCairoFontType(val)	(cairo_font_type_to_sv (val))
cairo_font_weight_t cairo_font_weight_from_sv (SV * font_weight);
SV * cairo_font_weight_to_sv (cairo_font_weight_t val);
#define SvCairoFontWeight(sv)		(cairo_font_weight_from_sv (sv))
#define newSVCairoFontWeight(val)	(cairo_font_weight_to_sv (val))
cairo_format_t cairo_format_from_sv (SV * format);
SV * cairo_format_to_sv (cairo_format_t val);
#define SvCairoFormat(sv)		(cairo_format_from_sv (sv))
#define newSVCairoFormat(val)	(cairo_format_to_sv (val))
cairo_hint_metrics_t cairo_hint_metrics_from_sv (SV * hint_metrics);
SV * cairo_hint_metrics_to_sv (cairo_hint_metrics_t val);
#define SvCairoHintMetrics(sv)		(cairo_hint_metrics_from_sv (sv))
#define newSVCairoHintMetrics(val)	(cairo_hint_metrics_to_sv (val))
cairo_hint_style_t cairo_hint_style_from_sv (SV * hint_style);
SV * cairo_hint_style_to_sv (cairo_hint_style_t val);
#define SvCairoHintStyle(sv)		(cairo_hint_style_from_sv (sv))
#define newSVCairoHintStyle(val)	(cairo_hint_style_to_sv (val))
cairo_line_cap_t cairo_line_cap_from_sv (SV * line_cap);
SV * cairo_line_cap_to_sv (cairo_line_cap_t val);
#define SvCairoLineCap(sv)		(cairo_line_cap_from_sv (sv))
#define newSVCairoLineCap(val)	(cairo_line_cap_to_sv (val))
cairo_line_join_t cairo_line_join_from_sv (SV * line_join);
SV * cairo_line_join_to_sv (cairo_line_join_t val);
#define SvCairoLineJoin(sv)		(cairo_line_join_from_sv (sv))
#define newSVCairoLineJoin(val)	(cairo_line_join_to_sv (val))
cairo_operator_t cairo_operator_from_sv (SV * operator);
SV * cairo_operator_to_sv (cairo_operator_t val);
#define SvCairoOperator(sv)		(cairo_operator_from_sv (sv))
#define newSVCairoOperator(val)	(cairo_operator_to_sv (val))
cairo_path_data_type_t cairo_path_data_type_from_sv (SV * path_data_type);
SV * cairo_path_data_type_to_sv (cairo_path_data_type_t val);
#define SvCairoPathDataType(sv)		(cairo_path_data_type_from_sv (sv))
#define newSVCairoPathDataType(val)	(cairo_path_data_type_to_sv (val))
cairo_pattern_type_t cairo_pattern_type_from_sv (SV * pattern_type);
SV * cairo_pattern_type_to_sv (cairo_pattern_type_t val);
#define SvCairoPatternType(sv)		(cairo_pattern_type_from_sv (sv))
#define newSVCairoPatternType(val)	(cairo_pattern_type_to_sv (val))
cairo_pdf_version_t cairo_pdf_version_from_sv (SV * pdf_version);
SV * cairo_pdf_version_to_sv (cairo_pdf_version_t val);
#define SvCairoPdfVersion(sv)		(cairo_pdf_version_from_sv (sv))
#define newSVCairoPdfVersion(val)	(cairo_pdf_version_to_sv (val))
#ifdef CAIRO_HAS_PS_SURFACE
cairo_ps_level_t cairo_ps_level_from_sv (SV * ps_level);
SV * cairo_ps_level_to_sv (cairo_ps_level_t val);
#define SvCairoPsLevel(sv)		(cairo_ps_level_from_sv (sv))
#define newSVCairoPsLevel(val)	(cairo_ps_level_to_sv (val))
#endif /* #ifdef CAIRO_HAS_PS_SURFACE */
cairo_region_overlap_t cairo_region_overlap_from_sv (SV * region_overlap);
SV * cairo_region_overlap_to_sv (cairo_region_overlap_t val);
#define SvCairoRegionOverlap(sv)		(cairo_region_overlap_from_sv (sv))
#define newSVCairoRegionOverlap(val)	(cairo_region_overlap_to_sv (val))
cairo_status_t cairo_status_from_sv (SV * status);
SV * cairo_status_to_sv (cairo_status_t val);
#define SvCairoStatus(sv)		(cairo_status_from_sv (sv))
#define newSVCairoStatus(val)	(cairo_status_to_sv (val))
cairo_subpixel_order_t cairo_subpixel_order_from_sv (SV * subpixel_order);
SV * cairo_subpixel_order_to_sv (cairo_subpixel_order_t val);
#define SvCairoSubpixelOrder(sv)		(cairo_subpixel_order_from_sv (sv))
#define newSVCairoSubpixelOrder(val)	(cairo_subpixel_order_to_sv (val))
cairo_surface_type_t cairo_surface_type_from_sv (SV * surface_type);
SV * cairo_surface_type_to_sv (cairo_surface_type_t val);
#define SvCairoSurfaceType(sv)		(cairo_surface_type_from_sv (sv))
#define newSVCairoSurfaceType(val)	(cairo_surface_type_to_sv (val))
#ifdef CAIRO_HAS_SVG_SURFACE
cairo_svg_version_t cairo_svg_version_from_sv (SV * svg_version);
SV * cairo_svg_version_to_sv (cairo_svg_version_t val);
#define SvCairoSvgVersion(sv)		(cairo_svg_version_from_sv (sv))
#define newSVCairoSvgVersion(val)	(cairo_svg_version_to_sv (val))
#endif /* #ifdef CAIRO_HAS_SVG_SURFACE */

/* flags */

cairo_text_cluster_flags_t cairo_text_cluster_flags_from_sv (SV * text_cluster_flags);
SV * cairo_text_cluster_flags_to_sv (cairo_text_cluster_flags_t val);
#define SvCairoTextClusterFlags(sv)		(cairo_text_cluster_flags_from_sv (sv))
#define newSVCairoTextClusterFlags(val)	(cairo_text_cluster_flags_to_sv (val))
