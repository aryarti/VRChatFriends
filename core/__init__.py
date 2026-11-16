"""Core do VRChat Friends: dados, API e formatacao. Nenhuma interface aqui.

Regra da pasta: nada neste diretorio pode importar tkinter, PySide6 ou QML.
Se precisar de algo da interface, o objeto vai como parametro.
"""

from .fonts import FAMILY, FAMILY_SEMIBOLD, font_files
from .formatting import (
    METHOD_LABELS,
    PLATFORM_LABELS,
    STATUS_DESCRIPTION_MAX,
    STATUS_LABELS,
    STATUS_ORDER,
    describe_location,
    hint_for,
    humanize_delta,
    humanize_epoch,
    platform_label,
)
from .models import Friend, Profile, Session, sort_friends
from .paths import (
    APP_NAME,
    APP_ROOT,
    APP_VERSION,
    DATA_DIR,
    ICON_FILE,
    REFRESH_SECONDS,
    RETRY_SECONDS,
    avatar_cache_path,
)
from . import alerts, favorites
from .sorting import (
    COLUMNS as SORT_COLUMNS,
    DEFAULT_COLUMN as SORT_DEFAULT_COLUMN,
    DEFAULT_DIRECTION as SORT_DEFAULT_DIRECTION,
    normalize as sort_normalize,
    normalize_choice as sort_choice,
    sort_friends as sort_by_column,
)
from .service import ApiError, VRChatService
from .store import (
    attach_logging,
    load_json,
    load_settings,
    merge_settings,
    save_json,
    save_settings,
)
from .vrchat import VRChatClient

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_ROOT",
    "DATA_DIR",
    "ICON_FILE",
    "REFRESH_SECONDS",
    "RETRY_SECONDS",
    "STATUS_DESCRIPTION_MAX",
    "SORT_COLUMNS",
    "SORT_DEFAULT_COLUMN",
    "SORT_DEFAULT_DIRECTION",
    "sort_by_column",
    "sort_choice",
    "sort_normalize",
    "humanize_epoch",
    "avatar_cache_path",
    "alerts",
    "favorites",
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
    "merge_settings",
    "save_json",
    "save_settings",
    "sort_friends",
]
