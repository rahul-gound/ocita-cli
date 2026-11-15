# ocita Architecture & Design

`ocita` is designed as a smart, fast, self-contained alternative to Claude Code CLI built specifically for the Bash terminal.

```
                  ┌────────────────────────────────────────┐
                  │              User / Shell              │
                  │   $ ocita "fix authentication bug"     │
                  │   $ cat log.txt | ocita "explain"      │
                  │   $ ocita  (Interactive REPL)          │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │              bin/ocita                 │
                  │  • Symlink resolution                  │
                  │  • CLI argument parsing                │
                  │  • Stdin pipe detection                │
                  │  • Environment & config propagation    │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │          lib/ocita_core.py             │
                  │  ┌──────────────────────────────────┐  │
                  │  │ Context Aggregator               │  │
                  │  │ • OCITA.md / CLAUDE.md detector  │  │
                  │  │ • Git branch / status / diff     │  │
                  │  │ • Directory tree mapper          │  │
                  │  └──────────────────┬───────────────┘  │
                  │                     ▼                  │
                  │  ┌──────────────────────────────────┐  │
                  │  │ Agent Loop & Multi-Turn REPL     │  │
                  │  │ • Max reasoning steps guard      │  │
                  │  │ • Slash command router           │  │
                  │  │ • Session state serializer       │  │
                  │  └──────────┬───────────────┬───────┘  │
                  │             │               │          │
                  │             ▼               ▼          │
                  │  ┌───────────────┐ ┌────────────────┐  │
                  │  │ Provider Hub  │ │ Tool Executor  │  │
                  │  │ • Anthropic   │ │ • bash         │  │
                  │  │ • OpenRouter  │ │ • view_file    │  │
                  │  │ • OpenAI      │ │ • edit_file    │  │
                  │  │ • DeepSeek    │ │ • write_file   │  │
                  │  │ • Ollama      │ │ • search_text  │  │
                  │  │ • Gemini      │ │ • search_files │  │
                  │  │ • Groq        │ │ • web_fetch    │  │
                  │  └───────────────┘ └────────────────┘  │
                  └────────────────────────────────────────┘
```

## 1. Zero External Dependencies
Unlike many coding agents that require dozens of heavy Node.js or Python packages, `ocita` requires only standard Bash and the standard Python 3 library (`urllib.request`, `json`, `subprocess`, `re`, `pathlib`). No `pip install`, no `npm install`, no virtual environment configuration needed.

## 2. Multi-Provider Protocol Adapter
`ocita` supports both native Anthropic Messages API format (`tools`, `tool_use`, `tool_result`) and OpenAI function calling format (`tools`, `function`, `tool_calls`). This enables seamless switching between Anthropic (Claude 3.7 Sonnet), OpenRouter, DeepSeek, Google Gemini, Groq, and local offline models via Ollama.

## 3. Interactive Permission Guard
Similar to Claude Code, `ocita` protects user files and systems:
- Mutating tools (`bash`, `write_file`, `edit_file`) require interactive approval by default (`[y]es / [n]o / [a]lways / [e]dit`).
- Power users and CI/CD pipelines can pass `-y`, `--yes`, or `--dangerously-skip-permissions` to enable full autonomous operation.

## 4. Exact Replacement File Editing
Rather than rewriting whole files (which consumes excessive tokens and risks losing code), `ocita` implements Claude Code's exact string replacement model:
- Verifies that `old_string` matches exact whitespace, indentation, and characters.
- Detects ambiguity if `old_string` occurs multiple times and requests more context.
- Preserves file line-ending format (`CRLF` on Windows, `LF` on Linux/macOS).

## 5. Session Management & Persistence
All turns, token usages, and tool executions are serialized to `~/.local/share/ocita/sessions/<session_id>.json`. This enables inspection, resuming sessions, and cost tracking.
