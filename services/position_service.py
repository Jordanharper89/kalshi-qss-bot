import json
import time
from pathlib import Path
from threading import RLock

from services.base_service import BaseService
from services.order_manager import order_manager, get_sell_price


POSITIONS_FILE = Path("positions.json")


class PositionService(BaseService):
    def __init__(self):
        super().__init__("position_service")
        self._lock = RLock()
        self.positions_file = POSITIONS_FILE
        self.load_count = 0
        self.save_count = 0
        self.update_count = 0

    def start(self):
        self.mark_started()

    def stop(self):
        self.mark_stopped()

    def load_positions(self):
        with self._lock:
            self.load_count += 1

            if not self.positions_file.exists():
                return {}

            try:
                with open(self.positions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                return data if isinstance(data, dict) else {}

            except Exception:
                return {}

    def save_positions(self, positions):
        with self._lock:
            with open(self.positions_file, "w", encoding="utf-8") as f:
                json.dump(positions, f, indent=2)

            self.save_count += 1

    def get_position(self, ticker):
        ticker = str(ticker).upper().strip()
        positions = self.load_positions()
        return positions.get(ticker)

    def all_positions(self):
        return self.load_positions()

    def update_position(self, ticker, updates):
        ticker = str(ticker).upper().strip()
        positions = self.load_positions()

        current = positions.get(ticker, {})
        current.update(updates)
        current["ticker"] = ticker
        current["updated_at"] = time.time()

        positions[ticker] = current
        self.save_positions(positions)

        with self._lock:
            self.update_count += 1

        return current

    def remove_position(self, ticker):
        ticker = str(ticker).upper().strip()
        positions = self.load_positions()

        removed = positions.pop(ticker, None)
        self.save_positions(positions)

        return removed

    def current_price(self, ticker, side="YES"):
        market = order_manager.get_market(ticker)

        if not market:
            return None

        return get_sell_price(market, side)

    def refresh_position(self, ticker):
        ticker = str(ticker).upper().strip()
        position = self.get_position(ticker)

        if not position:
            return None

        side = position.get("side", "YES")
        entry_price = position.get("entry_price")
        current_price = self.current_price(ticker, side)

        if current_price is None or entry_price is None:
            return position

        try:
            entry_price = float(entry_price)
            current_price = float(current_price)
            change_pct = ((current_price - entry_price) / entry_price) * 100
        except Exception:
            change_pct = None

        updates = {
            "current_price": current_price,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "last_checked": time.time(),
        }

        return self.update_position(ticker, updates)

    def refresh_all_positions(self):
        positions = self.load_positions()
        refreshed = {}

        for ticker in positions.keys():
            item = self.refresh_position(ticker)
            if item:
                refreshed[ticker] = item

        return refreshed

    def diagnostics(self):
        data = super().diagnostics()
        data.update(
            {
                "positions_file": str(self.positions_file),
                "positions_count": len(self.load_positions()),
                "load_count": self.load_count,
                "save_count": self.save_count,
                "update_count": self.update_count,
            }
        )
        return data


position_service = PositionService()