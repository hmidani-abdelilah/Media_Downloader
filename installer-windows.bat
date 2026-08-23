@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ERRORLEVEL="
title Media Downloader - Windows setup
color 0A

set "DRY_RUN=0"
set "NO_LAUNCH=0"
set "NO_PAUSE=0"
set "REPAIR_MODE=0"
set "IN_PLACE_MODE=0"
set "ERROR_MESSAGE="
set "CURRENT_STEP=Starting setup"

:ParseArguments
if "%~1"=="" goto ArgumentsParsed
if /I "%~1"=="--dry-run" set "DRY_RUN=1"
if /I "%~1"=="--no-launch" set "NO_LAUNCH=1"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
if /I "%~1"=="--repair" set "REPAIR_MODE=1"
if /I "%~1"=="--in-place" set "IN_PLACE_MODE=1"
shift
goto ParseArguments

:ArgumentsParsed
for %%I in ("%~dp0.") do set "SCRIPT_DIR=%%~fI"
set "POWERSHELL_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%POWERSHELL_EXE%" set "POWERSHELL_EXE=powershell.exe"
set "ORIGINAL_PATH=%PATH%"
set "WINDOWS_ARCH=%PROCESSOR_ARCHITECTURE%"
if defined PROCESSOR_ARCHITEW6432 set "WINDOWS_ARCH=%PROCESSOR_ARCHITEW6432%"
set "PYTHON_ARM_X64_DIR="
if defined LOCALAPPDATA set "PYTHON_ARM_X64_DIR=%LOCALAPPDATA%\Programs\Media_Downloader\Python312-x64"
if not defined PYTHON_ARM_X64_DIR if defined USERPROFILE set "PYTHON_ARM_X64_DIR=%USERPROFILE%\AppData\Local\Programs\Media_Downloader\Python312-x64"
set "WINGET_EXE="
set "SHORTCUT_CREATED=0"
set "JS_RUNTIME_OK=0"
set "ARIA2_OK=0"
set "PROJECT_REFRESH_SOURCE=0"
set "PROJECT_REPAIR_BACKUP="

call :ResolveProjectDirectory
if not defined PROJECT_DIR goto InstallationFailed
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if "%DRY_RUN%"=="1" goto DryRun

echo.
echo ============================================================
echo              Media Downloader - Windows setup
echo ============================================================
echo This setup installs everything for the current Windows user.
echo Administrator rights are not required.
echo Project: "%PROJECT_DIR%"
echo.

set "PROJECT_EXISTED=0"
if exist "%PROJECT_DIR%\app.py" set "PROJECT_EXISTED=1"
if "%REPAIR_MODE%"=="1" goto ProjectAvailable
if "%PROJECT_EXISTED%"=="1" goto ProjectAvailable
set "CURRENT_STEP=Downloading the project"
echo [1/8] Downloading Media Downloader...
if not "%IN_PLACE_MODE%"=="1" set "PROJECT_REFRESH_SOURCE=1"
call :DownloadProject
set "INITIAL_DOWNLOAD_EXIT=%ERRORLEVEL%"
set "PROJECT_REFRESH_SOURCE=0"
if not "%INITIAL_DOWNLOAD_EXIT%"=="0" goto InstallationFailed

:ProjectAvailable
call :SyncInstaller
if errorlevel 1 goto InstallationFailed
if "%REPAIR_MODE%"=="1" goto RefreshExistingProject
if "%PROJECT_EXISTED%"=="1" if not "%IN_PLACE_MODE%"=="1" goto UpdateExistingProject
goto ProjectSourceReady

:RefreshExistingProject
set "CURRENT_STEP=Refreshing the application files"
echo       Repair mode: refreshing application files from one source revision...
call :RefreshProjectSource
if errorlevel 1 goto InstallationFailed
goto ProjectSourceReady

:UpdateExistingProject
set "CURRENT_STEP=Updating the application files"
echo [1/8] Updating Media Downloader from GitHub...
call :RefreshProjectSource
if errorlevel 1 goto InstallationFailed

:ProjectSourceReady
call :EnsureProjectFiles
if errorlevel 1 goto InstallationFailed

set "CURRENT_STEP=Finding Python"
echo [2/8] Checking Python 3.10 or newer...
call :FindPython
if defined BASE_PYTHON goto PythonAvailable
call :InstallPython
if errorlevel 1 goto InstallationFailed
call :FindPython
if not defined BASE_PYTHON set "ERROR_MESSAGE=Python 3.10 or newer could not be installed or found."
if not defined BASE_PYTHON goto InstallationFailed

:PythonAvailable
for /f "delims=" %%V in ('"%BASE_PYTHON%" --version 2^>^&1') do set "PYTHON_VERSION=%%V"
echo       Using %PYTHON_VERSION%

set "CURRENT_STEP=Creating the private Python environment"
echo [3/8] Preparing the private Python environment...
call :EnsureVirtualEnvironment
if errorlevel 1 goto InstallationFailed

set "CURRENT_STEP=Installing Python packages"
echo [4/8] Installing application packages...
echo       This can take several minutes on the first run.
call :InstallPythonDependencies
if errorlevel 1 goto InstallationFailed

set "PATH=%VENV_DIR%\Scripts;%PATH%"

set "CURRENT_STEP=Installing a JavaScript runtime"
echo [5/8] Checking the JavaScript runtime used by yt-dlp...
call :EnsureJavaScriptRuntime

set "CURRENT_STEP=Checking Aria2"
echo [6/8] Checking the optional Aria2 downloader...
call :EnsureAria2

set "CURRENT_STEP=Installing FFmpeg"
echo [7/8] Checking FFmpeg and ffprobe...
call :EnsureFFmpeg
if errorlevel 1 goto InstallationFailed

set "CURRENT_STEP=Validating the installation"
echo [8/8] Validating packages and creating shortcuts...
call :ValidatePythonDependencies
if errorlevel 1 goto InstallationFailed
call :CreateShortcuts
if not errorlevel 1 goto ShortcutsReady
if "%REPAIR_MODE%"=="1" goto ShortcutRepairContinues
goto InstallationFailed

:ShortcutRepairContinues
echo       Repair completed; the existing shortcut was left unchanged.
set "ERROR_MESSAGE="

:ShortcutsReady

echo.
echo ============================================================
echo Installation completed successfully.
echo Project: "%PROJECT_DIR%"
echo Python environment: "%VENV_DIR%"
if "%JS_RUNTIME_OK%"=="1" echo JavaScript runtime: "%JS_RUNTIME_NAME%"
if not "%JS_RUNTIME_OK%"=="1" echo JavaScript runtime: not available - YouTube may expose fewer formats.
if "%ARIA2_OK%"=="1" echo Aria2: available
if not "%ARIA2_OK%"=="1" echo Aria2: optional component not available
if "%SHORTCUT_CREATED%"=="1" echo Desktop shortcut: created with the application icon
if not "%SHORTCUT_CREATED%"=="1" echo Desktop shortcut: unchanged or unavailable; use run-it.bat if needed
echo ============================================================
echo.

