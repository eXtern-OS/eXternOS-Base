#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debian".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "KF5::SonnetCore" for configuration "Debian"
set_property(TARGET KF5::SonnetCore APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::SonnetCore PROPERTIES
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5SonnetCore.so.5.64.0"
  IMPORTED_SONAME_DEBIAN "libKF5SonnetCore.so.5"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::SonnetCore )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::SonnetCore "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5SonnetCore.so.5.64.0" )

# Import target "KF5::SonnetUi" for configuration "Debian"
set_property(TARGET KF5::SonnetUi APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::SonnetUi PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_DEBIAN "KF5::SonnetCore"
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5SonnetUi.so.5.64.0"
  IMPORTED_SONAME_DEBIAN "libKF5SonnetUi.so.5"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::SonnetUi )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::SonnetUi "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5SonnetUi.so.5.64.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
