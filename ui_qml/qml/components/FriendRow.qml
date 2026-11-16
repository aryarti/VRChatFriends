import QtQuick
import ".."

// Uma linha da lista: avatar redondo, nome, status (dot + rótulo) e mundo.
// A cor vive só no dot e no rótulo do status — nunca na linha inteira.
// Favorito ganha estrela e contorno na cor de destaque; favorito fora do ar
// (bloco do fim) vem apagado, com "visto há X" no lugar do mundo.
Item {
    id: root

    property var row: ({})
    property bool selected: false
    property bool favorito: !!(row && row.favorito)
    property bool offline: !!(row && row.offline)
    // só na web (sem cliente aberto): a bolinha de status é vazada, não cheia
    property bool naWeb: !!(row && row.web)

    signal clicked()
    signal rightClicked()
    signal starClicked()

    height: Theme.rowHeight

    Rectangle {
        anchors.fill: parent
        color: root.selected || mouse.containsMouse ? Theme.bg3 : "transparent"
        Behavior on color { ColorAnimation { duration: Theme.durFast } }
    }

    // contorno do favorito: fica por cima do fundo de hover e embaixo do conteúdo
    Rectangle {
        id: contorno
        objectName: "contornoFavorito"
        visible: root.favorito
        anchors.fill: parent
        anchors.margins: 2
        radius: Theme.rSm
        color: "transparent"
        border.width: 1
        border.color: Theme.favoritoBorder
    }

    // barra de seleção
    Rectangle {
        visible: root.selected
        width: 3
        radius: 1.5
        color: Theme.accent
        anchors {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
            topMargin: Theme.s2
            bottomMargin: Theme.s2
        }
    }

    Image {
        id: avatar
        width: Theme.avatarSize
        height: Theme.avatarSize
        anchors {
            left: parent.left
            leftMargin: Theme.listPad
            verticalCenter: parent.verticalCenter
        }
        source: root.row && root.row.avatar ? root.row.avatar : ""
        sourceSize.width: Theme.avatarSize * 2
        sourceSize.height: Theme.avatarSize * 2
        fillMode: Image.PreserveAspectFit
        smooth: true
        opacity: root.offline ? Theme.offlineOpacity : 1
        visible: source.toString() !== ""
    }

    // sem ícone: círculo neutro com a inicial
    Rectangle {
        visible: !avatar.visible
        width: Theme.avatarSize
        height: Theme.avatarSize
        radius: width / 2
        color: Theme.bg2
        border.width: 1
        border.color: Theme.border
        opacity: root.offline ? Theme.offlineOpacity : 1
        anchors {
            left: parent.left
            leftMargin: Theme.listPad
            verticalCenter: parent.verticalCenter
        }
        Text {
            anchors.centerIn: parent
            text: root.row && root.row.name ? root.row.name.charAt(0).toUpperCase() : "?"
            color: Theme.text3
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fsSm
        }
    }

    Text {
        id: nameLabel
        text: root.row && root.row.name ? root.row.name : ""
        color: root.offline ? Theme.text2 : Theme.text1
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsMd
        font.weight: 600
        elide: Text.ElideRight
        opacity: root.offline ? Theme.offlineOpacity : 1
        anchors {
            left: avatar.right
            leftMargin: Theme.s3
            verticalCenter: parent.verticalCenter
            right: statusDot.left
            rightMargin: Theme.s3
        }
    }

    Rectangle {
        id: statusDot
        objectName: "statusDotLinha"
        // Vazada = está só na web: sem preenchimento, só o anel. Cheia = abriu
        // o jogo/cliente. As três properties existem para o teste poder ler o
        // que é desenhado (border é um QQuickPen, o Python não alcança).
        property bool vazada: root.naWeb
        property real anel: vazada ? Theme.dotWebRing : 0
        property color corAnel: Theme.statusColor(root.row ? root.row.status : "")
        width: Theme.dotSize
        height: Theme.dotSize
        radius: width / 2
        color: vazada ? "transparent" : corAnel
        border.width: anel
        border.color: corAnel
        opacity: root.offline ? Theme.offlineOpacity : 1
        anchors {
            verticalCenter: parent.verticalCenter
            left: parent.left
            leftMargin: Theme.colStatus
        }
    }

    Text {
        id: statusLabel
        text: root.row && root.row.status_label ? root.row.status_label : ""
        color: Theme.statusColor(root.row ? root.row.status : "")
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsSm
        opacity: root.offline ? Theme.offlineOpacity : 1
        anchors {
            left: statusDot.right
            leftMargin: Theme.s2
            verticalCenter: parent.verticalCenter
        }
    }

    Text {
        id: worldLabel
        // instância pública: quantidade de gente no mesmo mundo, em tom mais discreto.
        // Favorito fora do ar não tem mundo: mostra há quanto tempo foi visto.
        text: {
            if (root.offline) {
                var quando = root.row ? (root.row.active || "") : "";
                return quando ? ("visto há " + quando) : "";
            }
            var w = root.row && root.row.world ? root.row.world : "";
            var rotulo = root.row ? (root.row.occupants_label || "") : "";
            return rotulo ? (w + " <font color='" + Theme.text3 + "'>· " + rotulo + "</font>") : w;
        }
        textFormat: Text.StyledText
        color: root.offline ? Theme.text3 : Theme.text2
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsMd
        elide: Text.ElideRight
        opacity: root.offline ? Theme.offlineOpacity : 1
        anchors {
            left: parent.left
            leftMargin: Theme.colWorld
            right: parent.right
            rightMargin: Theme.s3 + Theme.starSize + Theme.s2
            verticalCenter: parent.verticalCenter
        }
    }

    // ---- estrela de favorito (fora do bloco apagado: a estrela fica sempre nítida)
    Text {
        id: estrela
        objectName: "estrela"
        text: root.favorito ? "★" : "☆"
        color: root.favorito ? Theme.starOn
                             : (estrelaArea.containsMouse ? Theme.text2 : Theme.starOff)
        font.family: Theme.fontFamily
        font.pixelSize: Theme.starSize
        anchors {
            right: parent.right
            rightMargin: Theme.s3
            verticalCenter: parent.verticalCenter
        }
        Behavior on color { ColorAnimation { duration: Theme.durFast } }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        cursorShape: Qt.PointingHandCursor
        onClicked: (m) => {
            if (m.button === Qt.RightButton)
                root.rightClicked();
            else
                root.clicked();
        }
    }

    // por cima do MouseArea da linha: clicar na estrela não abre o perfil
    MouseArea {
        id: estrelaArea
        objectName: "cliqueEstrela"
        width: Theme.starSize + 16
        height: Math.min(parent.height, 32)
        anchors.right: estrela.right
        anchors.rightMargin: -8
        anchors.verticalCenter: parent.verticalCenter
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.starClicked()
    }
}
