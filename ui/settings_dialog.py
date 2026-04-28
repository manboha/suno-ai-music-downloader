import customtkinter as ctk
import tkinter.font as tkfont

from services.settings import Settings, save_settings

BG_COLOR = "#14181d"
PANEL_COLOR = "#1b2128"
PANEL_ALT = "#202832"
BORDER_COLOR = "#2a333d"
INPUT_COLOR = "#11161c"
BUTTON_COLOR = "#4f8cff"
BUTTON_HOVER = "#72a4ff"
BUTTON_TEXT = "#f7fbff"
TEXT_MAIN = "#f5f7fb"
TEXT_MUTED = "#98a5b3"
ACCENT_PRIMARY = "#7eb6ff"
ACCENT_WARM = "#ffd3a1"


class SettingsDialog(ctk.CTkToplevel):
    """
    설정 다이얼로그. OptionsModal.tsx 대응.
    파일명 형식 / 덮어쓰기 / 앨범아트 임베드 설정.
    """

    TEMPLATES = ["{trackno} - {name}", "{trackno}. {name}", "{name}"]

    def __init__(self, parent, settings: Settings):
        super().__init__(parent)
        self.settings = settings
        self.result: Settings | None = None
        self._fonts = self._init_fonts()

        self.title("Settings")
        self.geometry("460x430")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)
        self.grab_set()

        self._build()
        self._load_values()

    def _init_fonts(self):
        available = set(tkfont.families())

        def pick(*names: str) -> str:
            for name in names:
                if name in available:
                    return name
            return "Arial"

        sans = pick("Pretendard", "SUIT", "Noto Sans KR", "Malgun Gothic", "Segoe UI")
        return {
            "title": ctk.CTkFont(family=sans, size=16, weight="bold"),
            "label": ctk.CTkFont(family=sans, size=13, weight="bold"),
            "body": ctk.CTkFont(family=sans, size=13),
            "button": ctk.CTkFont(family=sans, size=13, weight="bold"),
            "eyebrow": ctk.CTkFont(family=sans, size=11, weight="bold"),
        }

    def _build(self):
        body = ctk.CTkFrame(
            self,
            fg_color=PANEL_COLOR,
            corner_radius=18,
            border_width=1,
            border_color=BORDER_COLOR,
        )
        body.pack(fill="both", expand=True, padx=14, pady=14)

        header = ctk.CTkFrame(body, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 4))

        ctk.CTkLabel(
            header,
            text="◎ SETTINGS",
            anchor="w",
            font=self._fonts["eyebrow"],
            text_color=ACCENT_PRIMARY,
        ).pack(fill="x")
        ctk.CTkLabel(
            header,
            text="Suno AI Music Downloader",
            anchor="w",
            font=self._fonts["title"],
            text_color=ACCENT_WARM,
        ).pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(
            header,
            text="Settings",
            anchor="w",
            font=self._fonts["body"],
            text_color=TEXT_MUTED,
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            body,
            text="Filename format",
            anchor="w",
            font=self._fonts["label"],
            text_color=TEXT_MAIN,
        ).pack(fill="x", padx=18, pady=(0, 6))
        self.template_var = ctk.StringVar()
        self.template_combo = ctk.CTkComboBox(
            body,
            values=self.TEMPLATES,
            variable=self.template_var,
            state="readonly",
            height=44,
            corner_radius=12,
            font=self._fonts["body"],
            dropdown_font=self._fonts["body"],
            fg_color=INPUT_COLOR,
            border_color=BORDER_COLOR,
            button_color=PANEL_ALT,
            button_hover_color="#2a3440",
            text_color=TEXT_MAIN,
        )
        self.template_combo.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(
            body,
            text="Overwrite existing files",
            anchor="w",
            font=self._fonts["label"],
            text_color=TEXT_MAIN,
        ).pack(fill="x", padx=18, pady=(0, 6))
        self.overwrite_var = ctk.StringVar()
        self.overwrite_combo = ctk.CTkComboBox(
            body,
            values=["False - Skip existing files", "True - Overwrite files"],
            variable=self.overwrite_var,
            state="readonly",
            height=44,
            corner_radius=12,
            font=self._fonts["body"],
            dropdown_font=self._fonts["body"],
            fg_color=INPUT_COLOR,
            border_color=BORDER_COLOR,
            button_color=PANEL_ALT,
            button_hover_color="#2a3440",
            text_color=TEXT_MAIN,
        )
        self.overwrite_combo.pack(fill="x", padx=18, pady=(0, 12))

        ctk.CTkLabel(
            body,
            text="Embed album art into MP3",
            anchor="w",
            font=self._fonts["label"],
            text_color=TEXT_MAIN,
        ).pack(fill="x", padx=18, pady=(0, 6))
        self.embed_var = ctk.StringVar()
        self.embed_combo = ctk.CTkComboBox(
            body,
            values=["True - Download and embed artwork", "False - Ignore artwork"],
            variable=self.embed_var,
            state="readonly",
            height=44,
            corner_radius=12,
            font=self._fonts["body"],
            dropdown_font=self._fonts["body"],
            fg_color=INPUT_COLOR,
            border_color=BORDER_COLOR,
            button_color=PANEL_ALT,
            button_hover_color="#2a3440",
            text_color=TEXT_MAIN,
        )
        self.embed_combo.pack(fill="x", padx=18, pady=(0, 18))

        btn_frame = ctk.CTkFrame(body, fg_color="transparent")
        btn_frame.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=self._save_and_close,
            height=44,
            width=132,
            corner_radius=12,
            font=self._fonts["button"],
            fg_color=BUTTON_COLOR,
            hover_color=BUTTON_HOVER,
            text_color=BUTTON_TEXT,
        ).pack(side="right")

    def _load_values(self):
        self.template_var.set(self.settings.name_template)
        self.overwrite_var.set(
            "True - Overwrite files" if self.settings.overwrite_files else "False - Skip existing files"
        )
        self.embed_var.set(
            "True - Download and embed artwork" if self.settings.embed_images else "False - Ignore artwork"
        )

    def _save_and_close(self):
        self.settings.name_template = self.template_var.get()
        self.settings.overwrite_files = self.overwrite_var.get().startswith("True")
        self.settings.embed_images = self.embed_var.get().startswith("True")
        save_settings(self.settings)
        self.result = self.settings
        self.destroy()
