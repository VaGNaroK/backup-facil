import os
import sys
import json
import schedule
import time
import threading
import hashlib
import shutil
import sqlite3
import re
import logging
import keyring
from datetime import datetime
import py7zr
from plyer import notification

# ==========================================
# FONTE ÚNICA DE VERDADE (VERSÃO DO APP)
# ==========================================
APP_VERSION = "0.3.9"

logger = logging.getLogger("backup_facil")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    _fh = logging.StreamHandler(sys.stdout)
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(_fh)

# ==========================================
# 🧭 GPS DE DIRETÓRIOS (ATUALIZADO PARA FLATPAK/LINUX)
# ==========================================
def get_base_dir():
    """Descobre a raiz do projeto e define onde salvar os dados de forma segura"""
    
    # 1. Checagem VIP para Flatpak (O sandbox redireciona o ~ automaticamente para ~/.var/app/...)
    if os.environ.get("FLATPAK_ID"):
        flatpak_data_dir = os.path.join(os.path.expanduser("~"), "data")
        os.makedirs(flatpak_data_dir, exist_ok=True)
        return flatpak_data_dir

    # 2. Checagem para instaladores nativos (.deb ou Windows .exe)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # Se foi instalado globalmente no Linux (via .deb)
        if exe_dir == '/usr/bin':
            user_config_dir = os.path.join(os.path.expanduser("~"), ".config", "backup_facil_pro")
            os.makedirs(user_config_dir, exist_ok=True)
            return user_config_dir
        else:
            # Se for um .exe portátil do Windows ou rodando de um pendrive
            return exe_dir
    else:
        # 3. Se for código fonte (.py) rodando solto no terminal
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_dir()

# Ajuste no DATA_DIR para não duplicar pastas 'data' nas versões instaladas
if os.environ.get("FLATPAK_ID") or BASE_DIR.endswith("backup_facil_pro"): 
    DATA_DIR = BASE_DIR
else:
    # Se for código fonte ou portátil, cria a subpasta 'data'
    DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

# Aponta os ficheiros para o diretório correto
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")
BACKUP_HISTORY_FILE = os.path.join(DATA_DIR, "backup_history.json")
INCREMENTAL_DB_FILE = os.path.join(DATA_DIR, "incremental_db.db")

# ✅ Fechaduras de Segurança (Thread Safety) para evitar colisões
history_lock = threading.Lock()
config_lock = threading.Lock()

def expand_path(path):
    if not path: return ""
    if isinstance(path, list): return [expand_path(p) for p in path]
    path = path.strip()
    if path.startswith("~") or path.startswith("/home") or (len(path) > 1 and path[1] == ":"):
        return os.path.expanduser(path)
    return path

def normalize_path_separator(path):
    if not path: return path
    return path.replace("\\", "/")

# ==================== CONTROLO DE PAUSA E CANCELAMENTO ====================
backup_pause_event = threading.Event()
backup_pause_event.set()
backup_abort_event = threading.Event()

class BackupCancelledException(Exception): pass

def toggle_pause_backup():
    if backup_pause_event.is_set():
        backup_pause_event.clear()
        return True
    else:
        backup_pause_event.set()
        return False

def abort_backup():
    backup_abort_event.set()
    backup_pause_event.set() 

# ==================== GESTÃO DE PERFIS (COM KEYRING) ====================
def save_profiles(profiles):
    try:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Erro ao salvar perfis: {e}")

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as pf:
                data = json.load(pf)
                for key in data:
                    if "config" in data[key]:
                        cfg = data[key]["config"]
                        if "origin" in cfg: cfg["origin"] = expand_path(cfg["origin"])
                        if "destination" in cfg: cfg["destination"] = expand_path(cfg["destination"])
                        if "folder_exclusions" in cfg and isinstance(cfg["folder_exclusions"], str):
                            cfg["folder_exclusions"] = [f.strip() for f in cfg["folder_exclusions"].split(',') if f.strip()]
                return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Erro ao ler perfis: {e}")
    return {"default": {"name": "Padrão", "config": {}}}

