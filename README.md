# YT to MP3

This project contains Python scripts for processing YouTube links and playlists. This guide covers setting up and running `YTMP3.py` on Windows.

## Requirements

- Windows 10 or later
- Python 3, available from PowerShell as `py`
- FFmpeg, with both `ffmpeg` and `ffprobe` available on `PATH`
- Internet access and a playlist the script can access

Check that FFmpeg is installed by opening a new PowerShell window and running:

```powershell
ffmpeg -version
ffprobe -version
```

If either command is not recognized, install an FFmpeg build and add its `bin` folder to `PATH`. Alternatively, set `FFMPEG_LOCATION` in `YTMP3.py` to the FFmpeg `bin` folder.

## Setup

Open PowerShell in the project folder. Replace the example path with where you put the project:

```powershell
cd "C:\path\to\YT_to_MP3"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The requirements file installs the dependencies for the project’s scripts. If you only plan to use `YTMP3.py`, it imports `yt-dlp` as its only third-party Python package; you can install that instead of the full requirements file:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade yt-dlp
```

## Configure and run `YTMP3.py`

Before running it on another computer, open `YTMP3.py` and review the configuration near the top:

- `PLAYLIST_URL`: set this to a regular YouTube or YouTube Music playlist URL, or to a single video/track URL. The script uses yt-dlp to read and download the audio. Individual items can still fail if they are unavailable or inaccessible (for example, due to region restrictions).
- `OUTPUT_FOLDER`: change this from the current computer’s `C:\Users\rahil\...` path to a folder on your computer. For a folder beside the script, use:

  ```python
  OUTPUT_FOLDER = Path(__file__).resolve().parent / "Script_Downloaded_Tracks_with_Metadata"
  ```
- `FFMPEG_LOCATION`: leave this as `None` if FFmpeg is on `PATH`; otherwise, set it to the FFmpeg `bin` folder.

Then run:

```powershell
.\.venv\Scripts\python.exe .\YTMP3.py
```

The script creates the output folder if needed. For a playlist, it reads the entries, reverses their order, and processes them in that order. For a single video/track URL, it processes that item. Existing MP3 files are skipped; after two consecutive existing files, it stops early. For each downloaded entry, it converts the audio to MP3 and processes its metadata and thumbnail.

## Troubleshooting

- **Python is not found:** Install Python 3 and ensure the Python launcher (`py`) is available, then reopen PowerShell.
- **FFmpeg or ffprobe is required:** Add FFmpeg’s `bin` folder to `PATH`, or set `FFMPEG_LOCATION`. Open a new terminal after changing `PATH`.
- **Playlist or track cannot be retrieved:** Check the URL and confirm the playlist is accessible from your network. Some entries may be unavailable.
- **A download fails unexpectedly:** Update yt-dlp in the project environment and try again:

  ```powershell
  .\.venv\Scripts\python.exe -m pip install --upgrade yt-dlp
  ```

## Other platforms

`YTMP3.py` is not set up to run directly on iOS. It expects Python and FFmpeg/ffprobe in a desktop environment, and its default output path is Windows-specific.
