
# Copyright (c) 2006, Alexander Neundorf, <neundorf@kde.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the University nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

find_package(Gettext REQUIRED)

# The Python executable used for building ki18n will be used as a fallback
# solution if it cannot be found in $PATH when building applications.
set(_KI18N_PYTHON_EXECUTABLE "/usr/bin/python")

find_program(KI18N_PYTHON_EXECUTABLE NAMES python3 python2 python)
if(NOT KI18N_PYTHON_EXECUTABLE)
    set(KI18N_PYTHON_EXECUTABLE "${_KI18N_PYTHON_EXECUTABLE}")
endif()

set(_ki18n_pmap_compile_script ${CMAKE_CURRENT_LIST_DIR}/ts-pmap-compile.py)
set(_ki18n_uic_script ${CMAKE_CURRENT_LIST_DIR}/kf5i18nuic.cmake)
set(_ki18n_build_pofiles_script ${CMAKE_CURRENT_LIST_DIR}/build-pofiles.cmake)
set(_ki18n_build_tsfiles_script ${CMAKE_CURRENT_LIST_DIR}/build-tsfiles.cmake)

#create the implementation files from the ui files and add them to the list of sources
#usage: KI18N_WRAP_UI(foo_SRCS ${ui_files}) or KI18N_WRAP_UI(TARGET ${ui_files})
macro (KI18N_WRAP_UI _sources )
   if(NOT TARGET Qt5::uic)
      message(FATAL_ERROR "Qt5Widgets should be found before calling ki18n_wrap_ui(). Please add find_package(Qt5Widgets ...)")
   endif()

   foreach (_current_FILE ${ARGN})

      get_filename_component(_tmp_FILE ${_current_FILE} ABSOLUTE)
      get_filename_component(_basename ${_tmp_FILE} NAME_WE)
      set(_header ${CMAKE_CURRENT_BINARY_DIR}/ui_${_basename}.h)

      get_target_property(QT_UIC_EXECUTABLE Qt5::uic LOCATION)
      # we need to run uic and replace some things in the generated file
      # this is done by executing the cmake script kf5i18nuic.cmake
      add_custom_command(OUTPUT ${_header}
         COMMAND ${CMAKE_COMMAND}
         ARGS
         -DKDE_UIC_EXECUTABLE:FILEPATH=${QT_UIC_EXECUTABLE}
         -DKDE_UIC_FILE:FILEPATH=${_tmp_FILE}
         -DKDE_UIC_H_FILE:FILEPATH=${_header}
         -DKDE_UIC_BASENAME:STRING=${_basename}
         -P ${_ki18n_uic_script}
         MAIN_DEPENDENCY ${_tmp_FILE}
      )
      set_source_files_properties(${_header} PROPERTIES SKIP_AUTOMOC ON)
      if(TARGET ${_sources})
         target_sources(${_sources} PRIVATE ${_header})
      else()
         list(APPEND ${_sources} ${_header})
      endif()
   endforeach (_current_FILE)
endmacro (KI18N_WRAP_UI)

