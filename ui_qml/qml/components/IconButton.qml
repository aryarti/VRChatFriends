import QtQuick
import ".."

// Botão quadrado de ícone (28-36 px). Um set só, monocromático.
Rectangle {
    id: root

    property alias text: label.text
    property string tooltip: ""

    // ícone de recarregar DESENHADO (arco). O glifo "⟳" não tem centro geométrico —
    // a tinta fica fora do centro da caixa de texto e o giro sai desalinhado.
    property bool desenhoRecarga: false

    // gira só o desenho, no centro dele
    property bool girando: false
    property int giroDuracao: 900

    signal clicked()

    implicitWidth: 36
    implicitHeight: 36
    radius: Theme.rSm
    color: mouse.containsMouse ? Theme.bg3 : "transparent"
    border.width: activeFocus ? 2 : 0
    border.color: Theme.accent

    Behavior on color { ColorAnimation { duration: Theme.durFast } }
    scale: mouse.pressed ? 0.96 : 1.0
    Behavior on scale { NumberAnimation { duration: Theme.durFast } }

    Text {
        id: label
        anchors.centerIn: parent
        visible: !root.desenhoRecarga
        color: mouse.containsMouse ? Theme.text1 : Theme.text2
        font.family: Theme.fontFamily
        font.pixelSize: Theme.fsLg
    }

    // ---- ícone de recarga: arco de 285° com ponta de seta, desenhado no Canvas
    Canvas {
        id: arco
        objectName: "giroGlifo"
        anchors.fill: parent
        visible: root.desenhoRecarga
        antialiasing: true
        transformOrigin: Item.Center

        onPaint: {
            var ctx = getContext("2d");
            ctx.reset ? ctx.reset() : ctx.clearRect(0, 0, width, height);
            var cx = width / 2;
            var cy = height / 2;
            var r = Math.min(width, height) / 2 - 7;
            var inicio = -Math.PI * 0.42;      // começa no topo-esquerda
            var fim = inicio + Math.PI * 1.58; // 285°

            ctx.strokeStyle = mouse.containsMouse ? Theme.text1 : Theme.text2;
            ctx.lineWidth = 2;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.arc(cx, cy, r, inicio, fim, false);
            ctx.stroke();

            // ponta de seta na extremidade livre
            var ax = cx + r * Math.cos(fim);
            var ay = cy + r * Math.sin(fim);
            var tang = fim + Math.PI / 2;
            var tam = 3.2;
            ctx.fillStyle = ctx.strokeStyle;
            ctx.beginPath();
            ctx.moveTo(ax + tam * Math.cos(tang), ay + tam * Math.sin(tang));
            ctx.lineTo(ax + tam * Math.cos(tang + 2.4), ay + tam * Math.sin(tang + 2.4));
            ctx.lineTo(ax + tam * Math.cos(tang - 2.4), ay + tam * Math.sin(tang - 2.4));
            ctx.closePath();
            ctx.fill();
        }

        // giro contínuo: velocidade angular constante (ease num spinner trava)
        NumberAnimation on rotation {
            running: root.girando
            loops: Animation.Infinite
            from: 0
            to: 360
            duration: root.giroDuracao
            easing.type: Easing.Linear
        }

        // volta ao ângulo zero sem salto: termina a volta em curso e só então zera
        NumberAnimation {
            id: fimGiro
            target: arco
            property: "rotation"
            easing.type: Easing.OutQuad
            onStopped: arco.rotation = 0
        }
    }

    onGirandoChanged: {
        if (girando) {
            fimGiro.stop();
            return;
        }
        // ângulo atual -> próximo múltiplo de 360, na velocidade do giro
        var atual = arco.rotation;
        var falta = 360 - (atual % 360);
        if (falta <= 2) {
            arco.rotation = 0;
            return;
        }
        fimGiro.from = atual;
        fimGiro.to = atual + falta;
        fimGiro.duration = Math.max(90, giroDuracao * falta / 360);
        fimGiro.start();
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
        onContainsMouseChanged: arco.requestPaint()
    }
}