if "%NO_LAUNCH%"=="1" goto InstallationSucceeded
echo Starting Media Downloader...
start "" /min "%PROJECT_DIR%\run-it.bat"

:InstallationSucceeded
endlocal
exit /b 0

:DryRun
echo Media Downloader setup dry run
echo No files, packages, shortcuts, or system settings will be changed.
echo Script directory: "%SCRIPT_DIR%"
if defined SOURCE_PROJECT_DIR echo Local source detected: "%SOURCE_PROJECT_DIR%"
echo Project directory: "%PROJECT_DIR%"
echo Virtual environment: "%PROJECT_DIR%\.venv"
if "%IN_PLACE_MODE%"=="1" echo Installation mode: in-place
if not "%IN_PLACE_MODE%"=="1" echo Installation mode: per-user ^(stable LocalAppData folder^)
if exist "%PROJECT_DIR%\app.py" echo Project source: existing installation
if not exist "%PROJECT_DIR%\app.py" echo Project source: GitHub download required
exit /b 0

:InstallationFailed
echo.
echo ============================================================
echo SETUP FAILED
echo Step: %CURRENT_STEP%
if defined ERROR_MESSAGE echo Reason: "%ERROR_MESSAGE%"
echo.
echo Fix the reported problem, then run installer-windows.bat again.
echo Project: "%PROJECT_DIR%"
echo ============================================================
if "%NO_PAUSE%"=="1" goto InstallationFailedNoPause
pause

:InstallationFailedNoPause
endlocal
exit /b 1


:: -----------------------------------------------------------------
:: Project discovery and download
:: -----------------------------------------------------------------
:ResolveProjectDirectory
set "SOURCE_PROJECT_DIR="
set "PROJECT_DIR="
if exist "%SCRIPT_DIR%\app.py" if exist "%SCRIPT_DIR%\requirements.txt" set "SOURCE_PROJECT_DIR=%SCRIPT_DIR%"
if not defined SOURCE_PROJECT_DIR if exist "%SCRIPT_DIR%\Media_Downloader\app.py" if exist "%SCRIPT_DIR%\Media_Downloader\requirements.txt" set "SOURCE_PROJECT_DIR=%SCRIPT_DIR%\Media_Downloader"
if defined LOCALAPPDATA set "INSTALL_ROOT=%LOCALAPPDATA%\Programs\Media_Downloader"
if not defined INSTALL_ROOT if defined USERPROFILE set "INSTALL_ROOT=%USERPROFILE%\Media_Downloader"
if not defined INSTALL_ROOT set "INSTALL_ROOT=%SCRIPT_DIR%\Media_Downloader"
set "PROJECT_DIR=%INSTALL_ROOT%"
if not "%IN_PLACE_MODE%"=="1" exit /b 0
if defined SOURCE_PROJECT_DIR set "PROJECT_DIR=%SOURCE_PROJECT_DIR%"
if not defined SOURCE_PROJECT_DIR set "PROJECT_DIR=%SCRIPT_DIR%"
exit /b 0

:DownloadProject
call :CheckPowerShell
if errorlevel 1 exit /b 1
set "PROJECT_REPOSITORY=hmidani-abdelilah/Media_Downloader"
set "PROJECT_DOWNLOAD_TARGET=%PROJECT_DIR%"
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; $headers=@{ 'User-Agent'='Media-Downloader-Installer' }; $commit=(Invoke-RestMethod -Headers $headers -Uri ('https://api.github.com/repos/' + $env:PROJECT_REPOSITORY + '/commits/main')).sha; if ([string]::IsNullOrWhiteSpace($commit)) { throw 'GitHub did not return a source revision.' }; $base='https://raw.githubusercontent.com/' + $env:PROJECT_REPOSITORY + '/' + $commit + '/'; $files=@('app.py','gui.py','downloader.py','convert.py','utils.py','path_ffmpeg.py','ffmpeg_check.py','aria2_check.py','notification.py','requirements.txt','languages/ar.json','languages/en.json','languages/fr.json','asset/Icon.ico','asset/Icon.png'); $stage=Join-Path $env:TEMP ('MediaDownloader-source-' + [guid]::NewGuid().ToString('N')); try { New-Item -ItemType Directory -Force -Path $stage | Out-Null; foreach ($relative in $files) { $staged=Join-Path $stage ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar)); New-Item -ItemType Directory -Force -Path (Split-Path -Parent $staged) | Out-Null; Invoke-WebRequest -UseBasicParsing -Headers $headers -Uri ($base + $relative) -OutFile $staged; if ((Get-Item -LiteralPath $staged).Length -eq 0) { throw ('GitHub returned an empty file: ' + $relative) } }; New-Item -ItemType Directory -Force -Path $env:PROJECT_DOWNLOAD_TARGET | Out-Null; $refreshSource=($env:PROJECT_REFRESH_SOURCE -eq '1'); foreach ($relative in $files) { $destination=Join-Path $env:PROJECT_DOWNLOAD_TARGET ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar)); if ((Test-Path -LiteralPath $destination) -and -not $refreshSource) { continue }; $parent=Split-Path -Parent $destination; New-Item -ItemType Directory -Force -Path $parent | Out-Null; if ($refreshSource -and (Test-Path -LiteralPath $destination) -and -not [string]::IsNullOrWhiteSpace($env:PROJECT_REPAIR_BACKUP)) { $backup=Join-Path $env:PROJECT_REPAIR_BACKUP ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar)); New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null; Copy-Item -LiteralPath $destination -Destination $backup -Force }; Copy-Item -LiteralPath (Join-Path $stage ($relative.Replace('/', [IO.Path]::DirectorySeparatorChar))) -Destination $destination -Force }; [IO.File]::WriteAllText((Join-Path $env:PROJECT_DOWNLOAD_TARGET '.source-commit'), $commit, [Text.Encoding]::ASCII) } finally { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }"
set "DOWNLOAD_EXIT=%ERRORLEVEL%"
if not "%DOWNLOAD_EXIT%"=="0" set "ERROR_MESSAGE=The project download failed. Check the Internet connection and try again."
if not "%DOWNLOAD_EXIT%"=="0" exit /b 1
if not exist "%PROJECT_DIR%\app.py" set "ERROR_MESSAGE=The project was downloaded, but app.py was not found."
if not exist "%PROJECT_DIR%\app.py" exit /b 1
exit /b 0

:SyncInstaller
if not exist "%PROJECT_DIR%\." mkdir "%PROJECT_DIR%" >nul 2>&1
if not exist "%PROJECT_DIR%\." set "ERROR_MESSAGE=The application installation folder could not be created."
if not exist "%PROJECT_DIR%\." exit /b 1
for %%I in ("%PROJECT_DIR%\installer-windows.bat") do set "INSTALLED_INSTALLER=%%~fI"
if /I "%~f0"=="%INSTALLED_INSTALLER%" exit /b 0
copy /y "%~f0" "%INSTALLED_INSTALLER%" >nul 2>&1
if errorlevel 1 set "ERROR_MESSAGE=installer-windows.bat could not be copied into the installed project."
if errorlevel 1 exit /b 1
fc /b "%~f0" "%INSTALLED_INSTALLER%" >nul 2>&1
if errorlevel 1 set "ERROR_MESSAGE=The installed copy of installer-windows.bat could not be verified."
if errorlevel 1 exit /b 1
exit /b 0

