<p align="center">
  <h1 align="center">⚡ ocita</h1>
  <p align="center"><strong>The Smart, Autonomous Enterprise Claude Code CLI Alternate in Bash & PowerShell</strong></p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#gemini--chatgpt">Gemini & ChatGPT</a> •
    <a href="#claudeai-login--auth">Claude.ai Login</a> •
    <a href="#deliberate-pacing--comments">Slow Pacing & Comments</a> •
    <a href="#hackatime--wakatime-time-tracking">Hackatime</a> •
    <a href="#repl-commands">Commands</a>
  </p>
</p>

---

## 💡 What is ocita?

**ocita** is an open-source, lightweight, autonomous AI coding agent designed specifically for terminal and Bash power users. It provides full functional parity with Anthropic's **Claude Code CLI**, while being completely provider-agnostic, zero-dependency, and deeply integrated with Unix pipes and shell workflows.

Whether you're developing on **Linux**, **macOS**, **WSL**, or **Git Bash on Windows**, `ocita` turns your terminal into a collaborative software engineering workstation.

```text
  ___   ____ _ _____ _   
 / _ \ / ___(_)__   / \  
| | | | |   | | / // _ \ 
| |_| | |___| |/ // ___ \
 \___/ \____|_/_//_/   \_\
  Smart Claude Code CLI Alternative in Bash | v1.0.0
```

---

## ✨ Features

- 🔄 **Full Agentic Loop (ReAct)**: Autonomously reasons, plans, inspects files, runs tests, applies edits, and verifies fixes.
- 🧠 **Native Gemini & ChatGPT Integration**:
  - **Google Gemini**: First-class support for `gemini-2.0-flash`, `gemini-1.5-pro`, and `gemini-2.5-pro` via `GEMINI_API_KEY` or `/gemini`.
  - **OpenAI ChatGPT**: First-class support for `chatgpt-4o-latest`, `gpt-4o`, `o3-mini`, and `o1` via `OPENAI_API_KEY` or `/chatgpt`.
- ⏳ **Deliberate Slow Pacing Mode (`--slow`, `/slow`)**:
  - Works deliberately and methodically so you can follow each tool execution step in real time.
  - Generates clear, thorough, professional code comments (module headers, docstrings, inline algorithmic notes, edit rationales). Never outputs bare, cryptic code.
- ⏱️ **Automatic Hackatime / WakaTime Tracking**:
  - Automatically sends coding heartbeats on every file read, edit, write, and command execution.
  - Automatically loads configuration from `~/.wakatime.cfg` (`https://hackatime.hackclub.com/api/hackatime/v1`).
  - View real-time logged stats with `/time` or `/hackatime`.
- 🔐 **Dual Authentication (API & Claude.ai Web Login)**:
  - **Claude.ai Web Login**: Log in with your Claude.ai session key (`sessionKey=sk-ant-sid...` from browser cookies) using `/login claude`.
  - **Direct API Keys**: Anthropic (`ANTHROPIC_API_KEY`), OpenRouter, OpenAI, DeepSeek, Gemini, Groq.
  - **Offline / Local**: Ollama with zero authentication needed.
  - View status anytime with `/auth`, manage with `/login` and `/logout`.
- 🏢 **Elite Enterprise System Prompt**:
  - Operates at the level of a Principal Systems Architect.
  - Enforces Clean Architecture, SOLID, defensive boundaries, and OWASP Top 10 security standards.
  - Test-driven verification: automatically verifies changes with test runners (`npm test`, `pytest`, `cargo test`, `go test`) before marking tasks complete.
- 🛠️ **Expanded Enterprise Toolset**:
  - `bash`: Run terminal commands, test suites, linters, and package managers.
  - `view_file`: Read entire files or specific line windows with line numbering.
  - `edit_file`: Exact string replacement (Claude Code style) with unique match verification.
  - `write_file`: Create or overwrite files atomically.
  - `git_commit`: Autonomous conventional git commit generator.
  - `run_tests`: Auto-detects and runs project test suites with failure analysis.
  - `code_outline`: Extracts classes, functions, and interfaces from code files.
  - `wakatime_heartbeat`: Explicitly logs coding time to Hackatime.
  - `list_dir`, `search_files` (glob), `search_text` (ripgrep/regex), `git_diff`, `web_fetch`.
- 💬 **Rich REPL Commands**: `/time`, `/login`, `/auth`, `/logout`, `/review`, `/commit`, `/test`, `/lint`, `/doctor`, `/branch`, `/export`, `/model`, `/provider`, `/diff`, `/undo`.

---

## ⚖️ Claude Code vs. ocita

