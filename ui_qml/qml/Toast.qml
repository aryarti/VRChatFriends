import QtQuick
import "."

// Aviso "amigo entrou no jogo": janela PRÓPRIA do app (não é notificação do
// Windows). Sem moldura, sempre no topo e — o ponto importante — sem roubar foco
// (WindowDoesNotAcceptFocus), então dá para jogar com ela aparecendo.
// Empilha até Theme.toastMax cartões; cada um some sozinho em `msAviso` e pausa
// enquanto o mouse está em cima. Clique abre o cartão do amigo na janela principal.
// Favorito = cartão na cor de destaque; o resto no cinza padrão.
Window {
    id: w
    objectName: "toast"
    visible: cartoes.count > 0
    width: Theme.toastWidth
    height: pilha.implicitHeight + 2 * Theme.s2
    color: "transparent"
    title: "VRChat Friends — avisos"
    flags: Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
           | Qt.WindowDoesNotAcceptFocus

    // tempo na tela (o teste encurta isto) e quantos cabem empilhados
    property int msAviso: Theme.toastMs
    property int maximo: Theme.toastMax
    property int proximoUid: 1

    ListModel { id: cartoes }

    function adicionar(dado) {
        while (cartoes.count >= w.maximo)
            cartoes.remove(0);        // o mais velho sai: o novo é a notícia
        cartoes.append({
            uid: w.proximoUid++,
            id: dado.id || "",
            name: dado.name || "",
            world: dado.world || "",
            avatar: dado.avatar || "",
            favorito: dado.favorito === true,
            agregado: dado.agregado || 0,
            texto: dado.texto || ""
        });
    }

    function remover(uid) {
        for (var i = 0; i < cartoes.count; i++) {
            if (cartoes.get(i).uid === uid) {
                cartoes.remove(i);
                return;
            }
        }
    }

    Connections {
        target: bridge
        function onAmigoEntrou(json) {
            var dado;
            try { dado = JSON.parse(json); } catch (e) { return; }
            w.adicionar(dado);
        }
    }

    Column {
        id: pilha
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: Theme.s2
        spacing: Theme.s2

        Repeater {
            model: cartoes

            delegate: Rectangle {
                id: cartao
                objectName: "cartaoAviso"
                width: pilha.width
                height: 64
                radius: Theme.rMd
                // o id do modelo exposto como propriedade: o remover(uid) precisa dele
                property int uid: model.uid
                color: model.favorito ? Theme.toastFavoritoBg : Theme.toastBg
                border.width: 1
                border.color: model.favorito ? Theme.accent : Theme.toastBorder
                opacity: 0
                transform: Translate { id: deslize; y: 8 }

                ParallelAnimation {
                    id: entrada
                    NumberAnimation {
                        target: cartao; property: "opacity"
                        from: 0; to: 1
                        duration: Theme.durBase; easing.type: Theme.easeOut
                    }
                    NumberAnimation {
                        target: deslize; property: "y"
                        from: 8; to: 0
                        duration: Theme.durBase; easing.type: Theme.easeOut
                    }
                }
                Component.onCompleted: entrada.start()

                // some sozinho; o mouse por cima pausa a contagem
                Timer {
                    id: relogio
                    interval: w.msAviso
                    running: true
                    onTriggered: cartao.encerrar()
                }

                SequentialAnimation {
                    id: saida
                    NumberAnimation {
                        target: cartao; property: "opacity"
                        to: 0; duration: Theme.durFast; easing.type: Theme.easeIn
                    }
                    ScriptAction { script: w.remover(cartao.uid) }
                }

                function encerrar() {
                    relogio.stop();
                    if (!saida.running)
                        saida.start();
                }

                Rectangle {
                    id: avatar
                    width: 36
                    height: 36
                    radius: width / 2
                    color: Theme.bg2
                    anchors.left: parent.left
                    anchors.leftMargin: Theme.s3
                    anchors.verticalCenter: parent.verticalCenter

                    Image {
                        id: img
                        anchors.fill: parent
                        source: model.avatar || ""
                        fillMode: Image.PreserveAspectCrop
                        visible: status === Image.Ready
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: img.status !== Image.Ready
                        text: model.agregado > 0 ? String(model.agregado)
                                                 : (model.name || "?").charAt(0).toUpperCase()
                        color: Theme.text2
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsSm
                        font.weight: 600
                    }
                }

                Column {
                    anchors.left: avatar.right
                    anchors.leftMargin: Theme.s3
                    anchors.right: estrela.left
                    anchors.rightMargin: Theme.s2
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 2

                    Text {
                        width: parent.width
                        text: model.agregado > 0 ? (model.texto || (model.agregado + " amigos entraram"))
                                                 : (model.name || "")
                        color: Theme.text1
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsMd
                        font.weight: 600
                        elide: Text.ElideRight
                    }
                    Text {
                        width: parent.width
                        text: model.agregado > 0
                              ? "no jogo agora"
                              : ("entrou no jogo" + (model.world ? " · " + model.world : ""))
                        color: Theme.text2
                        font.family: Theme.fontFamily
                        font.pixelSize: Theme.fsXs
                        elide: Text.ElideRight
                    }
                }

                // marca discreta de favorito (o cartão já vem na cor de destaque)
                Text {
                    id: estrela
                    objectName: "estrelaAviso"
                    visible: model.favorito
                    text: "★"
                    color: Theme.accent
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.starSize
                    anchors.right: parent.right
                    anchors.rightMargin: Theme.s3
                    anchors.verticalCenter: parent.verticalCenter
                }

                MouseArea {
                    id: area
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        cartao.encerrar();
                        if (model.id)
                            bridge.clickAviso(model.id);
                    }
                    onContainsMouseChanged: {
                        if (containsMouse)
                            relogio.stop();
                        else if (cartao.opacity > 0)
                            relogio.restart();
                    }
                }
            }
        }
    }
}