:EnsureProjectFiles
call :EnsureLauncher
if errorlevel 1 exit /b 1
call :ValidateProjectFiles
if not errorlevel 1 exit /b 0
echo       The project is incomplete; downloading only the missing files...
call :DownloadProject
if errorlevel 1 exit /b 1
call :EnsureLauncher
if errorlevel 1 exit /b 1
call :ValidateProjectFiles
if not errorlevel 1 exit /b 0
set "ERROR_MESSAGE=The application files are incomplete after downloading them from GitHub."
exit /b 1

:RefreshProjectSource
set "PROJECT_REFRESH_SOURCE=1"
set "PROJECT_REPAIR_BACKUP=%PROJECT_DIR%\repair-backup-%RANDOM%-%RANDOM%"
call :DownloadProject
set "SOURCE_REFRESH_EXIT=%ERRORLEVEL%"
set "PROJECT_REFRESH_SOURCE=0"
if not "%SOURCE_REFRESH_EXIT%"=="0" set "ERROR_MESSAGE=The application files could not be refreshed. Existing files were preserved in the repair backup when possible."
if not "%SOURCE_REFRESH_EXIT%"=="0" exit /b 1
call :EnsureLauncher
if errorlevel 1 exit /b 1
echo       Previous application files were backed up in: "%PROJECT_REPAIR_BACKUP%"
exit /b 0

:EnsureLauncher
set "LAUNCHER_TARGET=%PROJECT_DIR%\run-it.bat"
set "LAUNCHER_CANDIDATE=%PROJECT_DIR%\run-it.installing-%RANDOM%-%RANDOM%.tmp"
echo       Checking the application launcher...
call :CheckPowerShell
if errorlevel 1 exit /b 1
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $p=[string][char]37; $q=[string][char]34; $gt=[string][char]62; $amp=[string][char]38; $forVar=$p+$p+'I'; $forPath=$p+'~dp0'; $forFull=$p+$p+'~fI'; $app=$p+'APP_DIR'+$p; $venv=$p+'VENV_PYTHON'+$p; $installer=$p+'INSTALLER_FILE'+$p; $path=$p+'PATH'+$p; $localApp=$p+'LOCALAPPDATA'+$p; $temp=$p+'TEMP'+$p; $log=$p+'LOG_FILE'+$p; $redirect=' '+$gt+'nul 2'+$gt+$amp+'1'; $lines=@('@echo off','setlocal EnableExtensions DisableDelayedExpansion',':: Media Downloader launcher version 2','title Media Downloader',('for '+$forVar+' in ('+$q+$forPath+'.'+$q+') do set '+$q+'APP_DIR='+$forFull+$q),('set '+$q+'VENV_PYTHON='+$app+'\.venv\Scripts\python.exe'+$q),('set '+$q+'INSTALLER_FILE='+$app+'\installer-windows.bat'+$q),('set '+$q+'LOG_FILE='+$temp+'\MediaDownloader-latest.log'+$q),('pushd '+$q+$app+$q),'if errorlevel 1 goto ProjectPathFailed',('set '+$q+'PATH='+$app+'\.venv\Scripts;'+$localApp+'\Microsoft\WinGet\Links;'+$path+$q),'set PYTHONUTF8=1','set PYTHONIOENCODING=utf-8','set PYTHONUNBUFFERED=1',('if not exist '+$q+$venv+$q+' goto Repair'),($q+$venv+$q+' -c '+$q+'import tkinter, customtkinter, tkinterdnd2, yt_dlp, PIL, CTkFileDialog, CTkMessagebox, CTkMenuBarPlus; import app'+$q+$redirect),'if errorlevel 1 goto Repair',('if not exist '+$q+$app+'\ffmpeg\bin\ffmpeg.exe'+$q+' goto CheckSystemFFmpeg'),('if not exist '+$q+$app+'\ffmpeg\bin\ffprobe.exe'+$q+' goto Repair'),($q+$app+'\ffmpeg\bin\ffmpeg.exe'+$q+' -version'+$redirect),'if errorlevel 1 goto Repair',($q+$app+'\ffmpeg\bin\ffprobe.exe'+$q+' -version'+$redirect),'if errorlevel 1 goto Repair','goto LaunchApplication',':CheckSystemFFmpeg',('where ffmpeg.exe'+$redirect),'if errorlevel 1 goto Repair',('where ffprobe.exe'+$redirect),'if errorlevel 1 goto Repair',':LaunchApplication','echo Starting Media Downloader...',($q+$venv+$q+' '+$q+$app+'\app.py'+$q+' '+$gt+$q+$log+$q+' 2'+$gt+$amp+'1'),'if errorlevel 1 goto ApplicationFailed','exit /b 0',':Repair','echo The installation needs repair. This can take several minutes...',('if not exist '+$q+$installer+$q+' goto RepairFailed'),('call '+$q+$installer+$q+' --repair --in-place --no-launch --no-pause'),'if errorlevel 1 goto RepairFailed',('start '+$q+$q+' /min '+$q+$app+'\run-it.bat'+$q),'exit /b 0',':ApplicationFailed','echo.','echo Media Downloader closed because of an error.',('echo Error details: '+$q+$log+$q),'echo Run installer-windows.bat again to repair the installation.','pause','exit /b 1',':RepairFailed','echo.','echo Automatic repair failed. Run installer-windows.bat again and review its error message.','pause','exit /b 1',':ProjectPathFailed','echo Windows could not open the Media Downloader installation folder.','pause','exit /b 1'); [IO.File]::WriteAllLines($env:LAUNCHER_CANDIDATE,$lines,(New-Object Text.UTF8Encoding($false)))"
if errorlevel 1 goto LauncherGenerationFailed
findstr /I /L /C:"Media Downloader launcher version 2" "%LAUNCHER_CANDIDATE%" >nul 2>&1
if errorlevel 1 goto LauncherGenerationFailed
if not exist "%LAUNCHER_TARGET%" goto InstallGeneratedLauncher
fc /b "%LAUNCHER_TARGET%" "%LAUNCHER_CANDIDATE%" >nul 2>&1
if not errorlevel 1 goto LauncherAlreadyValid
copy /y "%LAUNCHER_TARGET%" "%PROJECT_DIR%\run-it.before-installer.bat" >nul 2>&1
if errorlevel 1 goto LauncherBackupFailed

:InstallGeneratedLauncher
echo       Creating the application launcher...
copy /y "%LAUNCHER_CANDIDATE%" "%LAUNCHER_TARGET%" >nul 2>&1
if errorlevel 1 goto LauncherInstallFailed
fc /b "%LAUNCHER_TARGET%" "%LAUNCHER_CANDIDATE%" >nul 2>&1
if errorlevel 1 goto LauncherVerificationFailed
del /q "%LAUNCHER_CANDIDATE%" >nul 2>&1
exit /b 0

