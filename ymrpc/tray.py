import webbrowser

import pystray
from PIL import Image
from yandex_music import exceptions

from .constants import REPO_URL
from .enums import LogType
from .logger import log
from .presence import Presence
from .settings import create_rpc_settings_menu
from .utils import platform_checks
from . import state


def tray_click(icon, query):
    match str(query):
        case "GitHub":
            webbrowser.open(REPO_URL, new=2)
        case "Exit":
            Presence.stop()
            icon.stop()
            if platform_checks.IS_WINDOWS and state.window:
                import win32con
                import win32gui

                win32gui.PostMessage(state.window, win32con.WM_CLOSE, 0, 0)
            else:
                import os

                os._exit(0)


def get_account_name() -> str:
    try:
        user_info = Presence.client.me.account
        account_name = user_info.display_name
        return account_name or "None"
    except exceptions.UnauthorizedError:
        return "Invalid token."
    except exceptions.NetworkError:
        return "Network error."
    except Exception:
        return "None"


def toggle_auto_start_action(icon, item):
    platform_checks.toggle_auto_start()


def update_account_name(icon, new_account_name: str):
    rpc_settings_menu = create_rpc_settings_menu()
    settings_menu = pystray.Menu(
        pystray.MenuItem(f"Logged in as - {new_account_name}", lambda: None, enabled=False),
        pystray.MenuItem("Login to account...", lambda: _login_from_tray()),
    )

    icon.menu = pystray.Menu(
        pystray.MenuItem("Hide/Show Console", platform_checks.toggle_console, default=True),
        pystray.MenuItem(
            "Start with System", toggle_auto_start_action, checked=lambda item: state.auto_start
        ),
        pystray.MenuItem("Yandex settings", settings_menu),
        pystray.MenuItem("RPC settings", rpc_settings_menu),
        pystray.MenuItem("GitHub", tray_click),
        pystray.MenuItem("Exit", tray_click),
    )


def _login_from_tray():
    from .token_manager import Init_yaToken

    Init_yaToken(True)


def create_tray_icon():
    icon_path = platform_checks.get_icon_path()
    tray_image = Image.open(icon_path) if icon_path else Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    account_name = get_account_name()
    rpc_settings_menu = create_rpc_settings_menu()

    settings_menu = pystray.Menu(
        pystray.MenuItem(f"Logged in as - {account_name}", lambda: None, enabled=False),
        pystray.MenuItem("Login to account...", lambda: _login_from_tray()),
    )

    return pystray.Icon(
        "YandexMusicRPC",
        tray_image,
        "YandexMusicRPC",
        menu=pystray.Menu(
            pystray.MenuItem("Hide/Show Console", platform_checks.toggle_console, default=True),
            pystray.MenuItem(
                "Start with System", toggle_auto_start_action, checked=lambda item: state.auto_start
            ),
            pystray.MenuItem("Yandex settings", settings_menu),
            pystray.MenuItem("RPC settings", rpc_settings_menu),
            pystray.MenuItem("GitHub", tray_click),
            pystray.MenuItem("Exit", tray_click),
        ),
    )


def tray_thread(icon):
    icon.run()
