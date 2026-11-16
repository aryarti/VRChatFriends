pragma Singleton
import QtQuick

// Tokens da UI QML (skill design-qml). Única fonte de valores visuais.
// Os quatro status e as medidas da lista são adições do app: a skill define
// accent/success/danger, mas não cores de status nem altura de linha.
QtObject {
    // Superfícies
    readonly property color bg0: "#0E0F12"
    readonly property color bg1: "#15171B"
    readonly property color bg2: "#1C1F24"
    readonly property color bg3: "#252932"
    readonly property color bg3Hover: "#2F343F"

    // Texto
    readonly property color text1: "#F2F3F5"
    readonly property color text2: "#A0A6B0"
    readonly property color text3: "#6B7280"

    // Destaque
    readonly property color accent: "#7C5CFF"
    readonly property color accentHover: "#9279FF"
    readonly property color accentStrong: "#6B4BEA"   // fill do botão primário (branco 5.5:1)
    readonly property color accentStrongHover: "#7A5CF0"
    readonly property color danger: "#ED4245"
    readonly property color success: "#3BA55D"
    readonly property color border: "#23262C"

    // Espaçamento (escala de 4)
    readonly property int s1: 4
    readonly property int s2: 8
    readonly property int s3: 12
    readonly property int s4: 16
    readonly property int s5: 24
    readonly property int s6: 32

    // Raios
    readonly property int rSm: 6
    readonly property int rMd: 10
    readonly property int rLg: 16

    // widget flutuante (janela própria, compacta)
    readonly property int widgetW: 268
    readonly property int widgetH: 80

    // Tipografia
    readonly property string fontFamily: "Inter 18pt"   // assets/fonts (OFL); fallback: Segoe UI
    readonly property string monoFamily: "Consolas"
    readonly property int fsXs: 11
    readonly property int fsSm: 12
    readonly property int fsMd: 13
    readonly property int fsLg: 15
    readonly property int fsXl: 20

    // Movimento (zerado quando reducedMotion)
    readonly property bool reducedMotion: false
    readonly property int easeOut: Easing.OutCubic      // entradas
    readonly property int easeIn: Easing.InCubic        // saídas
    readonly property int easeInOut: Easing.InOutCubic  // A -> B
    readonly property int durFast: reducedMotion ? 0 : 120
    readonly property int durBase: reducedMotion ? 0 : 200
    readonly property int durSlow: reducedMotion ? 0 : 320

    // Status — mesmas cores da UI Tkinter, para as duas versões ficarem iguais
    readonly property color statusOnline: success
    readonly property color statusJoin: "#4FC3E8"
    readonly property color statusAsk: "#E8B04B"
    readonly property color statusBusy: "#FF7B72"
    readonly property color statusOffline: text2
    readonly property int statusDotSize: 10     // bolinha de status sob o avatar recolhido
    readonly property int statusDotRing: 2      // anel que separa a bolinha do avatar

    // Cabeçalho da lista: coluna ativa (seta ▲/▼ só nela)
    readonly property color headerHover: text2
    readonly property color headerActive: text1

    // Estrela de favorito (linha e cartão do amigo)
    readonly property int starSize: 16
    readonly property color starOn: accent
    readonly property color starOff: text3
    readonly property color favoritoBorder: accent
    readonly property real offlineOpacity: 0.55   // favorito fora do ar, "apagado"

    // Aviso "amigo entrou": janela própria no canto da tela
    readonly property int toastWidth: 360          // parecido com o toast da Steam
    readonly property int toastMs: 5000           // tempo na tela (pausa com o mouse em cima)
    readonly property int toastMax: 3             // cartões empilhados no máximo
    readonly property int toastMargin: 0          // espelho de posicionar_aviso() no main.py
    readonly property color toastBg: "#15171B"
    readonly property color toastFavoritoBg: "#261C4F"   // accent escurecido
    readonly property color toastBorder: Qt.rgba(1, 1, 1, 0.08)

    // Gradiente do cabeçalho (o único da tela, permitido pela skill)
    readonly property color headerGradientStart: "#1A1530"

    // Janela frameless: barra de título própria + alças de redimensionamento
    readonly property int titleBarHeight: 36
    readonly property int titleButtonWidth: 46      // 46x36 (skill design-qml)
    readonly property int resizeHandle: 6

    // Painel do meu perfil (barra lateral direita) e popup do amigo
    readonly property int panelClosed: 72
    readonly property int panelOpen: 320
    readonly property int panelAvatar: 40
    readonly property int panelAvatarOpen: 72
    readonly property int avatarBig: 96
    readonly property int popupWidth: 420
    readonly property int popupHeight: 540

    // Medidas da lista
    readonly property int rowHeight: 40
    readonly property int avatarSize: 28
    readonly property int dotSize: 8
    readonly property real dotWebRing: 1.5   // bolinha vazada de quem está só na web
    readonly property int listPad: 8          // respiro à esquerda da linha
    readonly property int colStatus: 198      // x do dot de status
    readonly property int colWorld: 302       // x do texto do mundo
    readonly property int headHeight: 32      // alvo clicável do header (>= 32 px)
    readonly property int btnHeight: 40
    readonly property int fieldHeight: 40
    readonly property int winWidth: 560
    readonly property int winHeight: 610

    function statusColor(key) {
        if (key === "join me") return statusJoin;
        if (key === "ask me") return statusAsk;
        if (key === "busy") return statusBusy;
        if (key === "offline") return statusOffline;
        return statusOnline;
    }
}
