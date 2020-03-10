
#ifndef KJOBWIDGETS_EXPORT_H
#define KJOBWIDGETS_EXPORT_H

#ifdef KJOBWIDGETS_STATIC_DEFINE
#  define KJOBWIDGETS_EXPORT
#  define KJOBWIDGETS_NO_EXPORT
#else
#  ifndef KJOBWIDGETS_EXPORT
#    ifdef KF5JobWidgets_EXPORTS
        /* We are building this library */
#      define KJOBWIDGETS_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KJOBWIDGETS_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KJOBWIDGETS_NO_EXPORT
#    define KJOBWIDGETS_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KJOBWIDGETS_DEPRECATED
#  define KJOBWIDGETS_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KJOBWIDGETS_DEPRECATED_EXPORT
#  define KJOBWIDGETS_DEPRECATED_EXPORT KJOBWIDGETS_EXPORT KJOBWIDGETS_DEPRECATED
#endif

#ifndef KJOBWIDGETS_DEPRECATED_NO_EXPORT
#  define KJOBWIDGETS_DEPRECATED_NO_EXPORT KJOBWIDGETS_NO_EXPORT KJOBWIDGETS_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KJOBWIDGETS_NO_DEPRECATED
#    define KJOBWIDGETS_NO_DEPRECATED
#  endif
#endif

#endif
