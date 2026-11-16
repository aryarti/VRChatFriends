# -*- coding: utf-8 -*-
"""Janela com dados falsos para ver a ocupação na lista (nenhuma chamada de rede)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from core import APP_NAME, font_files

AQUI = os.path.dirname(os.path.abspath(__file__))
QML_DIR = os.path.join(AQUI, "ui_qml", "qml")

AMIGOS = [
    {"id": "usr_1", "name": "Ana Pug", "status": "join me", "status_label": "Ask Me",
     "world": "The Great Pug · US", "platform": "standalonewindows", "location": "x",
     "active": "agora", "avatar": None, "icon_url": "",
     "occupants": 17, "capacity": 32, "occupants_label": "17/32"},
    {"id": "usr_2", "name": "Bia Pub", "status": "active", "status_label": "Online",
     "world": "Midnight Rooftop", "platform": "standalonewindows", "location": "x",
     "active": "agora", "avatar": None, "icon_url": "",
     "occupants": 8, "capacity": None, "occupants_label": "8"},
    {"id": "usr_3", "name": "Caio Private", "status": "active", "status_label": "Online",
     "world": "Mundo Fechado · privado · EU", "platform": "standalonewindows", "location": "x",
     "active": "agora", "avatar": None, "icon_url": "",
     "occupants": None, "capacity": None, "occupants_label": ""},
    {"id": "usr_4", "name": "Duda Web", "status": "active", "status_label": "Online",
     "world": "na web", "platform": "web", "location": "offline",
     "active": "agora", "avatar": None, "icon_url": "",
     "occupants": None, "capacity": None, "occupants_label": ""},
    {"id": "usr_5", "name": "Edu Menu", "status": "active", "status_label": "Online",
     "world": "no menu", "platform": "android", "location": "offline",
     "active": "agora", "avatar": None, "icon_url": "",
     "occupants": None, "capacity": None, "occupants_label": ""},
]


def main(segundos=45):
    app = QGuiApplication(sys.argv)
    for f in font_files():
        QFontDatabase.addApplicationFont(f)

    from ui_qml.main import Bridge

    bridge = Bridge()
    bridge._friends = AMIGOS
    bridge._count_text = "5 amigos online"
    bridge._state = "list"
    bridge._meta = "aryaah · atualizado 21:44"
    bridge._logged_in = True
    bridge._title = APP_NAME + " — aryaah"

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Main.qml")))
    if not engine.rootObjects():
        print("FALHA  Main.qml nao carregou")
        return 1
    QTimer.singleShot(segundos * 1000, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 45))
