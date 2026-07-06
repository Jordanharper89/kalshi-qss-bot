from pathlib import Path
import textwrap

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
TEST_FILE = ROOT / "test_oi_030_historical_outcome_tracking_engine.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

ENGINE = OI_DIR / "historical_outcome_tracking_engine.py"

ENGINE.write_text(textwrap.dedent(r'''
"""
OI-030 Historical Outcome Tracking Engine

Purpose:
- Measure what happened after historically similar market states.
- Build forward outcome curves by horizon.
- Read-only Oracle Intelligence.
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

DEFAULT_HORIZONS_MINUTES = [5, 15, 30, 60, 120, 360, 720, 1440]


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
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _stats(values: List[float]) -> Dict[str, Any]:
    clean = [_safe_float(v) for v in values if v is not None]
    if not clean:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "best": 0.0,
            "worst": 0.0,
            "positive_frequency": 0.0,
        }

    return {
        "count": len(clean),
        "mean": round(mean(clean), 6),
        "median": round(median(clean), 6),
        "std": round(pstdev(clean), 6) if len(clean) > 1 else 0.0,
        "best": round(max(clean), 6),
        "worst": round(min(clean), 6),
        "positive_frequency": round(len([v for v in clean if v > 0]) / len(clean) * 100.0, 4),
    }

def _std(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    if len(clean) <= 1:
        return 0.0
    return round(pstdev(clean), 6)

@dataclass
class OutcomePacket:
    module: str
    status: str
    generated_at: str
    database: Optional[str]
    live_market: Dict[str, Any]
    matches_found: int
    horizons_minutes: List[int]
    outcome_curve: Dict[str, Any]
    horizon_statistics: Dict[str, Any]
    confidence: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalOutcomeTrackingEngine:
    """
    Tracks forward historical outcomes for similar market states.

    Analysis only. No trading or execution logic.
    """

    def __init__(self, db_path: Optional[str] = None, horizons_minutes: Optional[List[int]] = None):
        self.db_path = self._resolve_db(db_path)
        self.horizons_minutes = horizons_minutes or DEFAULT_HORIZONS_MINUTES
        self.last_packet: Optional[Dict[str, Any]] = None

    def diagnostics(self) -> Dict[str, Any]:
        exists = bool(self.db_path and self.db_path.exists())
        return {
            "module": "OI-030 Historical Outcome Tracking Engine",
            "status": "ok" if exists else "waiting_for_history_db",
            "database": str(self.db_path) if self.db_path else None,
            "database_exists": exists,
            "horizons_minutes": self.horizons_minutes,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def forward_outcomes(self, live_market: Dict[str, Any], limit: int = 100000, max_matches: int = 100) -> Dict[str, Any]:
        notes: List[str] = []

        if not self.db_path or not self.db_path.exists():
            packet = self._empty_packet("waiting_for_history_db", live_market, "Historical database not found.")
            self.last_packet = packet
            return packet

        rows = self._load_rows(limit=limit, notes=notes)

        if not rows:
            packet = self._empty_packet("waiting_for_history_rows", live_market, "No usable historical rows found.")
            self.last_packet = packet
            return packet

        live = self._normalize_live_market(live_market)
        matches = self._find_matches(live, rows, max_matches=max_matches)
        outcomes = self._calculate_outcomes(matches, rows)

        packet = OutcomePacket(
            module="OI-030 Historical Outcome Tracking Engine",
            status="ok",
            generated_at=self._now(),
            database=str(self.db_path),
            live_market=live,
            matches_found=len(matches),
            horizons_minutes=self.horizons_minutes,
            outcome_curve=self._outcome_curve(outcomes),
            horizon_statistics=outcomes,
            confidence=self._confidence(outcomes, len(matches)),
            notes=notes or ["Historical forward outcome analysis completed successfully."],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def outcome_curve(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.forward_outcomes(live_market).get("outcome_curve", {})

    def horizon_statistics(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.forward_outcomes(live_market).get("horizon_statistics", {})

    def analyze_pattern(self, pattern_id: Optional[str] = None) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-030 Historical Outcome Tracking Engine",
                "status": "no_outcome_run_yet",
                "pattern_id": pattern_id,
                "read_only": True,
                "execution_allowed": False,
            }

        return {
            "module": "OI-030 Historical Outcome Tracking Engine",
            "status": self.last_packet.get("status"),
            "pattern_id": pattern_id or "latest_pattern",
            "matches_found": self.last_packet.get("matches_found"),
            "outcome_curve": self.last_packet.get("outcome_curve"),
            "confidence": self.last_packet.get("confidence"),
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
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
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

                    query = f"SELECT * FROM {table} ORDER BY {time_col} ASC LIMIT ?"
                    for row in conn.execute(query, (limit,)).fetchall():
                        normalized = self._normalize_row(dict(row), table)
                        if normalized:
                            rows.append(normalized)

                    if rows:
                        notes.append(f"Loaded outcome rows from table: {table}")
                        break

                except Exception as exc:
                    notes.append(f"Skipped table {table}: {exc}")

        finally:
            conn.close()

        return sorted(rows[:limit], key=lambda r: r["timestamp"])

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

        return {
            "source_table": table,
            "timestamp": dt,
            "ticker": str(row.get(self._pick(keys, ["ticker", "market_ticker", "symbol"])) or ""),
            "category": str(row.get(self._pick(keys, ["category", "market_category", "event_category", "type"])) or "unknown"),
            "hour": str(dt.hour),
            "weekday": dt.strftime("%A"),
            "yes_price": yes_price,
            "no_price": no_price,
            "spread": spread,
            "volume": _safe_float(row.get(self._pick(keys, ["volume", "volume_24h", "total_volume"]))),
            "liquidity": _safe_float(row.get(self._pick(keys, ["liquidity", "open_interest", "oi", "depth"]))),
            "volatility": yes_price,
        }

    def _normalize_live_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        ts = _parse_dt(market.get("timestamp")) or datetime.now(timezone.utc)

        bid = _safe_float(market.get("bid") or market.get("best_bid") or market.get("yes_bid"))
        ask = _safe_float(market.get("ask") or market.get("best_ask") or market.get("yes_ask"))

        spread = _safe_float(market.get("spread") or market.get("bid_ask_spread"))
        if spread == 0.0 and bid and ask:
            spread = abs(ask - bid)

        yes_price = _safe_float(market.get("yes_price") or market.get("yes_bid") or market.get("price") or market.get("last_price"))
        no_price = _safe_float(market.get("no_price") or market.get("no_bid"))

        return {
            "ticker": market.get("ticker") or market.get("market_ticker") or market.get("symbol"),
            "category": str(market.get("category") or market.get("market_category") or "unknown"),
            "timestamp": ts.isoformat(),
            "hour": str(ts.hour),
            "weekday": ts.strftime("%A"),
            "yes_price": yes_price,
            "no_price": no_price,
            "spread": spread,
            "volume": _safe_float(market.get("volume") or market.get("volume_24h") or market.get("total_volume")),
            "liquidity": _safe_float(market.get("liquidity") or market.get("open_interest") or market.get("oi") or market.get("depth")),
            "volatility": yes_price,
        }

    def _find_matches(self, live: Dict[str, Any], rows: List[Dict[str, Any]], max_matches: int) -> List[Dict[str, Any]]:
        scored = []

        for row in rows:
            score = 0.0

            if live["category"] == row["category"]:
                score += 30.0

            if live["hour"] == row["hour"]:
                score += 15.0

            if live["weekday"] == row["weekday"]:
                score += 10.0

            score += self._numeric_similarity(live["yes_price"], row["yes_price"]) * 0.15
            score += self._numeric_similarity(live["volume"], row["volume"]) * 0.15
            score += self._numeric_similarity(live["liquidity"], row["liquidity"]) * 0.15

            row_copy = dict(row)
            row_copy["match_score"] = round(score, 4)

            if score >= 55:
                scored.append(row_copy)

        scored.sort(key=lambda r: r["match_score"], reverse=True)
        return scored[:max_matches]

    def _calculate_outcomes(self, matches: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}

        for horizon in self.horizons_minutes:
            yes_changes = []
            no_changes = []
            liquidity_changes = []
            spread_changes = []
            volume_changes = []
            volatility_changes = []

            for start in matches:
                future = self._future_row(start, rows, horizon)
                if not future:
                    continue

                yes_changes.append(future["yes_price"] - start["yes_price"])
                no_changes.append(future["no_price"] - start["no_price"])
                liquidity_changes.append(future["liquidity"] - start["liquidity"])
                spread_changes.append(future["spread"] - start["spread"])
                volume_changes.append(future["volume"] - start["volume"])
                volatility_changes.append(future["volatility"] - start["volatility"])

            out[str(horizon)] = {
                "horizon_minutes": horizon,
                "observations": len(yes_changes),
                "yes_price_change": _stats(yes_changes),
                "no_price_change": _stats(no_changes),
                "liquidity_change": _stats(liquidity_changes),
                "spread_change": _stats(spread_changes),
                "volume_change": _stats(volume_changes),
                "volatility_change": _stats(volatility_changes),
                "confidence": self._horizon_confidence(yes_changes),
            }

        return out

    def _future_row(self, start: Dict[str, Any], rows: List[Dict[str, Any]], horizon_minutes: int) -> Optional[Dict[str, Any]]:
        target = start["timestamp"] + timedelta(minutes=horizon_minutes)
        same_ticker = [r for r in rows if r["ticker"] == start["ticker"] and r["timestamp"] >= target]

        if same_ticker:
            return same_ticker[0]

        same_category = [
            r for r in rows
            if r["category"] == start["category"]
            and r["timestamp"] >= target
            and r["timestamp"] <= target + timedelta(minutes=10)
        ]

        return same_category[0] if same_category else None

    def _outcome_curve(self, outcomes: Dict[str, Any]) -> Dict[str, Any]:
        curve = []

        for horizon in self.horizons_minutes:
            data = outcomes.get(str(horizon), {})
            curve.append({
                "horizon_minutes": horizon,
                "observations": data.get("observations", 0),
                "avg_yes_change": (data.get("yes_price_change") or {}).get("mean", 0.0),
                "avg_no_change": (data.get("no_price_change") or {}).get("mean", 0.0),
                "avg_liquidity_change": (data.get("liquidity_change") or {}).get("mean", 0.0),
                "avg_spread_change": (data.get("spread_change") or {}).get("mean", 0.0),
                "confidence_score": (data.get("confidence") or {}).get("score", 0.0),
            })

        return {
            "curve": curve,
            "read_only": True,
            "execution_allowed": False,
        }

    def _confidence(self, outcomes: Dict[str, Any], matches_found: int) -> Dict[str, Any]:
        observation_counts = [v.get("observations", 0) for v in outcomes.values()]
        avg_obs = mean(observation_counts) if observation_counts else 0.0
        score = min(100.0, (matches_found * 0.8) + (avg_obs * 0.7))

        return {
            "score": round(score, 4),
            "label": self._label(score),
            "matches_found": matches_found,
            "average_horizon_observations": round(avg_obs, 4),
        }

    def _horizon_confidence(self, values: List[float]) -> Dict[str, Any]:
        count = len(values)
        consistency = max(0.0, 100.0 - _std(values))
        sample_score = min(100.0, count * 5.0)
        score = round((sample_score * 0.65) + (consistency * 0.35), 4)

        return {
            "score": score,
            "label": self._label(score),
            "sample_size": count,
            "consistency": round(consistency, 4),
        }

    def _numeric_similarity(self, a: float, b: float) -> float:
        a = _safe_float(a)
        b = _safe_float(b)

        if a == 0 and b == 0:
            return 100.0

        denom = max(abs(a), abs(b), 1.0)
        return max(0.0, 100.0 - (abs(a - b) / denom * 100.0))

    def _empty_packet(self, status: str, live_market: Dict[str, Any], note: str) -> Dict[str, Any]:
        return OutcomePacket(
            module="OI-030 Historical Outcome Tracking Engine",
            status=status,
            generated_at=self._now(),
            database=str(self.db_path) if self.db_path else None,
            live_market=self._normalize_live_market(live_market),
            matches_found=0,
            horizons_minutes=self.horizons_minutes,
            outcome_curve={"curve": [], "read_only": True, "execution_allowed": False},
            horizon_statistics={},
            confidence={"score": 0.0, "label": "waiting_for_data"},
            notes=[note],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

    def _label(self, score: float) -> str:
        if score >= 85:
            return "very_high"
        if score >= 70:
            return "high"
        if score >= 50:
            return "moderate"
        if score >= 25:
            return "low"
        return "thin"

    def _pick(self, keys: List[str], candidates: List[str]) -> Optional[str]:
        lower = {k.lower(): k for k in keys}
        for candidate in candidates:
            if candidate.lower() in lower:
                return lower[candidate.lower()]
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_outcome_engine = HistoricalOutcomeTrackingEngine()
''').strip() + "\n", encoding="utf-8")

