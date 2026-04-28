@echo off
setlocal

cd /d "%~dp0"

set "DIST_DIR=%CD%\dist\Suno AI Music Downloader"
set "RELEASE_DIR=%CD%\release"
set "ARCHIVE_NAME=Suno-AI-Music-Downloader-v1.0.0-win64.zip"
set "ARCHIVE_PATH=%RELEASE_DIR%\%ARCHIVE_NAME%"

if not exist "%DIST_DIR%\Suno AI Music Downloader.exe" (
    echo [ERROR] Built app not found.
    echo Run build_exe.bat first.
    exit /b 1
)

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"
if exist "%ARCHIVE_PATH%" del "%ARCHIVE_PATH%"

echo [1/2] Creating release archive...
powershell -NoProfile -Command "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%ARCHIVE_PATH%' -Force"
if errorlevel 1 exit /b 1

echo [2/2] Release package ready:
echo "%ARCHIVE_PATH%"
exit /b 0
