@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "CORE_PY=%PROJECT_ROOT%\lib\ocita_core.py"

REM Find Python executable
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=python"
    goto :RUN
)

where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PYTHON_EXE=py"
    goto :RUN
)

echo [Error] Python 3 is required by ocita. Please ensure Python is installed and in your PATH.
exit /b 1

:RUN
REM If arguments exist, pass them
if "%~1"=="" (
    "%PYTHON_EXE%" "%CORE_PY%" --interactive
) else (
    REM Check for help or version
    if "%~1"=="-h" goto :HELP
    if "%~1"=="--help" goto :HELP
    if "%~1"=="-v" goto :VERSION
    if "%~1"=="--version" goto :VERSION
    
    "%PYTHON_EXE%" "%CORE_PY%" --prompt "%*"
)
exit /b %ERRORLEVEL%

:HELP
"%PYTHON_EXE%" -c "import sys, os; sys.path.insert(0, r'%PROJECT_ROOT%\lib'); import ocita_core; print_banner(); print('Run ocita in PowerShell with bin\\ocita.ps1 -Help or in Bash with bin/ocita --help')"
exit /b 0

:VERSION
echo ocita version 1.2.0 (Claude Code CLI Alternate for PowerShell and Bash)
echo Project Root: %PROJECT_ROOT%
exit /b 0
