# 💾 Backup Fácil Professional

Uma ferramenta de desktop robusta e multiplataforma para automação, gestão e criptografia de backups locais. Desenvolvida em Python com uma interface gráfica moderna e responsiva utilizando **PySide6** (Qt).

![Versão](https://img.shields.io/badge/vers%C3%A3o-0.3.4-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![PySide6](https://img.shields.io/badge/GUI-PySide6-brightgreen)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-orange)

## ✨ Principais Funcionalidades

* **Interface Moderna e Responsiva:** UI em Dark Mode, dividida em abas (Dashboard, Backup, Restauração e Comparação), processada em segundo plano via `QThread` (Zero travamentos).
* **Criptografia Militar:** Suporte nativo a compressão `.7z` com criptografia **AES-256**.
* **Backups Incrementais:** Motor inteligente usando SQLite e Hashes MD5 para copiar apenas os arquivos modificados ou novos.
* **Filtros Avançados (Regex):** Capacidade de ignorar arquivos e pastas por extensões ou Expressões Regulares avançadas (ex: `^temp_.*`).
* **Comparador de Backups:** Aba dedicada para auditar e comparar dois arquivos de backup distintos, listando arquivos exclusivos e modificados.
* **Segurança de Credenciais:** Integração com o `keyring` do sistema operacional (Cofre do Linux/Windows) para não expor senhas em texto puro nos arquivos de configuração.
* **Agendamento Inteligente:** Rotinas automatizadas em background com proteção de Thread Safety (Locks).

## 🛠️ Tecnologias Utilizadas

* **Python 3** (Linguagem Core)
* **PySide6** (Framework de Interface Gráfica / Qt)
* **py7zr** (Motor de compressão e criptografia)
* **SQLite3** (Banco de dados para controle de arquivos incrementais)
* **Keyring** (Ofuscação e segurança de senhas)
* **PyInstaller & Bash** (Pipeline de compilação e geração de pacotes `.deb`)

## 🗂️ Estrutura do Projeto

O projeto segue um padrão de arquitetura limpa, separando código fonte, recursos visuais, dados de usuário e scripts de automação:

```text
BACKUP_FACIL/
├── src/                    # Código-fonte Python principal
│   ├── main.py             # Ponto de entrada e Janela Principal
│   ├── logic.py            # Regras de negócio, backend e QThreads
│   └── ui_components.py    # Componentes visuais do PySide6
├── assets/                 # Imagens, ícones e arquivos visuais
├── scripts/                # Scripts de compilação e empacotamento
│   └── gerar_deb.sh        # Script gerador do instalador Linux Mint/Debian
├── data/                   # (Gerado em dev) Configurações e DB local
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação