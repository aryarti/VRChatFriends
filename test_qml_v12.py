# -*- coding: utf-8 -*-
"""UI da v1.1, parte 2 (sem rede): estrela de favorito, fixados no topo, bloco offline
apagado, aviso "amigo entrou" (cartão, cor, clique, tempo, empilhamento) e a
política de silêncio (desligado / Busy / 10 min).

Usa a plataforma real do Qt (winId) porque o ListView só cria os delegates com a
janela de verdade, e a janela fica FORA da tela (-4000) para não incomodar.

Uso: python -B test_qml_v12.py
"""
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QObject, QPointF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QFontDatabase  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

FORA_DA_TELA = -4000


def buscar(item, nome):
    """Percorre a árvore visual (delegate de ListView não aparece no findChildren)."""
    if item is None:
        return None
    if item.objectName() == nome:
        return item
    for filho in item.childItems():
        achado = buscar(filho, nome)
        if achado is not None:
            return achado
    return None


def linhas_visiveis():
    """Os delegates da lista na ordem da tela."""
    item = win.findChild(QObject, "lista").property("contentItem")
    if item is None:
        return []
    return [c for c in item.childItems() if c.objectName() == "rowItem"]

import core.vrchat as vrc_mod  # noqa: E402
import ui_qml.main as qm  # noqa: E402
from core import Friend  # noqa: E402
from core import favorites  # noqa: E402

# nada de arquivo real: sessão, cache de mundos e avatares vão para temp
_TMP = tempfile.mkdtemp(prefix="vrc_v12_")
vrc_mod.SESSION_FILE = os.path.join(_TMP, "session.json")
vrc_mod.WORLD_CACHE = os.path.join(_TMP, "worlds.json")
vrc_mod.AVATARS_DIR = os.path.join(_TMP, "avatars")
os.makedirs(vrc_mod.AVATARS_DIR, exist_ok=True)
import core.paths as paths_mod  # noqa: E402

paths_mod.AVATARS_DIR = vrc_mod.AVATARS_DIR

falhas = []


def check(nome, cond, extra=""):
    print(("OK   " if cond else "FALHA") + f"  {nome}" + (f"  [{extra}]" if extra else ""))
    if not cond:
        falhas.append(nome)


def processar(vezes=3):
    for _ in range(vezes):
        QApplication.processEvents()


app = QApplication(sys.argv)
for arquivo in qm.font_files():
    QFontDatabase.addApplicationFont(arquivo)

# PNGs de verdade no cache (o QML abre os arquivos; lixo geraria aviso)
from PIL import Image  # noqa: E402

Image.new("RGBA", (56, 56), (120, 90, 255, 255)).save(os.path.join(vrc_mod.AVATARS_DIR, "u9-56.png"))
Image.new("RGBA", (56, 56), (60, 60, 70, 255)).save(os.path.join(vrc_mod.AVATARS_DIR, "a.png"))

agora = time.time()
# o "arquivo" fica num dict mutável: o bridge relê os favoritos do disco a cada
# estrela (correção da v1.1 para duas janelas abertas), então o settings falso
# precisa guardar o que foi gravado — antes ele devolvia sempre o mesmo config.
arquivo = {"dados": {"favorites": {"u9": {"name": "Zeca", "last_seen": agora - 7200}}}}
salvos = []


def _ler_settings():
    return json.loads(json.dumps(arquivo["dados"]))


def _gravar_settings(dados):
    salvos.append(json.loads(json.dumps(dados, default=str)))
    arquivo["dados"] = json.loads(json.dumps(dados, default=str))


qm.load_settings = _ler_settings
qm.save_settings = _gravar_settings

bridge = qm.Bridge()
bridge._logged_in = True
bridge._user_name = "aryaah"
bridge._meu_status = "active"

amigos = [
    Friend(id="u1", name="Ana", status="active", world="Pug", location="wrld_a:1",
           platform="standalonewindows",
           avatar=os.path.join(vrc_mod.AVATARS_DIR, "a.png")),
    Friend(id="u2", name="Bia", status="join me", world="Pug", location="wrld_a:1",
           platform="standalonewindows"),
    Friend(id="u3", name="Caio", status="busy", world="na web", location="offline",
           platform="web"),
]

