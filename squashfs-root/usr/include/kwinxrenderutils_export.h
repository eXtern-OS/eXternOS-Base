
#ifndef KWINXRENDERUTILS_EXPORT_H
#define KWINXRENDERUTILS_EXPORT_H

#ifdef KWINXRENDERUTILS_STATIC_DEFINE
#  define KWINXRENDERUTILS_EXPORT
#  define KWINXRENDERUTILS_NO_EXPORT
#else
#  ifndef KWINXRENDERUTILS_EXPORT
#    ifdef kwinxrenderutils_EXPORTS
        /* We are building this library */
#      define KWINXRENDERUTILS_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KWINXRENDERUTILS_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KWINXRENDERUTILS_NO_EXPORT
#    define KWINXRENDERUTILS_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KWINXRENDERUTILS_DEPRECATED
#  define KWINXRENDERUTILS_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KWINXRENDERUTILS_DEPRECATED_EXPORT
#  define KWINXRENDERUTILS_DEPRECATED_EXPORT KWINXRENDERUTILS_EXPORT KWINXRENDERUTILS_DEPRECATED
#endif

#ifndef KWINXRENDERUTILS_DEPRECATED_NO_EXPORT
#  define KWINXRENDERUTILS_DEPRECATED_NO_EXPORT KWINXRENDERUTILS_NO_EXPORT KWINXRENDERUTILS_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KWINXRENDERUTILS_NO_DEPRECATED
#    define KWINXRENDERUTILS_NO_DEPRECATED
#  endif
#endif

#endif
