#!/usr/bin/env python3
"""
ocita_core.py - Core Engine for ocita (Enterprise Claude Code CLI alternative for Bash)
Zero external dependencies - Uses Python 3 Standard Library only.
Integrated with Hackatime, Claude.ai Web & API Auth, Enterprise System Prompt, and Testing Suite.
"""

import sys
import os
import re
import json
import time
import glob
import shlex
import shutil
import base64
import urllib.request
import urllib.error
import urllib.parse
import subprocess
import threading
from pathlib import Path

# Optional readline support for nice terminal editing & history
try:
    import readline
except ImportError:
    pass

# Enable ANSI virtual terminal processing on Windows (PowerShell, CMD, Windows Terminal)
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        hStdOut = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode))
        mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        kernel32.SetConsoleMode(hStdOut, mode)
    except Exception:
        pass

# Import modular enterprise components
from auth import AuthManager
from hackatime import HackatimeTracker
from prompts import build_enterprise_system_prompt

# ==============================================================================
# ANSI Terminal Styling
# ==============================================================================
class Style:
    IS_TTY = sys.stdout.isatty()
    RESET = "\033[0m" if IS_TTY else ""
    BOLD = "\033[1m" if IS_TTY else ""
    DIM = "\033[2m" if IS_TTY else ""
    ITALIC = "\033[3m" if IS_TTY else ""
    UNDERLINE = "\033[4m" if IS_TTY else ""

    BLACK = "\033[30m" if IS_TTY else ""
    RED = "\033[31m" if IS_TTY else ""
    GREEN = "\033[32m" if IS_TTY else ""
    YELLOW = "\033[33m" if IS_TTY else ""
    BLUE = "\033[34m" if IS_TTY else ""
    MAGENTA = "\033[35m" if IS_TTY else ""
    CYAN = "\033[36m" if IS_TTY else ""
    WHITE = "\033[37m" if IS_TTY else ""

    BRIGHT_BLACK = "\033[90m" if IS_TTY else ""
    BRIGHT_RED = "\033[91m" if IS_TTY else ""
    BRIGHT_GREEN = "\033[92m" if IS_TTY else ""
    BRIGHT_YELLOW = "\033[93m" if IS_TTY else ""
    BRIGHT_BLUE = "\033[94m" if IS_TTY else ""
    BRIGHT_MAGENTA = "\033[95m" if IS_TTY else ""
    BRIGHT_CYAN = "\033[96m" if IS_TTY else ""
    BRIGHT_WHITE = "\033[97m" if IS_TTY else ""
    BG_DARK = "\033[48;5;236m" if IS_TTY else ""


def colorize(text, style_seq):
    return f"{style_seq}{text}{Style.RESET}"


def print_banner():
    banner = f"""{Style.BOLD}{Style.CYAN}
  ___   ____ _ _____ _   
 / _ \\ / ___(_)__   / \\  
| | | | |   | | / // _ \\ 
| |_| | |___| |/ // ___ \\
 \\___/ \\____|_/_//_/   \\_\\{Style.RESET}
{Style.DIM}  Enterprise Claude Code CLI Alternate in Bash | v1.2.0 | Hackatime Enabled{Style.RESET}
"""
    print(banner)


# ==============================================================================
# Spinner & Progress Animation
# ==============================================================================
class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message="Thinking..."):
        self.message = message
        self.running = False
        self.thread = None
        self.is_tty = sys.stdout.isatty()

    def _spin(self):
        idx = 0
        while self.running:
            frame = self.FRAMES[idx % len(self.FRAMES)]
            if self.is_tty:
                sys.stdout.write(f"\r{Style.CYAN}{frame}{Style.RESET} {Style.DIM}{self.message}{Style.RESET} ")
                sys.stdout.flush()
            time.sleep(0.08)
            idx += 1

    def start(self):
        if not self.is_tty:
            return
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def update(self, new_message):
        self.message = new_message

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        if self.is_tty:
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()


# ==============================================================================
# Terminal Markdown Renderer
# ==============================================================================
def render_markdown(text):
    if not Style.IS_TTY:
        return text

    lines = text.split("\n")
    in_code_block = False
    code_lang = ""
    rendered = []

    for line in lines:
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line[3:].strip()
                rendered.append(f"{Style.DIM}┌─ {code_lang or 'code'} ────────────────────────────────────────{Style.RESET}")
            else:
                in_code_block = False
                rendered.append(f"{Style.DIM}└────────────────────────────────────────────────────{Style.RESET}")
            continue

        if in_code_block:
            rendered.append(f"{Style.CYAN}│ {Style.RESET}{line}")
            continue

        # Format headings
        if line.startswith("# "):
            rendered.append(f"\n{Style.BOLD}{Style.BRIGHT_CYAN}# {line[2:]}{Style.RESET}")
        elif line.startswith("## "):
            rendered.append(f"\n{Style.BOLD}{Style.BRIGHT_BLUE}## {line[3:]}{Style.RESET}")
        elif line.startswith("### "):
            rendered.append(f"\n{Style.BOLD}{Style.WHITE}### {line[4:]}{Style.RESET}")
        elif line.startswith("> "):
            rendered.append(f"{Style.DIM}│ {line[2:]}{Style.RESET}")
        elif line.startswith("- ") or line.startswith("* "):
            content = line[2:]
            content = re.sub(r"`([^`]+)`", f"{Style.YELLOW}\\1{Style.RESET}", content)
            content = re.sub(r"\*\*([^*]+)\*\*", f"{Style.BOLD}\\1{Style.RESET}", content)
            rendered.append(f"  {Style.BRIGHT_CYAN}•{Style.RESET} {content}")
        else:
            l = line
            l = re.sub(r"`([^`]+)`", f"{Style.YELLOW}\\1{Style.RESET}", l)
            l = re.sub(r"\*\*([^*]+)\*\*", f"{Style.BOLD}\\1{Style.RESET}", l)
            rendered.append(l)

    return "\n".join(rendered)


