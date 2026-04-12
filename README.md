# 💾 Backup Fácil Professional

Uma ferramenta de desktop robusta e multiplataforma para automação, gestão e criptografia de backups locais. Desenvolvida em Python com uma interface gráfica moderna e responsiva utilizando **PySide6** (Qt).

![Versão](https://img.shields.io/badge/vers%C3%A3o-0.3.9-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-green)
![Flatpak](https://img.shields.io/badge/Distribui%C3%A7%C3%A3o-Flatpak-brightgreen)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-GPL--3.0-orange)

## ✨ Principais Funcionalidades

* **Monitor de Desempenho em Tempo Real (NOVO):** Visualização da taxa de gravação (MB/s) diretamente na interface, permitindo acompanhar o progresso real de arquivos gigantes sem ansiedade.
* **Suporte Oficial a Flatpak (NOVO):** Distribuição universal e segura via sandbox, garantindo que o app funcione em qualquer distribuição Linux.
* **GPS de Diretórios Dinâmico:** Motor de lógica que detecta o ambiente de execução (Flatpak vs Nativo) e redireciona automaticamente o salvamento de dados para evitar erros de permissão.
* **Criptografia Militar:** Suporte nativo a compressão `.7z` com criptografia **AES-256**.
* **Backups Incrementais:** Motor inteligente usando SQLite e Hashes MD5 para copiar apenas os arquivos modificados ou novos.
* **Filtros Avançados (Regex):** Capacidade de ignorar arquivos e pastas por extensões ou Expressões Regulares avançadas (ex: `^temp_.*`).
* **Segurança de Credenciais:** Integração com o `keyring` do sistema operacional para armazenamento ofuscado de senhas.

## 🛠️ Tecnologias Utilizadas

* **Python 3.11+** (Linguagem Core)
* **PySide6** (Framework de Interface Gráfica / Qt)
* **py7zr** (Motor de compressão e criptografia)
* **flatpak-builder** (Pipeline de empacotamento universal)
* **SQLite3** (Controle de integridade incremental)
* **Keyring** (Segurança de credenciais)

## 🗂️ Estrutura do Projeto

O projeto segue um padrão de arquitetura separando código, recursos e manifestos de distribuição:

```text
BACKUP_FACIL/
├── src/                    # Código-fonte Python principal
│   ├── main.py             # Ponto de entrada
│   ├── logic.py            # Motor de backup e GPS de diretórios
│   └── ui_components.py    # Interface e Monitor Cardíaco (MB/s)
├── assets/                 # Ícone (256x256) e recursos visuais
├── scripts/                # Scripts de compilação e empacotamento
│   ├── gerar_deb.sh        # Script gerador do instalador Linux Mint/Debian
│   ├── gerar_exe.bat       # Script gerador do executável Windows
│   └── gerar_flatpak.sh    # Script automatizado para compilar e empacotar o Flatpak
├── io.github.vagnarok.BackupFacilPro.yml  # Manifesto Flatpak
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação
```

## 🚀 Como Executar em Modo de Desenvolvimento

1. Clone o repositório:
   ```bash
   git clone [https://github.com/VaGNaroK/backup-facil.git](https://github.com/VaGNaroK/backup-facil.git)
   cd backup-facil
   ```

2. Configure o ambiente e instale as dependências:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Execute:
   ```bash
   python3 src/main.py
   ```

## 📦 Como Compilar e Instalar (Linux - Flatpak)

Este é o método recomendado para garantir compatibilidade universal. Todo o processo de compilação e nomeação da versão atual foi automatizado.

1. **Dê permissão de execução ao script (apenas na primeira vez):**
   ```bash
   chmod +x scripts/gerar_flatpak.sh
   ```

2. **Gere o arquivo instalador:**
   O script lerá automaticamente a versão do aplicativo direto no código fonte e compilará o pacote `.flatpak` na raiz do projeto.
   ```bash
   ./scripts/gerar_flatpak.sh
   ```

3. **Instale o pacote gerado:**
   Você pode dar dois cliques no arquivo gerado através do seu gerenciador de janelas, ou usar o terminal:
   ```bash
   flatpak install --user ./Backup_Facil_Pro_v0.3.9.flatpak
   ```

## 📦 Como Compilar e Instalar (Linux - .deb)

Para distribuições baseadas em Debian/Mint:

1. **Gerar Binário via PyInstaller:**
   ```bash
   python3 -m PyInstaller --noconsole --onefile --name "Backup_Facil_Pro" --icon="assets/icon.png" --add-data "assets:assets" --hidden-import logic --hidden-import ui_components src/main.py
   ```

2. **Gerar e Instalar o Pacote:**
   ```bash
   chmod +x scripts/gerar_deb.sh
   ./scripts/gerar_deb.sh
   sudo dpkg -i backup-facil-pro_0.3.9_amd64.deb
   ```

## 🪟 Como Compilar (Windows)

1. No terminal do Windows, com o ambiente virtual ativo, execute:
   ```cmd
   python -m PyInstaller --noconsole --onefile --name "Backup_Facil_Pro" --icon="assets\icon.ico" --add-data "assets;assets" --hidden-import logic --hidden-import ui_components src\main.py
   ```

---
*Desenvolvido por VaGNaroK com um help de IA.*