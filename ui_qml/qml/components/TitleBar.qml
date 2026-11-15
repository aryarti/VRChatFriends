import QtQuick
import QtQuick.Controls.Basic
import ".."

// Barra de título própria (janela frameless). Componente isolado e substituível.
// Mover/redimensionar usam as APIs nativas do sistema — nada de calcular
// posição do mouse à mão (regra da skill design-qml).
Rectangle {
    id: bar
    property string titulo: ""

    signal fechar()

    height: Theme.titleBarHeight
    color: Theme.bg0

    // arrastar: startSystemMove no press (API nativa). O DragHandler com target:null
    // não disparava nesta janela frameless — o press direto é o caminho confiável.
    // Duplo clique continua maximizando/restaurando.
    MouseArea {
        id: areaBarra
        anchors.left: parent.left
        anchors.right: botoes.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        acceptedButtons: Qt.LeftButton
        onPressed: Window.window.startSystemMove()
        onDoubleClicked: {
            if (Window.window.visibility === Window.Maximized) {
                Window.window.showNormal();
            } else {
                Window.window.showMaximized();
            }
        }
    }

    Text {
        anchors.left: parent.left
        anchors.leftMargin: Theme.s3
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: botoes.left
        anchors.rightMargin: Theme.s2
        text: bar.titulo
        color: Theme.text2
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsXs
        elide: Text.ElideRight
    }

    Row {
        id: botoes
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height

        // minimizar
        Item {
            width: Theme.titleButtonWidth
            height: bar.height
            Rectangle {
                anchors.fill: parent
                color: hoverMin.containsMouse ? Theme.bg3 : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "─"
                    color: Theme.text2
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsSm
                }
            }
            MouseArea {
                id: hoverMin
                anchors.fill: parent
                hoverEnabled: true
                onClicked: Window.window.showMinimized()
            }
        }

        // maximizar / restaurar
        Item {
            width: Theme.titleButtonWidth
            height: bar.height
            Rectangle {
                anchors.fill: parent
                color: hoverMax.containsMouse ? Theme.bg3 : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: Window.window.visibility === Window.Maximized ? "❐" : "□"
                    color: Theme.text2
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsSm
                }
            }
            MouseArea {
                id: hoverMax
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    if (Window.window.visibility === Window.Maximized) {
                        Window.window.showNormal();
                    } else {
                        Window.window.showMaximized();
                    }
                }
            }
        }

        // fechar (vai para a bandeja, como no Tkinter)
        Item {
            width: Theme.titleButtonWidth
            height: bar.height
            Rectangle {
                anchors.fill: parent
                color: hoverClose.containsMouse ? Theme.danger : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: hoverClose.containsMouse ? "#FFFFFF" : Theme.text2
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsSm
                }
            }
            MouseArea {
                id: hoverClose
                anchors.fill: parent
                hoverEnabled: true
                onClicked: bar.fechar()
            }
        }
    }

    // linha de separação com o conteúdo
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: Theme.border
    }
}
