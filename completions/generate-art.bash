# Bash completion for generate_art.py
# Source this file: source completions/generate-art.bash
# Or copy to /etc/bash_completion.d/

_generate_art() {
    local cur prev opts styles models
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    styles="acid ice blocky ascii amiga dark neon minimal fire"
    models="opus sonnet haiku"
    colors="bright_cyan bright_white bright_red bright_green bright_yellow bright_blue bright_magenta cyan white red green yellow blue magenta bright_black"
    opts="--style -s --width -w --examples -n --save --model --max-budget --color -c --instruction -i --cache --build-corpus --list-styles --verbose -v --help -h"

    case "${prev}" in
        --style|-s)
            COMPREPLY=( $(compgen -W "${styles}" -- "${cur}") )
            return 0
            ;;
        --model)
            COMPREPLY=( $(compgen -W "${models}" -- "${cur}") )
            return 0
            ;;
        --color|-c)
            COMPREPLY=( $(compgen -W "${colors}" -- "${cur}") )
            return 0
            ;;
        --save)
            COMPREPLY=( $(compgen -f -X '!*.ans' -- "${cur}") )
            return 0
            ;;
        --build-corpus|--cache)
            COMPREPLY=( $(compgen -d -- "${cur}") )
            return 0
            ;;
        --width|-w|--examples|-n|--max-budget|--instruction|-i)
            return 0
            ;;
    esac

    if [[ "${cur}" == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
        return 0
    fi
}

complete -F _generate_art generate_art.py
complete -F _generate_art generate-art
