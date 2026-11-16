"""VRChat Friends — interface QML (PySide6/QtQuick, skill design-qml).

Ponte fina: as propriedades/slots abaixo apenas chamam core/. Nenhuma regra de dados
aqui, e o QML nao conhece nada alem deste objeto `bridge`.
"""

import json
import os
import sys
import threading
import time
from datetime import datetime

from PySide6.QtCore import Property, QLockFile, QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QFontDatabase, QGuiApplication, QIcon, QWindow
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

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
    DATA_DIR,
    ICON_FILE,
    alerts,
    avatar_cache_path,
    favorites,
    font_files,
    METHOD_LABELS,
    REFRESH_SECONDS,
    RETRY_SECONDS,
    SORT_COLUMNS,
    STATUS_DESCRIPTION_MAX,
    ApiError,
    VRChatService,
    platform_label,
    attach_logging,
    hint_for,
    load_settings,
    merge_settings,
    save_settings,
    sort_choice,
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
    sortChanged = Signal()          # coluna/direção da ordem mudou
    refreshOk = Signal()            # atualização concluída (o timer volta ao ritmo normal)
    refreshFailed = Signal()        # atualização falhou (o timer tenta antes)
    favoritosChanged = Signal()     # estrela ligada/desligada (QML rebind)
    avisosChanged = Signal()        # avisos de "amigo entrou" ligados/desligados
    amigoEntrou = Signal(str)       # aviso pronto pro toast (JSON)
    abrirAmigo = Signal(str)        # aviso clicado: abra o cartão deste id
    meuPerfilSalvo = Signal(bool, str)   # (ok, mensagem) ao editar status/bio
    profileReady = Signal(str)      # perfil do amigo em JSON
    myProfileReady = Signal(str)    # meu perfil em JSON

    # sinais internos: worker -> thread da interface
    _restored = Signal(bool)
    _friendsReady = Signal(object)
    _avatarsReady = Signal(object)
    _entradasReady = Signal(object)   # quem entrou no jogo, vindo do worker
    _errorReady = Signal(str)
    _expiredReady = Signal()
    _loginReady = Signal(bool, bool, str, str)
    _verifyReady = Signal(bool, str)
    _resentReady = Signal(bool, bool, str, str)

    def __init__(self):
        super().__init__()
        self.service = VRChatService()
        self.settings = load_settings()
        self._friends = []        # linhas (dicts) na ordem que o QML desenha
        self._all_friends = []    # Friend da última busca, sem ordem
        self._offline = []        # favoritos fora do ar (Friend sintético, sem rede)
        self._friend_by_id = {}   # id -> Friend (o perfil completo precisa do objeto)
        self._refresh_token = 0   # muda a cada atualização -> o QML reanima a lista
        self._count_text = "—"
        self._state = "loading"
        self._meta = ""
        # coluna/direção da ordenação: vêm do settings.json (padrão Status ▲)
        self._sort_column, self._sort_dir = sort_choice(
            self.settings.get("sort_column"), self.settings.get("sort_direction")
        )
        # favoritos locais: {id: {"name", "last_seen"}} — estado do settings.json
        self._favoritos = favorites.carregar(self.settings)
        self._favoritos_versao = 0
        # avisos de "amigo entrou"
        self._avisos = bool(self.settings.get("alerts", True))
        self._snapshot = None      # foto da última atualização BEM-SUCEDIDA
        self._avisados = {}        # id -> quando avisei (janela de 10 min)
        self._meu_status = ""      # meu status no VRChat; "busy" silencia os avisos
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
        self._refreshing = False   # só um ciclo de atualização por vez
        self._last_error = ""      # motivo curto da última falha (vai para a tela)

        self._restored.connect(self._on_restored)
        self._friendsReady.connect(self._apply_friends)
        self._avatarsReady.connect(self._apply_avatars)
        self._entradasReady.connect(self._on_entradas)
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
        """Só quem está ONLINE (favorito offline não conta)."""
        return len(self._all_friends)

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

    # ------------------------------------------------------------ ordenação
    @Property(str, notify=sortChanged)
    def sortColumn(self):
        """'name' | 'status' | 'world' — coluna ativa (a única que mostra seta)."""
        return self._sort_column

    @Property(str, notify=sortChanged)
    def sortDirection(self):
        """'asc' (▲) ou 'desc' (▼)."""
        return self._sort_dir

    @Property(int, constant=True)
    def statusMaxLength(self):
        """Teto do status (statusDescription) imposto pela API do VRChat."""
        return STATUS_DESCRIPTION_MAX

    @Property(int, constant=True)
    def refreshSeconds(self):
        return REFRESH_SECONDS

    @Property(int, constant=True)
    def retrySeconds(self):
        return RETRY_SECONDS

    @Property(str, notify=metaChanged)
    def lastError(self):
        """Motivo curto da última falha de atualização ('' quando deu tudo certo)."""
        return self._last_error

    # ------------------------------------------------------------ favoritos / avisos
    @Property(int, notify=favoritosChanged)
    def favoritosVersion(self):
        """Muda a cada estrela ligada/desligada — o QML reconsulta `isFavorito`."""
        return self._favoritos_versao

    @Property(bool, notify=avisosChanged)
    def avisos(self):
        """Avisos de 'amigo entrou' ligados (menu da bandeja)."""
        return self._avisos

    @Slot(str, result=bool)
    def isFavorito(self, friend_id):
        return bool(friend_id) and friend_id in self._favoritos

    # ------------------------------------------------------------ settings
    def _favoritos_no_disco(self):
        """Favoritos como estão no arquivo AGORA (None = arquivo sem a chave).

        A estrela pode ter sido clicada em outra janela do app: o arquivo é a
        verdade, não a memória desta instância.
        """
        dados = load_settings()
        if favorites.CHAVE not in dados:
            return None
        return favorites.carregar(dados)

    def _persistir(self, favoritos_novos=None, remover=()):
        """Grava só o que esta ação mudou, mesclando com o arquivo do disco.

        `self.settings` é só a visão desta janela; o arquivo pode ter sido
        mexido por outra cópia aberta do app. Favoritos entram na gravação
        apenas quando quem chama mexeu neles — assim a janela antiga não apaga
        a estrela que a outra acabou de salvar.
        """
        mudancas = {
            chave: valor
            for chave, valor in self.settings.items()
            if chave != favorites.CHAVE
        }
        if favoritos_novos is not None:
            mudancas[favorites.CHAVE] = favoritos_novos
        self.settings = merge_settings(
            mudancas, remover, carregar=load_settings, gravar=save_settings
        )
        return self.settings

    @Slot(str)
    def toggleFavorito(self, friend_id):
        """Estrela clicada: alterna e regrava o settings.json na hora."""
        amigo = self._friend_by_id.get(friend_id)
        if amigo is None:
            amigo = next((f for f in self._offline if f.id == friend_id), None)
        if amigo is None:
            return
        base = self._favoritos_no_disco()
        if base is None:
            base = self._favoritos
        self._favoritos, virou = favorites.alternar(base, amigo, time.time())
        self._persistir(favoritos_novos=self._favoritos)
        self._favoritos_versao += 1
        self.favoritosChanged.emit()
        self._recalcular_offline()
        # `self._friends` também conta: desfavoritar o último offline apaga a
        # linha dele, e sem isso ela ficava na tela até a próxima atualização
        if self._all_friends or self._offline or self._friends:
            self._friends = self._rows()
            self.friendsChanged.emit()

    @Slot(bool)
    def setAvisos(self, ligado):
        ligado = bool(ligado)
        if ligado == self._avisos:
            return
        self._avisos = ligado
        self.settings["alerts"] = ligado
        self._persistir()
        self.avisosChanged.emit()

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
        self._meu_status = ((self.service.client.me or {}).get("status") or "") if ok else ""
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
        # a dica de login antiga não serve mais (apagar de verdade: merge não remove)
        self.settings.pop("login_hint", None)
        self._persistir(remover=("login_hint",))
        self._logged_in = True
        self._user_name = self.service.display_name
        self._meu_status = (self.service.client.me or {}).get("status") or ""
        self._snapshot = None      # primeira atualização após entrar só aprende a foto
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
        self._snapshot = None      # 2FA concluído = sessão nova, foto nova
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
        """Um ciclo por vez: antes, um clique durante a atualização era descartado
        em silêncio (o usuário via 'nada aconteceu' e clicava de novo)."""
        if self._refreshing or self._busy:
            return
        self._refreshing = True
        self._busy = True
        self.busyChanged.emit()
        self._meta = "atualizando…"
        self.metaChanged.emit()
        self._thread(self._work_refresh)

    @Slot()
    def autoRefresh(self):
        """Chamado pelo timer de REFRESH_SECONDS (antes esse timer não existia)."""
        if not self._logged_in:
            return
        self.refresh()

    def _work_refresh(self):
        try:
            amigos = self.service.fetch_friends()
            self._friendsReady.emit(amigos)
            self.service.fetch_avatars(amigos, size=AVATAR_PX)
            self._avatarsReady.emit(amigos)
            # aviso de "entrou no jogo" só depois dos avatares: o cartão já tem ícone
            self._avisar_entradas(amigos)
        except PermissionError:
            self._expiredReady.emit()
        except ApiError as exc:
            self._errorReady.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self._errorReady.emit(repr(exc))

    # ------------------------------------------------------------ avisos
    def _avisar_entradas(self, amigos):
        """Quem passou para 'no jogo' desde a foto anterior (roda no worker).

        Só o worker mexe em `_snapshot`, e só no caminho de sucesso: atualização
        que falhou não chega aqui e portanto não inventa entrada nem perde a foto.
        """
        atual = alerts.snapshot(amigos)
        novos = alerts.entradas_novas(self._snapshot, atual)
        self._snapshot = atual
        if novos:
            self._entradasReady.emit(novos)

    def _on_entradas(self, novos):
        """Política do aviso (thread da interface): ligado? não estou Busy? 10 min?"""
        if not self._logged_in or not self._avisos:
            return
        if (self._meu_status or "").strip().lower() == "busy":
            return
        agora = time.time()
        novos = alerts.filtrar_intervalo(novos, self._avisados, agora)
        if not novos:
            return
        for dado in novos:
            self._avisados[dado["id"]] = agora
        for aviso in alerts.agrupar(novos, self._favoritos):
            if aviso.get("avatar"):
                aviso["avatar"] = QUrl.fromLocalFile(aviso["avatar"]).toString()
            self.amigoEntrou.emit(json.dumps(aviso, ensure_ascii=False))

    @Slot(str)
    def clickAviso(self, friend_id):
        """Cartão do aviso clicado: traz a janela e abre o perfil."""
        if not friend_id:
            return
        self.requestShow.emit()
        self.abrirAmigo.emit(friend_id)

    def _rows(self):
        """Linhas do QML na ordem final: favoritos online, resto dos online, offline.

        A ordem é decidida no core (`favorites.montar_lista`); aqui só entra o que é
        de tela: URL do avatar e as marcas `favorito` / `offline`. as_dict() do
        modelo, não um dict à mão: montar campo a campo já deixou ocupação/capacidade
        de fora e o QML nunca recebia o número.
        """
        linhas = []
        ordenados = favorites.montar_lista(
            self._all_friends, self._offline, self._favoritos,
            self._sort_column, self._sort_dir,
        )
        for f in ordenados:
            dados = f.as_dict()
            dados["avatar"] = QUrl.fromLocalFile(f.avatar).toString() if f.avatar else ""
            dados["favorito"] = f.id in self._favoritos
            dados["offline"] = (f.status or "").lower() == "offline"
            linhas.append(dados)
        return linhas

    def _recalcular_offline(self):
        """Favoritos fora do ar: nenhuma requisição, avatar do cache em disco.

        Só roda no caminho de atualização bem-sucedida (ou ao mexer numa estrela):
        em falha de rede o bloco anterior fica como está.
        """
        self._offline = favorites.amigos_offline(
            self._favoritos,
            {f.id for f in self._all_friends},
            avatar_de=lambda uid: avatar_cache_path(uid, AVATAR_PX),
        )

    def _apply_friends(self, amigos):
        self._busy = False
        self._refreshing = False
        self.busyChanged.emit()
        self._all_friends = list(amigos)
        # favoritos: o arquivo é a verdade (outra janela pode ter estrelado alguém
        # entre uma atualização e outra); nome e "visto" só no caminho de sucesso
        base = self._favoritos_no_disco()
        if base is not None and base != self._favoritos:
            self._favoritos = base
        self._favoritos, mudou = favorites.marcar_vistos(self._favoritos, amigos, time.time())
        if mudou:
            self._persistir(favoritos_novos=self._favoritos)
        self._recalcular_offline()
        self._friend_by_id = {f.id: f for f in amigos}
        self._friend_by_id.update({f.id: f for f in self._offline})
        self._friends = self._rows()
        n = len(amigos)
        self._count_text = f"{n} amigo{'s' if n != 1 else ''} online"
        self._state = "list" if self._friends else "empty"
        self._last_update = datetime.now()
        self._last_error = ""
        self._refresh_token += 1
        self.friendsChanged.emit()
        self.refreshTokenChanged.emit()
        self.countChanged.emit()
        self.stateChanged.emit()
        self._update_meta()
        self.refreshOk.emit()

    @Slot(str)
    def setSort(self, column):
        """Cabeçalho clicado: mesma coluna alterna, coluna nova começa crescente.

        A ordem é gravada no settings.json e aplicada na hora, sem nova requisição.
        """
        if column not in SORT_COLUMNS:
            return
        if column == self._sort_column:
            direcao = "desc" if self._sort_dir == "asc" else "asc"
        else:
            direcao = "asc"
        self._sort_column, self._sort_dir = column, direcao
        self.settings["sort_column"] = column
        self.settings["sort_direction"] = direcao
        self._persistir()
        self.sortChanged.emit()
        if self._all_friends:
            self._friends = self._rows()
            # só friendsChanged: refreshToken fica parado para a lista não reanimar
            self.friendsChanged.emit()

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
        self._refreshing = False
        self.busyChanged.emit()
        # o log guarda o erro cru; a tela mostra o motivo em duas palavras
        print(f"[erro] {msg}", file=sys.stderr)
        self._last_error = _motivo_curto(msg)
        if self._friends:
            # keep the list on screen, but tell the truth about its age
            self._meta = f"desatualizado · {self._last_error}"
            self.metaChanged.emit()
            self.refreshFailed.emit()
            return
        self._state = "error"
        self._count_text = "—"
        self._meta = f"falha ao atualizar · {self._last_error}"
        self.stateChanged.emit()
        self.countChanged.emit()
        self.metaChanged.emit()
        self.refreshFailed.emit()

    def _on_expired(self):
        self._busy = False
        self._refreshing = False
        self.busyChanged.emit()
        # sessão nova = foto nova: nada de avisar "entrou" comparando com a sessão antiga
        self._snapshot = None
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
            self._meu_status = perfil.status or self._meu_status
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
            perfil = self.service.my_profile(force=force)
            # meu status decide se o aviso fala ou não (Busy silencia)
            self._meu_status = perfil.status or ""
            self.myProfileReady.emit(_json_perfil(perfil))
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
        self._persistir()
        self.widgetAbertoChanged.emit()
        self.requestWidget.emit(valor)

    @Slot(int, int)
    def salvarWidgetPos(self, x, y):
        self.settings["widget_pos"] = [int(x), int(y)]
        self._persistir()

    @Slot(bool)
    def setTopmost(self, valor):
        self._topmost = bool(valor)
        self.settings["topmost"] = self._topmost
        self._persistir()
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


