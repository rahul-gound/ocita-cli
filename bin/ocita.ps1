<#
.SYNOPSIS
    ocita - Enterprise Claude Code CLI Alternate in PowerShell
    Version: 1.2.0
.DESCRIPTION
    Autonomous coding agent for PowerShell and Windows Terminal with Hackatime,
    multi-provider AI support (Claude.ai, Anthropic, OpenRouter, DeepSeek, Ollama),
    and enterprise software engineering standards.
#>

[CmdletBinding()]
param(
    [Alias('p')]
    [string]$Provider = 'openrouter',

    [Alias('m')]
    [string]$Model = 'anthropic/claude-3.7-sonnet',

    [Alias('y', 'dangerously-skip-permissions')]
    [switch]$Yes,

    [Alias('c')]
    [switch]$Continue,

    [Alias('s')]
    [string]$Session,

    [int]$MaxSteps = 25,

    [string]$System,

    [switch]$Init,

    [switch]$Slow,

    [switch]$Fast,

    [switch]$Version,

    [Alias('h')]
    [switch]$Help,

    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Prompt
)

$IsVerbose = $PSBoundParameters.ContainsKey('Verbose')

$ErrorActionPreference = 'Stop'

# Resolve root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$CorePy = Join-Path $ProjectRoot "lib\ocita_core.py"

function Show-OcitaHelp {
    Write-Host "ocita" -ForegroundColor Cyan -NoNewline
    Write-Host " - Enterprise Claude Code CLI Alternate in PowerShell (v1.2.0)" -ForegroundColor White
    Write-Host "Built-in Hackatime / WakaTime, Claude.ai Web & API Auth, Enterprise Prompting`n" -ForegroundColor DarkGray

    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  ocita [OPTIONS] [PROMPT]"
    Write-Host "  Get-Content error.log | ocita `"diagnose and fix this`""
    Write-Host "  git diff | ocita `"review these changes`"`n"

    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  -p, -Provider <name>    AI provider (gemini, chatgpt, anthropic, openrouter, deepseek, ollama, groq)"
    Write-Host "  -m, -Model <name>       Model name (e.g. gemini-2.0-flash, chatgpt-4o-latest, gpt-4o, claude-3-7-sonnet)"
    Write-Host "  -Slow                   Work slowly and deliberately with comprehensive explanatory code comments (default)"
    Write-Host "  -Fast                   Disable deliberate pacing mode"
    Write-Host "  -y, -Yes                Automatically approve tool execution (non-interactive mode)"
    Write-Host "  -c, -Continue           Continue recent session in this directory"
    Write-Host "  -s, -Session <id>       Resume specific session ID"
    Write-Host "  -MaxSteps <num>         Maximum reasoning steps per turn (default: 25)"
    Write-Host "  -System <prompt>        Override custom system instructions"
    Write-Host "  -Init                   Create an OCITA.md template in current directory"
    Write-Host "  -v, -Verbose            Show debug logs & API payloads"
    Write-Host "  -Version                Show version information"
    Write-Host "  -h, -Help               Show this help message`n"

    Write-Host "AUTHENTICATION & LOGINS:" -ForegroundColor Yellow
    Write-Host "  gemini       `$env:GEMINI_API_KEY, `$env:GEMINI_COOKIE (Google Gemini: API Key, __Secure-1PSID cookie, or credits)"
    Write-Host "  chatgpt      `$env:OPENAI_API_KEY    (OpenAI ChatGPT: chatgpt-4o-latest, gpt-4o, o3-mini)"
    Write-Host "  claude.ai    /login claude        (Login via Claude.ai sessionKey cookie or Anthropic API Key)"
    Write-Host "  anthropic    `$env:ANTHROPIC_API_KEY (Direct Anthropic API key)"
    Write-Host "  openrouter   `$env:OPENROUTER_API_KEY(Claude 3.7, DeepSeek R1, GPT-4o, etc.)"
    Write-Host "  deepseek     `$env:DEEPSEEK_API_KEY  (Direct DeepSeek API key)"
    Write-Host "  ollama       (None required)      (Local models via http://localhost:11434)"
    Write-Host "  groq         `$env:GROQ_API_KEY      (Groq high-speed inference)`n"

    Write-Host "INTERACTIVE REPL COMMANDS:" -ForegroundColor Yellow
    Write-Host "  /help              Show available REPL commands"
    Write-Host "  /argon             Switch immediately to Google Gemini 4 Argon (Frontier Reasoning & Coding)"
    Write-Host "  /gemini [model]    Switch provider to Google Gemini (default: gemini-4-argon)"
    Write-Host "  /chatgpt [model]   Switch provider to ChatGPT (default: chatgpt-4o-latest)"
    Write-Host "  /claude [model]    Switch provider to Claude (default: claude-3-7-sonnet)"
    Write-Host "  /models            List recommended frontier models"
    Write-Host "  /cookie [val]      Inspect or set Gemini web cookie (__Secure-1PSID)"
    Write-Host "  /slow [on|off]     Toggle deliberate step pacing & detailed comments"
    Write-Host "  /time, /hackatime  View today's Hackatime / WakaTime stats"
    Write-Host "  /login             Authenticate with Gemini (key/cookie/credits), Claude.ai, ChatGPT"
    Write-Host "  /auth              Display connected providers"
    Write-Host "  /review            Architectural & security code review on diff"
    Write-Host "  /commit            Autonomous conventional git commit"
    Write-Host "  /test              Auto-detect and run project test suite"
    Write-Host "  /lint              Auto-detect and run project linter"
    Write-Host "  /doctor            Diagnose system, tools, Hackatime & API health"
    Write-Host "  /model, /provider  Switch model or provider"
    Write-Host "  /diff, /undo       Inspect diff or undo last change"
    Write-Host "  /exit, /quit       Exit ocita`n"
}

