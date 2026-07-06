"""
OPS-003 — Persistent Historical Data Store

Purpose:
- Store live market observations over time.
- Give Oracle memory beyond the latest snapshot.
- Build the foundation for rhythm analysis, volume timing, historical edges, and learning.

Storage:
- SQLite local database
- No external database required
- Read/write storage only
- No trade execution
"""

import json
import time
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


class HistoricalDataStoreError(Exception):
    pass


class HistoricalDataStore:
    def __init__(self, db_path: str = "qseries_v2/data/qseries_history.sqlite3", event_bus: Any = None):
        self.db_path = Path(db_path)
        self.event_bus = event_bus
        self._lock = threading.RLock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        if self.event_bus is None:
            return

        try:
            if hasattr(self.event_bus, "publish"):
                self.event_bus.publish(event_type, payload)
            elif hasattr(self.event_bus, "emit"):
                self.event_bus.emit(event_type, payload)
        except Exception:
            pass

    def _connect(self):
        return sqlite3.connect(str(self.db_path), timeout=30)

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS market_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observed_at REAL NOT NULL,
                    ticker TEXT NOT NULL,
                    event_ticker TEXT,
                    series_ticker TEXT,
                    category TEXT,
                    title TEXT,
                    status TEXT,
                    yes_bid INTEGER,
                    yes_ask INTEGER,
                    no_bid INTEGER,
                    no_ask INTEGER,
                    last_price INTEGER,
                    volume INTEGER,
                    open_interest INTEGER,
                    liquidity INTEGER,
                    close_time TEXT,
                    expiration_time TEXT,
                    raw_json TEXT
                )
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_observations_ticker_time
                ON market_observations(ticker, observed_at)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_observations_category_time
                ON market_observations(category, observed_at)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_observations_event_time
                ON market_observations(event_ticker, observed_at)
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS snapshot_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observed_at REAL NOT NULL,
                    source TEXT,
                    market_count INTEGER,
                    inserted_count INTEGER,
                    duration_seconds REAL,
                    status TEXT,
                    error TEXT,
                    metadata_json TEXT
                )
            """)

            conn.commit()
            conn.close()

    def record_market_observation(self, market: Dict[str, Any], observed_at: Optional[float] = None) -> Dict[str, Any]:
        observed_at = observed_at or time.time()

        ticker = market.get("ticker")
        if not ticker:
            raise HistoricalDataStoreError("Market observation requires ticker.")

        series_ticker = market.get("series_ticker") or self._infer_series_ticker(ticker)

        with self._lock:
            conn = self._connect()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO market_observations (
                    observed_at,
                    ticker,
                    event_ticker,
                    series_ticker,
                    category,
                    title,
                    status,
                    yes_bid,
                    yes_ask,
                    no_bid,
                    no_ask,
                    last_price,
                    volume,
                    open_interest,
                    liquidity,
                    close_time,
                    expiration_time,
                    raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                observed_at,
                ticker,
                market.get("event_ticker"),
                series_ticker,
                market.get("category"),
                market.get("title"),
                market.get("status"),
                market.get("yes_bid"),
                market.get("yes_ask"),
                market.get("no_bid"),
                market.get("no_ask"),
                market.get("last_price"),
                market.get("volume"),
                market.get("open_interest"),
                market.get("liquidity"),
                market.get("close_time"),
                market.get("expiration_time"),
                json.dumps(market, default=str),
            ))

            conn.commit()
            row_id = cur.lastrowid
            conn.close()

        return {
            "status": "ok",
            "id": row_id,
            "ticker": ticker,
            "observed_at": observed_at,
        }

    def record_snapshot(self, markets: List[Dict[str, Any]], source: str = "market_cache", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        started = time.time()
        observed_at = started
        inserted = 0
        error = None
        status = "ok"

        try:
            with self._lock:
                conn = self._connect()
                cur = conn.cursor()

                rows = []
                for market in markets:
                    ticker = market.get("ticker")
                    if not ticker:
                        continue

                    rows.append((
                        observed_at,
                        ticker,
                        market.get("event_ticker"),
                        market.get("series_ticker") or self._infer_series_ticker(ticker),
                        market.get("category"),
                        market.get("title"),
                        market.get("status"),
                        market.get("yes_bid"),
                        market.get("yes_ask"),
                        market.get("no_bid"),
                        market.get("no_ask"),
                        market.get("last_price"),
                        market.get("volume"),
                        market.get("open_interest"),
                        market.get("liquidity"),
                        market.get("close_time"),
                        market.get("expiration_time"),
                        json.dumps(market, default=str),
                    ))

                cur.executemany("""
                    INSERT INTO market_observations (
                        observed_at,
                        ticker,
                        event_ticker,
                        series_ticker,
                        category,
                        title,
                        status,
                        yes_bid,
                        yes_ask,
                        no_bid,
                        no_ask,
                        last_price,
                        volume,
                        open_interest,
                        liquidity,
                        close_time,
                        expiration_time,
                        raw_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)

                inserted = len(rows)
                duration = time.time() - started

                cur.execute("""
                    INSERT INTO snapshot_runs (
                        observed_at,
                        source,
                        market_count,
                        inserted_count,
                        duration_seconds,
                        status,
                        error,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    observed_at,
                    source,
                    len(markets),
                    inserted,
                    duration,
                    status,
                    error,
                    json.dumps(metadata or {}, default=str),
                ))

                conn.commit()
                conn.close()

        except Exception as exc:
            status = "error"
            error = str(exc)
            duration = time.time() - started

            with self._lock:
                conn = self._connect()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO snapshot_runs (
                        observed_at,
                        source,
                        market_count,
                        inserted_count,
                        duration_seconds,
                        status,
                        error,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    observed_at,
                    source,
                    len(markets),
                    inserted,
                    duration,
                    status,
                    error,
                    json.dumps(metadata or {}, default=str),
                ))
                conn.commit()
                conn.close()

        result = {
            "module": "ops_003_historical_data_store",
            "status": status,
            "source": source,
            "market_count": len(markets),
            "inserted_count": inserted,
            "duration_seconds": round(duration, 4),
            "observed_at": observed_at,
            "error": error,
        }

        self._emit("ops.history.snapshot.recorded", result)
        return result

    def latest_for_ticker(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT *
                FROM market_observations
                WHERE ticker = ?
                ORDER BY observed_at DESC
                LIMIT ?
            """, (ticker, int(limit)))
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

        return rows

    def count_observations(self) -> int:
        with self._lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM market_observations")
            count = cur.fetchone()[0]
            conn.close()
        return int(count)

    def recent_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT *
                FROM snapshot_runs
                ORDER BY observed_at DESC
                LIMIT ?
            """, (int(limit),))
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()

        return rows

    def _infer_series_ticker(self, ticker: str) -> Optional[str]:
        if not ticker or "-" not in ticker:
            return None
        return ticker.split("-")[0]

    def diagnostics(self) -> Dict[str, Any]:
        snapshot_count = 0

        with self._lock:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM market_observations")
            obs_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM snapshot_runs")
            snapshot_count = cur.fetchone()[0]
            conn.close()

        return {
            "module": "ops_003_historical_data_store",
            "status": "ok",
            "db_path": str(self.db_path),
            "observation_count": int(obs_count),
            "snapshot_count": int(snapshot_count),
            "read_only_trading": True,
        }


def build_historical_data_store(
    db_path: str = "qseries_v2/data/qseries_history.sqlite3",
    event_bus: Any = None,
) -> HistoricalDataStore:
    return HistoricalDataStore(db_path=db_path, event_bus=event_bus)


if __name__ == "__main__":
    store = build_historical_data_store()
    print(store.diagnostics())
