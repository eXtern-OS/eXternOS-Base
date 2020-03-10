# Copyright (c) 2017 Aleix Pol Gonzalez <aleixpol@kde.org>
# Copyright (c) 2017 Harald Sitter <sitter@kde.org>
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

file(GLOB_RECURSE pofiles RELATIVE "${PO_DIR}" "${PO_DIR}/**.po")

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
        message(FATAL_ERROR "failed generating ${PO_DIR}")
    endif()
endfunction()

foreach(pofile IN LISTS pofiles)
    get_filename_component(name ${pofile} NAME)
    # Regex the basename, cmake only allows stripping the longest extension, we
    # need the shortest or we'll screw up "org.kde.plasma.kittens.po"
    # https://bugs.kde.org/show_bug.cgi?id=379116
    string(REGEX REPLACE "^(.+)(\\.[^.]+)$" "\\1" name ${name})
    get_filename_component(langdir ${pofile} DIRECTORY)
    set(dest ${COPY_TO}/${langdir}/LC_MESSAGES)
    file(MAKE_DIRECTORY ${dest})

    list(APPEND commands COMMAND ${GETTEXT_MSGFMT_EXECUTABLE} -o ${dest}/${name}.mo ${PO_DIR}/${pofile})
    math(EXPR i "${i}+1")
    if(i EQUAL ${numberOfProcesses})
        _processCommands()
        set(i 0)
        set(commands)
    endif()
endforeach()

_processCommands()
