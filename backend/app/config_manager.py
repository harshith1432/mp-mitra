import os
import sys
import json
import base64
import hashlib
import uuid
import socket
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Load env variables from .env if present (dev environment support)
# Make sure we do this before ConfigManager evaluates defaults
try:
    # Try loading from the root of the project as well as backend
    load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))
    load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))
except Exception:
    pass
load_dotenv()

class ConfigManager:
    def __init__(self):
        # Resolve config directory
        if os.name == 'nt':  # Windows
            self.app_data = Path(os.getenv('LOCALAPPDATA', os.getenv('APPDATA', 'C:\\'))) / 'MPMitra'
        else:  # macOS / Linux
            self.app_data = Path.home() / '.config' / 'mpmitra'
        
        self.app_data.mkdir(parents=True, exist_ok=True)
        self.config_path = self.app_data / 'config.json'
        
        # Load active configuration
        self.config = self._load_config()

    def _get_machine_key(self) -> bytes:
        """Derive a unique encryption key based on machine MAC address and hostname."""
        mac = str(uuid.getnode())
        hostname = socket.gethostname()
        raw_key = f"MPMitra_Secure_Salt_{mac}_{hostname}".encode('utf-8')
        return hashlib.sha256(raw_key).digest()

    def encrypt(self, val: str) -> str:
        """Encrypts a string using a pure-Python machine-keyed XOR cipher."""
        if not val:
            return ""
        key = self._get_machine_key()
        val_bytes = val.encode('utf-8')
        encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(val_bytes)])
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, val: str) -> str:
        """Decrypts a machine-keyed XOR cipher string."""
        if not val:
            return ""
        try:
            key = self._get_machine_key()
            encrypted_bytes = base64.b64decode(val.encode('utf-8'))
            decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes)])
            return decrypted.decode('utf-8')
        except Exception:
            return ""

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSON file or initializes defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ConfigWarning] Failed to read config file, resetting to defaults: {e}", file=sys.stderr)
        
        # Default configuration
        default_db = f"sqlite:///{str(self.app_data / 'mpmitra.db')}"
        return {
            "DATABASE_URL": default_db,
            "UPDATE_CHANNEL": "stable",
            "PORT": 8000,
            "HOST": "127.0.0.1",
            "SECRETS": {}
        }

    def save(self):
        """Saves current configuration state to disk."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"[ConfigError] Failed to save config: {e}", file=sys.stderr)

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a configuration parameter."""
        # For development, check environment first for certain keys (like DATABASE_URL, PORT, HOST)
        import sys
        if not getattr(sys, 'frozen', False):
            env_val = os.getenv(key)
            if env_val:
                return env_val
        return self.config.get(key, default)

    def set(self, key: str, val: Any):
        """Sets a configuration parameter and saves."""
        self.config[key] = val
        self.save()

    def get_secret(self, key: str, default: str = "") -> str:
        """Gets and decrypts a sensitive configuration parameter."""
        secrets = self.config.get("SECRETS", {})
        encrypted_val = secrets.get(key)
        if encrypted_val:
            return self.decrypt(encrypted_val)
        # Fallback to environment variables for dev environments
        env_val = os.getenv(key)
        if env_val:
            return env_val
        return default

    def set_secret(self, key: str, val: str):
        """Encrypts and stores a sensitive configuration parameter."""
        if "SECRETS" not in self.config:
            self.config["SECRETS"] = {}
        self.config["SECRETS"][key] = self.encrypt(val)
        self.save()

# Global config manager instance
config_manager = ConfigManager()
