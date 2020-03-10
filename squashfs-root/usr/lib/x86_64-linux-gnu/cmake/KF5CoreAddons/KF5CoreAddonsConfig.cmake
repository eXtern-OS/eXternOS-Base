
####### Expanded from @PACKAGE_INIT@ by configure_package_config_file() #######
####### Any changes to this file will be overwritten by the next CMake run ####
####### The input file was KF5CoreAddonsConfig.cmake.in                            ########

get_filename_component(PACKAGE_PREFIX_DIR "${CMAKE_CURRENT_LIST_DIR}/../../../../" ABSOLUTE)

# Use original install prefix when loaded through a "/usr move"
# cross-prefix symbolic link such as /lib -> /usr/lib.
get_filename_component(_realCurr "${CMAKE_CURRENT_LIST_DIR}" REALPATH)
get_filename_component(_realOrig "/usr/lib/x86_64-linux-gnu/cmake/KF5CoreAddons" REALPATH)
if(_realCurr STREQUAL _realOrig)
  set(PACKAGE_PREFIX_DIR "/usr")
endif()
unset(_realOrig)
unset(_realCurr)

macro(set_and_check _var _file)
  set(${_var} "${_file}")
  if(NOT EXISTS "${_file}")
    message(FATAL_ERROR "File or directory ${_file} referenced by variable ${_var} does not exist !")
  endif()
endmacro()

macro(check_required_components _NAME)
  foreach(comp ${${_NAME}_FIND_COMPONENTS})
    if(NOT ${_NAME}_${comp}_FOUND)
      if(${_NAME}_FIND_REQUIRED_${comp})
        set(${_NAME}_FOUND FALSE)
      endif()
    endif()
  endforeach()
endmacro()

####################################################################################

include(CMakeFindDependencyMacro)
find_dependency(Qt5Core 5.11.0)

####################################################################################
# CMAKE_AUTOMOC

if(NOT CMAKE_VERSION VERSION_LESS "3.10.0")
    # CMake 3.9+ warns about automoc on files without Q_OBJECT, and doesn't know about other macros.
    # 3.10+ lets us provide more macro names that require automoc.
    list(APPEND CMAKE_AUTOMOC_MACRO_NAMES K_PLUGIN_FACTORY;K_PLUGIN_FACTORY_WITH_JSON;K_PLUGIN_CLASS_WITH_JSON)
endif()

if(NOT CMAKE_VERSION VERSION_LESS "3.9.0")
    # CMake's automoc needs help to find names of plugin metadata files in case Q_PLUGIN_METADATA
    # is indirectly used via other C++ preprocessor macros
    # 3.9+ lets us provide some filter rule pairs (keyword, regexp) to match the names of such files
    # in the plain text of the sources. See AUTOMOC_DEPEND_FILTERS docs for details.
    foreach(macro_name  K_PLUGIN_FACTORY_WITH_JSON;K_PLUGIN_CLASS_WITH_JSON)
        list(APPEND CMAKE_AUTOMOC_DEPEND_FILTERS
            "${macro_name}"
            "[\n^][ \t]*${macro_name}[ \t\n]*\\([^,]*,[ \t\n]*\"([^\"]+)\""
        )
    endforeach()
endif()
####################################################################################

if(CMAKE_CROSSCOMPILING AND KF5_HOST_TOOLING)
    find_file(KCOREADDONS_TARGETSFILE KF5CoreAddons/KF5CoreAddonsToolingTargets.cmake
        PATHS ${KF5_HOST_TOOLING} ${CMAKE_CURRENT_LIST_DIR}
        NO_DEFAULT_PATH
        NO_CMAKE_FIND_ROOT_PATH)
    include("${KCOREADDONS_TARGETSFILE}")
else()
    include("${CMAKE_CURRENT_LIST_DIR}/KF5CoreAddonsToolingTargets.cmake")
    if(CMAKE_CROSSCOMPILING AND DESKTOPTOJSON_EXECUTABLE)
        set_target_properties(KF5::desktoptojson PROPERTIES IMPORTED_LOCATION_NONE ${DESKTOPTOJSON_EXECUTABLE})
        set_target_properties(KF5::desktoptojson PROPERTIES IMPORTED_LOCATION ${DESKTOPTOJSON_EXECUTABLE})
    endif()
endif()
include("${CMAKE_CURRENT_LIST_DIR}/KF5CoreAddonsTargets.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/KF5CoreAddonsMacros.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/KF5CoreAddonsQchTargets.cmake")
