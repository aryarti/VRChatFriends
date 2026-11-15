# -*- coding: utf-8 -*-
"""Abre a janela com o painel do meu perfil expandido (só leitura) para conferir."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from core import APP_NAME, font_files

AQUI = os.path.dirname(os.path.abspath(__file__))
QML_DIR = os.path.join(AQUI, "ui_qml", "qml")


def main(segundos=40):
    app = QGuiApplication(sys.argv)
    for f in font_files():
        QFontDatabase.addApplicationFont(f)

    from ui_qml.main import Bridge

    bridge = Bridge()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Main.qml")))
    janela = engine.rootObjects()[0]

    bridge.start()   # restaura sessão e busca a lista (como o app real)

    def abrir():
        bridge.requestMyProfile()
        QTimer.singleShot(1500, expandir)

    def expandir():
        painel = janela.findChild(QObject, "myPanel")
        if painel is not None:
            painel.setProperty("expanded", True)
        print("painel aberto:", painel is not None)

    QTimer.singleShot(2500, abrir)
    QTimer.singleShot(segundos * 1000, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 40))
