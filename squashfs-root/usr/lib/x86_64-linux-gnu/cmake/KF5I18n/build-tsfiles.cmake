# Copyright (c) 2017 Aleix Pol Gonzalez <aleixpol@kde.org>
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

file(GLOB_RECURSE ts_files RELATIVE ${PO_DIR} ${PO_DIR}/**/scripts/*)
foreach(ts_file ${ts_files})
    if(ts_file MATCHES "\\.svn")
        continue()
    endif()

    get_filename_component(subpath ${ts_file} DIRECTORY)
    string(REPLACE "scripts" "LC_SCRIPTS" subpath ${subpath})

    message(STATUS "copying... ${PO_DIR}/${ts_file} DESTINATION ${COPY_TO}/${subpath}" )
    file(COPY ${PO_DIR}/${ts_file} DESTINATION ${COPY_TO}/${subpath})
endforeach()


include(ProcessorCount)
ProcessorCount(numberOfProcesses)

set(i 0)
set(commands)

function(_processCommands)
    if(NOT commands)
        return()
    endif()

    execute_process(
        ${commands}
        RESULT_VARIABLE code
    )
    if(code)
        message(FATAL_ERROR "failed generating: ${PO_DIR}")
    endif()
endfunction()

file(GLOB_RECURSE pmap_files RELATIVE ${PO_DIR} "${PO_DIR}/**.pmap")
foreach(pmap_file ${pmap_files})
    get_filename_component(pmap_basename ${pmap_file} NAME)
    get_filename_component(subpath ${pmap_file} DIRECTORY)
    string(REPLACE "scripts" "LC_SCRIPTS" subpath ${subpath})
    set(pmapc_file "${COPY_TO}/${subpath}/${pmap_basename}c")

    message(STATUS "building... ${pmap_file} to ${pmapc_file}" )
    list(APPEND commands
        COMMAND ${PYTHON_EXECUTABLE}
            -B
            ${_ki18n_pmap_compile_script}
            ${PO_DIR}/${pmap_file}
            ${pmapc_file}
    )
    math(EXPR i "${i}+1")
    if (i EQUAL ${numberOfProcesses})
        _processCommands()
        set(i 0)
    endif()
endforeach()

_processCommands()
