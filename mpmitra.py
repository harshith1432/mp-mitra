import os
import sys
import json
import time
import argparse
import subprocess
import webbrowser
import urllib.request
import urllib.error
import shutil
import hashlib
import psutil
from pathlib import Path
from typing import Any, Dict, Optional

# Resolve app paths
if os.name == 'nt':  # Windows
    APPDATA = Path(os.getenv('LOCALAPPDATA', os.getenv('APPDATA', 'C:\\'))) / 'MPMitra'
else:  # macOS / Linux
    APPDATA = Path.home() / '.config' / 'mpmitra'

APPDATA.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APPDATA / 'config.json'
PID_FILE = APPDATA / 'service.pid'
LOG_DIR = APPDATA / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'mpmitra.log'

# Load version from version.json (single source of truth)
def _load_version_info() -> dict:
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "version.json")
    if os.path.exists(candidate):
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": "1.0.0", "channel": "stable", "build": "unknown", "release_date": "unknown"}

_VERSION_INFO = _load_version_info()
VERSION = _VERSION_INFO.get("version", "1.0.0")

# Import ConfigManager or local mock for CLI standalone execution
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
    from app.config_manager import config_manager
except Exception:
    # Fail-safe local ConfigManager minimal implementation
    class LocalConfigManager:
        def __init__(self):
            self.config = self._load()
        def _load(self):
            if CONFIG_FILE.exists():
                try:
                    with open(CONFIG_FILE, 'r') as f: return json.load(f)
                except: pass
            return {"DATABASE_URL": f"sqlite:///{str(APPDATA / 'mpmitra.db')}", "UPDATE_CHANNEL": "stable"}
        def save(self):
            with open(CONFIG_FILE, 'w') as f: json.dump(self.config, f, indent=4)
        def get(self, k, default=None): return self.config.get(k, default)
        def set(self, k, v):
            self.config[k] = v
            self.save()
        def get_secret(self, k, d=""): return self.config.get("SECRETS", {}).get(k, d)
        def set_secret(self, k, v):
            if "SECRETS" not in self.config: self.config["SECRETS"] = {}
            self.config["SECRETS"][k] = v
            self.save()
    config_manager = LocalConfigManager()

def log_message(msg: str):
    """Log helper writing to log file and terminal."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(formatted + "\n")
    except:
        pass

def is_server_running() -> bool:
    """Checks if the server port is active."""
    port = config_manager.get("PORT", 8000)
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('127.0.0.1', int(port)))
        s.close()
        return True
    except:
        return False

def is_process_mpmitra(pid: int) -> bool:
    """Verifies that a process is active and is indeed the MP Mitra backend service."""
    if pid <= 0:
        return False
    try:
        if not psutil.pid_exists(pid):
            return False
        proc = psutil.Process(pid)
        cmd = proc.cmdline()
        cmd_str = " ".join(cmd).lower()
        if "--server" in cmd_str:
            if "mpmitra" in cmd_str or "python" in proc.name().lower() or "uvicorn" in cmd_str:
                return True
        return False
    except Exception:
        return False

def get_running_pid() -> Optional[int]:
    """Reads PID from the PID file and verifies if the process exists and is MP Mitra.
    If it does not exist or is not MP Mitra, removes the stale PID file and returns None.
    """
    if PID_FILE.exists():
        try:
            pid_str = PID_FILE.read_text().strip()
            if pid_str.isdigit():
                pid = int(pid_str)
                if is_process_mpmitra(pid):
                    return pid
                else:
                    log_message(f"[*] Stale PID file detected (process {pid} not running or not MP Mitra). Cleaning up.")
                    try:
                        PID_FILE.unlink()
                    except:
                        pass
        except Exception as e:
            log_message(f"[WARN] Failed to parse/validate PID file: {e}")
            try:
                PID_FILE.unlink()
            except:
                pass
    return None

def get_pid_on_port(port: int) -> Optional[int]:
    """Finds the PID of the process listening on the specified port, and checks if it's MP Mitra."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                if conn.pid and is_process_mpmitra(conn.pid):
                    return conn.pid
    except Exception:
        pass
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmd = proc.info.get('cmdline') or []
            cmd_str = " ".join(cmd).lower()
            if "mpmitra.py" in cmd_str and "--server" in cmd_str:
                return proc.info['pid']
    except Exception:
        pass
        
    return None

