"""
Наврядле кому-то из нерусскоговорящих ребят понадобится такого рода программа, 
поэтому все комментарии будут на русском.

Если что пусть пользуются переводчиком, кекв
"""

import os
import sys
import pathlib
from typing import Optional

import psutil

from ..enums import LogType
from ..logger import log
from .. import state

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"

APP_NAME = "YandexMusicRPC"
_LOCK_FILE = pathlib.Path.home() / f".{APP_NAME}.lock"
_LINUX_AUTOSTART_FILE = pathlib.Path.home() / ".config" / "autostart" / f"{APP_NAME}.desktop"
_WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_executable_environment() -> bool:
    if getattr(sys, "frozen", False):
        return True
    return not IS_WINDOWS


def ensure_console_mode() -> None:
    """Настройка консоли по принципу «best-effort». Актуально только для Windows; в других системах не выполняется."""
    if not IS_WINDOWS:
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        kernel32.SetConsoleMode(handle, 7)
    except Exception as e:
        log(f"Failed to set console mode: {e}", LogType.Error)


def set_console_title(title: str) -> None:
    """Задаёт заголовок окна терминала на любой системе"""
    if IS_WINDOWS:
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except Exception as e:
            log(f"Failed to set console title: {e}", LogType.Error)
    else:
        try:
            sys.stdout.write(f"\33]0;{title}\a")
            sys.stdout.flush()
        except Exception:
            pass


def wait_and_exit() -> None:
    """Останавливает цикл активности и завершает работу процесса."""
    try:
        from ..presence import Presence

        Presence.stop()
    except Exception:
        pass

    log("Application is shutting down.")
    try:
        input("Press Enter to exit.")
    except (EOFError, OSError):
        pass
    sys.exit(0)


def is_already_running() -> bool:
    """
    Определяет, запущен ли уже другой экземпляр *этого* приложения,
    используя файл блокировки PID в домашнем каталоге пользователя.
    """
    my_pid = os.getpid()

    try:
        if _LOCK_FILE.exists():
            try:
                old_pid = int(_LOCK_FILE.read_text().strip())
            except ValueError:
                old_pid = -1

            if old_pid > 0 and old_pid != my_pid and psutil.pid_exists(old_pid):
                try:
                    proc = psutil.Process(old_pid)
                    cmdline = " ".join(proc.cmdline()).lower()
                    if "main.py" in cmdline or APP_NAME.lower() in cmdline:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        _LOCK_FILE.write_text(str(my_pid))
    except Exception as e:
        log(f"Error while checking for a running instance: {e}", LogType.Error)

    return False


def is_yandex_music_running() -> bool:
    """
    Проверяет, запущено ли само настольное приложение "Яндекс Музыка"
    """
    target_names = ["yandex", "music"]
    try:
        for proc in psutil.process_iter(["name"]):
            proc_name = (proc.info.get("name") or "").lower()
            if all(part in proc_name for part in target_names):
                return True
        return False
    except Exception as e:
        log(f"Error while checking running processes: {e}", LogType.Error)
        return False


def get_icon_path() -> Optional[pathlib.Path]:
    """Определяет путь к значку приложения с учетом различных вариантов программы."""
    try:
        if getattr(sys, "frozen", False):
            resources_path = pathlib.Path(sys._MEIPASS)
        else:
            # ymrpc/utils/platform_checks.py -> ymrpc/ -> project root
            resources_path = pathlib.Path(__file__).resolve().parent.parent.parent

        icon_path = resources_path / "assets" / "YMRPC_ico.ico"
        if icon_path.exists():
            return icon_path

        log(f"Icon not found at {icon_path}", LogType.Error)
        return None
    except Exception as e:
        log(f"Failed to determine icon path: {e}", LogType.Error)
        return None


def _launch_command() -> str:
    """Создает команду, используемую для перезапуска приложения при входе в систему."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    main_path = pathlib.Path(__file__).resolve().parent.parent.parent / "main.py"
    return f'"{sys.executable}" "{main_path}"'


def is_in_autostart() -> bool:
    """Проверяет, зарегистрировано ли приложение для автоматического запуска при входе в систему."""
    if IS_WINDOWS:
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WINDOWS_RUN_KEY) as key:
                winreg.QueryValueEx(key, APP_NAME)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            log(f"Failed to check Windows autostart: {e}", LogType.Error)
            return False
    elif IS_LINUX or IS_MACOS:
        return _LINUX_AUTOSTART_FILE.exists()

    return False


def toggle_auto_start() -> bool:
    """Включает/отключает автозапуск. Возвращает конечное состояние."""
    currently_enabled = is_in_autostart()

    if IS_WINDOWS:
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _WINDOWS_RUN_KEY, 0, winreg.KEY_ALL_ACCESS) as key:
                if currently_enabled:
                    winreg.DeleteValue(key, APP_NAME)
                else:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _launch_command())
        except Exception as e:
            log(f"Failed to toggle Windows autostart: {e}", LogType.Error)

    elif IS_LINUX or IS_MACOS:
        try:
            if currently_enabled:
                _LINUX_AUTOSTART_FILE.unlink(missing_ok=True)
            else:
                _LINUX_AUTOSTART_FILE.parent.mkdir(parents=True, exist_ok=True)
                desktop_entry = (
                    "[Desktop Entry]\n"
                    "Type=Application\n"
                    f"Name={APP_NAME}\n"
                    f"Exec={_launch_command()}\n"
                    "Terminal=false\n"
                    "X-GNOME-Autostart-enabled=true\n"
                )
                _LINUX_AUTOSTART_FILE.write_text(desktop_entry)
        except Exception as e:
            log(f"Failed to toggle Linux autostart: {e}", LogType.Error)
    else:
        log("Autostart toggling is not supported on this platform.", LogType.Error)

    new_state = is_in_autostart()
    state.auto_start = new_state
    log(f"Autostart is now {'enabled' if new_state else 'disabled'}.", LogType.Update_Status)
    return new_state


def check_startup_status() -> None:
    """Обновляет значение параметра `state.auto_start`, полученное из системы, и записывает его в журнал."""
    state.auto_start = is_in_autostart()
    log(f"Autostart is currently {'enabled' if state.auto_start else 'disabled'}.")


def toggle_console(icon=None, item=None) -> None:
    """
    Показывает/скрывает окно консоли. Имеет смысл только в Windows, где
    приложение работает с реальным дескриптором окна консоли; в Linux/macOS такого
    дескриптора нет, поэтому эта функция просто информирует пользователя.
    """
    if IS_WINDOWS:
        try:
            import win32con
            import win32gui

            if state.window:
                is_visible = win32gui.IsWindowVisible(state.window)
                win32gui.ShowWindow(state.window, win32con.SW_HIDE if is_visible else win32con.SW_SHOW)
        except Exception as e:
            log(f"Failed to toggle console window: {e}", LogType.Error)
    else:
        log(
            "Showing/hiding the console window is a Windows-only feature. "
            "On Linux, minimize or close your terminal window instead.",
            LogType.Notification,
        )
