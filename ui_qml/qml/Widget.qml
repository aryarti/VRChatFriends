import QtQuick
import "."

// Widget flutuante: janela própria, sempre no topo, compacta (estilo mini player).
// Não é a janela principal — aqui o card redondo é o próprio widget: a janela é
// transparente só para o canto existir, sem moldura nenhuma.
Window {
    id: w

    width: Theme.widgetW
    height: Theme.widgetH
    color: "transparent"
    visibility: bridge.widgetAberto ? Window.Windowed : Window.Hidden
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    title: "VRChat Friends"

    // nomes dos primeiros amigos ONLINE, o resto vira "+N" (favorito offline não conta)
    function nomes() {
        var f = bridge.friends;
        var online = [];
        for (var i = 0; i < f.length; i++) {
            if (!f[i].offline)
                online.push(f[i]);
        }
        if (online.length === 0)
            return "ninguém online";
        var lista = [];
        for (var j = 0; j < Math.min(2, online.length); j++)
            lista.push(online[j].name);
        var resto = online.length - lista.length;
        return lista.join(" · ") + (resto > 0 ? "  +" + resto : "");
    }

    Rectangle {
        id: card
        anchors.fill: parent
        radius: Theme.rMd
        color: Qt.rgba(0.08, 0.09, 0.11, 0.94)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.10)

        // arrastar em qualquer ponto; clique curto abre a janela principal.
        // Fica ABAIXO da coluna de propósito: um MouseArea cobrindo o cartao
        // inteiro engolia o X e o botao de atualizar (defeito visto em 16/11).
        // Por baixo, os botoes recebem o clique primeiro e o resto do cartao
        // continua arrastavel.
        MouseArea {
            id: area
            anchors.fill: parent
            property point inicio
            property bool arrastou: false
            onPressed: function (mouse) {
                inicio = Qt.point(mouse.x, mouse.y);
                arrastou = false;
            }
            onPositionChanged: function (mouse) {
                if (!pressed || arrastou)
                    return;
                if (Math.abs(mouse.x - inicio.x) > 4 || Math.abs(mouse.y - inicio.y) > 4) {
                    arrastou = true;
                    w.startSystemMove();
                }
            }
            onReleased: {
                if (!arrastou) {
                    bridge.requestShow();
                } else {
                    bridge.salvarWidgetPos(w.x, w.y);
                }
            }
        }

        Column {
            anchors.fill: parent
            anchors.leftMargin: Theme.s3
            anchors.rightMargin: Theme.s2
            anchors.topMargin: Theme.s2
            anchors.bottomMargin: Theme.s2
            spacing: 2

            // ---- linha 1: estado + quantidade            [⟳] [✕]
            Item {
                width: parent.width
                height: 24

                Rectangle {
                    id: dot
                    width: 7
                    height: 7
                    radius: width / 2
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    color: bridge.state === "error" ? Theme.statusBusy
                           : (bridge.count > 0 ? Theme.statusOnline : Theme.statusOffline)
                }

                Text {
                    id: qtd
                    anchors.left: dot.right
                    anchors.leftMargin: Theme.s2
                    anchors.verticalCenter: parent.verticalCenter
                    text: bridge.countText
                    color: Theme.text1
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsSm
                    font.weight: 600
                }

                IconButton {
                    id: btGirar
                    objectName: "btGirar"
                    anchors.right: btFechar.left
                    anchors.rightMargin: 2
                    anchors.verticalCenter: parent.verticalCenter
                    implicitWidth: 22
                    implicitHeight: 22
                    desenhoRecarga: true
                    onClicked: bridge.refresh()

                    Timer {
                        id: minGiroW
                        interval: 700
                        onTriggered: if (!bridge.busy) btGirar.girando = false
                    }
                    Connections {
                        target: bridge
                        function onBusyChanged() {
                            if (bridge.busy) {
                                btGirar.girando = true;
                                minGiroW.restart();
                            } else if (!minGiroW.running) {
                                btGirar.girando = false;
                            }
                        }
                    }
                }

                IconButton {
                    id: btFechar
                    objectName: "btFechar"
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    implicitWidth: 22
                    implicitHeight: 22
                    text: "✕"
                    onClicked: bridge.setWidgetAberto(false)
                }
            }

            // ---- linha 2: quem está online
            Text {
                width: parent.width
                text: w.nomes()
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsSm
                elide: Text.ElideRight
                maximumLineCount: 1
            }

            // ---- linha 3: quando atualizou
            Text {
                width: parent.width
                text: bridge.metaText
                color: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
                elide: Text.ElideRight
            }
        }
    }

    // grava a posição quando ela para de mudar (ou ao esconder)
    Timer {
        id: posTimer
        interval: 600
        onTriggered: bridge.salvarWidgetPos(w.x, w.y)
    }
    onXChanged: posTimer.restart()
    onYChanged: posTimer.restart()
    onVisibilityChanged: if (visibility === Window.Hidden) bridge.salvarWidgetPos(w.x, w.y)
}
