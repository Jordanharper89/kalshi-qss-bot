import json
import time
from pathlib import Path
from threading import RLock

from services.base_service import BaseService


JOURNAL_FILE = Path("trade_journal.json")


class TradeJournal(BaseService):
    def __init__(self):
        super().__init__("trade_journal")

        self._lock = RLock()

        self.journal_file = JOURNAL_FILE

        self.read_count = 0
        self.write_count = 0

    def start(self):
        self.mark_started()

    def stop(self):
        self.mark_stopped()

    def _load(self):
        with self._lock:
            self.read_count += 1

            if not self.journal_file.exists():
                return []

            try:
                with open(self.journal_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if isinstance(data, list):
                    return data

            except Exception:
                pass

            return []

    def _save(self, events):
        with self._lock:
            with open(self.journal_file, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2)

            self.write_count += 1

    def record_event(self, event_type, ticker=None, payload=None):
        events = self._load()

        event = {
            "timestamp": int(time.time()),
            "event": str(event_type),
            "ticker": str(ticker).upper().strip() if ticker else None,
            "payload": payload or {},
        }

        events.append(event)

        self._save(events)

        return event

    def recent(self, limit=25):
        return self._load()[-limit:]

    def by_ticker(self, ticker, limit=25):
        ticker = str(ticker).upper().strip()

        events = [
            x
            for x in self._load()
            if x.get("ticker") == ticker
        ]

        return events[-limit:]

    def diagnostics(self):
        d = super().diagnostics()

        d.update(
            {
                "journal_file": str(self.journal_file),
                "events": len(self._load()),
                "reads": self.read_count,
                "writes": self.write_count,
            }
        )

        return d


trade_journal = TradeJournal()