"""Familia Inter embarcada: onde estao os arquivos e como as UIs a chamam.

Aqui NAO se importa toolkit nenhum — so se lista o que existe em assets/fonts.
Quem carrega e cada UI (GDI privado no Tk, QFontDatabase no Qt).
"""

import os

from .paths import ASSETS_DIR

FONT_DIR = os.path.join(ASSETS_DIR, "fonts")

# nomes reais que GDI e Qt reportam para os estaticos 18pt (medidos, nao supostos)
FAMILY = "Inter 18pt"
FAMILY_SEMIBOLD = "Inter 18pt SemiBold"
FALLBACK = "Segoe UI"
FALLBACK_SEMIBOLD = "Segoe UI Semibold"


def font_files():
    """TTFs da familia, em ordem estavel (Regular antes de Bold)."""
    if not os.path.isdir(FONT_DIR):
        return []
    return [
        os.path.join(FONT_DIR, nome)
        for nome in sorted(os.listdir(FONT_DIR))
        if nome.lower().endswith(".ttf")
    ]