erros = []
engine = QQmlApplicationEngine()
engine.warnings.connect(lambda lote: erros.extend(str(w.toString()) for w in lote))
engine.rootContext().setContextProperty("bridge", bridge)
engine.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Main.qml")))
if not engine.rootObjects():
    print("FALHA  Main.qml não carregou:", erros)
    sys.exit(1)
win = engine.rootObjects()[0]
win.setPosition(FORA_DA_TELA, FORA_DA_TELA)   # longe da tela: não atrapalha ninguém
win.show()
bridge._apply_friends(amigos)
processar()
QTest.qWait(300)


def linhas():
    return bridge.property("friends")


def nomes():
    return [l["name"] for l in linhas()]


# ---------------------------------------------------------------- lista
check("favorito offline entra no fim, apagado",
      nomes() == ["Bia", "Ana", "Caio", "Zeca"], nomes())
check("linha offline marcada", linhas()[-1]["offline"] is True)
check("linha online não marcada offline", all(not l["offline"] for l in linhas()[:-1]))
check("favorito offline tem status Offline", linhas()[-1]["status_label"] == "Offline",
      linhas()[-1]["status_label"])
check("favorito offline mostra 'visto há'", linhas()[-1]["active"] == "2 h",
      linhas()[-1]["active"])
check("avatar do favorito offline vem do cache", linhas()[-1]["avatar"].startswith("file:"),
      linhas()[-1]["avatar"])
check("contador conta só quem está online",
      bridge.property("count") == 3 and "3 amigos online" in bridge.property("countText"),
      f"{bridge.property('count')} / {bridge.property('countText')}")

# ---------------------------------------------------------------- estrela na linha
def delegados_por_id():
    saida = {}
    for item in linhas_visiveis():
        linha = item.property("row") or {}
        saida[linha.get("id")] = item
    return saida


delegados = delegados_por_id()
check("as 4 linhas existem no QML", len(delegados) == 4, str(sorted(delegados)))

row_ana = delegados.get("u1")
estrela_ana = buscar(row_ana, "estrela")
check("estrela apagada quando não é favorito", estrela_ana.property("text") == "☆",
      estrela_ana.property("text"))


def clicar_objeto(item, nome_filho):
    alvo = buscar(item, nome_filho)
    ponto = alvo.mapToScene(QPointF(alvo.width() / 2, alvo.height() / 2))
    QTest.mouseClick(win, Qt.LeftButton, Qt.NoModifier, ponto.toPoint())
    processar()
    QTest.qWait(150)


clicar_objeto(row_ana, "estrela")
check("clique na estrela favorita", "u1" in bridge._favoritos, str(list(bridge._favoritos)))
check("favorito novo sobe para o topo", nomes()[0] == "Ana", nomes())
check("settings gravou o favorito",
      salvos and "u1" in (salvos[-1].get("favorites") or {}), str(salvos[-1] if salvos else None))
check("settings guardou nome e visto",
      (salvos[-1]["favorites"]["u1"]["name"] == "Ana"
       and salvos[-1]["favorites"]["u1"]["last_seen"] > 0),
      str(salvos[-1]["favorites"].get("u1")))

delegados = delegados_por_id()
estrela_ana = buscar(delegados["u1"], "estrela")
contorno = buscar(delegados["u1"], "contornoFavorito")
check("estrela acesa no favorito", estrela_ana.property("text") == "★", estrela_ana.property("text"))
check("contorno do favorito visível", contorno.property("visible") is True)
check("não favorito continua sem contorno",
      buscar(delegados["u2"], "contornoFavorito").property("visible") is False)

# segundo clique tira o favorito
clicar_objeto(delegados["u1"], "estrela")
check("segundo clique desfavorita", "u1" not in bridge._favoritos, str(list(bridge._favoritos)))
check("lista volta à ordem normal", nomes() == ["Bia", "Ana", "Caio", "Zeca"], nomes())

