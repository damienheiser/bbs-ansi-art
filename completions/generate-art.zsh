#compdef generate_art.py generate-art

# Zsh completion for generate_art.py

_generate_art() {
    local -a styles models colors providers

    styles=(
        'acid:Classic ACiD Productions 1990s'
        'ice:iCE Advertisements - clean'
        'blocky:Block characters, oldschool'
        'ascii:Pure ASCII, no block chars'
        'amiga:Amiga demoscene, colorful'
        'dark:Gothic, moody'
        'neon:Cyberpunk neon glow'
        'minimal:Clean, thin, whitespace'
        'fire:Fire Graphics - detailed'
    )

    models=(
        'opus:Claude Opus (best, 1M ctx)'
        'sonnet:Claude Sonnet (fast)'
        'haiku:Claude Haiku (fastest)'
        'o4-mini:OpenAI o4-mini'
        'gpt-4o:OpenAI GPT-4o'
        'gemini-2.5-pro:Google Gemini 2.5 Pro'
        'llama3.3:Meta Llama 3.3'
    )

    colors=(
        'bright_cyan' 'bright_white' 'bright_red' 'bright_green'
        'bright_yellow' 'bright_blue' 'bright_magenta'
        'cyan' 'white' 'red' 'green' 'yellow' 'blue' 'magenta'
        'bright_black'
    )

    providers=(
        'claude:Claude CLI (default)'
        'codex:OpenAI Codex CLI'
        'gemini:Google Gemini CLI'
        'opencode:Opencode CLI'
        'llama:Meta Llama CLI'
        'anthropic:Anthropic API'
        'openai:OpenAI API'
        'google:Google GenAI API'
    )

    _arguments -s \
        '(-s --style)'{-s,--style}'[Style preset]:style:(( ${styles} ))' \
        '(-w --width)'{-w,--width}'[Output width in columns]:width:' \
        '(-n --examples)'{-n,--examples}'[Number of corpus examples]:count:' \
        '--save[Save as .ans file]:output file:_files -g "*.ans"' \
        '--provider[LLM provider]:provider:(( ${providers} ))' \
        '--model[Model name]:model:(( ${models} ))' \
        '--max-budget[Max cost in USD]:budget:' \
        '(-c --color)'{-c,--color}'[Monochrome color]:color:( ${colors} )' \
        '*'{-i,--instruction}'[Extra LLM instruction]:instruction:' \
        '--corpus-group[Use examples from this group]:group:' \
        '--cache[Corpus cache path]:cache:_files -g "*.json"' \
        '--build-corpus[Build corpus from archive dir]:path:_directories' \
        '--list-styles[List style presets]' \
        '--list-corpus[List corpus groups and artists]' \
        '--list-providers[List LLM providers]' \
        '(-v --verbose)'{-v,--verbose}'[Verbose logging]' \
        '(-h --help)'{-h,--help}'[Show help]' \
        '*:text to render:'
}

_generate_art "$@"
