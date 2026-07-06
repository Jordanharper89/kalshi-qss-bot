from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()

def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path.rename(path.with_suffix(path.suffix + f".bak_{stamp}"))

target = ROOT / "oracle_dashboard_refresh.py"
backup(target)

target.write_text(r'''
"""
ORACLE-025.4 — Dashboard Background Refresh

Purpose:
- Keep a prebuilt Oracle Dashboard snapshot ready in memory
- Reduce dashboard rebuilds during Telegram navigation
- Make dashboard taps feel faster
- Safe add-on module: does not change trading/scanner logic
"""

import threading
import time
import traceback

REFRESH_INTERVAL_SECONDS = 2.0

_snapshot_lock = threading.Lock()
_snapshot = {
    "text": "🧠 Oracle Dashboard loading...",
    "reply_markup": None,
    "updated_at": 0,
    "ok": False,
    "error": None,
}

_refresh_thread = None
_refresh_running = False
_builder_func = None


def _now():
    return time.time()


def set_dashboard_builder(builder_func):
    """
    Register the function that builds the dashboard.

    builder_func should return either:
    - text
    - (text, reply_markup)
    - {"text": text, "reply_markup": reply_markup}
    """
    global _builder_func
    _builder_func = builder_func


def _normalize_dashboard_result(result):
    if isinstance(result, dict):
        return result.get("text", ""), result.get("reply_markup")

    if isinstance(result, tuple):
        if len(result) >= 2:
            return result[0], result[1]
        if len(result) == 1:
            return result[0], None

    return str(result), None


def refresh_once():
    """
    Rebuild the dashboard snapshot one time.
    Safe to call manually from telegram_bot.py.
    """
    global _snapshot

    if _builder_func is None:
        with _snapshot_lock:
            _snapshot = {
                "text": "⚠️ Oracle Dashboard builder is not registered yet.",
                "reply_markup": None,
                "updated_at": _now(),
                "ok": False,
                "error": "builder_not_registered",
            }
        return _snapshot

    try:
        result = _builder_func()
        text, reply_markup = _normalize_dashboard_result(result)

        with _snapshot_lock:
            _snapshot = {
                "text": text,
                "reply_markup": reply_markup,
                "updated_at": _now(),
                "ok": True,
                "error": None,
            }

    except Exception as exc:
        with _snapshot_lock:
            _snapshot = {
                "text": "⚠️ Oracle Dashboard refresh error. Check logs.",
                "reply_markup": None,
                "updated_at": _now(),
                "ok": False,
                "error": str(exc),
            }

        print("[ORACLE-025.4] Dashboard refresh error:")
        print(traceback.format_exc())

    return get_snapshot()


def get_snapshot():
    """
    Return the latest prebuilt dashboard snapshot.
    """
    with _snapshot_lock:
        return dict(_snapshot)


def get_dashboard_text():
    return get_snapshot().get("text", "")


def get_dashboard_reply_markup():
    return get_snapshot().get("reply_markup")


def _refresh_loop():
    global _refresh_running

    while _refresh_running:
        refresh_once()
        time.sleep(REFRESH_INTERVAL_SECONDS)


def start_dashboard_refresh(builder_func=None):
    """
    Start background refresh thread.
    Safe to call multiple times.
    """
    global _refresh_thread, _refresh_running

    if builder_func is not None:
        set_dashboard_builder(builder_func)

    if _refresh_running:
        return

    _refresh_running = True
    _refresh_thread = threading.Thread(
        target=_refresh_loop,
        name="OracleDashboardRefresh",
        daemon=True,
    )
    _refresh_thread.start()

    print("[ORACLE-025.4] Dashboard background refresh started")


def stop_dashboard_refresh():
    global _refresh_running
    _refresh_running = False
    print("[ORACLE-025.4] Dashboard background refresh stopped")


def dashboard_refresh_status():
    snap = get_snapshot()
    age = round(_now() - snap.get("updated_at", 0), 2) if snap.get("updated_at") else None

    return {
        "running": _refresh_running,
        "updated_at": snap.get("updated_at"),
        "age_seconds": age,
        "ok": snap.get("ok"),
        "error": snap.get("error"),
    }
'''.lstrip(), encoding="utf-8")

print("✅ Created oracle_dashboard_refresh.py")
print("")
print("ORACLE-025.4 installed as a safe add-on.")
print("")
print("Next step:")
print("Send me the Oracle dashboard section of telegram_bot.py")
print("and I’ll wire it to use get_snapshot() instead of rebuilding every tap.")