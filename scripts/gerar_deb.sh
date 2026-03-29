#!/bin/bash

# ==========================================
# CONFIGURAÇÕES DO PACOTE
# ==========================================
APP_NAME="backup-facil-pro"
APP_VERSION="0.3.4"
ARCHITECTURE="amd64"
MAINTAINER="VaGNaroK <vagnarok@email.com>"
DESCRIPTION="Ferramenta profissional para backups locais, incrementais e criptografados."

# Nome da pasta de construção do pacote
BUILD_DIR="${APP_NAME}_${APP_VERSION}_${ARCHITECTURE}"

echo "🚀 Iniciando a criação do pacote .deb para o Backup Fácil Pro v${APP_VERSION}..."

# ==========================================
# 1. CRIANDO A ESTRUTURA DE PASTAS DO DEBIAN
# ==========================================
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/pixmaps"

# ==========================================
# 2. COPIANDO OS ARQUIVOS DO SEU PROJETO
# ==========================================
echo "📦 Copiando o binário e os assets..."

if [ ! -f "dist/Backup_Facil_Pro" ]; then
    echo "❌ Erro: Executável não encontrado em dist/Backup_Facil_Pro."
    echo "Rode o PyInstaller primeiro!"
    exit 1
fi
cp "dist/Backup_Facil_Pro" "${BUILD_DIR}/usr/bin/${APP_NAME}"
cp "assets/icon.png" "${BUILD_DIR}/usr/share/pixmaps/${APP_NAME}.png"

# ==========================================
# 3. CRIANDO O ARQUIVO DE CONTROLE (DEBIAN/control)
# ==========================================
echo "📝 Gerando o arquivo de controle..."
cat <<EOF > "${BUILD_DIR}/DEBIAN/control"
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Maintainer: ${MAINTAINER}
Depends: libc6 (>= 2.31)
Description: ${DESCRIPTION}
 Backup Fácil Professional é uma interface gráfica em PySide6 
 para automação e gestão de backups com suporte a compressão 7z, 
 criptografia AES-256 e backups incrementais.
EOF

# ==========================================
# 4. CRIANDO O ATALHO DO MENU (.desktop)
# ==========================================
echo "🖥️ Gerando atalho para o Menu do Linux Mint..."
cat <<EOF > "${BUILD_DIR}/usr/share/applications/${APP_NAME}.desktop"
[Desktop Entry]
Version=1.0
Name=Backup Fácil Professional
Comment=Faça backups seguros e criptografados
Exec=/usr/bin/${APP_NAME}
Icon=/usr/share/pixmaps/${APP_NAME}.png
Terminal=false
Type=Application
Categories=Utility;System;
EOF

# ==========================================
# 5. AJUSTANDO PERMISSÕES
# ==========================================
echo "🔐 Ajustando permissões do sistema..."
chmod 755 "${BUILD_DIR}/DEBIAN"
chmod 644 "${BUILD_DIR}/DEBIAN/control"
chmod 755 "${BUILD_DIR}/usr/bin/${APP_NAME}"
chmod 644 "${BUILD_DIR}/usr/share/applications/${APP_NAME}.desktop"
chmod 644 "${BUILD_DIR}/usr/share/pixmaps/${APP_NAME}.png"

# ==========================================
# 6. CONSTRUINDO O PACOTE FINAL
# ==========================================
echo "⚙️ Empacotando o .deb..."
dpkg-deb --build "${BUILD_DIR}"

# ==========================================
# 7. LIMPEZA PROFUNDA DE CACHE
# ==========================================
echo "🧹 Limpando caches de compilação e arquivos residuais..."
# Remove a pasta temporária de construção do Debian
rm -r "${BUILD_DIR}"
# Remove as pastas geradas pelo PyInstaller
rm -rf "build/"
rm -rf "dist/"
# Remove o arquivo .spec gerado pelo PyInstaller
rm -f *.spec
# Procura e remove recursivamente todas as pastas __pycache__ do Python
find . -type d -name "__pycache__" -exec rm -r {} +

echo "✅ SUCESSO! O pacote ${BUILD_DIR}.deb foi criado na raiz do seu projeto e o ambiente foi limpo."