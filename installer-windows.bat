@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Media Downloader installer
color 0A

:: ===== Demande de droits administrateur =====
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Demande des droits administrateur...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ===== Déterminer le dossier du projet =====
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

if exist "%SCRIPT_DIR%\app.py" if exist "%SCRIPT_DIR%\requirements.txt" (
    set "PROJECT_DIR=%SCRIPT_DIR%"
) else (
    set "PROJECT_DIR=%SCRIPT_DIR%\Media_Downloader"
)

cd /d "%SCRIPT_DIR%"

winget source reset --force

echo Installation ou mise a jour de FFmpeg...
winget upgrade -e --id Gyan.FFmpeg
if %ERRORLEVEL% NEQ 0 (
    echo Tentative d'installation de FFmpeg...
    winget install -e --id Gyan.FFmpeg
)
if %ERRORLEVEL% NEQ 0 (
    echo Echec pour FFmpeg.
    pause
    exit /b 1
)

echo Installation ou mise a jour de Python...
winget upgrade -e --id Python.Python.3
if %ERRORLEVEL% NEQ 0 (
    echo Tentative d'installation de Python...
    winget install -e --id Python.Python.3
)
if %ERRORLEVEL% NEQ 0 (
    echo Echec pour Python.
    pause
    exit /b 1
)

echo Installation ou mise a jour de git...
winget upgrade -e --id Git.Git
if %ERRORLEVEL% NEQ 0 (
    echo Tentative d'installation de git...
    winget install -e --id Git.Git
)
if %ERRORLEVEL% NEQ 0 (
    echo Echec pour git.
    pause
    exit /b 1
)

echo Rechargement dynamique du PATH...
for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "syspath=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "userpath=%%b"
set "PATH=%syspath%;%userpath%"

if exist "%PROJECT_DIR%\app.py" (
    echo Le projet existe deja. Utilisation du dossier actuel.
) else (
    echo Clonage du repository git...
    git clone https://github.com/hmidani-abdelilah/Media_Downloader.git "%PROJECT_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo Echec du clonage du repository git.
        pause
        exit /b 1
    )
)

echo Entree dans le dossier du projet...
cd /d "%PROJECT_DIR%"

echo Mise a jour de pip...
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m pip install --upgrade pip
) else (
    python -m pip install --upgrade pip
)

if %ERRORLEVEL% NEQ 0 (
    echo Echec de la mise a jour de pip.
    pause
    exit /b 1
)

echo Installation des dependances Python...
if exist "requirements.txt" (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        py -3 -m pip install --upgrade -r requirements.txt
    ) else (
        python -m pip install --upgrade -r requirements.txt
    )
) else (
    echo Erreur : Le fichier requirements.txt est introuvable dans le dossier du script.
    pause
    exit /b 1
)
if %ERRORLEVEL% NEQ 0 (
    echo Echec de l'installation des packages pip.
    pause
    exit /b 1
)

:: ===== CREATION DU RACCOURCI SUR LE BUREAU =====
echo Creation du raccourci sur le Bureau...

set "TARGET_PATH=%PROJECT_DIR%\run-it.bat"
set "SHORTCUT_PATH=%PUBLIC%\Desktop\Media Downloader.lnk"
set "ICON_PATH=%PROJECT_DIR%\asset\Icon.ico"
if not exist "%ICON_PATH%" set "ICON_PATH=%PROJECT_DIR%\Icon.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='%TARGET_PATH%';$s.WorkingDirectory='%PROJECT_DIR%';if(Test-Path '%ICON_PATH%'){$s.IconLocation='%ICON_PATH%'};$s.Save()"

if %ERRORLEVEL% NEQ 0 (
    echo Passage au bureau utilisateur alternatif...
    for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "[Environment]::GetFolderPath('Desktop')"`) do set "USER_DESKTOP=%%I"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USER_DESKTOP%\Media Downloader.lnk');$s.TargetPath='%TARGET_PATH%';$s.WorkingDirectory='%PROJECT_DIR%';if(Test-Path '%ICON_PATH%'){$s.IconLocation='%ICON_PATH%'};$s.Save()"
)

echo.
echo Installation terminee avec succes !
echo Executez run-it.bat pour lancer le programme.
echo Un raccourci a ete cree sur votre Bureau.
pause