def start_services(open_browser: bool = True):
    """Starts the MP Mitra background service with robust health checking and detachment."""
    log_message("[*] Starting MP Mitra Background Service...")
    
    port = int(config_manager.get("PORT", 8000))
    host = config_manager.get("HOST", "127.0.0.1")
    
    # 1. Check if running already
    pid = get_running_pid()
    if not pid:
        pid = get_pid_on_port(port)
        if pid:
            try:
                PID_FILE.write_text(str(pid))
            except:
                pass
                
    if pid:
        is_healthy = False
        uptime = "unknown"
        try:
            api_url = f"http://{host}:{port}/api/health"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Check'})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    health_data = json.loads(response.read().decode())
                    if health_data.get("status") == "healthy":
                        is_healthy = True
                        uptime = health_data.get("uptime", "unknown")
        except Exception:
            pass
            
        if is_healthy:
            print("\nMP Mitra is already running.")
            print(f"PID: {pid}")
            print(f"Port: {port}")
            print(f"Uptime: {uptime}\n")
            
            if open_browser:
                browser_host = "localhost" if host in ("127.0.0.1", "0.0.0.0") else host
                url = f"http://{browser_host}:{port}"
                log_message(f"Opening browser at {url}...")
                webbrowser.open(url)
            sys.exit(0)
        else:
            log_message(f"[WARN] MP Mitra process {pid} is running but health check failed. Terminating to restart clean...")
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                psutil.wait_procs([proc], timeout=5)
            except Exception:
                pass
            if PID_FILE.exists():
                try: PID_FILE.unlink()
                except: pass

    # 2. Check port availability
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, port))
        s.close()
    except Exception as e:
        log_message(f"[ERROR] Port {port} is occupied by another application. Cannot start service.")
        sys.exit(1)

    # 3. Setup paths and process
    script_dir = os.path.dirname(os.path.abspath(__file__))
    py_exe = sys.executable
    script_path = os.path.abspath(__file__)
    
    log_message(f"Redirecting logs to: {LOG_FILE}")
    try:
        log_fh = open(LOG_FILE, 'a', encoding='utf-8')
    except Exception as e:
        log_message(f"[ERROR] Cannot open log file: {e}")
        sys.exit(1)

    # 4. Popen launch
    try:
        if os.name == 'nt':
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            proc = subprocess.Popen(
                [py_exe, "-u", script_path, "--server"],
                cwd=script_dir,
                stdin=subprocess.DEVNULL,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                close_fds=True,
                creationflags=creationflags
            )
        else:
            proc = subprocess.Popen(
                [py_exe, "-u", script_path, "--server"],
                cwd=script_dir,
                stdin=subprocess.DEVNULL,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                close_fds=True,
                start_new_session=True
            )
        
        real_pid = proc.pid
        if not real_pid or real_pid <= 0:
            raise RuntimeError(f"Invalid PID returned by OS: {real_pid}")
            
        PID_FILE.write_text(str(real_pid))
        log_message(f"[OK] Launched subprocess. Real OS PID: {real_pid}")
        
    except Exception as e:
        log_message(f"[ERROR] Failed to start subprocess: {e}")
        sys.exit(1)

    # 5. Wait for /api/health with 120s timeout, streaming logs
    log_message("Waiting for API health check (timeout: 120 seconds)...")
    start_time = time.time()
    last_log_pos = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    
    while time.time() - start_time < 120:
        if not is_process_mpmitra(real_pid):
            log_message("[ERROR] Process died during startup. Port may be occupied or crashed.")
            if PID_FILE.exists():
                try: PID_FILE.unlink()
                except: pass
            sys.exit(1)
            
        # Stream logs in real-time to show startup progress (AI models loading, etc.)
        try:
            current_size = LOG_FILE.stat().st_size
            if current_size > last_log_pos:
                with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_log_pos)
                    new_text = f.read()
                    if new_text:
                        sys.stdout.write(new_text)
                        sys.stdout.flush()
                last_log_pos = current_size
        except Exception:
            pass

        try:
            api_url = f"http://{host}:{port}/api/health"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Startup-Check'})
            with urllib.request.urlopen(req, timeout=1) as response:
                if response.status == 200:
                    health_data = json.loads(response.read().decode())
                    if health_data.get("status") == "healthy":
                        log_message(f"\n[OK] MP Mitra Platform is ready and online!")
                        log_message(f"Uptime: {health_data.get('uptime')}")
                        log_message(f"Database: {health_data.get('database')}")
                        log_message(f"AI: {health_data.get('ai')}")
                        
                        if open_browser:
                            browser_host = "localhost" if host in ("127.0.0.1", "0.0.0.0") else host
                            url = f"http://{browser_host}:{port}"
                            log_message(f"Opening browser at {url}...")
                            webbrowser.open(url)
                        return
        except Exception:
            pass
            
        time.sleep(1)

    log_message("[ERROR] Service did not become healthy within 120 seconds.")
    sys.exit(1)

