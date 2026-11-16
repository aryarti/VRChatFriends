# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller — VRChat Friends v1.1 (interface QML).

Um diretório (não onefile): abre rápido, o antivírus reclama menos e dá para
substituir um arquivo só quando preciso. Tudo que o app lê em tempo de execução
(QML, fontes, ícone) entra como dado; os módulos QML do PySide6 vão inteiros
porque o motor do Qt procura por caminho, não por import do Python.
"""

import os

import PySide6

RAIZ = os.path.dirname(os.path.abspath(SPEC))
QML_DO_PYSIDE = os.path.join(os.path.dirname(PySide6.__file__), "qml")

datas = [
    (os.path.join(RAIZ, "assets"), "assets"),
    (os.path.join(RAIZ, "ui_qml", "qml"), os.path.join("ui_qml", "qml")),
    # QtQuick.Controls.Basic, Layouts, Effects, Window, QtQml/Models... (~14 MB)
    (QML_DO_PYSIDE, os.path.join("PySide6", "qml")),
]

a = Analysis(
    [os.path.join(RAIZ, "app_qml.py")],
    pathex=[RAIZ],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickControls2",
        "PySide6.QtNetwork",
        "PySide6.QtSvg",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # a UI Tkinter não entra nesta build
    excludes=[
        "tkinter",
        "customtkinter",
        "pystray",
        "numpy",
        "PySide6.QtTest",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore",
        "PySide6.QtMultimedia",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtQuick3D",
        "PySide6.QtPdf",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VRChat Friends",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,            # app de janela: nada de console preto
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(RAIZ, "assets", "icon.ico"),
    version=os.path.join(RAIZ, "versao_exe.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VRChat Friends",
)
