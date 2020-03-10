
#ifndef KWIN_EXPORT_H
#define KWIN_EXPORT_H

#ifdef KWIN_STATIC_DEFINE
#  define KWIN_EXPORT
#  define KWIN_NO_EXPORT
#else
#  ifndef KWIN_EXPORT
#    ifdef kwin_EXPORTS
        /* We are building this library */
#      define KWIN_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KWIN_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KWIN_NO_EXPORT
#    define KWIN_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KWIN_DEPRECATED
#  define KWIN_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KWIN_DEPRECATED_EXPORT
#  define KWIN_DEPRECATED_EXPORT KWIN_EXPORT KWIN_DEPRECATED
#endif

#ifndef KWIN_DEPRECATED_NO_EXPORT
#  define KWIN_DEPRECATED_NO_EXPORT KWIN_NO_EXPORT KWIN_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KWIN_NO_DEPRECATED
#    define KWIN_NO_DEPRECATED
#  endif
#endif

#endif
