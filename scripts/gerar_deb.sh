#!/bin/bash

# Define as cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sem cor

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🛠️  GERADOR DE PACOTE .DEB AUTOMÁTICO  🛠️  ${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. Verifica se está rodando dentro do VENV
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${RED}❌ Erro: Ambiente virtual não ativado!${NC}"
    echo -e "Rode: ${YELLOW}source venv/bin/activate${NC} antes de executar este script."
    exit 1
fi

# 2. Extrai a versão dinamicamente do logic.py
VERSION=$(grep -oP 'APP_VERSION = "\K[^"]+' src/logic.py)
if [ -z "$VERSION" ]; then
    echo -e "${RED}❌ Erro: Não foi possível ler a APP_VERSION no src/logic.py${NC}"
    exit 1
fi
echo -e "📦 Versão detectada: ${GREEN}v${VERSION}${NC}"

# 3. Verifica e instala o PyInstaller se necessário
if ! python -c "import PyInstaller" &> /dev/null; then
    echo -e "${YELLOW}⚠️ PyInstaller não encontrado. Instalando no ambiente virtual...${NC}"
    pip install pyinstaller
else
    echo -e "${GREEN}✅ PyInstaller detectado.${NC}"
fi

# 4. Compila o executável com PyInstaller
echo -e "\n⏳ Compilando o binário a partir do código fonte..."
python -m PyInstaller --noconsole --onefile --name "Backup_Facil_Pro" \
    --icon="assets/icon.png" \
    --add-data "assets:assets" \
    --hidden-import logic \
    --hidden-import ui_components \
    src/main.py

# Verifica se a compilação teve sucesso
if [ ! -f "dist/Backup_Facil_Pro" ]; then
    echo -e "${RED}❌ Erro: A compilação falhou. Executável não gerado.${NC}"
    exit 1
fi

# 5. Prepara a estrutura de pastas do pacote Debian
echo -e "\n⏳ Montando a estrutura do pacote .deb..."
BUILD_DIR="build_deb"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR/DEBIAN
mkdir -p $BUILD_DIR/usr/bin
mkdir -p $BUILD_DIR/usr/share/applications
mkdir -p $BUILD_DIR/usr/share/icons/hicolor/256x256/apps

# 6. Copia os arquivos para a estrutura
cp dist/Backup_Facil_Pro $BUILD_DIR/usr/bin/backup-facil-pro
chmod +x $BUILD_DIR/usr/bin/backup-facil-pro
cp assets/icon.png $BUILD_DIR/usr/share/icons/hicolor/256x256/apps/backup-facil-pro.png

# 7. Cria o arquivo de atalho (.desktop) para o Menu Iniciar
cat <<EOF > $BUILD_DIR/usr/share/applications/backup-facil-pro.desktop
[Desktop Entry]
Name=Backup Fácil Pro
Comment=Ferramenta profissional para automação de backups
Exec=/usr/bin/backup-facil-pro
Icon=backup-facil-pro
Terminal=false
Type=Application
Categories=Utility;System;Archiving;
EOF

# 8. Cria o arquivo de controle do Debian
cat <<EOF > $BUILD_DIR/DEBIAN/control
Package: backup-facil-pro
Version: $VERSION
Section: utils
Priority: optional
Architecture: amd64
Maintainer: VaGNaroK
Description: Ferramenta de desktop robusta para automação, gestão e criptografia de backups locais.
EOF

# 9. Gera o pacote final .deb
DEB_NAME="backup-facil-pro_${VERSION}_amd64.deb"
echo -e "\n⏳ Fechando o pacote..."
dpkg-deb --build $BUILD_DIR $DEB_NAME

# 10. Limpeza da sujeira de compilação
rm -rf $BUILD_DIR
rm -rf build/
rm -f Backup_Facil_Pro.spec

echo -e "\n${GREEN}✅ Sucesso Absoluto!${NC}"
echo -e "O instalador ${BLUE}${DEB_NAME}${NC} está pronto na raiz do seu projeto!"