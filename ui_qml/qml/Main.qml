import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import "."

Window {
    id: win
    visible: true
    width: Theme.winWidth
    height: Theme.winHeight
    minimumWidth: 480
    minimumHeight: 380
    color: Theme.bg0
    title: bridge.windowTitle
    // quantas linhas já reanimaram (contador só para verificação automatizada)
    property int animacoesLista: 0
    // janela sem moldura: a barra de título é nossa (skill design-qml, seção Janela)
    flags: Qt.Window | Qt.FramelessWindowHint

    // meu perfil recarrega quando o login conclui (a lista chega depois do restore)
    Connections {
        target: bridge
        function onFriendsChanged() {
            if (bridge.loggedIn) bridge.requestMyProfile();
        }
    }

    // ============================================================ BARRA DE TÍTULO
    TitleBar {
        id: titleBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        titulo: bridge.windowTitle
        onFechar: bridge.hideToTray()   // fechar = ir para a bandeja (igual ao Tkinter)
    }

    // ============================================================ LOGIN
    Item {
        id: loginPane
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: !bridge.loggedIn

        Column {
            id: loginCol
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: Theme.s5
            spacing: Theme.s2

            Text {
                text: bridge.stage === "2fa" ? "Confirmar código" : "Entrar no VRChat"
                color: Theme.text1
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXl
                font.weight: 600
            }
            Text {
                text: bridge.loginHint
                width: loginCol.width
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsSm
                wrapMode: Text.WordWrap
                lineHeight: 1.3
            }

            // ---- credenciais
            Column {
                width: loginCol.width
                spacing: Theme.s1
                topPadding: Theme.s4
                visible: bridge.stage !== "2fa"

                Text {
                    text: "Usuário ou e-mail"
                    color: Theme.text2
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsXs
                }
                TextField {
                    id: userField
                    width: parent.width
                    text: bridge.lastUser
                    placeholderText: "usuário"
                    onAccepted: bridge.doLogin(userField.text, passField.text)
                }
                Item { width: 1; height: Theme.s2 }
                Text {
                    text: "Senha"
                    color: Theme.text2
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsXs
                }
                TextField {
                    id: passField
                    width: parent.width
                    echoMode: TextInput.Password
                    placeholderText: "senha"
                    onAccepted: bridge.doLogin(userField.text, passField.text)
                }
                Item { width: 1; height: Theme.s3 }
                AppButton {
                    width: parent.width
                    height: Theme.btnHeight
                    text: bridge.busy ? "Entrando…" : "Entrar"
                    enabled: !bridge.busy
                    onClicked: bridge.doLogin(userField.text, passField.text)
                }
            }

            // ---- 2FA
            Column {
                width: loginCol.width
                spacing: Theme.s1
                topPadding: Theme.s4
                visible: bridge.stage === "2fa"

                Text {
                    text: bridge.codeLabel
                    color: Theme.text2
                    font.family: Theme.fontFamily
                    font.pixelSize: Theme.fsXs
                }
                TextField {
                    id: codeField
                    width: parent.width
                    code: true
                    placeholderText: "000000"
                    onAccepted: bridge.doVerify(codeField.text)
                }
                Item { width: 1; height: Theme.s3 }
                RowLayout {
                    width: parent.width
                    spacing: Theme.s2
                    AppButton {
                        Layout.fillWidth: true
                        height: Theme.btnHeight
                        text: bridge.busy ? "Verificando…" : "Confirmar"
                        enabled: !bridge.busy
                        onClicked: bridge.doVerify(codeField.text)
                    }
                    AppButton {
                        height: Theme.btnHeight
                        primary: false
                        text: "Reenviar"
                        enabled: !bridge.busy
                        onClicked: bridge.resend()
                    }
                    AppButton {
                        height: Theme.btnHeight
                        primary: false
                        implicitWidth: 44
                        text: "↩"
                        onClicked: bridge.backToCreds()
                    }
                }
            }

            Item { width: 1; height: Theme.s3 }
            Text {
                id: msgLine
                text: bridge.message
                width: loginCol.width
                color: bridge.messageKind === "error" ? Theme.statusBusy
                       : (bridge.messageKind === "ok" ? Theme.success : Theme.text2)
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
                wrapMode: Text.WordWrap
            }
        }
    }

    // ============================================================ LISTA
    Item {
        id: listPane
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        visible: bridge.loggedIn

        // gradiente do cabeçalho: o ÚNICO da tela (permitido pela skill)
        Rectangle {
            id: header
            width: parent.width
            height: 92
            gradient: Gradient {
                GradientStop { position: 0.0; color: Theme.headerGradientStart }
                GradientStop { position: 1.0; color: Theme.bg0 }
            }
        }

        Item {
            id: topBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: Theme.s4
            anchors.rightMargin: Theme.s3
            anchors.topMargin: Theme.s3
            height: 40

            Text {
                id: countLabel
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: bridge.countText
                color: Theme.text1
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXl
                font.weight: 600
            }
            // o "esconder" saiu daqui: fechar (x) na barra de título já vai para a bandeja
            IconButton {
                id: btnAtualizar
                objectName: "btnAtualizar"
                anchors.right: parent.right
                anchors.rightMargin: Theme.panelAvatar + Theme.s2
                anchors.verticalCenter: parent.verticalCenter
                desenhoRecarga: true
                onClicked: bridge.refresh()

                // girando: propriedade do IconButton (gira só o glifo, no centro).
                // O refresh costuma acabar em ~100 ms (mundos em cache): sem um tempo
                // mínimo o giro nem aparece.
                Timer {
                    id: minGiro
                    interval: 700
                    onTriggered: if (!bridge.busy) btnAtualizar.girando = false
                }
                Connections {
                    target: bridge
                    function onBusyChanged() {
                        if (bridge.busy) {
                            btnAtualizar.girando = true;
                            minGiro.restart();
                        } else if (!minGiro.running) {
                            btnAtualizar.girando = false;
                        }
                    }
                }
            }
        }

        // cabeçalho das colunas (fica de pé também no vazio/erro)
        Item {
            id: colHead
            anchors.top: header.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: Theme.headHeight

            Text {
                x: Theme.listPad + Theme.avatarSize + Theme.s3
                anchors.verticalCenter: parent.verticalCenter
                text: "AMIGO"
                color: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
            }
            Text {
                x: Theme.colStatus + Theme.dotSize + Theme.s2
                anchors.verticalCenter: parent.verticalCenter
                text: "STATUS"
                color: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
            }
            Text {
                x: Theme.colWorld
                anchors.verticalCenter: parent.verticalCenter
                text: "MUNDO"
                color: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
            }
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Theme.border
            }
        }

        ListView {
            id: list
            anchors.top: colHead.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: foot.top
            clip: true
            model: bridge.friends
            boundsBehavior: Flickable.StopAtBounds
            currentIndex: -1
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
                width: 8
                contentItem: Rectangle {
                    implicitWidth: 6
                    radius: 3
                    color: parent.pressed ? Theme.accent : Theme.bg3Hover
                }
            }

            delegate: FriendRow {
                id: rowItem
                objectName: "rowItem"
                width: list.width
                row: modelData
                selected: list.currentIndex === index

                // entrada: fade + 10px, só nos 8 primeiros e nunca quando reducedMotion
                transform: Translate { id: slide; y: 0 }
                Component.onCompleted: {
                    if (index < 8 && !Theme.reducedMotion) {
                        rowItem.opacity = 0;
                        slide.y = 10;
                        intro.start();
                    }
                }
                ParallelAnimation {
                    id: intro
                    NumberAnimation {
                        target: rowItem
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: Theme.durBase
                        easing.type: Theme.easeOut
                    }
                    NumberAnimation {
                        target: slide
                        property: "y"
                        from: 10
                        to: 0
                        duration: Theme.durBase
                        easing.type: Theme.easeOut
                    }
                }

                // a cada recarga (refreshToken muda) a entrada sobe de novo
                Connections {
                    target: bridge
                    function onRefreshTokenChanged() {
                        if (index < 8 && !Theme.reducedMotion) {
                            rowItem.opacity = 0;
                            slide.y = 10;
                            intro.restart();
                            win.animacoesLista += 1;
                        }
                    }
                }

                onClicked: {
                    list.currentIndex = index;
                    popup.perfil = ({});
                    popup.titulo = modelData.name;
                    popup.open();
                    bridge.requestProfile(modelData.id);
                }
                onRightClicked: {
                    list.currentIndex = index;
                    ctxMenu.popup();
                }
            }
        }

        // vazio / erro
        Column {
            id: emptyBlock
            visible: bridge.state !== "list"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: 20
            spacing: Theme.s2

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: bridge.state === "error" ? "⟳" : "◌"
                color: bridge.state === "error" ? Theme.statusBusy : Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: 28
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: bridge.state === "error" ? "Falha ao atualizar" : "Nenhum amigo online agora"
                color: bridge.state === "error" ? Theme.statusBusy : Theme.text1
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsMd
                font.weight: 600
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: bridge.state === "error" ? "Nova tentativa em 45 s" : "A lista se atualiza a cada 45 s"
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsSm
            }
            AppButton {
                anchors.horizontalCenter: parent.horizontalCenter
                primary: false
                text: bridge.state === "error" ? "Tentar agora" : "Atualizar agora"
                onClicked: bridge.refresh()
            }
        }

        // rodapé
        Item {
            id: foot
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 44

            Rectangle {
                width: parent.width
                height: 1
                color: Theme.border
            }
            // o antigo "sempre no topo" virou widget flutuante: o botão abre/fecha
            AppButton {
                id: btWidget
                objectName: "btWidget"
                anchors.left: parent.left
                anchors.leftMargin: Theme.s3
                anchors.verticalCenter: parent.verticalCenter
                small: true
                height: 26
                primary: bridge.widgetAberto
                text: (bridge.widgetAberto ? "● " : "◱ ") + "widget"
                onClicked: bridge.setWidgetAberto(!bridge.widgetAberto)
            }
            Text {
                id: metaFoot
                anchors.right: verFoot.left
                anchors.rightMargin: Theme.s2
                anchors.verticalCenter: parent.verticalCenter
                text: bridge.metaText
                color: Theme.text2
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
            }

            // versão do app: canto inferior direito, discreta
            Text {
                id: verFoot
                objectName: "verFoot"
                anchors.right: parent.right
                anchors.rightMargin: Theme.s3
                anchors.verticalCenter: parent.verticalCenter
                text: bridge.versionText
                color: Theme.text3
                font.family: Theme.fontFamily
                font.pixelSize: Theme.fsXs
            }
        }

        Connections {
            target: bridge
            function onProfileReady(json) {
                try { popup.perfil = JSON.parse(json); } catch (e) { popup.perfil = ({}); }
            }
            function onMyProfileReady(json) {
                try { myPanel.perfil = JSON.parse(json); } catch (e) { myPanel.perfil = ({}); }
            }
        }

        Component.onCompleted: {
            if (bridge.loggedIn) bridge.requestMyProfile();
        }

        // menu de contexto (camada flutuante: glass leve, sem blur)
        Menu {
            id: ctxMenu
            background: Rectangle {
                implicitWidth: 220
                color: Qt.rgba(0.08, 0.09, 0.11, 0.88)
                radius: Theme.rMd
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.08)
            }
            MenuItem {
                text: "Copiar link vrchat://"
                onTriggered: bridge.copyLaunch(list.currentIndex)
            }
            MenuItem {
                text: "Copiar nome do mundo"
                onTriggered: bridge.copyWorld(list.currentIndex)
            }
            MenuSeparator {}
            MenuItem {
                text: "Atualizar"
                onTriggered: bridge.refresh()
            }
        }
    }

    // clique fora do cartão do meu perfil fecha (mesmo comportamento do popup do amigo)
    MouseArea {
        id: fechaPainel
        objectName: "fechaPainel"
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 95
        enabled: myPanel.expanded
        visible: enabled
        // hoverEnabled é obrigatório aqui: um MouseArea sem hover não captura o
        // hover, e as linhas de baixo continuam reagindo (dava hover ATRAVÉS do
        // painel aberto). Com hover, esta área fica com o mouse só para ela.
        hoverEnabled: enabled
        onClicked: myPanel.toggled(false)
    }

    // ============================================================ MEU PERFIL
    // recolhido é só o ícone (sem barra, sem seta); aberto vira cartão sobre a lista
    SidePanel {
        id: myPanel
        objectName: "myPanel"
        z: 96
        anchors.right: parent.right
        anchors.rightMargin: Theme.s3
        anchors.top: titleBar.bottom
        anchors.topMargin: Theme.s3
        visible: bridge.loggedIn
        onToggled: function (expandido) {
            myPanel.expanded = expandido;
        }
    }

    // ============================================================ REDIMENSIONAR
    // alças finas nas bordas inferiores + cantos, com startSystemResize (API nativa)
    Item {
        id: alcas
        anchors.top: titleBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 90

        MouseArea {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Theme.resizeHandle * 2
            width: Theme.resizeHandle
            cursorShape: Qt.SizeHorCursor
            onPressed: win.startSystemResize(Qt.LeftEdge)
        }
        MouseArea {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Theme.resizeHandle * 2
            width: Theme.resizeHandle
            cursorShape: Qt.SizeHorCursor
            onPressed: win.startSystemResize(Qt.RightEdge)
        }
        MouseArea {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: Theme.resizeHandle * 2
            anchors.rightMargin: Theme.resizeHandle * 2
            height: Theme.resizeHandle
            cursorShape: Qt.SizeVerCursor
            onPressed: win.startSystemResize(Qt.BottomEdge)
        }
        MouseArea {
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            width: Theme.resizeHandle * 2
            height: Theme.resizeHandle * 2
            cursorShape: Qt.SizeFDiagCursor
            onPressed: win.startSystemResize(Qt.LeftEdge | Qt.BottomEdge)
        }
        MouseArea {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            width: Theme.resizeHandle * 2
            height: Theme.resizeHandle * 2
            cursorShape: Qt.SizeBDiagCursor
            onPressed: win.startSystemResize(Qt.RightEdge | Qt.BottomEdge)
        }
    }

    // ============================================================ POPUP DO AMIGO
    // camada própria acima de tudo: fade + escala, e a janela não muda de tamanho
    FriendPopup {
        id: popup
        objectName: "popup"
    }
}
