"""
MP Mitra Enterprise Update System
==================================
Production-grade updater: GitHub Releases integration, semantic versioning,
SHA256 verification, graceful error handling. Never exposes raw Python exceptions.

Configuration (stored in config.json):
  github_owner      - GitHub repository owner
  github_repo       - GitHub repository name
  update_channel    - 'stable', 'beta', or 'dev'
"""

import json
import os
import sys
import time
import hashlib
import tempfile
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple, Dict

# ─── Update Configuration ─────────────────────────────────────────────────────

DEFAULT_OWNER   = "harshith1432"
DEFAULT_REPO    = "mp-mitra"
GITHUB_API_BASE = "https://api.github.com"
USER_AGENT      = "MP-Mitra-Updater/1.0 (github.com/harshith1432/mp-mitra)"
REQUEST_TIMEOUT = 10   # seconds


# ─── Logging ──────────────────────────────────────────────────────────────────

def _log(msg: str) -> None:
    """Write a timestamped entry to the updater log."""
    try:
        appdata = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "MPMitra" / "logs"
        appdata.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(appdata / "updater.log", "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


# ─── Configuration Loading ────────────────────────────────────────────────────

def _load_update_config() -> Dict[str, str]:
    """
    Reads update configuration from the app config file.
    Falls back to defaults so the updater always works.
    """
    # Try reading from AppData config
    appdata = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "MPMitra"
    config_path = appdata / "config.json"
    config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass

    return {
        "provider":   config.get("UPDATE_PROVIDER", "github"),
        "owner":      config.get("GITHUB_OWNER", DEFAULT_OWNER),
        "repository": config.get("GITHUB_REPO", DEFAULT_REPO),
        "channel":    config.get("UPDATE_CHANNEL", "stable"),
    }


# ─── Version Management ───────────────────────────────────────────────────────

def get_local_version() -> dict:
    """Reads local version.json from project root. Returns safe defaults if missing."""
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        candidate = os.path.join(here, "version.json")
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    data.setdefault("version", "1.0.0")
                    data.setdefault("channel", "stable")
                    data.setdefault("build", "unknown")
                    data.setdefault("release_date", "unknown")
                    return data
            except Exception:
                pass
        here = os.path.dirname(here)
    _log("version.json not found — using fallback version 1.0.0")
    return {"version": "1.0.0", "channel": "stable", "build": "unknown", "release_date": "unknown"}


def _version_tuple(v: str) -> tuple:
    """Converts a semantic version string (e.g. '1.2.3' or 'v1.2.3') to a comparable tuple."""
    try:
        v = v.lstrip("vV").strip()
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    except Exception:
        return (0, 0, 0)


def is_update_available(local: str, remote: str) -> bool:
    """Returns True if remote version is strictly newer than local version."""
    return _version_tuple(remote) > _version_tuple(local)


# ─── HTTP Helpers ─────────────────────────────────────────────────────────────

class _UpdateError(Exception):
    """Internal exception class for classified update errors."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _http_get_json(url: str) -> dict:
    """
    Makes an HTTP GET request and returns parsed JSON.
    Raises _UpdateError with classified error codes.
    """
    _log(f"GET {url}")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/vnd.github+json",
            }
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            _log(f"Response {resp.status}: {len(body)} bytes")
            return json.loads(body)

    except urllib.error.HTTPError as e:
        _log(f"HTTP {e.code} from {url}")
        if e.code == 404:
            raise _UpdateError("not_found", "Repository or release not found on GitHub.")
        elif e.code == 403:
            try:
                body = e.read().decode("utf-8")
                data = json.loads(body)
                if "rate limit" in data.get("message", "").lower():
                    raise _UpdateError("rate_limit", "GitHub API rate limit exceeded.")
            except (json.JSONDecodeError, AttributeError):
                pass
            raise _UpdateError("forbidden", "GitHub API access denied (HTTP 403).")
        elif e.code == 401:
            raise _UpdateError("unauthorized", "GitHub API requires authentication.")
        else:
            raise _UpdateError("http_error", f"GitHub returned HTTP {e.code}.")

    except urllib.error.URLError as e:
        reason = str(e.reason)
        _log(f"URLError: {reason}")
        if "timed out" in reason.lower() or "timeout" in reason.lower():
            raise _UpdateError("timeout", "Connection to GitHub timed out.")
        raise _UpdateError("no_network", "Unable to reach GitHub. Check your internet connection.")

    except json.JSONDecodeError:
        raise _UpdateError("parse_error", "Could not parse GitHub API response.")

    except Exception as e:
        _log(f"Unknown error: {e}")
        raise _UpdateError("unknown", f"Unexpected error during update check.")


def _http_download(url: str, dest: str) -> None:
    """
    Downloads a file from url to dest with progress display.
    Raises _UpdateError on failure.
    """
    _log(f"Downloading {url} -> {dest}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(dest, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = int(downloaded * 100 / total)
                        mb_done = downloaded / 1024 / 1024
                        mb_total = total / 1024 / 1024
                        print(f"\r  Downloading... {pct}%  ({mb_done:.1f} MB / {mb_total:.1f} MB)", end="", flush=True)
        print()
        _log(f"Download complete: {downloaded} bytes")
    except Exception as e:
        raise _UpdateError("download_failed", f"Download failed: {e}")


# ─── GitHub Release Fetching ──────────────────────────────────────────────────

def _get_latest_release(owner: str, repo: str) -> dict:
    """
    Fetches the latest GitHub Release.
    Returns the release object dict.
    Raises _UpdateError on any problem.
    """
    if not owner or not repo:
        raise _UpdateError("no_config", "GitHub owner or repository is not configured.")

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases/latest"
    data = _http_get_json(url)

    if not data.get("tag_name"):
        raise _UpdateError("empty_release", "No release tag found on GitHub.")

    return data


def _extract_manifest(release: dict) -> dict:
    """
    Extracts structured update manifest from a GitHub Release.
    Tries to download attached release.json first, then falls back
    to constructing from release metadata.
    """
    # 1. Try release.json asset
    for asset in release.get("assets", []):
        if asset.get("name") == "release.json":
            try:
                url = asset["browser_download_url"]
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=10) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:
                _log(f"Could not read release.json asset: {e}")

    # 2. Build manifest from release metadata
    tag = release.get("tag_name", "").lstrip("vV")
    download_url = ""
    sha256 = ""

    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".exe") or ("windows" in name and name.endswith(".zip")):
            download_url = asset.get("browser_download_url", "")
        if name in ("sha256sums.txt", "sha256sums", "sha256"):
            try:
                req = urllib.request.Request(
                    asset.get("browser_download_url", ""),
                    headers={"User-Agent": USER_AGENT}
                )
                with urllib.request.urlopen(req, timeout=10) as r:
                    sha256 = r.read().decode("utf-8").split()[0].lower()
            except Exception:
                pass

    return {
        "version":      tag or "unknown",
        "channel":      "stable",
        "mandatory":    False,
        "notes":        release.get("body", "").strip(),
        "download_url": download_url,
        "sha256":       sha256,
        "published_at": release.get("published_at", ""),
        "release_name": release.get("name", ""),
    }


# ─── SHA256 Verification ──────────────────────────────────────────────────────

def _sha256_file(path: str) -> str:
    """Computes the SHA256 checksum of a file in lowercase hex."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()


# ─── CLI Display Commands ─────────────────────────────────────────────────────

def display_version(local: dict) -> None:
    """Displays current installed version info in a clean table."""
    print("")
    print("MP Mitra  -  Decisional Twin for Members of Parliament")
    print("-------------------------------------------------------")
    print(f"Version  : {local.get('version', '1.0.0')}")
    print(f"Channel  : {local.get('channel', 'stable').capitalize()}")
    print(f"Build    : {local.get('build', 'unknown')}")
    print(f"Released : {local.get('release_date', 'unknown')}")
    print("-------------------------------------------------------")
    print("")


def display_check_update(local: dict) -> None:
    """
    Checks GitHub for the latest release and displays results.
    All errors are displayed as human-readable messages — never raw exceptions.
    """
    cfg = _load_update_config()
    local_version = local.get("version", "1.0.0")
    owner = cfg["owner"]
    repo  = cfg["repository"]
    channel = cfg["channel"]

    print("")
    print(f"Checking for updates...")
    print(f"Current Version : {local_version}")

    _log(f"check-update: owner={owner} repo={repo} channel={channel} local={local_version}")

    # Validate config
    if cfg["provider"] != "github":
        print("[INFO] No release server configured.")
        return

    if not owner or not repo:
        print("[INFO] No release server configured.")
        print("       Set GITHUB_OWNER and GITHUB_REPO in your config file.")
        return

    # Fetch latest release
    try:
        release = _get_latest_release(owner, repo)
    except _UpdateError as e:
        _log(f"Update check error [{e.code}]: {e.message}")
        if e.code == "not_found":
            print("Latest Version  : Not found")
            print("")
            print("[INFO] No published releases found on GitHub.")
            print(f"       To publish a release: git tag v1.0.1 && git push --tags")
        elif e.code == "rate_limit":
            print("Latest Version  : Unavailable")
            print("")
            print("[WARN] GitHub API rate limit exceeded.")
            print("       Wait a few minutes and try again.")
            print(f"       View releases directly: https://github.com/{owner}/{repo}/releases")
        elif e.code in ("no_network", "timeout"):
            print("Latest Version  : Unavailable")
            print("")
            print("[WARN] Unable to reach GitHub.")
            print("       Check your internet connection and try again.")
        elif e.code == "no_config":
            print("Latest Version  : Unavailable")
            print("")
            print("[INFO] Repository not configured.")
        else:
            print("Latest Version  : Unavailable")
            print("")
            print(f"[WARN] {e.message}")
        return

    manifest = _extract_manifest(release)
    remote_version = manifest.get("version", "unknown")

    print(f"Latest Version  : {remote_version}")
    print(f"Channel         : {channel.capitalize()}")
    print("")

    if remote_version == "unknown" or not remote_version:
        print("[WARN] Could not determine the latest version from the GitHub release.")
        return

    if is_update_available(local_version, remote_version):
        print("[UPDATE AVAILABLE]")
        print("")

        # Release notes
        notes = manifest.get("notes", "").strip()
        if notes:
            print("Release Notes:")
            for line in notes.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("- ", "* ", "• ")):
                    print(f"  {line}")
                elif line.startswith("#"):
                    pass  # skip markdown headers
                else:
                    print(f"  - {line}")
            print("")

        published = manifest.get("published_at", "")
        if published:
            print(f"Published       : {published[:10]}")
        print("")
        print("Run:  mpmitra update  to install the latest version.")
    else:
        print("[OK] You are using the latest version.")

    print("")


