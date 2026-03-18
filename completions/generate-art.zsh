#compdef generate_art.py generate-art

# Zsh completion for generate_art.py
# Source this file: source completions/generate-art.zsh
# Or copy to a directory in your $fpath

_generate_art() {
    local -a styles models colors

    styles=(
        'acid:Classic ACiD Productions 1990s'
        'ice:iCE Advertisements - clean, professional'
        'blocky:Simple block characters, oldschool'
        'ascii:Pure ASCII art, no block chars'
        'amiga:Amiga demoscene, colorful'
        'dark:Gothic, moody'
        'neon:Cyberpunk neon glow'
        'minimal:Clean, thin, whitespace'
        'fire:Fire Graphics collective - detailed'
    )

    models=(
        'opus:Best quality, 1M context (slowest)'
        'sonnet:Good balance of speed and quality'
        'haiku:Fastest, lower quality'
    )

    colors=(
        'bright_cyan' 'bright_white' 'bright_red' 'bright_green'
        'bright_yellow' 'bright_blue' 'bright_magenta'
        'cyan' 'white' 'red' 'green' 'yellow' 'blue' 'magenta'
        'bright_black'
    )

    _arguments -s \
        '(-s --style)'{-s,--style}'[Style preset]:style:(( ${styles} ))' \
        '(-w --width)'{-w,--width}'[Output width in columns]:width:' \
        '(-n --examples)'{-n,--examples}'[Number of corpus examples]:count:' \
        '--save[Save output as .ans file]:output file:_files -g "*.ans"' \
        '--model[Claude model]:model:(( ${models} ))' \
        '--max-budget[Max cost in USD]:budget:' \
        '(-c --color)'{-c,--color}'[Monochrome color override]:color:( ${colors} )' \
        '*'{-i,--instruction}'[Extra instruction for the LLM]:instruction:' \
        '--cache[Corpus cache path]:cache path:_files -g "*.json"' \
        '--build-corpus[Build corpus from archive directory]:corpus path:_directories' \
        '--list-styles[List available styles]' \
        '(-v --verbose)'{-v,--verbose}'[Verbose logging]' \
        '(-h --help)'{-h,--help}'[Show help]' \
        '*:text to render:'
}

_generate_art "$@"
