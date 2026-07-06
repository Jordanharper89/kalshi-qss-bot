from pathlib import Path
from datetime import datetime

path = Path("oracle_message_cache.py")

if path.exists():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(f".py.bak_{stamp}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Backup created: {backup.name}")

path.write_text(r'''
"""
ORACLE-037.2 — Message Cache Stabilization

Purpose:
- Fix missing oracle_message_cache imports
- Support dashboard duplicate edit detection
- Support short TTL snapshot caching
- Keep compatibility with ORACLE-025.3+
"""

import time
import json
import hashlib
import threading

CACHE_TTL_SECONDS = 5

_lock = threading.Lock()
_snapshot_cache = {}
_last_edit_hash = {}


def _now():
    return time.time()


def _stable_json(value):
    try:
        return json.dumps(value, sort_keys=True, default=str)
    except Exception:
        return str(value)


def _hash(text, reply_markup=None):
    raw = str(text or "") + "|" + _stable_json(reply_markup)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_dashboard_snapshot_cached(cache_key, builder_func, ttl=CACHE_TTL_SECONDS):
    """
    Cache expensive dashboard/snapshot builders for a few seconds.
    """
    now = _now()

    with _lock:
        item = _snapshot_cache.get(cache_key)

        if item and now - item["time"] <= ttl:
            return item["value"]

    value = builder_func()

    with _lock:
        _snapshot_cache[cache_key] = {
            "time": now,
            "value": value,
        }

    return value


def should_skip_dashboard_edit(chat_id, message_id, text, reply_markup=None):
    """
    Return True if the same text + keyboard was already sent to this message.
    """
    key = f"{chat_id}:{message_id}"
    payload_hash = _hash(text, reply_markup)

    with _lock:
        return _last_edit_hash.get(key) == payload_hash


def remember_dashboard_edit(chat_id, message_id, text, reply_markup=None):
    """
    Remember latest text + keyboard hash for this Telegram message.
    """
    key = f"{chat_id}:{message_id}"
    payload_hash = _hash(text, reply_markup)

    with _lock:
        _last_edit_hash[key] = payload_hash


def clear_dashboard_cache():
    with _lock:
        _snapshot_cache.clear()


def clear_dashboard_edit_cache():
    with _lock:
        _last_edit_hash.clear()


def diagnostics():
    return {
        "module": "oracle_message_cache",
        "status": "ok",
        "snapshot_cache_items": len(_snapshot_cache),
        "edit_cache_items": len(_last_edit_hash),
        "ttl_seconds": CACHE_TTL_SECONDS,
    }


if __name__ == "__main__":
    print(diagnostics())
'''.lstrip(), encoding="utf-8")

print("===================================")
print(" ORACLE-037.2 INSTALLED")
print(" Message Cache Stabilized")
print("===================================")
print()
print("Test:")
print(" python oracle_message_cache.py")
print(" python telegram_bot.py")