# ==============================================================================
# Tool Definitions & Implementations
# ==============================================================================
TOOLS_SCHEMA = [
    {
        "name": "bash",
        "description": "Execute a bash shell command in the project directory. Use this to run build commands, tests, git operations, install dependencies, or inspect the environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The exact bash command line to run."
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "view_file",
        "description": "Read the contents of a file. Supports line range viewing to inspect specific sections of large files.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative or absolute path to the file to read."
                },
                "start_line": {
                    "type": "integer",
                    "description": "Optional starting line number (1-based)."
                },
                "end_line": {
                    "type": "integer",
                    "description": "Optional ending line number (inclusive)."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "edit_file",
        "description": "Replace an exact string in a file with new content. Fails safely if the old_string is not found or appears multiple times without exact specificity.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit."
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact text to be replaced (must match whitespace and indentation exactly)."
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement text."
                }
            },
            "required": ["path", "old_string", "new_string"]
        }
    },
    {
        "name": "write_file",
        "description": "Create a new file or completely overwrite an existing file with the specified content.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path of the file to create or overwrite."
                },
                "content": {
                    "type": "string",
                    "description": "The full text content to write."
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "list_dir",
        "description": "List files and subdirectories in a directory with entry count, file types, and sizes.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path (defaults to current directory if omitted)."
                }
            }
        }
    },
    {
        "name": "search_files",
        "description": "Find files matching a glob pattern (e.g. '**/*.py', 'src/**/*.tsx', '*.json').",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match."
                },
                "path": {
                    "type": "string",
                    "description": "Directory path to search in (defaults to current directory)."
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "search_text",
        "description": "Search for a regex or substring across files in the codebase (uses ripgrep if installed, or fast Python regex traversal).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text or regex query to search."
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (defaults to '.')."
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Optional file pattern to limit search, e.g. '*.py' or '*.js'."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "git_diff",
        "description": "Inspect unstaged and staged git changes in the repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "staged": {
                    "type": "boolean",
                    "description": "Whether to view staged changes (--staged)."
                }
            }
        }
    },
    {
        "name": "git_commit",
        "description": "Stage files and commit changes with a conventional commit message.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Conventional commit message (e.g. 'feat(auth): add JWT validation')."
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of files to stage; defaults to all tracked and untracked changes."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "run_tests",
        "description": "Auto-detect and run the project test suite (npm test, pytest, cargo test, go test, mvn test).",
        "parameters": {
            "type": "object",
            "properties": {
                "runner": {
                    "type": "string",
                    "description": "Optional custom test command override (e.g. 'pytest tests/test_auth.py')."
                }
            }
        }
    },
    {
        "name": "code_outline",
        "description": "Extract top-level structure, classes, functions, and interfaces from a code file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the source code file to outline."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "wakatime_heartbeat",
        "description": "Explicitly record a coding heartbeat to Hackatime / WakaTime for a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file being worked on."
                },
                "is_write": {
                    "type": "boolean",
                    "description": "Whether this heartbeat represents a file modification."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "web_fetch",
        "description": "Fetch text content or JSON from an HTTP/HTTPS URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The web URL to fetch."
                }
            },
            "required": ["url"]
        }
    }
]