:LauncherAlreadyValid
del /q "%LAUNCHER_CANDIDATE%" >nul 2>&1
exit /b 0

:LauncherGenerationFailed
set "ERROR_MESSAGE=The canonical run-it.bat launcher could not be generated."
del /q "%LAUNCHER_CANDIDATE%" >nul 2>&1
exit /b 1

:LauncherBackupFailed
set "ERROR_MESSAGE=The existing run-it.bat could not be backed up before replacement."
del /q "%LAUNCHER_CANDIDATE%" >nul 2>&1
exit /b 1

:LauncherInstallFailed
set "ERROR_MESSAGE=run-it.bat could not be installed."
del /q "%LAUNCHER_CANDIDATE%" >nul 2>&1
exit /b 1

:LauncherVerificationFailed
set "ERROR_MESSAGE=run-it.bat was installed but could not be verified."
del /q "%LAUNCHER_CANDIDATE%" >nul 2>&1
exit /b 1

:ValidateProjectFiles
if not exist "%PROJECT_DIR%\app.py" exit /b 1
if not exist "%PROJECT_DIR%\gui.py" exit /b 1
if not exist "%PROJECT_DIR%\downloader.py" exit /b 1
if not exist "%PROJECT_DIR%\convert.py" exit /b 1
if not exist "%PROJECT_DIR%\utils.py" exit /b 1
if not exist "%PROJECT_DIR%\path_ffmpeg.py" exit /b 1
if not exist "%PROJECT_DIR%\ffmpeg_check.py" exit /b 1
if not exist "%PROJECT_DIR%\aria2_check.py" exit /b 1
if not exist "%PROJECT_DIR%\notification.py" exit /b 1
if not exist "%PROJECT_DIR%\installer-windows.bat" exit /b 1
if not exist "%PROJECT_DIR%\run-it.bat" exit /b 1
if not exist "%PROJECT_DIR%\requirements.txt" exit /b 1
if not exist "%PROJECT_DIR%\languages\en.json" exit /b 1
if not exist "%PROJECT_DIR%\languages\ar.json" exit /b 1
if not exist "%PROJECT_DIR%\languages\fr.json" exit /b 1
if not exist "%PROJECT_DIR%\asset\Icon.ico" exit /b 1
if not exist "%PROJECT_DIR%\asset\Icon.png" exit /b 1
findstr /I /L /C:".venv\Scripts\python.exe" "%PROJECT_DIR%\run-it.bat" >nul 2>&1
if errorlevel 1 exit /b 1
exit /b 0


:: -----------------------------------------------------------------
:: Python discovery and installation
:: -----------------------------------------------------------------
:FindPython
set "BASE_PYTHON="
if /I "%WINDOWS_ARCH%"=="ARM64" if defined PYTHON_ARM_X64_DIR call :TryPythonPath "%PYTHON_ARM_X64_DIR%\python.exe"
if defined BASE_PYTHON exit /b 0
call :TryPythonLaunchers "-3.12"
if defined BASE_PYTHON exit /b 0
call :TryPythonLaunchers "-3.13"
if defined BASE_PYTHON exit /b 0
call :TryPythonLaunchers "-3.11"
if defined BASE_PYTHON exit /b 0
call :TryPythonLaunchers "-3.10"
if defined BASE_PYTHON exit /b 0
call :TryPythonLaunchers "-3"
if defined BASE_PYTHON exit /b 0
call :TryPythonFromPath
if defined BASE_PYTHON exit /b 0
if defined LOCALAPPDATA call :TryPythonPath "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined BASE_PYTHON exit /b 0
if defined ProgramFiles call :TryPythonPath "%ProgramFiles%\Python312\python.exe"
exit /b 0

:TryPythonCommand
set "PYTHON_CANDIDATE="
for /f "usebackq delims=" %%P in (`"%~1" %~2 -c "import sys; print(sys.executable)" 2^>nul`) do set "PYTHON_CANDIDATE=%%P"
if not defined PYTHON_CANDIDATE exit /b 1
call :TryPythonPath "%PYTHON_CANDIDATE%"
exit /b 0

:TryPythonLaunchers
for /f "delims=" %%P in ('where py.exe 2^>nul') do if not defined BASE_PYTHON call :TryPythonLauncherPath "%%P" "%~1"
exit /b 0

:TryPythonLauncherPath
set "PYTHON_LAUNCHER_CANDIDATE=%~1"
set "PYTHON_LAUNCHER_WITHOUT_ALIAS=%PYTHON_LAUNCHER_CANDIDATE:WindowsApps=%"
if /I not "%PYTHON_LAUNCHER_WITHOUT_ALIAS%"=="%PYTHON_LAUNCHER_CANDIDATE%" exit /b 1
call :TryPythonCommand "%PYTHON_LAUNCHER_CANDIDATE%" "%~2"
exit /b 0

:TryPythonPath
if not exist "%~1" exit /b 1
for %%I in ("%~1") do set "PYTHON_CANDIDATE_FULL=%%~fI"
if defined VENV_PYTHON if /I "%PYTHON_CANDIDATE_FULL%"=="%VENV_PYTHON%" exit /b 1
"%~1" -c "import sys, tkinter; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 exit /b 1
if /I "%WINDOWS_ARCH%"=="ARM64" "%~1" -c "import sysconfig; raise SystemExit(0 if sysconfig.get_platform().lower() == 'win-amd64' else 1)" >nul 2>&1
if /I "%WINDOWS_ARCH%"=="ARM64" if errorlevel 1 exit /b 1
set "BASE_PYTHON=%~1"
exit /b 0

:TryPythonFromPath
set "PYTHON_PATH_CANDIDATE="
for /f "delims=" %%P in ('where python.exe 2^>nul') do if not defined BASE_PYTHON call :TryNonAliasPythonPath "%%P"
exit /b 0

:TryNonAliasPythonPath
set "PYTHON_PATH_CANDIDATE=%~1"
set "PYTHON_PATH_WITHOUT_ALIAS=%PYTHON_PATH_CANDIDATE:WindowsApps=%"
if /I not "%PYTHON_PATH_WITHOUT_ALIAS%"=="%PYTHON_PATH_CANDIDATE%" exit /b 1
call :TryPythonPath "%PYTHON_PATH_CANDIDATE%"
exit /b 0

:InstallPython
if /I "%WINDOWS_ARCH%"=="ARM64" goto InstallPythonDirect
call :FindWinget
if not defined WINGET_EXE goto InstallPythonDirect
echo       Installing Python 3.12 for the current user with WinGet...
"%WINGET_EXE%" install --exact --id "Python.Python.3.12" --scope user --source winget --silent --accept-source-agreements --accept-package-agreements
call :RefreshPath
call :FindPython
if defined BASE_PYTHON exit /b 0

