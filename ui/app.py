import threading
from pathlib import Path
from tkinter import filedialog
import tkinter.font as tkfont

import customtkinter as ctk

from services.downloader import download_playlist
from services.settings import Settings, load_settings, save_settings
from services.suno import (
    ClipStatus, Playlist, PlaylistClip,
    format_duration, get_songs_from_playlist
)
from ui.settings_dialog import SettingsDialog

# ── 상수 ─────────────────────────────────────────────────
STATUS_SYMBOLS = {
    ClipStatus.NONE:       ("", "gray60"),
    ClipStatus.PROCESSING: ("...", "#89a6c8"),
    ClipStatus.SUCCESS:    ("Done", "#4ed19a"),
    ClipStatus.SKIPPED:    ("Skip", "#e3b05f"),
    ClipStatus.ERROR:      ("Error", "#f07a78"),
}

BG_COLOR = "#14181d"
HEADER_COLOR = "#101419"
PANEL_COLOR = "#1b2128"
PANEL_ALT = "#202832"
BORDER_COLOR = "#2a333d"
INPUT_COLOR = "#11161c"
BUTTON_COLOR = "#4f8cff"
BUTTON_HOVER = "#72a4ff"
BUTTON_TEXT = "#f7fbff"
TEXT_MAIN = "#f5f7fb"
TEXT_MUTED = "#98a5b3"
TEXT_FAINT = "#73808f"
ACCENT_PRIMARY = "#7eb6ff"
ACCENT_WARM = "#ffd3a1"


