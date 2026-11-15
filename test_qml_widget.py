# -*- coding: utf-8 -*-
"""Checa o widget flutuante: janela própria, sem moldura, sempre no topo, show/hide."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QObject, QTimer, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

AQUI = os.path.dirname(os.path.abspath(__file__))
QML_DIR = os.path.join(AQUI, "ui_qml", "qml")


def main(espera=8):
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    from ui_qml.main import Bridge

    bridge = Bridge()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Widget.qml")))
    if not engine.rootObjects():
        print("FALHA  Widget.qml não carregou")
        return 1
    w = engine.rootObjects()[0]

    def checar():
        flags = w.flags()
        sem_moldura = bool(flags & Qt.FramelessWindowHint)
        no_topo = bool(flags & Qt.WindowStaysOnTopHint)
        ferramenta = bool(flags & Qt.Tool)
        print(("OK  " if sem_moldura else "FALHA") + "  sem moldura")
        print(("OK  " if no_topo else "FALHA") + "  sempre no topo")
        print(("OK  " if ferramenta else "FALHA") + "  janela de ferramenta (fora da barra de tarefas)")
        print(f"  tamanho: {w.width()}x{w.height()}")

        # começa escondido (setting padrão) e aparece com widgetAberto
        antes = w.isVisible()
        bridge.setWidgetAberto(True)

        def depois_de_abrir():
            aberto = w.isVisible()
            print(f"  visível antes={antes} depois={aberto}")
            print(("OK  " if (not antes and aberto) else "FALHA")
                  + "  abre e fecha pelo bridge")
            bridge.setWidgetAberto(False)

            def depois_de_fechar():
                print(("OK  " if not w.isVisible() else "FALHA") + "  esconde ao fechar")
                print("  posição salva:", bridge.settings.get("widget_pos"))
                app.quit()

            QTimer.singleShot(300, depois_de_fechar)

        QTimer.singleShot(300, depois_de_abrir)

    QTimer.singleShot(1200, checar)
    QTimer.singleShot(espera * 1000, app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 8))
