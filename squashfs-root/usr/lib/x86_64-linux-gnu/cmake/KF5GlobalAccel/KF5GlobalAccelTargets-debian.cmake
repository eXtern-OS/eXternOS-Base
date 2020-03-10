#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debian".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "KF5::GlobalAccel" for configuration "Debian"
set_property(TARGET KF5::GlobalAccel APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::GlobalAccel PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_DEBIAN "Qt5::X11Extras"
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5GlobalAccel.so.5.64.0"
  IMPORTED_SONAME_DEBIAN "libKF5GlobalAccel.so.5"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::GlobalAccel )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::GlobalAccel "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5GlobalAccel.so.5.64.0" )

# Import target "KF5::GlobalAccelPrivate" for configuration "Debian"
set_property(TARGET KF5::GlobalAccelPrivate APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::GlobalAccelPrivate PROPERTIES
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5GlobalAccelPrivate.so.5.64.0"
  IMPORTED_SONAME_DEBIAN "libKF5GlobalAccelPrivate.so.5"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::GlobalAccelPrivate )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::GlobalAccelPrivate "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5GlobalAccelPrivate.so.5.64.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
