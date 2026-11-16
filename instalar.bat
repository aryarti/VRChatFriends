@echo off
setlocal
cd /d "%~dp0"

echo === VRChat Friends - instalacao ===
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    set "PY=python"
)

if exist ".venv\Scripts\pythonw.exe" (
    echo Ambiente ja existe, reinstalando dependencias...
) else (
    echo Criando ambiente Python isolado em .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO: Python 3 nao encontrado. Instale em https://python.org e rode de novo.
        pause
        exit /b 1
    )
)

echo Instalando dependencias (core + Tkinter)...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERRO ao instalar dependencias.
    pause
    exit /b 1
)

echo Instalando a UI QML (PySide6-Essentials, ~70 MB)...
".venv\Scripts\python.exe" -m pip install -r requirements-qml.txt --quiet
if errorlevel 1 (
    echo AVISO: a UI QML nao pode ser instalada. A versao Tkinter continua funcionando.
)

if not exist "assets\icon.ico" (
    echo Gerando icone...
    ".venv\Scripts\python.exe" make_icon.py
)

echo.
echo Pronto! Abrindo o app...
start "" ".venv\Scripts\pythonw.exe" "ui_qml\main.py"
timeout /t 2 >nul
exit /b 0
