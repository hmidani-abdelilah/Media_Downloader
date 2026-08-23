@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "ERRORLEVEL="
title Media Downloader

set "CHECK_ONLY=0"
set "ALLOW_REPAIR=1"
set "NO_PAUSE=0"
set "REPAIR_ATTEMPTED=0"
set "PUSHD_OK=0"
set "LAUNCH_ERROR="

:ParseArguments
if "%~1"=="" goto ArgumentsParsed
if /I "%~1"=="--check" set "CHECK_ONLY=1"
if /I "%~1"=="--check" set "ALLOW_REPAIR=0"
if /I "%~1"=="--check" set "NO_PAUSE=1"
if /I "%~1"=="--no-repair" set "ALLOW_REPAIR=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
shift
goto ParseArguments

:ArgumentsParsed
for %%I in ("%~dp0.") do set "SOURCE_DIR=%%~fI"
pushd "%SOURCE_DIR%" >nul 2>&1
if errorlevel 1 goto ProjectPathError
set "PUSHD_OK=1"
set "APP_DIR=%SOURCE_DIR%"
set "APP_FILE=%SOURCE_DIR%\app.py"
set "INSTALLER_FILE=%SOURCE_DIR%\installer-windows.bat"
set "VENV_DIR=%SOURCE_DIR%\.venv"
set "VENV_PYTHON=%SOURCE_DIR%\.venv\Scripts\python.exe"
set "INITIAL_PATH=%PATH%"
set "ORIGINAL_PATH=%PATH%"

if not exist "%APP_FILE%" goto ApplicationMissing

:Preflight
set "PATH=%VENV_DIR%\Scripts;%ORIGINAL_PATH%"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUNBUFFERED=1"

if not exist "%VENV_PYTHON%" goto EnvironmentMissing
"%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto EnvironmentDamaged

"%VENV_PYTHON%" -c "import tkinter, customtkinter, tkinterdnd2, yt_dlp, PIL, CTkFileDialog, CTkMessagebox, CTkMenuBarPlus" >nul 2>&1
if errorlevel 1 goto DependenciesMissing

call :CheckFFmpeg
if not "%FFMPEG_OK%"=="1" goto FFmpegMissing

"%VENV_PYTHON%" -c "import app" >nul 2>&1
if errorlevel 1 goto ApplicationFilesDamaged

if "%CHECK_ONLY%"=="1" goto CheckSucceeded
goto LaunchApplication

:EnvironmentMissing
set "LAUNCH_ERROR=The private Python environment is missing."
goto RepairInstallation

:EnvironmentDamaged
set "LAUNCH_ERROR=The private Python environment is damaged or uses an unsupported Python version."
goto RepairInstallation

:DependenciesMissing
set "LAUNCH_ERROR=One or more application packages are missing or damaged."
goto RepairInstallation

:FFmpegMissing
set "LAUNCH_ERROR=FFmpeg or ffprobe is missing."
goto RepairInstallation

:ApplicationFilesDamaged
set "LAUNCH_ERROR=One or more application files are missing, damaged, or incompatible."
goto RepairInstallation

:RepairInstallation
if "%ALLOW_REPAIR%"=="0" goto LauncherFailed
if "%REPAIR_ATTEMPTED%"=="1" goto LauncherFailed
if not exist "%INSTALLER_FILE%" goto InstallerMissing
set "REPAIR_ATTEMPTED=1"
echo %LAUNCH_ERROR%
echo Running the automatic repair. This may take several minutes...
set "REPAIR_COMMAND=%INSTALLER_FILE%"
"%ComSpec%" /D /S /C ""%%REPAIR_COMMAND%%" --repair --no-launch --no-pause"
set "REPAIR_EXIT=%ERRORLEVEL%"
if not "%REPAIR_EXIT%"=="0" goto RepairFailed
call :RefreshPath
goto Preflight

:LaunchApplication
call :PrepareLog
if not "%LOG_ENABLED%"=="1" goto LaunchWithoutLog
echo Starting Media Downloader...
echo If startup fails, details will be saved in:
echo "%LOG_FILE%"
>>"%LOG_FILE%" "%VENV_PYTHON%" --version
>>"%LOG_FILE%" echo.
if errorlevel 1 set "LOG_ENABLED=0"
if not "%LOG_ENABLED%"=="1" goto LaunchWithoutLog
"%VENV_PYTHON%" "%APP_FILE%" >>"%LOG_FILE%" 2>&1
set "APP_EXIT=%ERRORLEVEL%"
goto ApplicationFinished

:LaunchWithoutLog
echo Starting Media Downloader...
echo Warning: the log file is unavailable, so errors will remain in this window.
"%VENV_PYTHON%" "%APP_FILE%"
set "APP_EXIT=%ERRORLEVEL%"

:ApplicationFinished
if not "%APP_EXIT%"=="0" goto ApplicationCrashed
set "FINAL_EXIT=0"
goto Finish

:CheckSucceeded
echo Media Downloader installation check passed.
"%VENV_PYTHON%" --version
echo Python environment: "%VENV_DIR%"
echo FFmpeg: available
call :ReportOptionalTools
set "FINAL_EXIT=0"
goto Finish

:ApplicationCrashed
set "LAUNCH_ERROR=Media Downloader closed with error code %APP_EXIT%."
echo.
echo %LAUNCH_ERROR%
if "%LOG_ENABLED%"=="1" echo Error details: "%LOG_FILE%"
if not "%LOG_ENABLED%"=="1" echo No log file could be written. Review the error shown above.
set "FINAL_EXIT=%APP_EXIT%"
if "%FINAL_EXIT%"=="0" set "FINAL_EXIT=1"
goto PauseAndFinish