:InstallPythonDirect
call :CheckPowerShell
if errorlevel 1 exit /b 1
echo       WinGet did not provide Python; using the official Python installer...
set "PYTHON_INSTALLER_SUFFIX=-amd64.exe"
if /I "%WINDOWS_ARCH%"=="x86" set "PYTHON_INSTALLER_SUFFIX=.exe"
set "PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10%PYTHON_INSTALLER_SUFFIX%"
set "PYTHON_INSTALLER_FILE=%TEMP%\MediaDownloader-python-%RANDOM%-%RANDOM%%PYTHON_INSTALLER_SUFFIX%"
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri $env:PYTHON_INSTALLER_URL -OutFile $env:PYTHON_INSTALLER_FILE; $signature=Get-AuthenticodeSignature -LiteralPath $env:PYTHON_INSTALLER_FILE; if ($signature.Status -ne 'Valid') { throw 'The Python installer signature is not valid.' }; if ($signature.SignerCertificate.Subject -notlike '*Python Software Foundation*') { throw 'The Python installer publisher is not trusted.' }"
set "PYTHON_DOWNLOAD_EXIT=%ERRORLEVEL%"
if not "%PYTHON_DOWNLOAD_EXIT%"=="0" del /q "%PYTHON_INSTALLER_FILE%" >nul 2>&1
if not "%PYTHON_DOWNLOAD_EXIT%"=="0" set "ERROR_MESSAGE=The official Python installer could not be downloaded or verified."
if not "%PYTHON_DOWNLOAD_EXIT%"=="0" exit /b 1
if /I "%WINDOWS_ARCH%"=="ARM64" goto InstallEmulatedPythonOnArm
start "" /wait "%PYTHON_INSTALLER_FILE%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_pip=1 Include_tcltk=1 Include_test=0 Include_doc=0 Shortcuts=0
set "PYTHON_SETUP_EXIT=%ERRORLEVEL%"
goto PythonInstallerFinished

:InstallEmulatedPythonOnArm
if not defined PYTHON_ARM_X64_DIR set "ERROR_MESSAGE=A per-user Python directory could not be determined on Windows ARM."
if not defined PYTHON_ARM_X64_DIR exit /b 1
echo       Windows ARM detected: using isolated x64 Python for package compatibility...
start "" /wait "%PYTHON_INSTALLER_FILE%" /quiet InstallAllUsers=0 TargetDir="%PYTHON_ARM_X64_DIR%" PrependPath=0 Include_launcher=0 Include_pip=1 Include_tcltk=1 Include_test=0 Include_doc=0 Shortcuts=0
set "PYTHON_SETUP_EXIT=%ERRORLEVEL%"

:PythonInstallerFinished
del /q "%PYTHON_INSTALLER_FILE%" >nul 2>&1
if not "%PYTHON_SETUP_EXIT%"=="0" set "ERROR_MESSAGE=The official Python installer returned an error."
if not "%PYTHON_SETUP_EXIT%"=="0" exit /b 1
call :RefreshPath
call :FindPython
if not defined BASE_PYTHON set "ERROR_MESSAGE=Python setup finished, but Python could not be started. Restart Windows and run this installer again."
if not defined BASE_PYTHON exit /b 1
exit /b 0


:: -----------------------------------------------------------------
:: Private virtual environment and Python packages
:: -----------------------------------------------------------------
:EnsureVirtualEnvironment
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
if not exist "%VENV_PYTHON%" goto CreateVirtualEnvironment
"%VENV_PYTHON%" -c "import sys, tkinter; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto RebuildVirtualEnvironment
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if not errorlevel 1 exit /b 0

:RebuildVirtualEnvironment
echo       The existing .venv is damaged or too old; rebuilding it...

:CreateVirtualEnvironment
"%BASE_PYTHON%" -m venv --clear "%VENV_DIR%"
set "VENV_CREATE_EXIT=%ERRORLEVEL%"
if not "%VENV_CREATE_EXIT%"=="0" set "ERROR_MESSAGE=Python could not create %VENV_DIR%. Check folder permissions and free disk space."
if not "%VENV_CREATE_EXIT%"=="0" exit /b 1
if not exist "%VENV_PYTHON%" set "ERROR_MESSAGE=The virtual environment was created without python.exe."
if not exist "%VENV_PYTHON%" exit /b 1
"%VENV_PYTHON%" -m ensurepip --upgrade >nul 2>&1
set "ENSUREPIP_EXIT=%ERRORLEVEL%"
if not "%ENSUREPIP_EXIT%"=="0" set "ERROR_MESSAGE=pip could not be initialized inside the virtual environment."
if not "%ENSUREPIP_EXIT%"=="0" exit /b 1
exit /b 0

:InstallPythonDependencies
set "PIP_DISABLE_PIP_VERSION_CHECK=1"
set "PIP_NO_INPUT=1"
set "PYTHONUTF8=1"
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
set "PIP_BOOTSTRAP_EXIT=%ERRORLEVEL%"
if not "%PIP_BOOTSTRAP_EXIT%"=="0" set "ERROR_MESSAGE=pip, setuptools, or wheel could not be updated."
if not "%PIP_BOOTSTRAP_EXIT%"=="0" exit /b 1
set "REQUIREMENTS_INSTALL_FILE=%PROJECT_DIR%\requirements.txt"
set "REQUIREMENTS_SOURCE=%PROJECT_DIR%\requirements.txt"
set "FILTERED_REQUIREMENTS_FILE=%TEMP%\MediaDownloader-requirements-%RANDOM%-%RANDOM%.txt"
call :CheckPowerShell
if errorlevel 1 exit /b 1
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $filtered=@(); foreach ($line in [IO.File]::ReadAllLines($env:REQUIREMENTS_SOURCE)) { if ($line -notmatch '^\s*(aria2|yt-dlp)(\[.*\])?\s*([<>=!~].*)?(\s*#.*)?$') { $filtered += $line } }; [IO.File]::WriteAllLines($env:FILTERED_REQUIREMENTS_FILE,$filtered,(New-Object Text.UTF8Encoding($false)))"
if errorlevel 1 set "ERROR_MESSAGE=A temporary requirements file could not be prepared."
if errorlevel 1 exit /b 1
set "REQUIREMENTS_INSTALL_FILE=%FILTERED_REQUIREMENTS_FILE%"
"%VENV_PYTHON%" -m pip install --upgrade -r "%REQUIREMENTS_INSTALL_FILE%"
set "REQUIREMENTS_EXIT=%ERRORLEVEL%"
if defined FILTERED_REQUIREMENTS_FILE del /q "%FILTERED_REQUIREMENTS_FILE%" >nul 2>&1
if not "%REQUIREMENTS_EXIT%"=="0" set "ERROR_MESSAGE=One or more packages in requirements.txt could not be installed."
if not "%REQUIREMENTS_EXIT%"=="0" exit /b 1

"%VENV_PYTHON%" -m pip install --upgrade Pillow
if errorlevel 1 set "ERROR_MESSAGE=Pillow could not be installed."
if errorlevel 1 exit /b 1

"%VENV_PYTHON%" -m pip install --upgrade nodeenv
if errorlevel 1 echo       Warning: nodeenv fallback could not be installed.

