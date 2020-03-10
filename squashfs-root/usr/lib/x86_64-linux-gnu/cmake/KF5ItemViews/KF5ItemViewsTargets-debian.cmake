#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debian".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "KF5::ItemViews" for configuration "Debian"
set_property(TARGET KF5::ItemViews APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::ItemViews PROPERTIES
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5ItemViews.so.5.64.0"
  IMPORTED_SONAME_DEBIAN "libKF5ItemViews.so.5"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::ItemViews )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::ItemViews "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5ItemViews.so.5.64.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
