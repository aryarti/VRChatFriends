import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

// Meu perfil: recolhido é SÓ o avatar (sem fundo, sem seta); no clique abre um
// cartão que passa por cima da lista. A janela não muda de tamanho.
// O perfil vem do bridge (/auth/user já carregado no login — sem requisição).
Item {
    id: panel
    property bool expanded: false
    property var perfil: ({})
    property bool bioSujo: false     // texto da bio mexido e ainda não salvo
    property string aviso: ""        // "salvo" / erro, some sozinho
    signal toggled(bool expandido)

    // bio nova do servidor não pode sobrescrever o que o usuário está digitando
    onPerfilChanged: if (!bioSujo) bioEdit.text = perfil.status_description || ""

    // abrir o painel relê o perfil no servidor: se você mudou a mensagem no jogo,
    // ela aparece aqui sem depender do que veio no login
    onExpandedChanged: if (expanded) bridge.atualizarMeuPerfil()

    Connections {
        target: bridge
        function onMeuPerfilSalvo(ok, msg) {
            panel.aviso = ok ? "salvo no VRChat" : msg;
            if (ok)
                panel.bioSujo = false;
            avisoTimer.restart();
        }
    }

    Timer {
        id: avisoTimer
        interval: 3500
        onTriggered: panel.aviso = ""
    }

    width: expanded ? Theme.panelOpen : Theme.panelAvatar
    height: expanded ? carta.height : Theme.panelAvatar

    // ------------------------------------------------ ícone (recolhido)
    Rectangle {
        id: icone
        width: Theme.panelAvatar
        height: Theme.panelAvatar
        radius: width / 2
        anchors.right: parent.right
        anchors.top: parent.top
        color: Theme.bg2
        visible: !panel.expanded
        opacity: panel.expanded ? 0 : 1

        Image {
            id: imgIcone
            anchors.fill: parent
            source: panel.perfil.avatar || ""
            fillMode: Image.PreserveAspectCrop
            visible: status === Image.Ready
        }
        Text {
            anchors.centerIn: parent
            visible: imgIcone.status !== Image.Ready
            text: (panel.perfil.name || "?").charAt(0).toUpperCase()
            color: Theme.text3
            font.family: Theme.fontFamily
            font.pixelSize: Theme.fsSm
        }
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: panel.toggled(true)
        }
    }

    // ------------------------------------------------ cartão (aberto)
    Rectangle {
        id: carta
        width: Theme.panelOpen
        height: conteudo.implicitHeight + 2 * Theme.s3
        anchors.right: parent.right
        anchors.top: parent.top
        radius: Theme.rMd
        color: Theme.bg1
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.08)
        visible: opacity > 0
        opacity: panel.expanded ? 1 : 0
        scale: panel.expanded ? 1.0 : 0.98
        transformOrigin: Item.Right

        Behavior on opacity {
            NumberAnimation {
                duration: panel.expanded ? Theme.durBase : Theme.durFast
                easing.type: panel.expanded ? Theme.easeOut : Theme.easeIn
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: panel.expanded ? Theme.durBase : Theme.durFast
                easing.type: panel.expanded ? Theme.easeOut : Theme.easeIn
            }
        }

        Column {
            id: conteudo
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Theme.s3
            spacing: Theme.s1

            // avatar grande: clicar recolhe (é o mesmo toggle do ícone)
            Item {
                width: parent.width
                height: Theme.panelAvatarOpen

                Rectangle {
                    id: avatarGrande
                    width: Theme.panelAvatarOpen
                    height: Theme.panelAvatarOpen
                    radius: width / 2
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: Theme.bg2

                    Image {
                        id: imgGrande
                        anchors.fill: parent
                        source: panel.perfil.avatar || ""
                        fillMode: Image.PreserveAspectCrop
                        visible: status === Image.Ready
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: imgGrande.status !== Image.Ready
                        text: (panel.perfil.name || "?").charAt(0).toUpperCase()
                        color: Theme.text3
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsXl
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: panel.toggled(false)
                }
            }

            Text {
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                text: panel.perfil.name || "—"
                color: Theme.text1
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsLg
                font.weight: 600
                elide: Text.ElideRight
            }

            // ---- status: clicar troca no VRChat (PUT /users/{id})
            Row {
                width: parent.width
                spacing: Theme.s1

                Repeater {
                    model: [
                        ["active", "Online"],
                        ["join me", "Join Me"],
                        ["ask me", "Ask Me"],
                        ["busy", "Busy"]
                    ]
                    delegate: Rectangle {
                        property bool atual: (panel.perfil.status || "active") === modelData[0]
                        width: (parent.width - 3 * Theme.s1) / 4
                        height: 24
                        radius: Theme.rSm
                        color: atual ? Theme.bg3 : (chipMouse.containsMouse ? Theme.bg2 : "transparent")
                        border.width: 1
                        border.color: atual ? Theme.statusColor(modelData[0]) : Theme.border

                        Text {
                            anchors.centerIn: parent
                            text: modelData[1]
                            color: atual ? Theme.statusColor(modelData[0]) : Theme.text2
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fsXs
                        }
                        MouseArea {
                            id: chipMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: bridge.setMyStatus(modelData[0])
                        }
                    }
                }
            }

            Text {
                width: parent.width
                visible: !!panel.perfil.pronouns
                horizontalAlignment: Text.AlignHCenter
                text: panel.perfil.pronouns || ""
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
                elide: Text.ElideRight
            }

            // ---- mensagem de status (statusDescription): editável, salva no VRChat
            TextArea {
                id: bioEdit
                objectName: "bioEdit"
                width: parent.width
                height: 62
                placeholderText: "mensagem de status"
                wrapMode: TextArea.Wrap
                selectByMouse: true
                color: Theme.text1
                placeholderTextColor: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsSm
                background: Rectangle {
                    color: Theme.bg2
                    radius: Theme.rSm
                    border.width: 1
                    border.color: bioEdit.activeFocus ? Theme.accent : Theme.border
                }
                onTextChanged: panel.bioSujo = (text !== (panel.perfil.status_description || ""))
            }

            Row {
                width: parent.width
                spacing: Theme.s2

                AppButton {
                    small: true
                    primary: panel.bioSujo
                    text: "Salvar status"
                    enabled: panel.bioSujo
                    onClicked: bridge.setMyBio(bioEdit.text)
                }
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - 130
                    text: panel.aviso
                    color: panel.aviso.indexOf("salvo") === 0 ? Theme.success : Theme.statusBusy
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsXs
                    elide: Text.ElideRight
                }
            }

            // verdade que a UI precisa dizer: o "About Me" nao vem mais na API
            Text {
                width: parent.width
                text: "o \"About Me\" do VRChat não vem pela API — aqui é a mensagem de status"
                color: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
                wrapMode: Text.WordWrap
            }

            Item { width: 1; height: Theme.s1 }

            Rectangle {
                width: parent.width
                height: 1
                color: Theme.border
            }

            Item { width: 1; height: Theme.s1 }

            Repeater {
                model: panel.linhas()
                delegate: Item {
                    width: conteudo.width
                    height: Math.max(textoValor.implicitHeight, textoRotulo.implicitHeight) + Theme.s1

                    Text {
                        id: textoRotulo
                        anchors.left: parent.left
                        anchors.top: parent.top
                        text: modelData[0]
                        color: Theme.text3
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsXs
                        width: 84
                        elide: Text.ElideRight
                    }
                    Text {
                        id: textoValor
                        anchors.left: textoRotulo.right
                        anchors.leftMargin: Theme.s2
                        anchors.right: parent.right
                        anchors.top: parent.top
                        text: modelData[1]
                        color: Theme.text1
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsSm
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Item { width: 1; height: Theme.s1 }

            Text {
                text: bridge.countText
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
            }

            AppButton {
                width: parent.width
                primary: false
                text: "Abrir no site"
                visible: !!panel.perfil.profile_url
                onClicked: Qt.openUrlExternally(panel.perfil.profile_url)
            }
        }
    }

    function linhas() {
        var p = panel.perfil || {};
        var out = [];
        if (p.trust) out.push(["Confiança", p.trust]);
        if (p.languages_text) out.push(["Idiomas", p.languages_text]);
        if (p.joined) out.push(["Conta desde", p.joined]);
        if (p.last_login) out.push(["Último login", p.last_login]);
        return out;
    }
}
