
#ifndef KAUTHCORE_EXPORT_H
#define KAUTHCORE_EXPORT_H

#ifdef KAUTHCORE_STATIC_DEFINE
#  define KAUTHCORE_EXPORT
#  define KAUTHCORE_NO_EXPORT
#else
#  ifndef KAUTHCORE_EXPORT
#    ifdef KF5AuthCore_EXPORTS
        /* We are building this library */
#      define KAUTHCORE_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KAUTHCORE_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KAUTHCORE_NO_EXPORT
#    define KAUTHCORE_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KAUTHCORE_DEPRECATED
#  define KAUTHCORE_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KAUTHCORE_DEPRECATED_EXPORT
#  define KAUTHCORE_DEPRECATED_EXPORT KAUTHCORE_EXPORT KAUTHCORE_DEPRECATED
#endif

#ifndef KAUTHCORE_DEPRECATED_NO_EXPORT
#  define KAUTHCORE_DEPRECATED_NO_EXPORT KAUTHCORE_NO_EXPORT KAUTHCORE_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KAUTHCORE_NO_DEPRECATED
#    define KAUTHCORE_NO_DEPRECATED
#  endif
#endif

#endif