def instancia_unica(avisar=True):
    """Deixa rodar UMA copia do app e devolve a trava (None = ja havia outra).

    Com duas janelas abertas, a mais antiga regravava o settings.json com a lista
    velha de favoritos e apagava a estrela salva pela outra (visto em 16/11).
    A trava morre junto com o processo; se sobrou de um crash, o PID nao existe
    mais e `removeStaleLockFile()` a libera. `avisar=False` e para os testes
    (sem caixa de dialogo).
    """
    trava = QLockFile(os.path.join(DATA_DIR, "app.lock"))
    if trava.tryLock(200):
        return trava
    if trava.removeStaleLockFile() and trava.tryLock(200):
        return trava
    if avisar:
        QMessageBox.information(
            None,
            APP_NAME,
            "O VRChat Friends já está aberto.\n\n"
            "Clique no ícone dele na bandeja (perto do relógio) para abrir a janela.",
        )
    return None


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


def posicionar_aviso(janela, tela=None, margem=0):
    """Põe a janela do aviso no canto INFERIOR DIREITO da TELA PRINCIPAL.

    `availableGeometry` já desconta a barra de tarefas e vem em pixels
    independentes de DPI — é exatamente o "acima da barra, como a notificação
    da Steam". Margem 0: o respiro de 8 px vem do padding do cartão no QML,
    então o vão visível até a barra fica igual ao da Steam.

    O aviso pertence ao sistema, não à janela do app: ele nasce no monitor
    principal mesmo com o app aberto no secundário (pedido do dono, 16/11).
    `tela` só existe para o teste (ou) forçar outro monitor.
    Devolve (x, y) para quem quiser registrar/logar.
    """
    if tela is None:
        tela = QGuiApplication.primaryScreen()
    if tela is None:
        return None
    area = tela.availableGeometry()
    x = int(area.x() + area.width() - janela.width() - margem)
    y = int(area.y() + area.height() - janela.height() - margem)
    try:
        janela.setPosition(x, y)
    except Exception:
        pass
    return x, y


