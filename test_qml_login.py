# -*- coding: utf-8 -*-
"""Abre a tela de LOGIN do QML com dados falsos (sem rede), para conferir visual."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

import ui_qml.main as qm

QQuickStyle.setStyle("Basic")
app = QApplication(sys.argv)
bridge = qm.Bridge()
bridge._last_user = "usuario_teste"   # só preenche o campo
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("bridge", bridge)
engine.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Main.qml")))
if not engine.rootObjects():
    print("FALHA ao carregar")
    sys.exit(1)
QTimer.singleShot(int(float(sys.argv[1] if len(sys.argv) > 1 else 6) * 1000), app.quit)
app.exec()
print("ok login qml")
