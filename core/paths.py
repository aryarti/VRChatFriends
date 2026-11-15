"""Caminhos, constantes de API e de sessao. Nenhuma interface aqui."""

import os

APP_NAME = "VRChat Friends"
APP_VERSION = "1.0"
API = "https://api.vrchat.cloud/api/1"
UA = "VRChatFriends/1.0 (Windows; personal-use)"

# raiz do projeto (o diretorio que contem core/, ui_qml/, assets/)
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(APP_ROOT, "assets")
ICON_FILE = os.path.join(ASSETS_DIR, "icon.ico")

DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "VRChatFriends")
SESSION_FILE = os.path.join(DATA_DIR, "session.json")
WORLD_CACHE = os.path.join(DATA_DIR, "worlds.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
LOG_FILE = os.path.join(DATA_DIR, "app.log")
AVATARS_DIR = os.path.join(DATA_DIR, "avatars")

REFRESH_SECONDS = 45
