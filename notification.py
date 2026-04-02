import platform
import os
import subprocess
import threading
import asyncio
from utils import resource_path # لمعالجة مسارات الملفات بشكل صحيح


class Notifier:
    def notification(self):
        system = platform.system()
        icon_path_ico =resource_path("asset/Icon.ico")
        icon_path_png = resource_path("asset/Icon.png")
        
        if system == "Windows":
            try:
                from winotify import Notification
                toast = Notification(
                    app_id="Media Downloader",
                    title="Download Complete",
                    msg="Your video is ready!",
                    icon=icon_path_ico
                )
                threading.Thread(target=toast.show, daemon=True).start()
            except ImportError:
                print("winotify n'est pas installé.")

        elif system in ["Linux", "Darwin"]:
            # Priorité à notify-send (souvent présent par défaut sur Linux) sudo apt install libnotify-bin
            notify_send_exists = subprocess.run(["which", "notify-send"], capture_output=True).returncode == 0
            
            if notify_send_exists:
                subprocess.run([
                    "notify-send", "Download Complete", "Your video is ready!",
                    "-i", icon_path_png
                ])
            else:
                # Alternative avec desktop-notifier
                try:
                    from desktop_notifier import DesktopNotifier
                    notifier = DesktopNotifier(app_name="Media Downloader")
                    
                    async def send_notif():
                        await notifier.send(title="Download Complete", message="Your video is ready!")
                    
                    # On lance l'async de manière sécurisée
                    threading.Thread(target=lambda: asyncio.run(send_notif()), daemon=True).start()
                except ImportError:
                    print("Aucun système de notification trouvé.")
