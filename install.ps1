# ==============================================================================
# ocita - PowerShell Installer for Windows
# ==============================================================================

[CmdletBinding()]
param()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BinDir = Join-Path $ScriptDir "bin"

Write-Host "Installing ocita for PowerShell & Windows..." -ForegroundColor Cyan

# Check Python
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    Write-Warning "Python was not detected in PATH. Please install Python 3.8+ to use ocita."
} else {
    Write-Host "✔ Detected Python: $($PythonCmd.Source)" -ForegroundColor Green
}

# Determine User Bin directory in PATH
$UserBin = Join-Path $HOME "bin"
if (-not (Test-Path $UserBin)) {
    New-Item -ItemType Directory -Path $UserBin -Force | Out-Null
}

# Copy or create wrappers
Copy-Item (Join-Path $BinDir "ocita.cmd") (Join-Path $UserBin "ocita.cmd") -Force
Copy-Item (Join-Path $BinDir "ocita.ps1") (Join-Path $UserBin "ocita.ps1") -Force

Write-Host "✔ Installed ocita wrappers to $UserBin" -ForegroundColor Green

# Check if UserBin is in PATH
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$UserBin*") {
    Write-Host "`nAdding $UserBin to your User PATH environment variable..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$UserBin", "User")
    $env:PATH = "$env:PATH;$UserBin"
    Write-Host "✔ Added $UserBin to PATH!" -ForegroundColor Green
}

Write-Host "`n✔ ocita installation complete!" -ForegroundColor Green
Write-Host "You can now run 'ocita' directly from PowerShell, CMD, or Windows Terminal!`n"
Write-Host "Quick Start in PowerShell:"
Write-Host "  ocita                  # Launch interactive REPL"
Write-Host "  ocita /login claude    # Log in with Claude.ai or Anthropic key"
Write-Host "  ocita /time            # Check Hackatime status"
