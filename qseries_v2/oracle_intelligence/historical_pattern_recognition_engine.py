"""
OI-025 Historical Pattern Recognition Engine

Read-only Oracle Intelligence module.

Purpose:
- Find historical market records similar to a live market.
- Score similarity across category, time, weekday, expiration, liquidity,
  spread, volume, volatility, YES price, and NO price.
- Return pattern frequency, confidence, data quality, and historical context.
- No execution.
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

NUMERIC_METRICS = ["liquidity", "spread", "volume", "volatility", "yes_price", "no_price"]


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


def _avg(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(mean(clean), 6) if clean else 0.0


def _std(values: List[float]) -> float:
    clean = [_safe_float(v) for v in values if v is not None]
    return round(pstdev(clean), 6) if len(clean) > 1 else 0.0


@dataclass
class PatternMatchResult:
    module: str
    status: str
    generated_at: str
    database: Optional[str]
    live_market: Dict[str, Any]
    matches_found: int
    top_matches: List[Dict[str, Any]]
    pattern_summary: Dict[str, Any]
    confidence: Dict[str, Any]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalPatternRecognitionEngine:
    """
    Finds historical setups similar to the current market.

    This engine is analysis-only. It never sends execution instructions.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = self._resolve_db(db_path)
        self.last_result: Optional[Dict[str, Any]] = None

    def diagnostics(self) -> Dict[str, Any]:
        exists = bool(self.db_path and self.db_path.exists())
        return {
            "module": "OI-025 Historical Pattern Recognition Engine",
            "status": "ok" if exists else "waiting_for_history_db",
            "database": str(self.db_path) if self.db_path else None,
            "database_exists": exists,
            "last_result_ready": self.last_result is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def find_similar_markets(self, live_market: Dict[str, Any], limit: int = 100000, top_n: int = 10) -> Dict[str, Any]:
        if not self.db_path or not self.db_path.exists():
            result = PatternMatchResult(
                module="OI-025 Historical Pattern Recognition Engine",
                status="waiting_for_history_db",
                generated_at=self._now(),
                database=str(self.db_path) if self.db_path else None,
                live_market=self._normalize_live_market(live_market),
                matches_found=0,
                top_matches=[],
                pattern_summary={},
                confidence={
                    "score": 0.0,
                    "label": "waiting_for_data",
                    "sample_size": 0,
                    "data_quality": "waiting_for_data",
                    "historical_consistency": 0.0,
                },
                read_only=True,
                execution_allowed=False,
            ).to_dict()
            self.last_result = result
            return result

        notes: List[str] = []
        rows = self._load_rows(limit=limit, notes=notes)
        live = self._normalize_live_market(live_market)

        scored = []
        for row in rows:
            score_detail = self._similarity(live, row)
            scored.append({
                "similarity": score_detail["score"],
                "label": score_detail["label"],
                "reasons": score_detail["reasons"],
                "historical_market": {
                    "ticker": row.get("ticker"),
                    "category": row.get("category"),
                    "timestamp": row.get("timestamp").isoformat() if row.get("timestamp") else None,
                    "hour": row.get("hour"),
                    "weekday": row.get("weekday"),
                    "expiration_window": row.get("expiration_window"),
                    "liquidity": row.get("liquidity"),
                    "spread": row.get("spread"),
                    "volume": row.get("volume"),
                    "yes_price": row.get("yes_price"),
                    "no_price": row.get("no_price"),
                },
            })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        top_matches = scored[:top_n]

        strong_matches = [m for m in scored if m["similarity"] >= 75.0]
        summary_source = strong_matches if strong_matches else top_matches

        summary = self._pattern_summary(summary_source)
        confidence = self._confidence(summary_source, rows)

        result = PatternMatchResult(
            module="OI-025 Historical Pattern Recognition Engine",
            status="ok",
            generated_at=self._now(),
            database=str(self.db_path),
            live_market=live,
            matches_found=len(summary_source),
            top_matches=top_matches,
            pattern_summary=summary,
            confidence=confidence,
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_result = result
        return result

    def compare_pattern(self, live_market: Dict[str, Any]) -> Dict[str, Any]:
        return self.find_similar_markets(live_market)

    def top_patterns(self) -> Dict[str, Any]:
        result = self.last_result
        if not result:
            return {
                "module": "OI-025 Historical Pattern Recognition Engine",
                "status": "no_pattern_run_yet",
                "patterns": [],
                "read_only": True,
                "execution_allowed": False,
            }

        return {
            "module": "OI-025 Historical Pattern Recognition Engine",
            "status": result.get("status"),
            "patterns": result.get("top_matches", []),
            "confidence": result.get("confidence", {}),
            "read_only": True,
            "execution_allowed": False,
        }

    def pattern_statistics(self, pattern_id: Optional[str] = None) -> Dict[str, Any]:
        result = self.last_result
        if not result:
            return {
                "module": "OI-025 Historical Pattern Recognition Engine",
                "status": "no_pattern_run_yet",
                "pattern_id": pattern_id,
                "statistics": {},
                "read_only": True,
                "execution_allowed": False,
            }

        return {
            "module": "OI-025 Historical Pattern Recognition Engine",
            "status": result.get("status"),
            "pattern_id": pattern_id or "latest_pattern",
            "statistics": result.get("pattern_summary", {}),
            "confidence": result.get("confidence", {}),
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

                    query = f"SELECT * FROM {table} ORDER BY {time_col} DESC LIMIT ?"
                    for row in conn.execute(query, (limit,)).fetchall():
                        normalized = self._normalize_row(dict(row), table)
                        if normalized:
                            rows.append(normalized)

                    if rows:
                        notes.append(f"Loaded pattern rows from table: {table}")
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

        expiration = _parse_dt(row.get(self._pick(keys, ["expiration", "expiration_time", "close_time", "end_time"])))

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
            "expiration_window": self._expiration_window(dt, expiration),
            "liquidity": _safe_float(row.get(self._pick(keys, ["liquidity", "open_interest", "oi", "depth"]))),
            "spread": spread,
            "volume": _safe_float(row.get(self._pick(keys, ["volume", "volume_24h", "total_volume"]))),
            "volatility": yes_price,
            "yes_price": yes_price,
            "no_price": no_price,
        }

    def _normalize_live_market(self, market: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = _parse_dt(market.get("timestamp")) or datetime.now(timezone.utc)
        expiration = _parse_dt(
            market.get("expiration")
            or market.get("expiration_time")
            or market.get("close_time")
            or market.get("end_time")
        )

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
            "timestamp": timestamp.isoformat(),
            "hour": str(timestamp.hour),
            "weekday": timestamp.strftime("%A"),
            "expiration_window": self._expiration_window(timestamp, expiration),
            "liquidity": _safe_float(market.get("liquidity") or market.get("open_interest") or market.get("oi") or market.get("depth")),
            "spread": spread,
            "volume": _safe_float(market.get("volume") or market.get("volume_24h") or market.get("total_volume")),
            "volatility": yes_price,
            "yes_price": yes_price,
            "no_price": no_price,
        }

    def _similarity(self, live: Dict[str, Any], hist: Dict[str, Any]) -> Dict[str, Any]:
        reasons = []

        categorical_scores = []

        category_score = 100.0 if live.get("category") == hist.get("category") else 40.0
        categorical_scores.append(category_score)
        if category_score == 100.0:
            reasons.append("same_category")

        hour_distance = abs(int(live.get("hour", 0)) - int(hist.get("hour", 0)))
        hour_distance = min(hour_distance, 24 - hour_distance)
        hour_score = max(0.0, 100.0 - (hour_distance * 12.5))
        categorical_scores.append(hour_score)
        if hour_score >= 87.5:
            reasons.append("similar_hour")

        weekday_score = 100.0 if live.get("weekday") == hist.get("weekday") else 70.0
        categorical_scores.append(weekday_score)
        if weekday_score == 100.0:
            reasons.append("same_weekday")

        expiration_score = 100.0 if live.get("expiration_window") == hist.get("expiration_window") else 55.0
        categorical_scores.append(expiration_score)
        if expiration_score == 100.0:
            reasons.append("same_expiration_window")

        numeric_scores = []
        for metric in NUMERIC_METRICS:
            live_val = _safe_float(live.get(metric))
            hist_val = _safe_float(hist.get(metric))
            numeric_score = self._numeric_similarity(live_val, hist_val)
            numeric_scores.append(numeric_score)
            if numeric_score >= 85.0:
                reasons.append(f"similar_{metric}")

        categorical_component = mean(categorical_scores) if categorical_scores else 0.0
        numeric_component = mean(numeric_scores) if numeric_scores else 0.0

        score = round((categorical_component * 0.45) + (numeric_component * 0.55), 4)

        if score >= 90:
            label = "extremely_similar"
        elif score >= 75:
            label = "strong_match"
        elif score >= 50:
            label = "moderate_match"
        else:
            label = "weak_match"

        return {
            "score": score,
            "label": label,
            "reasons": reasons[:12],
        }

    def _numeric_similarity(self, a: float, b: float) -> float:
        a = _safe_float(a)
        b = _safe_float(b)

        if a == 0 and b == 0:
            return 100.0

        denominator = max(abs(a), abs(b), 1.0)
        distance = abs(a - b) / denominator

        return round(max(0.0, 100.0 - (distance * 100.0)), 4)

    def _pattern_summary(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not matches:
            return {
                "occurrences": 0,
                "first_seen": None,
                "last_seen": None,
                "average_similarity": 0.0,
                "average_interval_hours": 0.0,
                "typical_characteristics": {},
            }

        timestamps = []
        historical = []

        for match in matches:
            item = match.get("historical_market", {})
            historical.append(item)
            dt = _parse_dt(item.get("timestamp"))
            if dt:
                timestamps.append(dt)

        timestamps.sort()

        intervals = []
        for i in range(1, len(timestamps)):
            intervals.append((timestamps[i] - timestamps[i - 1]).total_seconds() / 3600.0)

        characteristics = {}
        for metric in ["liquidity", "spread", "volume", "yes_price", "no_price"]:
            values = [_safe_float(item.get(metric)) for item in historical]
            characteristics[metric] = {
                "avg": _avg(values),
                "std": _std(values),
                "min": round(min(values), 6) if values else 0.0,
                "max": round(max(values), 6) if values else 0.0,
            }

        return {
            "occurrences": len(matches),
            "first_seen": timestamps[0].isoformat() if timestamps else None,
            "last_seen": timestamps[-1].isoformat() if timestamps else None,
            "average_similarity": _avg([m.get("similarity", 0.0) for m in matches]),
            "average_interval_hours": _avg(intervals),
            "typical_characteristics": characteristics,
        }

    def _confidence(self, matches: List[Dict[str, Any]], all_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        sample_size = len(matches)
        avg_similarity = _avg([m.get("similarity", 0.0) for m in matches])
        consistency = max(0.0, 100.0 - _std([m.get("similarity", 0.0) for m in matches]))

        sample_score = min(sample_size / 50.0, 1.0) * 100.0
        data_quality_score = min(len(all_rows) / 500.0, 1.0) * 100.0

        score = round(
            (avg_similarity * 0.45)
            + (consistency * 0.25)
            + (sample_score * 0.20)
            + (data_quality_score * 0.10),
            4,
        )

        if score >= 85:
            label = "very_high"
            data_quality = "excellent"
        elif score >= 70:
            label = "high"
            data_quality = "good"
        elif score >= 50:
            label = "moderate"
            data_quality = "fair"
        else:
            label = "low"
            data_quality = "thin"

        return {
            "score": score,
            "label": label,
            "sample_size": sample_size,
            "data_quality": data_quality,
            "data_quality_score": round(data_quality_score, 4),
            "historical_consistency": round(consistency, 4),
            "average_similarity": avg_similarity,
        }

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


oracle_pattern_engine = HistoricalPatternRecognitionEngine()