class ToolExecutor:
    def __init__(self, auto_approve=False, tracker=None):
        self.auto_approve = auto_approve
        self.always_allowed = set()
        self.last_modified_files = []
        self.tracker = tracker or HackatimeTracker()

    def execute(self, tool_name, args):
        method_name = f"tool_{tool_name}"
        if not hasattr(self, method_name):
            return f"Error: Unknown tool '{tool_name}'."
        
        # Confirmation check for mutating or executing actions
        is_mutating = tool_name in ("bash", "write_file", "edit_file", "git_commit")
        if is_mutating and not self.auto_approve and tool_name not in self.always_allowed:
            confirmed, modified_args = self._prompt_confirmation(tool_name, args)
            if not confirmed:
                return "Operation aborted by user."
            args = modified_args

        try:
            handler = getattr(self, method_name)
            return handler(args)
        except Exception as e:
            return f"Execution error in {tool_name}: {str(e)}"

    def _prompt_confirmation(self, tool_name, args):
        print(f"\n{Style.BOLD}{Style.BRIGHT_YELLOW}⚠️  Permission Required:{Style.RESET}")
        if tool_name == "bash":
            print(f"  Command: {Style.CYAN}{args.get('command')}{Style.RESET}")
        elif tool_name in ("write_file", "edit_file"):
            print(f"  File: {Style.CYAN}{args.get('path')}{Style.RESET}")
            if tool_name == "edit_file":
                print(f"  Edit old text ({len(args.get('old_string', ''))} chars) -> new text ({len(args.get('new_string', ''))} chars)")
            else:
                lines = args.get('content', '').count('\n') + 1
                print(f"  Write content ({lines} lines, {len(args.get('content', ''))} chars)")
        elif tool_name == "git_commit":
            print(f"  Commit Message: {Style.CYAN}{args.get('message')}{Style.RESET}")

        while True:
            try:
                choice = input(f"{Style.BOLD}Allow? [y]es / [n]o / [a]lways allow {tool_name} / [e]dit: {Style.RESET}").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                return False, args

            if choice in ("y", "yes", ""):
                return True, args
            elif choice in ("n", "no"):
                return False, args
            elif choice in ("a", "always"):
                self.always_allowed.add(tool_name)
                return True, args
            elif choice in ("e", "edit"):
                if tool_name == "bash":
                    try:
                        new_cmd = input(f"New command [{args.get('command')}]: ").strip()
                        if new_cmd:
                            args["command"] = new_cmd
                        return True, args
                    except (EOFError, KeyboardInterrupt):
                        return False, args
                elif tool_name == "git_commit":
                    try:
                        new_msg = input(f"New commit message [{args.get('message')}]: ").strip()
                        if new_msg:
                            args["message"] = new_msg
                        return True, args
                    except (EOFError, KeyboardInterrupt):
                        return False, args
                else:
                    print("Interactive editing only supported for bash or commit commands.")
            else:
                print("Invalid choice. Enter y, n, a, or e.")

    def tool_bash(self, args):
        cmd = args.get("command", "").strip()
        if not cmd:
            return "Error: Empty command provided."

        print(f"{Style.BOLD}{Style.CYAN}⚡ [bash]{Style.RESET} {cmd}")
        self.tracker.send_heartbeat("terminal", is_write=True, category="building")

        try:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            stdout, _ = process.communicate(timeout=180)
            exit_code = process.returncode

            output = stdout or ""
            max_len = 15000
            if len(output) > max_len:
                output = output[:max_len] + f"\n... [Output truncated; {len(stdout) - max_len} bytes omitted]"

            res = f"Exit code: {exit_code}\nOutput:\n{output}" if output else f"Exit code: {exit_code} (No output)"
            return res
        except subprocess.TimeoutExpired:
            process.kill()
            return "Error: Command timed out after 180 seconds."
        except Exception as e:
            return f"Error executing bash: {str(e)}"

    def tool_view_file(self, args):
        path_str = args.get("path", "")
        if not path_str:
            return "Error: path is required."
        p = Path(path_str)
        if not p.is_file():
            return f"Error: File not found at '{path_str}'."

        start_line = args.get("start_line")
        end_line = args.get("end_line")

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return f"Error reading file: {str(e)}"

        # Send read heartbeat
        self.tracker.send_heartbeat(path_str, is_write=False)

        total_lines = len(lines)
        s = max(1, int(start_line)) if start_line is not None else 1
        e = min(total_lines, int(end_line)) if end_line is not None else total_lines

        if s > total_lines:
            return f"Error: start_line {s} exceeds file line count ({total_lines})."

        print(f"{Style.BOLD}{Style.CYAN}📖 [view]{Style.RESET} {path_str} (lines {s}-{e} of {total_lines})")
        
        result_lines = []
        for idx in range(s - 1, e):
            line_no = idx + 1
            clean_line = lines[idx].rstrip("\r\n")
            result_lines.append(f"{line_no:5d} | {clean_line}")

        return "\n".join(result_lines)

    def tool_edit_file(self, args):
        path_str = args.get("path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")

        if not path_str or not old_string:
            return "Error: path and old_string are required."

        p = Path(path_str)
        if not p.is_file():
            return f"Error: File not found at '{path_str}'."

        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            return f"Error reading file for edit: {str(e)}"

        content_norm = content.replace("\r\n", "\n")
        old_norm = old_string.replace("\r\n", "\n")
        new_norm = new_string.replace("\r\n", "\n")

        count = content_norm.count(old_norm)
        if count == 0:
            return f"Error: old_string not found in '{path_str}'. Verify exact whitespace, indentation and characters."
        if count > 1:
            return f"Error: old_string matches {count} occurrences in '{path_str}'. Please provide more surrounding context to disambiguate."

        updated_content = content_norm.replace(old_norm, new_norm, 1)
        if "\r\n" in content:
            updated_content = updated_content.replace("\n", "\r\n")

        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(updated_content)
            self.last_modified_files.append(path_str)
            # Send write heartbeat to Hackatime
            self.tracker.send_heartbeat(path_str, is_write=True)
            print(f"{Style.BOLD}{Style.GREEN}✏️  [edit]{Style.RESET} Successfully edited {path_str}")
            return f"Successfully updated '{path_str}' (1 replacement made)."
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def tool_write_file(self, args):
        path_str = args.get("path", "")
        content = args.get("content", "")

        if not path_str:
            return "Error: path is required."

        p = Path(path_str)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            self.last_modified_files.append(path_str)
            self.tracker.send_heartbeat(path_str, is_write=True)
            lines_count = content.count("\n") + 1
            print(f"{Style.BOLD}{Style.GREEN}📝 [write]{Style.RESET} Wrote {path_str} ({lines_count} lines, {len(content)} bytes)")
            return f"File '{path_str}' written successfully ({lines_count} lines, {len(content)} bytes)."
        except Exception as e:
            return f"Error writing file '{path_str}': {str(e)}"

    def tool_git_commit(self, args):
        message = args.get("message", "").strip()
        files = args.get("files", [])
        if not message:
            return "Error: Commit message is required."

        print(f"{Style.BOLD}{Style.CYAN}📦 [git commit]{Style.RESET} '{message}'")
        try:
            if files:
                for f in files:
                    subprocess.run(["git", "add", f], check=True, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["git", "add", "-A"], check=True, stderr=subprocess.DEVNULL)

            res = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            output = res.stdout.strip() or res.stderr.strip()
            self.tracker.send_heartbeat("git_commit", is_write=True, category="coding")
            return f"Commit completed (Exit {res.returncode}):\n{output}"
        except Exception as e:
            return f"Git commit failed: {str(e)}"

    def tool_run_tests(self, args):
        runner = args.get("runner", "").strip()
        print(f"{Style.BOLD}{Style.CYAN}🧪 [run_tests]{Style.RESET} Testing suite...")

        # Detect runner if not explicitly provided
        if not runner:
            if Path("package.json").is_file():
                runner = "npm test"
            elif Path("pytest.ini").is_file() or Path("tests").is_dir() or glob.glob("test_*.py"):
                runner = "pytest" if shutil.which("pytest") else "python -m unittest discover tests"
            elif Path("Cargo.toml").is_file():
                runner = "cargo test"
            elif Path("go.mod").is_file():
                runner = "go test ./..."
            elif Path("Makefile").is_file():
                runner = "make test"
            else:
                runner = "npm test"

        print(f"  Executing test runner: {Style.YELLOW}{runner}{Style.RESET}")
        self.tracker.send_heartbeat("tests", is_write=False, category="testing")
        return self.tool_bash({"command": runner})

    def tool_code_outline(self, args):
        path_str = args.get("path", "")
        p = Path(path_str)
        if not p.is_file():
            return f"Error: File not found at '{path_str}'."

        print(f"{Style.BOLD}{Style.CYAN}🗺️  [outline]{Style.RESET} {path_str}")
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return f"Error reading file: {str(e)}"

        outline = []
        # Basic AST-like regex outline for major languages
        patterns = [
            re.compile(r"^\s*(def|class|async def)\s+([a-zA-Z0-9_]+)"),
            re.compile(r"^\s*(export\s+)?(function|class|interface|type|const|let)\s+([a-zA-Z0-9_]+)"),
            re.compile(r"^\s*(pub\s+)?(fn|struct|enum|trait|impl)\s+([a-zA-Z0-9_]+)")
        ]

        for idx, line in enumerate(lines, 1):
            for pat in patterns:
                m = pat.match(line)
                if m:
                    outline.append(f"Line {idx:4d}: {line.strip()}")
                    break

        return "\n".join(outline) if outline else "No top-level declarations detected."

    def tool_wakatime_heartbeat(self, args):
        path = args.get("path", "coding")
        is_write = args.get("is_write", False)
        self.tracker.send_heartbeat(path, is_write=is_write)
        return f"Logged heartbeat for '{path}' (is_write={is_write}) to Hackatime."

    def tool_list_dir(self, args):
        path_str = args.get("path", ".") or "."
        p = Path(path_str)
        if not p.is_dir():
            return f"Error: '{path_str}' is not a directory."

        print(f"{Style.BOLD}{Style.CYAN}📁 [ls]{Style.RESET} {path_str}")
        try:
            entries = []
            for item in sorted(p.iterdir()):
                name = item.name
                if name.startswith(".git"):
                    continue
                if item.is_dir():
                    entries.append(f"{name}/ [DIR]")
                else:
                    size = item.stat().st_size
                    entries.append(f"{name} ({size} bytes)")
            return "\n".join(entries) if entries else "(Empty directory)"
        except Exception as e:
            return f"Error listing directory: {str(e)}"

    def tool_search_files(self, args):
        pattern = args.get("pattern", "*")
        root_path = args.get("path", ".") or "."
        print(f"{Style.BOLD}{Style.CYAN}🔍 [glob]{Style.RESET} Pattern '{pattern}' in {root_path}")

        try:
            matches = []
            for p in Path(root_path).rglob(pattern):
                parts = p.parts
                if any(skip in parts for skip in (".git", "node_modules", ".venv", "__pycache__", "dist", "build")):
                    continue
                matches.append(str(p))
                if len(matches) >= 100:
                    break

            if not matches:
                return f"No files matched pattern '{pattern}'."
            return f"Found {len(matches)} files:\n" + "\n".join(matches[:100])
        except Exception as e:
            return f"Error searching files: {str(e)}"

    def tool_search_text(self, args):
        query = args.get("query", "")
        root_path = args.get("path", ".") or "."
        file_pattern = args.get("file_pattern", "")

        if not query:
            return "Error: query is required."

        print(f"{Style.BOLD}{Style.CYAN}🔎 [grep]{Style.RESET} '{query}' in {root_path}")

        if shutil.which("rg"):
            cmd = ["rg", "-n", "--max-count", "100", query, root_path]
            if file_pattern:
                cmd.extend(["-g", file_pattern])
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
                output = res.stdout
                return output if output else f"No matches found for '{query}'."
            except Exception:
                pass

        try:
            regex = re.compile(query, re.IGNORECASE)
            matches = []
            for root, dirs, files in os.walk(root_path):
                dirs[:] = [d for d in dirs if d not in (".git", "node_modules", ".venv", "__pycache__", "dist", "build")]
                for f in files:
                    if file_pattern and not Path(f).match(file_pattern):
                        continue
                    file_path = os.path.join(root, f)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as stream:
                            for idx, line in enumerate(stream, 1):
                                if regex.search(line):
                                    matches.append(f"{file_path}:{idx}:{line.strip()}")
                                    if len(matches) >= 100:
                                        break
                    except Exception:
                        continue
                if len(matches) >= 100:
                    break

            return "\n".join(matches) if matches else f"No matches found for '{query}'."
        except Exception as e:
            return f"Error executing search: {str(e)}"

    def tool_git_diff(self, args):
        staged = args.get("staged", False)
        cmd = "git diff --staged" if staged else "git diff"
        print(f"{Style.BOLD}{Style.CYAN}🌿 [git diff]{Style.RESET} {cmd}")
        try:
            res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
            output = res.stdout
            return output if output else "No changes detected (working tree clean)."
        except Exception as e:
            return f"Error getting git diff: {str(e)}"

    def tool_web_fetch(self, args):
        url = args.get("url", "")
        if not url.startswith("http://") and not url.startswith("https://"):
            return "Error: URL must start with http:// or https://"

        print(f"{Style.BOLD}{Style.CYAN}🌐 [fetch]{Style.RESET} {url}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ocita-cli/1.2.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode("utf-8", errors="replace")
                if len(data) > 10000:
                    data = data[:10000] + f"\n... [Truncated {len(data)-10000} bytes]"
                return data
        except Exception as e:
            return f"Failed to fetch {url}: {str(e)}"


# ==============================================================================
# Multi-Provider Protocol Adapter (API & Claude.ai Session)
# ==============================================================================
class ProviderHandler:
    auth_manager = AuthManager()

    @classmethod
    def call_api(cls, provider, model, system_prompt, messages, tools):
        provider = provider.lower()
        if provider in ("anthropic", "claude"):
            return cls._call_anthropic(model, system_prompt, messages, tools)
        else:
            return cls._call_openai_compatible(provider, model, system_prompt, messages, tools)

    @classmethod
    def _call_anthropic(cls, model, system_prompt, messages, tools):
        auth_type, key = cls.auth_manager.get_claude_auth_type()
        if not key:
            raise ValueError(
                "Anthropic / Claude credentials not found.\n"
                "Please run '/login claude' or export ANTHROPIC_API_KEY=your_key."
            )

        # Normalize model name for Anthropic API
        anthropic_model = model
        if "claude-3-7-sonnet" in model or "claude-3.7-sonnet" in model:
            anthropic_model = "claude-3-7-sonnet-20250219"
        elif "claude-3-5-sonnet" in model or "claude-3.5-sonnet" in model:
            anthropic_model = "claude-3-5-sonnet-20241022"

        # Map tools to Anthropic schema
        anthropic_tools = []
        for t in tools:
            anthropic_tools.append({
                "name": t["name"],
                "description": t["description"],
                "input_schema": t.get("parameters", {"type": "object", "properties": {}})
            })

        # Map messages
        anthropic_msgs = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                continue
            elif role == "user":
                anthropic_msgs.append({"role": "user", "content": content})
            elif role == "assistant":
                if "tool_calls" in m and m["tool_calls"]:
                    c_blocks = []
                    if content:
                        c_blocks.append({"type": "text", "text": content})
                    for tc in m["tool_calls"]:
                        c_blocks.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc["args"]
                        })
                    anthropic_msgs.append({"role": "assistant", "content": c_blocks})
                else:
                    anthropic_msgs.append({"role": "assistant", "content": content})
            elif role == "tool":
                anthropic_msgs.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.get("tool_call_id", ""),
                        "content": str(content)
                    }]
                })

        payload = {
            "model": anthropic_model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": anthropic_msgs,
            "tools": anthropic_tools
        }

        headers = {
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        if auth_type == "claude_ai_session":
            # Session cookie authentication
            headers["Cookie"] = f"sessionKey={key}"
            headers["x-api-key"] = key
        else:
            headers["x-api-key"] = key

        url = "https://api.anthropic.com/v1/messages"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        text_content = ""
        tool_calls = []

        for block in data.get("content", []):
            if block.get("type") == "text":
                text_content += block.get("text", "")
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "id": block.get("id"),
                    "name": block.get("name"),
                    "args": block.get("input", {})
                })

        usage = data.get("usage", {})
        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0)
        }

    @classmethod
    def _call_openai_compatible(cls, provider, model, system_prompt, messages, tools):
        api_key = cls.auth_manager.get_key(provider)
        if provider != "ollama" and not api_key:
            raise ValueError(
                f"No API key configured for provider '{provider}'.\n"
                f"Please run '/login {provider}' or export {provider.upper()}_API_KEY=your_key."
            )

        openai_tools = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {"type": "object", "properties": {}})
                }
            })

        chat_msgs = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = m["role"]
            if role == "assistant" and "tool_calls" in m and m["tool_calls"]:
                tc_list = []
                for tc in m["tool_calls"]:
                    tc_list.append({
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"])
                        }
                    })
                chat_msgs.append({
                    "role": "assistant",
                    "content": m.get("content") or None,
                    "tool_calls": tc_list
                })
            elif role == "tool":
                chat_msgs.append({
                    "role": "tool",
                    "tool_call_id": m.get("tool_call_id", ""),
                    "content": str(m.get("content", ""))
                })
            else:
                chat_msgs.append({
                    "role": role,
                    "content": m.get("content", "")
                })

        payload = {
            "model": model,
            "messages": chat_msgs,
            "tools": openai_tools,
            "tool_choice": "auto"
        }

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/ocita-cli/ocita"
            headers["X-Title"] = "ocita-cli"

        endpoints = {
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "openai": "https://api.openai.com/v1/chat/completions",
            "chatgpt": "https://api.openai.com/v1/chat/completions",
            "deepseek": "https://api.deepseek.com/chat/completions",
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "google": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "mistral": "https://api.mistral.ai/v1/chat/completions",
            "perplexity": "https://api.perplexity.ai/chat/completions",
            "together": "https://api.together.xyz/v1/chat/completions",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "ollama": "http://localhost:11434/v1/chat/completions"
        }
        url = endpoints.get(provider, "https://openrouter.ai/api/v1/chat/completions")

        # Normalize model names for providers
        actual_model = model
        if provider in ("gemini", "google"):
            if not actual_model or actual_model in ("default", "gemini", "argon", "gemini-argon"):
                actual_model = "gemini-4-argon"
        elif provider in ("chatgpt", "openai"):
            if not actual_model or actual_model in ("default", "chatgpt"):
                actual_model = "chatgpt-4o-latest"

        payload["model"] = actual_model
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        choice = data["choices"][0]["message"]
        text_content = choice.get("content") or ""
        tool_calls = []

        if "tool_calls" in choice and choice["tool_calls"]:
            for tc in choice["tool_calls"]:
                fn = tc.get("function", {})
                args_raw = fn.get("arguments", "{}")
                try:
                    args_parsed = json.loads(args_raw)
                except Exception:
                    args_parsed = {"raw": args_raw}

                tool_calls.append({
                    "id": tc.get("id", f"call_{int(time.time()*1000)}"),
                    "name": fn.get("name", ""),
                    "args": args_parsed
                })

        usage = data.get("usage", {})
        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0)
        }


