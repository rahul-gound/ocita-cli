# OCITA.md - Project Instructions for ocita-cli

Welcome to `ocita-cli`! This repository contains **ocita**, a lightweight, intelligent alternative to Claude Code CLI built natively in and for the Bash environment.

## Architecture & Design Principles
- **Bash-Native**: Native integration with Unix pipelines, subshells, git commands, and terminal ANSI styling.
- **Zero External Python Dependencies**: Built using the Python standard library only (`urllib`, `json`, `subprocess`, `os`, `re`, `pathlib`). No heavy packages, no virtual environments needed.
- **Provider Agnostic**: Out-of-the-box support for OpenRouter, Anthropic, OpenAI, DeepSeek, Ollama (offline free local models), Google Gemini, and Groq.
- **Claude Code Tool Parity**: Full autonomous tool calling loop including `bash`, `view_file`, `edit_file` (exact string replacement), `write_file`, `list_dir`, `search_files` (glob), `search_text` (ripgrep/regex grep), `git_diff`, and `web_fetch`.
- **Safety First**: Interactive permission gate before running mutating or shell commands, with `-y` / `--dangerously-skip-permissions` flag for non-interactive automation.

## Project Structure
- `bin/ocita`: Main bash entry point, handles argument parsing, pipes, environment exports, and launches the engine.
- `lib/ocita_core.py`: Core agent engine, multi-provider API client, tool execution engine, session manager, and interactive REPL.
- `lib/prompt.sh`: Terminal UI styling, banners, badges, and colors.
- `lib/context.sh`: Project context extractor (`OCITA.md`, `CLAUDE.md`, git branch/diff/status, directory tree).
- `config/config.default.json`: Default provider models, endpoints, and configuration options.
- `tests/test_engine.py`: Unit test suite for tools and core logic.
- `install.sh`: One-line symlink installer to `~/.local/bin` or `/usr/local/bin`.

## Development & Testing Commands
- Run test suite: `python tests/test_engine.py`
- Test CLI help: `bash bin/ocita --help`
- Test CLI version: `bash bin/ocita --version`
- Run local unit tests in bash: `./bin/ocita -y "run python tests/test_engine.py and report results"`