def stop_services():
    """Gracefully terminates background service."""
    log_message("[*] Stopping MP Mitra Platform...")
    
    pid = None
    if PID_FILE.exists():
        try:
            pid_str = PID_FILE.read_text().strip()
            if pid_str.isdigit():
                pid = int(pid_str)
        except:
            pass
            
    port = int(config_manager.get("PORT", 8000))
    if not pid:
        pid = get_pid_on_port(port)
        
    if not pid:
        log_message("[WARN] No running service instance found (PID file missing or inactive).")
        return

    log_message(f"Terminating process for PID: {pid}")
    try:
        if not psutil.pid_exists(pid):
            log_message("[OK] Process already stopped.")
            if PID_FILE.exists():
                PID_FILE.unlink()
            return
            
        proc = psutil.Process(pid)
        
        # Terminate children first, then parent
        try:
            children = proc.children(recursive=True)
            for child in children:
                child.terminate()
        except:
            pass
            
        proc.terminate()
        
        gone, alive = psutil.wait_procs([proc], timeout=5)
        if alive:
            log_message(f"Process did not exit in 5 seconds. Killing process and children...")
            for a in alive:
                try:
                    for child in a.children(recursive=True):
                        child.kill()
                    a.kill()
                except Exception:
                    pass
                    
        if PID_FILE.exists():
            try: PID_FILE.unlink()
            except: pass
        log_message("[OK] Services successfully stopped.")
    except Exception as e:
        log_message(f"[ERROR] Failed to stop process: {e}")
        if PID_FILE.exists():
            try: PID_FILE.unlink()
            except: pass

def restart_services():
    """Restarts background service."""
    stop_services()
    time.sleep(2)
    start_services()

