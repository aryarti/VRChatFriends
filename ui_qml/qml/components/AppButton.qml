import QtQuick
import ".."

// Botão do app: primário (accent) ou secundário (bg3). Único preenchido por área.
Rectangle {
    id: root

    property alias text: label.text
    property bool primary: true
    property bool small: false

    signal clicked()

    implicitHeight: small ? Theme.s6 : Theme.btnHeight
    implicitWidth: label.implicitWidth + Theme.s5
    radius: Theme.rMd

    color: !enabled ? Theme.bg2
                    : (primary ? (mouse.containsMouse ? Theme.accentStrongHover : Theme.accentStrong)
                               : (mouse.containsMouse ? Theme.bg3Hover : Theme.bg3))
    border.width: primary ? (activeFocus ? 2 : 0) : 1
    border.color: activeFocus ? Theme.accent : Theme.border

    Behavior on color { ColorAnimation { duration: Theme.durFast } }
    scale: mouse.pressed ? 0.98 : 1.0
    Behavior on scale { NumberAnimation { duration: Theme.durFast } }

    activeFocusOnTab: true
    opacity: enabled ? 1.0 : 0.55

    Text {
        id: label
        anchors.centerIn: parent
        color: root.primary ? "#FFFFFF" : Theme.text1
        font.family: Theme.fontFamily
        font.pixelSize: root.small ? Theme.fsSm : Theme.fsMd
        font.weight: root.primary ? 600 : 400
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
