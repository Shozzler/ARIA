"""
Activity tracking for ARIA
Tracks recently visited pages and recently performed appliance actions,
per user, so the dashboard can show a "Recent" section and /history can
show the full list. Stored the same way auth.py stores users: one JSON
file, keyed by username.
"""

import json
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

ACTIVITY_FILE = os.path.join("data", "activity.json")
MAX_ENTRIES_PER_USER = 50   # kept around for the /history page
DASHBOARD_LIMIT = 6         # unpinned items shown on the dashboard


def ensure_data_folder():
    os.makedirs("data", exist_ok=True)


def load_activity() -> dict:
    ensure_data_folder()
    if not os.path.exists(ACTIVITY_FILE):
        return {}
    try:
        with open(ACTIVITY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading activity: {e}")
        return {}


def save_activity(data: dict):
    ensure_data_folder()
    with open(ACTIVITY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def relative_time(iso_str: str) -> str:
    """Turn an ISO timestamp into 'X minutes ago' style text."""
    if not iso_str:
        return ""
    try:
        then = datetime.fromisoformat(iso_str)
    except ValueError:
        return ""
    now = datetime.now(timezone.utc)
    seconds = (now - then).total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(seconds / 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"


def _record(username: str, entry_id: str, kind: str, label: str, url: str, meta: dict = None):
    """Add or bump an entry for this user. Bumping an existing id moves it
    to the top and increments its use count instead of duplicating it."""
    data = load_activity()
    user_entries = data.get(username, [])

    existing = next((e for e in user_entries if e["id"] == entry_id), None)
    if existing:
        existing["label"] = label
        existing["url"] = url
        existing["last_used"] = _now_iso()
        existing["count"] = existing.get("count", 1) + 1
        if meta:
            existing["meta"] = meta
    else:
        user_entries.append({
            "id": entry_id,
            "kind": kind,
            "label": label,
            "url": url,
            "meta": meta or {},
            "count": 1,
            "pinned": False,
            "last_used": _now_iso(),
        })

    # Keep everything sorted most-recent-first, and cap the unpinned tail
    # so the file (and the History page) don't grow forever. Pinned items
    # are never trimmed.
    user_entries.sort(key=lambda e: e["last_used"], reverse=True)
    pinned = [e for e in user_entries if e.get("pinned")]
    unpinned = [e for e in user_entries if not e.get("pinned")][:MAX_ENTRIES_PER_USER]
    merged = pinned + unpinned
    merged.sort(key=lambda e: e["last_used"], reverse=True)

    data[username] = merged
    save_activity(data)


def record_visit(username: str, page_id: str, label: str, url: str):
    _record(username, f"page:{page_id}", "page", label, url)


def record_action(username: str, ha_id: str, action_type: str, label: str, url: str,
                   program_key: str = None, temperature=None):
    """action_type is 'power' or 'program'. Only 'program' actions get a
    one-click repeat button on the dashboard - repeating a power toggle
    is ambiguous (repeat = toggle again = the opposite state)."""
    key_part = program_key or "power"
    temp_part = temperature or "-"
    entry_id = f"action:{ha_id}:{key_part}:{temp_part}"
    meta = {
        "ha_id": ha_id,
        "action_type": action_type,
        "program_key": program_key,
        "temperature": temperature,
    }
    _record(username, entry_id, "action", label, url, meta)


def get_activity(username: str, limit: int = None) -> list:
    """Pinned items always included; unpinned capped at `limit` if given."""
    data = load_activity()
    entries = list(data.get(username, []))
    if limit is None:
        return entries
    pinned = [e for e in entries if e.get("pinned")]
    unpinned = [e for e in entries if not e.get("pinned")]
    return pinned + unpinned[:max(0, limit - len(pinned))]


def toggle_pin(username: str, entry_id: str):
    """Returns the new pinned state, or None if the entry wasn't found."""
    data = load_activity()
    entries = data.get(username, [])
    entry = next((e for e in entries if e["id"] == entry_id), None)
    if not entry:
        return None
    entry["pinned"] = not entry.get("pinned", False)
    save_activity(data)
    return entry["pinned"]
