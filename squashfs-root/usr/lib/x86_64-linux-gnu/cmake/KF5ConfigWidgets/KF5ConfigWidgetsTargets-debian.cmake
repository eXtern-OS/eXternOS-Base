#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debian".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "KF5::ConfigWidgets" for configuration "Debian"
set_property(TARGET KF5::ConfigWidgets APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::ConfigWidgets PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_DEBIAN "KF5::CoreAddons;KF5::GuiAddons;KF5::I18n;Qt5::DBus"
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5ConfigWidgets.so.5.64.0"
  IMPORTED_SONAME_DEBIAN "libKF5ConfigWidgets.so.5"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::ConfigWidgets )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::ConfigWidgets "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libKF5ConfigWidgets.so.5.64.0" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
