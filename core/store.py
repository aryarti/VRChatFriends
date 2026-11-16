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


def merge_settings(changes, drop=(), carregar=None, gravar=None):
    """Grava `changes` por cima do que ja esta no arquivo e devolve o resultado.

    Duas copias do app abertas gravavam o settings inteiro a partir da propria
    memoria: a janela que estava com a lista velha de favoritos apagava a
    estrela salva pela outra (visto em 16/11). Mesclando no arquivo, cada
    escrita responde so pelas chaves que ela realmente mudou.

    `carregar`/`gravar` existem para os testes apontarem para um arquivo
    temporario sem mexer no settings do dono.
    """
    carregar = carregar or load_settings
    gravar = gravar or save_settings
    atual = carregar()
    atual.update(changes or {})
    for chave in drop or ():
        atual.pop(chave, None)
    gravar(atual)
    return atual


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