| Feature | Claude Code CLI | **ocita** |
| :--- | :---: | :---: |
| **Terminal / Bash Native** | ⚠️ Heavy Node.js binary | ✅ Pure Bash & Python Stdlib |
| **Provider Support** | ❌ Anthropic only | ✅ Anthropic, OpenRouter, OpenAI, DeepSeek, Ollama, Gemini, Groq |
| **Offline / Local Models** | ❌ Not supported | ✅ Supported via Ollama (`qwen2.5-coder`, `llama3.1`, etc.) |
| **Exact String File Editing** | ✅ Supported | ✅ Supported |
| **Interactive Approval Guard** | ✅ Supported | ✅ Supported |
| **Dangerous Skip Flag (`-y`)** | ✅ Supported | ✅ Supported |
| **Unix Pipe Input** | ✅ Supported | ✅ Supported |
| **Project Guidelines (`CLAUDE.md`)** | ✅ Supported | ✅ Reads both `OCITA.md` and `CLAUDE.md` |
| **Installation Footprint** | ~150 MB (Node dependencies) | **< 100 KB (Zero external dependencies)** |
| **Open Source** | ❌ Proprietary | ✅ MIT Open Source |

---

## 🚀 Quick Start

### 1. Installation

#### In Bash (Linux, macOS, WSL, Git Bash on Windows):
```bash
git clone https://github.com/himanshu/ocita-cli.git
cd ocita-cli
./install.sh
```

#### In PowerShell (Windows / Windows Terminal):
```powershell
git clone https://github.com/himanshu/ocita-cli.git
cd ocita-cli
.\install.ps1
```
*Tip: You can also simply run `ocita` from anywhere once `bin/` or `~/bin` is in your PATH!*

---

### 2. Configure Authentication (Claude.ai or API Keys)

You can authenticate in two ways:

#### A. Login with Claude.ai (Web Session or Anthropic API Key)
Launch `ocita` and run `/login claude`:
```bash
ocita
ocita:my-project> /login claude
```
You can paste:
1. Your **Claude.ai Web Session Key** (`sessionKey=sk-ant-sid...` from browser cookies: open `claude.ai` -> Press F12 -> Application/Storage -> Cookies -> `sessionKey`).
2. OR your **Anthropic API Key** (`sk-ant-api...`).

Your credentials are saved securely in `~/.config/ocita/auth.json`.

#### B. Direct Environment Variables
```bash
# Option 1: Direct Anthropic (Claude 3.7 / 3.5 Sonnet)
export ANTHROPIC_API_KEY="sk-ant-..."

# Option 2: OpenRouter (Default - Claude 3.7, DeepSeek R1, GPT-4o, etc.)
export OPENROUTER_API_KEY="sk-or-v1-..."

# Option 3: DeepSeek
export DEEPSEEK_API_KEY="sk-..."

# Option 4: OpenAI
export OPENAI_API_KEY="sk-..."

# Option 5: Local & Free via Ollama (No API key needed!)
# Just run: ocita -p ollama -m qwen2.5-coder:7b
```

---

## 🤖 Gemini & ChatGPT Quick Access

You can seamlessly switch between **Google Gemini**, **OpenAI ChatGPT**, and **Claude** at any time:

### Switching in Interactive REPL
```bash
ocita:my-project> /gemini                # Switches to Google Gemini (gemini-2.0-flash)
ocita:my-project> /gemini gemini-1.5-pro # Switches to Gemini 1.5 Pro
ocita:my-project> /chatgpt               # Switches to ChatGPT (chatgpt-4o-latest / gpt-4o)
ocita:my-project> /chatgpt o3-mini       # Switches to OpenAI o3-mini reasoning model
```

### Launching Directly from CLI
```bash
# Launch with Gemini
ocita -p gemini -m gemini-2.0-flash

# Launch with ChatGPT
ocita -p chatgpt -m gpt-4o
```

---

## ⏳ Deliberate Slow Pacing & Comprehensive Code Commenting

`ocita` includes a **deliberate slow pacing mode** (`--slow`, `/slow`) designed for high-stakes enterprise engineering:

1. **Observable Step Pacing**: Rather than rushing blindly through edits, `ocita` introduces controlled pacing between tool calls so you can watch what it is reading, testing, and modifying.
2. **Mandatory Production Comments**: Every file created or edited includes:
   - **Module overview headers**: Explaining purpose and architecture.
   - **Full Docstrings**: Type contracts, parameter descriptions, return values, and failure modes.
   - **Inline comments**: Explaining the *why* behind algorithms, edge cases, formulas, and regexes.
   - **Refactor rationales**: Clear notes explaining why changes were made.

Toggle it anytime inside the REPL:
```bash
ocita:my-project> /slow off    # Switch to fast mode
ocita:my-project> /slow on     # Enable deliberate pacing with rich comments
```

`ocita` has native, automatic integration with Hack Club's **Hackatime** and **WakaTime**.

