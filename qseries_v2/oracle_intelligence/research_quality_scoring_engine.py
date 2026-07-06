"""
OI-076 Research Quality Scoring Engine

Purpose:
- Score the quality of an Oracle research packet.
- Evaluate evidence depth, diversity, agreement, calibration, memory strength,
  forecast strength, runtime health, meta intelligence, and drift risk.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ResearchQualityScoringEngine:
    module_name = "oi_076_research_quality_scoring_engine"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "purpose": "institutional_research_quality_scoring",
        }

    def score_packet(
        self,
        packet: Dict[str, Any],
        meta_report: Optional[Dict[str, Any]] = None,
        weight_report: Optional[Dict[str, Any]] = None,
        runtime_status: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        dimensions = {
            "evidence_depth": self._evidence_depth(packet),
            "evidence_diversity": self._evidence_diversity(packet),
            "agreement": self._agreement(packet),
            "calibration": self._calibration(meta_report),
            "historical_support": self._historical_support(packet),
            "forecast_strength": self._forecast_strength(packet),
            "memory_strength": self._memory_strength(packet),
            "runtime_health": self._runtime_health(runtime_status),
            "meta_intelligence": self._meta_intelligence(meta_report),
            "dynamic_weight_quality": self._dynamic_weight_quality(weight_report),
            "information_completeness": self._information_completeness(packet),
        }

        drift_penalty = self._drift_penalty(packet)
        risk_penalty = self._risk_penalty(packet)

        raw_score = sum(dimensions.values()) / len(dimensions)
        final_score = max(0.0, min(100.0, raw_score - drift_penalty - risk_penalty))

        result = {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "research_quality_score": round(final_score, 2),
            "grade": self._grade(final_score),
            "institutional_ready": final_score >= 85,
            "confidence_level": self._confidence_label(final_score),
            "dimensions": {k: round(v, 2) for k, v in dimensions.items()},
            "penalties": {
                "drift_penalty": round(drift_penalty, 2),
                "risk_penalty": round(risk_penalty, 2),
            },
            "missing_evidence": self._missing_evidence(packet, meta_report, weight_report, runtime_status),
            "summary": self._summary(final_score, dimensions, drift_penalty, risk_penalty),
            "execution_enabled": False,
            "execution_owner": "Q Series",
        }

        return result

    def _evidence_depth(self, packet: Dict[str, Any]) -> float:
        summary = packet.get("summary", {}) or {}
        raw = packet.get("raw", {}) or {}
        synthesis = raw.get("synthesis", {}) or {}

        analog_count = summary.get("analog_count")
        if analog_count is None:
            analog_count = (
                synthesis.get("analog_retrieval", {})
                .get("summary", {})
                .get("count", 0)
            )

        graph_nodes = summary.get("graph_nodes") or 0
        graph_edges = summary.get("graph_edges") or 0

        score = 40.0
        score += min(float(analog_count or 0), 50.0) * 0.8
        score += min(float(graph_nodes or 0), 50.0) * 0.2
        score += min(float(graph_edges or 0), 100.0) * 0.1

        return min(100.0, score)

    def _evidence_diversity(self, packet: Dict[str, Any]) -> float:
        present = 0
        total = 8

        if packet.get("consensus_votes"):
            present += 1
        if packet.get("consensus"):
            present += 1
        if packet.get("summary", {}).get("top_analog"):
            present += 1
        if packet.get("summary", {}).get("dna_id") or packet.get("summary", {}).get("dna_family"):
            present += 1
        if packet.get("summary", {}).get("graph_nodes"):
            present += 1
        if packet.get("summary", {}).get("expected_probability") is not None:
            present += 1
        if packet.get("summary", {}).get("adjusted_confidence") is not None:
            present += 1
        if packet.get("signals"):
            present += 1

        return (present / total) * 100.0

    def _agreement(self, packet: Dict[str, Any]) -> float:
        consensus = packet.get("consensus", {}) or {}
        agreement = consensus.get("agreement_pct") or packet.get("summary", {}).get("agreement_pct")

        if agreement is None:
            return 50.0

        return max(0.0, min(100.0, float(agreement)))

    def _calibration(self, meta_report: Optional[Dict[str, Any]]) -> float:
        if not meta_report:
            return 60.0

        health = float(meta_report.get("overall_health", 60.0) or 60.0)
        return max(0.0, min(100.0, health))

    def _historical_support(self, packet: Dict[str, Any]) -> float:
        summary = packet.get("summary", {}) or {}
        analog_count = float(summary.get("analog_count") or 0)
        top = summary.get("top_analog") or {}

        top_similarity = float(top.get("similarity_pct") or 0)
        retrieval = float(top.get("retrieval_score_pct") or 0)

        score = min(analog_count, 50.0) * 1.0
        score += top_similarity * 0.25
        score += retrieval * 0.25

        return max(0.0, min(100.0, score))

    def _forecast_strength(self, packet: Dict[str, Any]) -> float:
        summary = packet.get("summary", {}) or {}
        signals = packet.get("signals", {}) or {}

        probability = summary.get("expected_probability") or signals.get("expected_probability")
        confidence = summary.get("adjusted_confidence") or signals.get("adjusted_confidence")

        vals = []

        if probability is not None:
            p = float(probability)
            if p <= 1:
                p *= 100.0
            vals.append(p)

        if confidence is not None:
            vals.append(float(confidence))

        if not vals:
            return 50.0

        return max(0.0, min(100.0, sum(vals) / len(vals)))

    def _memory_strength(self, packet: Dict[str, Any]) -> float:
        summary = packet.get("summary", {}) or {}
        analog_count = float(summary.get("analog_count") or 0)
        graph_nodes = float(summary.get("graph_nodes") or 0)

        return min(100.0, 45.0 + min(analog_count, 40.0) + min(graph_nodes, 50.0) * 0.3)

    def _runtime_health(self, runtime_status: Optional[Dict[str, Any]]) -> float:
        if not runtime_status:
            return 75.0

        health = runtime_status.get("health")

        if health == "healthy":
            return 100.0
        if health == "degraded":
            return 65.0
        return 50.0

    def _meta_intelligence(self, meta_report: Optional[Dict[str, Any]]) -> float:
        if not meta_report:
            return 60.0

        return max(0.0, min(100.0, float(meta_report.get("overall_health", 60.0) or 60.0)))

    def _dynamic_weight_quality(self, weight_report: Optional[Dict[str, Any]]) -> float:
        if not weight_report:
            return 60.0

        weights = weight_report.get("optimized_weights", {}) or {}
        if not weights:
            return 60.0

        total = sum(float(v) for v in weights.values())
        spread = max(weights.values()) - min(weights.values()) if len(weights) > 1 else 0

        score = 100.0 - abs(1.0 - total) * 100.0 - float(spread) * 25.0
        return max(0.0, min(100.0, score))

    def _information_completeness(self, packet: Dict[str, Any]) -> float:
        missing = self._missing_evidence(packet, None, None, None)
        return max(0.0, 100.0 - len(missing) * 10.0)

    def _drift_penalty(self, packet: Dict[str, Any]) -> float:
        summary = packet.get("summary", {}) or {}
        outliers = summary.get("outlier_engines") or packet.get("consensus", {}).get("outlier_engines") or []
        stability = summary.get("research_stability") or packet.get("consensus", {}).get("research_stability")

        penalty = len(outliers) * 4.0

        if str(stability).lower() == "low":
            penalty += 12.0
        elif str(stability).lower() == "medium":
            penalty += 5.0

        return penalty

    def _risk_penalty(self, packet: Dict[str, Any]) -> float:
        summary = packet.get("summary", {}) or {}
        risk = str(summary.get("risk_level") or packet.get("signals", {}).get("risk_level") or "").lower()
        tail = str(summary.get("tail_risk_level") or packet.get("signals", {}).get("tail_risk_level") or "").lower()

        penalty = 0.0

        if risk == "high":
            penalty += 10.0
        elif risk == "medium":
            penalty += 4.0

        if tail == "high":
            penalty += 10.0
        elif tail == "medium":
            penalty += 4.0

        return penalty

    def _missing_evidence(
        self,
        packet: Dict[str, Any],
        meta_report: Optional[Dict[str, Any]],
        weight_report: Optional[Dict[str, Any]],
        runtime_status: Optional[Dict[str, Any]],
    ) -> List[str]:
        missing = []

        summary = packet.get("summary", {}) or {}

        if not packet.get("consensus_votes"):
            missing.append("Subsystem votes")

        if not summary.get("top_analog"):
            missing.append("Top historical analog")

        if not summary.get("dna_id") and not summary.get("dna_family"):
            missing.append("Market DNA")

        if not summary.get("graph_nodes"):
            missing.append("Knowledge graph context")

        if meta_report is None:
            missing.append("Meta intelligence report")

        if weight_report is None:
            missing.append("Dynamic weight report")

        if runtime_status is None:
            missing.append("Runtime health")

        return missing

    def _summary(self, score: float, dimensions: Dict[str, float], drift_penalty: float, risk_penalty: float) -> Dict[str, Any]:
        weakest = min(dimensions.items(), key=lambda kv: kv[1])
        strongest = max(dimensions.items(), key=lambda kv: kv[1])

        return {
            "headline": f"Research quality is {self._confidence_label(score)} ({self._grade(score)}).",
            "strongest_dimension": strongest[0],
            "weakest_dimension": weakest[0],
            "total_penalty": round(drift_penalty + risk_penalty, 2),
        }

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

    def _confidence_label(self, score: float) -> str:
        if score >= 90:
            return "Very High"
        if score >= 80:
            return "High"
        if score >= 70:
            return "Moderate"
        if score >= 60:
            return "Developing"
        return "Weak"


research_quality_scoring_engine = ResearchQualityScoringEngine()