:ApplicationMissing
set "LAUNCH_ERROR=app.py was not found next to run-it.bat. Extract or download the complete project first."
goto LauncherFailed

:InstallerMissing
set "LAUNCH_ERROR=installer-windows.bat is missing, so automatic repair cannot continue."
goto LauncherFailed

:RepairFailed
set "LAUNCH_ERROR=Automatic repair failed. Review the installer message above, then run installer-windows.bat again."
goto LauncherFailed

:ProjectPathError
set "LAUNCH_ERROR=Windows could not open the folder that contains run-it.bat."
goto LauncherFailed

:LauncherFailed
echo.
echo Media Downloader could not start.
echo %LAUNCH_ERROR%
if defined APP_DIR echo Project: "%APP_DIR%"
set "FINAL_EXIT=1"

:PauseAndFinish
if "%NO_PAUSE%"=="1" goto Finish
pause

:Finish
if "%PUSHD_OK%"=="1" popd
endlocal & exit /b %FINAL_EXIT%


:: -----------------------------------------------------------------
:: Preflight helpers
:: -----------------------------------------------------------------
:CheckFFmpeg
set "FFMPEG_OK=0"
if not exist "%APP_DIR%\ffmpeg\bin\ffmpeg.exe" if not exist "%APP_DIR%\ffmpeg\bin\ffprobe.exe" goto CheckSystemFFmpeg
if not exist "%APP_DIR%\ffmpeg\bin\ffmpeg.exe" exit /b 1
if not exist "%APP_DIR%\ffmpeg\bin\ffprobe.exe" exit /b 1
"%APP_DIR%\ffmpeg\bin\ffmpeg.exe" -version >nul 2>&1
if errorlevel 1 exit /b 1
"%APP_DIR%\ffmpeg\bin\ffprobe.exe" -version >nul 2>&1
if errorlevel 1 exit /b 1
set "FFMPEG_OK=1"
exit /b 0

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

:PrepareLog
set "LOG_ENABLED=0"
set "LOG_DIR="
set "LOG_FILE="
if defined LOCALAPPDATA set "LOG_DIR=%LOCALAPPDATA%\Media Downloader\logs"
if not defined LOG_DIR set "LOG_DIR=%TEMP%\Media Downloader\logs"
if not exist "%LOG_DIR%\." mkdir "%LOG_DIR%" >nul 2>&1
if not exist "%LOG_DIR%\." goto PrepareFallbackLog
set "LOG_FILE=%LOG_DIR%\latest.log"
>"%LOG_FILE%" echo Media Downloader launch log
if errorlevel 1 goto PrepareFallbackLog
set "LOG_ENABLED=1"
exit /b 0

:PrepareFallbackLog
set "LOG_FILE=%TEMP%\MediaDownloader-latest-%RANDOM%-%RANDOM%.log"
>"%LOG_FILE%" echo Media Downloader launch log
if errorlevel 1 exit /b 0
set "LOG_ENABLED=1"
exit /b 0

:ReportOptionalTools
set "REPORT_DENO="
set "REPORT_NODE="
set "REPORT_ARIA2="
if exist "%VENV_DIR%\Scripts\deno.exe" call :TestDenoForReport "%VENV_DIR%\Scripts\deno.exe"
for /f "delims=" %%D in ('where deno.exe 2^>nul') do if not defined REPORT_DENO call :TestDenoForReport "%%D"
if exist "%VENV_DIR%\Scripts\node.exe" call :TestNodeForReport "%VENV_DIR%\Scripts\node.exe"
for /f "delims=" %%N in ('where node.exe 2^>nul') do if not defined REPORT_NODE call :TestNodeForReport "%%N"
if exist "%VENV_DIR%\Scripts\aria2c.exe" call :TestAria2ForReport "%VENV_DIR%\Scripts\aria2c.exe"
for /f "delims=" %%A in ('where aria2c.exe 2^>nul') do if not defined REPORT_ARIA2 call :TestAria2ForReport "%%A"
if defined REPORT_DENO echo JavaScript runtime: Deno 2.3+ ^("%REPORT_DENO%"^)
if defined REPORT_NODE echo JavaScript runtime: Node.js 22+ ^("%REPORT_NODE%"^)
if not defined REPORT_DENO if not defined REPORT_NODE echo JavaScript runtime: optional runtime not available
if defined REPORT_ARIA2 echo Aria2: available ^("%REPORT_ARIA2%"^)
if not defined REPORT_ARIA2 echo Aria2: optional component not available
exit /b 0

:TestDenoForReport
"%~1" eval "const v=Deno.version.deno.split('.').map(Number);Deno.exit(v[0]>2||(v[0]===2&&v[1]>=3)?0:1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "REPORT_DENO=%~1"
exit /b 0

:TestNodeForReport
"%~1" -e "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)" >nul 2>&1
if errorlevel 1 exit /b 1
set "REPORT_NODE=%~1"
exit /b 0

:TestAria2ForReport
"%~1" --version >nul 2>&1
if errorlevel 1 exit /b 1
set "REPORT_ARIA2=%~1"
exit /b 0

:RefreshPath
set "REFRESHED_PATH="
if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" for /f "usebackq delims=" %%P in (`%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -Command "$m=[Environment]::GetEnvironmentVariable('Path','Machine'); $u=[Environment]::GetEnvironmentVariable('Path','User'); [Console]::Write($m + ';' + $u)" 2^>nul`) do set "REFRESHED_PATH=%%P"
if defined REFRESHED_PATH set "ORIGINAL_PATH=%REFRESHED_PATH%"
if not defined REFRESHED_PATH set "ORIGINAL_PATH=%INITIAL_PATH%"
if defined LOCALAPPDATA set "ORIGINAL_PATH=%ORIGINAL_PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links"
exit /b 0
