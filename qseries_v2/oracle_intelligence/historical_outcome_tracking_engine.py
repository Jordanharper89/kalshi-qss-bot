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


def _std(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(pstdev(clean), 6) if len(clean) > 1 else 0.0


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
        "std": _std(clean),
        "best": round(max(clean), 6),
        "worst": round(min(clean), 6),
        "positive_frequency": round(len([v for v in clean if v > 0]) / len(clean) * 100.0, 4),
    }


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
            yes_changes, no_changes = [], []
            liquidity_changes, spread_changes = [], []
            volume_changes, volatility_changes = [], []

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

        same_ticker = [
            r for r in rows
            if r["ticker"] == start["ticker"] and r["timestamp"] >= target
        ]
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