class App(ctk.CTk):
    """
    메인 윈도우. App.tsx 대응.
    3단계 UI: ① URL 입력 → ② 곡 목록 → ③ 폴더 선택 + 다운로드
    """

    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Suno AI Music Downloader")
        self.geometry("860x720")
        self.minsize(840, 580)

        self.settings = load_settings()
        self._clips: list[PlaylistClip] = []
        self._playlist: Playlist | None = None
        self._clip_selection: dict[str, ctk.BooleanVar] = {}
        self._stop_event = threading.Event()
        self._fonts = self._init_fonts()

        # 초기 저장 폴더: 설정에 있으면 사용, 없으면 음악 폴더
        default_folder = self.settings.save_folder or str(Path.home() / "Music")
        self._save_folder = ctk.StringVar(value=default_folder)

        self._build_ui()

    # ── UI 구성 ────────────────────────────────────────────

    def _init_fonts(self):
        available = set(tkfont.families())

        def pick(*names: str) -> str:
            for name in names:
                if name in available:
                    return name
            return "Arial"

        sans = pick("Pretendard", "SUIT", "Noto Sans KR", "Malgun Gothic", "Segoe UI")
        mono = pick("JetBrains Mono", "Consolas", "Courier New")
        return {
            "title": ctk.CTkFont(family=sans, size=16, weight="bold"),
            "section": ctk.CTkFont(family=sans, size=15, weight="bold"),
            "body": ctk.CTkFont(family=sans, size=13),
            "body_bold": ctk.CTkFont(family=sans, size=13, weight="bold"),
            "small": ctk.CTkFont(family=sans, size=11),
            "mono": ctk.CTkFont(family=mono, size=12),
            "badge": ctk.CTkFont(family=sans, size=13, weight="bold"),
            "header_icon": ctk.CTkFont(family=sans, size=20, weight="bold"),
            "hero": ctk.CTkFont(family=sans, size=12),
        }

    def _build_ui(self):
        self.configure(fg_color=BG_COLOR)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()

        top = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        top.grid(row=1, column=0, sticky="ew", padx=18, pady=(16, 10))
        top.grid_columnconfigure(1, weight=1)

        self._section_badge(top, "1", row=0, col=0)
        ctk.CTkLabel(top, text="Paste playlist link", font=self._fonts["section"], text_color=TEXT_MAIN).grid(
            row=0, column=1, sticky="w", padx=6, pady=(16, 0)
        )
        self._settings_btn = ctk.CTkButton(
            top,
            text="⚙",
            width=40,
            height=36,
            corner_radius=12,
            command=self._open_settings,
            font=self._fonts["body_bold"],
            fg_color=PANEL_ALT,
            hover_color="#2a3440",
            border_width=1,
            border_color=BORDER_COLOR,
            text_color=ACCENT_PRIMARY,
        )
        self._settings_btn.grid(row=0, column=2, padx=(4, 16), pady=(14, 0))

        url_row = ctk.CTkFrame(top, fg_color="transparent")
        url_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(14, 16))
        url_row.grid_columnconfigure(0, weight=1)

        self._url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="https://suno.com/playlist/...",
            height=46,
            corner_radius=12,
            font=self._fonts["body"],
            fg_color=INPUT_COLOR,
            border_color=BORDER_COLOR,
            text_color=TEXT_MAIN,
        )
        self._url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._fetch_btn = ctk.CTkButton(
            url_row,
            text="Get playlist songs",
            width=150,
            height=46,
            corner_radius=12,
            command=self._on_fetch,
            font=self._fonts["body_bold"],
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
        )
        self._fetch_btn.grid(row=0, column=1)

        mid_label = ctk.CTkFrame(self, fg_color="transparent")
        mid_label.grid(row=2, column=0, sticky="ew", padx=18, pady=(8, 0))
        mid_label.grid_columnconfigure(1, weight=1)
        mid_label.grid_columnconfigure(2, weight=0)
        self._section_badge(mid_label, "2", row=0, col=0)
        self._playlist_label = ctk.CTkLabel(
            mid_label, text="Review songs", font=self._fonts["section"], text_color=TEXT_MAIN
        )
        self._playlist_label.grid(row=0, column=1, sticky="w", padx=6)
        self._selection_btn = ctk.CTkButton(
            mid_label,
            text="Select all",
            width=96,
            height=32,
            corner_radius=10,
            font=self._fonts["small"],
            fg_color=PANEL_ALT,
            hover_color="#2a3440",
            text_color=ACCENT_PRIMARY,
            command=self._toggle_selection_mode,
            state="disabled",
        )
        self._selection_btn.grid(row=0, column=2, sticky="e")

        self._table_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        self._table_frame.grid(row=3, column=0, sticky="nsew", padx=18, pady=(8, 10))
        self._build_table_header()

        bot = ctk.CTkFrame(self, fg_color=PANEL_COLOR, corner_radius=18, border_width=1, border_color=BORDER_COLOR)
        bot.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 18))
        bot.grid_columnconfigure(0, weight=0)
        bot.grid_columnconfigure(1, weight=1)

        self._section_badge(bot, "3", row=0, col=0)
        ctk.CTkLabel(bot, text="Select folder and download", font=self._fonts["section"], text_color=TEXT_MAIN).grid(
            row=0, column=1, sticky="w", padx=6, pady=(16, 0)
        )

        folder_row = ctk.CTkFrame(bot, fg_color="transparent")
        folder_row.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(14, 12))
        folder_row.grid_columnconfigure(0, weight=1)

        self._folder_entry = ctk.CTkEntry(
            folder_row,
            textvariable=self._save_folder,
            state="readonly",
            height=46,
            corner_radius=12,
            font=self._fonts["body"],
            fg_color=INPUT_COLOR,
            border_color=BORDER_COLOR,
            text_color=TEXT_MAIN,
        )
        self._folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._folder_entry.bind("<Button-1>", lambda _: self._select_folder())

        self._dl_btn = ctk.CTkButton(
            folder_row,
            text="Download songs",
            width=144,
            height=46,
            corner_radius=12,
            command=self._on_download,
            state="disabled",
            font=self._fonts["body_bold"],
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
        )
        self._dl_btn.grid(row=0, column=1)

        self._progress_bar = ctk.CTkProgressBar(
            bot,
            fg_color=INPUT_COLOR,
            progress_color=ACCENT_PRIMARY,
        )
        self._progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", padx=16, pady=(0, 8))
        self._progress_bar.set(0)
        self._progress_bar.grid_remove()

        self._status_label = ctk.CTkLabel(bot, text="", text_color=TEXT_FAINT, font=self._fonts["small"])
        self._status_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 14))

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=HEADER_COLOR, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(header, fg_color=HEADER_COLOR, corner_radius=0, height=52)
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.grid_columnconfigure(0, weight=1)

        title_group = ctk.CTkFrame(title_row, fg_color="transparent")
        title_group.grid(row=0, column=0, pady=(10, 8))

        ctk.CTkLabel(
            title_group,
            text="◎",
            font=self._fonts["header_icon"],
            text_color=ACCENT_PRIMARY,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            title_group,
            text="Suno",
            font=self._fonts["title"],
            text_color=ACCENT_WARM,
        ).pack(side="left")
        ctk.CTkLabel(
            title_group,
            text=" AI Music Downloader",
            font=self._fonts["title"],
            text_color=TEXT_MAIN,
        ).pack(side="left")

        divider = ctk.CTkFrame(header, fg_color=BORDER_COLOR, corner_radius=0, height=1)
        divider.grid(row=1, column=0, sticky="ew")

    def _section_badge(self, parent, number: str, row: int, col: int):
        badge = ctk.CTkLabel(
            parent, text=number, width=28, height=28,
            fg_color=BUTTON_COLOR, corner_radius=14,
            font=self._fonts["badge"], text_color="white"
        )
        badge.grid(row=row, column=col, padx=(16, 4), pady=(14, 0))

    def _build_table_header(self):
        headers = [("Pick", "w"), ("Title", "w"), ("Length", "e"), ("Status", "e")]
        for col, (text, anchor) in enumerate(headers):
            ctk.CTkLabel(
                self._table_frame,
                text=text,
                font=self._fonts["body_bold"],
                anchor=anchor,
                text_color=TEXT_MUTED,
            ).grid(row=0, column=col, sticky=anchor, padx=12, pady=(12, 12))
        self._table_frame.grid_columnconfigure(1, weight=1)

    # ── 이벤트 핸들러 ───────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self, self.settings)
        self.wait_window(dlg)
        if dlg.result:
            self.settings = dlg.result

    def _select_folder(self):
        folder = filedialog.askdirectory(title="저장 폴더 선택")
        if folder:
            self._save_folder.set(folder)
            self.settings.save_folder = folder
            save_settings(self.settings)

    def _on_fetch(self):
        url = self._url_entry.get().strip()
        if not url:
            self._set_status("URL을 입력해 주세요.", color="orange")
            return
        self._set_busy(True, "Loading playlist...")
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url: str):
        try:
            playlist, clips = get_songs_from_playlist(url)
            self.after(0, self._on_fetch_done, playlist, clips)
        except Exception as e:
            self.after(0, self._on_fetch_error, str(e))

    def _on_fetch_done(self, playlist: Playlist, clips: list[PlaylistClip]):
        self._playlist = playlist
        self._clips = clips
        self._clip_selection = {
            clip.id: ctk.BooleanVar(value=True)
            for clip in clips
        }
        self._playlist_label.configure(
            text=f"Review songs  -  {playlist.name} ({len(clips)})"
        )
        self._rebuild_table()
        self._set_busy(False)
        self._dl_btn.configure(state="normal")
        self._selection_btn.configure(state="normal")
        self._refresh_selection_button()
        self._set_status(f"{len(clips)} songs loaded.", color="#4ed19a")

    def _on_fetch_error(self, msg: str):
        self._playlist = None
        self._clips = []
        self._clip_selection = {}
        self._playlist_label.configure(text="Review songs")
        self._rebuild_table()
        self._set_busy(False)
        self._selection_btn.configure(state="disabled", text="Select all")
        self._set_status(f"오류: {msg}", color="#e74c3c")

    def _on_download(self):
        if not self._clips or not self._playlist:
            return
        selected_clips = self._get_selected_clips()
        if not selected_clips:
            self._set_status("Select at least one song.", color="#f07a78")
            return
        self._stop_event.clear()
        self._set_busy(True, "Downloading songs...")
        self._progress_bar.set(0)
        self._progress_bar.grid()

        for clip in selected_clips:
            clip.status = ClipStatus.NONE
        self._rebuild_table()

        threading.Thread(target=self._download_worker, args=(selected_clips,), daemon=True).start()

    def _download_worker(self, selected_clips: list[PlaylistClip]):
        download_playlist(
            playlist=self._playlist,
            clips=selected_clips,
            save_folder=self._save_folder.get(),
            settings=self.settings,
            on_status=lambda clip_id, status: self.after(0, self._update_clip_status, clip_id, status),
            on_progress=lambda done, total: self.after(0, self._update_progress, done, total),
            on_done=lambda ok: self.after(0, self._on_download_done, ok),
            stop_event=self._stop_event,
        )

    def _on_download_done(self, ok: bool):
        self._set_busy(False)
        self._progress_bar.set(1)
        if ok:
            self._set_status("Download complete.", color="#4ed19a")
        else:
            self._set_status("Download failed.", color="#f07a78")
        self.after(3000, self._progress_bar.grid_remove)

    # ── 상태 업데이트 ────────────────────────────────────────

    def _update_clip_status(self, clip_id: str, status: ClipStatus):
        """updateClipStatus() + scrollToRow() 대응."""
        for clip in self._clips:
            if clip.id == clip_id:
                clip.status = status
                break
        self._refresh_status_cell(clip_id, status)

    def _update_progress(self, done: int, total: int):
        """completedItems useEffect 대응."""
        pct = done / total if total else 0
        self._progress_bar.set(pct)
        self._set_status(f"Downloading... {done}/{total}")

    def _set_busy(self, busy: bool, msg: str = ""):
        state = "disabled" if busy else "normal"
        self._fetch_btn.configure(state=state)
        self._url_entry.configure(state="disabled" if busy else "normal")
        self._selection_btn.configure(state="disabled" if busy or not self._clips else "normal")
        if not busy:
            self._dl_btn.configure(state="normal" if self._get_selected_clips() else "disabled")
        else:
            self._dl_btn.configure(state="disabled")
        if msg:
            self._set_status(msg)

    def _set_status(self, msg: str, color: str = "gray60"):
        self._status_label.configure(text=msg, text_color=color)

    # ── 테이블 렌더링 ────────────────────────────────────────

    def _rebuild_table(self):
        for widget in self._table_frame.winfo_children():
            widget.destroy()
        self._build_table_header()
        self._row_status_labels: dict[str, ctk.CTkLabel] = {}

        for i, clip in enumerate(self._clips, start=1):
            row = (i * 2) - 1
            sym, color = STATUS_SYMBOLS[clip.status]
            selected_var = self._clip_selection.get(clip.id)

            checkbox = ctk.CTkCheckBox(
                self._table_frame,
                text="",
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=6,
                border_width=2,
                fg_color=BUTTON_COLOR,
                hover_color=BUTTON_HOVER,
                border_color=BORDER_COLOR,
                variable=selected_var,
                command=self._on_selection_changed,
            )
            checkbox.grid(row=row, column=0, sticky="w", padx=(12, 4))

            title_frame = ctk.CTkFrame(self._table_frame, fg_color="transparent")
            title_frame.grid(row=row, column=1, sticky="ew", padx=(8, 8), pady=(0, 2))
            ctk.CTkLabel(
                title_frame, text=clip.title, anchor="w",
                font=self._fonts["body_bold"], wraplength=520, text_color=TEXT_MAIN
            ).pack(anchor="w")

            ctk.CTkLabel(
                self._table_frame,
                text=format_duration(clip.duration),
                width=70, anchor="e", font=self._fonts["mono"], text_color=TEXT_MAIN
            ).grid(row=row, column=2, sticky="e", padx=12)

            status_lbl = ctk.CTkLabel(
                self._table_frame, text=sym, width=60,
                text_color=color, font=self._fonts["small"], anchor="e"
            )
            status_lbl.grid(row=row, column=3, sticky="e", padx=(4, 12))
            self._row_status_labels[clip.id] = status_lbl

            divider = ctk.CTkFrame(self._table_frame, height=1, fg_color="#24303c")
            divider.grid(row=row + 1, column=0, columnspan=4, sticky="ew", padx=12, pady=(8, 12))

    def _refresh_status_cell(self, clip_id: str, status: ClipStatus):
        lbl = getattr(self, "_row_status_labels", {}).get(clip_id)
        if lbl:
            sym, color = STATUS_SYMBOLS[status]
            lbl.configure(text=sym, text_color=color)

    def _get_selected_clips(self) -> list[PlaylistClip]:
        return [
            clip for clip in self._clips
            if self._clip_selection.get(clip.id) and self._clip_selection[clip.id].get()
        ]

    def _on_selection_changed(self):
        self._refresh_selection_button()
        if self._clips:
            self._dl_btn.configure(state="normal" if self._get_selected_clips() else "disabled")

    def _refresh_selection_button(self):
        if not self._clips:
            self._selection_btn.configure(text="Select all")
            return
        all_selected = all(
            self._clip_selection.get(clip.id) and self._clip_selection[clip.id].get()
            for clip in self._clips
        )
        self._selection_btn.configure(text="Clear all" if all_selected else "Select all")

    def _toggle_selection_mode(self):
        if not self._clips:
            return
        all_selected = all(
            self._clip_selection.get(clip.id) and self._clip_selection[clip.id].get()
            for clip in self._clips
        )
        next_value = not all_selected
        for clip in self._clips:
            self._clip_selection[clip.id].set(next_value)
        self._on_selection_changed()
