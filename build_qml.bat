@echo off
rem Build do executavel QML (v1.0). Fecha o app antes: o PyInstaller nao consegue
rem sobrescrever arquivo em uso (_internal\*.pyd travado = PermissionError).
cd /d "%~dp0"

taskkill /F /IM "VRChat Friends.exe" >nul 2>&1
timeout /t 1 /nobreak >nul

.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean VRChatFriends.spec
if errorlevel 1 goto erro

echo.
echo Pronto: dist\VRChat Friends\VRChat Friends.exe
pause
exit /b 0

:erro
echo.
echo FALHOU. Se for PermissionError, feche o app (bandeja ^> Sair) e rode de novo.
pause
exit /b 1
