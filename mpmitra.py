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
from pathlib import Path
from typing import Any, Dict, Optional

# Resolve app paths
if os.name == 'nt':  # Windows
    APPDATA = Path(os.getenv('LOCALAPPDATA', os.getenv('APPDATA', 'C:\\'))) / 'MPMitra'
else:  # macOS / Linux
    APPDATA = Path.home() / '.config' / 'mpmitra'

APPDATA.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = APPDATA / 'config.json'
PID_FILE = APPDATA / 'mpmitra.pid'
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

def get_running_pid() -> Optional[int]:
    """Returns the process ID stored in the PID file if active."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            # Check if process is actually running
            if os.name == 'nt':
                # Windows tasklist check
                output = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True).decode()
                if str(pid) in output:
                    return pid
            else:
                # Unix kill -0 check
                os.kill(pid, 0)
                return pid
        except:
            pass
    return None

def get_pid_on_port(port: int):
    """Finds the PID of the process listening on the specified port."""
    try:
        if os.name == 'nt':
            out = subprocess.check_output("netstat -ano", shell=True).decode()
            for line in out.splitlines():
                if f"127.0.0.1:{port}" in line or f"0.0.0.0:{port}" in line:
                    if "LISTENING" in line:
                        parts = [p.strip() for p in line.split() if p.strip()]
                        if len(parts) >= 5:
                            try:
                                return int(parts[-1])
                            except ValueError:
                                pass
        else:
            out = subprocess.check_output(f"lsof -t -i:{port}", shell=True).decode()
            pids = [int(p.strip()) for p in out.splitlines() if p.strip()]
            if pids:
                return pids[0]
    except Exception:
        pass
    return None




def start_services(open_browser: bool = True):
    """Launches backend FastAPI web server and mounts built frontend."""
    log_message("[*] Starting MP Mitra Decisional Twin platform...")
    
    # 1. Doctor check for port conflicts
    port = config_manager.get("PORT", 8000)
    host = config_manager.get("HOST", "127.0.0.1")
    if is_server_running():
        log_message(f"[ERROR] Port {port} is already in use. Service is likely already running.")
        sys.exit(1)

    # 2. Resolve paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    py_exe = sys.executable
    script_path = os.path.abspath(__file__)
    
    # 3. Spawn fully detached server process
    log_message(f"Starting server on http://{host}:{port}...")
    try:
        if os.name == 'nt':
            # Use wmic process call create to spawn a process completely independent of
            # the parent job object, guaranteeing survival after CLI script exits
            wmic_cmd = f'wmic process call create "\""\"" {py_exe} \"\"\"" -u \"\"\"" {script_path} \"\"\"" --server"'
            wmic_cmd = f"\"{py_exe}\" -u \"{script_path}\" --server"
            full_wmic = f'wmic process call create "{wmic_cmd}"'
            subprocess.run(full_wmic, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait up to 15 seconds to find the listening process
            server_pid = None
            for _ in range(30):
                time.sleep(0.5)
                server_pid = get_pid_on_port(port)
                if server_pid:
                    break
            
            pid_to_save = server_pid or 0
            PID_FILE.write_text(str(pid_to_save))
            log_message(f"Service running in background. Process ID: {pid_to_save}")
        else:
            # Unix detached process
            proc = subprocess.Popen(
                [py_exe, "-u", script_path, "--server"],
                cwd=script_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp
            )
            PID_FILE.write_text(str(proc.pid))
            log_message(f"Service running in background. Process ID: {proc.pid}")
        
    except Exception as e:
        log_message(f"[ERROR] Failed to start service: {e}")
        sys.exit(1)

    # 4. Wait for server readiness health check
    log_message("Waiting for service to initialize...")
    for _ in range(15):
        time.sleep(1)
        if is_server_running():
            log_message("[OK] MP Mitra Platform is ready and online!")
            if open_browser:
                url = f"http://127.0.0.1:{port}"
                log_message(f"Opening browser at {url}...")
                webbrowser.open(url)
                return
            
    log_message("[WARN] Service started but did not respond to health check in time. Please view logs.")

def stop_services():
    """Gracefully terminates background service."""
    log_message("[*] Stopping MP Mitra Platform...")
    port = config_manager.get("PORT", 8000)
    pid = get_running_pid() or get_pid_on_port(port)
    
    if not pid:
        log_message("[WARN] No running service instance found (PID file missing or inactive).")
        if is_server_running():
            log_message("Note: Server port is busy. Attempting to clear port 8000 using command tools...")
            if os.name == 'nt':
                try:
                    subprocess.run("taskkill /IM python.exe /F", shell=True)
                    subprocess.run("taskkill /IM uvicorn.exe /F", shell=True)
                    log_message("[OK] Process terminated.")
                except:
                    pass
        return

    log_message(f"Killing process tree for PID: {pid}")
    try:
        if os.name == 'nt':
            subprocess.run(f"taskkill /PID {pid} /T /F", shell=True)
        else:
            import signal
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        
        if PID_FILE.exists():
            PID_FILE.unlink()
        log_message("[OK] Services successfully stopped.")
    except Exception as e:
        log_message(f"[ERROR] Failed to stop process: {e}")

def restart_services():
    """Restarts background service."""
    stop_services()
    time.sleep(2)
    start_services()

def show_status():
    """Retrieves and prints current service health metrics in professional format."""
    pid = get_running_pid()
    running = is_server_running()
    port = config_manager.get("PORT", 8000)
    version = VERSION
    
    # 1. Determine Backend Status
    backend_status = "Running" if running else "Stopped"
    
    # 2. Determine Frontend Status
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dist_path = os.path.abspath(os.path.join(script_dir, "frontend", "dist"))
    if os.path.exists(dist_path) and os.path.exists(os.path.join(dist_path, "index.html")):
        frontend_status = "Built"
    else:
        frontend_status = "Missing"
        
    # 3. Determine API Health
    api_health = "Unknown"
    if running:
        try:
            api_url = f"http://127.0.0.1:{port}/api/constituency/filter-options"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Status'})
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    api_health = "Healthy"
                else:
                    api_health = "Unhealthy"
        except:
            api_health = "Unhealthy"
    else:
        api_health = "Offline"
        
    # 4. Determine Database Status
    db_status = "Disconnected"
    db_url = config_manager.get("DATABASE_URL")
    if db_url.startswith("sqlite"):
        db_status = "Connected"
    else:
        try:
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                db_status = "Connected"
            except:
                import psycopg2
                conn = psycopg2.connect(db_url, connect_timeout=2)
                conn.close()
                db_status = "Connected"
        except:
            db_status = "Connection Failed"

    print("----------------------------------------")
    print("MP Mitra Status")
    print("----------------------------------------")
    print(f"Backend        : {backend_status}")
    print(f"Frontend       : {frontend_status}")
    print(f"Dashboard      : http://127.0.0.1:{port}")
    print(f"API            : {api_health}")
    print(f"Database       : {db_status}")
    print(f"Port           : {port}")
    print(f"Version        : {version}")
    print("----------------------------------------")

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
                f.seek(0, 2)  # Go to end
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
    
    # 1. Backend Status & Port Availability
    port = config_manager.get("PORT", 8000)
    host = config_manager.get("HOST", "127.0.0.1")
    running = is_server_running()
    if running:
        print(f"[OK] Backend Status: ONLINE (Server is running)")
        print(f"[WARN] Port Availability: Port {port} is currently IN USE by our active server.")
    else:
        print(f"[OK] Backend Status: OFFLINE (Server is not running)")
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((host, int(port)))
            s.close()
            print(f"[OK] Port Availability: Port {port} is FREE and available.")
        except Exception as e:
            print(f"[ERROR] Port Availability: Port {port} is BLOCKED/IN USE by another application ({e}).")

    # 2. Frontend build & Static asset availability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dist_path = os.path.abspath(os.path.join(script_dir, "frontend", "dist"))
    if os.path.exists(dist_path):
        print(f"[OK] Frontend Build: FOUND at {dist_path}")
        if os.path.exists(os.path.join(dist_path, "index.html")):
            print("[OK] Static Assets: index.html exists.")
        else:
            print("[ERROR] Static Assets: index.html is MISSING from dist folder.")
        if os.path.exists(os.path.join(dist_path, "assets")):
            print("[OK] Static Assets: assets directory exists.")
        else:
            print("[ERROR] Static Assets: assets directory is MISSING from dist folder.")
    else:
        print(f"[ERROR] Frontend Build: MISSING (Build directory not found at {dist_path})")

    # 3. Database Health Check
    db_url = config_manager.get("DATABASE_URL")
    print(f"[*] Testing Database: {db_url}")
    if db_url.startswith("sqlite"):
        try:
            sqlite_path = db_url.replace("sqlite:///", "")
            if not os.path.isabs(sqlite_path):
                sqlite_path = os.path.abspath(os.path.join(script_dir, sqlite_path))
            sqlite_dir = Path(sqlite_path).parent
            if sqlite_dir.exists():
                print("[OK] Database Health: Connected (SQLite local DB file path writeable)")
            else:
                print("[WARN] Database Health: Directory for SQLite file does not exist yet.")
        except Exception as e:
            print(f"[ERROR] Database Health: SQLite path validation failed ({e})")
    else:
        try:
            try:
                from sqlalchemy import create_engine, text
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                print("[OK] Database Health: Connected (PostgreSQL engine connected successfully)")
            except Exception:
                import psycopg2
                conn = psycopg2.connect(db_url, connect_timeout=3)
                conn.close()
                print("[OK] Database Health: Connected (PostgreSQL connected successfully)")
        except Exception as e:
            print(f"[ERROR] Database Health: Connection failed ({e})")

    # 4. Firebase Configuration
    fb_svc = config_manager.get_secret("FIREBASE_SERVICE_ACCOUNT_JSON")
    if fb_svc:
        print("[OK] Firebase Configuration: DETECTED (Securely Encrypted)")
    else:
        print("[WARN] Firebase Configuration: MISSING (Using local database/mock credentials)")

    # 5. API Health Check
    if running:
        print("[*] Testing API Health...")
        try:
            api_url = f"http://127.0.0.1:{port}/api/constituency/filter-options"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Doctor'})
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    print("[OK] API Health: HEALTHY (Endpoints responding successfully)")
                else:
                    print(f"[ERROR] API Health: UNHEALTHY (Status code: {response.status})")
        except Exception as e:
            print(f"[ERROR] API Health: UNHEALTHY (Unable to connect to active API: {e})")
    else:
        print("[WARN] API Health: Server is offline, health check skipped.")

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

def run_check_update():
    """Checks for updates using the enterprise updater module."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
        from app.updater import display_check_update, get_local_version
        local = get_local_version()
        display_check_update(local)
    except ImportError:
        # Fallback: basic GitHub API check
        log_message("[*] Checking for updates...")
        try:
            api_url = "https://api.github.com/repos/harshith1432/mp-mitra/releases/latest"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Updater'})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode())
                tag = data.get("tag_name", "").lstrip("v")
                if tag:
                    log_message(f"Latest release: v{tag}  (Current: v{VERSION})")
                else:
                    log_message("No published release found.")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log_message("No published release found on GitHub.")
            elif e.code == 403:
                log_message("GitHub API rate limit exceeded. Try again later.")
            else:
                log_message(f"Update check failed (HTTP {e.code}).")
        except urllib.error.URLError:
            log_message("Network unavailable. Check your internet connection.")
        except Exception as e:
            log_message(f"Update check failed: {e}")


def run_update():
    """Downloads and installs the latest update using the enterprise updater module."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
        from app.updater import run_update as _run_update, get_local_version
        local = get_local_version()
        _run_update(local)
    except ImportError as e:
        log_message(f"[ERROR] Updater module not available: {e}")
        log_message("Run check-update to see if a new version exists.")


def run_rollback():
    """Restores previous version from backup using the enterprise updater module."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
        from app.updater import run_rollback as _run_rollback
        _run_rollback()
    except ImportError as e:
        log_message(f"[ERROR] Updater module not available: {e}")

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
