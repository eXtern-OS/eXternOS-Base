#----------------------------------------------------------------
# Generated CMake target import file for configuration "Debian".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "KF5::kauth-policy-gen" for configuration "Debian"
set_property(TARGET KF5::kauth-policy-gen APPEND PROPERTY IMPORTED_CONFIGURATIONS DEBIAN)
set_target_properties(KF5::kauth-policy-gen PROPERTIES
  IMPORTED_LOCATION_DEBIAN "${_IMPORT_PREFIX}/lib/kauth/libexec/kauth-policy-gen"
  )

list(APPEND _IMPORT_CHECK_TARGETS KF5::kauth-policy-gen )
list(APPEND _IMPORT_CHECK_FILES_FOR_KF5::kauth-policy-gen "${_IMPORT_PREFIX}/lib/kauth/libexec/kauth-policy-gen" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
