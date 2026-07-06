import json
import time
from pathlib import Path
from threading import RLock

from services.base_service import BaseService
from services.trade_journal import trade_journal


WATCHLIST_FILE = Path("oracle_watchlist.json")


class OracleWatchlist(BaseService):
    def __init__(self):
        super().__init__("oracle_watchlist")
        self._lock = RLock()
        self.watchlist_file = WATCHLIST_FILE
        self.read_count = 0
        self.write_count = 0

    def start(self):
        self.mark_started()

    def stop(self):
        self.mark_stopped()

    def _load(self):
        with self._lock:
            self.read_count += 1

            if not self.watchlist_file.exists():
                return {}

            try:
                with open(self.watchlist_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}

    def _save(self, data):
        with self._lock:
            with open(self.watchlist_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.write_count += 1

    def add(self, ticker, note=None):
        ticker = str(ticker).upper().strip()
        data = self._load()

        data[ticker] = {
            "ticker": ticker,
            "note": note or "",
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "active": True,
        }

        self._save(data)
        trade_journal.record_event("ORACLE_WATCH_ADDED", ticker, data[ticker])
        return data[ticker]

    def remove(self, ticker):
        ticker = str(ticker).upper().strip()
        data = self._load()
        removed = data.pop(ticker, None)
        self._save(data)

        trade_journal.record_event("ORACLE_WATCH_REMOVED", ticker, removed or {})
        return removed

    def get(self, ticker):
        ticker = str(ticker).upper().strip()
        return self._load().get(ticker)

    def all(self):
        return self._load()

    def text(self):
        data = self._load()

        if not data:
            return "ORACLE WATCHLIST\n\nNo watched markets yet."

        lines = ["ORACLE WATCHLIST", ""]

        for ticker, item in data.items():
            lines.append(ticker)
            if item.get("note"):
                lines.append(f"Note: {item.get('note')}")
            lines.append("")

        return "\n".join(lines).strip()

    def diagnostics(self):
        d = super().diagnostics()
        data = self._load()

        d.update(
            {
                "watchlist_file": str(self.watchlist_file),
                "watch_count": len(data),
                "reads": self.read_count,
                "writes": self.write_count,
            }
        )

        return d


oracle_watchlist = OracleWatchlist()