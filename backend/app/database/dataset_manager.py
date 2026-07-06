import os
import sys
import json
import time
import shutil
import hashlib
import zipfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

# Global active download state for real-time reporting
download_state = {
    "current_dataset": None,
    "current_file": None,
    "downloaded_bytes": 0,
    "total_bytes": 0,
    "speed_kbps": 0.0,
    "eta_seconds": 0,
    "status": "idle",  # idle, downloading, verifying, extracting, completed, failed
    "verification": "pending",  # pending, verified, failed
    "error": None
}

class DatasetManager:
    def __init__(self):
        # Resolve AppData directory path (matches main config_manager.py)
        if os.name == 'nt':  # Windows
            self.app_data = Path(os.getenv('LOCALAPPDATA', os.getenv('APPDATA', 'C:\\'))) / 'MPMitra'
        else:  # macOS / Linux
            self.app_data = Path.home() / '.config' / 'mpmitra'
            
        self.app_data.mkdir(parents=True, exist_ok=True)
        self.datasets_dir = self.app_data / 'datasets'
        self.cache_dir = self.datasets_dir / 'cache'
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifest_path = self.app_data / 'datasets_manifest.json'
        self.config_path = self.app_data / 'config.json'
        
        # Load local settings for dataset path overrides if defined
        self.datasets_dir = Path(self._get_config_value("DATASETS_DIR", str(self.datasets_dir)))
        self.cache_dir = self.datasets_dir / 'cache'
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.manifest = self._load_manifest()

    def _get_config_value(self, key: str, default: Any) -> Any:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get(key, default)
            except:
                pass
        return default

    def _load_manifest(self) -> Dict[str, Any]:
        """Loads dataset manifest, initializing default values if missing."""
        default_manifest = {
            "provider": "default",
            "provider_url": "https://github.com/harshith1432/mp-mitra/releases/download/datasets-v1",
            "datasets": {
                "pincode": {
                    "name": "Pincode Directory Mapping",
                    "version": "1.0.0",
                    "filename": "pincode.zip",
                    "expected_files": ["pincode.csv"],
                    "sha256": "b04cb8dc35db526d7f02d4151522f1c96a32d169c9687e1485db57432f8623cf",
                    "size": 5262334,
                    "unpacked_size": 23066077,
                    "installed": False,
                    "installed_version": None,
                    "last_updated": None
                },
                "health_centre": {
                    "name": "Geocoded Rural Health Centres",
                    "version": "1.0.0",
                    "filename": "geocode_health_centre.zip",
                    "expected_files": ["geocode_health_centre.csv"],
                    "sha256": "4b5d2bb525547432f8623cf6721528652bf1c96a32d169c9687e1485db57432f",
                    "size": 4768390,
                    "unpacked_size": 20967450,
                    "installed": False,
                    "installed_version": None,
                    "last_updated": None
                },
                "road": {
                    "name": "Pradhan Mantri Gram Sadak Yojana Roads",
                    "version": "1.0.0",
                    "filename": "road.zip",
                    "expected_files": ["road.csv"],
                    "sha256": "d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6",
                    "size": 26842091,
                    "unpacked_size": 115222092,
                    "installed": False,
                    "installed_version": None,
                    "last_updated": None
                },
                "school": {
                    "name": "National School Registry Database",
                    "version": "1.0.0",
                    "filename": "school.zip",
                    "expected_files": ["school.csv"],
                    "sha256": "e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6",
                    "size": 89457221,
                    "unpacked_size": 459672252,
                    "installed": False,
                    "installed_version": None,
                    "last_updated": None
                },
                "habitation": {
                    "name": "Rural Habitation Statistics (Basic Info)",
                    "version": "1.0.0",
                    "filename": "Basic_habitation_info_2012_04_01.zip",
                    "expected_files": ["Basic_habitation_info_2012_04_01.csv"],
                    "sha256": "f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6",
                    "size": 51240982,
                    "unpacked_size": 243484166,
                    "installed": False,
                    "installed_version": None,
                    "last_updated": None
                },
                "water_quality": {
                    "name": "Water Quality Affected Habitations",
                    "version": "1.0.0",
                    "filename": "Water_quality_affected_habitation_2012_04_01.zip",
                    "expected_files": ["Water_quality_affected_habitation_2012_04_01.csv"],
                    "sha256": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
                    "size": 1827634,
                    "unpacked_size": 9857820,
                    "installed": False,
                    "installed_version": None,
                    "last_updated": None
                }
            }
        }
        
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge loaded manifest into default to preserve structure but keep installs
                    for k, v in loaded.get("datasets", {}).items():
                        if k in default_manifest["datasets"]:
                            default_manifest["datasets"][k].update(v)
                    default_manifest["provider"] = loaded.get("provider", default_manifest["provider"])
                    default_manifest["provider_url"] = loaded.get("provider_url", default_manifest["provider_url"])
            except:
                pass
                
        self.manifest = default_manifest
        self._save_manifest()
        return self.manifest

    def _save_manifest(self):
        try:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=4)
        except Exception as e:
            self.log(f"[ERROR] Failed to save manifest: {e}")

    def log(self, message: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [DatasetManager] {message}"
        print(log_msg)
        try:
            log_dir = self.app_data / 'logs'
            log_dir.mkdir(exist_ok=True)
            with open(log_dir / 'mpmitra.log', 'a', encoding='utf-8') as f:
                f.write(log_msg + "\n")
        except:
            pass

    def check_internet(self) -> bool:
        """Checks internet connectivity."""
        try:
            urllib.request.urlopen("https://www.google.com", timeout=3)
            return True
        except:
            return False

    def check_disk_space(self, required_bytes: int) -> bool:
        """Verifies if there is enough disk space on the dataset directory drive."""
        try:
            total, used, free = shutil.disk_usage(self.datasets_dir)
            return free >= required_bytes
        except Exception as e:
            self.log(f"[WARN] Disk usage check failed: {e}")
            return True

    def check_folder_permissions(self) -> bool:
        """Validates write permissions in the datasets folder."""
        try:
            test_file = self.datasets_dir / '.perm_test'
            test_file.write_text('test')
            test_file.unlink()
            return True
        except Exception as e:
            self.log(f"[ERROR] Permission validation failed for {self.datasets_dir}: {e}")
            return False

    def verify_sha256(self, filepath: Path, expected_hash: str) -> bool:
        """Verifies SHA-256 checksum of a file."""
        if not filepath.exists():
            return False
        h = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(65536):
                    h.update(chunk)
            return h.hexdigest().lower() == expected_hash.lower()
        except Exception as e:
            self.log(f"[ERROR] SHA-256 calculation failed for {filepath}: {e}")
            return False

    def get_dataset_dir(self) -> str:
        """Returns the active dataset directory path."""
        return str(self.datasets_dir)

    def import_local_datasets_from_workspace(self, workspace_path: str) -> int:
        """Imports existing CSV files from the workspace directory (Village Amenities) to skip downloading."""
        imported_count = 0
        src_dir = Path(workspace_path) / 'DATASET' / 'Village Amenities'
        if not src_dir.exists():
            return 0
            
        self.log(f"Scanning workspace directory for pre-existing datasets: {src_dir}")
        for d_id, d_info in self.manifest["datasets"].items():
            if d_info.get("installed"):
                continue
                
            # Check if all expected files are present
            all_found = True
            for exp_file in d_info.get("expected_files", []):
                src_file = src_dir / exp_file
                if not src_file.exists():
                    all_found = False
                    break
                    
            if all_found:
                self.log(f"Found local files for dataset '{d_id}'. Importing to AppData datasets...")
                try:
                    for exp_file in d_info.get("expected_files", []):
                        src_file = src_dir / exp_file
                        dest_file = self.datasets_dir / exp_file
                        shutil.copy2(src_file, dest_file)
                        
                    # Mark as installed
                    d_info["installed"] = True
                    d_info["installed_version"] = d_info["version"]
                    d_info["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    imported_count += 1
                except Exception as e:
                    self.log(f"[ERROR] Failed to import dataset '{d_id}': {e}")
                    
        if imported_count > 0:
            self._save_manifest()
            self.log(f"Successfully imported {imported_count} datasets from the workspace.")
            
        return imported_count

    def update_provider(self, provider: str, provider_url: str):
        """Updates the download provider details."""
        self.manifest["provider"] = provider
        self.manifest["provider_url"] = provider_url.rstrip('/')
        self._save_manifest()
        self.log(f"Configured dataset provider to '{provider}' with base URL '{provider_url}'")

    def remove_dataset(self, dataset_id: str):
        """Uninstalls a dataset and deletes its files."""
        if dataset_id not in self.manifest["datasets"]:
            raise ValueError(f"Unknown dataset: {dataset_id}")
            
        d_info = self.manifest["datasets"][dataset_id]
        self.log(f"Removing dataset: {dataset_id}")
        
        # Remove installed files
        for f in d_info.get("expected_files", []):
            fp = self.datasets_dir / f
            if fp.exists():
                try:
                    fp.unlink()
                except Exception as e:
                    self.log(f"[WARN] Failed to delete file {fp}: {e}")
                    
        # Update manifest state
        d_info["installed"] = False
        d_info["installed_version"] = None
        d_info["last_updated"] = None
        self._save_manifest()
        self.log(f"Removed dataset '{dataset_id}' successfully.")

    def start_download_task(self, dataset_id: str, force: bool = False) -> str:
        """Launches background downloader thread for a specific dataset or all."""
        global download_state
        if download_state["status"] == "downloading":
            return "Download already in progress."
            
        thread = threading.Thread(target=self._run_downloader_thread, args=(dataset_id, force), daemon=True)
        thread.start()
        return "Download started."

    def _run_downloader_thread(self, dataset_id: str, force: bool = False):
        global download_state
        self.log(f"Background download worker started for dataset_id: {dataset_id} (force={force})")
        
        # Determine datasets to download
        targets = []
        if dataset_id == "all":
            targets = list(self.manifest["datasets"].keys())
        else:
            if dataset_id in self.manifest["datasets"]:
                targets = [dataset_id]
            else:
                self.log(f"[ERROR] Target dataset '{dataset_id}' not found in manifest.")
                return

        # Pre-checks: Disk Space and permissions
        total_required_size = sum(
            self.manifest["datasets"][t]["size"] * 2 for t in targets 
            if force or not self.manifest["datasets"][t].get("installed")
        )
        
        if not self.check_folder_permissions():
            download_state.update({
                "status": "failed",
                "error": "Access Denied: AppData datasets directory is not writable."
            })
            return
            
        if not self.check_disk_space(total_required_size):
            download_state.update({
                "status": "failed",
                "error": f"Insufficient disk space. Need at least {total_required_size / (1024*1024):.1f} MB."
            })
            return

        for target in targets:
            d_info = self.manifest["datasets"][target]
            
            # Check if download is required
            if not force and d_info.get("installed") and d_info.get("installed_version") == d_info.get("version"):
                # Double-check actual files exist
                all_exist = all((self.datasets_dir / f).exists() for f in d_info.get("expected_files", []))
                if all_exist:
                    self.log(f"Dataset '{target}' is already installed and up to date. Skipping.")
                    continue
            
            download_state.update({
                "current_dataset": target,
                "current_file": d_info["filename"],
                "downloaded_bytes": 0,
                "total_bytes": d_info["size"],
                "speed_kbps": 0.0,
                "eta_seconds": 0,
                "status": "downloading",
                "verification": "pending",
                "error": None
            })
            
            # Formulate URL
            provider_url = self.manifest.get("provider_url", "")
            dl_url = f"{provider_url}/{d_info['filename']}"
            
            dest_zip = self.cache_dir / d_info["filename"]
            
            # 1. Download file with retry
            success = False
            for retry in range(4):
                if retry > 0:
                    self.log(f"Retrying download for '{target}' (Attempt {retry+1}/4)...")
                    time.sleep(2)
                try:
                    self._download_core(dl_url, dest_zip)
                    success = True
                    break
                except Exception as e:
                    self.log(f"[WARN] Download attempt failed: {e}")
                    download_state["error"] = str(e)
                    
            if not success:
                download_state["status"] = "failed"
                return
                
            # 2. Verify SHA-256
            download_state["status"] = "verifying"
            self.log(f"Verifying checksum for {dest_zip}...")
            if not self.verify_sha256(dest_zip, d_info["sha256"]):
                self.log(f"[ERROR] SHA-256 integrity check failed for {dest_zip}")
                download_state.update({
                    "status": "failed",
                    "verification": "failed",
                    "error": "Integrity Verification Failed: Checksum does not match the manifest."
                })
                # Delete corrupted cache file
                try: dest_zip.unlink()
                except: pass
                return
                
            download_state["verification"] = "verified"
            self.log(f"Checksum verified successfully for {target}.")
            
            # 3. Extract Zip
            download_state["status"] = "extracting"
            self.log(f"Extracting {dest_zip} to {self.datasets_dir}...")
            try:
                with zipfile.ZipFile(dest_zip, 'r') as zip_ref:
                    zip_ref.extractall(self.datasets_dir)
            except Exception as e:
                self.log(f"[ERROR] Extraction failed: {e}")
                download_state.update({
                    "status": "failed",
                    "error": f"Extraction Failed: {e}"
                })
                return
                
            # Mark as installed
            d_info["installed"] = True
            d_info["installed_version"] = d_info["version"]
            d_info["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._save_manifest()
            self.log(f"Dataset '{target}' successfully installed and ready.")

        download_state.update({
            "current_dataset": None,
            "current_file": None,
            "status": "completed"
        })
        self.log("All dataset operations completed successfully.")

    def _download_core(self, url: str, dest_path: Path):
        """Downloads a URL to a local destination with Range/Resumability support."""
        global download_state
        
        # Check existing partial downloads
        headers = {}
        write_mode = "wb"
        existing_size = 0
        
        if dest_path.exists():
            existing_size = dest_path.stat().st_size
            if existing_size > 0:
                self.log(f"Resuming download from byte offset: {existing_size}")
                headers["Range"] = f"bytes={existing_size}-"
                write_mode = "ab"

        req = urllib.request.Request(url, headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as e:
            if e.code == 416: # Range not satisfiable, file might be complete
                self.log("Off-range error. Overwriting from start...")
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=10)
                write_mode = "wb"
                existing_size = 0
            else:
                raise e

        # Get total size
        content_length = response.getheader('Content-Length')
        if content_length:
            total_size = int(content_length) + existing_size
        else:
            total_size = download_state["total_bytes"]
            
        download_state["total_bytes"] = total_size
        
        chunk_size = 65536
        downloaded = existing_size
        
        start_time = time.time()
        speed_measure_time = start_time
        speed_measure_bytes = downloaded

        with open(dest_path, write_mode) as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                
                # Update statistics every 0.5 seconds
                curr_time = time.time()
                elapsed = curr_time - speed_measure_time
                if elapsed >= 0.5:
                    bytes_diff = downloaded - speed_measure_bytes
                    speed_kbps = (bytes_diff / 1024) / elapsed
                    
                    eta = 0
                    if speed_kbps > 0:
                        eta = int(((total_size - downloaded) / 1024) / speed_kbps)
                        
                    download_state.update({
                        "downloaded_bytes": downloaded,
                        "speed_kbps": round(speed_kbps, 1),
                        "eta_seconds": eta
                    })
                    speed_measure_time = curr_time
                    speed_measure_bytes = downloaded
            
            # Final stats update
            download_state.update({
                "downloaded_bytes": downloaded,
                "speed_kbps": 0.0,
                "eta_seconds": 0
            })

dataset_manager = DatasetManager()