def contract_path(path):
    if not path: return ""
    if isinstance(path, list): return [contract_path(p) for p in path]
    home = os.path.expanduser("~")
    if path.startswith(home): return path.replace(home, "~", 1)
    return path

def save_config(data, profile_name="default"):
    with config_lock:
        data_to_save = data.copy()
        
        password = data_to_save.pop("password", None)
        
        if "origin" in data_to_save: data_to_save["origin"] = contract_path(data_to_save["origin"])
        if "destination" in data_to_save: data_to_save["destination"] = contract_path(data_to_save["destination"])
        
        profiles = load_profiles()
        profiles[profile_name] = {"name": profile_name, "config": data_to_save}
        save_profiles(profiles)
        
        if password:
            try:
                keyring.set_password("backup_facil_pro", profile_name, password)
            except (keyring.errors.KeyringError, OSError) as e:
                logger.warning(f"Erro ao salvar senha no keyring: {e}")
        else:
            try:
                keyring.delete_password("backup_facil_pro", profile_name)
            except (keyring.errors.KeyringError, OSError) as e:
                logger.warning(f"Erro ao deletar senha do keyring: {e}")
        
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Erro ao salvar config.json: {e}")

def load_config(profile_name=None):
    with config_lock:
        prof_name = profile_name if profile_name else "default"
        config = {}
        if profile_name:
            profiles = load_profiles()
            if profile_name in profiles: config = profiles[profile_name].get("config", {})
        elif os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: 
                    config = json.load(f)
                    if "origin" in config: config["origin"] = expand_path(config["origin"])
                    if "destination" in config: config["destination"] = expand_path(config["destination"])
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Erro ao ler config.json: {e}")
            
        try:
            pwd = keyring.get_password("backup_facil_pro", prof_name)
            if pwd: config["password"] = pwd
        except (keyring.errors.KeyringError, OSError) as e:
            logger.warning(f"Erro ao ler senha do keyring: {e}")
        
        return config