- Automatically reads your existing `~/.wakatime.cfg` (`api_url = https://hackatime.hackclub.com/api/hackatime/v1` and `api_key`).
- Sends heartbeats for:
  - Starting tasks and entering prompts (`coding`)
  - File modifications and edits (`write_file`, `edit_file`)
  - File reading and inspections (`view_file`)
  - Running test suites (`run_tests`)
- Check your tracked time anytime inside the REPL:
  ```bash
  ocita:my-project> /time
  ```
- Compatible with `wakatime-cli` (Windows, Linux, macOS) or falls back to direct asynchronous HTTPS REST API.

### 3. Launch

**Interactive REPL Mode:**
```bash
ocita
```

**Single-Task Mode:**
```bash
ocita "Add JWT authentication to the login endpoint in src/auth.py"
```

**Autonomous Non-Interactive Mode (`-y`):**
```bash
ocita -y "Run tests with pytest and fix any failures"
```

---

## 🔌 Supported Providers

| Provider | Flag | Key Variable | Default Model |
| :--- | :--- | :--- | :--- |
| **OpenRouter** | `-p openrouter` | `OPENROUTER_API_KEY` | `anthropic/claude-3.7-sonnet` |
| **Anthropic** | `-p anthropic` | `ANTHROPIC_API_KEY` | `claude-3-7-sonnet-20250219` |
| **DeepSeek** | `-p deepseek` | `DEEPSEEK_API_KEY` | `deepseek-chat` / `deepseek-reasoner` |
| **OpenAI** | `-p openai` | `OPENAI_API_KEY` | `gpt-4o` |
| **Ollama** (Local/Free) | `-p ollama` | *(None required)* | `qwen2.5-coder:7b` |
| **Gemini** | `-p gemini` | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| **Groq** | `-p groq` | `GROQ_API_KEY` | `llama-3.3-70b-versatile` |

---

## 🖥️ Interactive REPL Slash Commands

Inside the `ocita` interactive prompt:

- `/help` — Display list of all available commands
- `/time` / `/hackatime` — View today's tracked coding time and Hackatime connection
- `/login [target]` — Authenticate with Claude.ai (sessionKey or API key) or provider keys
- `/auth` — View current authentication status across providers
- `/logout [provider]` — Clear stored credentials
- `/review` — Run deep enterprise architectural & security code review on current git diff
- `/commit [msg]` — Autonomous conventional git commit generator
- `/test [runner]` — Auto-detect and run project tests (npm, pytest, cargo, go, make)
- `/lint` — Run project linter and report defects
- `/doctor` — Run full system diagnostic (Git, Python, Bash, Hackatime, API keys)
- `/model [name]` — Switch model on the fly (e.g. `/model claude-3-7-sonnet`)
- `/provider [name]` — Switch provider (e.g. `/provider anthropic`)
- `/diff` — Inspect current git diff
- `/undo` — Revert the last file modified by ocita
- `/branch [name]` — View or create git branch
- `/export [md|html]` — Export conversation transcript to Markdown or HTML
- `/compact` — Compress conversation history to preserve context tokens
- `/clear` — Clear current conversation context
- `/cost` / `/stats` — View total prompt/completion tokens and tool calls
- `/init` — Generate an `OCITA.md` file in the current directory
- `/exit` or `/quit` — Exit ocita

---

## 🛡️ Security & Permissions

`ocita` follows a defense-in-depth permission model:
- Read-only tools (`view_file`, `list_dir`, `search_files`, `search_text`, `git_diff`) run smoothly to inspect context.
- Mutating actions (`bash`, `write_file`, `edit_file`) pause and prompt for confirmation:
  ```text
  ⚠️  Permission Required:
    Command: npm test
  Allow? [y]es / [n]o / [a]lways allow bash / [e]dit: 
  ```
- To run non-interactively in scripts or CI/CD pipelines, pass `-y` or `--dangerously-skip-permissions`.

---

## 📁 Repository Structure

```text
ocita-cli/
├── bin/
│   └── ocita                 # Main bash CLI executable
├── lib/
│   ├── ocita_core.py         # Autonomous agent engine & multi-provider client
│   ├── prompt.sh             # ANSI UI styling and banner
│   └── context.sh            # Context extractor (OCITA.md, git info, repo map)
├── config/
│   └── config.default.json   # Default settings & endpoints
├── docs/
│   ├── ARCHITECTURE.md       # Technical design and architecture
│   └── USAGE.md              # In-depth usage guide and workflows
├── tests/
│   └── test_engine.py        # Comprehensive test suite
├── install.sh                # One-line installer script
├── OCITA.md                  # Project instructions for ocita
└── README.md                 # Documentation
```

---

## 🧪 Testing

To run the automated test suite:
```bash
python tests/test_engine.py
```

---

## 📄 License

MIT © [Himanshu](https://github.com/himanshu)
