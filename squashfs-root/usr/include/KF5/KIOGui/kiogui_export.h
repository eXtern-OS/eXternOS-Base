
#ifndef KIOGUI_EXPORT_H
#define KIOGUI_EXPORT_H

#ifdef KIOGUI_STATIC_DEFINE
#  define KIOGUI_EXPORT
#  define KIOGUI_NO_EXPORT
#else
#  ifndef KIOGUI_EXPORT
#    ifdef KF5KIOGui_EXPORTS
        /* We are building this library */
#      define KIOGUI_EXPORT __attribute__((visibility("default")))
#    else
        /* We are using this library */
#      define KIOGUI_EXPORT __attribute__((visibility("default")))
#    endif
#  endif

#  ifndef KIOGUI_NO_EXPORT
#    define KIOGUI_NO_EXPORT __attribute__((visibility("hidden")))
#  endif
#endif

#ifndef KIOGUI_DEPRECATED
#  define KIOGUI_DEPRECATED __attribute__ ((__deprecated__))
#endif

#ifndef KIOGUI_DEPRECATED_EXPORT
#  define KIOGUI_DEPRECATED_EXPORT KIOGUI_EXPORT KIOGUI_DEPRECATED
#endif

#ifndef KIOGUI_DEPRECATED_NO_EXPORT
#  define KIOGUI_DEPRECATED_NO_EXPORT KIOGUI_NO_EXPORT KIOGUI_DEPRECATED
#endif

#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef KIOGUI_NO_DEPRECATED
#    define KIOGUI_NO_DEPRECATED
#  endif
#endif

#endif
