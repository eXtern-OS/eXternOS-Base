/*
 * Copyright (C) 2003-2005, 2010, 2013 by the gtk2-perl team (see the file
 * AUTHORS for the full list)
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Library General Public License as published by
 * the Free Software Foundation; either version 2.1 of the License, or (at your
 * option) any later version.
 *
 * This library is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Library General Public
 * License for more details.
 *
 * You should have received a copy of the GNU Library General Public License
 * along with this library; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 * $Id$
 */

#ifndef _GPERL_H_
#define _GPERL_H_

#include "EXTERN.h"
#include "perl.h"
#include "XSUB.h"

#ifdef WIN32
  /* perl and glib disagree on a few macros... let the wookie win. */
# undef pipe
# undef malloc
# undef realloc
# undef free
#endif

#include <glib-object.h>

/*
 * --- filenames --------------------------------------------------------------
 */
typedef gchar* GPerlFilename;
typedef const gchar* GPerlFilename_const;
typedef gchar* GPerlFilename_own;
typedef GPerlFilename GPerlFilename_ornull;

gchar *gperl_filename_from_sv (SV *sv);
SV *gperl_sv_from_filename (const gchar *filename);

/*
 * --- enums and flags --------------------------------------------------------
 */
gboolean gperl_try_convert_enum (GType type, SV * sv, gint * val);
gint gperl_convert_enum (GType type, SV * val);
SV * gperl_convert_back_enum_pass_unknown (GType type, gint val);
SV * gperl_convert_back_enum (GType type, gint val);

gboolean gperl_try_convert_flag (GType type, const char * val_p, gint * val);
gint gperl_convert_flag_one (GType type, const char * val_p);
gint gperl_convert_flags (GType type, SV * val);
SV * gperl_convert_back_flags (GType type, gint val);

/*
 * --- fundamental types ------------------------------------------------------
 */
typedef struct _GPerlValueWrapperClass GPerlValueWrapperClass;

typedef SV*  (*GPerlValueWrapFunc)   (const GValue * value);
typedef void (*GPerlValueUnwrapFunc) (GValue       * value,
                                      SV           * sv);

struct _GPerlValueWrapperClass {
	GPerlValueWrapFunc   wrap;
	GPerlValueUnwrapFunc unwrap;
};

void gperl_register_fundamental (GType gtype, const char * package);
void gperl_register_fundamental_alias (GType gtype, const char * package);
void gperl_register_fundamental_full (GType gtype, const char * package, GPerlValueWrapperClass * wrapper_class);

GType gperl_fundamental_type_from_package (const char * package);
const char * gperl_fundamental_package_from_type (GType gtype);
GPerlValueWrapperClass * gperl_fundamental_wrapper_class_from_type (GType gtype);

/*
 * --- GErrors as exception objects -------------------------------------------
 */
/* it is rare that you should ever want or need these two functions. */
SV * gperl_sv_from_gerror (GError * error);
void gperl_gerror_from_sv (SV * sv, GError ** error);

void gperl_register_error_domain (GQuark domain,
                                  GType error_enum,
                                  const char * package);

void gperl_croak_gerror (const char * ignored, GError * err);

/*
 * --- inheritance management -------------------------------------------------
 */
/* push @{$parent_package}::ISA, $child_package */
void gperl_set_isa (const char * child_package, const char * parent_package);
/* unshift @{$parent_package}::ISA, $child_package */
void gperl_prepend_isa (const char * child_package, const char * parent_package);

/* these work regardless of what the actual type is (GBoxed, GObject, GEnum,
 * or GFlags).  in general it's safer to use the most specific one, but this
 * is handy when you don't care. */
GType gperl_type_from_package (const char * package);
const char * gperl_package_from_type (GType type);

/*
 * --- gchar converters -------------------------------------------------------
 */
typedef gchar gchar_length; /* length in bytes */
typedef gchar gchar_utf8_length; /* length in characters */
typedef gchar gchar_own;
typedef gchar gchar_ornull;
typedef gchar gchar_own_ornull;

/* clean function wrappers for treating gchar* as UTF8 strings, in the
 * same idiom as the rest of the cast macros.  these are wrapped up
 * as functions because comma expressions in macros get kinda tricky. */
/*const*/ gchar * SvGChar (SV * sv);
SV * newSVGChar (const gchar * str);

/*
 * --- 64 bit integer converters ----------------------------------------------
 */
gint64 SvGInt64 (SV *sv);
SV * newSVGInt64 (gint64 value);
guint64 SvGUInt64 (SV *sv);
SV * newSVGUInt64 (guint64 value);

