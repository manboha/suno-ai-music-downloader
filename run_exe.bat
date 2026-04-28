@echo off
setlocal

cd /d "%~dp0"

set "APP_EXE=%CD%\dist\Suno AI Music Downloader\Suno AI Music Downloader.exe"

if not exist "%APP_EXE%" (
    echo [ERROR] Built executable not found.
    echo Run build_exe.bat first.
    exit /b 1
)

start "" "%APP_EXE%"
exit /b 0
