import os
import traceback
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, 
                               QListWidget, QProgressBar, QFileDialog, QFrame, QMessageBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                               QCheckBox, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
import logic

# ==========================================
# 1. TRABALHADORES EM SEGUNDO PLANO (THREADS)
# ==========================================
class TrabalhadorBackup(QThread):
    sucesso = Signal(tuple)
    erro = Signal(str)

    def __init__(self, origens, destino, compressao, senha, incremental, exclusoes):
        super().__init__()
        self.origens = origens
        self.destino = destino
        self.compressao = compressao
        self.senha = senha
        self.incremental = incremental
        self.exclusoes = exclusoes

    def run(self):
        try:
            resultado = logic.start_backup_process(
                self.origens, 
                self.destino,
                compression_level=self.compressao,
                password=self.senha,
                incremental=self.incremental,
                exclusions=self.exclusoes
            )
            self.sucesso.emit(resultado)
        except Exception as e:
            self.erro.emit(f"{str(e)}\n\nDetalhes:\n{traceback.format_exc()}")

class TrabalhadorRestauracao(QThread):
    sucesso = Signal(str)
    erro = Signal(str)

    def __init__(self, arquivo_origem, pasta_destino, senha=None):
        super().__init__()
        self.arquivo_origem = arquivo_origem
        self.pasta_destino = pasta_destino
        self.senha = senha

    def run(self):
        try:
            mensagem, sucesso_bool = logic.restore_backup_process(
                self.arquivo_origem, 
                self.pasta_destino, 
                password=self.senha
            )
            if sucesso_bool:
                self.sucesso.emit(str(mensagem))
            else:
                self.erro.emit(str(mensagem))
        except Exception as e:
            self.erro.emit(f"Erro inesperado: {str(e)}\n\nDetalhes:\n{traceback.format_exc()}")

class TrabalhadorComparar(QThread):
    sucesso = Signal(dict)
    erro = Signal(str)

    def __init__(self, arquivo1, arquivo2, senha1=None, senha2=None):
        super().__init__()
        self.arquivo1 = arquivo1
        self.arquivo2 = arquivo2
        self.senha1 = senha1
        self.senha2 = senha2

    def run(self):
        try:
            resultado = logic.compare_backups(self.arquivo1, self.arquivo2, self.senha1, self.senha2)
            if "error" in resultado:
                self.erro.emit(resultado["error"])
            else:
                self.sucesso.emit(resultado)
        except Exception as e:
            self.erro.emit(f"{str(e)}\n\nDetalhes:\n{traceback.format_exc()}")


