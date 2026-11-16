# -*- coding: utf-8 -*-
"""Abre o app com dados FICTÍCIOS em um estado, para tirar print de divulgação.

Uso:
    python screenshots.py lista|popup|painel|widget|toast [segundos]

Nenhuma chamada de rede: o bridge é preenchido à mão. Os avatares também são gerados
aqui (círculo colorido com inicial), então nenhuma imagem de pessoa real entra no repo.
Os favoritos são fictícios: dois online fixados no topo e um offline (apagado,
"visto há 2 h") no fim da lista.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QObject, QMetaObject, QTimer, QUrl
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from core import APP_NAME, Friend, font_files

AQUI = os.path.dirname(os.path.abspath(__file__))
QML_DIR = os.path.join(AQUI, "ui_qml", "qml")
AVATARES = os.path.join(tempfile.gettempdir(), "vrchatfriends-showcase")

# (nome, status, mundo, plataforma, lotação, capacidade, cor, favorito, offline,
#  visto há)
AMIGOS = [
    ("Nina Fable", "join me", "The Great Pug · US", "standalonewindows", 17, 32, "#7C5CFF", True, False, ""),
    ("Rafa Nox", "active", "Cruzeiro Brasil · grupo · US", "standalonewindows", 0, 80, "#3BA55D", True, False, ""),
    ("Bia Sotto", "active", "na web", "web", None, None, "#E8B04B", False, False, ""),
    ("Caio Vento", "active", "no menu", "android", None, None, "#ED4245", False, False, ""),
    ("Duda Reis", "active", "Pixel Paradise", "standalonewindows", 23, 40, "#9B7BFF", False, False, ""),
    ("Téo Marlin", "ask me", "Midnight Rooftop", "standalonewindows", 8, None, "#4FC3E8", False, False, ""),
    ("Lia Kins", "ask me", "mundo privado", "standalonewindows", None, None, "#F0A868", False, False, ""),
    # favorito que não está online: entra no fim, apagado, com "visto há"
    ("Zeca Prado", "offline", "", "", None, None, "#6B7280", True, True, "2 h"),
]

MEU_PERFIL = {
    "id": "usr_eu", "name": "arya", "status": "join me", "status_label": "Join Me",
    "status_description": "modelando no zbrush — chama pra dançar",
    "pronouns": "any", "trust": "Trusted", "languages_text": "Português, Inglês",
    "joined": "14/04/2023", "last_login": "hoje 22:10", "world": "", "platform": "",
    "avatar": "", "profile_url": "", "note": "",
}

ROTULOS = {"join me": "Join Me", "ask me": "Ask Me", "active": "Online",
           "busy": "Busy", "offline": "Offline"}


def avatar(nome, cor, tamanho=128):
    """Círculo colorido com a inicial, desenhado aqui mesmo (sem imagem de terceiro)."""
    from PIL import Image, ImageDraw, ImageFont

    os.makedirs(AVATARES, exist_ok=True)
    destino = os.path.join(AVATARES, nome.replace(" ", "-").lower() + ".png")
    if os.path.exists(destino):
        return destino
    img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, tamanho - 1, tamanho - 1), fill=cor)
    try:
        fonte = ImageFont.truetype("arialbd.ttf", int(tamanho * 0.46))
    except Exception:
        fonte = ImageFont.load_default()
    letra = nome[0].upper()
    caixa = d.textbbox((0, 0), letra, font=fonte)
    d.text(((tamanho - (caixa[2] - caixa[0])) / 2 - caixa[0],
            (tamanho - (caixa[3] - caixa[1])) / 2 - caixa[1]),
           letra, font=fonte, fill="#FFFFFF")
    img.save(destino)
    return destino


def ident(nome):
    return "usr_" + nome.split()[0].lower()


def linhas_falsas():
    """As linhas que o QML desenha: favoritos no topo e um favorito offline no fim."""
    saida = []
    for nome, status, mundo, plat, occ, cap, cor, favorito, offline, visto in AMIGOS:
        rotulo = ""
        if occ:
            rotulo = f"{occ}/{cap}" if cap else str(occ)
        elif cap:
            rotulo = f"{1 if 'grupo' in mundo else 0}+/{cap}"
        saida.append({
            "id": ident(nome),
            "name": nome,
            "status": status,
            "status_label": ROTULOS.get(status, status),
            "world": mundo,
            "platform": plat,
            "web": (plat or "").lower() == "web",
            "location": "",
            "active": visto if offline else "agora",
            "avatar": QUrl.fromLocalFile(avatar(nome, cor)).toString(),
            "icon_url": "",
            "occupants": occ,
            "capacity": cap,
            "presentes": 1 if cap and not occ else 0,
            "occupants_label": rotulo,
            "favorito": favorito,
            "offline": offline,
        })
    return saida


def main(modo="lista", segundos=40):
    app = QGuiApplication(sys.argv)
    for f in font_files():
        QFontDatabase.addApplicationFont(f)

    from ui_qml.main import Bridge

    bridge = Bridge()
    # a ordem do print é fixa (Status ▲): o settings real não entra na foto
    bridge._sort_column, bridge._sort_dir = "status", "asc"
    bridge.sortChanged.emit()
    bridge._friends = linhas_falsas()
    # contadores e "quem está online" saem da lista de online (o offline não conta)
    bridge._all_friends = [
        Friend(id=ident(nome), name=nome, status=status, world=mundo, platform=plat,
               location="" if offline else "wrld_fake:1")
        for nome, status, mundo, plat, occ, cap, cor, favorito, offline, visto in AMIGOS
        if not offline
    ]
    bridge._favoritos = {ident(nome): {"name": nome, "last_seen": 0}
                         for nome, *_r in AMIGOS if _r[6]}
    bridge._favoritos_versao = 1
    online = len(bridge._all_friends)
    bridge._count_text = f"{online} amigos online"
    bridge._state = "list"
    bridge._meta = "arya · atualizado 22:10"
    bridge._logged_in = True
    bridge._title = APP_NAME + " — arya"
    bridge._user_name = "arya"

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Main.qml")))
    if not engine.rootObjects():
        print("FALHA: Main.qml não carregou")
        return 1
    janela = engine.rootObjects()[0]

    # avatar do meu perfil no canto superior (sem isso o ícone fica "?")
    meu = dict(MEU_PERFIL)
    meu["avatar"] = QUrl.fromLocalFile(avatar("arya", "#7C5CFF")).toString()
    QTimer.singleShot(
        600, lambda: bridge.myProfileReady.emit(json.dumps(meu, ensure_ascii=False))
    )

    if modo == "popup":
        def abrir_popup():
            perfil = dict(MEU_PERFIL)
            perfil.update({
                "id": ident("Nina Fable"),
                "name": "Nina Fable", "status": "join me", "status_label": "Join Me",
                "status_description": "dançando no pug até amanhã cedo ✦",
                "pronouns": "she/her", "trust": "Trusted User",
                "languages_text": "Português, Inglês", "joined": "02/09/2022",
                "last_login": "hoje 21:40",
                "avatar": QUrl.fromLocalFile(avatar("Nina Fable", "#7C5CFF")).toString(),
                "profile_url": "",
            })
            bridge.profileReady.emit(json.dumps(perfil, ensure_ascii=False))
            pop = janela.findChild(QObject, "popup")
            if pop is not None:
                QMetaObject.invokeMethod(pop, "open")
        QTimer.singleShot(1200, abrir_popup)

    elif modo == "painel":
        def abrir_painel():
            # expandir dispara atualizarMeuPerfil() (leitura no servidor); sem sessão
            # isso emite erro e apagaria os dados falsos — então reemito DEPOIS.
            painel = janela.findChild(QObject, "myPanel")
            if painel is not None:
                painel.setProperty("expanded", True)
            QTimer.singleShot(900, reemitir_perfil)

        def reemitir_perfil():
            perfil = dict(MEU_PERFIL)
            perfil["avatar"] = QUrl.fromLocalFile(avatar("arya", "#7C5CFF")).toString()
            bridge.myProfileReady.emit(json.dumps(perfil, ensure_ascii=False))

        QTimer.singleShot(1200, abrir_painel)

    elif modo == "widget":
        janela.hide()
        widget_engine = QQmlApplicationEngine()
        widget_engine.rootContext().setContextProperty("bridge", bridge)
        widget_engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Widget.qml")))
        if widget_engine.rootObjects():
            w = widget_engine.rootObjects()[0]
            w.setPosition(240, 200)
            bridge.setWidgetAberto(True)
            w.show()
            w.raise_()

            def congelar():
                # grabWindow mantém o alfa da janela: dá para compor sobre um fundo
                img = w.grabWindow()
                destino = os.path.join(AVATARES, "widget.png")
                img.save(destino)
                print("widget salvo em", destino)
            QTimer.singleShot(1500, congelar)

    elif modo == "toast":
        # os avisos: um de favorito (cor de destaque) e um normal (cinza)
        janela.hide()
        toast_engine = QQmlApplicationEngine()
        toast_engine.rootContext().setContextProperty("bridge", bridge)
        toast_engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Toast.qml")))
        if toast_engine.rootObjects():
            t = toast_engine.rootObjects()[0]
            t.setPosition(240, 200)
            t.setProperty("msAviso", 60000)   # tempo de sobra para o print
            QTimer.singleShot(700, lambda: bridge.amigoEntrou.emit(json.dumps({
                "id": ident("Nina Fable"), "name": "Nina Fable",
                "world": "The Great Pug · US",
                "avatar": QUrl.fromLocalFile(avatar("Nina Fable", "#7C5CFF")).toString(),
                "favorito": True, "agregado": 0,
            }, ensure_ascii=False)))
            QTimer.singleShot(900, lambda: bridge.amigoEntrou.emit(json.dumps({
                "id": ident("Duda Reis"), "name": "Duda Reis", "world": "Pixel Paradise",
                "avatar": QUrl.fromLocalFile(avatar("Duda Reis", "#9B7BFF")).toString(),
                "favorito": False, "agregado": 0,
            }, ensure_ascii=False)))

            def congelar_toast():
                t.show()
                img = t.grabWindow()
                destino = os.path.join(AVATARES, "toast.png")
                img.save(destino)
                print("toast salvo em", destino)
            QTimer.singleShot(1800, congelar_toast)

    elif modo == "aviso":
        # DEMO ao vivo: o aviso aparece de verdade na posição real do app
        # (canto inferior direito, acima da barra de tarefas, como a Steam).
        janela.hide()
        from ui_qml.main import posicionar_aviso

        toast_engine = QQmlApplicationEngine()
        toast_engine.rootContext().setContextProperty("bridge", bridge)
        toast_engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Toast.qml")))
        if toast_engine.rootObjects():
            t = toast_engine.rootObjects()[0]
            t.setProperty("msAviso", segundos * 1000)   # fica o tempo do demo na tela

            def ajustar(*_):
                if t.isVisible():
                    posicionar_aviso(t)

            t.heightChanged.connect(ajustar)
            t.visibleChanged.connect(lambda visivel: posicionar_aviso(t) if visivel else None)

            QTimer.singleShot(500, lambda: bridge.amigoEntrou.emit(json.dumps({
                "id": ident("Nina Fable"), "name": "Nina Fable",
                "world": "The Great Pug · US",
                "avatar": QUrl.fromLocalFile(avatar("Nina Fable", "#7C5CFF")).toString(),
                "favorito": True, "agregado": 0,
            }, ensure_ascii=False)))
            QTimer.singleShot(700, lambda: bridge.amigoEntrou.emit(json.dumps({
                "id": ident("Duda Reis"), "name": "Duda Reis", "world": "Pixel Paradise",
                "avatar": QUrl.fromLocalFile(avatar("Duda Reis", "#9B7BFF")).toString(),
                "favorito": False, "agregado": 0,
            }, ensure_ascii=False)))

            def medir():
                tela = t.screen()
                geo = tela.geometry() if tela else None
                util = tela.availableGeometry() if tela else None
                print(f"tela ......... {geo.width()}x{geo.height()} em ({geo.x()},{geo.y()})")
                print(f"área útil .... {util.width()}x{util.height()} em ({util.x()},{util.y()})"
                      f"  (barra de tarefas = {geo.height() - util.height()} px)")
                print(f"aviso ........ {t.width()}x{t.height()} em ({t.x()},{t.y()})")
                print(f"distância .... {util.x() + util.width() - (t.x() + t.width())} px da direita, "
                      f"{util.y() + util.height() - (t.y() + t.height())} px acima da barra")
                destino = os.path.join(AVATARES, "aviso.png")
                t.grabWindow().save(destino)
                print("print salvo em", destino)

            QTimer.singleShot(1400, medir)

    QTimer.singleShot(segundos * 1000, app.quit)
    return app.exec()


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "lista"
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    sys.exit(main(m, s))
