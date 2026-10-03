# Fiw's fish setup on Gentoo — the useful parts of cachyos-fish-config, minus pacman.
if status is-interactive
    function fish_greeting
        fastfetch
    end
end

set -x EDITOR nvim
set -x VISUAL nvim
set -x MANROFFOPT "-c"
set -x MANPAGER "sh -c 'col -bx | bat -l man -p'"
set -U __done_min_cmd_duration 10000
set -U __done_notification_urgency_level low
fish_add_path ~/.local/bin ~/.cargo/bin ~/.spicetify

# Listing
alias ls='eza -al --color=always --group-directories-first --icons=always'
alias la='eza -a --color=always --group-directories-first --icons=always'
alias ll='eza -l --color=always --group-directories-first --icons=always'
alias lt='eza -aT --color=always --group-directories-first --icons=always'
alias l.="eza -a | grep -e '^\.'"

# Misc
alias tarnow='tar -acf '
alias untar='tar -zxvf '
alias wget='wget -c '
alias psmem='ps auxf | sort -nr -k 4'
alias psmem10='ps auxf | sort -nr -k 4 | head -10'
alias grep='grep --color=auto'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# Gentoo
if type -q fiw-update
    alias update='sudo fiw-update'
end
alias big="qsize -a 2>/dev/null | sort -k2 -h | tail -30"

# !! and !$ like bash
function __history_previous_command
    switch (commandline -t)
        case "!"
            commandline -t $history[1]; commandline -f repaint
        case "*"
            commandline -i !
    end
end
function __history_previous_command_arguments
    switch (commandline -t)
        case "!"
            commandline -t ""
            commandline -f history-token-search-backward
        case "*"
            commandline -i '$'
    end
end
bind ! __history_previous_command
bind '$' __history_previous_command_arguments