# ==========================================
# 2. ABA DE BACKUP
# ==========================================
class AbaBackup(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # Destino
        titulo_destino = QLabel("1. Onde deseja salvar o backup?")
        titulo_destino.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout_destino = QHBoxLayout()
        self.campo_destino = QLineEdit()
        self.campo_destino.setPlaceholderText("Ex: /home/vagnarok/Backups")
        self.btn_procurar_destino = QPushButton("📁 Procurar")
        self.btn_procurar_destino.setCursor(Qt.PointingHandCursor)
        self.btn_procurar_destino.clicked.connect(self.selecionar_destino)
        layout_destino.addWidget(self.campo_destino)
        layout_destino.addWidget(self.btn_procurar_destino)

        # Origens
        titulo_origem = QLabel("2. Quais pastas deseja fazer backup?")
        titulo_origem.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_add_origem = QPushButton("➕ Adicionar Pasta")
        self.btn_add_origem.setCursor(Qt.PointingHandCursor)
        self.btn_add_origem.clicked.connect(self.adicionar_origem)
        self.lista_pastas = QListWidget()
        self.lista_pastas.setSelectionMode(QListWidget.ExtendedSelection)
        self.btn_remover_origem = QPushButton("🗑️ Remover Selecionada")
        self.btn_remover_origem.setCursor(Qt.PointingHandCursor)
        self.btn_remover_origem.setStyleSheet("background-color: #c0392b; color: white;")
        self.btn_remover_origem.clicked.connect(self.remover_origem)
        
        layout_botoes_origem = QHBoxLayout()
        layout_botoes_origem.addWidget(self.btn_add_origem)
        layout_botoes_origem.addWidget(self.btn_remover_origem)
        layout_botoes_origem.addStretch() 

        # Opções Avançadas (Regex e Incremental)
        titulo_opcoes = QLabel("3. Opções Avançadas e Segurança")
        titulo_opcoes.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        layout_opcoes = QHBoxLayout()
        layout_opcoes.setSpacing(15)

        layout_col1 = QVBoxLayout()
        lbl_compressao = QLabel("Nível de Compressão:")
        self.combo_compressao = QComboBox()
        self.combo_compressao.addItems(["Armazenar", "Rápido", "Normal", "Máximo"])
        self.combo_compressao.setCurrentText("Normal")
        self.combo_compressao.setCursor(Qt.PointingHandCursor)
        
        self.chk_incremental = QCheckBox("Ativar Backup Incremental")
        self.chk_incremental.setCursor(Qt.PointingHandCursor)
        
        layout_col1.addWidget(lbl_compressao)
        layout_col1.addWidget(self.combo_compressao)
        layout_col1.addWidget(self.chk_incremental)

        layout_col2 = QVBoxLayout()
        lbl_senha = QLabel("Senha (Opcional):")
        self.campo_senha = QLineEdit()
        self.campo_senha.setPlaceholderText("Deixe em branco para não usar senha")
        self.campo_senha.setEchoMode(QLineEdit.Password)
        
        lbl_regex = QLabel("Ignorar (Extensões ou Regex):")
        self.campo_regex = QLineEdit()
        self.campo_regex.setPlaceholderText("Ex: .tmp, .log, ^temp_.*")

        layout_col2.addWidget(lbl_senha)
        layout_col2.addWidget(self.campo_senha)
        layout_col2.addWidget(lbl_regex)
        layout_col2.addWidget(self.campo_regex)

        layout_opcoes.addLayout(layout_col1)
        layout_opcoes.addLayout(layout_col2)

        linha_separadora = QFrame()
        linha_separadora.setFrameShape(QFrame.HLine)
        linha_separadora.setStyleSheet("color: #555555;")

        # Botões
        layout_acoes = QHBoxLayout()
        self.btn_iniciar = QPushButton("▶ INICIAR BACKUP")
        self.btn_iniciar.setCursor(Qt.PointingHandCursor)
        self.btn_iniciar.setMinimumHeight(45)
        self.btn_iniciar.setStyleSheet("QPushButton { background-color: #27ae60; color: white; font-weight: bold; font-size: 14px; border-radius: 5px; } QPushButton:hover { background-color: #2ecc71; } QPushButton:disabled { background-color: #7f8c8d; }")
        self.btn_iniciar.clicked.connect(self.disparar_backup)

        self.btn_pausar = QPushButton("⏸️ Pausar")
        self.btn_pausar.setMinimumHeight(45)
        self.btn_pausar.setStyleSheet("QPushButton { background-color: #f39c12; color: white; font-weight: bold; border-radius: 5px; }")
        self.btn_pausar.clicked.connect(self.alternar_pausa)
        self.btn_pausar.hide() 

        self.btn_abortar = QPushButton("🛑 Abortar")
        self.btn_abortar.setMinimumHeight(45)
        self.btn_abortar.setStyleSheet("QPushButton { background-color: #c0392b; color: white; font-weight: bold; border-radius: 5px; }")
        self.btn_abortar.clicked.connect(self.abortar_processo)
        self.btn_abortar.hide() 

        layout_acoes.addWidget(self.btn_iniciar, stretch=2)
        layout_acoes.addWidget(self.btn_pausar, stretch=1)
        layout_acoes.addWidget(self.btn_abortar, stretch=1)

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setFixedHeight(10)
        self.barra_progresso.hide() 

        self.texto_status = QLabel("")
        self.texto_status.setAlignment(Qt.AlignCenter)

        # Montagem
        layout_principal.addWidget(titulo_destino)
        layout_principal.addLayout(layout_destino)
        layout_principal.addWidget(titulo_origem)
        layout_principal.addLayout(layout_botoes_origem)
        layout_principal.addWidget(self.lista_pastas)
        layout_principal.addWidget(titulo_opcoes)
        layout_principal.addLayout(layout_opcoes)
        layout_principal.addSpacing(10)
        layout_principal.addWidget(linha_separadora)
        layout_principal.addLayout(layout_acoes) 
        layout_principal.addWidget(self.barra_progresso)
        layout_principal.addWidget(self.texto_status)

    def selecionar_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a Pasta de Destino")
        if pasta: self.campo_destino.setText(pasta)

    def adicionar_origem(self):
        pasta = QFileDialog.getExistingDirectory(self, "Adicionar Pasta")
        if pasta:
            if pasta not in [self.lista_pastas.item(i).text() for i in range(self.lista_pastas.count())]:
                self.lista_pastas.addItem(pasta)

    def remover_origem(self):
        for item in self.lista_pastas.selectedItems():
            self.lista_pastas.takeItem(self.lista_pastas.row(item))

    def alternar_pausa(self):
        if hasattr(logic, 'toggle_pause_backup'):
            logic.toggle_pause_backup()
            if "Pausar" in self.btn_pausar.text():
                self.btn_pausar.setText("▶️ Retomar")
                self.btn_pausar.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
                self.texto_status.setText("⏸️ Backup em pausa...")
            else:
                self.btn_pausar.setText("⏸️ Pausar")
                self.btn_pausar.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
                self.texto_status.setText("⏳ Retomando compressão...")

    def abortar_processo(self):
        resposta = QMessageBox.question(self, "Confirmar", "Tem certeza que deseja abortar e cancelar o backup atual?", QMessageBox.Yes | QMessageBox.No)
        if resposta == QMessageBox.Yes:
            if hasattr(logic, 'abort_backup'):
                logic.abort_backup()
                self.btn_abortar.setEnabled(False)
                self.texto_status.setText("🛑 Abortando processo... Aguarde a finalização da thread.")

    def disparar_backup(self):
        destino = self.campo_destino.text().strip()
        origens = [self.lista_pastas.item(i).text() for i in range(self.lista_pastas.count())]
        nivel_compressao = self.combo_compressao.currentText()
        senha_digitada = self.campo_senha.text()
        incremental_ativo = self.chk_incremental.isChecked()
        exclusoes = self.campo_regex.text()

        if not destino or not origens:
            QMessageBox.warning(self, "Aviso", "Por favor, defina um destino e origens.")
            return

        for org in origens:
            if os.path.abspath(destino).startswith(os.path.abspath(org)):
                QMessageBox.critical(self, "Erro", "Destino não pode estar dentro da origem.")
                return

        self.btn_iniciar.hide()
        self.btn_pausar.show()
        self.btn_abortar.show()
        self.btn_abortar.setEnabled(True)
        self.btn_pausar.setText("⏸️ Pausar")
        self.btn_pausar.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold;")
        
        self.barra_progresso.setRange(0, 0)
        self.barra_progresso.show()
        tipo_bkp = "Incremental" if incremental_ativo else "Completo"
        self.texto_status.setText(f"⏳ Comprimindo arquivos (Modo: {tipo_bkp}), por favor aguarde...")
        self.texto_status.setStyleSheet("color: #f39c12; font-weight: bold;")

        self.worker = TrabalhadorBackup(origens, destino, nivel_compressao, senha_digitada, incremental_ativo, exclusoes)
        self.worker.sucesso.connect(self.backup_concluido)
        self.worker.erro.connect(self.backup_falhou)
        self.worker.start()

    def backup_concluido(self, resultado):
        self.resetar_interface()
        msg_sucesso = resultado[0] if isinstance(resultado, tuple) else str(resultado)
        self.texto_status.setText("✅ Backup Finalizado!")
        QMessageBox.information(self, "Sucesso", msg_sucesso)

    def backup_falhou(self, erro_msg):
        self.resetar_interface()
        self.texto_status.setText("❌ Processo interrompido ou falhou.")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Atenção")
        msg_box.setText("O backup não foi concluído com sucesso.")
        msg_box.setDetailedText(erro_msg)
        msg_box.exec()

    def resetar_interface(self):
        self.btn_iniciar.show()
        self.btn_pausar.hide()
        self.btn_abortar.hide()
        self.barra_progresso.hide()


# ==========================================
# 3. ABA DE RESTAURAÇÃO
# ==========================================
class AbaRestauracao(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        titulo_arquivo = QLabel("1. Qual arquivo deseja restaurar? (.7z, .zip)")
        titulo_arquivo.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout_arquivo = QHBoxLayout()
        self.campo_arquivo = QLineEdit()
        self.btn_procurar_arquivo = QPushButton("🔍 Selecionar Arquivo")
        self.btn_procurar_arquivo.setCursor(Qt.PointingHandCursor)
        self.btn_procurar_arquivo.clicked.connect(self.selecionar_arquivo)
        layout_arquivo.addWidget(self.campo_arquivo)
        layout_arquivo.addWidget(self.btn_procurar_arquivo)

        titulo_destino = QLabel("2. Para onde deseja extrair os arquivos?")
        titulo_destino.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout_destino = QHBoxLayout()
        self.campo_destino = QLineEdit()
        self.btn_procurar_destino = QPushButton("📁 Escolher Pasta")
        self.btn_procurar_destino.setCursor(Qt.PointingHandCursor)
        self.btn_procurar_destino.clicked.connect(self.selecionar_destino)
        layout_destino.addWidget(self.campo_destino)
        layout_destino.addWidget(self.btn_procurar_destino)

        titulo_senha = QLabel("3. Senha de Descompactação (Se houver)")
        titulo_senha.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.campo_senha = QLineEdit()
        self.campo_senha.setPlaceholderText("Digite a senha (deixe em branco se não houver)")
        self.campo_senha.setEchoMode(QLineEdit.Password)

        linha = QFrame()
        linha.setFrameShape(QFrame.HLine)
        linha.setStyleSheet("color: #555555;")

        self.btn_restaurar = QPushButton("⏪ INICIAR RESTAURAÇÃO")
        self.btn_restaurar.setCursor(Qt.PointingHandCursor)
        self.btn_restaurar.setMinimumHeight(45)
        self.btn_restaurar.setStyleSheet("QPushButton { background-color: #8e44ad; color: white; font-weight: bold; font-size: 14px; border-radius: 5px; } QPushButton:hover { background-color: #9b59b6; }")
        self.btn_restaurar.clicked.connect(self.disparar_restauracao)

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setFixedHeight(10)
        self.barra_progresso.hide()

        self.texto_status = QLabel("")
        self.texto_status.setAlignment(Qt.AlignCenter)

        layout_principal.addWidget(titulo_arquivo)
        layout_principal.addLayout(layout_arquivo)
        layout_principal.addSpacing(10)
        layout_principal.addWidget(titulo_destino)
        layout_principal.addLayout(layout_destino)
        layout_principal.addSpacing(10)
        layout_principal.addWidget(titulo_senha)
        layout_principal.addWidget(self.campo_senha)
        layout_principal.addStretch()
        layout_principal.addWidget(linha)
        layout_principal.addWidget(self.btn_restaurar)
        layout_principal.addWidget(self.barra_progresso)
        layout_principal.addWidget(self.texto_status)

    def selecionar_arquivo(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione o Backup", "", "Arquivos Compactados (*.7z *.zip);;Todos os Arquivos (*.*)")
        if arquivo: self.campo_arquivo.setText(arquivo)

    def selecionar_destino(self):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione o Destino da Restauração")
        if pasta: self.campo_destino.setText(pasta)

    def disparar_restauracao(self):
        arquivo = self.campo_arquivo.text().strip()
        destino = self.campo_destino.text().strip()
        senha_digitada = self.campo_senha.text()

        if not arquivo or not destino:
            QMessageBox.warning(self, "Aviso", "Selecione o arquivo e destino.")
            return

        self.btn_restaurar.setEnabled(False)
        self.btn_restaurar.setText("⏳ EXTRAINDO ARQUIVOS...")
        self.barra_progresso.setRange(0, 0)
        self.barra_progresso.show()
        self.texto_status.setText("Descompactando... Isso pode levar alguns minutos.")

        self.worker = TrabalhadorRestauracao(arquivo, destino, senha_digitada)
        self.worker.sucesso.connect(self.restauracao_concluida)
        self.worker.erro.connect(self.restauracao_falhou)
        self.worker.start()

    def restauracao_concluida(self, resultado):
        self.resetar_interface()
        self.texto_status.setText("✅ Restauração concluída com sucesso!")
        QMessageBox.information(self, "Sucesso", resultado)

    def restauracao_falhou(self, erro_msg):
        self.resetar_interface()
        self.texto_status.setText("❌ Erro na restauração.")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Erro")
        msg_box.setText("Falha ao extrair arquivos.")
        msg_box.setDetailedText(erro_msg)
        msg_box.exec()

    def resetar_interface(self):
        self.btn_restaurar.setEnabled(True)
        self.btn_restaurar.setText("⏪ INICIAR RESTAURAÇÃO")
        self.barra_progresso.hide()


# ==========================================
# 4. ABA DE COMPARAÇÃO
# ==========================================
class AbaComparar(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(15)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # Seleção do Arquivo 1
        layout_arq1 = QHBoxLayout()
        self.campo_arq1 = QLineEdit(placeholderText="Caminho do Backup Antigo (.7z)")
        btn_arq1 = QPushButton("🔍 Selecionar")
        btn_arq1.setCursor(Qt.PointingHandCursor)
        btn_arq1.clicked.connect(lambda: self.selecionar_arquivo(self.campo_arq1))
        self.senha_arq1 = QLineEdit(placeholderText="Senha (se houver)")
        self.senha_arq1.setEchoMode(QLineEdit.Password)
        layout_arq1.addWidget(self.campo_arq1, stretch=3)
        layout_arq1.addWidget(self.senha_arq1, stretch=1)
        layout_arq1.addWidget(btn_arq1)

        # Seleção do Arquivo 2
        layout_arq2 = QHBoxLayout()
        self.campo_arq2 = QLineEdit(placeholderText="Caminho do Backup Recente (.7z)")
        btn_arq2 = QPushButton("🔍 Selecionar")
        btn_arq2.setCursor(Qt.PointingHandCursor)
        btn_arq2.clicked.connect(lambda: self.selecionar_arquivo(self.campo_arq2))
        self.senha_arq2 = QLineEdit(placeholderText="Senha (se houver)")
        self.senha_arq2.setEchoMode(QLineEdit.Password)
        layout_arq2.addWidget(self.campo_arq2, stretch=3)
        layout_arq2.addWidget(self.senha_arq2, stretch=1)
        layout_arq2.addWidget(btn_arq2)

        # Botão Comparar
        self.btn_comparar = QPushButton("⚖️ COMPARAR BACKUPS")
        self.btn_comparar.setCursor(Qt.PointingHandCursor)
        self.btn_comparar.setStyleSheet("QPushButton { background-color: #2980b9; color: white; font-weight: bold; font-size: 14px; border-radius: 5px; height: 40px; } QPushButton:hover { background-color: #3498db; }")
        self.btn_comparar.clicked.connect(self.disparar_comparacao)

        # Resultados
        self.area_resultado = QTextEdit()
        self.area_resultado.setReadOnly(True)
        self.area_resultado.setStyleSheet("QTextEdit { background-color: #1e1e1e; font-family: monospace; color: #e0e0e0; padding: 10px; border: 1px solid #3f3f46; }")

        layout_principal.addWidget(QLabel("<b>Comparador de Arquivos</b> - Verifique as diferenças entre dois backups"))
        layout_principal.addLayout(layout_arq1)
        layout_principal.addLayout(layout_arq2)
        layout_principal.addWidget(self.btn_comparar)
        layout_principal.addWidget(QLabel("<b>Resultados da Análise:</b>"))
        layout_principal.addWidget(self.area_resultado)

    def selecionar_arquivo(self, campo):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione o Backup", "", "Arquivos Compactados (*.7z);;Todos os Arquivos (*.*)")
        if arquivo: campo.setText(arquivo)

    def disparar_comparacao(self):
        arq1, arq2 = self.campo_arq1.text().strip(), self.campo_arq2.text().strip()
        if not arq1 or not arq2:
            QMessageBox.warning(self, "Aviso", "Selecione os dois arquivos para comparação.")
            return

        self.btn_comparar.setEnabled(False)
        self.btn_comparar.setText("⏳ ANALISANDO HASHES...")
        self.area_resultado.clear()

        self.worker = TrabalhadorComparar(arq1, arq2, self.senha_arq1.text(), self.senha_arq2.text())
        self.worker.sucesso.connect(self.exibir_resultado)
        self.worker.erro.connect(self.falha_comparacao)
        self.worker.start()

    def exibir_resultado(self, dados):
        self.btn_comparar.setEnabled(True)
        self.btn_comparar.setText("⚖️ COMPARAR BACKUPS")
        
        relatorio = f"=== RELATÓRIO DE COMPARAÇÃO ===\n\n"
        relatorio += f"📁 Backup 1 (Antigo):  {dados.get('total_1', 0)} arquivos\n"
        relatorio += f"📁 Backup 2 (Recente): {dados.get('total_2', 0)} arquivos\n"
        relatorio += f"✅ Arquivos idênticos:  {dados.get('common', 0)}\n"
        relatorio += f"⚠️ Arquivos alterados:  {dados.get('different', 0)}\n\n"
        
        if dados.get('only_in_first'):
            relatorio += "[-] Arquivos EXCLUSIVOS do Backup 1 (Foram deletados no Backup 2):\n"
            for f in dados['only_in_first'][:30]: relatorio += f"  - {f}\n"
            if len(dados['only_in_first']) > 30: relatorio += "  ... (lista truncada)\n"
            
        if dados.get('only_in_second'):
            relatorio += "\n[+] Arquivos EXCLUSIVOS do Backup 2 (Foram criados recentemente):\n"
            for f in dados['only_in_second'][:30]: relatorio += f"  - {f}\n"
            if len(dados['only_in_second']) > 30: relatorio += "  ... (lista truncada)\n"

        self.area_resultado.setText(relatorio)

    def falha_comparacao(self, erro):
        self.btn_comparar.setEnabled(True)
        self.btn_comparar.setText("⚖️ COMPARAR BACKUPS")
        QMessageBox.critical(self, "Erro na Comparação", f"Ocorreu um erro ao comparar os arquivos:\n\n{erro}")


# ==========================================
# 5. ABA DE DASHBOARD
# ==========================================
class AbaDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.carregar_dados()

    def setup_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setSpacing(20)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        layout_cards = QHBoxLayout()
        frame_total, self.lbl_total_backups = self.criar_card("Total de Backups", "0")
        frame_tamanho, self.lbl_tamanho_total = self.criar_card("Tamanho Total", "0 MB")
        layout_cards.addWidget(frame_total)
        layout_cards.addWidget(frame_tamanho)

        layout_botoes = QHBoxLayout()
        self.btn_apagar_selecionado = QPushButton("🗑️ Apagar Selecionado")
        self.btn_apagar_selecionado.setCursor(Qt.PointingHandCursor)
        self.btn_apagar_selecionado.setStyleSheet("QPushButton { background-color: #d35400; color: white; font-weight: bold; border-radius: 4px; padding: 8px; } QPushButton:hover { background-color: #e67e22; }")
        self.btn_apagar_selecionado.clicked.connect(self.apagar_selecionado)

        self.btn_apagar_todos = QPushButton("🚨 ZERAR HISTÓRICO")
        self.btn_apagar_todos.setCursor(Qt.PointingHandCursor)
        self.btn_apagar_todos.setStyleSheet("QPushButton { background-color: #c0392b; color: white; font-weight: bold; border-radius: 4px; padding: 8px; } QPushButton:hover { background-color: #e74c3c; }")
        self.btn_apagar_todos.clicked.connect(self.apagar_todos)

        self.btn_atualizar = QPushButton("🔄 Atualizar Tabela")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.setStyleSheet("QPushButton { background-color: #2980b9; color: white; font-weight: bold; border-radius: 4px; padding: 8px; } QPushButton:hover { background-color: #3498db; }")
        self.btn_atualizar.clicked.connect(self.carregar_dados)

        layout_botoes.addWidget(self.btn_apagar_selecionado)
        layout_botoes.addWidget(self.btn_apagar_todos)
        layout_botoes.addStretch() 
        layout_botoes.addWidget(self.btn_atualizar)

        titulo_tabela = QLabel("Histórico Recente")
        titulo_tabela.setStyleSheet("font-weight: bold; font-size: 16px; color: #ffffff;")

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Data", "Tipo", "Tamanho", "Status"])
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet("QTableWidget { background-color: #252526; alternate-background-color: #2d2d30; border: 1px solid #3f3f46; border-radius: 5px; } QHeaderView::section { background-color: #333337; color: white; font-weight: bold; padding: 5px; border: 1px solid #3f3f46; }")

        layout_principal.addLayout(layout_cards)
        layout_principal.addLayout(layout_botoes)
        layout_principal.addWidget(titulo_tabela)
        layout_principal.addWidget(self.tabela)

    def criar_card(self, titulo, valor_inicial):
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #2d2d30; border-radius: 8px; border: 1px solid #3f3f46; }")
        layout = QVBoxLayout(frame)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #a0a0a0; font-size: 12px; border: none;")
        lbl_valor = QLabel(valor_inicial)
        lbl_valor.setStyleSheet("color: #27ae60; font-size: 26px; font-weight: bold; border: none;")
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        return frame, lbl_valor

    def apagar_selecionado(self):
        linhas_selecionadas = self.tabela.selectionModel().selectedRows()
        if not linhas_selecionadas:
            QMessageBox.warning(self, "Aviso", "Selecione uma linha na tabela para apagar.")
            return

        resposta = QMessageBox.question(self, "Confirmar", "Deseja apagar o registro de backup selecionado?", QMessageBox.Yes | QMessageBox.No)
        if resposta == QMessageBox.Yes:
            if not hasattr(logic, 'delete_backup_history_entry'):
                QMessageBox.critical(self, "Erro de Motor", "A função 'delete_backup_history_entry' não foi encontrada!")
                return
                
            for index in sorted(linhas_selecionadas, reverse=True):
                linha = index.row()
                if logic.delete_backup_history_entry(linha):
                    self.tabela.removeRow(linha)
            self.recalcular_cards_da_tabela()

    def apagar_todos(self):
        resposta = QMessageBox.question(self, "⚠️ ALERTA", "Tem certeza que deseja apagar o histórico de backups?", QMessageBox.Yes | QMessageBox.No)
        if resposta == QMessageBox.Yes:
            if hasattr(logic, 'clear_backup_history'):
                if logic.clear_backup_history():
                    self.tabela.setRowCount(0)
                    self.recalcular_cards_da_tabela()

    def recalcular_cards_da_tabela(self):
        total_linhas = self.tabela.rowCount()
        self.lbl_total_backups.setText(str(total_linhas))
        tamanho_total_mb = 0.0
        for row in range(total_linhas):
            try: tamanho_total_mb += float(self.tabela.item(row, 2).text().replace(" MB", "").strip())
            except: pass
        self.lbl_tamanho_total.setText(f"{tamanho_total_mb:.2f} MB")

    def carregar_dados(self):
        self.tabela.setRowCount(0)
        try:
            if hasattr(logic, 'load_backup_history'):
                historico = logic.load_backup_history()
                if not historico: return 
                for row_idx, item in enumerate(historico):
                    self.tabela.insertRow(row_idx)
                    self.tabela.setItem(row_idx, 0, QTableWidgetItem(str(item.get('date', item.get('timestamp', '-')))))
                    self.tabela.setItem(row_idx, 1, QTableWidgetItem(str(item.get('type', 'Completo'))))
                    tamanho_mb = item.get('size', 0) / (1024 * 1024)
                    self.tabela.setItem(row_idx, 2, QTableWidgetItem(f"{tamanho_mb:.2f} MB"))
                    self.tabela.setItem(row_idx, 3, QTableWidgetItem(str(item.get('status', '-'))))
                self.recalcular_cards_da_tabela()
        except: pass