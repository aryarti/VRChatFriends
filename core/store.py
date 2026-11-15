"""JSON em disco, configuracoes e log — infraestrutura compartilhada pelas duas UIs."""

import json
import os
import sys

from .paths import DATA_DIR, LOG_FILE, SETTINGS_FILE


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def save_json(path, data):
    """Escrita atomica: tmp + os.replace, nunca deixa arquivo pela metade."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] nao consegui salvar {path}: {exc}", file=sys.stderr)
        return False


def load_settings():
    data = load_json(SETTINGS_FILE, {})
    return data if isinstance(data, dict) else {}


def save_settings(settings):
    return save_json(SETTINGS_FILE, settings)


def attach_logging():
    """Com pythonw.exe nao existe console: joga stdout/stderr num arquivo.

    Toda UI deve chamar isto como primeira coisa do main().
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        return
    if sys.stdout is None or sys.stderr is None:
        try:
            fh = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
            if sys.stdout is None:
                sys.stdout = fh
            if sys.stderr is None:
                sys.stderr = fh
        except Exception:
            pass

    def _hook(exc_type, exc, tb):
        import traceback

        try:
            traceback.print_exception(exc_type, exc, tb, file=sys.stderr)
        except Exception:
            pass

    sys.excepthook = _hook