# ==============================================================================
# Context & Environment Discovery
# ==============================================================================
def gather_system_context():
    instructions = ""
    instructions_file = None
    cur = Path.cwd()

    for p in [cur] + list(cur.parents):
        for candidate in ["OCITA.md", "CLAUDE.md", "AGENT.md", ".ocita/instructions.md"]:
            target = p / candidate
            if target.is_file():
                try:
                    instructions = target.read_text(encoding="utf-8", errors="replace")
                    instructions_file = str(target)
                    break
                except Exception:
                    pass
        if instructions_file:
            break

    git_info = "Not a git repository."
    try:
        branch = subprocess.check_output("git branch --show-current", shell=True, stderr=subprocess.DEVNULL, text=True).strip()
        status = subprocess.check_output("git status --short", shell=True, stderr=subprocess.DEVNULL, text=True).strip()
        commits = subprocess.check_output("git log -n 5 --oneline", shell=True, stderr=subprocess.DEVNULL, text=True).strip()
        git_info = f"Current Branch: {branch}\nStatus:\n{status or 'Clean'}\nRecent Commits:\n{commits}"
    except Exception:
        pass

    dir_files = []
    try:
        for item in sorted(cur.iterdir()):
            if item.name.startswith(".git"):
                continue
            if item.is_dir():
                dir_files.append(f"{item.name}/ [DIR]")
            else:
                dir_files.append(item.name)
            if len(dir_files) >= 50:
                dir_files.append("... [more files]")
                break
    except Exception:
        pass

    # Detect active shell environment (Bash vs PowerShell)
    if "PSModulePath" in os.environ and sys.platform == "win32" and "BASH_VERSION" not in os.environ:
        active_shell = "PowerShell"
    elif "BASH_VERSION" in os.environ:
        active_shell = "Bash"
    else:
        active_shell = "PowerShell / Bash"

    system_prompt = build_enterprise_system_prompt(
        workspace_dir=str(cur),
        instructions_text=instructions,
        instructions_file=instructions_file,
        git_info=git_info,
        dir_listing=chr(10).join(dir_files),
        shell_name=active_shell
    )

    return system_prompt, instructions_file


