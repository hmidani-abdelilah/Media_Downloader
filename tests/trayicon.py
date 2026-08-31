# sudo apt install libgirepository1.0-dev libcairo2-dev pkg-config python3-dev libgirepository-2.0-dev
# pip install --upgrade pip 
# pip install pygobject

import os

os.environ["PYSTRAY_BACKEND"] = "gtk"

import pystray
from PIL import Image
from utils import resource_path

# Le reste de votre code corrigé (sans thread sur icon.run)
image = resource_path(os.path.join("asset", "Icon.png"))
img = Image.open(image)


def on_clicked(icon, item):
    print("Say Hello !!")


icon = pystray.Icon(
    "Abdelilah",
    img,
    menu=pystray.Menu(pystray.MenuItem("Say hello", on_clicked)),
)

icon.run()
