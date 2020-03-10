
#ifndef KWINEFFECTS_EXPORT_H
#define KWINEFFECTS_EXPORT_H

#ifdef KWINEFFECTS_STATIC_DEFINE
#  define KWINEFFECTS_EXPORT
#  define KWINEFFECTS_NO_EXPORT
#else
#  ifndef KWINEFFECTS_EXPORT
#    ifdef kwineffects_EXPORTS
        /* We are building this library */
#      define KWINEFFECTS_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KWINEFFECTS_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KWINEFFECTS_NO_EXPORT
#    define KWINEFFECTS_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KWINEFFECTS_DEPRECATED
#  define KWINEFFECTS_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KWINEFFECTS_DEPRECATED_EXPORT
#  define KWINEFFECTS_DEPRECATED_EXPORT KWINEFFECTS_EXPORT KWINEFFECTS_DEPRECATED
#endif

#ifndef KWINEFFECTS_DEPRECATED_NO_EXPORT
#  define KWINEFFECTS_DEPRECATED_NO_EXPORT KWINEFFECTS_NO_EXPORT KWINEFFECTS_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KWINEFFECTS_NO_DEPRECATED
#    define KWINEFFECTS_NO_DEPRECATED
#  endif
#endif

#endif
