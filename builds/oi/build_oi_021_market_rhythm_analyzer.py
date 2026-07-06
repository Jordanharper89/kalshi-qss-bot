from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_021_market_rhythm_analyzer.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ANALYZER = OI_DIR / "market_rhythm_analyzer.py"

ANALYZER.write_text(textwrap.dedent(r'''
"""
OI-021 Market Rhythm Analyzer

Read-only Oracle Intelligence module.

Purpose:
- Learn market rhythm behavior from OPS historical SQLite data.
- Build hourly, daily, weekly, expiration, liquidity, spread, volume,
  volatility, and category-specific profiles.
- Provide proprietary market intelligence only.
- No trade execution.
"""

from __future__ import annotations

import sqlite3
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional


DEFAULT_DB_CANDIDATES = [
    Path("qseries_v2/ops/qseries_history.sqlite3"),
    Path("qseries_v2/data/qseries_history.sqlite3"),
    Path("qseries_history.sqlite3"),
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _bucket(values: List[float]) -> Dict[str, float]:
    values = [_safe_float(v) for v in values if v is not None]
    if not values:
        return {
            "count": 0,
            "avg": 0.0,
            "min": 0.0,
            "max": 0.0,
            "std": 0.0,
        }

    return {
        "count": len(values),
        "avg": round(mean(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
        "std": round(pstdev(values), 6) if len(values) > 1 else 0.0,
    }


@dataclass
class RhythmSnapshot:
    module: str
    status: str
    generated_at: str
    database: Optional[str]
    rows_analyzed: int
    hourly_activity: Dict[str, Any]
    daily_activity: Dict[str, Any]
    weekly_activity: Dict[str, Any]
    expiration_behavior: Dict[str, Any]
    liquidity_curve: Dict[str, Any]
    spread_curve: Dict[str, Any]
    volume_curve: Dict[str, Any]
    volatility_curve: Dict[str, Any]
    category_patterns: Dict[str, Any]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRhythmAnalyzer:
    """
    Read-only analyzer for historical market behavior.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = self._resolve_db(db_path)
        self.last_snapshot: Optional[Dict[str, Any]] = None

    def _resolve_db(self, db_path: Optional[str]) -> Optional[Path]:
        if db_path:
            path = Path(db_path)
            return path if path.exists() else path

        for candidate in DEFAULT_DB_CANDIDATES:
            if candidate.exists():
                return candidate

        return DEFAULT_DB_CANDIDATES[0]

    def diagnostics(self) -> Dict[str, Any]:
        exists = bool(self.db_path and self.db_path.exists())
        return {
            "module": "OI-021 Market Rhythm Analyzer",
            "status": "ok" if exists else "waiting_for_history_db",
            "database": str(self.db_path) if self.db_path else None,
            "database_exists": exists,
            "last_snapshot_ready": self.last_snapshot is not None,
        }

    def analyze(self, limit: int = 50000) -> Dict[str, Any]:
        notes: List[str] = []

        if not self.db_path or not self.db_path.exists():
            snapshot = RhythmSnapshot(
                module="OI-021 Market Rhythm Analyzer",
                status="waiting_for_history_db",
                generated_at=self._now(),
                database=str(self.db_path) if self.db_path else None,
                rows_analyzed=0,
                hourly_activity={},
                daily_activity={},
                weekly_activity={},
                expiration_behavior={},
                liquidity_curve={},
                spread_curve={},
                volume_curve={},
                volatility_curve={},
                category_patterns={},
                notes=["Historical database not found yet. Analyzer is ready and read-only."],
            ).to_dict()
            self.last_snapshot = snapshot
            return snapshot

        rows = self._load_rows(limit=limit, notes=notes)

        hourly = self._profile_by_time(rows, "hour")
        daily = self._profile_by_time(rows, "date")
        weekly = self._profile_by_time(rows, "weekday")
        expiration = self._expiration_behavior(rows)
        liquidity = self._curve(rows, "liquidity")
        spread = self._curve(rows, "spread")
        volume = self._curve(rows, "volume")
        volatility = self._volatility_curve(rows)
        categories = self._category_patterns(rows)

        snapshot = RhythmSnapshot(
            module="OI-021 Market Rhythm Analyzer",
            status="ok",
            generated_at=self._now(),
            database=str(self.db_path),
            rows_analyzed=len(rows),
            hourly_activity=hourly,
            daily_activity=daily,
            weekly_activity=weekly,
            expiration_behavior=expiration,
            liquidity_curve=liquidity,
            spread_curve=spread,
            volume_curve=volume,
            volatility_curve=volatility,
            category_patterns=categories,
            notes=notes or ["Market rhythm analysis completed successfully."],
        ).to_dict()

        self.last_snapshot = snapshot
        return snapshot

    def get_snapshot(self) -> Dict[str, Any]:
        if self.last_snapshot is None:
            return self.analyze()
        return self.last_snapshot

    def oracle_insights(self) -> Dict[str, Any]:
        snap = self.get_snapshot()

        return {
            "module": "oracle_market_rhythm_insights",
            "status": snap.get("status"),
            "rows_analyzed": snap.get("rows_analyzed", 0),
            "best_activity_hours": self._top_keys(snap.get("hourly_activity", {}), "activity_score"),
            "strongest_liquidity_hours": self._top_keys(snap.get("liquidity_curve", {}), "avg"),
            "widest_spread_hours": self._top_keys(snap.get("spread_curve", {}), "avg"),
            "highest_volume_hours": self._top_keys(snap.get("volume_curve", {}), "avg"),
            "highest_volatility_hours": self._top_keys(snap.get("volatility_curve", {}), "avg"),
            "category_patterns": snap.get("category_patterns", {}),
            "read_only": True,
            "execution_allowed": False,
        }

    def _load_rows(self, limit: int, notes: List[str]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        try:
            tables = [
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            if not tables:
                notes.append("Historical database exists but contains no tables.")
                return []

            candidate_tables = [
                t for t in tables
                if any(k in t.lower() for k in ["market", "history", "snapshot", "record"])
            ] or tables

            for table in candidate_tables:
                try:
                    columns = [
                        c["name"]
                        for c in conn.execute(f"PRAGMA table_info({table})").fetchall()
                    ]

                    time_col = self._pick(columns, ["timestamp", "created_at", "recorded_at", "time", "updated_at"])
                    if not time_col:
                        continue

                    query = f"SELECT * FROM {table} ORDER BY {time_col} DESC LIMIT ?"
                    for row in conn.execute(query, (limit,)).fetchall():
                        mapped = self._normalize_row(dict(row), table)
                        if mapped:
                            rows.append(mapped)

                    if rows:
                        notes.append(f"Loaded historical rows from table: {table}")
                        break

                except Exception as exc:
                    notes.append(f"Skipped table {table}: {exc}")

        finally:
            conn.close()

        return rows[:limit]

    def _normalize_row(self, row: Dict[str, Any], table: str) -> Optional[Dict[str, Any]]:
        keys = list(row.keys())

        ts_key = self._pick(keys, ["timestamp", "created_at", "recorded_at", "time", "updated_at"])
        dt = _parse_dt(row.get(ts_key))
        if not dt:
            return None

        yes = _safe_float(row.get(self._pick(keys, ["yes_price", "yes_bid", "yes_ask", "price", "last_price"])))
        no = _safe_float(row.get(self._pick(keys, ["no_price", "no_bid", "no_ask"])))
        bid = _safe_float(row.get(self._pick(keys, ["bid", "best_bid", "yes_bid"])))
        ask = _safe_float(row.get(self._pick(keys, ["ask", "best_ask", "yes_ask"])))

        spread = _safe_float(row.get(self._pick(keys, ["spread", "bid_ask_spread"])))
        if spread == 0.0 and bid and ask:
            spread = abs(ask - bid)

        volume = _safe_float(row.get(self._pick(keys, ["volume", "volume_24h", "total_volume"])))
        liquidity = _safe_float(row.get(self._pick(keys, ["liquidity", "open_interest", "oi", "depth"])))

        category = row.get(self._pick(keys, ["category", "market_category", "event_category", "type"])) or "unknown"
        ticker = row.get(self._pick(keys, ["ticker", "market_ticker", "symbol"])) or ""
        expiration = row.get(self._pick(keys, ["expiration", "expiration_time", "close_time", "end_time"]))

        price = yes or row.get("price") or 0.0

        return {
            "source_table": table,
            "timestamp": dt,
            "hour": dt.hour,
            "date": dt.date().isoformat(),
            "weekday": dt.strftime("%A"),
            "category": str(category),
            "ticker": str(ticker),
            "price": _safe_float(price),
            "spread": spread,
            "volume": volume,
            "liquidity": liquidity,
            "expiration": _parse_dt(expiration),
        }

    def _profile_by_time(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for row in rows:
            group = str(row.get(key))
            grouped.setdefault(group, []).append(row)

        out = {}
        for group, items in grouped.items():
            activity_score = (
                len(items)
                + _bucket([r["volume"] for r in items])["avg"]
                + _bucket([r["liquidity"] for r in items])["avg"]
            )

            out[group] = {
                "records": len(items),
                "activity_score": round(activity_score, 6),
                "volume": _bucket([r["volume"] for r in items]),
                "liquidity": _bucket([r["liquidity"] for r in items]),
                "spread": _bucket([r["spread"] for r in items]),
            }

        return dict(sorted(out.items(), key=lambda kv: str(kv[0])))

    def _curve(self, rows: List[Dict[str, Any]], metric: str) -> Dict[str, Any]:
        grouped: Dict[str, List[float]] = {}
        for row in rows:
            grouped.setdefault(str(row["hour"]), []).append(_safe_float(row.get(metric)))

        return {
            hour: _bucket(values)
            for hour, values in sorted(grouped.items(), key=lambda kv: int(kv[0]))
        }

    def _volatility_curve(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        grouped: Dict[str, List[float]] = {}
        for row in rows:
            grouped.setdefault(str(row["hour"]), []).append(_safe_float(row.get("price")))

        out = {}
        for hour, prices in grouped.items():
            out[hour] = {
                "count": len(prices),
                "avg": round(pstdev(prices), 6) if len(prices) > 1 else 0.0,
                "min": round(min(prices), 6) if prices else 0.0,
                "max": round(max(prices), 6) if prices else 0.0,
                "std": round(pstdev(prices), 6) if len(prices) > 1 else 0.0,
            }

        return dict(sorted(out.items(), key=lambda kv: int(kv[0])))

    def _expiration_behavior(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        buckets = {
            "expires_under_1h": [],
            "expires_1h_to_6h": [],
            "expires_6h_to_24h": [],
            "expires_over_24h": [],
            "unknown_expiration": [],
        }

        for row in rows:
            exp = row.get("expiration")
            ts = row.get("timestamp")

            if not exp or not ts:
                buckets["unknown_expiration"].append(row)
                continue

            hours = (exp - ts).total_seconds() / 3600

            if hours < 1:
                buckets["expires_under_1h"].append(row)
            elif hours < 6:
                buckets["expires_1h_to_6h"].append(row)
            elif hours < 24:
                buckets["expires_6h_to_24h"].append(row)
            else:
                buckets["expires_over_24h"].append(row)

        return {
            name: {
                "records": len(items),
                "volume": _bucket([r["volume"] for r in items]),
                "liquidity": _bucket([r["liquidity"] for r in items]),
                "spread": _bucket([r["spread"] for r in items]),
                "volatility": _bucket([r["price"] for r in items]),
            }
            for name, items in buckets.items()
        }

    def _category_patterns(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for row in rows:
            grouped.setdefault(row.get("category", "unknown"), []).append(row)

        out = {}
        for category, items in grouped.items():
            out[category] = {
                "records": len(items),
                "top_hours": self._top_hour_for_items(items),
                "volume": _bucket([r["volume"] for r in items]),
                "liquidity": _bucket([r["liquidity"] for r in items]),
                "spread": _bucket([r["spread"] for r in items]),
                "price_volatility": round(pstdev([r["price"] for r in items]), 6) if len(items) > 1 else 0.0,
            }

        return dict(sorted(out.items(), key=lambda kv: kv[1]["records"], reverse=True))

    def _top_hour_for_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in items:
            grouped.setdefault(str(row["hour"]), []).append(row)

        scored = []
        for hour, rows in grouped.items():
            scored.append({
                "hour": hour,
                "records": len(rows),
                "activity_score": round(
                    len(rows)
                    + _bucket([r["volume"] for r in rows])["avg"]
                    + _bucket([r["liquidity"] for r in rows])["avg"],
                    6,
                ),
            })

        return sorted(scored, key=lambda x: x["activity_score"], reverse=True)[:5]

    def _top_keys(self, data: Dict[str, Any], field: str) -> List[Dict[str, Any]]:
        scored = []

        for key, value in data.items():
            if isinstance(value, dict):
                score = _safe_float(value.get(field))
                scored.append({"key": key, "score": score})

        return sorted(scored, key=lambda x: x["score"], reverse=True)[:5]

    def _pick(self, keys: List[str], candidates: List[str]) -> Optional[str]:
        lower = {k.lower(): k for k in keys}
        for candidate in candidates:
            if candidate.lower() in lower:
                return lower[candidate.lower()]
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_market_rhythm_analyzer = MarketRhythmAnalyzer()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.market_rhythm_analyzer import MarketRhythmAnalyzer


def build_test_db(path: Path):
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(str(path))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE market_history (
            timestamp TEXT,
            ticker TEXT,
            category TEXT,
            yes_price REAL,
            bid REAL,
            ask REAL,
            volume REAL,
            liquidity REAL,
            expiration TEXT
        )
    """)

    base = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)

    rows = []
    for i in range(48):
        ts = base - timedelta(hours=i)
        exp = ts + timedelta(hours=(i % 12) + 1)

        rows.append((
            ts.isoformat(),
            f"TEST-{i}",
            "crypto" if i % 2 == 0 else "sports",
            40 + (i % 20),
            38 + (i % 10),
            42 + (i % 10),
            100 + i * 5,
            500 + i * 10,
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_021_market_rhythm_analyzer():
    db_path = Path("test_oi_021_history.sqlite3")
    build_test_db(db_path)

    analyzer = MarketRhythmAnalyzer(str(db_path))

    diagnostics = analyzer.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True

    snapshot = analyzer.analyze()
    assert snapshot["status"] == "ok"
    assert snapshot["rows_analyzed"] == 48
    assert snapshot["hourly_activity"]
    assert snapshot["daily_activity"]
    assert snapshot["weekly_activity"]
    assert snapshot["expiration_behavior"]
    assert snapshot["liquidity_curve"]
    assert snapshot["spread_curve"]
    assert snapshot["volume_curve"]
    assert snapshot["volatility_curve"]
    assert snapshot["category_patterns"]
    assert snapshot["category_patterns"]["crypto"]["records"] == 24
    assert snapshot["category_patterns"]["sports"]["records"] == 24

    insights = analyzer.oracle_insights()
    assert insights["read_only"] is True
    assert insights["execution_allowed"] is False
    assert insights["best_activity_hours"]

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-021 Market Rhythm Analyzer")
    print({
        "rows_analyzed": snapshot["rows_analyzed"],
        "categories": list(snapshot["category_patterns"].keys()),
        "top_activity_hours": insights["best_activity_hours"][:3],
    })


if __name__ == "__main__":
    test_oi_021_market_rhythm_analyzer()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
if INIT.exists():
    content = INIT.read_text(encoding="utf-8")
else:
    content = ""

line = "from .market_rhythm_analyzer import MarketRhythmAnalyzer, oracle_market_rhythm_analyzer\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-021 INSTALLER")
print(" Market Rhythm Analyzer")
print("========================================")
print(f"[OK] Wrote {ANALYZER}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-021 installed")
print("")
print("Run:")
print("python test_oi_021_market_rhythm_analyzer.py")