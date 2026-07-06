from pathlib import Path
from datetime import datetime
import re

ROOT = Path.cwd()

def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path.rename(path.with_suffix(path.suffix + f".bak_{stamp}"))

cache_file = ROOT / "oracle_message_cache.py"

backup(cache_file)

cache_file.write_text(r'''
"""
ORACLE-025.3 — Dashboard Cache

Purpose:
- Cache Oracle Dashboard text/snapshot for 5 seconds
- Avoid duplicate Telegram editMessageText calls
- Reduce repeated JSON reads
- Keep dashboard navigation fast
"""

import time
import hashlib
import json

DASHBOARD_CACHE_TTL_SECONDS = 5

_dashboard_cache = {}
_last_dashboard_edits = {}


def _now():
    return time.time()


def _hash_payload(text, reply_markup=None):
    try:
        markup_text = json.dumps(reply_markup, sort_keys=True, default=str)
    except Exception:
        markup_text = str(reply_markup)

    raw = f"{text}|{markup_text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_dashboard_snapshot_cached(cache_key, builder_func, ttl=DASHBOARD_CACHE_TTL_SECONDS):
    """
    Returns cached dashboard text/data for a few seconds.
    builder_func must be a function that returns the dashboard content.
    """
    now = _now()
    item = _dashboard_cache.get(cache_key)

    if item:
        age = now - item["time"]
        if age <= ttl:
            return item["value"]

    value = builder_func()
    _dashboard_cache[cache_key] = {
        "time": now,
        "value": value,
    }
    return value


def should_skip_dashboard_edit(chat_id, message_id, text, reply_markup=None):
    """
    Returns True when Telegram would receive the exact same dashboard screen again.
    """
    key = f"{chat_id}:{message_id}"
    payload_hash = _hash_payload(text, reply_markup)

    previous = _last_dashboard_edits.get(key)
    if previous == payload_hash:
        return True

    return False


def remember_dashboard_edit(chat_id, message_id, text, reply_markup=None):
    key = f"{chat_id}:{message_id}"
    _last_dashboard_edits[key] = _hash_payload(text, reply_markup)


def clear_dashboard_cache():
    _dashboard_cache.clear()


def clear_dashboard_edit_cache():
    _last_dashboard_edits.clear()
'''.lstrip(), encoding="utf-8")

print("✅ Replaced oracle_message_cache.py")
print("")
print("NEXT MANUAL STEP:")
print("In telegram_bot.py, use these functions around Oracle dashboard editMessageText:")
print("")
print("from oracle_message_cache import get_dashboard_snapshot_cached, should_skip_dashboard_edit, remember_dashboard_edit")
print("")
print("Before rebuilding dashboard text:")
print("dashboard_text = get_dashboard_snapshot_cached('oracle_dashboard_main', build_dashboard_function)")
print("")
print("Before editMessageText:")
print("if should_skip_dashboard_edit(chat_id, message_id, dashboard_text, reply_markup):")
print("    return")
print("")
print("After successful editMessageText:")
print("remember_dashboard_edit(chat_id, message_id, dashboard_text, reply_markup)")