set "CURL_CFFI_OK=0"
"%VENV_PYTHON%" -m pip install --upgrade "yt-dlp[default,curl-cffi]"
if errorlevel 1 goto InstallYtDlpFallback
set "CURL_CFFI_OK=1"
goto YtDlpInstalled

:InstallYtDlpFallback
echo       Warning: curl-cffi is unavailable on this Windows architecture.
echo       Installing yt-dlp without curl-cffi...
"%VENV_PYTHON%" -m pip install --upgrade "yt-dlp[default]"
if errorlevel 1 set "ERROR_MESSAGE=yt-dlp could not be installed."
if errorlevel 1 exit /b 1

:YtDlpInstalled
if /I "%WINDOWS_ARCH%"=="x86" goto DenoPackageSkipped
"%VENV_PYTHON%" -m pip install --upgrade "yt-dlp[deno]"
if errorlevel 1 echo       Warning: the isolated Deno runtime could not be installed; Node will be tried next.

:DenoPackageSkipped
exit /b 0

:ValidatePythonDependencies
"%VENV_PYTHON%" -c "import tkinter, customtkinter, tkinterdnd2, yt_dlp, PIL, CTkFileDialog, CTkMessagebox, CTkMenuBarPlus"
set "IMPORT_TEST_EXIT=%ERRORLEVEL%"
if not "%IMPORT_TEST_EXIT%"=="0" set "ERROR_MESSAGE=The Python package import test failed. Run the installer again and review the pip error above."
if not "%IMPORT_TEST_EXIT%"=="0" exit /b 1
call :TestProjectCode
if not errorlevel 1 goto ProjectCodeReady
echo       Application files failed validation; restoring a clean source copy...
call :RepairProjectSource
if errorlevel 1 exit /b 1
call :TestProjectCode
if not errorlevel 1 goto ProjectCodeReady
set "ERROR_MESSAGE=Application files still fail validation after a clean source repair."
exit /b 1

:ProjectCodeReady
"%VENV_PYTHON%" -m pip check
if errorlevel 1 echo       Warning: pip reported a dependency conflict. The import test still passed.
if "%CURL_CFFI_OK%"=="1" "%VENV_PYTHON%" -c "import curl_cffi" >nul 2>&1
if "%CURL_CFFI_OK%"=="1" if errorlevel 1 echo       Warning: curl-cffi was installed but its import test failed.
exit /b 0

:TestProjectCode
"%VENV_PYTHON%" -c "import json, os; from pathlib import Path; from PIL import Image; root=Path(os.environ['PROJECT_DIR']); [json.loads((root / 'languages' / name).read_text(encoding='utf-8')) for name in ('en.json','ar.json','fr.json')]; icon=Image.open(root / 'asset' / 'Icon.ico'); icon.verify(); os.chdir(root); import app; window=app.DnDCTk(); window.withdraw(); window.update_idletasks(); window.destroy()"
if errorlevel 1 exit /b 1
exit /b 0

:RepairProjectSource
call :RefreshProjectSource
if errorlevel 1 exit /b 1
call :InstallPythonDependencies
if errorlevel 1 exit /b 1
exit /b 0


:: -----------------------------------------------------------------
:: JavaScript runtime for current yt-dlp releases
:: -----------------------------------------------------------------
:EnsureJavaScriptRuntime
call :CheckDeno
if "%JS_RUNTIME_OK%"=="1" goto JavaScriptRuntimeReady
call :CheckNode
if "%JS_RUNTIME_OK%"=="1" goto JavaScriptRuntimeReady

if not exist "%VENV_PYTHON%" goto TrySystemNode
"%VENV_PYTHON%" -m nodeenv -p --node=lts
call :CheckNode
if "%JS_RUNTIME_OK%"=="1" goto JavaScriptRuntimeReady

:TrySystemNode
call :FindWinget
if not defined WINGET_EXE goto JavaScriptRuntimeWarning
echo       Installing Node.js LTS as a fallback...
"%WINGET_EXE%" install --exact --id "OpenJS.NodeJS.LTS" --scope user --source winget --silent --accept-source-agreements --accept-package-agreements
"%WINGET_EXE%" upgrade --exact --id "OpenJS.NodeJS.LTS" --scope user --source winget --silent --accept-source-agreements --accept-package-agreements
call :RefreshPath
set "PATH=%VENV_DIR%\Scripts;%PATH%"
call :CheckNode
if "%JS_RUNTIME_OK%"=="1" goto JavaScriptRuntimeReady

:JavaScriptRuntimeWarning
echo       Warning: Deno 2.3+ or Node.js 22+ is not available.
echo       Normal downloads still work, but some YouTube formats may be missing.
exit /b 0

:JavaScriptRuntimeReady
echo       Found "%JS_RUNTIME_NAME%"
exit /b 0

:CheckDeno
set "JS_RUNTIME_OK=0"
set "JS_RUNTIME_NAME="
set "DENO_FOUND="
if exist "%VENV_DIR%\Scripts\deno.exe" call :TestDeno "%VENV_DIR%\Scripts\deno.exe"
if defined DENO_FOUND exit /b 0
for /f "delims=" %%D in ('where deno.exe 2^>nul') do if not defined DENO_FOUND call :TestDeno "%%D"
if defined DENO_FOUND exit /b 0
exit /b 1

:TestDeno
"%~1" eval "const v=Deno.version.deno.split('.').map(Number);Deno.exit(v[0]>2||(v[0]===2&&v[1]>=3)?0:1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "JS_RUNTIME_OK=1"
set "JS_RUNTIME_NAME=Deno (%~1)"
set "DENO_FOUND=1"
exit /b 0

:CheckNode
set "JS_RUNTIME_OK=0"
set "JS_RUNTIME_NAME="
set "NODE_FOUND="
if exist "%VENV_DIR%\Scripts\node.exe" call :TestNode "%VENV_DIR%\Scripts\node.exe"
if defined NODE_FOUND exit /b 0
for /f "delims=" %%N in ('where node.exe 2^>nul') do if not defined NODE_FOUND call :TestNode "%%N"
if defined NODE_FOUND exit /b 0
exit /b 1

:TestNode
"%~1" -e "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "JS_RUNTIME_OK=1"
set "JS_RUNTIME_NAME=Node.js (%~1)"
set "NODE_FOUND=1"
exit /b 0


:: -----------------------------------------------------------------
:: Aria2 - optional, but install it when possible
:: -----------------------------------------------------------------
:EnsureAria2
set "ARIA2_OK=0"
set "ARIA2_FOUND="
set "LOCAL_ARIA2=%PROJECT_DIR%\aria2\aria2c.exe"
if not exist "%LOCAL_ARIA2%" goto CheckOtherAria2
call :TestAria2 "%LOCAL_ARIA2%"
if defined ARIA2_FOUND goto Aria2Ready
call :QuarantineBrokenAria2
if errorlevel 1 goto Aria2Warning

