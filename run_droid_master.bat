@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
title DroidMaster Pro Launcher

echo =====================================================================
echo                 ⚡ DroidMaster Pro v2.9.0 Launcher
echo =====================================================================

set "PYTHON_EXE="

:: 1. Check if 'python' is accessible in system PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :RUN_APP
)

:: 2. Search standard user AppData Python installations
if exist "%LOCALAPPDATA%\Programs\Python" (
    for /f "delims=" %%D in ('dir /b /ad /o-n "%LOCALAPPDATA%\Programs\Python\Python*" 2^>nul') do (
        if exist "%LOCALAPPDATA%\Programs\Python\%%D\python.exe" (
            set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\%%D\python.exe"
            goto :RUN_APP
        )
    )
)

:: 3. Check system Program Files Python installations
if exist "%ProgramFiles%\Python3*" (
    for /f "delims=" %%D in ('dir /b /ad /o-n "%ProgramFiles%\Python3*" 2^>nul') do (
        if exist "%ProgramFiles%\%%D\python.exe" (
            set "PYTHON_EXE=%ProgramFiles%\%%D\python.exe"
            goto :RUN_APP
        )
    )
)

:: Python not found
echo [ERROR] Python not found in system PATH or standard installation directories.
echo Please ensure Python 3.9+ is installed and added to PATH.
echo Download Python: https://www.python.org/downloads/
echo.
pause
exit /b 1

:RUN_APP
echo [INFO] Found Python: !PYTHON_EXE!
echo [INFO] Starting DroidMaster Pro from "%~dp0"...
echo.

"!PYTHON_EXE!" "%~dp0main.py"
if %errorlevel% neq 0 (
    echo.
    echo =====================================================================
    echo [ERROR] DroidMaster Pro encountered an error and closed (Exit Code: %errorlevel%).
    echo See error details above.
    echo =====================================================================
    pause
    exit /b %errorlevel%
)

exit /b 0
