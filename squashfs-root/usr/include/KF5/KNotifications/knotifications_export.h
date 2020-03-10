
#ifndef KNOTIFICATIONS_EXPORT_H
#define KNOTIFICATIONS_EXPORT_H

#ifdef KNOTIFICATIONS_STATIC_DEFINE
#  define KNOTIFICATIONS_EXPORT
#  define KNOTIFICATIONS_NO_EXPORT
#else
#  ifndef KNOTIFICATIONS_EXPORT
#    ifdef KF5Notifications_EXPORTS
        /* We are building this library */
#      define KNOTIFICATIONS_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KNOTIFICATIONS_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KNOTIFICATIONS_NO_EXPORT
#    define KNOTIFICATIONS_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KNOTIFICATIONS_DEPRECATED
#  define KNOTIFICATIONS_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KNOTIFICATIONS_DEPRECATED_EXPORT
#  define KNOTIFICATIONS_DEPRECATED_EXPORT KNOTIFICATIONS_EXPORT KNOTIFICATIONS_DEPRECATED
#endif

#ifndef KNOTIFICATIONS_DEPRECATED_NO_EXPORT
#  define KNOTIFICATIONS_DEPRECATED_NO_EXPORT KNOTIFICATIONS_NO_EXPORT KNOTIFICATIONS_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KNOTIFICATIONS_NO_DEPRECATED
#    define KNOTIFICATIONS_NO_DEPRECATED
#  endif
#endif

#endif