# KI18N_INSTALL(podir)
# Search for .po files and scripting modules and install them to the standard
# location.
#
# This is a convenience function which relies on the following directory
# structure:
#
#  <podir>/
#    <lang>/
#      scripts/
#        <domain>/
#          *.js
#      *.po
#
# .po files are passed to build-pofiles.cmake
#
# .js files are installed using build-tsfiles.cmake
#
# For example, given the following directory structure:
#
#  po/
#    fr/
#      scripts/
#        kfoo/
#          kfoo.js
#      kfoo.po
#
# KI18N_INSTALL(po) does the following:
# - Compiles kfoo.po into kfoo.mo and installs it in
#   ${LOCALE_INSTALL_DIR}/fr/LC_MESSAGES or share/locale/fr/LC_MESSAGES if
#   ${LOCALE_INSTALL_DIR} is not set.
# - Installs kfoo.js in ${LOCALE_INSTALL_DIR}/fr/LC_SCRIPTS/kfoo
#
# KI18N_INSTALL_TS_FILES() is deprecated, use KI18N_INSTALL()
#
function(KI18N_INSTALL podir)
    if (NOT LOCALE_INSTALL_DIR)
        set(LOCALE_INSTALL_DIR share/locale)
    endif()

    # First try to find the po directory in the source directory, where the release scripts copy them before making the tarballs
    get_filename_component(absolute_podir ${podir} ABSOLUTE)

    # we try to find the po directory in the binary directory, in case it was downloaded
    # using ECM
    if (NOT (EXISTS "${absolute_podir}" AND IS_DIRECTORY "${absolute_podir}"))
	    get_filename_component(absolute_podir ${CMAKE_CURRENT_BINARY_DIR}/${podir} ABSOLUTE)
    endif()

    if (NOT (EXISTS "${absolute_podir}" AND IS_DIRECTORY "${absolute_podir}"))
        # Nothing to do if there's no podir and it would create an empty
        # LOCALE_INSTALL_DIR in that case.
        return()
    endif()

    get_filename_component(dirname ${LOCALE_INSTALL_DIR} NAME)
    get_filename_component(destname ${LOCALE_INSTALL_DIR} DIRECTORY)
    string(MD5 pathmd5 ${absolute_podir})

    add_custom_target(pofiles-${pathmd5} ALL
        COMMENT "Generating mo..."
        COMMAND ${CMAKE_COMMAND}
                -DGETTEXT_MSGFMT_EXECUTABLE=${GETTEXT_MSGFMT_EXECUTABLE}
                -DCOPY_TO=${CMAKE_CURRENT_BINARY_DIR}/${dirname}
                -DPO_DIR=${absolute_podir}
                -P ${_ki18n_build_pofiles_script}
    )
    add_custom_target(tsfiles-${pathmd5} ALL
        COMMENT "Generating ts..."
        COMMAND ${CMAKE_COMMAND}
                -DPYTHON_EXECUTABLE=${KI18N_PYTHON_EXECUTABLE}
                -D_ki18n_pmap_compile_script=${_ki18n_pmap_compile_script}
                -DCOPY_TO=${CMAKE_CURRENT_BINARY_DIR}/${dirname}
                -DPO_DIR=${absolute_podir}
                -P ${_ki18n_build_tsfiles_script}
    )

    if (NOT TARGET pofiles)
        add_custom_target(pofiles)
    endif()
    if (NOT TARGET tsfiles)
        add_custom_target(tsfiles)
    endif()
    add_dependencies(pofiles pofiles-${pathmd5})
    add_dependencies(tsfiles tsfiles-${pathmd5})

    file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${dirname})
    install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/${dirname} DESTINATION ${destname})
endfunction()

#install the scripts for a given language in the target folder
#usage: KI18N_INSTALL_TS_FILES("ja" ${scripts_dir})
function(KI18N_INSTALL_TS_FILES lang scripts_dir)
   file(GLOB_RECURSE ts_files RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} ${scripts_dir}/*)
   set(pmapc_files)
   foreach(ts_file ${ts_files})
      string(REGEX MATCH "\\.svn/" in_svn ${ts_file})
      if(NOT in_svn)
         # If ts_file is "path/to/foo/bar.js"
         # We want subpath to contain "foo"
         get_filename_component(subpath ${ts_file} DIRECTORY)
         get_filename_component(subpath ${subpath} NAME)
         install(FILES ${ts_file}
                 DESTINATION ${LOCALE_INSTALL_DIR}/${lang}/LC_SCRIPTS/${subpath})
         # If current file is a pmap, also install the compiled version.
         get_filename_component(ts_ext ${ts_file} EXT)
         if(ts_ext STREQUAL ".pmap")
            set(pmap_file ${ts_file})
            get_filename_component(pmap_basename ${ts_file} NAME)
            set(pmapc_basename "${pmap_basename}c")
            set(pmapc_file "${lang}-${subpath}-${pmapc_basename}")
            add_custom_command(OUTPUT ${pmapc_file}
               COMMAND ${KI18N_PYTHON_EXECUTABLE}
               ARGS
               -B
               ${_ki18n_pmap_compile_script}
               ${CMAKE_CURRENT_SOURCE_DIR}/${pmap_file}
               ${pmapc_file}
               DEPENDS ${pmap_file})
            install(FILES ${CMAKE_CURRENT_BINARY_DIR}/${pmapc_file}
                    DESTINATION ${LOCALE_INSTALL_DIR}/${lang}/LC_SCRIPTS/${subpath}
                    RENAME ${pmapc_basename})
            list(APPEND pmapc_files ${pmapc_file})
         endif()
      endif()
   endforeach()
   if(pmapc_files)
      if(NOT TARGET pmapfiles)
         add_custom_target(pmapfiles)
      endif()
      set(pmapc_target "pmapfiles-${lang}")
      string(REPLACE "@" "_" pmapc_target ${pmapc_target})
      add_custom_target(${pmapc_target} ALL DEPENDS ${pmapc_files})
      add_dependencies(pmapfiles ${pmapc_target})
   endif()
endfunction()
