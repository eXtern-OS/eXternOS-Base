set(_KINITDIR ${CMAKE_CURRENT_LIST_DIR})

macro(_FIND_KDEINIT_FILE OUTPUT_VAR INFIX)
    set(_KDE5INIT_DUMMY_FILENAME kde5init${INFIX}_dummy.cpp.in)
    if(KInit_SOURCE_DIR)
        set(${OUTPUT_VAR} "${KInit_SOURCE_DIR}/${_KDE5INIT_DUMMY_FILENAME}")
    else()
        find_file(${OUTPUT_VAR} NAMES ${_KDE5INIT_DUMMY_FILENAME} HINTS ${_KINITDIR})
    endif()
endmacro()

function (KF5_ADD_KDEINIT_EXECUTABLE _target_NAME )
    cmake_parse_arguments(KF5_KDEINIT "NOGUI" "" "" ${ARGN} )
    set(_SRCS ${KF5_KDEINIT_UNPARSED_ARGUMENTS})

    _FIND_KDEINIT_FILE(_KDE5INIT_DUMMY_FILEPATH "")
    configure_file(${_KDE5INIT_DUMMY_FILEPATH} ${CMAKE_CURRENT_BINARY_DIR}/${_target_NAME}_dummy.cpp)

    if(WIN32)
        if (MINGW)
            list(FIND _SRCS ${CMAKE_CURRENT_BINARY_DIR}/${_target_NAME}_res.o _res_position)
        else(MINGW)
            list(FIND _SRCS ${CMAKE_CURRENT_BINARY_DIR}/${_target_NAME}.rc _res_position)
        endif(MINGW)
        if(NOT _res_position EQUAL -1)
            list(GET _SRCS ${_res_position} _resourcefile)
            list(REMOVE_AT _SRCS ${_res_position})
        endif(NOT _res_position EQUAL -1)

        # We don't need a shared library on Windows, use a static library that gets included in the executable.
        # Since Windows doesn't use fork()+exec() there is no use for this library by kdeinit.
        # Having the static library ensures that target_link_libraries(myexe kdeinit_foo) also works on Windows and not just on UNIX
        add_library(kdeinit_${_target_NAME} STATIC ${_SRCS})
    else()
        # Use a shared library on UNIX so that kdeinit can dlopen() it
        add_library(kdeinit_${_target_NAME} SHARED ${_SRCS})
    endif()
    if (APPLE)
        set(_resourcefile ${MACOSX_BUNDLE_ICON_FILE})
    endif()
    add_executable(${_target_NAME} ${CMAKE_CURRENT_BINARY_DIR}/${_target_NAME}_dummy.cpp ${_resourcefile})
    target_link_libraries(${_target_NAME} kdeinit_${_target_NAME})
    set_target_properties(kdeinit_${_target_NAME} PROPERTIES OUTPUT_NAME kdeinit5_${_target_NAME})

    if(KF5_KDEINIT_NOGUI)
        ecm_mark_nongui_executable(${_target_NAME})
    endif()
endfunction ()
