"""
OI-080 Oracle AI Core v1

Purpose:
- Unite Oracle's institutional intelligence stack into one read-only AI core.
- Combine meta intelligence, dynamic weights, research quality, performance attribution,
  cross-engine agreement, and institutional intelligence into a single research envelope.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:
    from .oracle_meta_intelligence_engine import oracle_meta_intelligence_engine
except Exception:  # pragma: no cover
    oracle_meta_intelligence_engine = None

try:
    from .dynamic_engine_weight_optimizer import dynamic_engine_weight_optimizer
except Exception:  # pragma: no cover
    dynamic_engine_weight_optimizer = None

try:
    from .research_quality_scoring_engine import research_quality_scoring_engine
except Exception:  # pragma: no cover
    research_quality_scoring_engine = None

try:
    from .oracle_performance_attribution_engine import oracle_performance_attribution_engine
except Exception:  # pragma: no cover
    oracle_performance_attribution_engine = None

try:
    from .cross_engine_agreement_matrix import cross_engine_agreement_matrix
except Exception:  # pragma: no cover
    cross_engine_agreement_matrix = None

try:
    from .institutional_intelligence_score import institutional_intelligence_score_engine
except Exception:  # pragma: no cover
    institutional_intelligence_score_engine = None


class OracleAICoreV1:
    module_name = "oi_080_oracle_ai_core_v1"

    def __init__(
        self,
        meta_engine=None,
        weight_optimizer=None,
        quality_engine=None,
        attribution_engine=None,
        agreement_matrix=None,
        institutional_engine=None,
    ) -> None:
        self.meta_engine = meta_engine or oracle_meta_intelligence_engine
        self.weight_optimizer = weight_optimizer or dynamic_engine_weight_optimizer
        self.quality_engine = quality_engine or research_quality_scoring_engine
        self.attribution_engine = attribution_engine or oracle_performance_attribution_engine
        self.agreement_matrix = agreement_matrix or cross_engine_agreement_matrix
        self.institutional_engine = institutional_engine or institutional_intelligence_score_engine
        self._history = []

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "ai_core_version": "v1",
            "history_count": len(self._history),
            "engines": {
                "meta_engine": self._safe_status(self.meta_engine),
                "weight_optimizer": self._safe_status(self.weight_optimizer),
                "quality_engine": self._safe_status(self.quality_engine),
                "attribution_engine": self._safe_status(self.attribution_engine),
                "agreement_matrix": self._safe_status(self.agreement_matrix),
                "institutional_engine": self._safe_status(self.institutional_engine),
            },
        }

    def build_ai_research_envelope(
        self,
        packet: Dict[str, Any],
        actual_side: Optional[str] = None,
        runtime_status: Optional[Dict[str, Any]] = None,
        record: bool = True,
    ) -> Dict[str, Any]:
        meta_report = self._meta_report()
        weight_report = self._weight_report(meta_report)
        quality_report = self._quality_report(packet, meta_report, weight_report, runtime_status)
        attribution_report = self._attribution_report(packet, actual_side)
        agreement_report = self._agreement_report(packet, actual_side, record=record)
        institutional_report = self._institutional_report(
            packet=packet,
            meta_report=meta_report,
            weight_report=weight_report,
            quality_report=quality_report,
            attribution_report=attribution_report,
            agreement_report=agreement_report,
            runtime_status=runtime_status,
        )

        envelope = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "ai_core_version": "v1",
            "created_at": self._now(),
            "market_ticker": self._ticker(packet),
            "oracle_research_packet": packet,
            "meta_intelligence": meta_report,
            "dynamic_weights": weight_report,
            "research_quality": quality_report,
            "performance_attribution": attribution_report,
            "cross_engine_agreement": agreement_report,
            "institutional_intelligence": institutional_report,
            "final_summary": self._final_summary(
                quality_report,
                institutional_report,
                agreement_report,
                attribution_report,
            ),
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }

        if record:
            self._history.append(envelope)

        return envelope

    def history(self, limit: int = 25) -> Dict[str, Any]:
        return {
            "status": "ok",
            "read_only": True,
            "count": len(self._history),
            "items": self._history[-limit:],
        }

    def _meta_report(self) -> Dict[str, Any]:
        if self.meta_engine and hasattr(self.meta_engine, "evaluate_engines"):
            return self.meta_engine.evaluate_engines()
        return {"status": "unavailable", "read_only": True, "overall_health": 60.0}

    def _weight_report(self, meta_report: Dict[str, Any]) -> Dict[str, Any]:
        if self.weight_optimizer and hasattr(self.weight_optimizer, "optimize_weights"):
            return self.weight_optimizer.optimize_weights(meta_report=meta_report)
        return {"status": "unavailable", "read_only": True, "optimized_weights": {}}

    def _quality_report(
        self,
        packet: Dict[str, Any],
        meta_report: Dict[str, Any],
        weight_report: Dict[str, Any],
        runtime_status: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if self.quality_engine and hasattr(self.quality_engine, "score_packet"):
            return self.quality_engine.score_packet(packet, meta_report, weight_report, runtime_status)
        return {"status": "unavailable", "read_only": True, "research_quality_score": 0.0, "grade": "UNRATED"}

    def _attribution_report(self, packet: Dict[str, Any], actual_side: Optional[str]) -> Dict[str, Any]:
        if self.attribution_engine and hasattr(self.attribution_engine, "attribute_packet"):
            return self.attribution_engine.attribute_packet(packet, actual_side=actual_side)
        return {"status": "unavailable", "read_only": True, "attribution": {}}

    def _agreement_report(self, packet: Dict[str, Any], actual_side: Optional[str], record: bool = True) -> Dict[str, Any]:
        if self.agreement_matrix and hasattr(self.agreement_matrix, "analyze_consensus_packet"):
            return self.agreement_matrix.analyze_consensus_packet(packet, actual_side=actual_side, record=record)
        return {"status": "unavailable", "read_only": True, "consensus_diversity": {}}

    def _institutional_report(
        self,
        packet: Dict[str, Any],
        meta_report: Dict[str, Any],
        weight_report: Dict[str, Any],
        quality_report: Dict[str, Any],
        attribution_report: Dict[str, Any],
        agreement_report: Dict[str, Any],
        runtime_status: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if self.institutional_engine:
            if hasattr(self.institutional_engine, "score"):
                return self.institutional_engine.score(
                    packet=packet,
                    meta_report=meta_report,
                    weight_report=weight_report,
                    quality_report=quality_report,
                    attribution_report=attribution_report,
                    agreement_report=agreement_report,
                    runtime_status=runtime_status,
                )
            if hasattr(self.institutional_engine, "score_packet"):
                return self.institutional_engine.score_packet(
                    packet=packet,
                    meta_report=meta_report,
                    weight_report=weight_report,
                    quality_report=quality_report,
                    attribution_report=attribution_report,
                    agreement_report=agreement_report,
                    runtime_status=runtime_status,
                )

        quality = float(quality_report.get("research_quality_score", 0.0) or 0.0)
        meta = float(meta_report.get("overall_health", 60.0) or 60.0)
        diversity = float((agreement_report.get("consensus_diversity", {}) or {}).get("diversity_score", 60.0) or 60.0)
        alpha = float((attribution_report.get("attribution", {}) or {}).get("alpha_added", 0.0) or 0.0)
        score = max(0.0, min(100.0, quality * 0.45 + meta * 0.25 + diversity * 0.20 + max(alpha, 0.0) * 0.10))
        return {
            "status": "ok",
            "read_only": True,
            "institutional_intelligence_score": round(score, 2),
            "grade": self._grade(score),
            "institutional_ready": score >= 85,
            "source": "ai_core_fallback",
        }

    def _final_summary(
        self,
        quality_report: Dict[str, Any],
        institutional_report: Dict[str, Any],
        agreement_report: Dict[str, Any],
        attribution_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        institutional_score = institutional_report.get("institutional_intelligence_score")
        if institutional_score is None:
            institutional_score = institutional_report.get("score")

        return {
            "research_quality_score": quality_report.get("research_quality_score"),
            "research_quality_grade": quality_report.get("grade"),
            "institutional_intelligence_score": institutional_score,
            "institutional_grade": institutional_report.get("grade"),
            "institutional_ready": institutional_report.get("institutional_ready", False),
            "consensus_diversity": (agreement_report.get("consensus_diversity", {}) or {}).get("diversity_level"),
            "largest_positive_contributor": (attribution_report.get("attribution", {}) or {}).get("largest_positive_contributor"),
            "largest_negative_contributor": (attribution_report.get("attribution", {}) or {}).get("largest_negative_contributor"),
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }

    def _ticker(self, packet: Dict[str, Any]) -> Optional[str]:
        return packet.get("market_ticker") or (packet.get("summary", {}) or {}).get("market_ticker")

    def _safe_status(self, engine: Any) -> str:
        if engine is None:
            return "unavailable"
        try:
            return engine.status().get("status", "unknown")
        except Exception:
            return "error"

    def _grade(self, score: float) -> str:
        if score >= 95:
            return "A+"
        if score >= 90:
            return "A"
        if score >= 85:
            return "A-"
        if score >= 80:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "WATCH"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


oracle_ai_core_v1 = OracleAICoreV1()