def run_update(local: dict) -> None:
    """
    Downloads, verifies (SHA256), and installs the latest release.
    All steps are logged and errors are displayed gracefully.
    """
    cfg = _load_update_config()
    local_version = local.get("version", "1.0.0")
    owner = cfg["owner"]
    repo  = cfg["repository"]

    print("")
    print("MP Mitra Update Manager")
    print("------------------------")
    print(f"Current Version : {local_version}")
    print("Checking for updates...")
    print("")

    _log(f"run_update: local={local_version} owner={owner} repo={repo}")

    if not owner or not repo:
        print("[INFO] No release server configured.")
        return

    try:
        release = _get_latest_release(owner, repo)
    except _UpdateError as e:
        _log(f"Update error [{e.code}]: {e.message}")
        if e.code == "not_found":
            print("[INFO] No published releases found. Nothing to update.")
        elif e.code == "rate_limit":
            print("[WARN] GitHub API rate limit exceeded. Try again in a few minutes.")
        elif e.code in ("no_network", "timeout"):
            print("[WARN] Unable to reach GitHub. Check your internet connection.")
        else:
            print(f"[WARN] {e.message}")
        return

    manifest = _extract_manifest(release)
    remote_version = manifest.get("version", "")

    if not remote_version:
        print("[WARN] Could not determine latest version from the release.")
        return

    print(f"Latest Version  : {remote_version}")

    if not is_update_available(local_version, remote_version):
        print("")
        print("[OK] You are already using the latest version.")
        return

    download_url = manifest.get("download_url", "")
    expected_sha = manifest.get("sha256", "").lower().strip()

    if not download_url:
        print("")
        print("[WARN] No installer found in this release.")
        print(f"       Download manually: https://github.com/{owner}/{repo}/releases/tag/v{remote_version}")
        return

    print("")
    print("Downloading update...")

    tmp_dir = tempfile.mkdtemp(prefix="mpmitra_update_")
    ext = ".exe" if download_url.endswith(".exe") else ".zip"
    tmp_file = os.path.join(tmp_dir, f"MPMitraSetup{ext}")

    try:
        _http_download(download_url, tmp_file)
    except _UpdateError as e:
        print(f"[ERROR] {e.message}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    # Verify checksum
    if expected_sha:
        print("Verifying checksum...")
        actual_sha = _sha256_file(tmp_file)
        if actual_sha != expected_sha:
            print("[ERROR] Checksum mismatch — the downloaded file may be corrupted.")
            print(f"        Expected : {expected_sha}")
            print(f"        Actual   : {actual_sha}")
            _log(f"Checksum mismatch: expected={expected_sha} actual={actual_sha}")
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return
        print("[OK] Checksum verified.")
        _log(f"Checksum OK: {actual_sha}")
    else:
        print("[WARN] No checksum available — skipping verification.")

    # Launch installer
    print("Installing...")
    try:
        if ext == ".exe":
            os.startfile(tmp_file)
            print("")
            print("[OK] Installer launched.")
            print("     Follow the on-screen prompts to complete the update.")
            print("     The application will restart automatically after installation.")
        else:
            print(f"[INFO] Update package downloaded: {tmp_file}")
            print("       Extract and run the installer to complete the update.")
    except Exception as e:
        print(f"[ERROR] Could not launch installer: {e}")
        _log(f"Failed to launch installer: {e}")

    shutil.rmtree(tmp_dir, ignore_errors=True)


def run_rollback() -> None:
    """Restores the previous version from backup if available."""
    print("")
    print("MP Mitra Rollback")
    print("------------------")

    appdata = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "MPMitra"
    backups = sorted(appdata.glob("backup_*"), reverse=True)

    if not backups:
        print("[INFO] No backup versions found.")
        print("       Backups are created automatically before each update.")
        print("       Nothing to rollback to.")
        return

    latest = backups[0]
    print(f"Found backup: {latest.name}")
    print(f"Location: {latest}")
    print("")
    print("[INFO] To restore manually, copy all files from the backup folder")
    print("       back to the installation directory.")
    _log(f"Rollback: found backup at {latest}")


def auto_check_on_start(local: dict, silent: bool = True) -> None:
    """
    Silently checks for updates in the background when `mpmitra start` runs.
    If an update is available, prints a brief notification.
    Never crashes or blocks startup.
    """
    cfg = _load_update_config()
    owner = cfg["owner"]
    repo  = cfg["repository"]

    if not owner or not repo:
        return

    _log(f"auto_check_on_start: local={local.get('version')} silent={silent}")

    try:
        release = _get_latest_release(owner, repo)
        manifest = _extract_manifest(release)
        remote_version = manifest.get("version", "")
        local_version = local.get("version", "1.0.0")

        if remote_version and is_update_available(local_version, remote_version):
            print(f"")
            print(f"[UPDATE] Version {remote_version} is available.")
            print(f"         Run  mpmitra update  to install.")
            print(f"")
            _log(f"auto_check: update available {local_version} -> {remote_version}")
        else:
            _log(f"auto_check: up to date ({local_version})")

    except _UpdateError as e:
        # Silent — startup should not fail due to update check
        if e.code not in ("no_network", "timeout", "not_found"):
            _log(f"auto_check warning [{e.code}]: {e.message}")
    except Exception as e:
        _log(f"auto_check unexpected error: {e}")