# ==============================================================================
# Agent Session & Reasoning Loop
# ==============================================================================
class AgentSession:
    def __init__(self, provider="openrouter", model="anthropic/claude-3.7-sonnet", auto_approve=False, max_steps=25, slow_mode=True):
        self.provider = provider
        self.model = model
        self.max_steps = max_steps
        self.slow_mode = slow_mode
        self.tracker = HackatimeTracker()
        self.executor = ToolExecutor(auto_approve=auto_approve, tracker=self.tracker)
        self.system_prompt, self.instructions_file = gather_system_context()
        self.messages = []
        self.session_id = f"session_{int(time.time())}"
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tool_calls = 0

    def run_turn(self, user_prompt):
        self.messages.append({"role": "user", "content": user_prompt})
        self.tracker.send_heartbeat("user_prompt", is_write=True, category="coding")

        step = 0
        while step < self.max_steps:
            step += 1
            if self.slow_mode:
                time.sleep(0.35)

            spinner = Spinner(f"Thinking with {self.model} (step {step})...")
            spinner.start()

            try:
                response = ProviderHandler.call_api(
                    provider=self.provider,
                    model=self.model,
                    system_prompt=self.system_prompt,
                    messages=self.messages,
                    tools=TOOLS_SCHEMA
                )
            except Exception as e:
                spinner.stop()
                print(f"\n{Style.BOLD}{Style.RED}API Error:{Style.RESET} {str(e)}")
                return
            finally:
                spinner.stop()

            self.total_prompt_tokens += response.get("prompt_tokens", 0)
            self.total_completion_tokens += response.get("completion_tokens", 0)

            assistant_text = response.get("content", "")
            tool_calls = response.get("tool_calls", [])

            if assistant_text:
                print(render_markdown(assistant_text))

            if not tool_calls:
                self.messages.append({"role": "assistant", "content": assistant_text})
                break

            self.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "tool_calls": tool_calls
            })

            for tc in tool_calls:
                self.total_tool_calls += 1
                t_name = tc.get("name")
                t_args = tc.get("args", {})
                t_id = tc.get("id")

                if self.slow_mode:
                    print(f"{Style.DIM}  ⏳ [Paced] Evaluating {t_name}...{Style.RESET}")
                    time.sleep(0.3)

                result = self.executor.execute(t_name, t_args)

                self.messages.append({
                    "role": "tool",
                    "tool_call_id": t_id,
                    "name": t_name,
                    "content": result
                })

        if step >= self.max_steps:
            print(f"\n{Style.YELLOW}⚠️  Reached maximum reasoning steps ({self.max_steps}).{Style.RESET}")

        self.save_session()

    def save_session(self):
        sessions_dir = os.getenv("OCITA_SESSIONS_DIR", str(Path.home() / ".local/share/ocita/sessions"))
        Path(sessions_dir).mkdir(parents=True, exist_ok=True)
        session_file = Path(sessions_dir) / f"{self.session_id}.json"
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump({
                    "session_id": self.session_id,
                    "provider": self.provider,
                    "model": self.model,
                    "tokens": {
                        "prompt": self.total_prompt_tokens,
                        "completion": self.total_completion_tokens,
                        "tool_calls": self.total_tool_calls
                    },
                    "messages": self.messages
                }, f, indent=2)
        except Exception:
            pass


