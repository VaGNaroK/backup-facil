# 🛡️ Backup Fácil Professional (v0.3.1)

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-green?style=flat-square)
![Plataforma](https://img.shields.io/badge/Plataforma-Linux%20%7C%20Windows-lightgrey?style=flat-square)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-GPLv3-blue?style=flat-square)

O **Backup Fácil Professional** é um sistema avançado, multiplataforma e offline para gerenciamento e criação de backups. Desenvolvido para oferecer segurança de nível comercial com uma interface gráfica amigável (GUI) e suporte nativo a operações em segundo plano (System Tray).

---

## ✨ Principais Funcionalidades

* **Backups Incrementais Inteligentes:** Utiliza banco de dados SQLite e hashing (MD5) para fazer backup apenas dos arquivos modificados, economizando tempo e espaço.
* **Compressão Avançada:** Utiliza o formato `.7z` (LZMA2) com suporte a criptografia por senha.
* **Blindagem Multi-Thread:** A interface nunca congela. As operações de disco, verificação de espaço e compressão rodam em threads assíncronas (com proteção GIL).
* **System Tray Nativo:** Minimiza para a bandeja do sistema (suporte a AppIndicator no Linux Mint/Ubuntu e Tray no Windows).
* **Agendador Integrado:** Agende rotinas diárias ou semanais que rodam silenciosamente em segundo plano.
* **Dashboard Interativo:** Monitoramento em tempo real do espaço em disco, histórico de execuções e taxa de sucesso.
* **Sistema de Perfis:** Salve configurações diferentes (Ex: "Trabalho", "Projetos Pessoais") e alterne entre elas com um clique.
* **Ferramentas de Auditoria:** Compare dois arquivos de backup para ver as diferenças exatas de arquivos e teste a integridade contra corrompimentos (CRC).

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.12
* **Interface Gráfica:** CustomTkinter
* **Compressão:** `py7zr`
* **Banco de Dados:** SQLite3 (Embutido)
* **Integração OS:** `pystray`, `plyer` (Notificações), `PyGObject` (Linux Tray)

---

## 🚀 Instalação e Uso

### Opção 1: Instalador Linux (Pacote `.deb`)
A forma mais fácil de instalar no Linux Mint/Ubuntu/Debian.

1. Baixe o pacote `.deb` gerado na aba *Releases* (ou gere o seu próprio).
2. Instale via terminal:
   ```bash
   sudo apt install ./backup-facil-pro_0.3.1_amd64.deb