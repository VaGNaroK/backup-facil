import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
import threading
from datetime import datetime
from logic import (
    start_backup_process, restore_backup_process, start_scheduler, 
    stop_scheduler, save_config, load_config, check_7z_password,
    load_profiles, save_profiles, get_profile_names,
    get_dashboard_data, compare_backups, get_disk_space,
    load_backup_history, toggle_pause_backup, expand_path,
    abort_backup
)

DND_AVAILABLE = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except:
    pass

class BackupApp(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.ACCENT_COLOR = "#2ecc71"
        self.GRAY_BTN_COLOR = "#34495e"
        
        self.profiles = load_profiles()
        self.current_profile = "default"
        saved_data = load_config(self.current_profile)
        
        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color=self.ACCENT_COLOR)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        self.tab_backup = self.tabview.add("Backup")
        self.tab_restore = self.tabview.add("Restauração")
        self.tab_dashboard = self.tabview.add("📊 Dashboard")
        self.tab_profiles = self.tabview.add("Perfis")
        self.tab_settings = self.tabview.add("Configurações")
        self.tab_log = self.tabview.add("Log")

        self.setup_backup_tab(saved_data)
        self.setup_restore_tab()
        self.setup_dashboard_tab()
        self.setup_profiles_tab()
        self.setup_settings_tab(saved_data)
        self.setup_log_tab()

        self.progress = ctk.CTkProgressBar(self, progress_color=self.ACCENT_COLOR)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=20, pady=(10, 2))
        
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(pady=2)

        self.btn_pause = ctk.CTkButton(self.control_frame, text="⏸️ Pausar", fg_color=self.GRAY_BTN_COLOR, command=self.pause_action, width=140)
        self.btn_pause.pack(side="left", padx=5)
        self.btn_pause.configure(state="disabled")

        self.btn_cancel = ctk.CTkButton(self.control_frame, text="⏹️ Cancelar", fg_color="#e74c3c", command=self.cancel_action, width=140)
        self.btn_cancel.pack(side="left", padx=5)
        self.btn_cancel.configure(state="disabled")

        self.lbl_time_remaining = ctk.CTkLabel(self, text="", text_color="gray", font=("Roboto", 10))
        self.lbl_time_remaining.pack(pady=(0, 5))
        
        self.lbl_status = ctk.CTkLabel(self, text="Pronto.", text_color="gray")
        self.lbl_status.pack(pady=(0, 10))
        
        self.lbl_theme = ctk.CTkLabel(self, text="🌙 Dark", text_color="gray", font=("Roboto", 9))
        self.lbl_theme.pack(pady=(0, 5))

        if DND_AVAILABLE:
            try: self.setup_drag_and_drop()
            except Exception: pass

        # ✅ SOLUÇÃO 1: Adia a leitura do HD e o arranque do agendador em 200ms
        # Isso faz a janela aparecer imediatamente para o utilizador!
        self.after(200, lambda: self._finish_initialization(saved_data))

    def _finish_initialization(self, saved_data):
        """ ✅ Carregamento pós-janela para evitar os 12 segundos de delay """
        if saved_data.get("origin") and saved_data.get("destination"):
            start_scheduler(saved_data)
        self.refresh_dashboard()

    def pause_action(self):
        is_paused = toggle_pause_backup()
        if is_paused:
            self.btn_pause.configure(text="▶️ Retomar", fg_color="#f39c12", text_color="white")
            self.lbl_status.configure(text="PAUSADO", text_color="#f39c12")
            self.write_log("Backup pausado pelo usuário.")
        else:
            self.btn_pause.configure(text="⏸️ Pausar", fg_color=self.GRAY_BTN_COLOR)
            self.lbl_status.configure(text="Processando...", text_color="yellow")
            self.write_log("Backup retomado.")

    def cancel_action(self):
        if messagebox.askyesno("Cancelar", "Tem a certeza que deseja cancelar o backup em curso?\nOs ficheiros incompletos serão removidos."):
            abort_backup()
            self.lbl_status.configure(text="A cancelar o backup...", text_color="#e74c3c")
            self.btn_pause.configure(state="disabled")
            self.btn_cancel.configure(state="disabled")

    def setup_drag_and_drop(self):
        try:
            self.origin_view.drop_target_register(DND_FILES)
            self.origin_view.dnd_bind('<<Drop>>', self.on_drop)
        except: pass

    def on_drop(self, event):
        try:
            paths = event.data.split()
            for path in paths:
                path = path.strip('{}')
                if os.path.isdir(path):
                    self.add_to_origin_list(path)
                    self.write_log(f"Pasta adicionada via drag & drop: {path}")
        except: pass

    def write_log(self, message):
        self.log_view.configure(state="normal")
        self.log_view.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_view.see("end")
        self.log_view.configure(state="disabled")

    def setup_log_tab(self):
        self.log_view = ctk.CTkTextbox(self.tab_log, font=("Consolas", 11))
        self.log_view.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_view.configure(state="disabled")

    def setup_backup_tab(self, saved_data):
        ctk.CTkLabel(self.tab_backup, text="Fontes do Backup (Pastas):", font=("Roboto", 12, "bold")).pack(anchor="w", padx=15, pady=(10,0))
        
        if DND_AVAILABLE:
            ctk.CTkLabel(self.tab_backup, text="💡 Dica: Arraste pastas aqui!", font=("Roboto", 9), text_color="gray").pack(anchor="w", padx=15)
        
        self.origin_list = []
        self.origin_view = ctk.CTkTextbox(self.tab_backup, height=100)
        self.origin_view.pack(fill="x", padx=15, pady=5)
        self.origin_view.configure(state="disabled")
        
        saved_origins = saved_data.get("origin", [])
        if isinstance(saved_origins, str): saved_origins = [saved_origins] if saved_origins else []
        for p in saved_origins: self.add_to_origin_list(p)

        btns = ctk.CTkFrame(self.tab_backup, fg_color="transparent")
        btns.pack(fill="x", padx=15)
        ctk.CTkButton(btns, text="+ Pasta", fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=self.select_origin_folder).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(btns, text="Limpar", fg_color="#e74c3c", width=100, command=self.clear_origin_list).pack(side="right")

        self.dest_entry = self.add_file_picker(self.tab_backup, "📁 Destino do Backup", saved_data.get("destination", ""))

        row = ctk.CTkFrame(self.tab_backup, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=15)
        self.combo_compression = ctk.CTkOptionMenu(row, values=["Armazenar", "Rápido", "Normal", "Máximo"])
        self.combo_compression.set(saved_data.get("compression", "Normal"))
        self.combo_compression.pack(side="left")
        self.entry_pass = ctk.CTkEntry(row, placeholder_text="Senha Opcional", show="*", width=200)
        self.entry_pass.pack(side="right", fill="x", expand=True, padx=10)

        self.incremental_var = ctk.BooleanVar(value=saved_data.get("incremental", False))
        ctk.CTkCheckBox(self.tab_backup, text="🔄 Backup Incremental (apenas arquivos modificados)", variable=self.incremental_var).pack(anchor="w", padx=15, pady=5)

        ctk.CTkLabel(self.tab_backup, text="🔍 Filtros Avançados:", font=("Roboto", 11, "bold")).pack(anchor="w", padx=15, pady=(15,5))
        
        filters_frame = ctk.CTkFrame(self.tab_backup, fg_color="transparent")
        filters_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(filters_frame, text="Tamanho Mín. (KB):").pack(side="left")
        self.entry_min_size = ctk.CTkEntry(filters_frame, width=60, placeholder_text="0")
        self.entry_min_size.pack(side="left", padx=5)
        
        ctk.CTkLabel(filters_frame, text="Tamanho Máx. (KB):").pack(side="left", padx=(15,0))
        self.entry_max_size = ctk.CTkEntry(filters_frame, width=60, placeholder_text="0")
        self.entry_max_size.pack(side="left", padx=5)
        
        ctk.CTkLabel(filters_frame, text="SOMENTE estas extensões:").pack(side="left", padx=(15,0))
        self.entry_extensions = ctk.CTkEntry(filters_frame, width=130, placeholder_text="Ex: .txt, .pdf")
        self.entry_extensions.pack(side="left", padx=5)

        ctk.CTkLabel(filters_frame, text="Ignorar Pastas:").pack(side="left", padx=(15,0))
        self.entry_ignore_folders = ctk.CTkEntry(filters_frame, width=120, placeholder_text="temp, cache")
        self.entry_ignore_folders.pack(side="left", padx=5)
        self.entry_ignore_folders.insert(0, saved_data.get("folder_exclusions", ""))

        self.btn_start = ctk.CTkButton(self.tab_backup, text="INICIAR BACKUP", height=50, font=("Roboto", 16, "bold"), fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=self.start_backup_thread)
        self.btn_start.pack(fill="x", pady=15, padx=15)

    def setup_restore_tab(self):
        ctk.CTkLabel(self.tab_restore, text="Restaurar Backup:", font=("Roboto", 14, "bold")).pack(pady=15)
        
        frame_file = ctk.CTkFrame(self.tab_restore, fg_color="transparent")
        frame_file.pack(fill="x", padx=20, pady=5)
        self.restore_file_entry = ctk.CTkEntry(frame_file, placeholder_text="Selecione o arquivo .7z")
        self.restore_file_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(frame_file, text="📂", width=40, fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=self.select_restore_file).pack(side="right")
        
        self.restore_pass = ctk.CTkEntry(self.tab_restore, placeholder_text="Senha do backup (se houver)", show="*")
        self.restore_pass.pack(fill="x", padx=20, pady=10)

        frame_dest = ctk.CTkFrame(self.tab_restore, fg_color="transparent")
        frame_dest.pack(fill="x", padx=20, pady=5)
        self.restore_dest_entry = ctk.CTkEntry(frame_dest, placeholder_text="Pasta de destino para restaurar")
        self.restore_dest_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(frame_dest, text="📂", width=40, fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=lambda: self.browse_folder(self.restore_dest_entry)).pack(side="right")

        ctk.CTkButton(self.tab_restore, text="RESTAURAR BACKUP", height=45, font=("Roboto", 14, "bold"), fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=self.start_restore_thread).pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(self.tab_restore, text="🔍 Comparar Backups:", font=("Roboto", 12, "bold")).pack(anchor="w", padx=20, pady=(15,5))
        
        compare_frame = ctk.CTkFrame(self.tab_restore, fg_color="transparent")
        compare_frame.pack(fill="x", padx=20, pady=5)
        self.compare_file1 = ctk.CTkEntry(compare_frame, placeholder_text="Backup 1 (.7z)")
        self.compare_file1.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(compare_frame, text="📂", width=40, command=lambda: self.select_compare_file(self.compare_file1)).pack(side="left")
        
        compare_frame2 = ctk.CTkFrame(self.tab_restore, fg_color="transparent")
        compare_frame2.pack(fill="x", padx=20, pady=5)
        self.compare_file2 = ctk.CTkEntry(compare_frame2, placeholder_text="Backup 2 (.7z)")
        self.compare_file2.pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(compare_frame2, text="📂", width=40, command=lambda: self.select_compare_file(self.compare_file2)).pack(side="left")
        
        ctk.CTkButton(self.tab_restore, text="Comparar Backups", fg_color="#9b59b6", command=self.run_comparison).pack(fill="x", padx=20, pady=10)
        self.compare_result = ctk.CTkTextbox(self.tab_restore, height=150)
        self.compare_result.pack(fill="x", padx=20, pady=5)
        self.compare_result.configure(state="disabled")

    def select_compare_file(self, entry):
        f = filedialog.askopenfilename(filetypes=[("7-Zip", "*.7z")])
        if f: entry.delete(0, "end"); entry.insert(0, f)

    def run_comparison(self):
        file1 = self.compare_file1.get()
        file2 = self.compare_file2.get()
        if not file1 or not file2: return messagebox.showwarning("Atenção", "Selecione dois arquivos para comparar!")
        
        pwd1 = None
        if check_7z_password(file1):
            dialog1 = ctk.CTkInputDialog(text=f"O backup '{os.path.basename(file1)}' possui senha. Digite-a para continuar:", title="Senha Necessária")
            pwd1 = dialog1.get_input()
            if pwd1 is None: return 
            
        pwd2 = None
        if check_7z_password(file2):
            dialog2 = ctk.CTkInputDialog(text=f"O backup '{os.path.basename(file2)}' possui senha. Digite-a para continuar:", title="Senha Necessária")
            pwd2 = dialog2.get_input()
            if pwd2 is None: return
        
        self.write_log(f"Comparando: {os.path.basename(file1)} vs {os.path.basename(file2)}")
        result = compare_backups(file1, file2, pwd1, pwd2)
        
        self.compare_result.configure(state="normal")
        self.compare_result.delete("1.0", "end")
        
        if "error" in result: self.compare_result.insert("1.0", f"Erro: {result['error']}")
        else:
            text = f"📊 RESULTADO DA COMPARAÇÃO\nBackup 1: {result['total_1']} arquivos\nBackup 2: {result['total_2']} arquivos\n✅ Arquivos em comum: {result['common']}\n📁 Apenas no Backup 1: {len(result['only_in_first'])}\n📁 Apenas no Backup 2: {len(result['only_in_second'])}\n🔄 Diferenças totais: {result['different']}\n"
            self.compare_result.insert("1.0", text)
        self.compare_result.configure(state="disabled")

    def select_restore_file(self):
        f = filedialog.askopenfilename(filetypes=[("7-Zip", "*.7z")])
        if f:
            self.restore_file_entry.delete(0, "end"); self.restore_file_entry.insert(0, f)
            if not check_7z_password(f):
                self.restore_pass.delete(0, "end"); self.restore_pass.configure(state="disabled", placeholder_text="Arquivo sem senha")
            else: self.restore_pass.configure(state="normal", placeholder_text="Digite a senha")

    def start_restore_thread(self):
        archive = self.restore_file_entry.get()
        target = self.restore_dest_entry.get()
        
        if not archive or not os.path.exists(archive): 
            return messagebox.showerror("Erro", "Arquivo de backup não encontrado!")
            
        if not target or not os.path.exists(target): 
            return messagebox.showerror("Erro", "Selecione uma pasta de destino válida para restaurar!")

        self.lbl_status.configure(text="Restaurando (Pode demorar vários minutos)...", text_color="yellow")
        self.write_log(f"Restauração iniciada para: {target}")
        threading.Thread(target=self.run_restore_task, args=(archive, target), daemon=True).start()

    def run_restore_task(self, archive, target):
        self.progress.configure(mode="indeterminate"); self.progress.start()
        res, success = restore_backup_process(archive, target, self.restore_pass.get(), self.write_log)
        self.progress.stop(); self.progress.configure(mode="determinate"); self.progress.set(1)
        self.lbl_status.configure(text=res, text_color=self.ACCENT_COLOR if success else "red")

    def setup_dashboard_tab(self):
        ctk.CTkLabel(self.tab_dashboard, text="📊 Dashboard de Saúde dos Backups", font=("Roboto", 16, "bold")).pack(pady=15)
        stats_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        self.lbl_total_backups = self.create_stat_card(stats_frame, "Total Backups", "0", 0)
        self.lbl_success_rate = self.create_stat_card(stats_frame, "Taxa de Sucesso", "0%", 1)
        self.lbl_total_size = self.create_stat_card(stats_frame, "Tamanho Total", "0 MB", 2)
        self.lbl_disk_space = self.create_stat_card(stats_frame, "Espaço Livre", "Calculando...", 3)
        
        ctk.CTkLabel(self.tab_dashboard, text="🕐 Último Backup:", font=("Roboto", 12, "bold")).pack(anchor="w", padx=20, pady=(20,5))
        self.lbl_last_backup = ctk.CTkLabel(self.tab_dashboard, text="Nenhum backup realizado", text_color="gray", justify="left")
        self.lbl_last_backup.pack(anchor="w", padx=20)
        
        ctk.CTkLabel(self.tab_dashboard, text="⚠️ Alertas de Espaço:", font=("Roboto", 12, "bold")).pack(anchor="w", padx=20, pady=(20,5))
        self.lbl_space_alert = ctk.CTkLabel(self.tab_dashboard, text="Verificando...", text_color="gray", justify="left")
        self.lbl_space_alert.pack(anchor="w", padx=20)
        
        ctk.CTkButton(self.tab_dashboard, text="🔄 Atualizar Dashboard (F5)", fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=self.refresh_dashboard).pack(pady=20)

    def create_stat_card(self, parent, title, value, col):
        frame = ctk.CTkFrame(parent)
        frame.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(frame, text=title, font=("Roboto", 10), text_color="gray").pack()
        lbl_value = ctk.CTkLabel(frame, text=value, font=("Roboto", 16, "bold"), text_color=self.ACCENT_COLOR)
        lbl_value.pack()
        return lbl_value

    def refresh_dashboard(self):
        """ ✅ SOLUÇÃO 3/4: Thread Assíncrona para não travar a UI ao clicar Atualizar """
        self.lbl_disk_space.configure(text="Calculando...")
        self.lbl_space_alert.configure(text="Verificando...", text_color="gray")
        threading.Thread(target=self._refresh_dashboard_thread, daemon=True).start()

    def _refresh_dashboard_thread(self):
        data = get_dashboard_data()
        dest = self.dest_entry.get() if hasattr(self, 'dest_entry') else ""
        space_info = None
        
        if dest and os.path.exists(dest):
            space_info = get_disk_space(dest)
            
        # O tkinter não gosta que mudem a UI fora da thread principal, então devolvemos com 'after'
        self.after(0, lambda: self._update_dashboard_ui(data, dest, space_info))

    def _update_dashboard_ui(self, data, dest, space_info):
        self.lbl_total_backups.configure(text=str(data["total_backups"]))
        self.lbl_success_rate.configure(text=f"{data['success_rate']:.1f}%")
        self.lbl_total_size.configure(text=f"{data['total_size'] / (1024*1024):.1f} MB")
        
        if space_info and space_info["success"]:
            free_gb = space_info["free"] / (1024*1024*1024)
            self.lbl_disk_space.configure(text=f"{free_gb:.1f} GB")
            if space_info["percent_used"] > 90: self.lbl_space_alert.configure(text=f"🔴 CRÍTICO: {space_info['percent_used']:.1f}% do disco usado!", text_color="red")
            elif space_info["percent_used"] > 75: self.lbl_space_alert.configure(text=f"🟡 ATENÇÃO: {space_info['percent_used']:.1f}% do disco usado", text_color="orange")
            else: self.lbl_space_alert.configure(text="🟢 Espaço em disco OK", text_color="green")
        else:
            self.lbl_disk_space.configure(text="N/A")
            self.lbl_space_alert.configure(text="Destino não configurado ou offline")
        
        if data["last_backup"]:
            lb = data["last_backup"]
            self.lbl_last_backup.configure(text=f"📁 {lb.get('archive', 'Desconhecido')}\n📅 {lb.get('timestamp', '')[:19].replace('T', ' ')}\n📊 {lb.get('files', 0)} arquivos | {lb.get('size', 0) / (1024*1024):.1f} MB\n⏱️ {lb.get('duration', 0):.1f}s | {lb.get('type', 'completo')}")
        else: self.lbl_last_backup.configure(text="Nenhum backup realizado")

    def setup_profiles_tab(self):
        ctk.CTkLabel(self.tab_profiles, text="Gerenciar Perfis de Backup", font=("Roboto", 14, "bold")).pack(pady=15)
        ctk.CTkLabel(self.tab_profiles, text="Perfis Salvos:", font=("Roboto", 12)).pack(anchor="w", padx=20, pady=(10,0))
        self.profile_listbox = ctk.CTkOptionMenu(self.tab_profiles, values=get_profile_names())
        self.profile_listbox.pack(fill="x", padx=20, pady=5)
        self.profile_listbox.set(self.current_profile)
        
        btn_frame = ctk.CTkFrame(self.tab_profiles, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Carregar", fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=self.load_profile).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(btn_frame, text="Salvar Neste Perfil", fg_color="#3498db", command=self.save_current_profile).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(btn_frame, text="Novo Perfil", fg_color="#9b59b6", command=self.create_new_profile).pack(side="left", fill="x", expand=True, padx=(0,5))
        ctk.CTkButton(btn_frame, text="Excluir", fg_color="#e74c3c", command=self.delete_profile).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(self.tab_profiles, text="💡 Perfis permitem salvar configurações diferentes\n(ex: 'Trabalho', 'Pessoal', 'Projetos')", font=("Roboto", 10), text_color="gray", justify="left").pack(anchor="w", padx=20, pady=20)

    def load_profile(self):
        profile_name = self.profile_listbox.get()
        if profile_name == self.current_profile: return
        self.current_profile = profile_name
        saved_data = load_config(profile_name)
        
        self.dest_entry.delete(0, "end"); self.dest_entry.insert(0, saved_data.get("destination", ""))
        self.combo_compression.set(saved_data.get("compression", "Normal"))
        self.entry_pass.delete(0, "end")
        self.incremental_var.set(saved_data.get("incremental", False))
        
        self.origin_list = []
        self.origin_view.configure(state="normal"); self.origin_view.delete("1.0", "end"); self.origin_view.configure(state="disabled")
        for p in saved_data.get("origin", []): self.add_to_origin_list(p)
        
        self.write_log(f"Perfil carregado: {profile_name}")
        self.lbl_status.configure(text=f"Perfil '{profile_name}' carregado!", text_color=self.ACCENT_COLOR)
        self.refresh_dashboard()

    def save_current_profile(self):
        profile_name = self.profile_listbox.get()
        save_config(self.get_config(), profile_name)
        self.write_log(f"Perfil salvo: {profile_name}")
        self.lbl_status.configure(text=f"Perfil '{profile_name}' salvo!", text_color=self.ACCENT_COLOR)
        messagebox.showinfo("Sucesso", f"Configurações salvas no perfil '{profile_name}'!")

    def save_current_profile_quick(self):
        profile_name = self.profile_listbox.get()
        save_config(self.get_config(), profile_name)
        self.lbl_status.configure(text=f"✅ Salvo (Ctrl+S)", text_color=self.ACCENT_COLOR)

    def create_new_profile(self):
        dialog = ctk.CTkInputDialog(text="Nome do novo perfil:", title="Novo Perfil")
        profile_name = dialog.get_input()
        if profile_name and profile_name.strip():
            profile_name = profile_name.strip().replace(" ", "_")
            if profile_name in self.profiles: return messagebox.showwarning("Atenção", "Perfil já existe!")
            save_config(self.get_config(), profile_name)
            self.profile_listbox.configure(values=get_profile_names()); self.profile_listbox.set(profile_name)
            self.current_profile = profile_name
            self.write_log(f"Novo perfil criado: {profile_name}")
            messagebox.showinfo("Sucesso", f"Perfil '{profile_name}' criado!")

    def delete_profile(self):
        profile_name = self.profile_listbox.get()
        if profile_name == "default": return messagebox.showwarning("Atenção", "Não é possível excluir o perfil padrão!")
        if messagebox.askyesno("Confirmar", f"Excluir perfil '{profile_name}'?"):
            self.profiles = load_profiles()
            if profile_name in self.profiles:
                del self.profiles[profile_name]
                save_profiles(self.profiles)
                self.profile_listbox.configure(values=get_profile_names()); self.profile_listbox.set("default")
                self.current_profile = "default"
                self.write_log(f"Perfil excluído: {profile_name}")
                messagebox.showinfo("Sucesso", f"Perfil '{profile_name}' excluído!")

    def setup_settings_tab(self, saved_data):
        ctk.CTkLabel(self.tab_settings, text="Agendamento Automático:", font=("Roboto", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 0))
        f = ctk.CTkFrame(self.tab_settings, fg_color="transparent"); f.pack(fill="x", padx=20, pady=10)
        self.combo_freq = ctk.CTkOptionMenu(f, values=["Diário", "Semanal"]); self.combo_freq.set(saved_data.get("frequency", "Diário")); self.combo_freq.pack(side="left")
        self.entry_time = ctk.CTkEntry(f, width=80, placeholder_text="03:00"); self.entry_time.insert(0, saved_data.get("time", "03:00")); self.entry_time.pack(side="left", padx=10)
        
        ctk.CTkLabel(self.tab_settings, text="Retenção de Backups:", font=("Roboto", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 0))
        retention_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent"); retention_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(retention_frame, text="Manter últimos:").pack(side="left")
        self.entry_retention = ctk.CTkEntry(retention_frame, width=60); self.entry_retention.insert(0, str(saved_data.get("retention", 5))); self.entry_retention.pack(side="left", padx=10)
        ctk.CTkLabel(retention_frame, text="backups (0 = ilimitado)").pack(side="left")
        ctk.CTkButton(self.tab_settings, text="Salvar e Ativar Agendamento", command=self.activate_schedule).pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(self.tab_settings, text="🎨 Aparência:", font=("Roboto", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 0))
        ctk.CTkButton(self.tab_settings, text="🌙 Alternar Tema (Ctrl+T)", fg_color="#34495e", command=lambda: self.master.toggle_theme()).pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.tab_settings, text="⌨️ Atalhos de Teclado:", font=("Roboto", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 0))
        shortcuts_text = "Ctrl+S - Salvar perfil atual\n" "F5 - Atualizar dashboard\n" "Ctrl+T - Alternar tema Dark/Light\n" "Ctrl+Q - Sair do aplicativo"
        ctk.CTkLabel(self.tab_settings, text=shortcuts_text, font=("Consolas", 10), text_color="gray", justify="left").pack(anchor="w", padx=20, pady=10)

    def update_theme_status(self, theme): self.lbl_theme.configure(text=f"{'🌙' if theme == 'Dark' else '☀️'} {theme}")

    def add_to_origin_list(self, path):
        if path and path not in self.origin_list:
            self.origin_list.append(path); self.origin_view.configure(state="normal")
            self.origin_view.delete("1.0", "end"); self.origin_view.insert("1.0", "\n".join(self.origin_list)); self.origin_view.configure(state="disabled")

    def select_origin_folder(self):
        f = filedialog.askdirectory()
        if f: self.add_to_origin_list(f)

    def clear_origin_list(self):
        self.origin_list = []; self.origin_view.configure(state="normal"); self.origin_view.delete("1.0", "end"); self.origin_view.configure(state="disabled")

    def add_file_picker(self, parent, placeholder, default_value):
        fr = ctk.CTkFrame(parent, fg_color="transparent"); fr.pack(fill="x", pady=2, padx=15)
        en = ctk.CTkEntry(fr, placeholder_text=placeholder); en.pack(side="left", fill="x", expand=True, padx=(0,5)); en.insert(0, default_value)
        ctk.CTkButton(fr, text="📂", width=40, fg_color=self.ACCENT_COLOR, text_color=("black", "white"), command=lambda: self.browse_folder(en)).pack(side="right")
        return en

    def browse_folder(self, entry):
        f = filedialog.askdirectory()
        if f: entry.delete(0, "end"); entry.insert(0, f)

    def get_config(self):
        try: retention_val = int(self.entry_retention.get())
        except: retention_val = 5
        
        filters = {}
        try:
            min_size = int(self.entry_min_size.get())
            if min_size > 0: filters["min_size"] = min_size * 1024
        except: pass
        try:
            max_size = int(self.entry_max_size.get())
            if max_size > 0: filters["max_size"] = max_size * 1024
        except: pass
        
        exts = self.entry_extensions.get().strip()
        if exts: filters["file_types"] = [e.strip().lower() for e in exts.split(',')]
        
        folder_exts = self.entry_ignore_folders.get().split(',')
        
        return {
            "origin": self.origin_list, 
            "destination": expand_path(self.dest_entry.get()),
            "compression": self.combo_compression.get(), 
            "password": self.entry_pass.get(),
            "frequency": self.combo_freq.get(), 
            "time": self.entry_time.get(),
            "retention": retention_val, 
            "incremental": self.incremental_var.get(),
            "filters": filters, 
            "folder_exclusions": self.entry_ignore_folders.get(),
            "folder_list": [f.strip() for f in folder_exts if f.strip()]
        }

    def start_backup_thread(self):
        conf = self.get_config()
        if not conf["origin"]: return messagebox.showwarning("Atenção", "Selecione pelo menos uma pasta de origem!")
        save_config(conf, self.current_profile)
        
        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸️ Pausar", fg_color=self.GRAY_BTN_COLOR)
        self.btn_cancel.configure(state="normal")
        
        threading.Thread(target=self.run_backup_task, args=(conf,), daemon=True).start()

    def run_backup_task(self, conf):
        self.progress.configure(mode="determinate"); self.progress.set(0)
        
        def progress_callback(value, remaining=0):
            self.progress.set(value)
            if remaining > 0:
                mins, secs = int(remaining // 60), int(remaining % 60)
                self.lbl_time_remaining.configure(text=f"⏱️ Tempo restante: {mins}m {secs}s")
        
        r, success, stats = start_backup_process(
            conf["origin"], conf["destination"], conf["compression"], conf["password"], 
            "", conf["retention"], progress_callback, self.write_log, 
            conf["incremental"], conf["filters"], conf.get("folder_list", [])
        )
        
        self.lbl_time_remaining.configure(text="")
        self.lbl_status.configure(text=r, text_color=self.ACCENT_COLOR if success else "red")
        
        self.btn_start.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="⏸️ Pausar", fg_color=self.GRAY_BTN_COLOR)
        self.btn_cancel.configure(state="disabled")
        
        if success: self.refresh_dashboard()

    def activate_schedule(self):
        conf = self.get_config()
        if not conf["origin"] or not conf["destination"]: return messagebox.showwarning("Atenção", "Preencha as pastas de origem e destino na aba Backup primeiro!")
        save_config(conf, self.current_profile); start_scheduler(conf)
        self.write_log(f"Agendamento ativo para: {conf['frequency']} às {conf['time']}.")
        messagebox.showinfo("Sucesso", f"Agendamento configurado para {conf['frequency']} às {conf['time']}.\nRetenção: {conf['retention']} backups.\nBackup incremental: {'Ativado' if conf['incremental'] else 'Desativado'}\n\n⚠️ O programa precisa estar aberto para o backup automático funcionar.")