# ==============================================================================
# Interactive REPL & Extended Commands
# ==============================================================================
def handle_slash_command(cmd, session):
    parts = cmd.strip().split(maxsplit=1)
    keyword = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    auth_mgr = ProviderHandler.auth_manager

    if keyword in ("/help", "/h", "/?"):
        print(f"""
{Style.BOLD}Interactive Commands:{Style.RESET}
  {Style.CYAN}/help{Style.RESET}              Show this help message
  {Style.CYAN}/argon{Style.RESET}             Switch immediately to Google Gemini 4 Argon (Frontier Reasoning & Coding)
  {Style.CYAN}/gemini [model]{Style.RESET}    Switch provider to Google Gemini (e.g. gemini-4-argon, gemini-2.0-flash)
  {Style.CYAN}/chatgpt [model]{Style.RESET}   Switch provider to ChatGPT (e.g. chatgpt-4o-latest, gpt-4o, o3-mini)
  {Style.CYAN}/claude [model]{Style.RESET}    Switch provider to Anthropic Claude (e.g. claude-3-7-sonnet)
  {Style.CYAN}/models{Style.RESET}            List recommended frontier models for Gemini, ChatGPT & Claude
  {Style.CYAN}/slow [on|off]{Style.RESET}     Toggle deliberate step pacing & mandatory comment mode
  {Style.CYAN}/time{Style.RESET}, {Style.CYAN}/hackatime{Style.RESET}   View Hackatime tracking stats & connection
  {Style.CYAN}/login [target]{Style.RESET}    Authenticate with Claude.ai, Gemini, ChatGPT or API key
  {Style.CYAN}/logout [provider]{Style.RESET} Clear stored credentials
  {Style.CYAN}/auth{Style.RESET}              Display active authentication status
  {Style.CYAN}/review{Style.RESET}            Run enterprise architectural & security code review on diff
  {Style.CYAN}/commit [msg]{Style.RESET}      Autonomous conventional git commit generator
  {Style.CYAN}/test [runner]{Style.RESET}      Auto-detect and run project test suite
  {Style.CYAN}/lint{Style.RESET}              Auto-detect and run project linter
  {Style.CYAN}/doctor{Style.RESET}            Diagnose system, tools, Hackatime, and API health
  {Style.CYAN}/model [name]{Style.RESET}      View or switch active model
  {Style.CYAN}/provider [name]{Style.RESET}   View or switch provider (gemini, chatgpt, anthropic, etc.)
  {Style.CYAN}/diff{Style.RESET}              Show current git diff
  {Style.CYAN}/undo{Style.RESET}              Revert the last file modified by ocita
  {Style.CYAN}/branch [name]{Style.RESET}    View or create git branch
  {Style.CYAN}/export [md|html]{Style.RESET}  Export conversation transcript
  {Style.CYAN}/clear{Style.RESET}             Clear conversation history
  {Style.CYAN}/compact{Style.RESET}           Compact context window to save tokens
  {Style.CYAN}/cost{Style.RESET} / {Style.CYAN}/stats{Style.RESET}     Show token consumption and tool call statistics
  {Style.CYAN}/init{Style.RESET}              Create OCITA.md in current directory
  {Style.CYAN}/exit{Style.RESET}, {Style.CYAN}/quit{Style.RESET}        Exit ocita
""")
        return True

    elif keyword == "/argon":
        session.provider = "gemini"
        session.model = "gemini-4-argon"
        print(f"{Style.GREEN}✔ Switched to Google Gemini 4 Argon (gemini-4-argon){Style.RESET}")
        print(f"  {Style.DIM}Frontier reasoning, autonomous code architecture, 1M context window.{Style.RESET}")
        return True

    elif keyword == "/claude":
        model_name = arg or "claude-3-7-sonnet"
        session.provider = "anthropic"
        session.model = model_name
        print(f"{Style.GREEN}✔ Switched to Anthropic Claude ({model_name}){Style.RESET}")
        print(f"  {Style.DIM}Hybrid reasoning, deep coding precision, and enterprise architecture.{Style.RESET}")
        return True

    elif keyword == "/models":
        print(f"\n{Style.BOLD}Recommended Frontier Models:{Style.RESET}")
        print(f"  {Style.CYAN}Google Gemini:{Style.RESET}")
        print(f"    • {Style.BOLD}gemini-4-argon{Style.RESET}       - Frontier Reasoning & Code Architecture (1M Context) [Default]")
        print(f"    • {Style.BOLD}gemini-2.0-flash{Style.RESET}     - Next-gen high speed & multi-modal execution")
        print(f"    • {Style.BOLD}gemini-1.5-pro{Style.RESET}       - Deep context reasoning & complex codebase analysis")
        print(f"  {Style.CYAN}OpenAI / ChatGPT:{Style.RESET}")
        print(f"    • {Style.BOLD}chatgpt-4o-latest{Style.RESET}    - Dynamic frontier model matching chatgpt.com")
        print(f"    • {Style.BOLD}gpt-4o{Style.RESET}               - Flagship high-intelligence multi-modal model")
        print(f"    • {Style.BOLD}o3-mini{Style.RESET}              - Advanced mathematical and competitive coding reasoning")
        print(f"  {Style.CYAN}Anthropic Claude:{Style.RESET}")
        print(f"    • {Style.BOLD}claude-3-7-sonnet{Style.RESET}    - Hybrid thinking and state-of-the-art coding")
        print(f"    • {Style.BOLD}claude-3-5-haiku{Style.RESET}     - Fast, cost-efficient everyday tasks\n")
        return True

    elif keyword == "/gemini":
        model_name = arg or "gemini-4-argon"
        session.provider = "gemini"
        session.model = model_name
        print(f"{Style.GREEN}✔ Switched provider to Google Gemini ({model_name}){Style.RESET}")
        return True

    elif keyword in ("/chatgpt", "/openai"):
        model_name = arg or "chatgpt-4o-latest"
        session.provider = "chatgpt"
        session.model = model_name
        print(f"{Style.GREEN}✔ Switched provider to ChatGPT ({model_name}){Style.RESET}")
        return True

    elif keyword == "/slow":
        if arg.lower() in ("off", "false", "0", "disable", "fast"):
            session.slow_mode = False
            print(f"{Style.YELLOW}Deliberate pacing mode: OFF (Fast mode){Style.RESET}")
        else:
            session.slow_mode = True
            print(f"{Style.GREEN}Deliberate pacing mode: ON (Thoughtful step pacing with comments enabled){Style.RESET}")
        return True

    elif keyword in ("/time", "/hackatime"):
        print(f"\n{Style.BOLD}{Style.CYAN}⏱️  Hackatime / WakaTime Tracker:{Style.RESET}")
        info = session.tracker.check_connection()
        today = session.tracker.get_today_stats()
        print(f"  Today's Tracked Time: {Style.BOLD}{Style.GREEN}{today}{Style.RESET}")
        if info.get("user_name"):
            print(f"  Account User:        {Style.BOLD}{info['user_name']}{Style.RESET}")
        print(f"  Project:             {session.tracker.project_name}")
        print(f"  API Endpoint:        {session.tracker.api_url}")
        print(f"  Server Connection:   {Style.GREEN}✔ Connected & Verified{Style.RESET}" if info['user_name'] else f"{Style.YELLOW}⚠ Unverified{Style.RESET}")
        print(f"  Transport:           Direct HTTPS REST API (Zero lag, no sqlite deadlock)\n")
        return True

    elif keyword == "/login":
        target = (arg or "").lower()
        if not target:
            print(f"\n{Style.BOLD}Select Provider to Authenticate:{Style.RESET}")
            print(f"  1. {Style.BOLD}gemini{Style.RESET}    - Google Gemini (Gemini 4 Argon, 2.0 Flash) [AI Studio key]")
            print(f"  2. {Style.BOLD}chatgpt{Style.RESET}   - OpenAI / ChatGPT (chatgpt-4o-latest, gpt-4o, o3-mini)")
            print(f"  3. {Style.BOLD}claude{Style.RESET}    - Claude.ai sessionKey or Anthropic API Key")
            print(f"  4. {Style.BOLD}other{Style.RESET}     - DeepSeek, Mistral, Perplexity, OpenRouter, Groq")
            target = input(f"{Style.CYAN}Enter provider [gemini/chatgpt/claude/other]: {Style.RESET}").strip().lower() or "gemini"

        if target in ("gemini", "google"):
            print(f"\n{Style.BOLD}Google Gemini Setup (Gemini 4 Argon, 2.0 Flash):{Style.RESET}")
            print("  Get your free API key at: https://aistudio.google.com/apikey")
            val = input(f"\n{Style.CYAN}Paste your Google Gemini API Key: {Style.RESET}").strip()
            if val:
                valid, msg = auth_mgr.validate_key("gemini", val)
                if not valid:
                    print(f"{Style.YELLOW}⚠ Warning: {msg}{Style.RESET}")
                auth_mgr.set_key("gemini", val)
                session.provider = "gemini"
                session.model = "gemini-4-argon"
                print(f"{Style.GREEN}✔ Successfully configured Google Gemini! Default model set to gemini-4-argon.{Style.RESET}")

        elif target in ("chatgpt", "openai"):
            print(f"\n{Style.BOLD}OpenAI / ChatGPT Setup (chatgpt-4o-latest, gpt-4o, o3-mini):{Style.RESET}")
            print("  Get your API key at: https://platform.openai.com/api-keys")
            val = input(f"\n{Style.CYAN}Paste your OpenAI / ChatGPT API Key: {Style.RESET}").strip()
            if val:
                valid, msg = auth_mgr.validate_key("chatgpt", val)
                if not valid:
                    print(f"{Style.YELLOW}⚠ Warning: {msg}{Style.RESET}")
                auth_mgr.set_key("chatgpt", val)
                session.provider = "chatgpt"
                session.model = "chatgpt-4o-latest"
                print(f"{Style.GREEN}✔ Successfully configured ChatGPT! Default model set to chatgpt-4o-latest.{Style.RESET}")

        elif target in ("claude", "claude.ai", "anthropic"):
            print(f"\n{Style.BOLD}Claude.ai & Anthropic Authentication Setup:{Style.RESET}")
            print("  1. Anthropic API Key (sk-ant-api...)")
            print("  2. Claude.ai Web Session Key (sk-ant-sid... from browser cookies)")
            print("     [Tip: Open claude.ai in browser -> F12 DevTools -> Application/Storage -> Cookies -> sessionKey]")
            val = input(f"\n{Style.CYAN}Paste your Anthropic API Key or Claude.ai sessionKey: {Style.RESET}").strip()
            if val:
                valid, msg = auth_mgr.validate_key("claude", val)
                if not valid:
                    print(f"{Style.YELLOW}⚠ Warning: {msg}{Style.RESET}")
                auth_mgr.set_key("claude", val)
                session.provider = "anthropic"
                session.model = "claude-3-7-sonnet"
                print(f"{Style.GREEN}✔ Successfully saved Claude credentials! Default model set to claude-3-7-sonnet.{Style.RESET}")
        else:
            val = input(f"{Style.CYAN}Enter API key for {target}: {Style.RESET}").strip()
            if val:
                valid, msg = auth_mgr.validate_key(target, val)
                if not valid:
                    print(f"{Style.YELLOW}⚠ Warning: {msg}{Style.RESET}")
                auth_mgr.set_key(target, val)
                session.provider = target
                print(f"{Style.GREEN}✔ Successfully saved {target} API key!{Style.RESET}")
        return True

    elif keyword == "/logout":
        target = (arg or session.provider).lower()
        auth_mgr.remove_key(target)
        print(f"{Style.GREEN}✔ Cleared stored credentials for {target}.{Style.RESET}")
        return True

    elif keyword == "/auth":
        print(f"\n{Style.BOLD}Configured Authentication Providers:{Style.RESET}")
        status = auth_mgr.list_status()
        for p, d in status.items():
            mark = f"{Style.GREEN}✔ Connected{Style.RESET}" if d["authenticated"] else f"{Style.RED}✖ Not configured{Style.RESET}"
            detail = f"({d.get('type')}: {d.get('preview', '')})" if d.get("preview") else f"({d.get('type')})" if d.get("type") else ""
            print(f"  {p:<12} {mark} {Style.DIM}{detail}{Style.RESET}")
        print()
        return True

    elif keyword == "/review":
        diff_content = session.executor.tool_git_diff({"staged": False})
        if "No changes detected" in diff_content:
            print(f"{Style.YELLOW}No git changes detected to review.{Style.RESET}")
            return True
        review_prompt = f"""Conduct a rigorous Enterprise Architectural & Security Code Review of the following git diff:

```diff
{diff_content}
```

Evaluate across:
1. Architectural integrity & SOLID principles
2. Edge case coverage & defensive error handling
3. OWASP security risks (injection, sanitization, memory safety)
4. Performance & efficiency
Provide actionable remediation recommendations.
"""
        session.run_turn(review_prompt)
        return True

    elif keyword == "/commit":
        msg = arg
        if not msg:
            diff_content = session.executor.tool_git_diff({"staged": False})
            prompt = f"Inspect this git diff and create a conventional commit using git_commit:\n```diff\n{diff_content}\n```"
            session.run_turn(prompt)
        else:
            res = session.executor.tool_git_commit({"message": msg})
            print(res)
        return True

    elif keyword == "/test":
        res = session.executor.tool_run_tests({"runner": arg})
        print(res)
        return True

    elif keyword == "/lint":
        print(f"{Style.BOLD}{Style.CYAN}🔍 [lint]{Style.RESET} Checking code quality...")
        if Path("package.json").is_file():
            res = session.executor.tool_bash({"command": "npm run lint || npx eslint ."})
        elif glob.glob("*.py") or Path("tests").is_dir():
            cmd = "ruff check ." if shutil.which("ruff") else "flake8 ." if shutil.which("flake8") else "python -m py_compile *.py"
            res = session.executor.tool_bash({"command": cmd})
        else:
            res = "No standard linter configuration detected."
        print(res)
        return True

    elif keyword == "/doctor":
        print(f"\n{Style.BOLD}{Style.CYAN}🩺 ocita System Doctor Diagnostic:{Style.RESET}")
        # Python
        print(f"  Python:      {Style.GREEN}✔ {sys.version.split()[0]} ({sys.executable}){Style.RESET}")
        # Bash / Git
        git_path = shutil.which("git")
        print(f"  Git:         {Style.GREEN}✔ {git_path}{Style.RESET}" if git_path else f"  Git: {Style.RED}✖ Not found{Style.RESET}")
        # Ripgrep
        rg_path = shutil.which("rg")
        print(f"  Ripgrep:     {Style.GREEN}✔ {rg_path}{Style.RESET}" if rg_path else f"  Ripgrep: {Style.DIM}Python regex fallback active{Style.RESET}")
        # Hackatime
        waka = session.tracker.check_connection()
        print(f"  Hackatime:   {Style.GREEN}✔ Configured ({waka['api_url']}){Style.RESET}" if waka['configured'] else f"  Hackatime: {Style.YELLOW}⚠ Missing API key in ~/.wakatime.cfg{Style.RESET}")
        # Active Provider
        auth_type, key = auth_mgr.get_claude_auth_type() if session.provider in ("anthropic", "claude") else (None, auth_mgr.get_key(session.provider))
        has_auth = bool(key) or session.provider == "ollama"
        print(f"  Provider:    {Style.BOLD}{session.provider}{Style.RESET} ({session.model}) - {'✔ Authenticated' if has_auth else '✖ Missing Key'}\n")
        return True

    elif keyword == "/branch":
        if arg:
            res = subprocess.run(f"git checkout -b '{arg}'", shell=True, capture_output=True, text=True)
            print(res.stdout or res.stderr)
        else:
            res = subprocess.run("git branch -a", shell=True, capture_output=True, text=True)
            print(res.stdout)
        return True

    elif keyword == "/export":
        fmt = (arg or "md").lower()
        export_file = Path(f"ocita_session_{int(time.time())}.{fmt}")
        if fmt == "html":
            html_content = f"<html><body><h1>ocita Transcript</h1><pre>{json.dumps(session.messages, indent=2)}</pre></body></html>"
            export_file.write_text(html_content, encoding="utf-8")
        else:
            md_lines = [f"# ocita Session Transcript ({session.session_id})\n"]
            for m in session.messages:
                md_lines.append(f"### {m['role'].upper()}:\n{m.get('content', '')}\n")
            export_file.write_text("\n".join(md_lines), encoding="utf-8")
        print(f"{Style.GREEN}✔ Exported session transcript to {export_file.resolve()}{Style.RESET}")
        return True

    elif keyword == "/model":
        if arg:
            session.model = arg
            print(f"{Style.GREEN}✔ Switched model to: {session.model}{Style.RESET}")
        else:
            print(f"Current model: {Style.BOLD}{session.model}{Style.RESET} (Provider: {session.provider})")
        return True

    elif keyword == "/provider":
        if arg:
            session.provider = arg.lower()
            print(f"{Style.GREEN}✔ Switched provider to: {session.provider}{Style.RESET}")
        else:
            print(f"Current provider: {Style.BOLD}{session.provider}{Style.RESET}")
        return True

    elif keyword == "/diff":
        diff_out = session.executor.tool_git_diff({"staged": False})
        print(diff_out)
        return True

    elif keyword == "/undo":
        if not session.executor.last_modified_files:
            print(f"{Style.YELLOW}No files modified by ocita in this session.{Style.RESET}")
        else:
            last_file = session.executor.last_modified_files.pop()
            print(f"Reverting {last_file} via git checkout...")
            subprocess.run(f"git checkout -- '{last_file}'", shell=True)
            print(f"{Style.GREEN}✔ Restored {last_file}{Style.RESET}")
        return True

    elif keyword == "/clear":
        session.messages = []
        print(f"{Style.GREEN}✔ Conversation history cleared.{Style.RESET}")
        return True

    elif keyword == "/compact":
        if len(session.messages) > 4:
            preserved = session.messages[-4:]
            session.messages = [{"role": "system", "content": "Previous turns compacted."}] + preserved
            print(f"{Style.GREEN}✔ History compacted. Retained last 4 messages.{Style.RESET}")
        else:
            print("History is already short.")
        return True

    elif keyword in ("/cost", "/stats"):
        print(f"""
{Style.BOLD}Session Statistics:{Style.RESET}
  Provider:           {session.provider}
  Model:              {session.model}
  Prompt Tokens:      {session.total_prompt_tokens:,}
  Completion Tokens:  {session.total_completion_tokens:,}
  Total Tokens:       {session.total_prompt_tokens + session.total_completion_tokens:,}
  Tool Calls:         {session.total_tool_calls}
""")
        return True

    elif keyword == "/init":
        cur_ocita = Path.cwd() / "OCITA.md"
        if cur_ocita.exists():
            print(f"{Style.YELLOW}OCITA.md already exists at {cur_ocita}{Style.RESET}")
        else:
            template = """# Project Guidelines (OCITA.md)

## Tech Stack & Commands
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`

## Conventions
- Follow clean enterprise coding practices.
- Run tests after modifying code.
"""
            cur_ocita.write_text(template, encoding="utf-8")
            print(f"{Style.GREEN}✔ Created OCITA.md{Style.RESET}")
        return True

    elif keyword in ("/exit", "/quit"):
        print(f"{Style.DIM}Goodbye!{Style.RESET}")
        sys.exit(0)

    return False


