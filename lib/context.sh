#!/usr/bin/env bash
# ==============================================================================
# ocita - Project Context Extractor & Template Initializer
# ==============================================================================

set -o pipefail

# Find project instructions file (OCITA.md, CLAUDE.md, AGENT.md)
find_instructions_file() {
  local cur_dir="$PWD"
  while [ "$cur_dir" != "/" ] && [ "$cur_dir" != "." ] && [ -n "$cur_dir" ]; do
    for fname in "OCITA.md" "CLAUDE.md" "AGENT.md" ".ocita/instructions.md"; do
      if [ -f "$cur_dir/$fname" ]; then
        echo "$cur_dir/$fname"
        return 0
      fi
    done
    local parent_dir
    parent_dir="$(dirname "$cur_dir")"
    if [ "$parent_dir" = "$cur_dir" ]; then
      break
    fi
    cur_dir="$parent_dir"
  done
  return 1
}

# Generate project structure summary
get_dir_tree() {
  if command -v rg >/dev/null 2>&1; then
    rg --files --hidden -g '!.git' -g '!node_modules' -g '!.venv' -g '!__pycache__' -g '!dist' -g '!build' | head -n 40
  elif command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files | head -n 40
  else
    find . -maxdepth 2 -not -path '*/.*' -not -path './node_modules*' | head -n 40
  fi
}

# Get git status and branch
get_git_info() {
  if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    local branch
    branch="$(git branch --show-current 2>/dev/null || echo "detached")"
    local status
    status="$(git status --short 2>/dev/null | head -n 15)"
    local recent_commits
    recent_commits="$(git log -n 5 --oneline 2>/dev/null)"
    
    echo "Git Branch: $branch"
    if [ -n "$status" ]; then
      echo "Modified/Untracked Files:"
      echo "$status"
    else
      echo "Working tree clean."
    fi
    if [ -n "$recent_commits" ]; then
      echo "Recent Commits:"
      echo "$recent_commits"
    fi
  else
    echo "Not a git repository."
  fi
}

# Init command: create OCITA.md in current directory
init_project() {
  local target_file="$PWD/OCITA.md"
  if [ -f "$target_file" ]; then
    echo -e "\033[33m⚠ OCITA.md already exists at $target_file\033[0m"
    return 0
  fi

  cat << 'EOF' > "$target_file"
# Project Guidelines (OCITA.md)

Welcome to this repository! This file gives instructions and conventions for **ocita** (and other AI agents) working in this codebase.

## Overview
- Project Name: [Enter project name]
- Description: [Brief description of what this project does]
- Tech Stack: [e.g. TypeScript, Node.js, Python, Rust, Bash, React]

## Development Commands
- Install dependencies: `npm install` (or `pip install -r requirements.txt`)
- Run tests: `npm test` (or `pytest`)
- Run linter/typecheck: `npm run lint` / `tsc --noEmit`
- Start dev server: `npm run dev`

## Code Style & Conventions
- Indentation: 2 spaces
- Follow modern idioms and maintain clean error handling.
- Always run tests and verify changes before completing tasks.

## Agent Guidelines
- Do not modify production configurations without explicit confirmation.
- Keep changes concise, well-documented, and targeted.
EOF

  echo -e "\033[32m✔ Created OCITA.md template in $target_file\033[0m"
  echo "You can now customize it with your project's specific conventions and commands."
}

# Handle direct CLI invocation
if [ "$1" = "init" ]; then
  init_project
  exit 0
fi
