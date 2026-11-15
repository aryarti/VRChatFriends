"""VRChat Friends — interface QML (PySide6/QtQuick, skill design-qml).

Ponte fina: as propriedades/slots abaixo apenas chamam core/. Nenhuma regra de dados
aqui, e o QML nao conhece nada alem deste objeto `bridge`.
"""

import os
import sys
import threading
from datetime import datetime

from PySide6.QtCore import Property, QObject, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QFontDatabase, QIcon, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

# congelado (PyInstaller): tudo vive em sys._MEIPASS, não ao lado do .py
_AQUI = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(_AQUI)
if getattr(sys, "frozen", False):
    _RAIZ = getattr(sys, "_MEIPASS", _RAIZ)
    _AQUI = os.path.join(_RAIZ, "ui_qml")
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from core import (  # noqa: E402
    APP_NAME,
    APP_VERSION,
    ICON_FILE,
    font_files,
    METHOD_LABELS,
    REFRESH_SECONDS,
    ApiError,
    VRChatService,
    platform_label,
    attach_logging,
    hint_for,
    load_settings,
    save_settings,
)

QML_DIR = os.path.join(_AQUI, "qml")
AVATAR_PX = 56  # 2x de 28 (tela HiDPI) — o QML desenha em 28


class Bridge(QObject):
    """Tudo que o QML enxerga. Thread-safe: workers emitem sinais, slots aplicam."""

    # notificações para o QML
    friendsChanged = Signal()
    countChanged = Signal()
    stateChanged = Signal()
    metaChanged = Signal()
    loginChanged = Signal()
    busyChanged = Signal()
    titleChanged = Signal()
    topmostChanged = Signal()
    widgetAbertoChanged = Signal()
    requestHide = Signal()
    requestQuit = Signal()
    requestTopmost = Signal(bool)
    requestWidget = Signal(bool)
    requestShow = Signal()
    refreshTokenChanged = Signal()
    meuPerfilSalvo = Signal(bool, str)   # (ok, mensagem) ao editar status/bio
    profileReady = Signal(str)      # perfil do amigo em JSON
    myProfileReady = Signal(str)    # meu perfil em JSON

    # sinais internos: worker -> thread da interface
    _restored = Signal(bool)
    _friendsReady = Signal(object)
    _avatarsReady = Signal(object)
    _errorReady = Signal(str)
    _expiredReady = Signal()
    _loginReady = Signal(bool, bool, str, str)
    _verifyReady = Signal(bool, str)
    _resentReady = Signal(bool, bool, str, str)

    def __init__(self):
        super().__init__()
        self.service = VRChatService()
        self.settings = load_settings()
        self._friends = []
        self._friend_by_id = {}   # id -> Friend (o perfil completo precisa do objeto)
        self._refresh_token = 0   # muda a cada atualização -> o QML reanima a lista
        self._count_text = "—"
        self._state = "loading"
        self._meta = ""
        self._logged_in = False
        self._stage = "creds"
        self._hint = (
            "A senha é usada uma única vez para criar a sessão; só o cookie de sessão "
            "fica salvo nesta máquina."
        )
        self._code_label = "Código do e-mail"
        self._message = ""
        self._message_kind = "info"
        self._busy = False
        self._title = APP_NAME
        self._topmost = bool(self.settings.get("topmost", False))
        self._widget_aberto = bool(self.settings.get("widget_aberto", False))
        self._last_user = self.settings.get("last_user", "")
        self._user_name = ""
        self._last_update = None

        self._restored.connect(self._on_restored)
        self._friendsReady.connect(self._apply_friends)
        self._avatarsReady.connect(self._apply_avatars)
        self._errorReady.connect(self._on_error)
        self._expiredReady.connect(self._on_expired)
        self._loginReady.connect(self._on_login)
        self._verifyReady.connect(self._on_verify)
        self._resentReady.connect(self._on_resent)

    # ------------------------------------------------------------ propriedades
    @Property("QVariantList", notify=friendsChanged)
    def friends(self):
        return self._friends

    @Property(str, notify=countChanged)
    def countText(self):
        return self._count_text

    @Property(int, notify=countChanged)
    def count(self):
        return len(self._friends)

    @Property(bool, notify=widgetAbertoChanged)
    def widgetAberto(self):
        return self._widget_aberto

    @Property(str, notify=stateChanged)
    def state(self):
        return self._state

    @Property(str, notify=metaChanged)
    def metaText(self):
        return self._meta

    @Property(bool, notify=loginChanged)
    def loggedIn(self):
        return self._logged_in

    @Property(str, notify=loginChanged)
    def stage(self):
        return self._stage

    @Property(str, notify=loginChanged)
    def loginHint(self):
        return self._hint

    @Property(str, notify=loginChanged)
    def codeLabel(self):
        return self._code_label

    @Property(str, notify=loginChanged)
    def message(self):
        return self._message

    @Property(str, notify=loginChanged)
    def messageKind(self):
        return self._message_kind

    @Property(str, notify=loginChanged)
    def lastUser(self):
        return self._last_user

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(int, notify=refreshTokenChanged)
    def refreshToken(self):
        return self._refresh_token

    @Property(str, notify=titleChanged)
    def windowTitle(self):
        return self._title

    @Property(bool, notify=topmostChanged)
    def topmost(self):
        return self._topmost

    # ------------------------------------------------------------ helpers
    def _set_message(self, texto, kind="info"):
        self._message = texto
        self._message_kind = kind
        self.loginChanged.emit()

    def _update_meta(self):
        when = self._last_update.strftime("%H:%M") if self._last_update else "—"
        self._meta = f"{self._user_name} · atualizado {when}" if self._user_name else f"atualizado {when}"
        self.metaChanged.emit()

    def _thread(self, fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    # ------------------------------------------------------------ sessão
    @Slot()
    def start(self):
        self._thread(self._work_restore)

    def _work_restore(self):
        try:
            ok = self.service.restore()
        except Exception:
            ok = False
        self._restored.emit(ok)

    def _on_restored(self, ok):
        self._logged_in = bool(ok)
        self._user_name = self.service.display_name if ok else ""
        self._title = f"{APP_NAME} — {self._user_name}" if self._user_name else APP_NAME
        self.loginChanged.emit()
        self.titleChanged.emit()
        if ok:
            self._update_meta()
            self.refresh()

    @Slot(str, str)
    def doLogin(self, usuario, senha):
        if self._busy:
            return
        if not usuario.strip() or not senha:
            self._set_message("Preencha usuário e senha.", "error")
            return
        self._busy = True
        self.busyChanged.emit()
        self._set_message("")
        self._thread(self._work_login, usuario.strip(), senha)

    def _work_login(self, usuario, senha):
        try:
            ok, need_2fa, msg = self.service.login(usuario, senha)
        except Exception as exc:  # noqa: BLE001
            ok, need_2fa, msg = False, False, str(exc)
        self._loginReady.emit(ok, need_2fa, msg, usuario)

    def _on_login(self, ok, need_2fa, msg, usuario):
        self._busy = False
        self.busyChanged.emit()
        if need_2fa:
            tipos = msg.split(",")
            primario = "emailOtp" if "emailOtp" in tipos else tipos[0]
            self._stage = "2fa"
            self._hint = hint_for(primario)
            self._code_label = {
                "totp": "Código do app autenticador",
                "otp": "Código de recuperação",
            }.get(primario, "Código do e-mail")
            self._message = ""
            self.loginChanged.emit()
            return
        if not ok:
            self._set_message(msg, "error")
            return
        self._last_user = usuario
        self.settings["last_user"] = usuario
        self.settings.pop("login_hint", None)
        save_settings(self.settings)
        self._logged_in = True
        self._user_name = self.service.display_name
        self._title = f"{APP_NAME} — {self._user_name}" if self._user_name else APP_NAME
        self._message = ""
        self.loginChanged.emit()
        self.titleChanged.emit()
        self._update_meta()
        self.refresh()

    @Slot(str)
    def doVerify(self, codigo):
        if self._busy:
            return
        if not codigo.strip():
            self._set_message("Digite o código que chegou.", "info")
            return
        self._busy = True
        self.busyChanged.emit()
        self._set_message("")
        self._thread(self._work_verify, codigo)

    def _work_verify(self, codigo):
        try:
            ok, msg = self.service.verify(codigo, "emailOtp")
        except Exception as exc:  # noqa: BLE001
            ok, msg = False, str(exc)
        self._verifyReady.emit(ok, msg)

    def _on_verify(self, ok, msg):
        self._busy = False
        self.busyChanged.emit()
        if not ok:
            self._set_message(msg, "error")
            return
        self._logged_in = True
        self._user_name = self.service.display_name
        self._title = f"{APP_NAME} — {self._user_name}" if self._user_name else APP_NAME
        self._message = ""
        self.loginChanged.emit()
        self.titleChanged.emit()
        self._update_meta()
        self.refresh()

    @Slot()
    def resend(self):
        if self._busy:
            return
        usuario = self._last_user
        self._busy = True
        self.busyChanged.emit()
        self._thread(self._work_resend, usuario)

    def _work_resend(self, usuario):
        # o VRChat reenvia o código quando o login é refeito
        self._resentReady.emit(True, True, "novo código pedido", usuario)

    def _on_resent(self, ok, need_2fa, msg, usuario):
        self._busy = False
        self.busyChanged.emit()
        self._set_message("Pedindo novo código… digite o que chegar no e-mail.", "ok")

    @Slot()
    def backToCreds(self):
        self._stage = "creds"
        self._message = ""
        self.loginChanged.emit()

    # ------------------------------------------------------------ dados
    @Slot()
    def refresh(self):
        if self._busy:
            return
        self._busy = True
        self.busyChanged.emit()
        self._meta = "atualizando…"
        self.metaChanged.emit()
        self._thread(self._work_refresh)

    def _work_refresh(self):
        try:
            amigos = self.service.fetch_friends()
            self._friendsReady.emit(amigos)
            self.service.fetch_avatars(amigos, size=AVATAR_PX)
            self._avatarsReady.emit(amigos)
        except PermissionError:
            self._expiredReady.emit()
        except ApiError as exc:
            self._errorReady.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self._errorReady.emit(repr(exc))

    def _apply_friends(self, amigos):
        self._busy = False
        self.busyChanged.emit()
        self._friend_by_id = {f.id: f for f in amigos}
        # as_dict() do modelo, não um dict à mão: montar campo a campo aqui já deixou
        # ocupação/capacidade de fora e o QML nunca recebia o número.
        self._friends = []
        for f in amigos:
            dados = f.as_dict()
            dados["avatar"] = QUrl.fromLocalFile(f.avatar).toString() if f.avatar else ""
            self._friends.append(dados)
        n = len(amigos)
        self._count_text = f"{n} amigo{'s' if n != 1 else ''} online"
        self._state = "list" if n else "empty"
        self._last_update = datetime.now()
        self._refresh_token += 1
        self.friendsChanged.emit()
        self.refreshTokenChanged.emit()
        self.countChanged.emit()
        self.stateChanged.emit()
        self._update_meta()

    def _apply_avatars(self, amigos):
        mapa = {f.id: f.avatar for f in amigos if f.avatar}
        if not mapa:
            return
        novos = []
        for linha in self._friends:
            caminho = mapa.get(linha["id"])
            if caminho and not linha["avatar"]:
                linha = dict(linha)
                linha["avatar"] = QUrl.fromLocalFile(caminho).toString()
            novos.append(linha)
        self._friends = novos
        self.friendsChanged.emit()

    def _on_error(self, msg):
        self._busy = False
        self.busyChanged.emit()
        print(f"[erro] {msg}", file=sys.stderr)
        if self._friends:
            self._meta = "falha ao atualizar"
            self.metaChanged.emit()
            return
        self._state = "error"
        self._count_text = "—"
        self._meta = "falha ao atualizar"
        self.stateChanged.emit()
        self.countChanged.emit()
        self.metaChanged.emit()

    def _on_expired(self):
        self._busy = False
        self.busyChanged.emit()
        self._logged_in = False
        self._stage = "creds"
        self._message = "A sessão expirou. Entre novamente."
        self._message_kind = "error"
        self.loginChanged.emit()

    # ------------------------------------------------------------ ações
    def _row(self, index):
        if 0 <= index < len(self._friends):
            return self._friends[index]
        return None

    @Slot(int)
    def copyWorld(self, index):
        linha = self._row(index)
        if not linha:
            return
        QApplication.clipboard().setText(linha["world"])
        self._meta = "nome do mundo copiado"
        self.metaChanged.emit()

    @Slot(int)
    def copyLaunch(self, index):
        linha = self._row(index)
        if not linha or not linha.get("location"):
            return
        QApplication.clipboard().setText(f"vrchat://launch?id={linha['location']}")
        self._meta = "link copiado"
        self.metaChanged.emit()

    # ------------------------------------------------------------ perfil
    @Slot(str)
    def requestProfile(self, friend_id):
        """Busca o perfil completo em segundo plano e devolve JSON."""
        amigo = self._friend_by_id.get(friend_id)
        if amigo is None:
            self.profileReady.emit("{}")
            return
        self._thread(self._work_profile, amigo)

    def _work_profile(self, amigo):
        try:
            self.profileReady.emit(_json_perfil(self.service.fetch_profile(amigo)))
        except Exception as exc:  # noqa: BLE001
            self.profileReady.emit(_json_perfil(None, str(exc)))

    @Property(str, constant=True)
    def versionText(self):
        return f"v{APP_VERSION}"

    @Slot(str)
    def setMyStatus(self, status):
        """Troca meu status no VRChat ('active', 'ask me', 'join me', 'busy')."""
        self._thread(lambda: self._work_salvar(status=status))

    @Slot(str)
    def setMyBio(self, texto):
        """Salva minha bio (statusDescription) no VRChat."""
        self._thread(lambda: self._work_salvar(bio=texto))

    def _work_salvar(self, status=None, bio=None):
        try:
            perfil = self.service.update_me(
                status=status, status_description=bio
            )
            self.myProfileReady.emit(_json_perfil(perfil))
            self.meuPerfilSalvo.emit(True, "salvo no VRChat")
        except PermissionError:
            self.meuPerfilSalvo.emit(False, "sessão expirada")
            self._expiredReady.emit()
        except Exception as exc:  # noqa: BLE001
            self.meuPerfilSalvo.emit(False, str(exc)[:120])

    @Slot()
    def requestMyProfile(self):
        self._thread(self._work_my_profile)

    @Slot()
    def atualizarMeuPerfil(self):
        """Relê o meu perfil no servidor (usado ao abrir o painel)."""
        self._thread(lambda: self._work_my_profile(force=True))

    def _work_my_profile(self, force=False):
        try:
            self.myProfileReady.emit(_json_perfil(self.service.my_profile(force=force)))
        except Exception as exc:  # noqa: BLE001
            self.myProfileReady.emit(_json_perfil(None, str(exc)))

    @Slot(bool)
    def setWidgetAberto(self, valor):
        """Mostra/esconde o widget flutuante (fica lembrado entre sessões)."""
        valor = bool(valor)
        if valor == self._widget_aberto:
            return
        self._widget_aberto = valor
        self.settings["widget_aberto"] = valor
        save_settings(self.settings)
        self.widgetAbertoChanged.emit()
        self.requestWidget.emit(valor)

    @Slot(int, int)
    def salvarWidgetPos(self, x, y):
        self.settings["widget_pos"] = [int(x), int(y)]
        save_settings(self.settings)

    @Slot(bool)
    def setTopmost(self, valor):
        self._topmost = bool(valor)
        self.settings["topmost"] = self._topmost
        save_settings(self.settings)
        self.topmostChanged.emit()
        self.requestTopmost.emit(self._topmost)

    @Slot()
    def hideToTray(self):
        self.requestHide.emit()

    @Slot()
    def showWindow(self):
        """Usado pelo QML (ex.: atalho) para voltar da bandeja."""
        self.requestShow.emit()

    @Slot()
    def quitApp(self):
        self.requestQuit.emit()


def arredondar_janela(janela, preferencia=2):
    """Cantos arredondados NATIVOS no Windows 11 (DWM), sem transparência.

    DWMWA_WINDOW_CORNER_PREFERENCE = 33; DWMWCP_ROUND = 2. O DWM também desliga o
    arredondamento sozinho quando a janela está maximizada — que é justamente o bug
    que a skill design-qml alerta quando se faz isso "na mão" com transparência.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        from ctypes import byref, c_int

        hwnd = int(janela.winId())
        attr = c_int(preferencia)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, byref(attr), ctypes.sizeof(attr)
        )
        return res == 0
    except Exception:
        return False


def _json_perfil(perfil, erro=""):
    """Profile -> JSON que o QML lê (avatar como URL de arquivo)."""
    import json

    if perfil is None:
        return json.dumps({"erro": erro}, ensure_ascii=False)
    dados = perfil.as_dict()
    dados["avatar"] = QUrl.fromLocalFile(perfil.avatar).toString() if perfil.avatar else ""
    dados["platform_label"] = platform_label(perfil.platform) if perfil.platform else ""
    return json.dumps(dados, ensure_ascii=False)


def main():
    attach_logging()
    QQuickStyle.setStyle("Basic")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # Inter embarcada (assets/fonts): no Qt basta registrar antes de carregar o QML
    for arquivo in font_files():
        QFontDatabase.addApplicationFont(arquivo)

    # Ícone ANTES da janela existir: é o que a barra de tarefas mostra.
    icone = QIcon(ICON_FILE) if os.path.exists(ICON_FILE) else QIcon()
    if not icone.isNull():
        app.setWindowIcon(icone)

    bridge = Bridge()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Main.qml")))
    if not engine.rootObjects():
        print("Falha ao carregar o QML", file=sys.stderr)
        return 1

    janela = engine.rootObjects()[0]
    if not icone.isNull():
        janela.setIcon(icone)      # a janela frameless não herda: precisa explícito

    # cantos arredondados nativos (DWM) — sem transparência e sem quebrar ao maximizar
    janela.show()
    arredondar_janela(janela)

    def _mostrar():
        """Traz de volta da bandeja E de minimizado."""
        try:
            if janela.visibility() == QWindow.Visibility.Minimized:
                janela.setVisibility(QWindow.Visibility.Windowed)
            janela.show()
            janela.raise_()
            janela.requestActivate()
        except Exception:
            pass

    def _aplicar_topmost(valor):
        janela.setFlag(Qt.WindowType.WindowStaysOnTopHint, bool(valor))
        janela.show()

    # ---- widget flutuante: janela própria, compacta, sempre no topo
    widget = None
    try:
        eng_widget = QQmlApplicationEngine()
        eng_widget.rootContext().setContextProperty("bridge", bridge)
        eng_widget.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Widget.qml")))
        if eng_widget.rootObjects():
            widget = eng_widget.rootObjects()[0]
            # o canto é do card desenhado no QML: o DWM não deve arredondar de novo
            arredondar_janela(widget, 1)
    except Exception as exc:
        print("widget indisponível:", exc, file=sys.stderr)
        widget = None

    def _posicionar_widget():
        pos = bridge.settings.get("widget_pos")
        if isinstance(pos, (list, tuple)) and len(pos) == 2:
            try:
                widget.setPosition(int(pos[0]), int(pos[1]))
            except Exception:
                pass

    def _aplicar_widget(aberto):
        if widget is None:
            return
        try:
            if aberto:
                _posicionar_widget()
                widget.show()
                widget.raise_()
            else:
                widget.hide()
        except Exception:
            pass

    bridge.requestWidget.connect(_aplicar_widget)
    if bridge.widgetAberto and widget is not None:
        _posicionar_widget()

    def _sair():
        """Guarda posição do widget + settings antes de fechar."""
        try:
            if widget is not None:
                bridge.settings["widget_pos"] = [int(widget.x()), int(widget.y())]
        except Exception:
            pass
        save_settings(bridge.settings)
        app.quit()

    bridge.requestHide.connect(janela.hide)
    bridge.requestShow.connect(_mostrar)
    bridge.requestTopmost.connect(_aplicar_topmost)
    bridge.requestQuit.connect(_sair)

    tray = None
    try:
        tray = QSystemTrayIcon(QIcon(ICON_FILE), app)
        menu = QMenu()
        menu.addAction("Mostrar", _mostrar)
        tray.activated.connect(
            lambda motivo: _mostrar()
            if motivo in (QSystemTrayIcon.ActivationReason.Trigger,
                          QSystemTrayIcon.ActivationReason.DoubleClick)
            else None
        )
        menu.addAction("Atualizar agora", bridge.refresh)
        menu.addSeparator()
        menu.addAction("Sair", app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip(APP_NAME)
        tray.show()
    except Exception:
        tray = None

    bridge.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
