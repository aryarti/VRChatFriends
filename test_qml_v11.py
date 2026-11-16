# -*- coding: utf-8 -*-
"""Teste de UI da v1.1 (offscreen, sem rede): cabeçalho ordenável, seta na coluna
ativa, seleção que sobrevive à reordenação, bolinha de status e limite de 32.

Uso: python -B test_qml_v11.py
"""
import json
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import Q_ARG, QCoreApplication, QMetaObject, QPointF, Qt  # noqa: E402
from PySide6.QtGui import QFontDatabase  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import ui_qml.main as qm  # noqa: E402
from core import Friend  # noqa: E402

# nenhum arquivo real em %LOCALAPPDATA% pode ser tocado por este teste
import core.vrchat as vrc_mod  # noqa: E402
import tempfile  # noqa: E402

_TMP = tempfile.mkdtemp(prefix="vrc_v11_")
vrc_mod.SESSION_FILE = os.path.join(_TMP, "session.json")
vrc_mod.WORLD_CACHE = os.path.join(_TMP, "worlds.json")
vrc_mod.AVATARS_DIR = os.path.join(_TMP, "avatars")

falhas = []


def check(nome, cond, extra=""):
    print(("OK   " if cond else "FALHA") + f"  {nome}" + (f"  [{extra}]" if extra else ""))
    if not cond:
        falhas.append(nome)


def processar(vezes=3):
    for _ in range(vezes):
        QCoreApplication.processEvents()


app = QApplication(sys.argv)
for arquivo in qm.font_files():
    QFontDatabase.addApplicationFont(arquivo)

# settings: nem lê nem grava o arquivo real do usuário
salvos = []
qm.load_settings = lambda: {}
qm.save_settings = lambda dados: salvos.append(dict(dados))

bridge = qm.Bridge()
bridge._logged_in = True
bridge._user_name = "aryaah"

erros = []
engine = QQmlApplicationEngine()
engine.warnings.connect(lambda lote: erros.extend(str(w.toString()) for w in lote))
engine.rootContext().setContextProperty("bridge", bridge)
engine.load(os.path.join(qm.QML_DIR, "Main.qml"))
if not engine.rootObjects():
    print("FALHA  Main.qml não carregou:", erros)
    sys.exit(1)
win = engine.rootObjects()[0]
processar()

check("padrão ao abrir: Status ▲",
      bridge.property("sortColumn") == "status" and bridge.property("sortDirection") == "asc",
      f"{bridge.property('sortColumn')} {bridge.property('sortDirection')}")

# ---------------------------------------------------------------- dados falsos
# nomes em ordem inversa à do status, de propósito: assim nome ≠ status
amigos = [
    Friend(id="u1", name="Zeca", status="join me", world="Zeta · público",
           location="wrld_z:1"),
    Friend(id="u2", name="ana", status="active", world="Alfa · grupo",
           location="wrld_a:1~group(grp_1)"),
    Friend(id="u3", name="Bruno", status="ask me", world="Beta",
           location="wrld_b:1"),
    Friend(id="u4", name="Caio", status="busy", world="Alfa",
           location="wrld_c:1"),
]
bridge._apply_friends(amigos)
processar()

def ordem():
    return [linha["name"] for linha in bridge.property("friends")]

check("lista entra em Status ▲", ordem() == ["Zeca", "ana", "Bruno", "Caio"], ordem())

from PySide6.QtCore import QObject  # noqa: E402

seta_nome = win.findChild(QObject, "setaAmigo")
seta_status = win.findChild(QObject, "setaStatus")
seta_mundo = win.findChild(QObject, "setaMundo")
check("seta existe nas três colunas",
      bool(seta_nome) and bool(seta_status) and bool(seta_mundo))
check("seta só na coluna ativa (Status)",
      seta_status.property("visible") is True
      and seta_nome.property("visible") is False
      and seta_mundo.property("visible") is False,
      f"{seta_nome.property('visible')} {seta_status.property('visible')} "
      f"{seta_mundo.property('visible')}")
check("seta crescente é ▲", seta_status.property("text") == "▲", seta_status.property("text"))

