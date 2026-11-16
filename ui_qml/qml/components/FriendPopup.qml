import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import ".."

// Popup do amigo como CAMADA animada (não Popup do Controls): controle total de
// opacity/scale com ease. Abre com fade + leve escala, fecha mais rápido com ease-in.
Item {
    id: pop
    property bool opened: false
    property var perfil: ({})
    property string titulo: ""
    // favorito: reavaliado a cada estrela (favoritosVersion força a dependência)
    property bool favorito: {
        bridge.favoritosVersion;
        return bridge.isFavorito(pop.perfil.id || "");
    }

    anchors.fill: parent
    visible: opacity > 0
    opacity: opened ? 1 : 0
    enabled: opened
    focus: opened
    z: 100

    Behavior on opacity {
        NumberAnimation {
            duration: pop.opened ? Theme.durBase : Theme.durFast
            easing.type: pop.opened ? Theme.easeOut : Theme.easeIn
        }
    }

    function open() {
        pop.opened = true;
        pop.forceActiveFocus();
    }
    function close() {
        pop.opened = false;
    }

    Keys.onEscapePressed: pop.close()

    // véu: fecha ao clicar fora
    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.55)
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true    // sem isso o hover da lista atravessa o véu
            onClicked: pop.close()
        }
    }

    // cartão
    Rectangle {
        id: card
        objectName: "card"
        width: Math.min(Theme.popupWidth, pop.width - Theme.s6)
        height: Math.min(Theme.popupHeight, pop.height - Theme.s6)
        anchors.centerIn: parent
        radius: Theme.rLg
        color: Theme.bg1        // fallback sólido: Qt não tem backdrop-filter
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.08)

        // a escala acompanha a abertura (mesma duração do fade)
        scale: pop.opened ? 1.0 : 0.96
        Behavior on scale {
            NumberAnimation {
                duration: pop.opened ? Theme.durBase : Theme.durFast
                easing.type: pop.opened ? Theme.easeOut : Theme.easeIn
            }
        }

        // engole cliques no cartão (senão o véu fecharia)
        MouseArea {
            anchors.fill: parent
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Theme.s4
            spacing: Theme.s2

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s3

                Rectangle {
                    Layout.preferredWidth: Theme.avatarBig
                    Layout.preferredHeight: Theme.avatarBig
                    radius: width / 2
                    color: Theme.bg2

                    Image {
                        id: img
                        anchors.fill: parent
                        source: pop.perfil.avatar || ""
                        fillMode: Image.PreserveAspectCrop
                        visible: status === Image.Ready
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: img.status !== Image.Ready
                        text: (pop.perfil.name || pop.titulo || "?").charAt(0).toUpperCase()
                        color: Theme.text3
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsXl
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: Theme.s1

                    Text {
                        Layout.fillWidth: true
                        text: pop.perfil.name || pop.titulo || "—"
                        color: Theme.text1
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsXl
                        font.weight: 600
                        elide: Text.ElideRight
                    }
                    RowLayout {
                        spacing: Theme.s2
                        Rectangle {
                            objectName: "statusDotPerfil"
                            Layout.preferredWidth: Theme.dotSize
                            Layout.preferredHeight: Theme.dotSize
                            radius: width / 2
                            // vazada quando o amigo está só na web (igual à linha)
                            color: pop.perfil.web ? "transparent"
                                                  : Theme.statusColor(pop.perfil.status || "active")
                            border.width: pop.perfil.web ? Theme.dotWebRing : 0
                            border.color: Theme.statusColor(pop.perfil.status || "active")
                        }
                        Text {
                            text: pop.perfil.status_label || ""
                            color: Theme.statusColor(pop.perfil.status || "active")
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fsSm
                        }
                        Item { Layout.fillWidth: true }
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: !!pop.perfil.pronouns
                        text: pop.perfil.pronouns || ""
                        color: Theme.text2
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsXs
                        elide: Text.ElideRight
                    }
                }

                // estrela de favorito: mesma ação da linha (grava no settings.json)
                Text {
                    id: estrelaPerfil
                    objectName: "estrelaPerfil"
                    Layout.alignment: Qt.AlignTop | Qt.AlignRight
                    text: pop.favorito ? "★" : "☆"
                    color: pop.favorito ? Theme.starOn : Theme.starOff
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.starSize + 6
                    Behavior on color { ColorAnimation { duration: Theme.durFast } }

                    MouseArea {
                        anchors.fill: parent
                        anchors.margins: -8
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (pop.perfil.id)
                                bridge.toggleFavorito(pop.perfil.id);
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: !!pop.perfil.status_description
                text: pop.perfil.status_description || ""
                color: Theme.text1
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsMd
                wrapMode: Text.WordWrap
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.border
            }

            Text {
                Layout.fillWidth: true
                visible: !pop.perfil.name && !pop.perfil.erro
                text: "Carregando perfil…"
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsSm
            }
            Text {
                Layout.fillWidth: true
                visible: !!pop.perfil.erro
                text: "Não deu para carregar: " + (pop.perfil.erro || "")
                color: Theme.statusBusy
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsSm
                wrapMode: Text.WordWrap
            }

            Column {
                Layout.fillWidth: true
                spacing: Theme.s1

                Repeater {
                    model: pop.linhas()
                    delegate: Item {
                        width: parent.width
                        height: Math.max(valor.implicitHeight, rotulo.implicitHeight) + Theme.s1
                        Text {
                            id: rotulo
                            anchors.left: parent.left
                            anchors.top: parent.top
                            text: modelData[0]
                            color: Theme.text3
                            font.family: Theme.fontFamily
                            font.pixelSize: Theme.fsXs
                            width: 78
                        }
                        Text {
                            id: valor
                            anchors.left: rotulo.right
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
            }

            Item { Layout.fillHeight: true }

            RowLayout {
                Layout.fillWidth: true
                spacing: Theme.s2

                AppButton {
                    primary: false
                    text: "Abrir no site"
                    visible: !!pop.perfil.profile_url
                    onClicked: Qt.openUrlExternally(pop.perfil.profile_url)
                }
                Item { Layout.fillWidth: true }
                AppButton {
                    primary: false
                    text: "Fechar"
                    onClicked: pop.close()
                }
            }
        }
    }

    function linhas() {
        var p = pop.perfil || {};
        var out = [];
        if (p.world) out.push(["Mundo", p.world]);
        if (p.platform_label) out.push(["Plataforma", p.platform_label]);
        if (p.trust) out.push(["Confiança", p.trust]);
        if (p.languages_text) out.push(["Idiomas", p.languages_text]);
        if (p.joined) out.push(["Conta desde", p.joined]);
        if (p.last_login) out.push(["Último login", p.last_login]);
        if (p.note) out.push(["Sua nota", p.note]);
        return out;
    }
}
