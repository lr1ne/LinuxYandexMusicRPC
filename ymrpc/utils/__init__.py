import re
from typing import Optional

from ..enums import ButtonConfig, LanguageConfig


def format_duration(duration_ms: int) -> str:
    """Formats duration from milliseconds to M:SS format."""
    total_seconds = duration_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02}"


def trim_string(text: str, max_chars: int) -> str:
    """Trims and truncates a string if it exceeds max_chars."""
    return f"{text[:max_chars]}..." if len(text) > max_chars else text


def single_char(s: str) -> str:
    """Wraps a single character string in quotes."""
    return f'"{s}"' if len(s) == 1 else s


def extract_deep_link(url: str) -> Optional[str]:
    """Extracts a Yandex Music deep link from a standard web URL."""
    pattern = r"https://music.yandex.ru/album/(\d+)/track/(\d+)"
    match = re.match(pattern, url)
    if match:
        album_id, track_id = match.groups()
        share_track_path = f"album/{album_id}/track/{track_id}"
        return f"yandexmusic://{share_track_path}"
    return None


def build_buttons(url: str) -> list:
    """
    Generates a list of buttons (label and URL) based on the configured
    button_config and the provided URL.
    """
    from .. import state

    def create_button(label_en: str, label_ru: str, url_btn: str) -> dict:
        """Helper function to create a button dictionary."""
        label_lang = label_en if state.language_config == LanguageConfig.ENGLISH else label_ru
        return {"label": label_lang, "url": url_btn}

    buttons = []

    if state.button_config == ButtonConfig.YANDEX_MUSIC_WEB:
        buttons.append(create_button("Listen on Yandex Music", "Откр. в браузере", url))
    elif state.button_config == ButtonConfig.YANDEX_MUSIC_APP:
        deep_link = extract_deep_link(url)
        buttons.append(create_button("Listen on Yandex Music (in App)", "Откр. в прилож.", deep_link))
    elif state.button_config == ButtonConfig.BOTH:
        buttons.append(create_button("Listen on Yandex Music (Web)", "Откр. в браузере", url))
        deep_link = extract_deep_link(url)
        buttons.append(create_button("Listen on Yandex Music (App)", "Откр. в прилож.", deep_link))

    for button in buttons:
        label = button["label"]
        if len(label.encode("utf-8")) > 32:
            raise ValueError(f"Label '{label}' exceeds 32 bytes")

    return buttons


def blur_string(s: str) -> str:
    """Blurs a string for display purposes if it is too long."""
    return "" if s is None else (s if len(s) <= 8 else s[:4] + "*" * (len(s) - 8) + s[-4:])
