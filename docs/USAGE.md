# ocita Usage Guide

This guide covers workflows, configuration, shell piping, and tips for using **ocita**.

## 1. Quick Start

### Installation
Clone the repository and run the installer:
```bash
git clone https://github.com/himanshu/ocita-cli.git
cd ocita-cli
./install.sh
```

Or add `bin/ocita` directly to your `~/.bashrc`:
```bash
export PATH="$PATH:$HOME/ocita-cli/bin"
```

### Authentication Setup

Choose your preferred method:

#### Option 1: Login with Claude.ai (Web or API)
You can login interactively inside `ocita`:
```bash
ocita
ocita:my-project> /login claude
```
- **Claude.ai Web Session**: You can paste your `sessionKey=sk-ant-sid...` cookie from browser DevTools (`claude.ai` -> F12 -> Application/Storage -> Cookies).
- **Anthropic API Key**: Or paste your direct `sk-ant-api...` key.
- Check authentication status anytime with:
  ```bash
  ocita:my-project> /auth
  ```

#### Option 2: Environment Variables
```bash
# Direct Anthropic (Claude 3.7 / 3.5 Sonnet)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenRouter (Default - Claude 3.7, DeepSeek R1, GPT-4o, etc.)
export OPENROUTER_API_KEY="sk-or-v1-..."

# Direct OpenAI
export OPENAI_API_KEY="sk-..."

# DeepSeek
export DEEPSEEK_API_KEY="sk-..."

# Google Gemini
export GEMINI_API_KEY="AIzaSy..."

# Ollama (100% Free & Local, no key needed!)
# Just ensure Ollama is running: ollama serve
```

---

## ⏱️ Hackatime / WakaTime Time Tracking

`ocita` automatically reads your `~/.wakatime.cfg` file and sends heartbeats as you code, edit, and test.

### Viewing Time
```bash
ocita:my-project> /time
```
Output:
```text
⏱️  Hackatime / WakaTime Tracker:
  Today's Tracked Time: 1 hr 42 mins
  Project:             ocita-cli
  API Endpoint:        https://hackatime.hackclub.com/api/hackatime/v1
  Configured:          ✔ Yes
  CLI Tool:            ✔ C:\Users\himanshu\.wakatime\wakatime-cli-windows-amd64.exe
```

---

## 🏢 Enterprise Commands

### Autonomous Conventional Commits
```bash
ocita:my-project> /commit
```
`ocita` inspects your git diff, structures a Conventional Commit message (`feat(scope): ...`), stages the files, and creates the commit.

### Architectural & Security Code Review
```bash
ocita:my-project> /review
```
Performs a deep review on your current git diff covering SOLID principles, edge cases, OWASP vulnerabilities, and performance bottlenecks.

### Automated Testing
```bash
ocita:my-project> /test
```
Auto-detects whether your project is npm, pytest, cargo, go, or make, executes the suite, and summarizes failures.

### System Diagnostics
```bash
ocita:my-project> /doctor
```
Validates Python, Git, Ripgrep, Hackatime configuration, and active AI provider connectivity.

---

## 2. Interactive REPL Mode

Launch `ocita` inside any code repository:
```bash
ocita
```

You will see:
```text
  ___   ____ _ _____ _   
 / _ \ / ___(_)__   / \  
| | | | |   | | / // _ \ 
| |_| | |___| |/ // ___ \
 \___/ \____|_/_//_/   \_\
  Smart Claude Code CLI Alternative in Bash | v1.0.0

Working Directory: /home/user/my-app
Provider: openrouter | Model: anthropic/claude-3.7-sonnet
Type your prompt or /help for commands. Press Ctrl+C or Ctrl+D to exit.

ocita:my-app> 
```

### REPL Commands
- `/help`: Display available commands
- `/model <name>`: Switch active model on the fly (e.g. `/model deepseek/deepseek-r1`)
- `/provider <name>`: Switch provider (e.g. `/provider ollama`)
- `/diff`: Display unstaged git changes
- `/undo`: Revert the last file change made by ocita
- `/clear`: Clear conversation context
- `/compact`: Truncate older context to save tokens
- `/cost`: Show tokens used and call count
- `/init`: Generate starter `OCITA.md` in current directory
- `/exit`: Exit session

---

## 3. Single-Task & Non-Interactive Mode

Execute a specific task directly without entering interactive mode:
```bash
ocita "Add a health-check endpoint at /api/health returning status 200 OK"
```

Run fully autonomously without manual tool confirmation prompts:
```bash
ocita -y "Find all deprecated console.log statements in src/ and remove them"
```

---

## 4. Unix Pipeline & Bash Integration

### Diagnosing Log Files
```bash
cat /var/log/nginx/error.log | ocita "Why are these requests failing?"
```

### Code Reviewing Git Diffs
```bash
git diff main | ocita "Review this diff for security risks and edge cases"
```

### Analyzing Test Failures
```bash
pytest | ocita "Diagnose the failing test and fix it in place"
```

---

## 5. Local Offline Coding with Ollama

Run completely offline with zero data leaving your machine:
```bash
# Pull model in Ollama
ollama pull qwen2.5-coder:7b

# Launch ocita with Ollama
ocita -p ollama -m qwen2.5-coder:7b
```

---

## 6. Project Instructions (OCITA.md / CLAUDE.md)
`ocita` automatically reads project instructions from the current or parent directories. You can initialize one with:
```bash
ocita --init
```
Or create an `OCITA.md` file specifying build commands, code guidelines, and constraints.
