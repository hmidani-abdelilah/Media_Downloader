@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Media Downloader installer
color 0A

set "DRY_RUN=0"
if /I "%~1"=="--dry-run" set "DRY_RUN=1"

:: ===== Demande de droits administrateur =====
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Demande des droits administrateur...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ===== Determiner les repertoires =====
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

set "INSTALL_ROOT=%USERPROFILE%\Media_Downloader"
set "PROJECT_DIR=%INSTALL_ROOT%"

if exist "%SCRIPT_DIR%\app.py" if exist "%SCRIPT_DIR%\requirements.txt" (
    set "PROJECT_DIR=%SCRIPT_DIR%"
    echo Utilisation du dossier courant comme source du projet.
) else if exist "%SCRIPT_DIR%\Media_Downloader\app.py" if exist "%SCRIPT_DIR%\Media_Downloader\requirements.txt" (
    set "PROJECT_DIR=%SCRIPT_DIR%\Media_Downloader"
    echo Utilisation du sous-dossier Media_Downloader comme source du projet.
) else (
    echo Le script sera installe dans %INSTALL_ROOT%
)

if /I "%DRY_RUN%"=="1" (
    echo Mode de test actif : aucune installation ne sera lancee.
    echo Dossier cible : %PROJECT_DIR%
    exit /b 0
)

:: ===== Etape 1 : installation de FFmpeg =====
set "WINGET_FLAGS=--accept-source-agreements --accept-package-agreements --disable-interactivity"
echo [1/6] Installation ou mise a jour de FFmpeg...
call :InstallWingetPackage "FFmpeg" "Gyan.FFmpeg"

:: ===== Etape 2 : installation de Python =====
echo [2/6] Installation ou mise a jour de Python...
call :InstallWingetPackage "Python" "Python.Python.3"

:: ===== Etape 3 : installation de Git =====
echo [3/6] Installation ou mise a jour de Git...
call :InstallWingetPackage "Git" "Git.Git"

:: ===== Recharger PATH =====
echo [4/6] Rechargement du PATH...
for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "syspath=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "userpath=%%b"
set "PATH=%syspath%;%userpath%"

:: ===== Etape 4 : telechargement du depot =====
if exist "%PROJECT_DIR%\app.py" (
    echo [4/6] Le projet existe deja. Utilisation du dossier actuel.
) else (
    echo [4/6] Telechargement du depot GitHub...
    if not exist "%INSTALL_ROOT%" mkdir "%INSTALL_ROOT%"
    cd /d "%INSTALL_ROOT%"
    git clone https://github.com/hmidani-abdelilah/Media_Downloader.git "%INSTALL_ROOT%"
    if %ERRORLEVEL% NEQ 0 (
        echo Echec du clonage du repository GitHub.
        pause
        exit /b 1
    )
    set "PROJECT_DIR=%INSTALL_ROOT%"
)

:: ===== Etape 5 : installation des dependances =====
echo [5/6] Entree dans le dossier du projet...
cd /d "%PROJECT_DIR%"

set "REQ_FILE="
if exist "%PROJECT_DIR%\requirements.txt" (
    set "REQ_FILE=%PROJECT_DIR%\requirements.txt"
) else if exist "%PROJECT_DIR%\requirements windows11.txt" (
    set "REQ_FILE=%PROJECT_DIR%\requirements windows11.txt"
)

if not defined REQ_FILE (
    echo Aucun fichier requirements.txt n'a ete trouve dans le projet.
    pause
    exit /b 1
)

echo [5/6] Installation des dependances Python...
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 -m pip install --upgrade pip
    py -3 -m pip install --upgrade -r "%REQ_FILE%"
) else (
    python -m pip install --upgrade pip
    python -m pip install --upgrade -r "%REQ_FILE%"
)

if %ERRORLEVEL% NEQ 0 (
    echo Echec de l'installation des dependances Python.
    pause
    exit /b 1
)