# ---------------------------------------------------------------- clique real
def clicar(object_name):
    alvo = win.findChild(QObject, object_name)
    ponto = alvo.mapToScene(QPointF(alvo.width() / 2, alvo.height() / 2))
    QTest.mouseClick(win, Qt.LeftButton, Qt.NoModifier, ponto.toPoint())
    processar()


clicar("headAmigo")
check("1º clique em AMIGO: crescente por nome",
      bridge.property("sortColumn") == "name" and ordem() == ["ana", "Bruno", "Caio", "Zeca"],
      f"{bridge.property('sortColumn')} {bridge.property('sortDirection')} {ordem()}")
check("seta passou para AMIGO, ainda ▲",
      seta_nome.property("visible") is True and seta_nome.property("text") == "▲"
      and seta_status.property("visible") is False)

clicar("headAmigo")
check("2º clique em AMIGO: decrescente",
      bridge.property("sortDirection") == "desc"
      and ordem() == ["Zeca", "Caio", "Bruno", "ana"], ordem())
check("seta virou ▼", seta_nome.property("text") == "▼", seta_nome.property("text"))

clicar("headMundo")
check("clique em MUNDO começa crescente",
      bridge.property("sortColumn") == "world" and bridge.property("sortDirection") == "asc",
      f"{bridge.property('sortColumn')} {bridge.property('sortDirection')}")
check("MUNDO asc: público (por nome do mundo), depois grupo",
      ordem() == ["Caio", "Bruno", "Zeca", "ana"], ordem())

check("settings gravou coluna e direção",
      salvos and salvos[-1].get("sort_column") == "world"
      and salvos[-1].get("sort_direction") == "asc",
      str(salvos[-1] if salvos else None))

# ---------------------------------------------------------------- seleção
lista = win.findChild(QObject, "lista")
QMetaObject.invokeMethod(lista, "selecionar", Qt.DirectConnection, Q_ARG("QVariant", "u3"))
processar()
check("selecionar por id marca a linha",
      lista.property("currentIndex") == ordem().index("Bruno"),
      f"index={lista.property('currentIndex')} ordem={ordem()}")

clicar("headAmigo")   # reordena: o Bruno anda de lugar
processar(5)
check("reordenar mantém a seleção no mesmo amigo",
      lista.property("currentIndex") == ordem().index("Bruno"),
      f"index={lista.property('currentIndex')} ordem={ordem()}")

# atualizar a lista (novo refresh) não pode perder a seleção
bridge._apply_friends(list(amigos))
processar(5)
check("atualizar mantém a seleção no mesmo amigo",
      lista.property("currentIndex") == ordem().index("Bruno"),
      f"index={lista.property('currentIndex')} ordem={ordem()}")

# amigo que sai da lista: seleção é limpa, não pula para outro
bridge._apply_friends([a for a in amigos if a.id != "u3"])
processar(5)
check("amigo que saiu limpa a seleção", lista.property("currentIndex") == -1,
      str(lista.property("currentIndex")))

# ---------------------------------------------------------------- bolinha de status
bolinha = win.findChild(QObject, "bolinhaStatus")
check("bolinha de status existe", bool(bolinha))
perfil_busy = {"id": "u9", "name": "aryaah", "status": "busy",
               "status_description": "", "profile_url": ""}
bridge.myProfileReady.emit(json.dumps(perfil_busy))
processar()
QTest.qWait(250)   # deixa a ColorAnimation da bolinha terminar
cor = bolinha.property("color")
check("bolinha recolhida fica visível", bolinha.property("visible") in (True, 1),
      str(bolinha.property("visible")))
check("bolinha usa a cor do status escolhido (Busy)",
      cor is not None and cor.name().lower() == "#ff7b72",
      cor.name() if cor is not None else None)

for status, esperado in (("active", "#3ba55d"), ("join me", "#4fc3e8"), ("ask me", "#e8b04b")):
    bridge.myProfileReady.emit(json.dumps(dict(perfil_busy, status=status)))
    processar()
    QTest.qWait(250)
    cor = bolinha.property("color")
    check(f"bolinha acompanha o status '{status}'", cor is not None and cor.name().lower() == esperado,
          cor.name() if cor is not None else None)