/*
 * --- GValue -----------------------------------------------------------------
 */
gboolean gperl_value_from_sv (GValue * value, SV * sv);
SV * gperl_sv_from_value (const GValue * value);

/*
 * --- GBoxed -----------------------------------------------------------------
 */
typedef struct _GPerlBoxedWrapperClass GPerlBoxedWrapperClass;

typedef SV*      (*GPerlBoxedWrapFunc)    (GType        gtype,
					   const char * package,
					   gpointer     boxed,
					   gboolean     own);
typedef gpointer (*GPerlBoxedUnwrapFunc)  (GType        gtype,
					   const char * package,
					   SV         * sv);
typedef void     (*GPerlBoxedDestroyFunc) (SV         * sv);

struct _GPerlBoxedWrapperClass {
	GPerlBoxedWrapFunc    wrap;
	GPerlBoxedUnwrapFunc  unwrap;
	GPerlBoxedDestroyFunc destroy;
};

GPerlBoxedWrapperClass * gperl_default_boxed_wrapper_class (void);

void gperl_register_boxed (GType gtype,
			   const char * package,
			   GPerlBoxedWrapperClass * wrapper_class);
void gperl_register_boxed_alias (GType gtype, const char * package);
void gperl_register_boxed_synonym (GType registered_gtype, GType synonym_gtype);

SV * gperl_new_boxed (gpointer boxed, GType gtype, gboolean own);
SV * gperl_new_boxed_copy (gpointer boxed, GType gtype);
gpointer gperl_get_boxed_check (SV * sv, GType gtype);

GType gperl_boxed_type_from_package (const char * package);
const char * gperl_boxed_package_from_type (GType type);

/*
 * we need a GBoxed wrapper for a generic SV, so we can store SVs
 * in GObjects reliably.
 */
#define GPERL_TYPE_SV	(gperl_sv_get_type ())
GType gperl_sv_get_type (void) G_GNUC_CONST;
SV * gperl_sv_copy (SV * sv);
void gperl_sv_free (SV * sv);

/*
 * --- GObject ----------------------------------------------------------------
 */
typedef GObject GObject_ornull;
typedef GObject GObject_noinc;
#define newSVGObject(obj)	(gperl_new_object ((obj), FALSE))
#define newSVGObject_noinc(obj)	(gperl_new_object ((obj), TRUE))
#define SvGObject(sv)		(gperl_get_object_check (sv, G_TYPE_OBJECT))
#define SvGObject_ornull(sv)	(gperl_sv_is_defined (sv) ? SvGObject (sv) : NULL)

void gperl_register_object (GType gtype, const char * package);
void gperl_register_object_alias (GType gtype, const char * package);

typedef void (*GPerlObjectSinkFunc) (GObject *);
void gperl_register_sink_func (GType               gtype,
                               GPerlObjectSinkFunc func);

void gperl_object_set_no_warn_unreg_subclass (GType gtype, gboolean nowarn);

const char * gperl_object_package_from_type (GType gtype);
HV * gperl_object_stash_from_type (GType gtype);
GType gperl_object_type_from_package (const char * package);

SV * gperl_new_object (GObject * object, gboolean own);

GObject * gperl_get_object (SV * sv);
GObject * gperl_get_object_check (SV * sv, GType gtype);

SV * gperl_object_check_type (SV * sv, GType gtype);

void _gperl_attach_mg (SV * sv, void * ptr);
MAGIC * _gperl_find_mg (SV * sv);
void _gperl_remove_mg (SV * sv);

/*
 * --- GSignal ----------------------------------------------------------------
 */
SV * newSVGSignalFlags (GSignalFlags flags);
GSignalFlags SvGSignalFlags (SV * sv);
SV * newSVGSignalInvocationHint (GSignalInvocationHint * ihint);
SV * newSVGSignalQuery (GSignalQuery * query);

void gperl_signal_set_marshaller_for (GType             instance_type,
                                      char            * detailed_signal,
                                      GClosureMarshal   marshaller);
gulong gperl_signal_connect          (SV              * instance,
                                      char            * detailed_signal,
                                      SV              * callback,
                                      SV              * data,
                                      GConnectFlags     flags);

/*
 * --- GClosure ---------------------------------------------------------------
 */
typedef struct _GPerlClosure GPerlClosure;
struct _GPerlClosure {
	GClosure closure;
	SV * callback;
	SV * data; /* callback data */
	gboolean swap; /* TRUE if target and data are to be swapped */
	int id;
};