:CheckOtherAria2
if exist "%VENV_DIR%\Scripts\aria2c.exe" call :TestAria2 "%VENV_DIR%\Scripts\aria2c.exe"
if defined ARIA2_FOUND goto Aria2Ready
for /f "delims=" %%A in ('where aria2c.exe 2^>nul') do if not defined ARIA2_FOUND call :TestAria2 "%%A"
if defined ARIA2_FOUND goto Aria2Ready
call :FindWinget
if not defined WINGET_EXE goto Aria2Warning
"%WINGET_EXE%" install --exact --id "aria2.aria2" --scope user --source winget --silent --accept-source-agreements --accept-package-agreements
call :RefreshPath
set "PATH=%VENV_DIR%\Scripts;%PATH%"
for /f "delims=" %%A in ('where aria2c.exe 2^>nul') do if not defined ARIA2_FOUND call :TestAria2 "%%A"
if defined ARIA2_FOUND goto Aria2Ready

:Aria2Warning
echo       Warning: Aria2 is unavailable. Leave the Aria2 option unchecked in the app.
exit /b 0

:Aria2Ready
echo       Aria2 is ready.
exit /b 0

:QuarantineBrokenAria2
set "BROKEN_ARIA2=%PROJECT_DIR%\aria2\aria2c.exe.disabled-%RANDOM%-%RANDOM%"
move /y "%LOCAL_ARIA2%" "%BROKEN_ARIA2%" >nul 2>&1
if exist "%LOCAL_ARIA2%" exit /b 1
echo       A broken local aria2c.exe was disabled: "%BROKEN_ARIA2%"
exit /b 0

:TestAria2
"%~1" --version >nul 2>&1
if errorlevel 1 exit /b 1
set "ARIA2_OK=1"
set "ARIA2_FOUND=1"
exit /b 0


:: -----------------------------------------------------------------
:: FFmpeg - required; portable download is the WinGet fallback
:: -----------------------------------------------------------------
:EnsureFFmpeg
call :CheckFFmpeg
if "%FFMPEG_OK%"=="1" goto FFmpegReady
if "%FFMPEG_LOCAL_BROKEN%"=="1" goto DownloadPortableFFmpeg
call :FindWinget
if not defined WINGET_EXE goto DownloadPortableFFmpeg
echo       Installing FFmpeg with WinGet...
"%WINGET_EXE%" install --exact --id "Gyan.FFmpeg" --scope user --source winget --silent --accept-source-agreements --accept-package-agreements
call :RefreshPath
set "PATH=%VENV_DIR%\Scripts;%PATH%"
call :CheckFFmpeg
if "%FFMPEG_OK%"=="1" goto FFmpegReady

:DownloadPortableFFmpeg
echo       WinGet FFmpeg is unavailable; downloading a private portable copy...
call :DownloadFFmpegPortable
if errorlevel 1 exit /b 1
call :CheckFFmpeg
if not "%FFMPEG_OK%"=="1" set "ERROR_MESSAGE=FFmpeg or ffprobe is still missing after installation."
if not "%FFMPEG_OK%"=="1" exit /b 1

:FFmpegReady
echo       FFmpeg and ffprobe are ready.
exit /b 0

:CheckFFmpeg
set "FFMPEG_OK=0"
set "FFMPEG_LOCAL_BROKEN=0"
set "LOCAL_FFMPEG=%PROJECT_DIR%\ffmpeg\bin\ffmpeg.exe"
set "LOCAL_FFPROBE=%PROJECT_DIR%\ffmpeg\bin\ffprobe.exe"
if not exist "%LOCAL_FFMPEG%" if not exist "%LOCAL_FFPROBE%" goto CheckSystemFFmpeg
if not exist "%LOCAL_FFMPEG%" goto BrokenLocalFFmpeg
if not exist "%LOCAL_FFPROBE%" goto BrokenLocalFFmpeg
"%LOCAL_FFMPEG%" -version >nul 2>&1
if errorlevel 1 goto BrokenLocalFFmpeg
"%LOCAL_FFPROBE%" -version >nul 2>&1
if errorlevel 1 goto BrokenLocalFFmpeg
set "FFMPEG_OK=1"
exit /b 0

:BrokenLocalFFmpeg
set "FFMPEG_LOCAL_BROKEN=1"
set "BROKEN_FFMPEG_DIR=%PROJECT_DIR%\ffmpeg\bin.disabled-%RANDOM%-%RANDOM%"
move /y "%PROJECT_DIR%\ffmpeg\bin" "%BROKEN_FFMPEG_DIR%" >nul 2>&1
if exist "%LOCAL_FFMPEG%" set "ERROR_MESSAGE=Broken local FFmpeg files could not be disabled. Close programs using them and check folder permissions."
if exist "%LOCAL_FFMPEG%" exit /b 1
if exist "%LOCAL_FFPROBE%" set "ERROR_MESSAGE=Broken local FFmpeg files could not be disabled. Close programs using them and check folder permissions."
if exist "%LOCAL_FFPROBE%" exit /b 1
set "FFMPEG_LOCAL_BROKEN=0"
echo       Broken local FFmpeg files were preserved in: "%BROKEN_FFMPEG_DIR%"
goto CheckSystemFFmpeg

:CheckSystemFFmpeg
set "SYSTEM_FFMPEG="
set "SYSTEM_FFPROBE="
for /f "delims=" %%F in ('where ffmpeg.exe 2^>nul') do if not defined SYSTEM_FFMPEG set "SYSTEM_FFMPEG=%%F"
for /f "delims=" %%F in ('where ffprobe.exe 2^>nul') do if not defined SYSTEM_FFPROBE set "SYSTEM_FFPROBE=%%F"
if not defined SYSTEM_FFMPEG exit /b 1
if not defined SYSTEM_FFPROBE exit /b 1
"%SYSTEM_FFMPEG%" -version >nul 2>&1
if errorlevel 1 exit /b 1
"%SYSTEM_FFPROBE%" -version >nul 2>&1
if errorlevel 1 exit /b 1
set "FFMPEG_OK=1"
exit /b 0

