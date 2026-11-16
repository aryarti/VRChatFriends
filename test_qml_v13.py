# -*- coding: utf-8 -*-
"""Correções da v1.1 (sem rede): favoritos que sumiam, monitor do aviso e o X do widget.

Três defeitos que o dono viu usando a v1.1:

1. favorito que sumia — duas janelas do app gravavam o settings.json inteiro a partir
   da própria memória; a mais antiga apagava a estrela salva pela outra. Agora a
   gravação mescla com o arquivo e os favoritos vêm do disco;
2. o aviso de "amigo entrou" nascia no monitor onde estava a janela; agora nasce
   sempre no monitor principal;
3. o X do widget não fechava nada: o MouseArea de arrastar cobria o cartão inteiro
   e engolia o clique dos botões.

Uso: python -B test_qml_v13.py
"""
import inspect
import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QObject, QPointF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QFontDatabase, QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

FORA_DA_TELA = -4000


def buscar(item, nome):
    """Percorre a árvore visual (delegate/Repeater não aparecem no findChildren)."""
    if item is None:
        return None
    if item.objectName() == nome:
        return item
    for filho in item.childItems():
        achado = buscar(filho, nome)
        if achado is not None:
            return achado
    return None


import core.vrchat as vrc_mod  # noqa: E402
import ui_qml.main as qm  # noqa: E402
from core import Friend  # noqa: E402

# nada de arquivo real: sessão, mundos e avatares vão para temp
_TMP = tempfile.mkdtemp(prefix="vrc_v13_")
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


def processar(vezes=4):
    for _ in range(vezes):
        QApplication.processEvents()


# ---------------------------------------------------------------- "disco" falso
# Um dict faz o papel do settings.json; cada Bridge lê e grava por aqui. Assim duas
# instâncias (dois Bridge) realmente compartilham o arquivo, como no app de verdade.
ARQUIVO = {"dados": {}}


def _ler():
    return json.loads(json.dumps(ARQUIVO["dados"]))


def _gravar(dados):
    ARQUIVO["dados"] = json.loads(json.dumps(dados, default=str))


qm.load_settings = _ler
qm.save_settings = _gravar

app = QApplication(sys.argv)
for arquivo_fonte in qm.font_files():
    QFontDatabase.addApplicationFont(arquivo_fonte)

agora = time.time()

# ---------------------------------------------------------------- 1. favoritos
print("\n== favoritos: duas janelas abertas ==")
# janela A abre primeiro e fica com a lista de favoritos vazia na memória
janela_a = qm.Bridge()

# janela B abre depois e o dono estrela a Ana nela
janela_b = qm.Bridge()
janela_b._apply_friends([Friend(id="u1", name="Ana", status="active", world="Pug",
                                location="wrld_a:1", platform="standalonewindows")])
janela_b.toggleFavorito("u1")
check("estrela da outra janela chega no arquivo",
      "u1" in (ARQUIVO["dados"].get("favorites") or {}), str(ARQUIVO["dados"]))

# a janela velha grava outra coisa (mudar a ordenação grava o settings)
janela_a.setSort("name")
check("janela velha não apaga o favorito da outra",
      "u1" in (ARQUIVO["dados"].get("favorites") or {}), str(ARQUIVO["dados"]))
check("a ordenação da janela velha foi gravada",
      ARQUIVO["dados"].get("sort_column") == "name", str(ARQUIVO["dados"].get("sort_column")))

# a Ana sai do ar: o favorito tem de aparecer apagado no fim da lista
janela_a._apply_friends([])
linhas = janela_a.property("friends")
check("favorito offline aparece na lista da janela velha",
      [l["name"] for l in linhas] == ["Ana"], str([l["name"] for l in linhas]))
check("linha offline marcada e com 'visto há'",
      bool(linhas) and linhas[0]["offline"] is True and linhas[0]["active"] != "",
      str(linhas[:1]))

# salvou a posição do widget (grava o settings) e o favorito continua lá
janela_a.salvarWidgetPos(100, 200)
check("gravar outra chave não derruba o favorito",
      "u1" in (ARQUIVO["dados"].get("favorites") or {}), str(ARQUIVO["dados"]))

# reinício do app: o favorito offline volta do arquivo
janela_c = qm.Bridge()
janela_c._apply_friends([])
linhas_c = janela_c.property("friends")
check("depois de reiniciar, o favorito offline continua na lista",
      [l["name"] for l in linhas_c] == ["Ana"], str([l["name"] for l in linhas_c]))

# desfavoritar continua funcionando (estrela apagada de novo)
janela_c.toggleFavorito("u1")
check("desfavoritar apaga do arquivo", not (ARQUIVO["dados"].get("favorites") or {}),
      str(ARQUIVO["dados"].get("favorites")))
check("desfavoritar tira a linha da lista", janela_c.property("friends") == [],
      str(janela_c.property("friends")))

# ---------------------------------------------------------------- 2. widget
print("\n== widget: o X fecha ==")
bridge = qm.Bridge()
bridge._apply_friends([])
avisos_qml = []
eng_widget = QQmlApplicationEngine()
eng_widget.warnings.connect(lambda lote: avisos_qml.extend(str(w.toString()) for w in lote))
eng_widget.rootContext().setContextProperty("bridge", bridge)
eng_widget.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Widget.qml")))
if not eng_widget.rootObjects():
    print("FALHA  Widget.qml não carregou")
    sys.exit(1)
