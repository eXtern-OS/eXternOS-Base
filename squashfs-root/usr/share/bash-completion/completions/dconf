
# Check for bash
[ -z "$BASH_VERSION" ] && return

####################################################################################################

__dconf() {
  local choices

  case "${COMP_CWORD}" in
    1)
      choices=$'help \nread \nlist \nwrite \nreset\n update \nlock \nunlock \nwatch \ndump \nload '
      ;;

    2)
      case "${COMP_WORDS[1]}" in
        help)
          choices=$'help \nread \nlist \nwrite \nreset\n update \nlock \nunlock \nwatch \ndump \nload '
          ;;
        list|dump|load)
          choices="$(dconf _complete / "${COMP_WORDS[2]}")"
          ;;
        read|list|write|lock|unlock|watch|reset)
          choices="$(dconf _complete '' "${COMP_WORDS[2]}")"
          ;;
      esac
      ;;

    3)
      case "${COMP_WORDS[1]} ${COMP_WORDS[2]}" in
	reset\ -f)
          choices="$(dconf _complete '' "${COMP_WORDS[3]}")"
          ;;
      esac
      ;;
  esac

  local IFS=$'\n'
  COMPREPLY=($(compgen -W "${choices}" "${COMP_WORDS[$COMP_CWORD]}"))
}

####################################################################################################

complete -o nospace -F __dconf dconf
