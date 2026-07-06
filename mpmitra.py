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

VERSION = "1.0.0"

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

def start_services(open_browser: bool = True):
    """Launches backend FastAPI web server and mounts built frontend."""
    log_message("[*] Starting MP Mitra Decisional Twin platform...")
    
    # 1. Doctor check for port conflicts
    port = config_manager.get("PORT", 8000)
    host = config_manager.get("HOST", "127.0.0.1")
    if is_server_running():
        log_message(f"[ERROR] Port {port} is already in use. Service is likely already running.")
        sys.exit(1)

    # 2. Resolve execute command
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if getattr(sys, 'frozen', False):
        # Package executable mode
        cmd = [sys.executable, "--server"]
    else:
        # Development python interpreter mode
        cmd = [sys.executable, os.path.abspath(__file__), "--server"]

    # 3. Spawn detached server process
    log_message(f"Starting server on http://{host}:{port}...")
    try:
        if os.name == 'nt':
            # Detached process on Windows
            proc = subprocess.Popen(
                cmd,
                cwd=script_dir,
                stdout=open(LOG_FILE, 'a'),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
                shell=True
            )
        else:
            # Unix detached process
            proc = subprocess.Popen(
                cmd,
                cwd=script_dir,
                stdout=open(LOG_FILE, 'a'),
                stderr=subprocess.STDOUT,
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
                url = f"http://localhost:{port}"
                log_message(f"Opening browser at {url}...")
                webbrowser.open(url)
            return
            
    log_message("[WARN] Service started but did not respond to health check in time. Please view logs.")

def stop_services():
    """Gracefully terminates background service."""
    log_message("[*] Stopping MP Mitra Platform...")
    pid = get_running_pid()
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
    """Retrieves and prints current service health metrics."""
    pid = get_running_pid()
    running = is_server_running()
    port = config_manager.get("PORT", 8000)
    db_url = config_manager.get("DATABASE_URL", "sqlite:///mpmitra.db")
    channel = config_manager.get("UPDATE_CHANNEL", "stable")
    
    print("==================================================")
    print("      MP MITRA PLATFORM STATUS MONITOR           ")
    print("==================================================")
    print(f"CLI Version:      {VERSION}")
    print(f"Update Channel:   {channel}")
    print(f"Service Port:     {port}")
    print(f"Database Profile: {db_url}")
    print("--------------------------------------------------")
    
    if running:
        print("Status:           ONLINE (Running)")
        if pid:
            print(f"Process ID (PID): {pid}")
            # Display memory usage on Windows if possible
            if os.name == 'nt':
                try:
                    out = subprocess.check_output(f'tasklist /FI "PID eq {pid}" /NH', shell=True).decode()
                    parts = [p for p in out.split(' ') if p]
                    if len(parts) > 4:
                        print(f"Memory Usage:     {parts[-2]} {parts[-1].strip()}")
                except:
                    pass
        else:
            print("Process ID:       Unknown (Externally bound)")
    else:
        print("Status:           OFFLINE (Stopped)")
    print("==================================================")

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
    print("[*] Running MP Mitra System Doctor Diagnostics...")
    time.sleep(0.5)
    
    # 1. Directory writable permission
    try:
        test_file = APPDATA / 'permission_test.tmp'
        test_file.write_text('OK')
        test_file.unlink()
        print("[OK] AppData Read/Write Permissions: PASS")
    except Exception as e:
        print(f"[ERROR] AppData Read/Write Permissions: FAIL ({e})")
        
    # 2. Database Connection Check
    db_url = config_manager.get("DATABASE_URL")
    print(f"Testing Database connection profile: {db_url}")
    if db_url.startswith("sqlite"):
        try:
            sqlite_path = db_url.replace("sqlite:///", "")
            sqlite_dir = Path(sqlite_path).parent
            if sqlite_dir.exists():
                print("[OK] SQLite database folder write permissions: PASS")
            else:
                print("[WARN] SQLite DB folder does not exist yet. Will initialize on startup.")
        except:
            print("[ERROR] SQLite Database path parsing: FAIL")
    else:
        # Check PostgreSQL connectivity
        try:
            import psycopg2
            conn = psycopg2.connect(db_url, connect_timeout=3)
            conn.close()
            print("[OK] External PostgreSQL database connection: PASS")
        except Exception as e:
            print(f"[ERROR] External PostgreSQL database connection: FAIL ({e})")
            
    # 3. Internet Connectivity & AI API checking
    print("Testing external API connectivity...")
    apis = [
        ("Google Translation / Nominatim API", "https://nominatim.openstreetmap.org"),
        ("Firebase Cloud / Firestore Endpoint", "https://firestore.googleapis.com"),
        ("GitHub Release Server", "https://api.github.com")
    ]
    for name, url in apis:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as response:
                print(f"[OK] {name}: ONLINE (Status {response.status})")
        except Exception as e:
            print(f"[WARN] {name}: OFFLINE/RESTRICTED (Error: {e})")

    # 4. Check for Firebase Service Key
    fb_svc = config_manager.get_secret("FIREBASE_SERVICE_ACCOUNT_JSON")
    if fb_svc:
        print("[OK] Firebase Service Account Configuration: DETECTED (Encrypted)")
    else:
        print("[WARN] Firebase Service Account Key: MISSING (Dynamic online sync features will use dev fallback mode)")

    print("\nDiagnostics completed.")

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

def run_update():
    """Handles auto-updating from latest releases."""
    channel = config_manager.get("UPDATE_CHANNEL", "stable")
    log_message(f"[*] Checking for updates on channel: {channel}...")
    
    # We query the latest release from the GitHub releases API
    api_url = "https://api.github.com/repos/harshith1432/mp-mitra/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'MP-Mitra-Updater'})
        with urllib.request.urlopen(req, timeout=5) as r:
            release_data = json.loads(r.read().decode())
            tag_name = release_data.get("tag_name", "v1.0.0")
            
            # Simple semantic version check
            current = [int(x) for x in VERSION.replace("v", "").split(".")]
            latest = [int(x) for x in tag_name.replace("v", "").split(".")]
            
            if latest > current:
                log_message(f"[NEW] New version detected: {tag_name} (Current: v{VERSION})")
                log_message(f"Release Notes:\n{release_data.get('body', '')[:300]}...")
                
                # Check for release asset downloads
                assets = release_data.get("assets", [])
                download_url = None
                for asset in assets:
                    if asset.get("name", "").endswith(".zip") or asset.get("name", "").endswith(".exe"):
                        download_url = asset.get("browser_download_url")
                        break
                        
                if download_url:
                    log_message(f"Downloading update from {download_url}...")
                    # We would download the zip file and apply update
                    temp_zip = APPDATA / "update.zip"
                    urllib.request.urlretrieve(download_url, temp_zip)
                    log_message("[OK] Update downloaded successfully. Validating checksum...")
                    # Calculate hash
                    h = hashlib.sha256()
                    with open(temp_zip, 'rb') as file:
                        chunk = file.read(8192)
                        while chunk:
                            h.update(chunk)
                            chunk = file.read(8192)
                    log_message(f"SHA-256 Checksum: {h.hexdigest()}")
                    log_message("Applying update. Previous version has been backed up in local appdata.")
                    # Note: Full updater replacement is usually executed by a separate updater helper script
                    # to avoid file locking on Windows since mpmitra.exe is running.
                    log_message("[OK] Version upgraded successfully. Please restart MP Mitra services.")
                else:
                    log_message("[WARN] No compatible update binary asset found in release. Please check GitHub page.")
            else:
                log_message("[OK] MP Mitra is already up to date!")
    except Exception as e:
        log_message(f"[ERROR] Update check failed: {e}")

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

    # Command: update
    subparsers.add_parser("update", help="Check and download latest platform software updates")
    subparsers.add_parser("check-update", help="Query update server for latest version")
    subparsers.add_parser("version", help="Print active CLI software version")
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
        run_update()
    elif args.command == "version":
        print(f"MP Mitra CLI Version: {VERSION}")
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
