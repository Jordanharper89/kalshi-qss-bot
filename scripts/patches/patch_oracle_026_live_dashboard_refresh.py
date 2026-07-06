from pathlib import Path

ROOT = Path.cwd()

refresh_file = ROOT / "oracle_dashboard_refresh.py"
bot_file = ROOT / "telegram_bot.py"

refresh_code = r'''
"""
ORACLE-026 — Live Dashboard Auto-Refresh

Purpose:
- Track the currently open Oracle Dashboard message.
- Refresh it lightly in the background.
- Skip duplicate edits when text has not changed.
- Stop safely when user leaves dashboard.

This module is intentionally simple and defensive.
"""

import time
import threading


class OracleDashboardRefreshManager:
    def __init__(self, refresh_seconds=5):
        self.refresh_seconds = refresh_seconds
        self.active = {}
        self.last_text = {}
        self.lock = threading.Lock()
        self.running = False

    def mark_open(self, chat_id, message_id):
        key = str(chat_id)
        with self.lock:
            self.active[key] = {
                "chat_id": chat_id,
                "message_id": message_id,
                "opened_at": time.time(),
            }

    def mark_closed(self, chat_id):
        key = str(chat_id)
        with self.lock:
            self.active.pop(key, None)
            self.last_text.pop(key, None)

    def should_send(self, chat_id, text):
        key = str(chat_id)
        with self.lock:
            old = self.last_text.get(key)
            if old == text:
                return False
            self.last_text[key] = text
            return True

    def get_active_dashboards(self):
        with self.lock:
            return list(self.active.values())

    def start(self, build_dashboard_text_func, edit_message_func):
        if self.running:
            return

        self.running = True

        def loop():
            while self.running:
                try:
                    dashboards = self.get_active_dashboards()

                    for item in dashboards:
                        chat_id = item.get("chat_id")
                        message_id = item.get("message_id")

                        if not chat_id or not message_id:
                            continue

                        text = build_dashboard_text_func(chat_id)

                        if not text:
                            continue

                        if not self.should_send(chat_id, text):
                            continue

                        edit_message_func(chat_id, message_id, text)

                except Exception as e:
                    print(f"[ORACLE-026] dashboard refresh error: {e}")

                time.sleep(self.refresh_seconds)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
        print("[ORACLE-026] Live dashboard refresh started")


oracle_dashboard_refresh = OracleDashboardRefreshManager(refresh_seconds=5)
'''

refresh_file.write_text(refresh_code, encoding="utf-8")
print("[OK] Created oracle_dashboard_refresh.py")


if not bot_file.exists():
    print("[WARN] telegram_bot.py not found. Created refresh module only.")
    raise SystemExit


text = bot_file.read_text(encoding="utf-8")

if "from oracle_dashboard_refresh import oracle_dashboard_refresh" not in text:
    text = "from oracle_dashboard_refresh import oracle_dashboard_refresh\n" + text
    print("[OK] Added ORACLE-026 import")

# Add safe helper functions near bottom if missing.
helpers = r'''

# ==============================
# ORACLE-026 LIVE DASHBOARD HELPERS
# ==============================

def oracle_026_mark_dashboard_open(chat_id, message_id):
    try:
        oracle_dashboard_refresh.mark_open(chat_id, message_id)
    except Exception as e:
        print(f"[ORACLE-026] mark open error: {e}")


def oracle_026_mark_dashboard_closed(chat_id):
    try:
        oracle_dashboard_refresh.mark_closed(chat_id)
    except Exception as e:
        print(f"[ORACLE-026] mark closed error: {e}")


def oracle_026_build_dashboard_text(chat_id):
    try:
        # Uses existing dashboard builder if available.
        if "build_oracle_dashboard_text" in globals():
            return build_oracle_dashboard_text()

        if "render_oracle_dashboard" in globals():
            return render_oracle_dashboard()

        if "build_oracle_dashboard" in globals():
            return build_oracle_dashboard()

        return None
    except Exception as e:
        print(f"[ORACLE-026] build text error: {e}")
        return None


def oracle_026_edit_dashboard_message(chat_id, message_id, text):
    try:
        # Uses existing Telegram edit helper if available.
        if "telegram_edit_message_text" in globals():
            return telegram_edit_message_text(chat_id, message_id, text)

        if "edit_message_text" in globals():
            return edit_message_text(chat_id, message_id, text)

        print("[ORACLE-026] No edit helper found yet")
    except Exception as e:
        print(f"[ORACLE-026] edit error: {e}")


def oracle_026_start_live_dashboard_refresh():
    try:
        oracle_dashboard_refresh.start(
            oracle_026_build_dashboard_text,
            oracle_026_edit_dashboard_message,
        )
    except Exception as e:
        print(f"[ORACLE-026] start refresh error: {e}")

'''

if "ORACLE-026 LIVE DASHBOARD HELPERS" not in text:
    text += helpers
    print("[OK] Added ORACLE-026 helper functions")

# Start refresh near common startup locations.
if "oracle_026_start_live_dashboard_refresh()" not in text:
    text += "\n\ntry:\n    oracle_026_start_live_dashboard_refresh()\nexcept Exception as e:\n    print(f'[ORACLE-026] startup error: {e}')\n"
    print("[OK] Added ORACLE-026 startup call")

bot_file.write_text(text, encoding="utf-8")
print("[DONE] ORACLE-026 patch applied")