def start_interactive_repl(session):
    print_banner()
    repo_name = Path.cwd().name
    print(f"{Style.BOLD}Working Directory:{Style.RESET} {Path.cwd()}")
    if session.instructions_file:
        print(f"{Style.DIM}Loaded instructions: {session.instructions_file}{Style.RESET}")
    print(f"{Style.DIM}Provider: {session.provider} | Model: {session.model}{Style.RESET}")
    
    # Display Hackatime status on startup
    today_time = session.tracker.get_today_stats()
    pacing_status = f"{Style.GREEN}Deliberate Pacing (with detailed code comments){Style.RESET}" if session.slow_mode else f"{Style.YELLOW}Fast Mode{Style.RESET}"
    print(f"{Style.DIM}Execution Mode: {pacing_status}{Style.RESET}")
    print(f"{Style.DIM}Hackatime Today: {Style.GREEN}{today_time}{Style.RESET}")
    print(f"{Style.DIM}Type your prompt or /help for commands. Press Ctrl+C or Ctrl+D to exit.{Style.RESET}\n")

    while True:
        try:
            prompt_str = f"{Style.BOLD}{Style.BRIGHT_CYAN}ocita:{repo_name}> {Style.RESET}"
            user_input = input(prompt_str).strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                handled = handle_slash_command(user_input, session)
                if handled:
                    continue

            session.run_turn(user_input)
            print()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Style.DIM}Exiting ocita.{Style.RESET}")
            break


