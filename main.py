import multiprocessing
import threading

from ymrpc.constants import REPO_URL
from ymrpc.enums import LogType
from ymrpc.logger import log
from ymrpc.presence import Presence
from ymrpc.settings import get_saves_settings
from ymrpc.token_manager import Init_yaToken
from ymrpc.tray import create_tray_icon, tray_thread
from ymrpc.version_check import GetLastVersion
from ymrpc.utils import platform_checks
from ymrpc import state


def main():
    multiprocessing.freeze_support()

    try:
        if platform_checks.is_executable_environment():
            platform_checks.ensure_console_mode()

            log("Launched. Check the actual version...")
            GetLastVersion(REPO_URL)

            get_saves_settings(True)

            if platform_checks.is_already_running():
                log("YandexMusicRPC is already running.", LogType.Error)
                platform_checks.wait_and_exit()
                return

            state.mainMenu = create_tray_icon()
            icon_thread = threading.Thread(target=tray_thread, args=(state.mainMenu,))
            icon_thread.daemon = True
            icon_thread.start()

            platform_checks.set_console_title("YandexMusicRPC - Console")
            platform_checks.check_startup_status()
        else:
            get_saves_settings(True)
            log("Launched without minimizing to tray and other and other gui functions")

        Init_yaToken(False)

        Presence.start()

    except KeyboardInterrupt:
        log("Keyboard interrupt received, stopping...")
        Presence.stop()


if __name__ == "__main__":
    main()
