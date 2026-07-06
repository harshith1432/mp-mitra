"""
MP MITRA — Citizen Session & Profile Manager (Firestore)
=========================================================
Manages persistent citizen profiles and conversation sessions.
Every citizen is identified by their WhatsApp number.
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from app.database.firebase_config import get_firestore_client
    _firestore_available = True
except Exception:
    _firestore_available = False

# ── In-memory fallback when Firestore is unavailable ─────────────────────────
_memory_store: Dict[str, Any] = {}


def _get_db():
    if _firestore_available:
        return get_firestore_client()
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATES
# ═══════════════════════════════════════════════════════════════════════════════

class SessionState:
    START            = "START"
    LANG_SELECT      = "LANG_SELECT"
    STATE_SELECT     = "STATE_SELECT"
    DISTRICT_SELECT  = "DISTRICT_SELECT"
    TALUK_SELECT     = "TALUK_SELECT"
    VILLAGE_SELECT   = "VILLAGE_SELECT"
    LOCATION_SHARE   = "LOCATION_SHARE"
    MAIN_MENU        = "MAIN_MENU"
    SUBMIT_DESCRIBE  = "SUBMIT_DESCRIBE"
    SUBMIT_CONFIRM   = "SUBMIT_CONFIRM"
    SUBMIT_PROCESSING= "SUBMIT_PROCESSING"
    TRACK            = "TRACK"
    SCHEME           = "SCHEME"
    PROJECTS         = "PROJECTS"
    AI_CHAT          = "AI_CHAT"
    UPDATE_LOCATION  = "UPDATE_LOCATION"


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_citizen_profile(phone: str) -> Optional[Dict]:
    """Retrieve citizen profile by WhatsApp number."""
    db = _get_db()
    if db:
        doc = db.collection("citizens").document(phone).get()
        if doc.exists:
            return doc.to_dict().get("profile")
    else:
        return _memory_store.get(phone, {}).get("profile")
    return None


def save_citizen_profile(phone: str, profile: Dict):
    """Save or update citizen profile."""
    db = _get_db()
    now = datetime.utcnow().isoformat()
    profile["last_active"] = now
    if db:
        db.collection("citizens").document(phone).set(
            {"profile": profile}, merge=True
        )
    else:
        if phone not in _memory_store:
            _memory_store[phone] = {}
        _memory_store[phone]["profile"] = profile


def update_profile_field(phone: str, field: str, value: Any):
    """Update a single field in citizen profile."""
    db = _get_db()
    if db:
        db.collection("citizens").document(phone).set(
            {"profile": {field: value}}, merge=True
        )
    else:
        if phone not in _memory_store:
            _memory_store[phone] = {"profile": {}}
        _memory_store[phone].setdefault("profile", {})[field] = value


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_session(phone: str) -> Dict:
    """Get current conversation session for a citizen."""
    db = _get_db()
    default = {"state": SessionState.START, "step": 0, "temp_data": {}}
    if db:
        doc = db.collection("citizens").document(phone).get()
        if doc.exists:
            return doc.to_dict().get("session", default)
    else:
        return _memory_store.get(phone, {}).get("session", default)
    return default


def save_session(phone: str, state: str, step: int = 0, temp_data: Dict = None):
    """Save conversation session state."""
    db = _get_db()
    session = {
        "state": state,
        "step": step,
        "temp_data": temp_data or {},
        "updated_at": datetime.utcnow().isoformat()
    }
    if db:
        db.collection("citizens").document(phone).set(
            {"session": session}, merge=True
        )
    else:
        if phone not in _memory_store:
            _memory_store[phone] = {}
        _memory_store[phone]["session"] = session


def update_session_temp(phone: str, key: str, value: Any):
    """Update a single key in session temp_data."""
    session = get_session(phone)
    session["temp_data"][key] = value
    save_session(phone, session["state"], session["step"], session["temp_data"])


def reset_session_to_menu(phone: str):
    """Reset session back to main menu after completing a flow."""
    save_session(phone, SessionState.MAIN_MENU, 0, {})


# ═══════════════════════════════════════════════════════════════════════════════
# SUBMISSION OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def save_submission(phone: str, submission: Dict) -> str:
    """Save a new citizen submission to Firestore."""
    import uuid
    submission_id = f"SUB-{str(uuid.uuid4())[:8].upper()}"
    submission["submission_id"] = submission_id
    submission["created_at"] = datetime.utcnow().isoformat()
    submission["status"] = "Received"

    db = _get_db()
    if db:
        db.collection("citizens").document(phone)\
          .collection("submissions").document(submission_id)\
          .set(submission)
    else:
        if phone not in _memory_store:
            _memory_store[phone] = {}
        _memory_store[phone].setdefault("submissions", {})[submission_id] = submission

    return submission_id


def get_submissions(phone: str) -> list:
    """Get all submissions for a citizen (citizen-visible fields only)."""
    VISIBLE_FIELDS = [
        "submission_id", "created_at", "category", "status",
        "ai_summary", "latest_remark", "progress_pct"
    ]
    db = _get_db()
    submissions = []
    if db:
        docs = db.collection("citizens").document(phone)\
                 .collection("submissions")\
                 .order_by("created_at", direction="DESCENDING")\
                 .limit(10).stream()
        for doc in docs:
            data = doc.to_dict()
            submissions.append({k: data.get(k, "") for k in VISIBLE_FIELDS})
    else:
        raw = _memory_store.get(phone, {}).get("submissions", {})
        for sid, data in sorted(raw.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
            submissions.append({k: data.get(k, "") for k in VISIBLE_FIELDS})
    return submissions


def update_submission_status(phone: str, submission_id: str, status: str,
                              ai_summary: str = "", remark: str = "", progress: int = 0):
    """Update submission status (used by AI pipeline)."""
    db = _get_db()
    update = {
        "status": status,
        "ai_summary": ai_summary,
        "latest_remark": remark,
        "progress_pct": progress,
        "updated_at": datetime.utcnow().isoformat()
    }
    if db:
        db.collection("citizens").document(phone)\
          .collection("submissions").document(submission_id)\
          .set(update, merge=True)
    else:
        subs = _memory_store.get(phone, {}).get("submissions", {})
        if submission_id in subs:
            subs[submission_id].update(update)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════════

def is_registered(phone: str) -> bool:
    """Check if citizen has completed profile setup."""
    profile = get_citizen_profile(phone)
    return bool(profile and profile.get("language") and profile.get("village"))


def get_language(phone: str) -> str:
    """Get stored language preference, default English."""
    profile = get_citizen_profile(phone)
    if profile:
        return profile.get("language", "en")
    return "en"
