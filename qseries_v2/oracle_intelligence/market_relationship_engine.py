from __future__ import annotations

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List, Optional
from math import sqrt

DEFAULT_DB_CANDIDATES = [
    Path("qseries_v2/ops/qseries_history.sqlite3"),
    Path("qseries_v2/data/qseries_history.sqlite3"),
    Path("qseries_history.sqlite3"),
]


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


def _corr(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 0.0
    x = a[:n]
    y = b[:n]
    mx = mean(x)
    my = mean(y)
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den_x = sqrt(sum((v - mx) ** 2 for v in x))
    den_y = sqrt(sum((v - my) ** 2 for v in y))
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 6)


@dataclass
class RelationshipPacket:
    module: str
    status: str
    generated_at: str
    database: Optional[str]
    rows_analyzed: int
    market_correlations: Dict[str, Any]
    category_correlations: Dict[str, Any]
    lead_lag: Dict[str, Any]
    influence_scores: Dict[str, Any]
    live_context: Dict[str, Any]
    notes: List[str]
    read_only: bool
    execution_allowed: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MarketRelationshipEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = self._resolve_db(db_path)
        self.last_packet: Optional[Dict[str, Any]] = None

    def diagnostics(self) -> Dict[str, Any]:
        exists = bool(self.db_path and self.db_path.exists())
        return {
            "module": "OI-037 Market Relationship Engine",
            "status": "ok" if exists else "waiting_for_history_db",
            "database": str(self.db_path) if self.db_path else None,
            "database_exists": exists,
            "last_packet_ready": self.last_packet is not None,
            "read_only": True,
            "execution_allowed": False,
        }

    def correlation_snapshot(self, live_markets: Optional[List[Dict[str, Any]]] = None, limit: int = 100000) -> Dict[str, Any]:
        notes: List[str] = []

        if not self.db_path or not self.db_path.exists():
            packet = self._empty_packet("waiting_for_history_db", "Historical database not found.")
            self.last_packet = packet
            return packet

        rows = self._load_rows(limit=limit, notes=notes)
        if not rows:
            packet = self._empty_packet("waiting_for_history_rows", "No usable historical rows found.")
            self.last_packet = packet
            return packet

        series = self._series_by_market(rows)
        categories = self._series_by_category(rows)

        market_corr = self._market_correlations(series)
        category_corr = self._category_correlations(categories)
        lead_lag = self._lead_lag_analysis(series)
        influence = self._influence_scores(market_corr, lead_lag)
        live_context = self._live_context(live_markets or [], market_corr, category_corr)

        packet = RelationshipPacket(
            module="OI-037 Market Relationship Engine",
            status="ok",
            generated_at=self._now(),
            database=str(self.db_path),
            rows_analyzed=len(rows),
            market_correlations=market_corr,
            category_correlations=category_corr,
            lead_lag=lead_lag,
            influence_scores=influence,
            live_context=live_context,
            notes=notes or ["Market relationship analysis completed successfully."],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

        self.last_packet = packet
        return packet

    def market_correlations(self) -> Dict[str, Any]:
        return self.correlation_snapshot().get("market_correlations", {})

    def category_correlations(self) -> Dict[str, Any]:
        return self.correlation_snapshot().get("category_correlations", {})

    def lead_lag_analysis(self) -> Dict[str, Any]:
        return self.correlation_snapshot().get("lead_lag", {})

    def influence_score(self, ticker: Optional[str] = None) -> Dict[str, Any]:
        scores = self.correlation_snapshot().get("influence_scores", {})
        if ticker:
            return scores.get(ticker, {})
        return scores

    def latest(self) -> Dict[str, Any]:
        if self.last_packet is None:
            return {
                "module": "OI-037 Market Relationship Engine",
                "status": "no_snapshot_yet",
                "read_only": True,
                "execution_allowed": False,
            }
        return self.last_packet

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
            tables = [r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            candidates = [t for t in tables if any(k in t.lower() for k in ["market", "history", "snapshot", "record"])] or tables

            for table in candidates:
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
                    notes.append(f"Loaded relationship rows from table: {table}")
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

        yes_price = _safe_float(row.get(self._pick(keys, ["yes_price", "yes_bid", "yes_ask", "price", "last_price"])))
        ticker = str(row.get(self._pick(keys, ["ticker", "market_ticker", "symbol"])) or "")
        if not ticker:
            return None

        return {
            "source_table": table,
            "timestamp": dt,
            "bucket": dt.replace(second=0, microsecond=0).isoformat(),
            "ticker": ticker,
            "category": str(row.get(self._pick(keys, ["category", "market_category", "event_category", "type"])) or "unknown"),
            "price": yes_price,
            "volume": _safe_float(row.get(self._pick(keys, ["volume", "volume_24h", "total_volume"]))),
            "liquidity": _safe_float(row.get(self._pick(keys, ["liquidity", "open_interest", "oi", "depth"]))),
        }

    def _series_by_market(self, rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault(row["ticker"], []).append(row)

        return {k: v for k, v in grouped.items() if len(v) >= 5}

    def _series_by_category(self, rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        by_bucket_cat: Dict[str, Dict[str, List[float]]] = {}

        for row in rows:
            key = row["bucket"]
            cat = row["category"]
            by_bucket_cat.setdefault(key, {}).setdefault(cat, []).append(row["price"])

        for bucket, cats in by_bucket_cat.items():
            dt = _parse_dt(bucket)
            for cat, prices in cats.items():
                grouped.setdefault(cat, []).append({
                    "timestamp": dt,
                    "bucket": bucket,
                    "category": cat,
                    "price": mean(prices),
                })

        return {k: v for k, v in grouped.items() if len(v) >= 5}

    def _price_changes(self, items: List[Dict[str, Any]]) -> List[float]:
        prices = [_safe_float(i.get("price")) for i in sorted(items, key=lambda x: x["timestamp"])]
        return [round(prices[i] - prices[i - 1], 6) for i in range(1, len(prices))]

    def _market_correlations(self, series: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        tickers = sorted(series.keys())
        pairs = []

        for i, a in enumerate(tickers):
            for b in tickers[i + 1:]:
                ca = self._price_changes(series[a])
                cb = self._price_changes(series[b])
                correlation = _corr(ca, cb)

                pairs.append({
                    "market_a": a,
                    "market_b": b,
                    "correlation": correlation,
                    "relationship": self._relationship_label(correlation),
                    "sample_size": min(len(ca), len(cb)),
                })

        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "pairs": pairs[:100],
            "pair_count": len(pairs),
            "strongest_positive": [p for p in pairs if p["correlation"] > 0][:10],
            "strongest_negative": [p for p in pairs if p["correlation"] < 0][:10],
        }

    def _category_correlations(self, categories: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        cats = sorted(categories.keys())
        pairs = []

        for i, a in enumerate(cats):
            for b in cats[i + 1:]:
                ca = self._price_changes(categories[a])
                cb = self._price_changes(categories[b])
                correlation = _corr(ca, cb)

                pairs.append({
                    "category_a": a,
                    "category_b": b,
                    "correlation": correlation,
                    "relationship": self._relationship_label(correlation),
                    "sample_size": min(len(ca), len(cb)),
                })

        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "pairs": pairs,
            "pair_count": len(pairs),
            "strongest": pairs[:10],
        }

    def _lead_lag_analysis(self, series: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        tickers = sorted(series.keys())
        results = []

        for i, leader in enumerate(tickers):
            for follower in tickers:
                if leader == follower:
                    continue

                leader_changes = self._price_changes(series[leader])
                follower_changes = self._price_changes(series[follower])

                best_lag = 0
                best_corr = 0.0

                for lag in [1, 2, 3, 5, 10]:
                    if len(leader_changes) <= lag or len(follower_changes) <= lag:
                        continue

                    corr = _corr(leader_changes[:-lag], follower_changes[lag:])
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = lag

                if abs(best_corr) >= 0.25:
                    results.append({
                        "leader": leader,
                        "follower": follower,
                        "lag_buckets": best_lag,
                        "correlation": round(best_corr, 6),
                        "relationship": self._relationship_label(best_corr),
                    })

        results.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "relationships": results[:100],
            "relationship_count": len(results),
            "top_leaders": self._top_leaders(results),
        }

    def _influence_scores(self, market_corr: Dict[str, Any], lead_lag: Dict[str, Any]) -> Dict[str, Any]:
        scores: Dict[str, Dict[str, Any]] = {}

        for pair in market_corr.get("pairs", []):
            for key in ["market_a", "market_b"]:
                ticker = pair[key]
                scores.setdefault(ticker, {"ticker": ticker, "correlation_strength": 0.0, "leadership": 0.0, "score": 0.0})
                scores[ticker]["correlation_strength"] += abs(_safe_float(pair.get("correlation"))) * 10

        for rel in lead_lag.get("relationships", []):
            leader = rel["leader"]
            scores.setdefault(leader, {"ticker": leader, "correlation_strength": 0.0, "leadership": 0.0, "score": 0.0})
            scores[leader]["leadership"] += abs(_safe_float(rel.get("correlation"))) * 25

        for ticker, data in scores.items():
            score = min(100.0, data["correlation_strength"] + data["leadership"])
            data["score"] = round(score, 4)
            data["label"] = self._label(score)

        return dict(sorted(scores.items(), key=lambda kv: kv[1]["score"], reverse=True))

    def _live_context(
        self,
        live_markets: List[Dict[str, Any]],
        market_corr: Dict[str, Any],
        category_corr: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not live_markets:
            return {
                "status": "no_live_markets_provided",
                "live_markets_analyzed": 0,
            }

        tickers = {
            m.get("ticker") or m.get("market_ticker") or m.get("symbol")
            for m in live_markets
        }

        relevant_pairs = [
            p for p in market_corr.get("pairs", [])
            if p.get("market_a") in tickers or p.get("market_b") in tickers
        ]

        return {
            "status": "ok",
            "live_markets_analyzed": len(live_markets),
            "relevant_relationships": relevant_pairs[:25],
            "strongest_live_relationship": relevant_pairs[0] if relevant_pairs else {},
            "read_only": True,
            "execution_allowed": False,
        }

    def _top_leaders(self, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        counts: Dict[str, float] = {}
        for rel in relationships:
            counts[rel["leader"]] = counts.get(rel["leader"], 0.0) + abs(_safe_float(rel["correlation"]))

        return [
            {"leader": k, "influence": round(v, 6)}
            for k, v in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:10]
        ]

    def _relationship_label(self, correlation: float) -> str:
        if correlation >= 0.75:
            return "strong_positive"
        if correlation >= 0.40:
            return "positive"
        if correlation <= -0.75:
            return "strong_negative"
        if correlation <= -0.40:
            return "negative"
        return "weak_or_mixed"

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

    def _empty_packet(self, status: str, note: str) -> Dict[str, Any]:
        return RelationshipPacket(
            module="OI-037 Market Relationship Engine",
            status=status,
            generated_at=self._now(),
            database=str(self.db_path) if self.db_path else None,
            rows_analyzed=0,
            market_correlations={},
            category_correlations={},
            lead_lag={},
            influence_scores={},
            live_context={},
            notes=[note],
            read_only=True,
            execution_allowed=False,
        ).to_dict()

    def _pick(self, keys: List[str], candidates: List[str]) -> Optional[str]:
        lower = {k.lower(): k for k in keys}
        for candidate in candidates:
            if candidate.lower() in lower:
                return lower[candidate.lower()]
        return None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_relationship_engine = MarketRelationshipEngine()
