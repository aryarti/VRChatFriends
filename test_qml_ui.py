# -*- coding: utf-8 -*-
"""Abre a UI QML com dados falsos para conferir popup do amigo e painel lateral.

Uso: python test_qml_ui.py [panel|popup] [segundos]
Não usa rede e não grava nada.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QMetaObject, QObject, QTimer, QUrl, Qt  # noqa: E402
from PySide6.QtGui import QFontDatabase  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtQuickControls2 import QQuickStyle  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import ui_qml.main as qm  # noqa: E402
from core import Friend, Profile  # noqa: E402
from core.paths import AVATARS_DIR  # noqa: E402

MODO = sys.argv[1] if len(sys.argv) > 1 else "panel"
SEGUNDOS = float(sys.argv[2]) if len(sys.argv) > 2 else 60

_96 = ([os.path.join(AVATARS_DIR, p) for p in sorted(os.listdir(AVATARS_DIR))
        if p.endswith("-96.png")] if os.path.isdir(AVATARS_DIR) else [])
_28 = ([os.path.join(AVATARS_DIR, p) for p in sorted(os.listdir(AVATARS_DIR))
        if p.endswith("-28.png")] if os.path.isdir(AVATARS_DIR) else [])

AMIGOS = [
    Friend(id="usr_a", name="Yuno-Vini", status="join me", world="fora do jogo",
           location="offline", avatar=_28[0] if _28 else None),
    Friend(id="usr_b", name="karu_212", status="ask me", world="mundo privado",
           location="private:x", avatar=_28[1] if len(_28) > 1 else None),
    Friend(id="usr_c", name="Bia Teste", status="active", world="fora do jogo",
           location="offline", avatar=_28[2] if len(_28) > 2 else None),
]

PERFIL_AMIGO = Profile(
    id="usr_a", name="Yuno-Vini", status="join me",
    status_description="bora jogar? tô no mundo da praia",
    pronouns="ele/dele", platform="standalonewindows", world="Furry Hangout · público",
    joined="22/08/2023", last_login="hoje 17:31",
    languages=["Português", "Inglês", "Espanhol"], trust="Veteran",
    note="Conheci em uma festa da chaos na praia",
    avatar=_96[0] if _96 else None,
    profile_url="https://vrchat.com/home/user/usr_a",
)
PERFIL_MEU = Profile(
    id="usr_me", name="aryaah", status="active", pronouns="any",
    platform="standalonewindows", joined="14/04/2023", last_login="hoje 18:48",
    languages=["Português", "Inglês"], trust="Trusted",
    avatar=_96[1] if len(_96) > 1 else (_96[0] if _96 else None),
    profile_url="https://vrchat.com/home/user/usr_me",
)


class BridgeFalso(qm.Bridge):
    """Sem rede: restore/login respondem na hora e os perfis vêm fixos."""

    def _work_restore(self):
        self.service.client.me = {"displayName": "aryaah"}
        self._restored.emit(True)

    def _work_refresh(self):
        self._friendsReady.emit(AMIGOS)
        self._avatarsReady.emit(AMIGOS)

    def _work_profile(self, amigo):
        self.profileReady.emit(qm._json_perfil(PERFIL_AMIGO))

    def _work_my_profile(self, force=False):
        self.myProfileReady.emit(qm._json_perfil(PERFIL_MEU))


def main():
    QQuickStyle.setStyle("Basic")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    for arquivo in qm.font_files():
        QFontDatabase.addApplicationFont(arquivo)

    bridge = BridgeFalso()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Main.qml")))
    if not engine.rootObjects():
        print("FALHA: QML não carregou", file=sys.stderr)
        return 1

    raiz = engine.rootObjects()[0]
    bridge.start()

    def montar():
        # frameless de verdade? (flag + APIs nativas de mover/redimensionar)
        flags = int(raiz.property("flags") or 0)
        print("FramelessWindowHint ativo:", bool(flags & int(Qt.WindowType.FramelessWindowHint)))
        print("startSystemMove:", hasattr(raiz, "startSystemMove"),
              "| startSystemResize:", hasattr(raiz, "startSystemResize"))
        print("painel encontrado:", raiz.findChild(QObject, "myPanel") is not None)
        alvo = raiz.findChild(QObject, "myPanel")
        if alvo is not None and MODO == "panel":
            alvo.setProperty("expanded", True)
        pop = raiz.findChild(QObject, "popup")
        print("popup encontrado:", pop is not None)
        if pop is not None and MODO == "popup":
            import json
            pop.setProperty("titulo", "Yuno-Vini")
            pop.setProperty("perfil", json.loads(qm._json_perfil(PERFIL_AMIGO)))
            QMetaObject.invokeMethod(pop, "open", Qt.ConnectionType.DirectConnection)
            # amostra a opacidade SEM bloquear o loop (senão a animação congela)
            def amostra(ms, alvo):
                def _f():
                    carta = alvo.findChild(QObject, "card")
                    escala = carta.property("scale") if carta else None
                    print(f"  t={ms}ms  opacity={alvo.property('opacity'):.2f}"
                          f"  scale={escala if escala is not None else '-'}")
                return _f

            for ms in (0, 60, 160, 400):
                QTimer.singleShot(ms, amostra(ms, pop))
    QTimer.singleShot(1200, montar)
    QTimer.singleShot(int(SEGUNDOS * 1000), app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
