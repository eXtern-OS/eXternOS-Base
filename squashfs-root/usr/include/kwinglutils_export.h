
#ifndef KWINGLUTILS_EXPORT_H
#define KWINGLUTILS_EXPORT_H

#ifdef KWINGLUTILS_STATIC_DEFINE
#  define KWINGLUTILS_EXPORT
#  define KWINGLUTILS_NO_EXPORT
#else
#  ifndef KWINGLUTILS_EXPORT
#    ifdef kwinglutils_EXPORTS
        /* We are building this library */
#      define KWINGLUTILS_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KWINGLUTILS_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KWINGLUTILS_NO_EXPORT
#    define KWINGLUTILS_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KWINGLUTILS_DEPRECATED
#  define KWINGLUTILS_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KWINGLUTILS_DEPRECATED_EXPORT
#  define KWINGLUTILS_DEPRECATED_EXPORT KWINGLUTILS_EXPORT KWINGLUTILS_DEPRECATED
#endif

#ifndef KWINGLUTILS_DEPRECATED_NO_EXPORT
#  define KWINGLUTILS_DEPRECATED_NO_EXPORT KWINGLUTILS_NO_EXPORT KWINGLUTILS_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KWINGLUTILS_NO_DEPRECATED
#    define KWINGLUTILS_NO_DEPRECATED
#  endif
#endif

#endif