:DownloadFFmpegPortable
call :CheckPowerShell
if errorlevel 1 exit /b 1
set "FFMPEG_ASSET_NAME=ffmpeg-master-latest-win64-gpl-shared.zip"
set "FFMPEG_RELEASE_REPOSITORY=BtbN/FFmpeg-Builds"
if /I "%WINDOWS_ARCH%"=="ARM64" set "FFMPEG_ASSET_NAME=ffmpeg-master-latest-winarm64-gpl-shared.zip"
if /I "%WINDOWS_ARCH%"=="x86" set "FFMPEG_ASSET_NAME=ffmpeg-master-latest-win32-gpl-shared.zip"
if /I "%WINDOWS_ARCH%"=="x86" set "FFMPEG_RELEASE_REPOSITORY=defisym/FFmpeg-Builds-Win32"
set "FFMPEG_DOWNLOAD_TARGET=%PROJECT_DIR%\ffmpeg\bin"
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ProgressPreference='SilentlyContinue'; $headers=@{ 'User-Agent'='Media-Downloader-Installer' }; $zip=Join-Path $env:TEMP ('MediaDownloader-ffmpeg-' + [guid]::NewGuid().ToString('N') + '.zip'); $out=Join-Path $env:TEMP ('MediaDownloader-ffmpeg-' + [guid]::NewGuid().ToString('N')); try { $release=Invoke-RestMethod -Headers $headers -Uri ('https://api.github.com/repos/' + $env:FFMPEG_RELEASE_REPOSITORY + '/releases/tags/latest'); $asset=$release.assets | Where-Object { $_.name -eq $env:FFMPEG_ASSET_NAME } | Select-Object -First 1; if ($null -eq $asset) { throw 'The matching FFmpeg release asset was not found.' }; Invoke-WebRequest -UseBasicParsing -Headers $headers -Uri $asset.browser_download_url -OutFile $zip; $digest=[string]$asset.digest; if ($digest -notmatch '^sha256:([0-9a-fA-F]{64})$') { throw 'GitHub did not provide an FFmpeg SHA-256 digest.' }; $expected=$Matches[1]; $actual=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash; if ($actual -ne $expected) { throw 'The FFmpeg archive checksum does not match.' }; Expand-Archive -LiteralPath $zip -DestinationPath $out -Force; $ffmpeg=Get-ChildItem -LiteralPath $out -Recurse -Filter 'ffmpeg.exe' | Select-Object -First 1; if ($null -eq $ffmpeg) { throw 'ffmpeg.exe was not found in the downloaded archive.' }; $ffprobe=Join-Path $ffmpeg.Directory.FullName 'ffprobe.exe'; if (-not (Test-Path -LiteralPath $ffprobe)) { throw 'ffprobe.exe was not found in the downloaded archive.' }; New-Item -ItemType Directory -Force -Path $env:FFMPEG_DOWNLOAD_TARGET | Out-Null; Copy-Item -Path (Join-Path $ffmpeg.Directory.FullName '*') -Destination $env:FFMPEG_DOWNLOAD_TARGET -Recurse -Force } finally { Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath $out -Recurse -Force -ErrorAction SilentlyContinue }"
set "FFMPEG_DOWNLOAD_EXIT=%ERRORLEVEL%"
if not "%FFMPEG_DOWNLOAD_EXIT%"=="0" if not defined ERROR_MESSAGE set "ERROR_MESSAGE=FFmpeg could not be installed. Check the Internet connection, antivirus, and available disk space."
if not "%FFMPEG_DOWNLOAD_EXIT%"=="0" exit /b 1
exit /b 0


:: -----------------------------------------------------------------
:: User shortcuts
:: -----------------------------------------------------------------
:CreateShortcuts
set "SHORTCUT_CREATED=0"
call :CheckPowerShell
if errorlevel 1 goto ShortcutWarning
set "SHORTCUT_TARGET=%PROJECT_DIR%\run-it.bat"
set "SHORTCUT_WORKDIR=%PROJECT_DIR%"
set "SHORTCUT_ICON=%PROJECT_DIR%\asset\Icon.ico"
if not exist "%SHORTCUT_ICON%" set "SHORTCUT_ICON=%PROJECT_DIR%\Icon.ico"
if not exist "%SHORTCUT_TARGET%" set "ERROR_MESSAGE=The application launcher is missing, so its shortcut cannot be created."
if not exist "%SHORTCUT_TARGET%" exit /b 1
if not exist "%SHORTCUT_ICON%" set "ERROR_MESSAGE=The application icon is missing, so the desktop shortcut cannot be created correctly."
if not exist "%SHORTCUT_ICON%" exit /b 1
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $shell=New-Object -ComObject WScript.Shell; $iconLocation=$env:SHORTCUT_ICON + ',0'; $desktop=[Environment]::GetFolderPath('Desktop'); if ([string]::IsNullOrWhiteSpace($desktop)) { throw 'Windows did not return the current user Desktop path.' }; New-Item -ItemType Directory -Force -Path $desktop | Out-Null; $desktopLink=Join-Path $desktop 'Media Downloader.lnk'; $shortcut=$shell.CreateShortcut($desktopLink); $shortcut.TargetPath=$env:SHORTCUT_TARGET; $shortcut.WorkingDirectory=$env:SHORTCUT_WORKDIR; $shortcut.Description='Media Downloader'; $shortcut.WindowStyle=7; $shortcut.IconLocation=$iconLocation; $shortcut.Save(); if (-not (Test-Path -LiteralPath $desktopLink -PathType Leaf)) { throw 'The Desktop shortcut was not created.' }; $programs=[Environment]::GetFolderPath('Programs'); if (-not [string]::IsNullOrWhiteSpace($programs)) { try { New-Item -ItemType Directory -Force -Path $programs | Out-Null; $menuLink=Join-Path $programs 'Media Downloader.lnk'; $menuShortcut=$shell.CreateShortcut($menuLink); $menuShortcut.TargetPath=$env:SHORTCUT_TARGET; $menuShortcut.WorkingDirectory=$env:SHORTCUT_WORKDIR; $menuShortcut.Description='Media Downloader'; $menuShortcut.WindowStyle=7; $menuShortcut.IconLocation=$iconLocation; $menuShortcut.Save() } catch { Write-Warning ('Start Menu shortcut: ' + $_.Exception.Message) } }"
set "SHORTCUT_EXIT=%ERRORLEVEL%"
if not "%SHORTCUT_EXIT%"=="0" goto ShortcutWarning
set "SHORTCUT_CREATED=1"
exit /b 0

:ShortcutWarning
set "ERROR_MESSAGE=The Desktop shortcut could not be created for the current Windows user."
echo       The application is installed, but its Desktop shortcut could not be created.
echo       You can still start the application with "%PROJECT_DIR%\run-it.bat".
exit /b 1


:: -----------------------------------------------------------------
:: Shared Windows helpers
:: -----------------------------------------------------------------
:FindWinget
set "WINGET_EXE="
for /f "delims=" %%W in ('where winget.exe 2^>nul') do if not defined WINGET_EXE set "WINGET_EXE=%%W"
if not defined WINGET_EXE if defined LOCALAPPDATA if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe" set "WINGET_EXE=%LOCALAPPDATA%\Microsoft\WindowsApps\winget.exe"
exit /b 0

:RefreshPath
set "REFRESHED_PATH="
for /f "usebackq delims=" %%P in (`"%POWERSHELL_EXE%" -NoLogo -NoProfile -Command "$m=[Environment]::GetEnvironmentVariable('Path','Machine'); $u=[Environment]::GetEnvironmentVariable('Path','User'); [Console]::Write($m + ';' + $u)" 2^>nul`) do set "REFRESHED_PATH=%%P"
if defined REFRESHED_PATH set "PATH=%REFRESHED_PATH%"
if not defined REFRESHED_PATH set "PATH=%ORIGINAL_PATH%"
if defined LOCALAPPDATA set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links"
exit /b 0

:CheckPowerShell
if exist "%POWERSHELL_EXE%" exit /b 0
where powershell.exe >nul 2>&1
if not errorlevel 1 exit /b 0
set "ERROR_MESSAGE=Windows PowerShell is required for downloads and shortcut creation."
exit /b 1
