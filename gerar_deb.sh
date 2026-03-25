#!/bin/bash
set -e

# Define as variáveis do projeto
PKG_NAME="backup-facil-pro"
PKG_VER="0.3.4"
ARCH="amd64"
DIR_NAME="${PKG_NAME}_${PKG_VER}_${ARCH}"

echo "🧹 1. Limpando builds antigos..."
rm -rf build dist $DIR_NAME *.deb

echo "🚀 2. Compilando o executável com PyInstaller..."
# O PyInstaller vai gerar o binário na pasta 'dist'
pyinstaller --noconsole --onefile --collect-all customtkinter --collect-all plyer --name "backup-facil-pro" main.py

echo "📁 3. Criando estrutura do pacote .deb..."
mkdir -p $DIR_NAME/DEBIAN
mkdir -p $DIR_NAME/usr/bin
mkdir -p $DIR_NAME/usr/share/applications
mkdir -p $DIR_NAME/usr/share/pixmaps

echo "⚙️ 4. Copiando o executável para /usr/bin..."
cp dist/backup-facil-pro $DIR_NAME/usr/bin/
chmod +x $DIR_NAME/usr/bin/backup-facil-pro

echo "🖼️ 5. Copiando o ícone para /usr/share/pixmaps..."
if [ -f "icon.png" ]; then
    cp icon.png $DIR_NAME/usr/share/pixmaps/backup-facil-pro.png
    echo "Ícone icon.png copiado com sucesso!"
else
    echo "⚠️ AVISO: icon.png não encontrado na pasta do projeto! O menu do Linux usará um ícone genérico."
fi

echo "📝 6. Criando arquivo DEBIAN/control..."
cat <<EOF > $DIR_NAME/DEBIAN/control
Package: $PKG_NAME
Version: $PKG_VER
Architecture: $ARCH
Maintainer: VaGNaroK <vagnarok@seuemail.com>
Depends: libayatana-appindicator3-1, gir1.2-ayatanaappindicator3-0.1, python3-dbus
Description: Backup Fácil Professional
 Um sistema avançado de backup offline, incremental e gerenciamento de arquivos.
EOF

echo "🖥️ 7. Criando atalho do menu (.desktop)..."
cat <<EOF > $DIR_NAME/usr/share/applications/backup-facil-pro.desktop
[Desktop Entry]
Version=1.0
Name=Backup Fácil Pro
Comment=Sistema avançado de backup incremental
Exec=/usr/bin/backup-facil-pro
Icon=backup-facil-pro
Terminal=false
Type=Application
Categories=Utility;System;
EOF

echo "📦 8. Construindo o arquivo .deb final..."
dpkg-deb --build $DIR_NAME

echo "✨ SUCESSO! O arquivo ${DIR_NAME}.deb foi gerado e está pronto para instalação."
