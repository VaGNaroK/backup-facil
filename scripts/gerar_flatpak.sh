#!/bin/bash

# Define as cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # Sem cor

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  🛠️  GERADOR DE FLATPAK AUTOMÁTICO  🛠️  ${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. Extrai a versão diretamente do logic.py (Mágica do Regex!)
VERSION=$(grep -oP 'APP_VERSION = "\K[^"]+' src/logic.py)

if [ -z "$VERSION" ]; then
    echo -e "${YELLOW}⚠️  Erro: Não foi possível ler a APP_VERSION no src/logic.py${NC}"
    exit 1
fi

echo -e "📦 Versão detectada: ${GREEN}v${VERSION}${NC}"
echo -e "⏳ Iniciando compilação no contêiner..."

# 2. Roda a compilação (instalando silenciosamente)
flatpak-builder build-dir io.github.vagnarok.BackupFacilPro.yml --force-clean --user --install

# 3. Define o nome do arquivo dinamicamente
BUNDLE_NAME="Backup_Facil_Pro_v${VERSION}.flatpak"

echo -e "⏳ Gerando o arquivo instalador final..."

# 4. Roda o empacotamento com o nome dinâmico
flatpak build-bundle ~/.local/share/flatpak/repo "$BUNDLE_NAME" io.github.vagnarok.BackupFacilPro

echo -e "${GREEN}✅ Sucesso Absoluto!${NC}"
echo -e "O instalador ${BLUE}${BUNDLE_NAME}${NC} foi gerado na raiz do projeto."