"""
OI-044 Oracle Similarity Intelligence Engine

Purpose:
- Compare current market setups against Oracle long-term memory.
- Answer: "Have I seen this before?"
- Return ranked historical analogs and aggregate outcome intelligence.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .oracle_memory_persistence_bridge import oracle_memory_persistence_bridge, OracleMemoryPersistenceBridge


NUMERIC_FEATURES = [
    "price",
    "yes_price",
    "no_price",
    "implied_probability",
    "volume",
    "liquidity",
    "spread",
    "momentum",
    "volatility",
    "time_to_expiration_minutes",
    "confidence",
    "forecast_value",
    "actual_value",
]

CATEGORICAL_FEATURES = [
    "ticker",
    "market_ticker",
    "category",
    "event_category",
    "regime",
    "rhythm_phase",
    "pattern_name",
    "strategy",
    "side",
]


class OracleSimilarityIntelligenceEngine:
    module_name = "oi_044_oracle_similarity_intelligence_engine"

    def __init__(self, memory_bridge: Optional[OracleMemoryPersistenceBridge] = None) -> None:
        self.memory_bridge = memory_bridge or oracle_memory_persistence_bridge

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "memory_bridge": self.memory_bridge.status()["status"],
        }

    def find_similar_setups(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> Dict[str, Any]:
        memories = self.memory_bridge.recall_persistent(
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=100000,
        )

        scored = []

        for memory in memories:
            candidate = self._memory_to_feature_source(memory)
            similarity, details = self._similarity_score(current_setup, candidate)

            if similarity >= min_similarity:
                scored.append({
                    "similarity": round(similarity, 4),
                    "similarity_pct": round(similarity * 100.0, 2),
                    "memory": memory,
                    "details": details,
                })

        scored.sort(
            key=lambda item: (
                item["similarity"],
                item["memory"].get("importance", 0),
                item["memory"].get("confidence", 0),
            ),
            reverse=True,
        )

        top_matches = scored[:limit]
        aggregate = self._aggregate_outcomes(top_matches)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "query": current_setup,
            "total_memories_scored": len(memories),
            "match_count": len(scored),
            "top_matches": top_matches,
            "aggregate": aggregate,
        }

    def explain_similarity(self, current_setup: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._memory_to_feature_source(memory)
        similarity, details = self._similarity_score(current_setup, candidate)

        return {
            "similarity": round(similarity, 4),
            "similarity_pct": round(similarity * 100.0, 2),
            "details": details,
            "read_only": True,
        }

    def _memory_to_feature_source(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        payload = memory.get("payload", {}) or {}

        merged = {}
        merged.update(payload)

        if "forecast" in payload and isinstance(payload["forecast"], dict):
            merged.update({f"forecast_{k}": v for k, v in payload["forecast"].items()})
            merged.update(payload["forecast"])

        if "outcome" in payload and isinstance(payload["outcome"], dict):
            merged.update({f"outcome_{k}": v for k, v in payload["outcome"].items()})

        merged.setdefault("ticker", memory.get("market_ticker"))
        merged.setdefault("market_ticker", memory.get("market_ticker"))
        merged.setdefault("confidence", memory.get("confidence"))
        merged.setdefault("importance", memory.get("importance"))
        merged.setdefault("memory_type", memory.get("memory_type"))

        return merged

    def _similarity_score(self, a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        numeric_scores = []
        categorical_scores = []

        numeric_details = {}
        categorical_details = {}

        for key in NUMERIC_FEATURES:
            if key in a and key in b and self._is_number(a[key]) and self._is_number(b[key]):
                score = self._numeric_similarity(float(a[key]), float(b[key]))
                numeric_scores.append(score)
                numeric_details[key] = round(score, 4)

        for key in CATEGORICAL_FEATURES:
            av = a.get(key)
            bv = b.get(key)

            if av is not None and bv is not None:
                score = 1.0 if str(av).lower() == str(bv).lower() else 0.0
                categorical_scores.append(score)
                categorical_details[key] = score

        tag_score = self._tag_overlap_score(a.get("tags", []), b.get("tags", []))

        numeric_component = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0
        categorical_component = sum(categorical_scores) / len(categorical_scores) if categorical_scores else 0.0

        if numeric_scores and categorical_scores:
            total = (numeric_component * 0.65) + (categorical_component * 0.25) + (tag_score * 0.10)
        elif numeric_scores:
            total = (numeric_component * 0.90) + (tag_score * 0.10)
        elif categorical_scores:
            total = (categorical_component * 0.85) + (tag_score * 0.15)
        else:
            total = tag_score

        return max(0.0, min(1.0, total)), {
            "numeric_component": round(numeric_component, 4),
            "categorical_component": round(categorical_component, 4),
            "tag_component": round(tag_score, 4),
            "numeric_features": numeric_details,
            "categorical_features": categorical_details,
        }

    def _numeric_similarity(self, a: float, b: float) -> float:
        if a == b:
            return 1.0

        scale = max(abs(a), abs(b), 1.0)
        distance = abs(a - b) / scale
        return max(0.0, 1.0 - distance)

    def _tag_overlap_score(self, a_tags: Any, b_tags: Any) -> float:
        a = set(str(x).lower() for x in (a_tags or []))
        b = set(str(x).lower() for x in (b_tags or []))

        if not a or not b:
            return 0.0

        return len(a & b) / len(a | b)

    def _aggregate_outcomes(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not matches:
            return {
                "occurrences": 0,
                "avg_similarity_pct": 0.0,
                "yes_count": 0,
                "no_count": 0,
                "unknown_count": 0,
                "yes_rate": None,
                "avg_confidence": None,
                "avg_importance": None,
            }

        yes_count = 0
        no_count = 0
        unknown_count = 0
        confidences = []
        importances = []

        for match in matches:
            memory = match["memory"]
            payload = memory.get("payload", {}) or {}
            outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

            result = (
                outcome.get("result")
                or outcome.get("resolved_side")
                or outcome.get("winner")
                or payload.get("result")
                or payload.get("resolved_side")
            )

            if result and str(result).upper() == "YES":
                yes_count += 1
            elif result and str(result).upper() == "NO":
                no_count += 1
            else:
                unknown_count += 1

            if memory.get("confidence") is not None:
                confidences.append(float(memory["confidence"]))

            if memory.get("importance") is not None:
                importances.append(float(memory["importance"]))

        known = yes_count + no_count

        return {
            "occurrences": len(matches),
            "avg_similarity_pct": round(sum(m["similarity_pct"] for m in matches) / len(matches), 2),
            "yes_count": yes_count,
            "no_count": no_count,
            "unknown_count": unknown_count,
            "yes_rate": round(yes_count / known, 4) if known else None,
            "avg_confidence": round(sum(confidences) / len(confidences), 2) if confidences else None,
            "avg_importance": round(sum(importances) / len(importances), 2) if importances else None,
        }

    def _is_number(self, value: Any) -> bool:
        try:
            v = float(value)
            return math.isfinite(v)
        except Exception:
            return False


oracle_similarity_intelligence_engine = OracleSimilarityIntelligenceEngine()
