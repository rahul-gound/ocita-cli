#!/usr/bin/env bash
# ==============================================================================
# ocita - Terminal UI Formatting and Banner
# ==============================================================================

# ANSI Color & Style Constants
if [ -t 1 ]; then
  RESET="\033[0m"
  BOLD="\033[1m"
  DIM="\033[2m"
  ITALIC="\033[3m"
  UNDERLINE="\033[4m"
  
  # Foreground Colors
  BLACK="\033[30m"
  RED="\033[31m"
  GREEN="\033[32m"
  YELLOW="\033[33m"
  BLUE="\033[34m"
  MAGENTA="\033[35m"
  CYAN="\033[36m"
  WHITE="\033[37m"
  
  # Bright Colors
  BRIGHT_BLACK="\033[90m"
  BRIGHT_RED="\033[91m"
  BRIGHT_GREEN="\033[92m"
  BRIGHT_YELLOW="\033[93m"
  BRIGHT_BLUE="\033[94m"
  BRIGHT_MAGENTA="\033[95m"
  BRIGHT_CYAN="\033[96m"
  BRIGHT_WHITE="\033[97m"
else
  RESET=""
  BOLD=""
  DIM=""
  ITALIC=""
  UNDERLINE=""
  BLACK=""
  RED=""
  GREEN=""
  YELLOW=""
  BLUE=""
  MAGENTA=""
  CYAN=""
  WHITE=""
  BRIGHT_BLACK=""
  BRIGHT_RED=""
  BRIGHT_GREEN=""
  BRIGHT_YELLOW=""
  BRIGHT_BLUE=""
  BRIGHT_MAGENTA=""
  BRIGHT_CYAN=""
  BRIGHT_WHITE=""
fi

# Print beautiful ASCII art logo
print_banner() {
  cat << "EOF"
  ___   ____ _ _____ _   
 / _ \ / ___(_)__   / \  
| | | | |   | | / // _ \ 
| |_| | |___| |/ // ___ \
 \___/ \____|_/_//_/   \_\
EOF
  echo -e "${DIM}  Claude Code CLI Alternative for Bash | v1.0.0${RESET}"
  echo ""
}

# Print status messages
info() {
  echo -e "${BRIGHT_BLUE}ℹ${RESET} $*"
}

success() {
  echo -e "${BRIGHT_GREEN}✔${RESET} $*"
}

warn() {
  echo -e "${BRIGHT_YELLOW}⚠${RESET} $*"
}

error() {
  echo -e "${BRIGHT_RED}✖${RESET} $*" >&2
}

tool_badge() {
  local tool_name="$1"
  local desc="$2"
  echo -e "${BOLD}${CYAN}⚡ [${tool_name}]${RESET} ${desc}"
}
