
#ifndef KNTLM_EXPORT_H
#define KNTLM_EXPORT_H

#ifdef KNTLM_STATIC_DEFINE
#  define KNTLM_EXPORT
#  define KNTLM_NO_EXPORT
#else
#  ifndef KNTLM_EXPORT
#    ifdef KF5KIONTLM_EXPORTS
        /* We are building this library */
#      define KNTLM_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KNTLM_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KNTLM_NO_EXPORT
#    define KNTLM_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KNTLM_DEPRECATED
#  define KNTLM_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KNTLM_DEPRECATED_EXPORT
#  define KNTLM_DEPRECATED_EXPORT KNTLM_EXPORT KNTLM_DEPRECATED
#endif

#ifndef KNTLM_DEPRECATED_NO_EXPORT
#  define KNTLM_DEPRECATED_NO_EXPORT KNTLM_NO_EXPORT KNTLM_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KNTLM_NO_DEPRECATED
#    define KNTLM_NO_DEPRECATED
#  endif
#endif

#endif