/* evaluates to true if the instance and data are to be swapped on invocation */
#define GPERL_CLOSURE_SWAP_DATA(gpc)	((gpc)->swap)

/* this is the one you want. */
GClosure * gperl_closure_new                 (SV              * callback, 
                                              SV              * data, 
                                              gboolean          swap);
/* very scary, use only if you really know what you are doing */
GClosure * gperl_closure_new_with_marshaller (SV              * callback, 
                                              SV              * data, 
                                              gboolean          swap,
                                              GClosureMarshal   marshaller);

/*
 * --- GPerlCallback ----------------------------------------------------------
 */
typedef struct _GPerlCallback GPerlCallback;
struct _GPerlCallback {
	gint    n_params;
	GType * param_types;
	GType   return_type;
	SV    * func;
	SV    * data;
	void  * priv;
};

GPerlCallback * gperl_callback_new     (SV            * func,
                                        SV            * data,
                                        gint            n_params,
                                        GType           param_types[],
					GType           return_type);

void            gperl_callback_destroy (GPerlCallback * callback);

void            gperl_callback_invoke  (GPerlCallback * callback,
                                        GValue        * return_value,
                                        ...);

/*
 * --- exception handling -----------------------------------------------------
 */
int  gperl_install_exception_handler (GClosure * closure);
void gperl_remove_exception_handler  (guint tag);
void gperl_run_exception_handlers    (void);

/*
 * --- log handling for extensions --------------------------------------------
 */
gint gperl_handle_logs_for (const gchar * log_domain);

/*
 * --- GParamSpec -------------------------------------------------------------
 */
typedef GParamSpec GParamSpec_ornull;
SV * newSVGParamSpec (GParamSpec * pspec);
GParamSpec * SvGParamSpec (SV * sv);
#define newSVGParamSpec_ornull(sv)	newSVGParamSpec(sv)

SV * newSVGParamFlags (GParamFlags flags);
GParamFlags SvGParamFlags (SV * sv);

void gperl_register_param_spec (GType gtype, const char * package);
const char * gperl_param_spec_package_from_type (GType gtype);
GType gperl_param_spec_type_from_package (const char * package);

/*
 * --- GKeyFile ---------------------------------------------------------------
 */
#if GLIB_CHECK_VERSION (2, 6, 0)
SV * newSVGKeyFile (GKeyFile * key_file);
GKeyFile * SvGKeyFile (SV * sv);
SV * newSVGKeyFileFlags (GKeyFileFlags flags);
GKeyFileFlags SvGKeyFileFlags (SV * sv);
#endif /* GLIB_CHECK_VERSION (2, 6, 0) */

/*
 * --- GBookmarkFile ----------------------------------------------------------
 */
#if GLIB_CHECK_VERSION (2, 12, 0)
SV * newSVGBookmarkFile (GBookmarkFile * bookmark_file);
GBookmarkFile * SvGBookmarkFile (SV * sv);
#endif /* GLIB_CHECK_VERSION (2, 12, 0) */

/*
 * --- GOption ----------------------------------------------------------------
 */
#if GLIB_CHECK_VERSION (2, 6, 0)

typedef GOptionContext GOptionContext_own;

#define GPERL_TYPE_OPTION_CONTEXT (gperl_option_context_get_type ())
GType gperl_option_context_get_type (void);

#define SvGOptionContext(sv)		(gperl_get_boxed_check ((sv), GPERL_TYPE_OPTION_CONTEXT))
#define newSVGOptionContext(val)	(gperl_new_boxed ((gpointer) (val), GPERL_TYPE_OPTION_CONTEXT, FALSE))
#define newSVGOptionContext_own(val)	(gperl_new_boxed ((gpointer) (val), GPERL_TYPE_OPTION_CONTEXT, TRUE))

typedef GOptionGroup GOptionGroup_own;

#define GPERL_TYPE_OPTION_GROUP (gperl_option_group_get_type ())
GType gperl_option_group_get_type (void);

#define SvGOptionGroup(sv)		(gperl_get_boxed_check ((sv), GPERL_TYPE_OPTION_GROUP))
#define newSVGOptionGroup(val)		(gperl_new_boxed ((gpointer) (val), GPERL_TYPE_OPTION_GROUP, FALSE))
#define newSVGOptionGroup_own(val)	(gperl_new_boxed ((gpointer) (val), GPERL_TYPE_OPTION_GROUP, TRUE))

#endif /* 2.6.0 */

/*
 * --- gutils.h / GUtils.xs ---------------------------------------------------
 */
#if GLIB_CHECK_VERSION (2, 14, 0)
GUserDirectory SvGUserDirectory (SV *sv);
SV * newSVGUserDirectory (GUserDirectory dir);
#endif

