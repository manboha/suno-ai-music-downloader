import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Settings:
    name_template: str = "{trackno} - {name}"
    overwrite_files: bool = False
    embed_images: bool = True
    save_folder: str = ""


SETTINGS_PATH = Path(os.getenv("APPDATA", "")) / "SunoDownloader" / "settings.json"


def load_settings() -> Settings:
    """설정 파일을 읽어 Settings 객체로 반환합니다."""
    if not SETTINGS_PATH.exists():
        return Settings()
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return Settings(
            name_template=data.get("name_template", "{trackno} - {name}"),
            overwrite_files=data.get("overwrite_files", False),
            embed_images=data.get("embed_images", True),
            save_folder=data.get("save_folder", ""),
        )
    except Exception:
        return Settings()


def save_settings(settings: Settings) -> None:
    """Settings 객체를 JSON 파일로 저장합니다."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(asdict(settings), f, ensure_ascii=False, indent=2)
