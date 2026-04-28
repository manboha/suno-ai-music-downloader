import re
import requests
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ClipStatus(Enum):
    NONE = "none"
    PROCESSING = "processing"
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class Playlist:
    name: str
    image_url: str


@dataclass
class PlaylistClip:
    id: str
    no: int
    title: str
    duration: float
    tags: str
    model_version: str
    audio_url: str
    image_url: str
    status: ClipStatus = ClipStatus.NONE


def get_songs_from_playlist(url: str) -> tuple[Playlist, list[PlaylistClip]]:
    """
    Suno 플레이리스트 URL에서 곡 목록을 가져옵니다.
    Suno.ts의 getSongsFromPlayList() 대응.
    """
    match = re.search(r"suno\.com/playlist/([^/?#]+)", url)
    if not match:
        raise ValueError("유효하지 않은 Suno 플레이리스트 URL입니다.")

    playlist_id = match.group(1)
    clips: list[PlaylistClip] = []
    current_page = 1
    song_no = 1
    playlist_name = ""
    playlist_image = ""

    while True:
        api_url = f"https://studio-api.prod.suno.com/api/playlist/{playlist_id}/?page={current_page}"
        response = requests.get(api_url, timeout=15)

        if response.status_code != 200:
            raise ConnectionError(f"플레이리스트 데이터를 가져오지 못했습니다. (상태코드: {response.status_code})")

        data = response.json()
        playlist_clips = data.get("playlist_clips", [])

        if not playlist_clips:
            break

        playlist_name = data.get("name", "Unknown Playlist")
        playlist_image = data.get("image_url", "")

        for item in playlist_clips:
            clip = item.get("clip", {})
            metadata = clip.get("metadata", {})
            clips.append(PlaylistClip(
                id=clip.get("id", ""),
                no=song_no,
                title=clip.get("title", "Untitled"),
                duration=metadata.get("duration", 0),
                tags=metadata.get("tags", ""),
                model_version=clip.get("major_model_version", ""),
                audio_url=clip.get("audio_url", ""),
                image_url=clip.get("image_url", ""),
            ))
            song_no += 1

        current_page += 1

    return Playlist(name=playlist_name, image_url=playlist_image), clips


def format_duration(seconds: float) -> str:
    """초 → mm:ss 포맷 변환. formatSecondsToTime() 대응."""
    total = round(seconds)
    mins = total // 60
    secs = total % 60
    return f"{mins}:{secs:02d}"
