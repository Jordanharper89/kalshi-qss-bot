"""
OI-047 Analog Market Retrieval Engine

Central Oracle retrieval layer.

Purpose:
- Retrieve best historical analog markets for a current setup.
- Combine similarity, market DNA, confidence, importance, recency, and outcome quality.
- Provide one stable retrieval API for downstream Oracle modules.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .oracle_similarity_intelligence_engine import (
    oracle_similarity_intelligence_engine,
    OracleSimilarityIntelligenceEngine,
)
from .market_dna_fingerprinting_engine import (
    market_dna_fingerprinting_engine,
    MarketDNAFingerprintingEngine,
)


class AnalogMarketRetrievalEngine:
    module_name = "oi_047_analog_market_retrieval_engine"

    def __init__(
        self,
        similarity_engine: Optional[OracleSimilarityIntelligenceEngine] = None,
        dna_engine: Optional[MarketDNAFingerprintingEngine] = None,
    ) -> None:
        self.similarity_engine = similarity_engine or oracle_similarity_intelligence_engine
        self.dna_engine = dna_engine or market_dna_fingerprinting_engine

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "similarity_engine": self.similarity_engine.status()["status"],
            "dna_engine": self.dna_engine.status()["status"],
        }

    def retrieve_analogs(
        self,
        current_setup: Dict[str, Any],
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 25,
        min_retrieval_score: float = 0.0,
    ) -> Dict[str, Any]:
        similarity_result = self.similarity_engine.find_similar_setups(
            current_setup=current_setup,
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=100000,
            min_similarity=0.0,
        )

        current_dna = self.dna_engine.fingerprint_market(current_setup)
        analogs = []

        for match in similarity_result.get("top_matches", []):
            memory = match.get("memory", {})
            candidate_setup = self._memory_to_candidate_setup(memory)
            candidate_dna = self.dna_engine.fingerprint_market(candidate_setup)
            dna_compare = self.dna_engine.compare_fingerprints(current_dna, candidate_dna)

            score_parts = self._score_parts(match, memory, dna_compare)
            retrieval_score = self._combine_score(score_parts)

            if retrieval_score >= min_retrieval_score:
                analogs.append({
                    "retrieval_score": round(retrieval_score, 4),
                    "retrieval_score_pct": round(retrieval_score * 100.0, 2),
                    "similarity_pct": match.get("similarity_pct", 0.0),
                    "dna_similarity_pct": dna_compare.get("dna_similarity_pct", 0.0),
                    "dna_family_match": current_dna.get("dna_family") == candidate_dna.get("dna_family"),
                    "memory": memory,
                    "score_parts": score_parts,
                    "similarity_details": match.get("details", {}),
                    "dna_details": dna_compare,
                })

        analogs.sort(
            key=lambda a: (
                a["retrieval_score"],
                a["memory"].get("importance", 0),
                a["memory"].get("confidence", 0),
            ),
            reverse=True,
        )

        top = analogs[:limit]

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "query": current_setup,
            "query_dna": current_dna,
            "total_candidates": similarity_result.get("total_memories_scored", 0),
            "analog_count": len(analogs),
            "top_analogs": top,
            "summary": self._summary(top),
        }

    def _memory_to_candidate_setup(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        payload = memory.get("payload", {}) or {}
        setup = {}
        setup.update(payload)

        if isinstance(payload.get("forecast"), dict):
            setup.update(payload["forecast"])

        if isinstance(payload.get("outcome"), dict):
            setup.update({f"outcome_{k}": v for k, v in payload["outcome"].items()})

        setup.setdefault("ticker", memory.get("market_ticker"))
        setup.setdefault("market_ticker", memory.get("market_ticker"))
        setup.setdefault("confidence", memory.get("confidence"))
        setup.setdefault("tags", memory.get("tags", []))
        return setup

    def _score_parts(
        self,
        match: Dict[str, Any],
        memory: Dict[str, Any],
        dna_compare: Dict[str, Any],
    ) -> Dict[str, float]:
        similarity = float(match.get("similarity", 0.0))
        dna = float(dna_compare.get("dna_similarity", 0.0))
        confidence = min(max(float(memory.get("confidence", 50.0)) / 100.0, 0.0), 1.0)
        importance = min(max(float(memory.get("importance", 50.0)) / 100.0, 0.0), 1.0)
        recency = self._recency_score(memory.get("updated_at") or memory.get("created_at"))
        outcome_quality = self._outcome_quality_score(memory)

        return {
            "similarity": round(similarity, 4),
            "dna": round(dna, 4),
            "confidence": round(confidence, 4),
            "importance": round(importance, 4),
            "recency": round(recency, 4),
            "outcome_quality": round(outcome_quality, 4),
        }

    def _combine_score(self, parts: Dict[str, float]) -> float:
        return (
            parts["similarity"] * 0.35
            + parts["dna"] * 0.25
            + parts["confidence"] * 0.15
            + parts["importance"] * 0.10
            + parts["outcome_quality"] * 0.10
            + parts["recency"] * 0.05
        )

    def _recency_score(self, iso_time: Any) -> float:
        if not iso_time:
            return 0.5

        try:
            dt = datetime.fromisoformat(str(iso_time).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            age_days = max((datetime.now(timezone.utc) - dt).total_seconds() / 86400.0, 0.0)

            if age_days <= 1:
                return 1.0
            if age_days <= 7:
                return 0.9
            if age_days <= 30:
                return 0.75
            if age_days <= 180:
                return 0.55
            if age_days <= 365:
                return 0.35
            return 0.20
        except Exception:
            return 0.5

    def _outcome_quality_score(self, memory: Dict[str, Any]) -> float:
        payload = memory.get("payload", {}) or {}
        outcome = payload.get("outcome") if isinstance(payload.get("outcome"), dict) else {}

        result = (
            outcome.get("result")
            or outcome.get("resolved_side")
            or outcome.get("winner")
            or payload.get("result")
            or payload.get("resolved_side")
        )

        if str(result).upper() in {"YES", "NO"}:
            return 1.0

        if payload.get("actual_value") is not None or outcome.get("actual_value") is not None:
            return 0.8

        return 0.35

    def _summary(self, analogs: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not analogs:
            return {
                "count": 0,
                "avg_retrieval_score_pct": 0.0,
                "avg_similarity_pct": 0.0,
                "avg_dna_similarity_pct": 0.0,
                "resolved_yes": 0,
                "resolved_no": 0,
                "unknown": 0,
            }

        yes = 0
        no = 0
        unknown = 0

        for analog in analogs:
            result = self._extract_result(analog["memory"])
            if result == "YES":
                yes += 1
            elif result == "NO":
                no += 1
            else:
                unknown += 1

        return {
            "count": len(analogs),
            "avg_retrieval_score_pct": round(sum(a["retrieval_score_pct"] for a in analogs) / len(analogs), 2),
            "avg_similarity_pct": round(sum(a["similarity_pct"] for a in analogs) / len(analogs), 2),
            "avg_dna_similarity_pct": round(sum(a["dna_similarity_pct"] for a in analogs) / len(analogs), 2),
            "resolved_yes": yes,
            "resolved_no": no,
            "unknown": unknown,
        }

    def _extract_result(self, memory: Dict[str, Any]) -> str:
        payload = memory.get("payload", {}) or {}
        outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

        result = (
            outcome.get("result")
            or outcome.get("resolved_side")
            or outcome.get("winner")
            or payload.get("result")
            or payload.get("resolved_side")
        )

        if result is None:
            return "UNKNOWN"

        result = str(result).upper()
        return result if result in {"YES", "NO"} else "UNKNOWN"


analog_market_retrieval_engine = AnalogMarketRetrievalEngine()