TEST_FILE.write_text(textwrap.dedent(r'''
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

from qseries_v2.oracle_intelligence.historical_outcome_tracking_engine import HistoricalOutcomeTrackingEngine


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
            liquidity REAL
        )
    """)

    base = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)
    rows = []

    for ticker_num in range(20):
        ticker = f"TEST-{ticker_num}"
        category = "crypto" if ticker_num < 12 else "sports"

        for step in range(40):
            ts = base + timedelta(minutes=5 * step)
            yes_price = 45 + (ticker_num % 5) + (step * 0.25)
            no_price = 100 - yes_price
            bid = yes_price - 2
            ask = yes_price + 2
            volume = 1000 + ticker_num * 20 + step * 10
            liquidity = 2500 + ticker_num * 30 + step * 15

            rows.append((
                ts.isoformat(),
                ticker,
                category,
                yes_price,
                no_price,
                bid,
                ask,
                volume,
                liquidity,
            ))

    cur.executemany("""
        INSERT INTO market_history
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def test_oi_030_historical_outcome_tracking_engine():
    db_path = Path("test_oi_030_history.sqlite3")
    build_test_db(db_path)

    engine = HistoricalOutcomeTrackingEngine(
        str(db_path),
        horizons_minutes=[5, 15, 30, 60],
    )

    diagnostics = engine.diagnostics()
    assert diagnostics["status"] == "ok"
    assert diagnostics["database_exists"] is True
    assert diagnostics["read_only"] is True
    assert diagnostics["execution_allowed"] is False

    live_market = {
        "ticker": "LIVE-TEST",
        "category": "crypto",
        "timestamp": "2026-06-29T12:00:00+00:00",
        "yes_price": 47,
        "no_price": 53,
        "bid": 45,
        "ask": 49,
        "volume": 1100,
        "liquidity": 2600,
    }

    packet = engine.forward_outcomes(live_market)
    assert packet["status"] == "ok"
    assert packet["matches_found"] > 0
    assert packet["horizon_statistics"]
    assert packet["horizon_statistics"]["5"]["observations"] > 0
    assert packet["horizon_statistics"]["15"]["yes_price_change"]["mean"] > 0
    assert packet["outcome_curve"]["curve"]
    assert packet["confidence"]["score"] > 0
    assert packet["read_only"] is True
    assert packet["execution_allowed"] is False

    curve = engine.outcome_curve(live_market)
    assert len(curve["curve"]) == 4

    stats = engine.horizon_statistics(live_market)
    assert "60" in stats

    pattern = engine.analyze_pattern()
    assert pattern["status"] == "ok"
    assert pattern["outcome_curve"]

    db_path.unlink(missing_ok=True)

    print("[PASS] OI-030 Historical Outcome Tracking Engine")
    print({
        "matches_found": packet["matches_found"],
        "confidence": packet["confidence"],
        "curve_points": len(packet["outcome_curve"]["curve"]),
        "horizon_15_yes_mean": packet["horizon_statistics"]["15"]["yes_price_change"]["mean"],
    })


if __name__ == "__main__":
    test_oi_030_historical_outcome_tracking_engine()
''').strip() + "\n", encoding="utf-8")

INIT = OI_DIR / "__init__.py"
content = INIT.read_text(encoding="utf-8") if INIT.exists() else ""

line = "from .historical_outcome_tracking_engine import HistoricalOutcomeTrackingEngine, oracle_outcome_engine\n"
if line not in content:
    content += ("\n" if content and not content.endswith("\n") else "") + line
    INIT.write_text(content, encoding="utf-8")

print("========================================")
print(" OI-030 INSTALLER")
print(" Historical Outcome Tracking Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST_FILE}")
print(f"[OK] Updated {INIT}")
print("")
print("[DONE] OI-030 installed")
print("")
print("Run:")
print("python test_oi_030_historical_outcome_tracking_engine.py")