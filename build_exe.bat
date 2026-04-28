@echo off
setlocal

cd /d "%~dp0"

set "VENV_PYTHON=%CD%\venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Python virtual environment not found: "%VENV_PYTHON%"
    echo Create the venv first, then install dependencies.
    exit /b 1
)

echo [1/3] Installing or updating build dependencies...
"%VENV_PYTHON%" -m pip install --upgrade pip pyinstaller
if errorlevel 1 exit /b 1

echo [2/3] Building Windows executable...
"%VENV_PYTHON%" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --name "Suno AI Music Downloader" ^
  --collect-all customtkinter ^
  --hidden-import PIL._tkinter_finder ^
  main.py
if errorlevel 1 exit /b 1

echo [3/3] Build complete.
echo Output: "%CD%\dist\Suno AI Music Downloader\Suno AI Music Downloader.exe"
exit /b 0
