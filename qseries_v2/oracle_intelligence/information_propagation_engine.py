"""
OI-083 Information Propagation Engine

Purpose:
- Track how information moves across markets after a catalyst.
- Identify origin markets, downstream markets, propagation delay, laggards, and information edge.
- Read-only Oracle intelligence layer.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import math


class InformationPropagationEngine:
    module_name = "oi_083_information_propagation_engine"

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._paths: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "events": len(self._events),
            "paths": len(self._paths),
        }

    def record_information_event(
        self,
        event_id: str,
        source_market: str,
        observations: List[Dict[str, Any]],
        event_type: str = "generic",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cleaned = [self._clean_observation(o) for o in observations or []]
        cleaned = [o for o in cleaned if o["ticker"]]
        cleaned.sort(key=lambda x: x["reaction_delay_minutes"])

        event = {
            "event_id": str(event_id),
            "event_type": str(event_type),
            "source_market": str(source_market),
            "observed_at": self._now(),
            "observations": cleaned,
            "metadata": metadata or {},
        }

        self._events.append(event)

        for obs in cleaned:
            if obs["ticker"] != source_market:
                key = f"{source_market}->{obs['ticker']}"
                self._paths[key].append({
                    "event_id": event_id,
                    "event_type": event_type,
                    "source_market": source_market,
                    "target_market": obs["ticker"],
                    "delay_minutes": obs["reaction_delay_minutes"],
                    "reaction_strength": obs["reaction_strength"],
                    "confidence": obs["confidence"],
                })

        return {
            "status": "ok",
            "read_only": True,
            "event_id": event_id,
            "source_market": source_market,
            "observation_count": len(cleaned),
            "sequence": cleaned,
        }

    def propagation_model(self, event_type: Optional[str] = None) -> Dict[str, Any]:
        events = [e for e in self._events if event_type is None or e["event_type"] == event_type]
        path_rows = []

        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for key, rows in self._paths.items():
            for row in rows:
                if event_type is None or row["event_type"] == event_type:
                    grouped[key].append(row)

        for key, rows in grouped.items():
            path_rows.append(self._summarize_path(key, rows))

        path_rows.sort(key=lambda r: (r["confidence"], -r["avg_delay_minutes"]), reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "event_type": event_type,
            "events_analyzed": len(events),
            "paths": path_rows,
            "strongest_path": path_rows[0] if path_rows else None,
            "summary": {
                "path_count": len(path_rows),
                "avg_delay_minutes": round(sum(p["avg_delay_minutes"] for p in path_rows) / len(path_rows), 2) if path_rows else 0.0,
            },
        }

    def detect_lagging_markets(
        self,
        source_market: str,
        live_markets: List[Dict[str, Any]],
        elapsed_minutes: float,
        event_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        model = self.propagation_model(event_type)
        expected = {p["target_market"]: p for p in model["paths"] if p["source_market"] == source_market}

        rows = []
        for market in live_markets or []:
            ticker = market.get("ticker") or market.get("market_ticker")
            path = expected.get(ticker)
            rows.append(self._lag_status(ticker, market, path, elapsed_minutes))

        rows.sort(key=lambda r: r["information_edge_score"], reverse=True)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "source_market": source_market,
            "elapsed_minutes": float(elapsed_minutes),
            "markets_analyzed": len(rows),
            "lagging_markets": [r for r in rows if r["lagging"]],
            "results": rows,
        }

    def _lag_status(self, ticker: str, market: Dict[str, Any], path: Optional[Dict[str, Any]], elapsed: float) -> Dict[str, Any]:
        reaction = self._num(market.get("reaction_strength") or market.get("move_pct") or market.get("price_delta_pct") or market.get("momentum"), 0.0)

        if not path:
            return {
                "ticker": ticker,
                "read_only": True,
                "status": "no_path_model",
                "lagging": False,
                "information_edge_score": 0.0,
                "reason_codes": ["no_propagation_path"],
            }

        expected_delay = path["avg_delay_minutes"]
        expected_strength = path["avg_reaction_strength"]
        overdue = elapsed > expected_delay
        underreacted = abs(reaction) < max(1.0, expected_strength * 0.35)

        score = 0.0
        reasons = []

        if overdue:
            score += 35
            reasons.append("expected_reaction_window_passed")
        if underreacted:
            score += 35
            reasons.append("market_underreacted")
        if path["confidence"] >= 75:
            score += 20
            reasons.append("high_confidence_propagation_path")
        if expected_strength >= 4:
            score += 10
            reasons.append("historically_meaningful_reaction")

        score = max(0.0, min(100.0, score))
        lagging = score >= 60

        if not reasons:
            reasons.append("reaction_in_line")

        return {
            "ticker": ticker,
            "read_only": True,
            "status": "lagging" if lagging else "in_line",
            "lagging": lagging,
            "expected_delay_minutes": round(expected_delay, 2),
            "elapsed_minutes": round(float(elapsed), 2),
            "reaction_strength": round(reaction, 4),
            "expected_reaction_strength": round(expected_strength, 4),
            "information_edge_score": round(score, 2),
            "reason_codes": reasons,
        }

    def _summarize_path(self, key: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        delays = [r["delay_minutes"] for r in rows]
        strengths = [r["reaction_strength"] for r in rows]
        confs = [r["confidence"] for r in rows]
        source, target = key.split("->", 1)

        return {
            "path_key": key,
            "source_market": source,
            "target_market": target,
            "count": len(rows),
            "avg_delay_minutes": round(sum(delays) / len(delays), 2),
            "avg_reaction_strength": round(sum(strengths) / len(strengths), 4),
            "avg_observation_confidence": round(sum(confs) / len(confs), 2),
            "confidence": round(min(100.0, 45 + len(rows) * 12), 2),
        }

    def _clean_observation(self, row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": row.get("ticker") or row.get("market_ticker"),
            "reaction_delay_minutes": self._num(row.get("reaction_delay_minutes") or row.get("delay_minutes"), 0.0),
            "reaction_strength": self._num(row.get("reaction_strength") or row.get("move_pct") or row.get("price_delta_pct"), 0.0),
            "confidence": self._num(row.get("confidence"), 50.0),
            "category": row.get("category"),
        }

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            v = float(value)
            return v if math.isfinite(v) else default
        except Exception:
            return default

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


information_propagation_engine = InformationPropagationEngine()
