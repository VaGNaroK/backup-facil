📝 Changelog - Backup Fácil Professional
Este arquivo registra todas as mudanças notáveis feitas no projeto Backup Fácil Professional desde o seu início.

[0.3.5] - 2026-03-31
🚀 Adicionado
Automação de limpeza no script gerar_deb.sh para remover arquivos .deb antigos e evitar confusão de versões.

Documentação completa no README.md com instruções de clonagem (git clone).

🔧 Corrigido
Caminho do Ícone: Ajustado o arquivo .desktop para usar o caminho absoluto /usr/share/pixmaps/, garantindo que o ícone oficial apareça no Menu do Linux Mint.

Versão do Pacote: Corrigido o erro de cache onde o script gerava versões antigas por falta de salvamento do arquivo.

Formatação do README: Corrigida a pré-visualização no VS Code que estava "engolindo" o texto dentro de blocos de código.

[0.3.4] - O Grande Salto Profissional (Refatoração MVC)
🏗️ Arquitetura e Organização
Nova Estrutura de Diretórios: Migração de "Flat Structure" para uma estrutura organizada:

src/: Código fonte.

assets/: Ícones e imagens.

scripts/: Automação de compilação.

data/: Configurações e bancos de dados locais (ignorado pelo Git).

GPS de Diretórios: Implementação de lógica dinâmica para localização de arquivos. No Linux instalado, o app agora salva dados em ~/.config/backup_facil_pro para evitar erros de permissão (PermissionError).

🎨 Interface Gráfica (GUI)
Migração de Framework: Substituição do CustomTkinter pelo PySide6 (Qt) para uma interface mais robusta e profissional.

UI Multi-Abas: Implementação de abas para Dashboard, Backup, Restauração e a nova aba de Comparação.

Dark Mode Profissional: Estilização via QSS (Qt Style Sheets) com foco em usabilidade.

🧠 Motor de Backup (Logic)
Threads de Execução: Migração para QThreads, permitindo que o backup rode em background sem travar a interface.

Backup Incremental: Novo sistema usando SQLite e Hashes MD5 para copiar apenas arquivos novos ou alterados.

Criptografia AES-256: Suporte a senhas em arquivos .7z via py7zr.

Filtros Regex: Implementação de filtros avançados para ignorar arquivos/pastas via expressões regulares.

Aba de Comparação: Nova funcionalidade para analisar diferenças entre dois arquivos de backup antes da restauração.

📦 Distribuição e DevOps
Instalador Linux (.deb): Criação do script gerar_deb.sh que gera um pacote instalável nativo para Linux Mint/Debian.

Compilação Windows (.exe): Script gerar_exe.bat atualizado para a nova estrutura e PySide6.

Requirements.txt: Padronização das dependências do projeto.

.gitignore: Configuração de segurança para não subir arquivos sensíveis ou binários pesados para o GitHub.

[0.3.0] a [0.3.3] - Primeiras Implementações
Definição das funcionalidades básicas de compressão.

Implementação inicial do histórico em JSON.

Integração básica com o agendador de tarefas (schedule).

Adição de notificações nativas via plyer.

Nota: A partir da versão 0.3.4, o projeto adotou o padrão de versionamento semântico e arquitetura modular.