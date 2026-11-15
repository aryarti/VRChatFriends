import QtQuick
import ".."
import QtQuick.Controls.Basic

// Campo de texto do app: bg2, borda de 1px, foco em accent.
TextField {
    id: root

    property bool code: false

    implicitHeight: Theme.fieldHeight
    leftPadding: Theme.s3
    rightPadding: Theme.s3
    font.family: code ? Theme.monoFamily : Theme.fontFamily
    font.pixelSize: code ? Theme.fsLg : Theme.fsMd
    horizontalAlignment: code ? TextInput.AlignHCenter : TextInput.AlignLeft
    color: Theme.text1
    placeholderTextColor: Theme.text3
    selectionColor: Theme.accent
    selectedTextColor: "#FFFFFF"

    background: Rectangle {
        radius: Theme.rMd
        color: Theme.bg2
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus ? Theme.accent : Theme.border
        Behavior on border.color { ColorAnimation { duration: Theme.durFast } }
    }
}
