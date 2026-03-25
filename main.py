import customtkinter as ctk
from ui_components import BackupApp
import threading
import sys
import platform

try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Backup Fácil Professional")
        self.geometry("900x800")
        
        if platform.system() == "Windows":
            try: self.iconbitmap("icon.ico")
            except: pass
        else:
            try:
                from tkinter import PhotoImage
                icon = PhotoImage(file="icon.png")
                self.iconphoto(False, icon)
            except: pass
        
        self.app_frame = BackupApp(master=self)
        self.tray_icon = None
        self.running = True
        self.current_theme = "Dark"
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_keyboard_shortcuts()
        
        # ✅ CORREÇÃO: Fim da lentidão de 10s no arranque!
        # O programa agora desenha a janela instantaneamente e carrega o ícone no fundo.
        if TRAY_AVAILABLE: 
            threading.Thread(target=self.setup_tray, daemon=True).start()

    def setup_keyboard_shortcuts(self):
        self.bind('<Control-s>', lambda e: self.app_frame.save_current_profile_quick())
        self.bind('<F5>', lambda e: self.app_frame.refresh_dashboard())
        self.bind('<Control-t>', lambda e: self.toggle_theme())
        self.bind('<Control-q>', lambda e: self.exit_app())

    def toggle_theme(self):
        if self.current_theme == "Dark": ctk.set_appearance_mode("Light"); self.current_theme = "Light"
        else: ctk.set_appearance_mode("Dark"); self.current_theme = "Dark"
        self.app_frame.update_theme_status(self.current_theme)

    def setup_tray(self):
        try:
            image = Image.new('RGB', (64, 64), color='green')
            self.tray_icon = pystray.Icon("backup_tray", image, "Backup Fácil Pro", menu=pystray.Menu(item("Abrir", self.show_window, default=True), item("Minimizar", self.minimize_to_tray), item("Sair", self.exit_app)))
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except Exception as e: print(f"Erro ao configurar tray: {e}")

    def show_window(self, icon=None, item=None):
        self.after(0, lambda: self.deiconify())
        self.after(0, lambda: self.focus_force())
        self.after(0, lambda: self.attributes('-topmost', True))
        self.after(100, lambda: self.attributes('-topmost', False))

    def minimize_to_tray(self, icon=None, item=None):
        self.withdraw()
        if self.tray_icon:
            try:
                self.tray_icon.notify("Backup Fácil", "Minimizado para a bandeja")
            except Exception:
                pass

    def on_close(self):
        from logic import stop_scheduler
        stop_scheduler()
        if self.tray_icon: self.minimize_to_tray()
        else: self.exit_app()

    def exit_app(self, icon=None, item=None):
        from logic import stop_scheduler
        stop_scheduler()
        self.running = False
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()