#!/usr/bin/env bash
# ==============================================================================
# ocita - One-Line Installer Script for Bash
# ==============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}Installing ocita (Claude Code CLI Bash Alternate)...${RESET}"

# Check for Bash
if [ -z "$BASH_VERSION" ]; then
  echo -e "${RED}[Error] This installer requires bash.${RESET}"
  exit 1
fi

# Determine source directory
SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OCITA_EXEC="$SCRIPT_DIR/bin/ocita"

if [ ! -f "$OCITA_EXEC" ]; then
  echo -e "${RED}[Error] Cannot find $OCITA_EXEC.${RESET}"
  echo "Please run install.sh from inside the cloned ocita repository."
  exit 1
fi

# Ensure executable permissions
chmod +x "$OCITA_EXEC"
chmod +x "$SCRIPT_DIR/lib/context.sh" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/lib/prompt.sh" 2>/dev/null || true

# Determine install target directory
TARGET_DIR=""
for candidate in "$HOME/.local/bin" "$HOME/bin" "/usr/local/bin"; do
  if [ -d "$candidate" ] && [ -w "$candidate" ]; then
    TARGET_DIR="$candidate"
    break
  fi
done

if [ -z "$TARGET_DIR" ]; then
  TARGET_DIR="$HOME/.local/bin"
  mkdir -p "$TARGET_DIR"
fi

SYMLINK_PATH="$TARGET_DIR/ocita"

echo "Creating symlink in $TARGET_DIR..."
ln -sf "$OCITA_EXEC" "$SYMLINK_PATH"

# Check if TARGET_DIR is in PATH
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
  echo -e "${YELLOW}Notice: $TARGET_DIR is not currently in your PATH.${RESET}"
  echo "Add the following line to your ~/.bashrc or ~/.zshrc:"
  echo -e "  ${BOLD}export PATH=\"\$PATH:$TARGET_DIR\"${RESET}"
fi

echo ""
echo -e "${GREEN}${BOLD}✔ Successfully installed ocita!${RESET}"
echo ""
echo "Quick Start:"
echo -e "  1. Set your API key: ${BOLD}export OPENROUTER_API_KEY=\"your_key\"${RESET} (or ANTHROPIC_API_KEY, etc.)"
echo -e "  2. Run: ${BOLD}ocita${RESET} (interactive REPL)"
echo -e "  3. Or run a single task: ${BOLD}ocita \"explain this codebase\"${RESET}"
echo ""
echo "Run 'ocita --help' for options."
