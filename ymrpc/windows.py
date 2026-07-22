import pathlib
import os
import sys
import time
from typing import Optional
import psutil
from .logger import log
from . import state
from .enums import LogType

TARGET_PROCESS_NAME = ["yandex", "music"]

def WaitAndExit() -> None:
    """
    Корректное завершение работы приложения.
    На Linux'е это, как правило, включает в себя очистку и завершение работы.
    """
    try:
        from .presence import Presence
        Presence.stop()
    except Exception:
        pass

    log("Application is shutting down. Press Enter to exit.")
    input("Press Enter to exit.")
    sys.exit(0)


def is_in_autostart() -> bool:
    """
    Проверяет, настроено ли приложение на запуск при запуске системы.
    """
    return False


def toggle_auto_start_linux() -> None:
    """
    Включает или отключает автостарт.
    Конкретная реализация зависит от целевого дистрибутива Linux и его настроек.
    """
    state.auto_start_linux = not state.auto_start_linux
    log(f"Bool auto_start_linux set state: {state.auto_start_linux}")
    # TODO: управление сервисом systemd, потом для других 


def is_already_running() -> bool:
    """
    Проверяет, запущен ли в данный момент процесс Yandex Music.
    """
    try:
        for proc in psutil.process_iter(['name']):
            proc_name = proc.info['name']
            for target in TARGET_PROCESS_NAME:
                if target in proc_name:
                    log(f"Found running process: {proc_name} (PID: {proc.pid})")
                    return True
        return False
    except Exception as e:
        log(f"Error while checking running processes: {e}", LogType.Error)
        return False

def get_icon_path() -> Optional[pathlib.Path]:
    """
    Определяет путь к значку приложения, учитывая различные варианты программы.
    """
    try:
        if getattr(sys, "frozen", False):
            resources_path = pathlib.Path(sys._MEIPASS)
        else:
            resources_path = pathlib.Path(__file__).parent

        return resources_path / "assets" / "YMRPC_ico.ico"
    except Exception as e:
        log(f"Failed to determine icon path: {e}", LogType.Error)
        return None