# ---------------------------------------------------------------- cartão do perfil
popup = win.findChild(QObject, "popup")
bridge.profileReady.emit(json.dumps({"id": "u2", "name": "Bia", "status": "join me"}))
processar()
estrela_popup = buscar(popup, "estrelaPerfil")
check("cartão do perfil tem estrela", bool(estrela_popup))
bridge.toggleFavorito("u2")
processar()
check("estrela do cartão acende ao favoritar", estrela_popup.property("text") == "★",
      estrela_popup.property("text"))
bridge.toggleFavorito("u2")
processar()

# ------------------------------------------------- bolinha vazada (quem está só na web)
def bolinha(nome_amigo):
    for delegate in linhas_visiveis():
        if delegate.property("row")["name"] == nome_amigo:
            return buscar(delegate, "statusDotLinha")
    return None


dot_web = bolinha("Caio")      # platform web -> vazada
dot_jogo = bolinha("Ana")      # standalonewindows -> cheia
check("bolinha: amigo só na web marca vazada",
      dot_web is not None and bool(dot_web.property("vazada")))
check("bolinha vazada: sem preenchimento e com anel de 1.5",
      dot_web is not None and dot_web.property("color").alpha() == 0
      and abs(float(dot_web.property("anel")) - 1.5) < 0.01,
      f"color={dot_web.property('color').name() if dot_web else '?'} "
      f"anel={dot_web.property('anel') if dot_web else '?'}")
check("bolinha vazada usa a cor do status (busy) no anel",
      dot_web is not None and dot_web.property("corAnel").name().lower() == "#ff7b72",
      dot_web.property("corAnel").name() if dot_web else "?")
check("bolinha: amigo no jogo continua cheia, sem anel",
      dot_jogo is not None and not bool(dot_jogo.property("vazada"))
      and dot_jogo.property("color").alpha() == 255
      and float(dot_jogo.property("anel")) == 0,
      f"color={dot_jogo.property('color').name() if dot_jogo else '?'} "
      f"anel={dot_jogo.property('anel') if dot_jogo else '?'}")

# ---------------------------------------------------------------- toast
eng_toast = QQmlApplicationEngine()
eng_toast.rootContext().setContextProperty("bridge", bridge)
eng_toast.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Toast.qml")))
if not eng_toast.rootObjects():
    print("FALHA  Toast.qml não carregou")
    sys.exit(1)
toast = eng_toast.rootObjects()[0]
toast.setPosition(FORA_DA_TELA, FORA_DA_TELA)   # também fora da tela
toast.setProperty("msAviso", 900)     # 900 ms em vez de 5 s, para o teste
processar()


def cartoes_toast():
    """Cartões do aviso na ordem da tela (Repeater não aparece no findChildren)."""
    saida = []

    def coleta(item):
        for filho in item.childItems():
            if filho.objectName() == "cartaoAviso":
                saida.append(filho)
            coleta(filho)

    raiz = toast.contentItem()
    if raiz is not None:
        coleta(raiz)
    return saida
check("toast começa escondido", toast.property("visible") in (False, 0),
      str(toast.property("visible")))
check("toast não é janela da barra de tarefas",
      bool(toast.property("flags") is not None))

# favorito -> cartão na cor de destaque; comum -> cinza
bridge.amigoEntrou.emit(json.dumps({"id": "u1", "name": "Ana", "world": "Pug",
                                    "avatar": "", "favorito": True, "agregado": 0}))
bridge.amigoEntrou.emit(json.dumps({"id": "u3", "name": "Caio", "world": "na web",
                                    "avatar": "", "favorito": False, "agregado": 0}))
processar()
QTest.qWait(250)
cartoes = cartoes_toast()
check("dois avisos empilhados", len(cartoes) == 2, str(len(cartoes)))
check("toast apareceu", toast.property("visible") in (True, 1), str(toast.property("visible")))
cores = [c.property("color") for c in cartoes]
check("um cartão em destaque e outro no cinza",
      cores[0].name().lower() == "#261c4f" and cores[1].name().lower() == "#15171b",
      [c.name() for c in cores])
