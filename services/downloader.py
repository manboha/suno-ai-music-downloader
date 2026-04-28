import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

import requests
from mutagen.id3 import ID3, APIC, error as MutagenError
from mutagen.mp3 import MP3
from pathvalidate import sanitize_filename

from services.suno import PlaylistClip, ClipStatus, Playlist
from services.settings import Settings

MAX_AUDIO_BYTES = 100 * 1024 * 1024
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def _make_song_filename(song: PlaylistClip, template: str, output_dir: Path) -> Path:
    """
    템플릿 문자열로 파일명 생성.
    getSongName() 대응. pathvalidate로 특수문자 처리.
    """
    track_no = str(song.no).zfill(2)
    safe_title = sanitize_filename(song.title, platform="windows")
    name = template.replace("{trackno}", track_no).replace("{name}", safe_title)
    return output_dir / f"{name}.mp3"


def _embed_album_art(mp3_path: Path, image_data: bytes) -> None:
    """
    MP3 파일에 앨범아트를 ID3 태그로 임베드합니다.
    add_image_to_mp3() Rust 커맨드 대응.
    원본의 await 누락 버그를 수정: 파일 쓰기 완료 후 태그 작업 실행.
    """
    try:
        try:
            tags = ID3(str(mp3_path))
        except MutagenError:
            tags = ID3()

        tags.add(APIC(
            encoding=3,           # UTF-8
            mime="image/jpeg",
            type=3,               # Cover (front)
            desc="Cover Art",
            data=image_data,
        ))
        tags.save(str(mp3_path), v2_version=4)
    except Exception as e:
        print(f"[경고] 앨범아트 임베드 실패: {mp3_path.name} — {e}")


def _validate_remote_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("유효하지 않은 다운로드 URL입니다.")


def _download_to_file(url: str, output_path: Path, max_bytes: int) -> None:
    _validate_remote_url(url)
    with requests.get(url, timeout=30, stream=True) as resp:
        if resp.status_code != 200:
            raise ConnectionError(f"HTTP {resp.status_code}")

        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ValueError("파일 크기가 허용 한도를 초과했습니다.")

        total = 0
        with output_path.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("파일 크기가 허용 한도를 초과했습니다.")
                f.write(chunk)


def _download_bytes(url: str, max_bytes: int) -> bytes:
    _validate_remote_url(url)
    with requests.get(url, timeout=15, stream=True) as resp:
        if resp.status_code != 200:
            raise ConnectionError(f"HTTP {resp.status_code}")

        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            raise ValueError("파일 크기가 허용 한도를 초과했습니다.")

        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("파일 크기가 허용 한도를 초과했습니다.")
            chunks.append(chunk)
        return b"".join(chunks)


def download_song(
    song: PlaylistClip,
    output_dir: Path,
    tmp_dir: Path,
    settings: Settings,
    on_status: Callable[[str, ClipStatus], None],
    on_progress: Callable[[], None],
) -> None:
    """
    단일 곡 다운로드 처리.
    원본 App.tsx의 limit() 내부 익명 함수 대응.
    """
    on_status(song.id, ClipStatus.PROCESSING)

    mp3_path = _make_song_filename(song, settings.name_template, output_dir)

    # 파일 존재 + 덮어쓰기 비활성화 → 스킵
    if not settings.overwrite_files and mp3_path.exists():
        on_status(song.id, ClipStatus.SKIPPED)
        on_progress()
        return

    try:
        # ① MP3 다운로드
        _download_to_file(song.audio_url, mp3_path, MAX_AUDIO_BYTES)

        # ③ 앨범아트 임베드
        if settings.embed_images and song.image_url:
            image_data = _download_bytes(song.image_url, MAX_IMAGE_BYTES)
            _embed_album_art(mp3_path, image_data)

        on_status(song.id, ClipStatus.SUCCESS)

    except Exception as e:
        print(f"[오류] {song.title}: {e}")
        on_status(song.id, ClipStatus.ERROR)

    finally:
        on_progress()


def download_playlist(
    playlist: Playlist,
    clips: list[PlaylistClip],
    save_folder: str,
    settings: Settings,
    on_status: Callable[[str, ClipStatus], None],
    on_progress: Callable[[int, int], None],
    on_done: Callable[[bool], None],
    stop_event: Optional[threading.Event] = None,
) -> None:
    """
    전체 플레이리스트 다운로드.
    pLimit(5) 대응: ThreadPoolExecutor(max_workers=5).
    별도 스레드에서 실행되어 GUI를 블로킹하지 않습니다.
    """
    safe_name = sanitize_filename(playlist.name, platform="windows") or "playlist"
    output_dir = Path(save_folder) / safe_name
    tmp_dir = output_dir / "tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    completed = 0
    total = len(clips)
    progress_lock = threading.Lock()

    def _progress():
        nonlocal completed
        with progress_lock:
            completed += 1
            current = completed
        on_progress(current, total)

    try:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(
                    download_song,
                    song, output_dir, tmp_dir, settings, on_status, _progress
                ): song
                for song in clips
            }
            for future in as_completed(futures):
                if stop_event and stop_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                future.result()  # 예외 전파

    except Exception as e:
        print(f"[치명 오류] {e}")
        on_done(False)
        return
    finally:
        # tmpDir 정리 (원본: deletePath(tmpDir))
        try:
            if tmp_dir.exists():
                for f in tmp_dir.iterdir():
                    f.unlink(missing_ok=True)
                tmp_dir.rmdir()
        except Exception:
            pass

    on_done(True)
