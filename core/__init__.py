"""Core do VRChat Friends: dados, API e formatacao. Nenhuma interface aqui.

Regra da pasta: nada neste diretorio pode importar PySide6, QML ou qualquer toolkit.
Se precisar de algo da interface, o objeto vai como parametro.
"""

from .fonts import FAMILY, FAMILY_SEMIBOLD, font_files
from .formatting import (
    METHOD_LABELS,
    PLATFORM_LABELS,
    STATUS_LABELS,
    STATUS_ORDER,
    describe_location,
    hint_for,
    humanize_delta,
    platform_label,
)
from .models import Friend, Profile, Session, sort_friends
from .paths import APP_NAME, APP_ROOT, APP_VERSION, ICON_FILE, REFRESH_SECONDS
from .service import ApiError, VRChatService
from .store import attach_logging, load_json, load_settings, save_json, save_settings
from .vrchat import VRChatClient

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_ROOT",
    "ICON_FILE",
    "REFRESH_SECONDS",
    "Friend",
    "Profile",
    "Session",
    "VRChatClient",
    "ApiError",
    "VRChatService",
    "METHOD_LABELS",
    "PLATFORM_LABELS",
    "STATUS_LABELS",
    "STATUS_ORDER",
    "attach_logging",
    "FAMILY",
    "FAMILY_SEMIBOLD",
    "describe_location",
    "font_files",
    "hint_for",
    "platform_label",
    "humanize_delta",
    "load_json",
    "load_settings",
    "save_json",
    "save_settings",
    "sort_friends",
]
