# Release Notes

## v1.0.0

Initial public release of `Suno AI Music Downloader`.

### Highlights

- Added Windows desktop GUI built with CustomTkinter
- Added Suno playlist loading workflow
- Added per-song selection before download
- Added parallel MP3 downloads
- Added optional album art embedding into MP3 files
- Added persistent settings for filename format, overwrite mode, and save folder
- Added PyInstaller build batch scripts for local EXE packaging

### UI

- Refined dark theme and card-based layout
- Added custom in-app header styling
- Restyled settings dialog to match the main application

### Stability

- Moved network work off the main UI thread
- Improved download progress handling under concurrency
- Cleared stale playlist state after fetch failures
- Added streaming downloads with basic URL and file size validation

### Notes

- This release is focused on Windows usage
- API compatibility may change if Suno changes its service behavior
- Users are responsible for complying with content rights and platform terms
