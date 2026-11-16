# -*- coding: utf-8 -*-
"""Caminho completo com dados REAIS: bridge -> /users/{id} -> popup do QML.

Não clica com o mouse: abre o popup por código (o mesmo slot que o clique chama),
mas passa pelo bridge de verdade, com a sessão real.
Uso: python test_qml_real.py [segundos]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QMetaObject, QObject, QTimer, QUrl, Qt  # noqa: E402
from PySide6.QtGui import QFontDatabase, QIcon  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtQuickControls2 import QQuickStyle  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import ui_qml.main as qm  # noqa: E402
from core import APP_NAME  # noqa: E402

SEGUNDOS = float(sys.argv[1]) if len(sys.argv) > 1 else 120


def main():
    QQuickStyle.setStyle("Basic")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    for arquivo in qm.font_files():
        QFontDatabase.addApplicationFont(arquivo)
    if os.path.exists(qm.ICON_FILE):
        app.setWindowIcon(QIcon(qm.ICON_FILE))

    bridge = qm.Bridge()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Main.qml")))
    if not engine.rootObjects():
        print("FALHA: QML não carregou", file=sys.stderr)
        return 1
    raiz = engine.rootObjects()[0]
    bridge.start()

    def abrir():
        pop = raiz.findChild(QObject, "popup")
        if not pop or not bridge._friends:
            print("FALHA: popup ou lista vazia")
            return
        primeiro = bridge._friends[0]
        print("abrindo perfil real de:", primeiro["name"])
        pop.setProperty("titulo", primeiro["name"])
        QMetaObject.invokeMethod(pop, "open", Qt.ConnectionType.DirectConnection)
        bridge.requestProfile(primeiro["id"])

    def conferir():
        pop = raiz.findChild(QObject, "popup")
        perfil = pop.property("perfil") if pop else None
        nome = (perfil or {}).get("name") if isinstance(perfil, dict) else None
        print("perfil recebido:", nome or perfil)

    QTimer.singleShot(2500, abrir)
    QTimer.singleShot(4500, conferir)
    QTimer.singleShot(int(SEGUNDOS * 1000), app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