# ---------------------------------------------------------------- 32 caracteres
bio = win.findChild(QObject, "bioEdit")
contador = win.findChild(QObject, "bioContador")
check("campo de status e contador existem", bool(bio) and bool(contador))
bio.setProperty("text", "a" * 40)
processar()
texto = bio.property("text")
check("status para em 32 caracteres", len(texto) == 32, f"{len(texto)}: {texto}")
check("contador mostra 32/32", contador.property("text") == "32/32", contador.property("text"))
bio.setProperty("text", "oi")
processar()
check("contador acompanha o texto", contador.property("text") == "2/32", contador.property("text"))
check("limite anunciado ao QML é 32", bridge.property("statusMaxLength") == 32)

# ---------------------------------------------------------------- timer de refresh
class ServicoFalso:
    """Imita o VRChatService sem tocar na rede."""

    def __init__(self, erro=None):
        self.buscas = 0
        self.erro = erro

    def fetch_friends(self):
        self.buscas += 1
        if self.erro:
            raise self.erro
        return [Friend(id="u1", name="Zeca", status="busy", location="wrld_z:1")]

    def fetch_avatars(self, amigos, size=20):
        return {}


def esperar(condicao, limite=100):
    for _ in range(limite):
        if condicao():
            return True
        QTest.qWait(20)
    return condicao()


b2 = qm.Bridge()
b2.service = ServicoFalso()
b2._logged_in = True
t = qm.criar_timer_refresh(b2)
check("timer de atualização automática existe e roda", t.isActive())
check("ritmo normal é 45 s", t.interval() == 45000, str(t.interval()))
b2.refreshFailed.emit()
check("depois de uma falha tenta em 15 s", t.interval() == 15000, str(t.interval()))
b2.refreshOk.emit()
check("depois de acertar volta a 45 s", t.interval() == 45000, str(t.interval()))

t.timeout.emit()
check("timeout do timer dispara a busca",
      esperar(lambda: b2.service.buscas >= 1 and not b2._refreshing), str(b2.service.buscas))

b4 = qm.Bridge()
b4.service = ServicoFalso()
b4._logged_in = False
t4 = qm.criar_timer_refresh(b4)
t4.timeout.emit()
processar()
check("deslogado o timer não busca", b4.service.buscas == 0, str(b4.service.buscas))
b4._logged_in = True
t4.timeout.emit()
check("logado o mesmo timer busca",
      esperar(lambda: b4.service.buscas >= 1 and not b4._refreshing), str(b4.service.buscas))

# ------------------------------------------------ falha chega na tela com motivo
b3 = qm.Bridge()
b3.service = ServicoFalso(erro=qm.ApiError(
    "429 Client Error: Too Many Requests for url: https://api.vrchat.cloud/api/1/auth/user/friends"))
b3._logged_in = True
b3.refresh()
check("falha termina o ciclo", esperar(lambda: not b3._refreshing))
check("motivo curto: limite de requisições",
      b3.property("lastError") == "limite de requisições", b3.property("lastError"))
check("estado vira erro", b3.property("state") == "error", b3.property("state"))
check("rodapé diz o motivo", "limite" in b3.property("metaText"), b3.property("metaText"))
check("motivo curto: sem conexão",
      qm._motivo_curto("ConnectionError(MaxRetryError('NewConnectionError'))") == "sem conexão")
check("motivo curto: timeout",
      qm._motivo_curto("ReadTimeout(ReadTimeoutError('timed out'))") == "sem resposta do VRChat")

# ---------------------------------------------------------------- janela de 60 s
# relógio real: o timer dispara sozinho sem clique (1 s em vez de 45 s)
b5 = qm.Bridge()
b5.service = ServicoFalso()
b5._logged_in = True
t5 = qm.criar_timer_refresh(b5)
t5.setInterval(300)
check("o timer dispara sozinho (sem clique)",
      esperar(lambda: b5.service.buscas >= 1 and not b5._refreshing, 60), str(b5.service.buscas))
t5.stop()


check("QML sem avisos", not erros, str(erros[:3]))

print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