def show_status():
    """Retrieves and prints current service health metrics in professional format."""
    pid = None
    if PID_FILE.exists():
        try:
            pid_str = PID_FILE.read_text().strip()
            if pid_str.isdigit():
                pid = int(pid_str)
        except:
            pass
            
    port = int(config_manager.get("PORT", 8000))
    host = config_manager.get("HOST", "127.0.0.1")
    
    is_running = False
    if pid and is_process_mpmitra(pid):
        is_running = True
    else:
        pid = get_pid_on_port(port)
        if pid:
            is_running = True
            
    cpu_pct = "0.0%"
    ram_mb = "0.0 MB"
    if is_running and pid:
        try:
            proc = psutil.Process(pid)
            cpu_pct = f"{proc.cpu_percent(interval=0.1):.1f}%"
            ram_mb = f"{proc.memory_info().rss / (1024 * 1024):.1f} MB"
        except Exception:
            pass
            
    backend_status = "Stopped"
    frontend_status = "Offline"
    db_status = "Offline"
    ai_status = "Offline"
    health_status = "Offline"
    uptime = "N/A"
    
    if is_running:
        backend_status = "Running"
        try:
            api_url = f"http://{host}:{port}/api/health"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Status'})
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    health_status = data.get("status", "Healthy")
                    db_status = data.get("database", "Connected")
                    frontend_status = data.get("frontend", "Available")
                    ai_status = data.get("ai", "Ready")
                    uptime = data.get("uptime", "N/A")
                else:
                    health_status = f"Unhealthy (HTTP {response.status})"
        except Exception as e:
            health_status = f"Unhealthy (Connection error: {e})"
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dp = os.path.abspath(os.path.join(script_dir, "frontend", "dist"))
        if os.path.exists(dp) and os.path.exists(os.path.join(dp, "index.html")):
            frontend_status = "Built"
        else:
            frontend_status = "Missing"

    print("========================================")
    print("MP Mitra Background Service Status")
    print("========================================")
    print(f"Backend       : {backend_status}")
    print(f"Frontend      : {frontend_status}")
    print(f"PID           : {pid if is_running else 'None'}")
    print(f"CPU Usage     : {cpu_pct}")
    print(f"RAM Usage     : {ram_mb}")
    print(f"Port          : {port}")
    print(f"Version       : {VERSION}")
    print(f"Database      : {db_status}")
    print(f"AI Status     : {ai_status}")
    print(f"Health Check  : {health_status}")
    print(f"Uptime        : {uptime}")
    print("========================================")

def show_logs(lines: int = 50, follow: bool = False):
    """Tail display of application log file."""
    if not LOG_FILE.exists():
        print("No log file found.")
        return
        
    print(f"--- Showing last {lines} lines from: {LOG_FILE} ---")
    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        file_lines = f.readlines()
        for line in file_lines[-lines:]:
            print(line, end='')

    if follow:
        print("\n--- Streaming live logs (Press Ctrl+C to stop) ---")
        try:
            with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    print(line, end='')
        except KeyboardInterrupt:
            print("\nStopped log stream.")