check("marca de estrela só no favorito",
      [buscar(c, "estrelaAviso").property("visible") for c in cartoes] == [True, False],
      str([buscar(c, "estrelaAviso").property("visible") for c in cartoes]))
check("janela do toast só cobre os cartões",
      toast.property("height") >= 2 * 64 and toast.property("height") <= 160,
      str(toast.property("height")))

# clique abre o cartão do amigo na janela principal
abertos = []
bridge.abrirAmigo.connect(lambda uid: abertos.append(uid))
cartao_comum = cartoes[1]
ponto = cartao_comum.mapToScene(QPointF(cartao_comum.width() / 2, cartao_comum.height() / 2))
QTest.mouseClick(toast, Qt.LeftButton, Qt.NoModifier, ponto.toPoint())
processar()
QTest.qWait(250)
check("clique no aviso pede o cartão do amigo", abertos == ["u3"], str(abertos))
check("cartão clicado foi embora", len(cartoes_toast()) == 1,
      str(len(cartoes_toast())))
check("popup do amigo abriu no Main.qml", popup.property("opened") is True)

# some sozinho
QTest.qWait(1200)
check("aviso some sozinho no tempo", len(cartoes_toast()) == 0,
      str(len(cartoes_toast())))
check("toast se esconde quando não há cartão", toast.property("visible") in (False, 0),
      str(toast.property("visible")))

# máximo de 3 empilhados
for i in range(5):
    bridge.amigoEntrou.emit(json.dumps({"id": f"x{i}", "name": f"Amigo {i}", "world": "",
                                        "avatar": "", "favorito": False, "agregado": 0}))
processar()
QTest.qWait(200)
check("no máximo 3 cartões empilhados", len(cartoes_toast()) == 3,
      str(len(cartoes_toast())))
QTest.qWait(1200)
processar()

# pausa com o mouse em cima
bridge.amigoEntrou.emit(json.dumps({"id": "u1", "name": "Ana", "world": "", "avatar": "",
                                    "favorito": True, "agregado": 0}))
processar()
QTest.qWait(150)
cartao = cartoes_toast()[0]
centro = cartao.mapToScene(QPointF(cartao.width() / 2, cartao.height() / 2)).toPoint()
QTest.mouseMove(toast, centro)
QTest.qWait(1400)          # bem mais que os 900 ms
check("mouse em cima pausa o tempo do aviso",
      len(cartoes_toast()) == 1,
      str(len(cartoes_toast())))
QTest.mouseMove(toast, centro + type(centro)(400, 0))
processar()
QTest.qWait(1400)
check("saindo com o mouse, o aviso volta a contar",
      len(cartoes_toast()) == 0,
      str(len(cartoes_toast())))

# ---------------------------------------------------------------- política do aviso
recebidos = []
bridge.amigoEntrou.connect(lambda txt: recebidos.append(json.loads(txt)))


def entrada(uid, nome):
    return {"id": uid, "name": nome, "world": "", "avatar": ""}


bridge._avisados.clear()
bridge._avisos = False
bridge._entradasReady.emit([entrada("u7", "Sete")])
processar()
check("avisos desligados não mostram nada", recebidos == [], str(recebidos))

bridge._avisos = True
bridge._meu_status = "busy"
bridge._entradasReady.emit([entrada("u7", "Sete")])
processar()
check("Busy silencia o aviso (e não gasta o intervalo)", recebidos == [], str(recebidos))

bridge._meu_status = "active"
bridge._entradasReady.emit([entrada("u7", "Sete")])
processar()
check("status normal volta a avisar", [a["id"] for a in recebidos] == ["u7"], str(recebidos))

bridge._entradasReady.emit([entrada("u7", "Sete")])
processar()
check("o mesmo amigo não avisa de novo em 10 min", len(recebidos) == 1, str(len(recebidos)))

bridge._entradasReady.emit([entrada("u7", "Sete"), entrada("u8", "Oito")])
processar()
check("outro amigo ainda avisa", [a["id"] for a in recebidos][-1:] == ["u8"], str(recebidos))

check("QML sem avisos", not erros, str(erros[:3]))

print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