if ($Help) {
    Show-OcitaHelp
    exit 0
}

if ($Version) {
    Write-Host "ocita version 1.2.0 (Claude Code CLI Alternate for PowerShell and Bash)" -ForegroundColor Cyan
    Write-Host "Project Root: $ProjectRoot"
    exit 0
}

# Handle -Init
if ($Init) {
    $TargetFile = Join-Path (Get-Location) "OCITA.md"
    if (Test-Path $TargetFile) {
        Write-Warning "OCITA.md already exists at $TargetFile"
    } else {
        $Template = @"
# Project Guidelines (OCITA.md)

## Tech Stack & Commands
- Build: ``npm run build``
- Test: ``npm test``
- Lint: ``npm run lint``

## Conventions
- Follow clean enterprise coding practices.
- Run tests after modifying code.
"@
        Set-Content -Path $TargetFile -Value $Template -Encoding UTF8
        Write-Host "✔ Created OCITA.md in $(Get-Location)" -ForegroundColor Green
    }
    exit 0
}

# Find Python interpreter
$PythonCmd = $null
foreach ($cmd in @('python', 'python3', 'py')) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $PythonCmd = $cmd
        break
    }
}

if (-not $PythonCmd) {
    Write-Error "Python 3 is required by ocita for API & JSON processing. Please ensure Python is installed and in your PATH."
    exit 1
}

# Capture pipeline / redirected input safely
$PipedInput = ""
try {
    if ([Console]::IsInputRedirected) {
        $PipedInput = [Console]::In.ReadToEnd().Trim()
    }
} catch {
    # Non-fatal if stdin cannot be probed
}

# Format prompt
$PromptText = if ($Prompt) { $Prompt -join ' ' } else { '' }
if ($PipedInput) {
    if ($PromptText) {
        $PromptText = "$PromptText`n`n``````input`n$PipedInput`n``````"
    } else {
        $PromptText = "Here is the input from standard input:`n`n``````input`n$PipedInput`n``````"
    }
}

# Set Environment Variables for Engine
$env:OCITA_DIR = $ProjectRoot
$env:OCITA_LIB = Join-Path $ProjectRoot "lib"
$env:OCITA_CONFIG_DIR = if ($env:XDG_CONFIG_HOME) { Join-Path $env:XDG_CONFIG_HOME "ocita" } else { Join-Path $HOME ".config\ocita" }
$env:OCITA_DATA_DIR = if ($env:XDG_DATA_HOME) { Join-Path $env:XDG_DATA_HOME "ocita" } else { Join-Path $HOME ".local\share\ocita" }
$env:OCITA_SESSIONS_DIR = Join-Path $env:OCITA_DATA_DIR "sessions"
$env:OCITA_PROVIDER = $Provider
$env:OCITA_MODEL = $Model
$env:OCITA_AUTO_APPROVE = if ($Yes) { "true" } else { "false" }
$env:OCITA_MAX_STEPS = $MaxSteps
$env:OCITA_SLOW = if ($Fast) { "false" } else { "true" }
$env:OCITA_FAST = if ($Fast) { "true" } else { "false" }
$env:OCITA_VERBOSE = if ($IsVerbose) { "true" } else { "false" }
$env:OCITA_SYSTEM_OVERRIDE = $System
$env:OCITA_CONTINUE = if ($Continue) { "true" } else { "false" }
$env:OCITA_SESSION_ID = $Session

# Launch Core Engine
if ($PromptText) {
    & $PythonCmd "$CorePy" --prompt $PromptText
} else {
    & $PythonCmd "$CorePy" --interactive
}
