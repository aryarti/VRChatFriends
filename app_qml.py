# -*- coding: utf-8 -*-
"""Ponto de entrada do executável (versão QML).

Fica na raiz de propósito: assim `core/`, `assets/` e `ui_qml/` são encontrados pelo
mesmo esquema no código-fonte e dentro do PyInstaller (sys._MEIPASS).
"""

import os
import sys


def raiz_do_app():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


if raiz_do_app() not in sys.path:
    sys.path.insert(0, raiz_do_app())

from ui_qml.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
