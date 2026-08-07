@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 app.py
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        python app.py
    ) else (
        echo Python n'a pas ete trouve. Installez Python puis relancez ce script.
        pause
        exit /b 1
    )
)