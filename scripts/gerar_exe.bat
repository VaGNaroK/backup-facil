@echo off
echo ==========================================
echo   Gerando o Executavel do Backup Facil Pro
echo ==========================================

echo [1] Limpando arquivos e caches antigos...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
del /q *.spec 2>nul

echo [2] Iniciando o PyInstaller (PySide6)...
python -m PyInstaller --noconsole --onefile --name "Backup_Facil_Pro" --icon="assets\icon.ico" --add-data "assets;assets" --hidden-import logic --hidden-import ui_components src\main.py

echo [3] Limpeza final profunda...
if exist "build" rmdir /s /q "build"
del /q *.spec 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo.
echo ==========================================
echo SUCESSO! O arquivo Backup_Facil_Pro.exe esta na pasta 'dist'!
echo ==========================================
pause