/*
 * --- GVariant ---------------------------------------------------------------
 */
#if GLIB_CHECK_VERSION (2, 24, 0)

typedef GVariant GVariant_noinc;
SV * newSVGVariant (GVariant * variant);
SV * newSVGVariant_noinc (GVariant * variant);
GVariant * SvGVariant (SV * sv);

typedef GVariantType GVariantType_own;
SV * newSVGVariantType (const GVariantType * type);
SV * newSVGVariantType_own (const GVariantType * type);
const GVariantType * SvGVariantType (SV * sv);

#endif /* 2.24.0 */

/*
 * --- GBytes -----------------------------------------------------------------
 */
#if GLIB_CHECK_VERSION (2, 32, 0)
typedef GBytes GBytes_own;
#define SvGBytes(sv)		(gperl_get_boxed_check ((sv), G_TYPE_BYTES))
#define newSVGBytes(val)	(gperl_new_boxed ((gpointer) (val), G_TYPE_BYTES, FALSE))
#define newSVGBytes_own(val)	(gperl_new_boxed ((gpointer) (val), G_TYPE_BYTES, TRUE))
#endif

/*
 * --- miscellaneous ----------------------------------------------------------
 */

/* for use with the typemap */
typedef char char_ornull;
typedef char char_own;
typedef char char_own_ornull;
typedef char char_byte;
typedef char char_byte_ornull;

/* never use this function directly.  use GPERL_CALL_BOOT. */
void _gperl_call_XS (pTHX_ void (*subaddr) (pTHX_ CV *), CV * cv, SV ** mark);

/*
 * call the boot code of a module by symbol rather than by name.
 *
 * in a perl extension which uses several xs files but only one pm, you
 * need to bootstrap the other xs files in order to get their functions
 * exported to perl.  if the file has MODULE = Foo::Bar, the boot symbol
 * would be boot_Foo__Bar.
 */
#ifndef XS_EXTERNAL
# define XS_EXTERNAL(name) XS(name)
#endif
#define GPERL_CALL_BOOT(name)	\
	{						\
		extern XS_EXTERNAL (name);		\
		_gperl_call_XS (aTHX_ name, cv, mark);	\
	}

gpointer gperl_alloc_temp (int nbytes);

gboolean gperl_str_eq (const char * a, const char * b);
guint    gperl_str_hash (gconstpointer key);

typedef struct {
  int argc;
  char **argv;
  void *priv;
} GPerlArgv;

GPerlArgv * gperl_argv_new (void);
void gperl_argv_update (GPerlArgv *pargv);
void gperl_argv_free (GPerlArgv *pargv);

char * gperl_format_variable_for_output (SV * sv);

gboolean gperl_sv_is_defined (SV *sv);

#define gperl_sv_is_ref(sv) \
	(gperl_sv_is_defined (sv) && SvROK (sv))
#define gperl_sv_is_array_ref(sv) \
	(gperl_sv_is_ref (sv) && SvTYPE (SvRV(sv)) == SVt_PVAV)
#define gperl_sv_is_code_ref(sv) \
	(gperl_sv_is_ref (sv) && SvTYPE (SvRV(sv)) == SVt_PVCV)
#define gperl_sv_is_hash_ref(sv) \
	(gperl_sv_is_ref (sv) && SvTYPE (SvRV(sv)) == SVt_PVHV)

void gperl_hv_take_sv (HV *hv, const char *key, size_t key_length, SV *sv);

/* helper wrapper for static string literals.  concatenating with "" enforces
 * the restriction. */
#define gperl_hv_take_sv_s(hv, key, sv) \
	gperl_hv_take_sv (hv, "" key "", sizeof(key) - 1, sv)

/* internal trickery */
gpointer gperl_type_class (GType type);

/*
 * helpful debugging stuff
 */
#define GPERL_OBJECT_VITALS(o) \
	((o)							\
	  ? form ("%s(%p)[%d]", G_OBJECT_TYPE_NAME (o), (o),	\
		  G_OBJECT (o)->ref_count)			\
	  : "NULL")
#define GPERL_WRAPPER_VITALS(w)	\
	((SvTRUE (w))					\
	  ? ((SvROK (w))				\
	    ? form ("SvRV(%p)->%s(%p)[%d]", (w),	\
		     sv_reftype (SvRV (w), TRUE),	\
		     SvRV (w), SvREFCNT (SvRV (w)))	\
	     : "[not a reference!]")			\
	  : "undef")

#endif /* _GPERL_H_ */
