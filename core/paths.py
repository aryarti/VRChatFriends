"""Caminhos, constantes de API e de sessao. Nenhuma interface aqui."""

import os

APP_NAME = "VRChat Friends"
APP_VERSION = "1.1.0"
API = "https://api.vrchat.cloud/api/1"
UA = "VRChatDesktopFriends/2.0 (Windows; personal-use; read-only)"

# raiz do projeto (o diretorio que contem core/, ui_tkinter/, ui_qml/)
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
# depois de uma falha o app tenta de novo mais cedo do que o ciclo normal
RETRY_SECONDS = 15


def avatar_cache_path(user_id, size):
    """Caminho do PNG redondo já baixado — sem rede. '' quando não existe."""
    if not user_id:
        return ""
    caminho = os.path.join(AVATARS_DIR, f"{user_id}-{int(size)}.png")
    return caminho if os.path.exists(caminho) else ""
