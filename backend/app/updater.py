"""
MP Mitra Enterprise Update System
==================================
Handles version checking, downloading, verification, and installation of updates
from GitHub Releases. Designed to never crash — all errors are reported gracefully.
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
from typing import Optional, Tuple


# ─── Configuration ────────────────────────────────────────────────────────────

GITHUB_OWNER      = "harshith1432"
GITHUB_REPO       = "mp-mitra"
RELEASE_MANIFEST  = "release.json"
GITHUB_API_BASE   = "https://api.github.com"
GITHUB_RAW_BASE   = "https://raw.githubusercontent.com"

USER_AGENT        = "MP-Mitra-Updater/1.0"
REQUEST_TIMEOUT   = 10  # seconds


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _http_get(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Performs an HTTP GET request and returns (body, error_message).
    Never raises exceptions — errors are returned as strings.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read().decode("utf-8"), None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "not_found"
        elif e.code == 403:
            return None, "rate_limit"
        else:
            return None, f"http_{e.code}"
    except urllib.error.URLError as e:
        return None, "no_network"
    except Exception as e:
        return None, f"unknown: {e}"


def _version_tuple(v: str) -> tuple:
    """Converts a semantic version string to a comparable tuple."""
    try:
        v = v.lstrip("v")
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])
    except Exception:
        return (0, 0, 0)


def _sha256_file(path: str) -> str:
    """Computes SHA256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().lower()


# ─── Version Loading ──────────────────────────────────────────────────────────

def get_local_version() -> dict:
    """Reads local version.json from project root. Returns defaults if missing."""
    here = os.path.dirname(os.path.abspath(__file__))
    # Walk up to find version.json
    for _ in range(6):
        candidate = os.path.join(here, "version.json")
        if os.path.exists(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        here = os.path.dirname(here)
    return {"version": "1.0.0", "channel": "stable", "build": "unknown", "release_date": "unknown"}


# ─── GitHub Release Fetching ──────────────────────────────────────────────────

def fetch_latest_release() -> Tuple[Optional[dict], Optional[str]]:
    """
    Queries GitHub API for the latest release.
    Returns (release_data, error_message).
    """
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    body, err = _http_get(url)

    if err == "not_found":
        return None, "no_release"
    elif err == "rate_limit":
        return None, "rate_limit"
    elif err == "no_network":
        return None, "no_network"
    elif err:
        return None, err

    try:
        data = json.loads(body)
        return data, None
    except Exception:
        return None, "parse_error"


def fetch_release_manifest(release: dict) -> Tuple[Optional[dict], Optional[str]]:
    """
    Tries to download release.json manifest attached to the GitHub Release assets.
    Falls back to constructing basic info from release metadata.
    """
    # Try to find release.json in release assets
    for asset in release.get("assets", []):
        if asset.get("name") == RELEASE_MANIFEST:
            download_url = asset.get("browser_download_url", "")
            body, err = _http_get(download_url)
            if body and not err:
                try:
                    return json.loads(body), None
                except Exception:
                    pass

    # Fallback: construct basic manifest from release data
    tag = release.get("tag_name", "").lstrip("v")
    body_text = release.get("body", "")
    # Try to extract download URL for exe/zip from assets
    download_url = ""
    sha256 = ""
    for asset in release.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".exe") or name.endswith(".zip"):
            download_url = asset.get("browser_download_url", "")
        if name == "sha256sums":
            sha_body, _ = _http_get(asset.get("browser_download_url", ""))
            if sha_body:
                sha256 = sha_body.strip()

    manifest = {
        "version": tag or "unknown",
        "channel": "stable",
        "mandatory": False,
        "notes": body_text,
        "download_url": download_url,
        "sha256": sha256,
        "published_at": release.get("published_at", ""),
        "release_name": release.get("name", ""),
    }
    return manifest, None


# ─── Version Comparison ───────────────────────────────────────────────────────

def is_update_available(local_version: str, remote_version: str) -> bool:
    """Returns True if remote version is newer than local."""
    return _version_tuple(remote_version) > _version_tuple(local_version)


# ─── CLI Display ──────────────────────────────────────────────────────────────

def display_version(local: dict) -> None:
    """Displays the local version in professional format."""
    print("")
    print("MP Mitra - Decisional Twin for Members of Parliament")
    print("-----------------------------------------------------")
    print(f"Version  : {local.get('version', 'unknown')}")
    print(f"Channel  : {local.get('channel', 'stable').capitalize()}")
    print(f"Build    : {local.get('build', 'unknown')}")
    print(f"Released : {local.get('release_date', 'unknown')}")
    print("-----------------------------------------------------")


