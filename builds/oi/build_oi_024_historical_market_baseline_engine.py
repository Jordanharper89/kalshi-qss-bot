from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_024_historical_market_baseline_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "historical_market_baseline_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-024 Historical Market Baseline Engine

Read-only Oracle Intelligence module.

Purpose:
- Build statistical historical baselines from OPS historical SQLite data.
- Compare live market snapshots against category/hour/weekday/expiration norms.
- Produce mean, median, min, max, variance, std, percentile bands, deviation, and percentile rank.
- No execution.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Dict, List, Optional


DEFAULT_DB_CANDIDATES = [
    Path("qseries_v2/ops/qseries_history.sqlite3"),
    Path("qseries_v2/data/qseries_history.sqlite3"),
    Path("qseries_history.sqlite3"),
]


METRICS = ["liquidity", "spread", "volume", "volatility", "yes_price", "no_price"]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
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


def _percentile(sorted_values: List[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return round(sorted_values[0], 6)

    k = (len(sorted_values) - 1) * (pct / 100.0)
    lower = int(k)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = k - lower
    value = sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    return round(value, 6)


def _stats(values: List[float]) -> Dict[str, Any]:
    clean = sorted([_safe_float(v) for v in values if v is not None])

    if not clean:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "min": 0.0,
            "max": 0.0,
            "variance": 0.0,
            "std": 0.0,
            "p10": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "normal_low": 0.0,
            "normal_high": 0.0,
        }

    avg = mean(clean)
    std = pstdev(clean) if len(clean) > 1 else 0.0

    return {
        "count": len(clean),
        "mean": round(avg, 6),
        "median": round(median(clean), 6),
        "min": round(min(clean), 6),
        "max": round(max(clean), 6),
        "variance": round(std ** 2, 6),
        "std": round(std, 6),
        "p10": _percentile(clean, 10),
        "p25": _percentile(clean, 25),
        "p50": _percentile(clean, 50),
        "p75": _percentile(clean, 75),
        "p90": _percentile(clean, 90),
        "normal_low": _percentile(clean, 25),
        "normal_high": _percentile(clean, 75),
    }


def _percentile_rank(values: List[float], current: float) -> float:
    clean = sorted([_safe_float(v) for v in values if v is not None])
    if not clean:
        return 0.0
    below_or_equal = len([v for v in clean if v <= current])
    return round((below_or_equal / len(clean)) * 100.0, 4)


def _deviation_pct(current: float, expected: float) -> float:
    if expected == 0:
        return 0.0
    return round(((current - expected) / expected) * 100.0, 4)


@dataclass
class BaselineSnapshot:
    module: str
    status: str
    generated_at: str
    database: Optional[str]
    rows_analyzed: int
    rolling_windows: Dict[str, Any]
    category_baselines: Dict[str, Any]
    hourly_baselines: Dict[str, Any]
    weekday_baselines: Dict[str, Any]
    expiration_baselines: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalMarketBaselineEngine:
    """
    Builds historical baselines and compares live markets against historical norms.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = self._resolve_db(db_path)
        self.last_snapshot: Optional[Dict[str, Any]] = None

    def diagnostics(self) -> Dict[str, Any]:
        exists = bool(self.db_path and self.db_path.exists())
        return {
            "module": "OI-024 Historical Market Baseline Engine",
            "status": "ok" if exists else "waiting_for_history_db",
            "database": str(self.db_path) if self.db_path else None,
            "database_exists": exists,
            "last_snapshot_ready": self.last_snapshot is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def get_baseline(self, limit: int = 100000) -> Dict[str, Any]:
        notes: List[str] = []

        if not self.db_path or not self.db_path.exists():
            snapshot = BaselineSnapshot(
                module="OI-024 Historical Market Baseline Engine",
                status="waiting_for_history_db",
                generated_at=self._now(),
                database=str(self.db_path) if self.db_path else None,
                rows_analyzed=0,
                rolling_windows={},
                category_baselines={},
                hourly_baselines={},
                weekday_baselines={},
                expiration_baselines={},
                notes=["Historical database not found yet. Baseline engine is ready and read-only."],
                read_only=True,
                execution_allowed=False,
            ).to_dict()
            self.last_snapshot = snapshot
            return snapshot

        rows = self._load_rows(limit=limit, notes=notes)

        snapshot = BaselineSnapshot(
            module="OI-024 Historical Market Baseline Engine",
            status="ok",
            generated_at=self._now(),
            database=str(self.db_path),
            rows_analyzed=len(rows),
            rolling_windows=self._rolling_windows(rows),
            category_baselines=self._group_baselines(rows, "category"),
            hourly_baselines=self._group_baselines(rows, "hour"),
            weekday_baselines=self._group_baselines(rows, "weekday"),
            expiration_baselines=self._group_baselines(rows, "expiration_window"),
            notes=notes or ["Historical market baselines completed successfully."],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_snapshot = snapshot
        return snapshot

    def category_baseline(self, category: str) -> Dict[str, Any]:
        baseline = self.last_snapshot or self.get_baseline()
        return baseline.get("category_baselines", {}).get(str(category), {})

    def hourly_baseline(self, hour: Any) -> Dict[str, Any]:
        baseline = self.last_snapshot or self.get_baseline()
        return baseline.get("hourly_baselines", {}).get(str(hour), {})

    def compare_live_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        baseline = self.last_snapshot or self.get_baseline()

        category = str(market.get("category", "unknown"))
        timestamp = _parse_dt(market.get("timestamp")) or datetime.now(timezone.utc)
        hour = str(timestamp.hour)
        weekday = timestamp.strftime("%A")

        expiration = _parse_dt(
            market.get("expiration")
            or market.get("expiration_time")
            or market.get("close_time")
            or market.get("end_time")
        )

        expiration_window = self._expiration_window(timestamp, expiration)

        comparisons = {
            "category": self._compare_group(market, baseline.get("category_baselines", {}).get(category, {})),
            "hour": self._compare_group(market, baseline.get("hourly_baselines", {}).get(hour, {})),
            "weekday": self._compare_group(market, baseline.get("weekday_baselines", {}).get(weekday, {})),
            "expiration_window": self._compare_group(
                market,
                baseline.get("expiration_baselines", {}).get(expiration_window, {}),
            ),
        }

        score = self._abnormality_score(comparisons)

        return {
            "module": "OI-024 Historical Market Baseline Engine",
            "status": baseline.get("status", "unknown"),
            "market": {
                "ticker": market.get("ticker") or market.get("market_ticker") or market.get("symbol"),
                "category": category,
                "hour": hour,
                "weekday": weekday,
                "expiration_window": expiration_window,
            },
            "comparisons": comparisons,
            "abnormality_score": score,
            "interpretation": self._interpret(score),
            "read_only": True,
            "execution_allowed": False,
        }

    def _resolve_db(self, db_path: Optional[str]) -> Optional[Path]:
        if db_path:
            return Path(db_path)

        for candidate in DEFAULT_DB_CANDIDATES:
            if candidate.exists():
                return candidate

        return DEFAULT_DB_CANDIDATES[0]

    def _load_rows(self, limit: int, notes: List[str]) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows: List[Dict[str, Any]] = []

        try:
            tables = [
                r["name"]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]

            candidate_tables = [
                t for t in tables
                if any(k in t.lower() for k in ["market", "history", "snapshot", "record"])
            ] or tables

            for table in candidate_tables:
                try:
                    columns = [c["name"] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
                    time_col = self._pick(columns, ["timestamp", "created_at", "recorded_at", "time", "updated_at"])
                    if not time_col:
                        continue

                    query = f"SELECT * FROM {table} ORDER BY {time_col} DESC LIMIT ?"
                    for row in conn.execute(query, (limit,)).fetchall():
                        normalized = self._normalize_row(dict(row), table)
                        if normalized:
                            rows.append(normalized)

                    if rows:
                        notes.append(f"Loaded baseline rows from table: {table}")
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

        bid = _safe_float(row.get(self._pick(keys, ["bid", "best_bid", "yes_bid"])))
        ask = _safe_float(row.get(self._pick(keys, ["ask", "best_ask", "yes_ask"])))

        spread = _safe_float(row.get(self._pick(keys, ["spread", "bid_ask_spread"])))
        if spread == 0.0 and bid and ask:
            spread = abs(ask - bid)

        yes_price = _safe_float(row.get(self._pick(keys, ["yes_price", "yes_bid", "yes_ask", "price", "last_price"])))
        no_price = _safe_float(row.get(self._pick(keys, ["no_price", "no_bid", "no_ask"])))
        volume = _safe_float(row.get(self._pick(keys, ["volume", "volume_24h", "total_volume"])))
        liquidity = _safe_float(row.get(self._pick(keys, ["liquidity", "open_interest", "oi", "depth"])))

        expiration = _parse_dt(row.get(self._pick(keys, ["expiration", "expiration_time", "close_time", "end_time"])))

        return {
            "source_table": table,
            "timestamp": dt,
            "category": str(row.get(self._pick(keys, ["category", "market_category", "event_category", "type"])) or "unknown"),
            "hour": str(dt.hour),
            "weekday": dt.strftime("%A"),
            "expiration_window": self._expiration_window(dt, expiration),
            "ticker": str(row.get(self._pick(keys, ["ticker", "market_ticker", "symbol"])) or ""),
            "liquidity": liquidity,
            "spread": spread,
            "volume": volume,
            "volatility": yes_price,
            "yes_price": yes_price,
            "no_price": no_price,
        }

    def _rolling_windows(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not rows:
            return {}

        latest = max(r["timestamp"] for r in rows)

        windows = {
            "last_24h": latest - timedelta(hours=24),
            "last_7d": latest - timedelta(days=7),
            "last_30d": latest - timedelta(days=30),
            "all_time": None,
        }

        out = {}
        for name, start in windows.items():
            subset = rows if start is None else [r for r in rows if r["timestamp"] >= start]
            out[name] = self._metric_baseline(subset)

        return out

    def _group_baselines(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for row in rows:
            grouped.setdefault(str(row.get(key, "unknown")), []).append(row)

        return {
            group: self._metric_baseline(items)
            for group, items in sorted(grouped.items(), key=lambda kv: str(kv[0]))
        }

    def _metric_baseline(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "records": len(rows),
            "metrics": {
                metric: _stats([r.get(metric, 0.0) for r in rows])
                for metric in METRICS
            },
        }

    def _compare_group(self, market: Dict[str, Any], group_baseline: Dict[str, Any]) -> Dict[str, Any]:
        metrics = group_baseline.get("metrics", {})
        out = {}

        for metric in METRICS:
            current = self._extract_market_metric(market, metric)
            stat = metrics.get(metric, {})
            expected = _safe_float(stat.get("mean"))
            values_count = int(stat.get("count", 0) or 0)

            out[metric] = {
                "current": round(current, 6),
                "expected": round(expected, 6),
                "deviation_pct": _deviation_pct(current, expected),
                "normal_low": _safe_float(stat.get("normal_low")),
                "normal_high": _safe_float(stat.get("normal_high")),
                "std": _safe_float(stat.get("std")),
                "sample_size": values_count,
                "is_abnormal": self._is_abnormal(current, stat),
            }

        return out

    def _extract_market_metric(self, market: Dict[str, Any], metric: str) -> float:
        if metric == "yes_price":
            return _safe_float(market.get("yes_price") or market.get("yes_bid") or market.get("price") or market.get("last_price"))
        if metric == "no_price":
            return _safe_float(market.get("no_price") or market.get("no_bid"))
        if metric == "spread":
            spread = _safe_float(market.get("spread") or market.get("bid_ask_spread"))
            if spread:
                return spread
            bid = _safe_float(market.get("bid") or market.get("best_bid") or market.get("yes_bid"))
            ask = _safe_float(market.get("ask") or market.get("best_ask") or market.get("yes_ask"))
            return abs(ask - bid) if bid and ask else 0.0

        return _safe_float(market.get(metric))

    def _is_abnormal(self, current: float, stat: Dict[str, Any]) -> bool:
        if not stat or int(stat.get("count", 0) or 0) == 0:
            return False
        low = _safe_float(stat.get("p10"))
        high = _safe_float(stat.get("p90"))
        return current < low or current > high

    def _abnormality_score(self, comparisons: Dict[str, Any]) -> Dict[str, Any]:
        abnormal = 0
        total = 0
        deviations = []

        for group in comparisons.values():
            for metric_data in group.values():
                total += 1
                if metric_data.get("is_abnormal"):
                    abnormal += 1
                deviations.append(abs(_safe_float(metric_data.get("deviation_pct"))))

        score = 0.0
        if total:
            score = (abnormal / total) * 70.0 + min((sum(deviations) / max(len(deviations), 1)) / 2.0, 30.0)

        score = round(score, 4)

        if score >= 75:
            label = "extreme"
        elif score >= 50:
            label = "high"
        elif score >= 25:
            label = "moderate"
        else:
            label = "normal"

        return {
            "score": score,
            "label": label,
            "abnormal_metrics": abnormal,
            "metrics_checked": total,
        }

    def _interpret(self, score: Dict[str, Any]) -> str:
        label = score.get("label")
        if label == "extreme":
            return "Current market behavior is extremely unusual versus historical baselines."
        if label == "high":
            return "Current market behavior is meaningfully unusual versus historical baselines."
        if label == "moderate":
            return "Current market behavior shows moderate deviation from historical baselines."
        return "Current market behavior is broadly within historical baseline ranges."

    def _expiration_window(self, timestamp: datetime, expiration: Optional[datetime]) -> str:
        if not expiration:
            return "unknown_expiration"

        hours = (expiration - timestamp).total_seconds() / 3600.0

        if hours < 1:
            return "expires_under_1h"
        if hours < 6:
            return "expires_1h_to_6h"
        if hours < 24:
            return "expires_6h_to_24h"
        return "expires_over_24h"

    def _pick(self, keys: List[str], candidates: List[str]) -> Optional[str]:
        lower = {k.lower(): k for k in keys}
        for candidate in candidates:
            if candidate.lower() in lower:
                return lower[candidate.lower()]
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_market_baseline_engine = HistoricalMarketBaselineEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.historical_market_baseline_engine import HistoricalMarketBaselineEngine


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
            no_price REAL,
            bid REAL,
            ask REAL,
            volume REAL,
            liquidity REAL,
            expiration TEXT
        )
    """)

    base = datetime(2026, 6, 29, 14, 0, tzinfo=timezone.utc)

    rows = []
    for i in range(120):
        ts = base - timedelta(hours=i % 48)
        category = "crypto" if i < 80 else "sports"
        exp = ts + timedelta(hours=(i % 12) + 1)

        rows.append((
            ts.isoformat(),
            f"TEST-{i}",
            category,
            45 + (i % 10),
            55 - (i % 10),
            43 + (i % 5),
            47 + (i % 5),
            100 + i,
            1000 + (i * 10),
            exp.isoformat(),
        ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_024_historical_market_baseline_engine():
    db_path = Path("test_oi_024_history.sqlite3")
    build_test_db(db_path)

    engine = HistoricalMarketBaselineEngine(str(db_path))

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    baseline = engine.get_baseline()
    assert baseline["status"] == "ok"
    assert baseline["rows_analyzed"] == 120
    assert baseline["rolling_windows"]["last_24h"]["records"] > 0
    assert baseline["rolling_windows"]["last_7d"]["records"] == 120
    assert baseline["category_baselines"]["crypto"]["records"] == 80
    assert baseline["category_baselines"]["sports"]["records"] == 40
    assert baseline["hourly_baselines"]
    assert baseline["weekday_baselines"]
    assert baseline["expiration_baselines"]
    assert baseline["read_only"] is True
    assert baseline["execution_allowed"] is False

    crypto_baseline = engine.category_baseline("crypto")
    assert crypto_baseline["records"] == 80
    assert crypto_baseline["metrics"]["liquidity"]["mean"] > 0
    assert crypto_baseline["metrics"]["spread"]["std"] >= 0

    hourly_baseline = engine.hourly_baseline("14")
    assert "metrics" in hourly_baseline

    live_market = {
        "ticker": "TEST-LIVE",
        "category": "crypto",
        "timestamp": datetime(2026, 6, 29, 14, 30, tzinfo=timezone.utc).isoformat(),
        "expiration": datetime(2026, 6, 29, 18, 30, tzinfo=timezone.utc).isoformat(),
        "yes_price": 90,
        "no_price": 10,
        "bid": 88,
        "ask": 92,
        "volume": 5000,
        "liquidity": 10000,
    }

    comparison = engine.compare_live_market(live_market)
    assert comparison["status"] == "ok"
    assert comparison["market"]["category"] == "crypto"
    assert comparison["comparisons"]["category"]["liquidity"]["current"] == 10000
    assert comparison["abnormality_score"]["metrics_checked"] > 0
    assert comparison["read_only"] is True
    assert comparison["execution_allowed"] is False

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-024 Historical Market Baseline Engine")
    print({
        "rows_analyzed": baseline["rows_analyzed"],
        "categories": list(baseline["category_baselines"].keys()),
        "comparison_label": comparison["abnormality_score"]["label"],
        "comparison_score": comparison["abnormality_score"]["score"],
    })


if __name__ == "__main__":
    test_oi_024_historical_market_baseline_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .historical_market_baseline_engine import HistoricalMarketBaselineEngine, oracle_market_baseline_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-024 INSTALLER")
print(" Historical Market Baseline Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-024 installed")
print("")
print("Run:")
print("python test_oi_024_historical_market_baseline_engine.py")