:: ===== Etape 6 : creation du raccourci bureau =====
echo [6/6] Creation du raccourci sur le Bureau...
set "TARGET_PATH=%PROJECT_DIR%\run-it.bat"
set "SHORTCUT_PATH=%PUBLIC%\Desktop\Media Downloader.lnk"
set "ICON_PATH=%PROJECT_DIR%\asset\Icon.ico"
if not exist "%ICON_PATH%" set "ICON_PATH=%PROJECT_DIR%\Icon.ico"

set "USER_DESKTOP=%PUBLIC%\Desktop"
if not exist "%USER_DESKTOP%" (
    for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "USER_DESKTOP=%%B"
)
if not exist "%USER_DESKTOP%" set "USER_DESKTOP=%USERPROFILE%\Desktop"

set "WSCRIPT_EXE="
if exist "%SystemRoot%\System32\wscript.exe" set "WSCRIPT_EXE=%SystemRoot%\System32\wscript.exe"
if not defined WSCRIPT_EXE if exist "%SystemRoot%\SysWOW64\wscript.exe" set "WSCRIPT_EXE=%SystemRoot%\SysWOW64\wscript.exe"
if not defined WSCRIPT_EXE if exist "%windir%\System32\wscript.exe" set "WSCRIPT_EXE=%windir%\System32\wscript.exe"
if not defined WSCRIPT_EXE if exist "%windir%\SysWOW64\wscript.exe" set "WSCRIPT_EXE=%windir%\SysWOW64\wscript.exe"

if defined WSCRIPT_EXE (
    > "%TEMP%\create_shortcut.vbs" ( 
        echo Set oWS = WScript.CreateObject("WScript.Shell")
        echo Set oLink = oWS.CreateShortcut("%SHORTCUT_PATH%")
        echo oLink.TargetPath = "%TARGET_PATH%"
        echo oLink.WorkingDirectory = "%PROJECT_DIR%"
        echo oLink.IconLocation = "%ICON_PATH%"
        echo oLink.Save
    )
    "%WSCRIPT_EXE%" "%TEMP%\create_shortcut.vbs" >nul 2>&1

    if not exist "%SHORTCUT_PATH%" (
        > "%TEMP%\create_shortcut_user.vbs" ( 
            echo Set oWS = WScript.CreateObject("WScript.Shell")
            echo Set oLink = oWS.CreateShortcut("%USER_DESKTOP%\Media Downloader.lnk")
            echo oLink.TargetPath = "%TARGET_PATH%"
            echo oLink.WorkingDirectory = "%PROJECT_DIR%"
            echo oLink.IconLocation = "%ICON_PATH%"
            echo oLink.Save
        )
        "%WSCRIPT_EXE%" "%TEMP%\create_shortcut_user.vbs" >nul 2>&1
    )
) else (
    echo wscript.exe est introuvable. Le raccourci ne peut pas etre cree automatiquement.
)

if exist "%SHORTCUT_PATH%" (
    echo Raccourci cree avec succes.
) else if exist "%USER_DESKTOP%\Media Downloader.lnk" (
    echo Raccourci cree sur le bureau utilisateur.
) else (
    echo Impossible de creer le raccourci automatiquement. Vous pouvez le creer manuellement.
)

echo.
echo Installation terminee avec succes !
echo Le programme a ete installe dans : %PROJECT_DIR%
echo Un raccourci a ete cree sur votre Bureau.
pause
exit /b 0

:InstallWingetPackage
set "PKG_NAME=%~1"
set "PKG_ID=%~2"

where winget >nul 2>nul
if errorlevel 1 (
    echo Avertissement : winget est introuvable. %PKG_NAME% ne sera pas installe automatiquement.
    exit /b 1
)

winget upgrade -e --id %PKG_ID% %WINGET_FLAGS%
if not errorlevel 1 (
    echo %PKG_NAME% est deja present ou mis a jour.
    exit /b 0
)

echo Tentative d'installation de %PKG_NAME%...
winget install -e --id %PKG_ID% %WINGET_FLAGS%
if not errorlevel 1 (
    echo %PKG_NAME% est installe avec succes.
    exit /b 0
)

echo Avertissement : impossible d'installer ou mettre a jour %PKG_NAME%. La suite de l'installation va continuer.
exit /b 1
