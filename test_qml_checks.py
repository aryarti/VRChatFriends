# -*- coding: utf-8 -*-
"""Checagens funcionais da UI QML (sem clique sintético, rodando de verdade).

1. ícone da janela (é o que a barra de tarefas usa)
2. minimizar -> "Mostrar" da bandeja traz de volta
3. recarregar -> o ícone gira (ângulo muda) e para no fim
4. painel do perfil aberto -> a área de "clique fora" fica ativa

Uso: python test_qml_checks.py [segundos]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QObject, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QIcon, QWindow  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import ui_qml.main as qm  # noqa: E402

SEGUNDOS = float(sys.argv[1]) if len(sys.argv) > 1 else 20


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icone = QIcon(qm.ICON_FILE) if os.path.exists(qm.ICON_FILE) else QIcon()
    if not icone.isNull():
        app.setWindowIcon(icone)

    bridge = qm.Bridge()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("bridge", bridge)
    engine.load(QUrl.fromLocalFile(os.path.join(qm.QML_DIR, "Main.qml")))
    if not engine.rootObjects():
        print("FALHA  QML não carregou")
        return 1

    raiz = engine.rootObjects()[0]
    if not icone.isNull():
        raiz.setIcon(icone)

    # o mesmo "Mostrar" que o main.py liga (bandeja -> janela)
    def mostrar():
        if raiz.visibility() == QWindow.Visibility.Minimized:
            raiz.setVisibility(QWindow.Visibility.Windowed)
        raiz.show()
        raiz.raise_()
        raiz.requestActivate()

    bridge.requestShow.connect(mostrar)
    bridge.start()

    def checar_botao_widget():
        botao = raiz.findChild(QObject, "btWidget")
        print(("OK  " if botao is not None else "FALHA")
              + "  rodapé tem o botão do widget flutuante")

    def checar_icone():
        print(("OK  " if not raiz.icon().isNull() else "FALHA")
              + "  janela tem ícone (barra de tarefas)")

    def checar_bandeja():
        raiz.showMinimized()

        def de_volta():
            bridge.showWindow()
            QTimer.singleShot(500, confirme)

        def confirme():
            v = raiz.visibility()
            print(("OK  " if v != QWindow.Visibility.Minimized else "FALHA")
                  + f"  showWindow trouxe a janela de volta ({v})")

        QTimer.singleShot(600, de_volta)

    def checar_giro():
        giro = raiz.findChild(QObject, "giroGlifo")
        if giro is None:
            print("FALHA  glifo do botão de recarregar não encontrado")
            return
        amostras = []

        def amostra(ms):
            def _f():
                amostras.append((ms, round(float(giro.property("rotation") or 0), 1)))
            return _f

        botao = raiz.findChild(QObject, "btnAtualizar")
        bridge.refresh()
        print("  busy logo após refresh:", bridge.property("busy"),
              "| girando:", botao.property("girando") if botao else "?")
        # o eixo: o glifo gira em torno do próprio centro, e o botão NÃO gira
        print("  rotação do botão (deve ficar 0):",
              botao.property("rotation") if botao else "?")
        # o fim da volta depende de onde o giro parou: amostra até 1500 ms
        for ms in (0, 200, 400, 700, 800, 900, 1050, 1200, 1500):
            QTimer.singleShot(ms, amostra(ms))

        def veredito():
            for linha in amostras:
                print("   ", linha)
            valores = [v for _ms, v in amostras]
            girou = len(set(valores)) > 2
            terminou_zero = valores[-1] == 0.0
            print(("OK  " if girou else "FALHA") + "  ícone gira ao recarregar")
            print(("OK  " if terminou_zero else "FALHA")
                  + "  termina a volta e zera (sem salto)")

        QTimer.singleShot(1750, veredito)

    def checar_reanimacao():
        """Cada linha reanima quando a lista é recarregada (contador do QML)."""
        antes = int(raiz.property("animacoesLista") or 0)
        bridge.refresh()

        def veredito():
            depois = int(raiz.property("animacoesLista") or 0)
            print(f"  linhas reanimadas: {antes} -> {depois}")
            print(("OK  " if depois > antes else "FALHA")
                  + "  lista reanima ao recarregar")

        QTimer.singleShot(800, veredito)

    def checar_painel():
        painel = raiz.findChild(QObject, "myPanel")
        fecha = raiz.findChild(QObject, "fechaPainel")
        if painel is None or fecha is None:
            print("FALHA  painel/área de clicar fora não encontrada")
            return
        painel.setProperty("expanded", True)

        def confirme():
            print(("OK  " if bool(fecha.property("enabled")) else "FALHA")
                  + "  clicar fora fecha o cartão do perfil")

        QTimer.singleShot(250, confirme)

    def checar_janela():
        """Regra da skill: raiz reta, opaca, sem borda própria — quem arredonda é o Windows."""
        cor = raiz.property("color")
        opaca = cor.alpha() == 255
        raiz_arredondada = raiz.findChild(QObject, "superficie") is not None
        print(("OK  " if opaca else "FALHA") + f"  janela opaca (alfa={cor.alpha()})")
        print(("OK  " if not raiz_arredondada else "FALHA")
              + "  sem retângulo arredondado/borda própria na raiz")

    QTimer.singleShot(2000, checar_janela)
    QTimer.singleShot(2200, checar_botao_widget)
    QTimer.singleShot(2500, checar_icone)
    QTimer.singleShot(3000, checar_bandeja)
    QTimer.singleShot(5000, checar_giro)
    QTimer.singleShot(8500, checar_reanimacao)
    QTimer.singleShot(11000, checar_painel)
    QTimer.singleShot(int(SEGUNDOS * 1000), app.quit)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
