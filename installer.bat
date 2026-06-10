@echo off
echo Installation/Mise a jour de FFmpeg (Derniere version)...
winget install -e --id Gyan.FFmpeg --upgrade-available
if %errorlevel% neq 0 (echo Echec pour FFmpeg. & pause & exit /b)

echo Installation/Mise a jour de Python (Derniere version stable)...
winget install -e --id Python.Python --upgrade-available
if %errorlevel% neq 0 (echo Echec pour Python. & pause & exit /b)

echo Rechargement dynamique du PATH...
for /f "tokens=2*" %%a in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "syspath=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "userpath=%%b"
set "PATH=%syspath%;%userpath%"

echo Mise a jour de pip...
python -m pip install --upgrade pip

echo Installation des dependances Python...
pip install --upgrade -r requirements.txt
if %errorlevel% neq 0 (echo Echec de l'installation des packages pip. & pause & exit /b)

echo Tous les packages sont a jour !
pause

