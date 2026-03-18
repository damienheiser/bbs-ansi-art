# Fish completion for generate_art.py
# Copy to ~/.config/fish/completions/generate_art.py.fish

complete -c generate_art.py -f
complete -c generate-art -f

complete -c generate_art.py -l style -s s -x -d "Style preset" \
    -a "acid\t'ACiD Productions 1990s'
        ice\t'iCE Advertisements'
        blocky\t'Block characters, oldschool'
        ascii\t'Pure ASCII, no block chars'
        amiga\t'Amiga demoscene, colorful'
        dark\t'Gothic, moody'
        neon\t'Cyberpunk neon glow'
        minimal\t'Clean, thin, whitespace'
        fire\t'Fire Graphics - detailed'"

complete -c generate_art.py -l model -x -d "Model name" \
    -a "opus\t'Claude Opus (best, 1M ctx)'
        sonnet\t'Claude Sonnet (fast)'
        haiku\t'Claude Haiku (fastest)'
        o4-mini\t'OpenAI o4-mini'
        gpt-4o\t'OpenAI GPT-4o'
        gemini-2.5-pro\t'Google Gemini 2.5 Pro'
        llama3.3\t'Meta Llama 3.3'"

complete -c generate_art.py -l provider -x -d "LLM provider" \
    -a "claude\t'Claude CLI (default)'
        codex\t'OpenAI Codex CLI'
        gemini\t'Google Gemini CLI'
        opencode\t'Opencode CLI'
        llama\t'Meta Llama CLI'
        anthropic\t'Anthropic API'
        openai\t'OpenAI API'
        google\t'Google GenAI API'"

complete -c generate_art.py -l color -s c -x -d "Monochrome color" \
    -a "bright_cyan bright_white bright_red bright_green bright_yellow
        bright_blue bright_magenta cyan white red green yellow blue
        magenta bright_black"

complete -c generate_art.py -l width -s w -x -d "Output width in columns"
complete -c generate_art.py -l examples -s n -x -d "Number of corpus examples"
complete -c generate_art.py -l save -r -d "Save as .ans file" -F
complete -c generate_art.py -l max-budget -x -d "Max cost in USD"
complete -c generate_art.py -l instruction -s i -x -d "Extra LLM instruction (repeatable)"
complete -c generate_art.py -l corpus-group -x -d "Use examples from this art group"
complete -c generate_art.py -l cache -r -d "Corpus cache path" -F
complete -c generate_art.py -l build-corpus -r -d "Build corpus from archive dir" -a "(__fish_complete_directories)"
complete -c generate_art.py -l list-styles -d "List style presets"
complete -c generate_art.py -l list-corpus -d "List corpus groups and artists"
complete -c generate_art.py -l list-providers -d "List LLM providers"
complete -c generate_art.py -l verbose -s v -d "Verbose logging"
complete -c generate_art.py -l help -s h -d "Show help"

complete -c generate-art -w generate_art.py
