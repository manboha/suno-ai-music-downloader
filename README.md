# Suno AI Music Downloader

Desktop GUI app for downloading songs from a Suno playlist as MP3 files on Windows.

This project was independently implemented in Python/CustomTkinter.

UI/UX inspiration was drawn in part from community Suno downloader projects, including:
- https://github.com/DrummerSi/suno-downloader

This implementation also includes UI refinements and some feature improvements beyond that reference workflow.

## Features

- Paste a Suno playlist link and load its songs
- Review the playlist before downloading
- Select only the songs you want to download
- Download up to 5 songs in parallel
- Save settings between runs
- Optional MP3 album art embedding
- Windows-friendly GUI with no terminal required

## Screens

- Playlist URL input
- Song review list with per-song selection
- Folder selection and download
- Settings dialog for filename format, overwrite mode, and artwork embedding

## Requirements

- Windows
- Python 3.13 recommended

## Install

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run From Source

```powershell
venv\Scripts\activate
python main.py
```

## Build EXE With PyInstaller

This repository includes helper batch files.

```powershell
.\build_exe.bat
.\run_exe.bat
```

Build output:

```text
dist\Suno AI Music Downloader\Suno AI Music Downloader.exe
```

To create a GitHub Release-ready ZIP package:

```powershell
.\package_release.bat
```

Release package output:

```text
release\Suno-AI-Music-Downloader-v1.0.0-win64.zip
```

## Project Structure

```text
main.py
services/
  downloader.py
  settings.py
  suno.py
ui/
  app.py
  settings_dialog.py
build_exe.bat
run_exe.bat
```

## Settings Storage

The app stores user settings here on Windows:

```text
%APPDATA%\SunoDownloader\settings.json
```

## Download and Run

For end users downloading a release build:

1. Download the ZIP file from the GitHub Releases page.
2. Extract the ZIP to a normal folder such as `Desktop` or `Documents`.
3. Open the extracted folder.
4. Run `Suno AI Music Downloader.exe`.

Notes:

- Do not run the app directly from inside the ZIP file.
- Keep all extracted files together in the same folder.
- On first run, Windows SmartScreen may show a warning for unsigned software. If you trust the file, choose the option to continue.

## Notes

- This app depends on Suno playlist/API behavior and may require updates if the service changes.
- Downloaded content rights and usage responsibility belong to the user.
- This project is intended for personal utility use.

## Privacy and Security

This project is designed as a local desktop utility. It does not include telemetry, analytics, advertising SDKs, or a developer-operated logging backend.

Data handling summary:

- The app does not send playlist URLs, song counts, local file paths, or user identifiers to a developer-controlled server.
- The app stores user preferences locally in `%APPDATA%\SunoDownloader\settings.json`.
- The app does not collect or reuse user login credentials, browser cookies, or access tokens.

Network behavior:

- The app makes direct HTTP requests only for:
  - loading playlist data from Suno-related public endpoints
  - downloading audio files from the remote `audio_url`
  - downloading cover art from the remote `image_url` when artwork embedding is enabled

Security scope:

- This is a native Python desktop application, so browser-only controls such as CSP do not apply.
- There is no built-in auto-update mechanism.
- There is no end-user debug panel or hidden logging console intended to transmit usage data.
- Download URLs are validated for basic `http`/`https` scheme and size limits before files are written.

Limitations:

- This project does not currently implement a strict host allowlist for all remote media URLs.
- Remote API compatibility and behavior depend on Suno and related file hosts.

## Known Limitations

- Windows-focused packaging and testing
- No installer package included by default
- Network/API failures depend on Suno availability and remote response quality

## License

MIT License. See [LICENSE](LICENSE).
