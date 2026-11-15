# -*- coding: utf-8 -*-
"""Carrega o QML em modo offscreen e falha se houver erro de tipo/binding.

Não abre janela nem usa rede: injeta um bridge com dados falsos.
Uso: python test_qml.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

import ui_qml.main as qm

# ---- perfil -> JSON do QML (o que o popup e o painel consomem)
import json  # noqa: E402

from core import Profile  # noqa: E402

_perfil = Profile(id="usr_1", name="Yuno-Vini", status="join me", world="Praia",
                  pronouns="ele/dele", joined="22/08/2023", last_login="hoje 17:31",
                  languages=["Português", "Inglês"], trust="Veteran",
                  note="nota", profile_url="https://vrchat.com/home/user/usr_1")
_dados = json.loads(qm._json_perfil(_perfil))
print(("OK   " if _dados["name"] == "Yuno-Vini" and _dados["world"] == "Praia"
       and _dados["trust"] == "Veteran" and _dados["languages_text"] == "Português, Inglês"
       else "FALHA") + "  perfil vira JSON para o QML")
_erro = json.loads(qm._json_perfil(None, "timed out"))
print(("OK   " if _erro.get("erro") == "timed out" else "FALHA") + "  erro vira JSON")

app = QApplication(sys.argv)

# Inter embarcada: registra (como o main faz) e confere que o Qt resolve a familia
for arquivo in qm.font_files():
    QFontDatabase.addApplicationFont(arquivo)
resolvida = QFontInfo(QFont("Inter 18pt", 13)).family()
print(("OK   " if resolvida == "Inter 18pt" else "FALHA") + f"  familia Inter no Qt: {resolvida}")

bridge = qm.Bridge()
# dados falsos direto no estado do bridge (sem tocar em rede)
bridge._logged_in = True
bridge._user_name = "eu"
bridge._count_text = "2 amigos online"
bridge._state = "list"
bridge._friends = [
    {"id": "a", "name": "Duda_Teste", "status": "join me", "status_label": "Join Me",
     "world": "Just Bikes · convite · EU", "location": "wrld_2:2", "avatar": ""},
    {"id": "b", "name": "Fabio_Teste", "status": "active", "status_label": "Online",
     "world": "Furry Hangout · público · JP", "location": "wrld_3:3", "avatar": ""},
]

erros = []
engine = QQmlApplicationEngine()
engine.warnings.connect(lambda lote: erros.extend(str(w.toString()) for w in lote))
engine.rootContext().setContextProperty("bridge", bridge)
engine.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Main.qml")))

ok = bool(engine.rootObjects())
print(("OK   " if ok else "FALHA") + "  Main.qml carregou")
if erros:
    print("avisos/erros do QML:")
    for e in erros:
        print("   ", e)

root = engine.rootObjects()[0] if ok else None
if root is not None:
    print("OK   título:", root.property("title"))
    print("OK   sem avisos do QML" if not erros else "FALHA  houve avisos do QML")

sys.exit(0 if ok and not erros else 1)
