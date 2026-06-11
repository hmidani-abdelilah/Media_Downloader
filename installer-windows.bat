@echo off
title Media Downloader installer 
color 0A 

:: ===== Request Admin Rights =====
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
 echo Requesting Administrator privileges...
 powershell -Command "Start-Process '%~f0' -Verb RunAs"
 exit
)

:: ===== Force le retour au dossier d'origine du script =====
cd /d "%~dp0"

winget source reset --force


echo Installation ou Mise a jour de FFmpeg...
:: Tente d'abord de mettre à jour, si échec (non installé), installe le programme
winget upgrade -e --id Gyan.FFmpeg
if %errorlevel% neq 0 (
    echo Tentative d'installation de FFmpeg...
    winget install -e --id Gyan.FFmpeg
)
if %errorlevel% neq 0 (echo Echec pour FFmpeg. & pause )

echo Installation ou Mise a jour de Python...
winget upgrade -e --id Python.Python.3.14
if %errorlevel% neq 0 (
    echo Tentative d'installation de Python...
    winget install -e --id Python.Python.3.14
)
if %errorlevel% neq 0 (echo Echec pour Python. & pause )

echo Rechargement dynamique du PATH...
for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "syspath=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "userpath=%%b"
set "PATH=%syspath%;%userpath%"

echo Mise a jour de pip...
python -m pip install --upgrade pip

echo.
echo Installation des dependances Python...
if exist "requirements.txt" (
    pip install --upgrade -r requirements.txt
) else (
    echo Erreur : Le fichier requirements.txt est introuvable dans le dossier du script.
    set ERRORLEVEL=1
)
if %errorlevel% neq 0 (echo Echec de l'installation des packages pip. & pause )


:: ===== CREATION DU RACCOURCI SUR LE BUREAU =====
echo Creation du raccourci sur le Bureau...

set "TARGET_PATH=%~dp0run-it.bat"
set "SHORTCUT_PATH=%PUBLIC%\Desktop\Media Downloader.lnk"
set "ICON_PATH=%~dp0Icon.ico"

:: Appel direct à l'exécutable PowerShell via son chemin complet en dur
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='%TARGET_PATH%';$s.WorkingDirectory='%~dp0';if(Test-Path '%ICON_PATH%'){$s.IconLocation='%ICON_PATH%'};$s.Save()"

if %errorlevel% neq 0 (
    echo Passage au bureau utilisateur alternatif...
    for /f "usebackq delims=" %%I in (`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "[Environment]::GetFolderPath('Desktop')"`) do set "USER_DESKTOP=%%I"
    C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USER_DESKTOP%\Media Downloader.lnk');$s.TargetPath='%TARGET_PATH%';$s.WorkingDirectory='%~dp0';if(Test-Path '%ICON_PATH%'){$s.IconLocation='%ICON_PATH%'};$s.Save()"
)

echo.
echo Tous les packages sont a jour !
echo Executez run-it.bat pour lancer le programme.
echo Un raccourci a ete cree sur votre Bureau.
pause