widget = eng_widget.rootObjects()[0]
widget.setPosition(FORA_DA_TELA, FORA_DA_TELA)
processar()
QTest.qWait(150)

mostradas = []
bridge.requestShow.connect(lambda: mostradas.append(1))
bridge.setWidgetAberto(True)
processar()
QTest.qWait(200)
check("widget aparece com widgetAberto", widget.property("visible") in (True, 1),
      str(widget.property("visible")))


def clicar(item, alvo):
    ponto = alvo.mapToScene(QPointF(alvo.width() / 2, alvo.height() / 2))
    QTest.mouseClick(item, Qt.LeftButton, Qt.NoModifier, ponto.toPoint())
    processar()
    QTest.qWait(200)


fechar = buscar(widget.contentItem(), "btFechar")
check("botão de fechar existe no widget", fechar is not None)
clicar(widget, fechar)
check("o X fecha o widget (bridge)", bridge.widgetAberto is False, str(bridge.widgetAberto))
check("o X esconde a janela do widget", widget.property("visible") in (False, 0),
      str(widget.property("visible")))
check("o X não abriu a janela principal", mostradas == [], str(mostradas))
check("o X foi gravado no settings (fica fechado no próximo abrir)",
      ARQUIVO["dados"].get("widget_aberto") is False, str(ARQUIVO["dados"].get("widget_aberto")))

# o resto do cartão continua clicável (clique curto abre a janela principal)
bridge.setWidgetAberto(True)
processar()
QTest.qWait(200)
alvo_livre = QPointF(widget.width() / 3, widget.height() - 10)
QTest.mouseClick(widget, Qt.LeftButton, Qt.NoModifier, alvo_livre.toPoint())
processar()
QTest.qWait(150)
check("clicar no cartão abre a janela principal", mostradas == [1], str(mostradas))
bridge.setWidgetAberto(False)
processar()

# ---------------------------------------------------------------- 3. monitor do aviso
print("\n== aviso: sempre no monitor principal ==")
eng_toast = QQmlApplicationEngine()
eng_toast.warnings.connect(lambda lote: avisos_qml.extend(str(w.toString()) for w in lote))
eng_toast.rootContext().setContextProperty("bridge", bridge)
eng_toast.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Toast.qml")))
if not eng_toast.rootObjects():
    print("FALHA  Toast.qml não carregou")
    sys.exit(1)
toast = eng_toast.rootObjects()[0]
toast.setPosition(FORA_DA_TELA, FORA_DA_TELA)
processar()

tela = QGuiApplication.primaryScreen()
area = tela.availableGeometry()
pos = qm.posicionar_aviso(toast)
esperado = (
    area.x() + area.width() - toast.width(),
    area.y() + area.height() - toast.height(),
)
check("aviso posicionado no canto da tela principal", tuple(pos) == esperado,
      f"{pos} != {esperado}")
check("aviso não depende da janela do app (sem 'referencia')",
      list(inspect.signature(qm.posicionar_aviso).parameters) == ["janela", "tela", "margem"],
      str(list(inspect.signature(qm.posicionar_aviso).parameters)))

# a máquina do dono tem dois monitores: mesmo com a "janela" no secundário o aviso
# tem de nascer no principal (era o defeito: `janela.screen()`)
telas = QGuiApplication.screens()
if len(telas) > 1:
    secundaria = telas[1].geometry()
    toast.setPosition(secundaria.x() + 100, secundaria.y() + 100)
    processar()
    pos_sec = qm.posicionar_aviso(toast)
    check("aviso não segue a janela para o monitor secundário",
          pos_sec[0] < secundaria.x(),
          f"{pos_sec} (secundário começa em {secundaria.x()})")
    check("aviso no secundário volta para o canto da principal",
          tuple(pos_sec) == esperado, f"{pos_sec} != {esperado}")
else:
    print("AVISO  só um monitor: o teste do monitor secundário foi pulado")

# altura muda (mais cartões) e o aviso continua colado no canto da principal
toast.setHeight(toast.height() + 60)
processar()
pos2 = qm.posicionar_aviso(toast)
check("aviso maior continua no canto da tela principal",
      tuple(pos2) == (esperado[0], area.y() + area.height() - toast.height()), str(pos2))

# ---------------------------------------------------------------- 4. uma cópia por vez
print("\n== uma copia por vez ==")
qm.DATA_DIR = os.path.join(_TMP, "uma_copia")
os.makedirs(qm.DATA_DIR, exist_ok=True)
primeira = qm.instancia_unica(avisar=False)
segunda = qm.instancia_unica(avisar=False)
check("a primeira copia pega a trava", primeira is not None)
check("a segunda copia nao roda", segunda is None)
check("trava criada na pasta de dados",
      os.path.exists(os.path.join(qm.DATA_DIR, "app.lock")))
# soltando a trava, outra copia entra (nao fica travado para sempre)
primeira.unlock()
terceira = qm.instancia_unica(avisar=False)
check("soltando a trava, outra copia entra", terceira is not None)
if terceira is not None:
    terceira.unlock()

check("QML do widget e do aviso sem erros", not avisos_qml, str(avisos_qml[:3]))

print()
print("FALHAS:", falhas if falhas else "nenhuma")
sys.exit(1 if falhas else 0)
