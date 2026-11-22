import re
import shutil
from pathlib import Path

import yt_dlp
from yt_dlp.postprocessor.metadataparser import MetadataFromFieldPP
from yt_dlp.postprocessor.metadataparser import MetadataParserPP

# -------- CONFIGURATION --------
PLAYLIST_URL = r""
OUTPUT_FOLDER = Path(r"")

# Set to the FFmpeg bin directory or ffmpeg executable if it is not on PATH.
FFMPEG_LOCATION = None
# --------------------------------


def safe_filename(name):
    """Remove characters that Windows does not allow in filenames."""
    name = str(name).strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.rstrip(". ")
    return name[:180] or "unnamed_audio"


def iter_track_info(url):
    options = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "lazy_playlist": True,
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        playlist = downloader.extract_info(url, download=False, process=False)
        if playlist is None:
            raise ValueError("Could not retrieve playlist or track information")

        entries = playlist.get("entries")
        if entries is None:
            yield downloader.process_ie_result(playlist, download=False)
            return

        entries = list(entries)
        entries.reverse()
        for entry in entries:
            if entry is None:
                yield None
                continue
            yield downloader.process_ie_result(entry, download=False)


def get_source_track_name(track):
    """Build a filename from available artist and track metadata."""
    song_name = track.get("track")
    if not isinstance(song_name, str) or not song_name.strip():
        song_name = track.get("title")
    if not isinstance(song_name, str) or not song_name.strip():
        raise ValueError("Could not retrieve the track title")
    song_name = song_name.strip()

    artist_value = track.get("artist")
    if isinstance(artist_value, str) and artist_value.strip():
        artist = artist_value.strip()
    else:
        artists = track.get("artists")
        if isinstance(artists, str):
            artist = artists.strip()
        elif isinstance(artists, (list, tuple)):
            artist = ", ".join(
                name.strip()
                for name in artists
                if isinstance(name, str) and name.strip()
            )
        else:
            artist = ""

    if not artist:
        return song_name

    if song_name.lower().startswith(f"{artist.lower()} -"):
        return song_name
    return f"{artist} - {song_name}"


def download_audio(url, filename, output_folder):
    output_template = str(output_folder / f"{filename}.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "overwrites": False,
        "quiet": False,
        "retries": 3,
        "writethumbnail": True,
        "postprocessor_args": {
            "thumbnailsconvertor+ffmpeg_o": [
                "-vf",
                "crop='min(iw,ih)':'min(iw,ih)'",
            ],
        },
        "postprocessors": [
            {
                "key": "MetadataParser",
                "actions": [
                    MetadataFromFieldPP.to_action(
                        "%(release_year)s:%(meta_year)s"
                    )
                ],
                "when": "pre_process",
            },
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            },
            {
                "key": "MetadataParser",
                "actions": [
                    (MetadataParserPP.Actions.REPLACE, "description", r"(?s).*", ""),
                    (MetadataParserPP.Actions.REPLACE, "webpage_url", r"(?s).*", ""),
                ],
                "when": "post_process",
            },
            {"key": "FFmpegMetadata"},
            {"key": "FFmpegThumbnailsConvertor", "format": "jpg>png/webp>png"},
            {"key": "EmbedThumbnail"},
        ],
    }
    if FFMPEG_LOCATION:
        options["ffmpeg_location"] = str(FFMPEG_LOCATION)

    with yt_dlp.YoutubeDL(options) as downloader:
        downloader.download([url])


def main():
    print("Starting YTMP3...", flush=True)
    if not FFMPEG_LOCATION and (
        not shutil.which("ffmpeg") or not shutil.which("ffprobe")
    ):
        raise RuntimeError(
            "FFmpeg and ffprobe are required for MP3 conversion. "
            "Install FFmpeg and add its bin folder to PATH, or set "
            "FFMPEG_LOCATION in this script."
        )

    output_folder = OUTPUT_FOLDER
    output_folder.mkdir(parents=True, exist_ok=True)

    print("Reading playlist entries before processing newest first...", flush=True)

    results = {"Downloaded": 0, "Skipped": 0, "Failed": 0}
    track_count = 0
    consecutive_existing = 0
    for track in iter_track_info(PLAYLIST_URL):
        track_count += 1
        if track is None:
            print("Skipped unavailable playlist entry")
            results["Skipped"] += 1
            consecutive_existing = 0
            continue

        try:
            track_name = get_source_track_name(track)
            track_url = (
                track.get("webpage_url")
                or track.get("original_url")
                or track.get("url")
            )
            if not track_url:
                raise ValueError("Could not retrieve the track URL")

            filename = safe_filename(track_name)
            output_file = output_folder / f"{filename}.mp3"
            if output_file.is_file():
                print(f"Skipped (already exists): {output_file.name}")
                results["Skipped"] += 1
                consecutive_existing += 1
                if consecutive_existing == 2:
                    print(
                        "Stopping early as got two consecutive downloaded tracks..."
                    )
                    break
                continue

            consecutive_existing = 0
            print(f"\nDownloading: {filename}")
            download_audio(str(track_url), filename, output_folder)
            print(f"SUCCESS: {filename}")
            results["Downloaded"] += 1
        except Exception as error:
            results["Failed"] += 1
            consecutive_existing = 0
            print(f"FAILED: {track.get('title', 'Playlist entry')} - {error}")

    if not track_count:
        raise ValueError("No tracks found at this URL")

    print(
        "\nFinished. "
        + ", ".join(f"{status}: {count}" for status, count in results.items())
    )
    print(f"Output folder: {output_folder}")


if __name__ == "__main__":
    main()
