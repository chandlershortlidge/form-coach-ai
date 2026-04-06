"""
Session persistence layer.

Phase 1: local JSON file storage.
Phase 2: swap to Firestore by replacing this module's internals.
The interface (create / get / list / update) stays the same.
"""

import json
import os
from datetime import datetime, timezone

SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "sessions_data.json")
MAX_SESSIONS = 50


def _read_all():
    if not os.path.exists(SESSIONS_FILE):
        return {}
    with open(SESSIONS_FILE, "r") as f:
        return json.load(f)


def _write_all(data):
    with open(SESSIONS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def create_session(session_id, *, user_query=None, video_filename=None):
    """Create a new session record. Returns the session dict."""
    now = datetime.now(timezone.utc).isoformat()
    session = {
        "session_id": session_id,
        "created_at": now,
        "updated_at": now,
        "exercise_label": None,
        "user_query": user_query,
        "video_filename": video_filename,
        "video_gcs_path": None,
        "classification_raw": None,
        "response": None,
        "status": "pending",
    }
    data = _read_all()
    data[session_id] = session
    # Prune oldest if over limit
    if len(data) > MAX_SESSIONS:
        sorted_ids = sorted(data, key=lambda k: data[k]["created_at"])
        for old_id in sorted_ids[: len(data) - MAX_SESSIONS]:
            del data[old_id]
    _write_all(data)
    return session


def get_session(session_id):
    """Return a session by id, or None."""
    data = _read_all()
    return data.get(session_id)


def update_session(session_id, **fields):
    """Merge fields into an existing session. Returns updated session or None."""
    data = _read_all()
    if session_id not in data:
        return None
    data[session_id].update(fields)
    data[session_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_all(data)
    return data[session_id]


def list_sessions(limit=20):
    """Return sessions newest-first, with only sidebar-relevant fields."""
    data = _read_all()
    sessions = sorted(data.values(), key=lambda s: s["created_at"], reverse=True)
    return [
        {
            "session_id": s["session_id"],
            "exercise_label": s.get("exercise_label"),
            "video_filename": s.get("video_filename"),
            "status": s.get("status"),
            "created_at": s.get("created_at"),
        }
        for s in sessions[:limit]
    ]
