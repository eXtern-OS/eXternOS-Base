/*

 This file includes config #define's for KWin's libraries
 that are installed. Installed files and files using them
 should be using these instead of their own.

*/

#ifndef KWINCONFIG_H
#define KWINCONFIG_H

/*
 
 These should be primarily used to detect what kind of compositing
 support is available.

*/

/* KWIN_HAVE_XRENDER_COMPOSITING - whether XRender-based compositing support is available */
#define KWIN_HAVE_XRENDER_COMPOSITING

#define HAVE_EPOXY_GLX 1

#define HAVE_DL_LIBRARY 1

#endif