# ==================== HISTÓRICO E DB INCREMENTAL ====================
def save_backup_history(archive_path, stats):
    with history_lock:
        history = load_backup_history_nolock()
        history.append({
            "timestamp": datetime.now().isoformat(), "archive": os.path.basename(archive_path),
            "path": archive_path, "size": stats.get("size", 0), "files": stats.get("files", 0),
            "status": stats.get("status", "unknown"), "duration": stats.get("duration", 0),
            "type": stats.get("type", "completo")
        })
        history = history[-100:]
        try:
            with open(BACKUP_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
        except OSError as e:
            logger.error(f"Erro ao salvar histórico: {e}")

def load_backup_history_nolock():
    if os.path.exists(BACKUP_HISTORY_FILE):
        try:
            with open(BACKUP_HISTORY_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except (json.JSONDecodeError, OSError): pass
    return []

def load_backup_history():
    with history_lock:
        return load_backup_history_nolock()

def clear_backup_history():
    with history_lock:
        try:
            with open(BACKUP_HISTORY_FILE, 'w', encoding='utf-8') as f: json.dump([], f)
            return True
        except OSError: return False

def delete_backup_history_entry(index):
    with history_lock:
        try:
            history = load_backup_history_nolock()
            if 0 <= index < len(history):
                del history[index]
                with open(BACKUP_HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=4, ensure_ascii=False)
                return True
        except (OSError, IndexError): return False

def init_incremental_db():
    conn = sqlite3.connect(INCREMENTAL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS arquivos (chave TEXT PRIMARY KEY, hash TEXT, mtime REAL, backup_date TEXT)''')
    conn.commit()
    return conn

def get_file_hash(filepath):
    try:
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf); buf = f.read(65536)
        return hasher.hexdigest()
    except (OSError, IOError): return None

# ==================== FILTROS AVANÇADOS E REGEX ====================
def is_excluded(filename, exclusions_list):
    if not exclusions_list: return False
    for exc in exclusions_list:
        if not exc: continue
        if exc.startswith('.') and filename.lower().endswith(exc.lower()):
            return True
        try:
            if re.search(exc, filename, re.IGNORECASE):
                return True
        except re.error:
            if exc.lower() in filename.lower():
                return True
    return False

def passes_advanced_filters(filepath, filters):
    if not filters: return True
    try:
        stat = os.stat(filepath)
        file_size = stat.st_size
        file_mtime = stat.st_mtime
        if "min_size" in filters and file_size < filters["min_size"]: return False
        if "max_size" in filters and file_size > filters["max_size"]: return False
        if "min_date" in filters and file_mtime < datetime.strptime(filters["min_date"], "%Y-%m-%d").timestamp(): return False
        if "max_date" in filters and file_mtime > datetime.strptime(filters["max_date"], "%Y-%m-%d").timestamp(): return False
        return True
    except (OSError, ValueError): return True

def get_files_to_backup_incremental(origins, exclusions=[], filters={}, folder_exclusions=[]):
    conn = init_incremental_db()
    cursor = conn.cursor()
    files_to_backup = []
    folder_ignore = [f.strip().lower() for f in folder_exclusions if f.strip()]
    
    for origin in origins:
        try:
            for root, dirs, files in os.walk(origin):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in folder_ignore]
                for file in files:
                    if file.startswith('.'): continue
                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, origin)
                    
                    if not passes_advanced_filters(src_file, filters): continue
                    if is_excluded(file, exclusions): continue 
                    
                    current_hash = get_file_hash(src_file)
                    current_mtime = os.path.getmtime(src_file)
                    key = f"{origin}|{rel_path}"
                    cursor.execute("SELECT hash FROM arquivos WHERE chave = ?", (key,))
                    result = cursor.fetchone()
                    
                    if not result or result[0] != current_hash:
                        files_to_backup.append({"path": src_file, "rel_path": rel_path, "origin": origin, "size": os.path.getsize(src_file), "mtime": current_mtime, "hash": current_hash})
        except OSError as e:
            logger.warning(f"Erro ao acessar origem '{origin}': {e}")
    conn.close()
    return files_to_backup

def count_files(origins, exclusions=[], filters={}, folder_exclusions=[]):
    total = 0
    folder_ignore = [f.strip().lower() for f in folder_exclusions if f.strip()]
    for origin in origins:
        try:
            for root, dirs, files in os.walk(origin):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in folder_ignore]
                for file in files:
                    if file.startswith('.'): continue
                    src_file = os.path.join(root, file)
                    if passes_advanced_filters(src_file, filters):
                        if not is_excluded(file, exclusions): 
                            total += 1
        except OSError as e:
            logger.warning(f"Erro ao contar arquivos em '{origin}': {e}")
    return total

# ==================== UTILITÁRIOS ====================
def get_disk_space(path, timeout=2.0):
    result = {"total": 0, "used": 0, "free": 0, "percent_used": 0, "success": False}
    def _check_disk():
        try:
            total, used, free = shutil.disk_usage(path)
            result.update({"total": total, "used": used, "free": free, "percent_used": (used / total) * 100, "success": True})
        except (OSError, ZeroDivisionError) as e:
            logger.warning(f"Erro ao verificar espaço em disco '{path}': {e}")
    t = threading.Thread(target=_check_disk, daemon=True)
    t.start(); t.join(timeout)
    return result

def check_disk_space_warning(path, threshold=90):
    space = get_disk_space(path)
    if space["success"] and space["percent_used"] > threshold: return True, space
    return False, space

def verify_backup_integrity(archive_path, password=None):
    try:
        pwd = password if (password and password.strip()) else None
        with py7zr.SevenZipFile(archive_path, mode='r', password=pwd) as z: z.test()
        return True, "Integridade verificada com sucesso!"
    except Exception as e: return False, f"Falha na verificação: {str(e)}"

def cleanup_old_backups(target, max_backups=5, log_callback=None):
    try:
        if not os.path.exists(target) or max_backups <= 0: return 0
        backups = sorted([f for f in os.listdir(target) if f.startswith("Backup_") and f.endswith(".7z")])
        removed_count = 0
        while len(backups) > max_backups:
            old_backup = backups.pop(0)
            os.remove(os.path.join(target, old_backup))
            removed_count += 1
            if log_callback: log_callback(f"Backup antigo removido: {old_backup}")
        return removed_count
    except Exception as e: return 0

def compare_backups(archive1, archive2, password1=None, password2=None):
    try:
        pwd1 = password1 if (password1 and password1.strip()) else None
        pwd2 = password2 if (password2 and password2.strip()) else None
        with py7zr.SevenZipFile(archive1, mode='r', password=pwd1) as z1: files1 = set(z1.getnames())
        with py7zr.SevenZipFile(archive2, mode='r', password=pwd2) as z2: files2 = set(z2.getnames())
        
        only_in_1 = files1 - files2
        only_in_2 = files2 - files1
        common = files1 & files2
        return {"total_1": len(files1), "total_2": len(files2), "only_in_first": list(only_in_1), "only_in_second": list(only_in_2), "common": len(common), "different": len(only_in_1) + len(only_in_2)}
    
    except py7zr.exceptions.PasswordRequired: 
        return {"error": "VOCÊ NÃO ADICIONOU A SENHA! Um (ou ambos) os arquivos selecionados são criptografados."}
    
    except py7zr.exceptions.CrcError: 
        return {"error": "SENHA INCORRETA! Ou o arquivo de backup está corrompido."}
    
    except Exception as e: 
        return {"error": f"Erro inesperado: {str(e)}"}

# ==================== BACKUP PRINCIPAL ====================
def start_backup_process(origins, target, compression_level="Normal", password=None, 
                         exclusions="", retention=5, progress_callback=None, 
                         ui_log_callback=None, speed_callback=None, incremental=False, filters={}, folder_exclusions=[],
                         volume_size="0"):
    start_time = time.time()
    backup_pause_event.set(); backup_abort_event.clear() 
    
    if not origins: return "Erro: Nenhuma pasta selecionada.", False, {}
    try: os.makedirs(target, exist_ok=True)
    except Exception as e: return f"Erro no destino: {e}", False, {}
    
    space_warning, space_info = check_disk_space_warning(target, 90)
    if space_warning and ui_log_callback: ui_log_callback(f"⚠️ ALERTA: Espaço em disco crítico ({space_info['percent_used']:.1f}% usado)")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_type = "incremental" if incremental else "completo"
    archive_name = f"Backup_{backup_type}_{timestamp}.7z"
    full_dest_path = os.path.join(target, archive_name)

    # ---------------------------------------------------------
    # 💓 NOVO: MONITOR CARDÍACO DE VELOCIDADE (THREAD PARALELA)
    # ---------------------------------------------------------
    monitor_running = [True]
    def speed_monitor():
        last_size = 0
        while monitor_running[0]:
            time.sleep(1)
            if not backup_pause_event.is_set():
                if speed_callback: speed_callback("⏸️ Pausado")
                continue
            try:
                if os.path.exists(full_dest_path):
                    current_size = os.path.getsize(full_dest_path)
                    delta = current_size - last_size
                    last_size = current_size
                    
                    if speed_callback:
                        if backup_abort_event.is_set():
                            speed_callback("🛑 Abortando... Aguardando arquivo atual.")
                        elif delta > 0:
                            speed_mb = delta / (1024 * 1024)
                            speed_callback(f"⚡ Gravando: {speed_mb:.1f} MB/s")
                        else:
                            speed_callback("⚙️ Processando...")
            except OSError:
                pass

    # Inicia o monitor em segundo plano
    monitor_thread = threading.Thread(target=speed_monitor, daemon=True)
    monitor_thread.start()
    # ---------------------------------------------------------

    exclude_list = [ext.strip() for ext in exclusions.split(',') if ext.strip()] if exclusions else []
    folder_ignore = [f.strip().lower() for f in folder_exclusions if f.strip()]
    presets = {"Armazenar": 0, "Rápido": 1, "Normal": 3, "Máximo": 9}
    
    if incremental:
        files_to_backup = get_files_to_backup_incremental(origins, exclude_list, filters, folder_ignore)
        total_files = len(files_to_backup)
    else:
        total_files = count_files(origins, exclude_list, filters, folder_ignore)
        files_to_backup = None
    
    files_processed = 0

    try:
        filters_compression = [{'id': py7zr.FILTER_LZMA2, 'preset': presets.get(compression_level, 3)}]
        pwd = password if (password and password.strip()) else None

        vol = volume_size.strip().lower() if volume_size else "0"
        use_volumes = vol not in ("0", "")

        if use_volumes:
            archive_obj = py7zr.SevenZipFile(target, 'w', filters=filters_compression, password=pwd, volume=vol)
            archive_name = f"Backup_{backup_type}_{timestamp}"
        else:
            archive_obj = py7zr.SevenZipFile(full_dest_path, 'w', filters=filters_compression, password=pwd)

        with archive_obj as archive:
            if pwd and not use_volumes: archive.header_encryption = True
            
            if incremental and files_to_backup:
                total = len(files_to_backup)
                for i, file_info in enumerate(files_to_backup):
                    backup_pause_event.wait() 
                    if backup_abort_event.is_set(): raise BackupCancelledException("Backup abortado.")
                    if os.path.abspath(file_info["path"]) == os.path.abspath(full_dest_path): continue
                    if os.path.islink(file_info["path"]) or not os.path.isfile(file_info["path"]): continue

                    try:
                        if progress_callback: progress_callback(int(((i + 1) / total) * 100))
                        if ui_log_callback: ui_log_callback(f"Comprimindo: {file_info['rel_path']}")
                        archive.write(file_info["path"], file_info["rel_path"])
                        files_processed += 1
                    except Exception as fe: continue
            else:
                for origin in origins:
                    folder_name = os.path.basename(origin)
                    for root, dirs, files in os.walk(origin):
                        backup_pause_event.wait() 
                        if backup_abort_event.is_set(): raise BackupCancelledException("Backup abortado.")
                        dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in folder_ignore]
                        
                        for file in files:
                            backup_pause_event.wait()
                            if backup_abort_event.is_set(): raise BackupCancelledException("Backup abortado pelo usuário.")
                            if file.startswith('.'): continue
                            
                            src_file = os.path.join(root, file)
                            if not passes_advanced_filters(src_file, filters): continue
                            if is_excluded(file, exclude_list): continue 
                            if os.path.abspath(src_file) == os.path.abspath(full_dest_path): continue
                            if os.path.islink(src_file) or not os.path.isfile(src_file): continue

                            try:
                                if ui_log_callback: ui_log_callback(f"Comprimindo: {os.path.relpath(src_file, origin)}")
                                archive.write(src_file, os.path.join(folder_name, os.path.relpath(src_file, origin)))
                                files_processed += 1
                            except Exception as fe: continue
                            
        integrity_ok, integrity_msg = verify_backup_integrity(full_dest_path, pwd)
        if not integrity_ok:
            if os.path.exists(full_dest_path): os.remove(full_dest_path)
            monitor_running[0] = False # Desliga o monitor em caso de erro
            return f"Erro: {integrity_msg}", False, {}
        
        if retention > 0: cleanup_old_backups(target, retention, ui_log_callback)
        
        stats = {"size": os.path.getsize(full_dest_path), "files": files_processed, "status": "success", "duration": time.time() - start_time, "type": backup_type}
        save_backup_history(full_dest_path, stats)
        
        if incremental and files_to_backup:
            conn = init_incremental_db()
            cursor = conn.cursor()
            for file_info in files_to_backup:
                key = f"{file_info['origin']}|{file_info['rel_path']}"
                cursor.execute('''INSERT OR REPLACE INTO arquivos (chave, hash, mtime, backup_date) VALUES (?, ?, ?, ?)''', (key, file_info["hash"], file_info["mtime"], timestamp))
            conn.commit()
            conn.close()
        
        try: notification.notify(title="Backup Fácil Pro", message=f"Backup concluído:\n{archive_name}", timeout=5)
        except Exception as e:
            logger.warning(f"Erro ao enviar notificação: {e}")
            
        monitor_running[0] = False # Desliga o monitor no sucesso
        if speed_callback: speed_callback("") # Limpa a tela
        return f"Sucesso: {archive_name} criado.", True, stats

    except BackupCancelledException as e:
        monitor_running[0] = False
        if speed_callback: speed_callback("")
        if os.path.exists(full_dest_path):
            try: os.remove(full_dest_path)
            except OSError:
                logger.warning(f"Erro ao remover ficheiro após cancelamento: {full_dest_path}")
        return str(e), False, {}
    except Exception as e:
        monitor_running[0] = False
        if speed_callback: speed_callback("")
        if os.path.exists(full_dest_path):
            try: os.remove(full_dest_path)
            except OSError:
                logger.warning(f"Erro ao remover ficheiro após erro crítico: {full_dest_path}")
        return f"Erro Crítico: {str(e)}", False, {}

# ==================== RESTAURAÇÃO E AGENDADOR ====================
def restore_backup_process(archive_path, extract_to, password=None, log_callback=None):
    try:
        pwd = password if (password and password.strip()) else None
        with py7zr.SevenZipFile(archive_path, mode='r', password=pwd) as z: z.extractall(path=extract_to)
        return "Sucesso: Restauração concluída!", True
    except py7zr.exceptions.PasswordRequired: return "Erro: Senha incorreta ou não fornecida!", False
    except py7zr.exceptions.CrcError: return "Erro: Falha de CRC (Ficheiro corrompido ou senha incorreta).", False
    except Exception as e: return f"Erro: {str(e)}", False

scheduler_running = False
scheduler_thread = None

def start_scheduler(config):
    global scheduler_running, scheduler_thread
    schedule.clear()
    
    def job():
        start_backup_process(
            origins=config.get("origin", []), target=config.get("destination", ""),
            compression_level=config.get("compression", "Normal"), password=config.get("password"),
            retention=config.get("retention", 5), incremental=config.get("incremental", False),
            filters=config.get("filters", {}), folder_exclusions=config.get("folder_exclusions", []),
            exclusions=config.get("exclusions", ""), volume_size=config.get("volume_size", "0"),
            ui_log_callback=lambda msg: logger.info(f"[Scheduler] {msg}")
        )

    freq = config.get("frequency", "Diário")
    horario = config.get("time", "03:00").strip()
    if len(horario) == 4 and horario[1] == ':': horario = "0" + horario
    
    try:
        if freq == "Diário":
            schedule.every().day.at(horario).do(job)
        elif freq == "Semanal":
            schedule.every().monday.at(horario).do(job)
        elif freq == "A cada 4 horas":
            schedule.every(4).hours.do(job)
        elif freq == "A cada 12 horas":
            schedule.every(12).hours.do(job)
    except (ValueError, TypeError) as e:
        logger.error(f"Erro ao configurar agendamento ({freq} {horario}): {e}")

    if not scheduler_running:
        scheduler_running = True
        def loop():
            while scheduler_running:
                schedule.run_pending()
                time.sleep(1)
        scheduler_thread = threading.Thread(target=loop, daemon=True)
        scheduler_thread.start()

def stop_scheduler():
    global scheduler_running
    scheduler_running = False
    schedule.clear()

def get_dashboard_data():
    history = load_backup_history()
    total_backups = len(history)
    successful = len([h for h in history if h.get("status") == "success"])
    return {
        "total_backups": total_backups, "successful": successful, "failed": total_backups - successful,
        "success_rate": (successful / total_backups * 100) if total_backups > 0 else 0,
        "last_backup": history[-1] if history else None,
        "total_size": sum(h.get("size", 0) for h in history),
        "total_files": sum(h.get("files", 0) for h in history),
        "recent_backups": history[-10:] if history else []
    }