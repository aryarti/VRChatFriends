import QtQuick
import ".."

// Uma linha da lista: avatar redondo, nome, status (dot + rótulo) e mundo.
// A cor vive só no dot e no rótulo do status — nunca na linha inteira.
Item {
    id: root

    property var row: ({})
    property bool selected: false

    signal clicked()
    signal rightClicked()

    height: Theme.rowHeight

    Rectangle {
        anchors.fill: parent
        color: root.selected || mouse.containsMouse ? Theme.bg3 : "transparent"
        Behavior on color { ColorAnimation { duration: Theme.durFast } }
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
        color: Theme.text1
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsMd
        font.weight: 600
        elide: Text.ElideRight
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
        width: Theme.dotSize
        height: Theme.dotSize
        radius: width / 2
        color: Theme.statusColor(root.row ? root.row.status : "")
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
        anchors {
            left: statusDot.right
            leftMargin: Theme.s2
            verticalCenter: parent.verticalCenter
        }
    }

    Text {
        id: worldLabel
        // instância pública: quantidade de gente no mesmo mundo, em tom mais discreto
        text: {
            var w = root.row && root.row.world ? root.row.world : "";
            var rotulo = root.row ? (root.row.occupants_label || "") : "";
            return rotulo ? (w + " <font color='" + Theme.text3 + "'>· " + rotulo + "</font>") : w;
        }
        textFormat: Text.StyledText
        color: Theme.text2
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsMd
        elide: Text.ElideRight
        anchors {
            left: parent.left
            leftMargin: Theme.colWorld
            right: parent.right
            rightMargin: Theme.s3
            verticalCenter: parent.verticalCenter
        }
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
}