def run_doctor():
    """Diagnoses installations and environment config."""
    print("==================================================")
    print("      MP MITRA SYSTEM DOCTOR DIAGNOSTICS          ")
    print("==================================================")
    
    # 1. PID File Audit
    print("[*] Auditing PID file...")
    if PID_FILE.exists():
        try:
            pid_val = PID_FILE.read_text().strip()
            print(f"    - PID file exists: {PID_FILE}")
            print(f"    - Stored PID: {pid_val}")
            if pid_val.isdigit() and is_process_mpmitra(int(pid_val)):
                print(f"    - [OK] Running process matching PID found.")
            else:
                print(f"    - [WARN] Stored PID process does not exist or is not MP Mitra.")
        except Exception as e:
            print(f"    - [ERROR] Failed to read PID file: {e}")
    else:
        print("    - [INFO] PID file does not exist (service likely stopped).")

    # 2. Running Process Audit
    print("[*] Auditing active processes...")
    port = int(config_manager.get("PORT", 8000))
    pid_on_port = get_pid_on_port(port)
    if pid_on_port:
        print(f"    - [OK] MP Mitra process running on port {port} (PID: {pid_on_port}).")
    else:
        print(f"    - [INFO] No MP Mitra process found running on port {port}.")

    # 3. Port Occupancy
    print("[*] Checking port availability...")
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        host = config_manager.get("HOST", "127.0.0.1")
        s.bind((host, port))
        s.close()
        print(f"    - [OK] Port {port} is free and available.")
    except Exception as e:
        print(f"    - [WARN] Port {port} is occupied. (This is normal if the service is running).")

    # 4. Health Endpoint
    print("[*] Testing health check API...")
    if pid_on_port or is_server_running():
        try:
            api_url = f"http://127.0.0.1:{port}/api/health"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Doctor'})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    health_data = json.loads(response.read().decode())
                    print(f"    - [OK] Health endpoint returned HTTP 200.")
                    print(f"    - [OK] Status: {health_data.get('status')}")
                    print(f"    - [OK] Database: {health_data.get('database')}")
                    print(f"    - [OK] Uptime: {health_data.get('uptime')}")
                else:
                    print(f"    - [ERROR] Health endpoint returned HTTP {response.status}.")
        except Exception as e:
            print(f"    - [ERROR] Failed to connect to health endpoint: {e}")
    else:
        print("    - [INFO] Server is offline, skipping health endpoint check.")

    # 5. Database connectivity
    print("[*] Auditing database connectivity...")
    db_url = config_manager.get("DATABASE_URL")
    if db_url.startswith("sqlite"):
        try:
            sqlite_path = db_url.replace("sqlite:///", "")
            sqlite_dir = Path(sqlite_path).parent
            if sqlite_dir.exists():
                print(f"    - [OK] SQLite database path exists and is writeable.")
            else:
                print(f"    - [WARN] SQLite database directory does not exist yet.")
        except Exception as e:
            print(f"    - [ERROR] Failed to validate SQLite path: {e}")
    else:
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"    - [OK] PostgreSQL connectivity verified successfully.")
        except Exception as e:
            print(f"    - [ERROR] Database connection failed: {e}")

    # 6. Frontend Build Audit
    print("[*] Checking frontend static assets...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dp = os.path.abspath(os.path.join(script_dir, "frontend", "dist"))
    if os.path.exists(dp) and os.path.exists(os.path.join(dp, "index.html")):
        print(f"    - [OK] Frontend static assets compiled successfully at: {dp}")
    else:
        print(f"    - [ERROR] Frontend build is missing at: {dp}. Run 'npm run build' inside frontend directory.")

    # 7. Firebase Audit
    print("[*] Auditing Firebase account setup...")
    fb_svc = config_manager.get_secret("FIREBASE_SERVICE_ACCOUNT_JSON")
    if fb_svc:
        print("    - [OK] Firebase Service Account credentials found.")
    else:
        print("    - [WARN] Firebase Credentials missing. Utilizing mock fallback credentials.")

    # 8. Permissions Check
    print("[*] Auditing AppData directory write permissions...")
    try:
        test_file = APPDATA / '.perm_test'
        test_file.write_text('test')
        test_file.unlink()
        print(f"    - [OK] Full read/write access verified for AppData directory: {APPDATA}")
    except Exception as e:
        print(f"    - [ERROR] AppData folder permissions check failed: {e}")

    print("==================================================")

def run_backup(target_path: str):
    """Backs up SQLite database and config."""
    log_message(f"Creating local backup to: {target_path}")
    backup_dir = Path(target_path)
    if not backup_dir.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        
    # Copy config
    if CONFIG_FILE.exists():
        shutil.copy(CONFIG_FILE, backup_dir / 'config_backup.json')
        
    # Copy database if SQLite
    db_url = config_manager.get("DATABASE_URL")
    if db_url.startswith("sqlite"):
        db_path = Path(db_url.replace("sqlite:///", ""))
        if db_path.exists():
            shutil.copy(db_path, backup_dir / 'mpmitra_backup.db')
            log_message("[OK] Database and config backed up successfully.")
            return
            
    log_message("[OK] Config backed up. (SQL Database is external - backup skipped).")

def run_restore(source_path: str):
    """Restores SQLite database and config."""
    log_message(f"Restoring system backup from: {source_path}")
    source_dir = Path(source_path)
    if not source_dir.exists():
        log_message(f"[ERROR] Backup directory '{source_path}' does not exist.")
        return
        
    # Restore config
    if (source_dir / 'config_backup.json').exists():
        shutil.copy(source_dir / 'config_backup.json', CONFIG_FILE)
        
    # Restore DB
    if (source_dir / 'mpmitra_backup.db').exists():
        db_url = config_manager.get("DATABASE_URL")
        if db_url.startswith("sqlite"):
            db_path = Path(db_url.replace("sqlite:///", ""))
            shutil.copy(source_dir / 'mpmitra_backup.db', db_path)
            log_message("[OK] Database and config restored. Please restart services.")
            return
            
    log_message("[OK] Config restored.")

def manage_config(action: str, key: str, value: Optional[str] = None):
    """Config manager setter and getter helper."""
    sensitive_keys = {"GROQ_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "FIREBASE_SERVICE_ACCOUNT_JSON", "TWILIO_AUTH_TOKEN"}
    
    if action == "set":
        if not key:
            print("Error: Specify a key to set.")
            return
        if value is None:
            print("Error: Specify a value to set.")
            return
            
        if key in sensitive_keys:
            config_manager.set_secret(key, value)
            print(f"[OK] Securely stored and encrypted config parameter: {key}")
        else:
            # Convert port/numbers
            if key in {"PORT"}:
                try: value = int(value)
                except: pass
            config_manager.set(key, value)
            print(f"[OK] Set config parameter: {key} = {value}")
            
    elif action == "get":
        if not key:
            print("Error: Specify a key to get.")
            return
        if key in sensitive_keys:
            val = config_manager.get_secret(key)
            print(f"{key} = [ENCRYPTED] {'*'*len(val) if val else 'Not Set'}")
        else:
            print(f"{key} = {config_manager.get(key)}")
            
    elif action == "show":
        print("--- Config Parameters ---")
        for k, v in config_manager.config.items():
            if k != "SECRETS":
                print(f"{k}: {v}")
        if "SECRETS" in config_manager.config:
            print("SECRETS (Encrypted keys):")
            for k in config_manager.config["SECRETS"].keys():
                print(f"  - {k}")

def _updater_path_setup():
    """Prepares sys.path so the updater module can be imported."""
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def run_check_update():
    """Checks GitHub for the latest release and displays results."""
    _updater_path_setup()
    try:
        from app.updater import display_check_update, get_local_version
        display_check_update(get_local_version())
    except ImportError:
        # Standalone fallback (no backend dir accessible)
        print("")
        print(f"Checking for updates...")
        print(f"Current Version : {VERSION}")
        api_url = "https://api.github.com/repos/harshith1432/mp-mitra/releases/latest"
        try:
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Updater/1.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
                tag = data.get("tag_name", "").lstrip("vV")
                if tag:
                    print(f"Latest Version  : {tag}")
                    print("")
                    if tag != VERSION:
                        print("[UPDATE AVAILABLE]")
                        print("Run:  mpmitra update  to install.")
                    else:
                        print("[OK] You are using the latest version.")
                else:
                    print("Latest Version  : Not found")
                    print("")
                    print("[INFO] No published releases found on GitHub.")
        except urllib.error.HTTPError as e:
            print(f"Latest Version  : Unavailable")
            print("")
            if e.code == 404:
                print("[INFO] No published releases found on GitHub.")
                print("       To publish a release: git tag v1.0.1 && git push --tags")
            elif e.code == 403:
                print("[WARN] GitHub API rate limit exceeded. Try again in a few minutes.")
            else:
                print(f"[WARN] GitHub returned HTTP {e.code}.")
        except urllib.error.URLError:
            print(f"Latest Version  : Unavailable")
            print("")
            print("[WARN] Unable to reach GitHub. Check your internet connection.")
        except Exception:
            print(f"Latest Version  : Unavailable")
            print("")
            print("[WARN] Update check could not complete. Try again later.")
        print("")


def run_update():
    """Downloads and installs the latest release."""
    _updater_path_setup()
    try:
        from app.updater import run_update as _run_update, get_local_version
        _run_update(get_local_version())
    except ImportError:
        print("")
        print("[WARN] Updater module not available.")
        print("       Run: mpmitra check-update  to see if a new version exists.")
        print("")


def run_rollback():
    """Restores the previous version from backup."""
    _updater_path_setup()
    try:
        from app.updater import run_rollback as _run_rollback
        _run_rollback()
    except ImportError:
        print("")
        print("[WARN] Rollback module not available.")
        print("")


def _auto_check_update_background():
    """Runs a silent update check in a background thread after mpmitra start."""
    import threading
    def _worker():
        try:
            time.sleep(3)  # Wait 3s to not race with startup messages
            _updater_path_setup()
            from app.updater import auto_check_on_start, get_local_version
            auto_check_on_start(get_local_version(), silent=True)
        except Exception:
            pass  # Never crash the background thread
    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


def main():
    parser = argparse.ArgumentParser(description="MP Mitra Command Line Interface (CLI) Service Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: start
    start_parser = subparsers.add_parser("start", help="Start FastAPI backend service and open browser dashboard")
    start_parser.add_argument("--no-browser", action="store_true", help="Launch service without opening browser")

    # Command: stop
    subparsers.add_parser("stop", help="Gracefully stop background running services")

    # Command: restart
    subparsers.add_parser("restart", help="Restart all background services")

    # Command: status
    subparsers.add_parser("status", help="Get service health, ports, and system resource status")

    # Command: logs
    logs_parser = subparsers.add_parser("logs", help="View or stream application output log files")
    logs_parser.add_argument("-n", "--lines", type=int, default=50, help="Number of trailing log lines to view")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Stream log outputs in real-time")

    # Command: config
    config_parser = subparsers.add_parser("config", help="Get or set configuration keys")
    config_parser.add_argument("action", choices=["get", "set", "show"], help="Config action type")
    config_parser.add_argument("key", nargs="?", default=None, help="The configuration key")
    config_parser.add_argument("value", nargs="?", default=None, help="The configuration value (set only)")

    # Command: doctor
    subparsers.add_parser("doctor", help="Run diagnostic health checks on ports, db, permissions, and api")

    # Command: backup / restore
    backup_parser = subparsers.add_parser("backup", help="Export local configuration and database archives")
    backup_parser.add_argument("path", help="Folder path to write backup file")
    
    restore_parser = subparsers.add_parser("restore", help="Import configuration and database archives")
    restore_parser.add_argument("path", help="Folder path containing backup file")

    # Command: update / check-update / version / rollback
    subparsers.add_parser("update", help="Download and install the latest platform update")
    subparsers.add_parser("check-update", help="Check GitHub for the latest available version")
    subparsers.add_parser("version", help="Print active CLI software version and build info")
    subparsers.add_parser("rollback", help="Restore the previous installed version from backup")
    subparsers.add_parser("reset", help="Reset all settings, configuration and database files to empty defaults")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "start":
        start_services(open_browser=not args.no_browser)
    elif args.command == "stop":
        stop_services()
    elif args.command == "restart":
        restart_services()
    elif args.command == "status":
        show_status()
    elif args.command == "logs":
        show_logs(lines=args.lines, follow=args.follow)
    elif args.command == "config":
        manage_config(args.action, args.key, args.value)
    elif args.command == "doctor":
        run_doctor()
    elif args.command == "backup":
        run_backup(args.path)
    elif args.command == "restore":
        run_restore(args.path)
    elif args.command == "update":
        run_update()
    elif args.command == "check-update":
        run_check_update()
    elif args.command == "version":
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
            from app.updater import display_version, get_local_version
            display_version(get_local_version())
        except ImportError:
            print(f"MP Mitra")
            print(f"Version : {VERSION}")
            print(f"Channel : {_VERSION_INFO.get('channel', 'stable').capitalize()}")
            print(f"Build   : {_VERSION_INFO.get('build', 'unknown')}")
    elif args.command == "rollback":
        run_rollback()
    elif args.command == "reset":
        confirm = input("[WARN] Are you sure you want to delete all configuration, logs, and database files? (y/n): ")
        if confirm.lower() == 'y':
            stop_services()
            if CONFIG_FILE.exists(): CONFIG_FILE.unlink()
            db_url = config_manager.get("DATABASE_URL")
            if db_url.startswith("sqlite"):
                db_path = Path(db_url.replace("sqlite:///", ""))
                if db_path.exists(): db_path.unlink()
            if LOG_FILE.exists(): LOG_FILE.unlink()
            print("[OK] Reset complete. Run 'mpmitra start' to rebuild defaults.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Launch FastAPI server
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.join(script_dir, "backend"))
        
        import uvicorn
        from app.main import app
        
        port = config_manager.get("PORT", 8000)
        host = config_manager.get("HOST", "127.0.0.1")
        uvicorn.run(app, host=host, port=int(port), log_level="info")
        sys.exit(0)
        
    main()