# ==============================================================================
# Main Entry Point
# ==============================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="ocita enterprise core engine")
    parser.add_argument("--prompt", type=str, help="Non-interactive task prompt")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive REPL")
    parser.add_argument("--slow", action="store_true", help="Enable deliberate pacing mode with explanatory comments")
    parser.add_argument("--fast", action="store_true", help="Disable deliberate pacing mode")
    args = parser.parse_args()

    provider = os.getenv("OCITA_PROVIDER", "openrouter")
    model = os.getenv("OCITA_MODEL", "anthropic/claude-3.7-sonnet")
    auto_approve = os.getenv("OCITA_AUTO_APPROVE", "false").lower() in ("true", "1", "yes")
    max_steps = int(os.getenv("OCITA_MAX_STEPS", "25"))

    slow_mode = True
    if args.fast or os.getenv("OCITA_FAST", "false").lower() in ("true", "1", "yes"):
        slow_mode = False
    elif args.slow or os.getenv("OCITA_SLOW", "true").lower() in ("true", "1", "yes"):
        slow_mode = True

    session = AgentSession(
        provider=provider,
        model=model,
        auto_approve=auto_approve,
        max_steps=max_steps,
        slow_mode=slow_mode
    )

    if args.prompt:
        session.run_turn(args.prompt)
    else:
        start_interactive_repl(session)


if __name__ == "__main__":
    main()
