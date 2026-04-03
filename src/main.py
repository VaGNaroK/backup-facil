import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from ui_components import AbaBackup, AbaDashboard, AbaRestauracao, AbaComparar, AbaLogs, AbaAgendamento, AbaSobre

# 🧭 GPS PARA IMAGENS
def get_asset_path(filename):
    if getattr(sys, 'frozen', False):
        # O PyInstaller esconde as imagens nesta pasta temporária
        base_dir = sys._MEIPASS 
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "assets", filename)

# --- ESTILO DARK PROFISSIONAL (QSS) ---
ESTILO_DARK = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QTabWidget::pane {
    border: 1px solid #333333;
    background-color: #252526;
    border-radius: 5px;
}
QTabBar::tab {
    background-color: #2d2d30;
    color: #a0a0a0;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #252526;
    color: #ffffff;
    border-bottom: 2px solid #27ae60;
}
QTabBar::tab:hover:!selected { background-color: #3e3e42; }
QLineEdit, QListWidget, QComboBox, QTextEdit {
    background-color: #2d2d30;
    border: 1px solid #3f3f46;
    border-radius: 4px;
    padding: 8px;
    color: #ffffff;
}
QLineEdit:focus, QListWidget:focus, QComboBox:focus, QTextEdit:focus { border: 1px solid #007acc; }
QPushButton {
    background-color: #3e3e42;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 8px 15px;
    color: #ffffff;
}
QPushButton:hover { background-color: #4e4e52; border: 1px solid #007acc; }
QPushButton:pressed { background-color: #007acc; }
QCheckBox { color: #e0e0e0; font-weight: bold; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 3px; border: 1px solid #3f3f46; background-color: #2d2d30; }
QCheckBox::indicator:checked { background-color: #27ae60; border: 1px solid #27ae60; }
"""

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backup Fácil Professional")
        
        # ✅ APLICANDO O SEU ÍCONE!
        caminho_icone = get_asset_path("icon.png")
        if os.path.exists(caminho_icone):
            self.setWindowIcon(QIcon(caminho_icone))
            
        self.resize(950, 750)
        
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        
        self.tabs = QTabWidget()
        
        self.aba_backup = AbaBackup()
        self.aba_restauracao = AbaRestauracao()
        self.aba_comparar = AbaComparar()
        self.aba_dashboard = AbaDashboard()
        self.aba_logs = AbaLogs()
        self.aba_agendamento = AbaAgendamento()
        self.aba_sobre = AbaSobre()

        self.tabs.addTab(self.aba_backup, "💾 Backup")
        self.tabs.addTab(self.aba_restauracao, "🕒 Restauração")
        self.tabs.addTab(self.aba_comparar, "⚖️ Comparar")
        self.tabs.addTab(self.aba_dashboard, "📈 Dashboard")
        self.tabs.addTab(self.aba_logs, "📝 Logs")
        self.tabs.addTab(self.aba_agendamento, "📅 Agendamento")
        self.tabs.addTab(self.aba_sobre, "ℹ️ Sobre")

        layout_principal.addWidget(self.tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILO_DARK)
    
    # Adiciona o ícone também na barra de tarefas do sistema operacional
    caminho_icone = get_asset_path("icon.png")
    if os.path.exists(caminho_icone):
        app.setWindowIcon(QIcon(caminho_icone))
        
    janela = JanelaPrincipal()
    janela.show()
    
    sys.exit(app.exec())