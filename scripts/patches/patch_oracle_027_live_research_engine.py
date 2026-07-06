from pathlib import Path

root = Path.cwd()
engine_file = root / "oracle_research_engine.py"
bot_file = root / "telegram_bot.py"

engine_code = r'''
"""
ORACLE-027 — Live Research Engine

Purpose:
- Run a lightweight Oracle research loop in the background.
- Maintain a shared market/opportunity snapshot cache.
- Let Oracle UI screens read cached data instead of rebuilding everything.
"""

import time
import threading


class OracleResearchEngine:
    def __init__(self, refresh_seconds=10):
        self.refresh_seconds = refresh_seconds
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        self.snapshot = {
            "status": "starting",
            "updated_at": None,
            "markets_checked": 0,
            "opportunities": [],
            "errors": [],
        }

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[ORACLE-027] Live research engine started")

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            try:
                self.refresh()
            except Exception as e:
                self._record_error(str(e))

            time.sleep(self.refresh_seconds)

    def refresh(self):
        """
        Safe first version:
        - Does not call APIs yet.
        - Prepares the shared cache structure.
        - Later builds will plug live market reads into this method.
        """
        with self.lock:
            self.snapshot["status"] = "running"
            self.snapshot["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.snapshot["markets_checked"] = self.snapshot.get("markets_checked", 0)
            self.snapshot["opportunities"] = self.snapshot.get("opportunities", [])
            self.snapshot["errors"] = self.snapshot.get("errors", [])[-10:]

    def _record_error(self, error):
        with self.lock:
            self.snapshot["status"] = "error"
            self.snapshot.setdefault("errors", []).append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": error,
            })
            self.snapshot["errors"] = self.snapshot["errors"][-10:]

    def get_snapshot(self):
        with self.lock:
            return dict(self.snapshot)

    def diagnostics_text(self):
        snap = self.get_snapshot()
        return (
            "ORACLE RESEARCH ENGINE\n\n"
            f"Status: {snap.get('status')}\n"
            f"Updated: {snap.get('updated_at')}\n"
            f"Markets checked: {snap.get('markets_checked')}\n"
            f"Opportunities: {len(snap.get('opportunities', []))}\n"
            f"Errors: {len(snap.get('errors', []))}"
        )


oracle_research_engine = OracleResearchEngine(refresh_seconds=10)
'''

engine_file.write_text(engine_code, encoding="utf-8")
print("[OK] Created oracle_research_engine.py")

if not bot_file.exists():
    print("[WARN] telegram_bot.py not found. Engine file created only.")
    raise SystemExit

text = bot_file.read_text(encoding="utf-8")

if "from oracle_research_engine import oracle_research_engine" not in text:
    text = "from oracle_research_engine import oracle_research_engine\n" + text
    print("[OK] Added ORACLE-027 import")

startup = '''
try:
    oracle_research_engine.start()
except Exception as e:
    print(f"[ORACLE-027] startup error: {e}")
'''

if "oracle_research_engine.start()" not in text:
    text += "\n\n# ORACLE-027 startup\n" + startup
    print("[OK] Added ORACLE-027 startup")

bot_file.write_text(text, encoding="utf-8")
print("[DONE] ORACLE-027 patch applied")