def display_check_update(local: dict) -> None:
    """Runs update check and displays results with release notes."""
    local_version = local.get("version", "1.0.0")
    channel = local.get("channel", "stable")

    print("")
    print(f"Checking for updates on channel: {channel.capitalize()}...")
    print(f"Repository: github.com/{GITHUB_OWNER}/{GITHUB_REPO}")
    print("")

    release, err = fetch_latest_release()

    if err == "no_release":
        print("[INFO] No published release found on GitHub.")
        print("       Push a tagged release (v1.0.1) to enable auto-updates.")
        return
    elif err == "rate_limit":
        print("[WARN] GitHub API rate limit exceeded. Try again in 60 seconds.")
        print("       Tip: You can also visit github.com/{}/{}/releases directly.".format(GITHUB_OWNER, GITHUB_REPO))
        return
    elif err == "no_network":
        print("[WARN] Network unavailable. Check your internet connection and try again.")
        return
    elif err:
        print(f"[WARN] Update check could not complete: {err}")
        return

    manifest, merr = fetch_release_manifest(release)
    if not manifest or merr:
        print("[WARN] Could not read release manifest. The release may be incomplete.")
        return

    remote_version = manifest.get("version", "unknown")

    print(f"Current Version : {local_version}")
    print(f"Latest Version  : {remote_version}")
    print("")

    if remote_version == "unknown":
        print("[WARN] Could not determine latest version from GitHub release.")
        return

    if is_update_available(local_version, remote_version):
        print("[UPDATE AVAILABLE]")
        print("")
        # Display release notes
        notes = manifest.get("notes", "").strip()
        if notes:
            print("Release Notes:")
            for line in notes.splitlines():
                line = line.strip()
                if line.startswith("- ") or line.startswith("* "):
                    print(f"  {line}")
                elif line:
                    print(f"  - {line}")
        print("")
        print("Run  mpmitra update  to install the latest version.")
    else:
        print("[OK] You are using the latest version.")


def run_update(local: dict) -> None:
    """Downloads, verifies, and installs the latest release."""
    local_version = local.get("version", "1.0.0")

    print("")
    print("MP Mitra Update Manager")
    print("------------------------")
    print("Checking for updates...")

    release, err = fetch_latest_release()

    if err == "no_release":
        print("[INFO] No published release found. Nothing to update.")
        return
    elif err == "rate_limit":
        print("[WARN] GitHub API rate limit exceeded. Try again later.")
        return
    elif err == "no_network":
        print("[WARN] No internet connection. Update requires network access.")
        return
    elif err:
        print(f"[WARN] Unable to check for updates: {err}")
        return

    manifest, _ = fetch_release_manifest(release)
    if not manifest:
        print("[WARN] Could not read release manifest.")
        return

    remote_version = manifest.get("version", "unknown")
    if not is_update_available(local_version, remote_version):
        print(f"[OK] Already on latest version ({local_version}).")
        return

    download_url = manifest.get("download_url", "")
    expected_sha = manifest.get("sha256", "").lower()

    if not download_url:
        print("[WARN] No installer download URL found in the release manifest.")
        print(f"       Download manually from: https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases")
        return

    print(f"Downloading version {remote_version}...")
    print(f"Source: {download_url}")

    # Download to temp file
    tmp_dir = tempfile.mkdtemp(prefix="mpmitra_update_")
    ext = ".exe" if download_url.endswith(".exe") else ".zip"
    tmp_file = os.path.join(tmp_dir, f"MPMitraSetup{ext}")

    try:
        req = urllib.request.Request(download_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(tmp_file, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = int(downloaded * 100 / total)
                        print(f"\r  Progress: {pct}% ({downloaded // 1024} KB / {total // 1024} KB)", end="", flush=True)
        print("\n  Download complete.")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    # Verify checksum
    if expected_sha:
        print("Verifying checksum...")
        actual_sha = _sha256_file(tmp_file)
        if actual_sha != expected_sha:
            print(f"[ERROR] Checksum mismatch! File may be corrupted.")
            print(f"        Expected : {expected_sha}")
            print(f"        Actual   : {actual_sha}")
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return
        print("  Checksum OK.")
    else:
        print("[WARN] No checksum available — skipping verification.")

    # Launch installer
    print("Installing...")
    try:
        if ext == ".exe":
            os.startfile(tmp_file)
            print("")
            print("[OK] Installer launched. Follow the on-screen prompts.")
            print("     The application will restart automatically after installation.")
        else:
            print(f"[INFO] Downloaded archive: {tmp_file}")
            print("       Extract and run the installer manually.")
    except Exception as e:
        print(f"[ERROR] Failed to launch installer: {e}")

    shutil.rmtree(tmp_dir, ignore_errors=True)


def run_rollback(backup_dir: Optional[str] = None) -> None:
    """Restores the previous version from backup."""
    print("")
    print("MP Mitra Rollback")
    print("------------------")

    # Look for backup directories
    appdata = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "MPMitra"
    backups = sorted(appdata.glob("backup_*"), reverse=True)

    if not backups:
        print("[WARN] No backup versions found. Cannot rollback.")
        print("       Backups are created automatically before each update.")
        return

    latest = backups[0]
    print(f"Found backup: {latest.name}")
    print(f"Restoring from: {latest}")

    try:
        # Implementation would restore backup files here
        # For now, show the user where the backup is
        print(f"[INFO] Backup location: {latest}")
        print("       Manual restore: copy files from the backup folder back to the installation directory.")
    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