def criar_timer_refresh(bridge, parent=None):
    """Timer da atualização automática (o que faltava na v1.0).

    Ritmo normal: REFRESH_SECONDS. Depois de uma falha cai para RETRY_SECONDS e
    volta ao normal na primeira atualização que der certo — é o "atualizar duas
    vezes" resolvido sem clique nenhum.
    """
    timer = QTimer(parent)
    timer.setInterval(REFRESH_SECONDS * 1000)
    timer.timeout.connect(bridge.autoRefresh)
    bridge.refreshOk.connect(lambda: timer.setInterval(REFRESH_SECONDS * 1000))
    bridge.refreshFailed.connect(lambda: timer.setInterval(RETRY_SECONDS * 1000))
    timer.start()
    return timer


def _motivo_curto(msg):
    """Erro cru de requests/HTTP -> motivo que cabe no rodapé da janela."""
    baixo = (msg or "").lower()
    if "429" in baixo or "too many" in baixo:
        return "limite de requisições"
    if "timed out" in baixo or "timeout" in baixo:
        return "sem resposta do VRChat"
    if "connection" in baixo or "max retries" in baixo or "getaddrinfo" in baixo:
        return "sem conexão"
    if any(codigo in baixo for codigo in ("500", "502", "503", "504")):
        return "servidor instável"
    if "401" in baixo or "403" in baixo:
        return "sessão recusada"
    texto = (msg or "").strip().splitlines()
    return (texto[0][:60] if texto else "erro desconhecido")


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

    trava = instancia_unica()
    if trava is None:
        return 0
    app.trava_app = trava      # precisa viver enquanto o app estiver aberto

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
        bridge._persistir()
        app.quit()

    bridge.requestHide.connect(janela.hide)
    bridge.requestShow.connect(_mostrar)
    bridge.requestTopmost.connect(_aplicar_topmost)
    bridge.requestQuit.connect(_sair)

    # ---- avisos "amigo entrou": janela própria, sem roubar foco, canto da tela
    toast = None
    try:
        eng_toast = QQmlApplicationEngine()
        eng_toast.rootContext().setContextProperty("bridge", bridge)
        eng_toast.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Toast.qml")))
        if eng_toast.rootObjects():
            toast = eng_toast.rootObjects()[0]
            # o canto arredondado é do cartão desenhado no QML: o DWM não arredonda de novo
            arredondar_janela(toast, 1)
    except Exception as exc:
        print("avisos indisponíveis:", exc, file=sys.stderr)
        toast = None

    def _posicionar_toast(*_):
        """Canto inferior direito do monitor PRINCIPAL (`posicionar_aviso`)."""
        if toast is not None:
            posicionar_aviso(toast)

    if toast is not None:
        # a altura muda com a quantidade de cartões: reposiciona a cada mudança
        toast.heightChanged.connect(_posicionar_toast)
        toast.visibleChanged.connect(lambda visivel: _posicionar_toast() if visivel else None)

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
        # liga/desliga os avisos de "amigo entrou" (fica salvo no settings.json)
        acao_avisos = menu.addAction("Avisos de amigo entrou")
        acao_avisos.setCheckable(True)
        acao_avisos.setChecked(bridge.avisos)
        acao_avisos.toggled.connect(bridge.setAvisos)
        bridge.avisosChanged.connect(lambda: acao_avisos.setChecked(bridge.avisos))
        menu.addSeparator()
        menu.addAction("Sair", app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip(APP_NAME)
        tray.show()
    except Exception:
        tray = None

    # atualização automática (o README prometia uma a cada 45 s e não existia)
    bridge.timer_refresh = criar_timer_refresh(bridge, app)

    bridge.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
