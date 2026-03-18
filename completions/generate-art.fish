# Fish completion for generate_art.py
# Copy to ~/.config/fish/completions/generate_art.py.fish
# Or source directly: source completions/generate-art.fish

# Disable file completions by default
complete -c generate_art.py -f
complete -c generate-art -f

# Styles
set -l styles acid ice blocky ascii amiga dark neon minimal fire

# Models
set -l models opus sonnet haiku

# Style descriptions for rich completions
complete -c generate_art.py -l style -s s -x -d "Style preset" \
    -a "acid\t'ACiD Productions 1990s'
        ice\t'iCE Advertisements - clean'
        blocky\t'Block characters, oldschool'
        ascii\t'Pure ASCII, no block chars'
        amiga\t'Amiga demoscene, colorful'
        dark\t'Gothic, moody'
        neon\t'Cyberpunk neon glow'
        minimal\t'Clean, thin, whitespace'
        fire\t'Fire Graphics - detailed'"

complete -c generate_art.py -l model -x -d "Claude model" \
    -a "opus\t'Best quality, 1M context'
        sonnet\t'Good speed/quality balance'
        haiku\t'Fastest, lower quality'"

complete -c generate_art.py -l width -s w -x -d "Output width in columns"
complete -c generate_art.py -l examples -s n -x -d "Number of corpus examples"
complete -c generate_art.py -l save -r -d "Save as .ans file" -F
complete -c generate_art.py -l max-budget -x -d "Max cost in USD"
complete -c generate_art.py -l color -s c -x -d "Monochrome color override" \
    -a "bright_cyan\t'Bright Cyan'
        bright_white\t'Bright White'
        bright_red\t'Bright Red'
        bright_green\t'Bright Green'
        bright_yellow\t'Bright Yellow'
        bright_blue\t'Bright Blue'
        bright_magenta\t'Bright Magenta'
        cyan\t'Cyan'
        white\t'White'
        red\t'Red'
        green\t'Green'
        yellow\t'Yellow'
        blue\t'Blue'
        magenta\t'Magenta'
        bright_black\t'Dark Gray'"
complete -c generate_art.py -l instruction -s i -x -d "Extra instruction for the LLM (repeatable)"
complete -c generate_art.py -l cache -r -d "Corpus cache path" -F
complete -c generate_art.py -l build-corpus -r -d "Build corpus from archive dir" -a "(__fish_complete_directories)"
complete -c generate_art.py -l list-styles -d "List available styles"
complete -c generate_art.py -l verbose -s v -d "Verbose logging"
complete -c generate_art.py -l help -s h -d "Show help"

# Duplicate for alias name
complete -c generate-art -w generate_art.py
