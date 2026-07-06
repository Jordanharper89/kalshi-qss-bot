from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "institutional_intelligence_score.py"
TEST = ROOT / "test_oi_079_institutional_intelligence_score.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-079 Institutional Intelligence Score

Purpose:
- Combine Oracle's institutional intelligence layers into one final score.
- Consume research quality, meta intelligence, dynamic weights, attribution,
  cross-engine agreement, consensus, runtime health, and portfolio state.
- Produce a single institutional readiness score for Q Series to consume.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class InstitutionalIntelligenceScore:
    module_name = "oi_079_institutional_intelligence_score"

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "purpose": "institutional_readiness_scoring",
        }

    def score(
        self,
        packet: Dict[str, Any],
        quality_report: Optional[Dict[str, Any]] = None,
        meta_report: Optional[Dict[str, Any]] = None,
        weight_report: Optional[Dict[str, Any]] = None,
        attribution_report: Optional[Dict[str, Any]] = None,
        agreement_report: Optional[Dict[str, Any]] = None,
        runtime_status: Optional[Dict[str, Any]] = None,
        portfolio_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        dimensions = {
            "research_quality": self._research_quality(quality_report),
            "consensus_strength": self._consensus_strength(packet),
            "engine_health": self._engine_health(meta_report),
            "weight_stability": self._weight_stability(weight_report),
            "performance_attribution": self._performance_attribution(attribution_report),
            "cross_engine_agreement": self._cross_engine_agreement(agreement_report),
            "runtime_health": self._runtime_health(runtime_status),
            "portfolio_context": self._portfolio_context(portfolio_report),
            "evidence_completeness": self._evidence_completeness(packet, quality_report),
            "risk_control": self._risk_control(packet, quality_report, portfolio_report),
        }

        penalties = {
            "drift_penalty": self._drift_penalty(packet, quality_report, agreement_report),
            "runtime_penalty": self._runtime_penalty(runtime_status),
            "portfolio_penalty": self._portfolio_penalty(portfolio_report),
            "missing_intelligence_penalty": self._missing_intelligence_penalty(
                quality_report,
                meta_report,
                weight_report,
                attribution_report,
                agreement_report,
                runtime_status,
                portfolio_report,
            ),
        }

        raw_score = self._weighted_score(dimensions)
        total_penalty = sum(penalties.values())
        final_score = max(0.0, min(100.0, raw_score - total_penalty))

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "institutional_intelligence_score": round(final_score, 2),
            "institutional_grade": self._grade(final_score),
            "institutional_ready": final_score >= 85.0,
            "deployment_readiness": self._readiness_label(final_score),
            "dimensions": {k: round(v, 2) for k, v in dimensions.items()},
            "penalties": {k: round(v, 2) for k, v in penalties.items()},
            "summary": self._summary(final_score, dimensions, penalties),
            "q_series_interface": {
                "execution_enabled": False,
                "execution_owner": "Q Series",
                "research_only": True,
                "consume_as": "institutional_research_score",
            },
            "missing_inputs": self._missing_inputs(
                quality_report,
                meta_report,
                weight_report,
                attribution_report,
                agreement_report,
                runtime_status,
                portfolio_report,
            ),
        }

    def _weighted_score(self, dimensions: Dict[str, float]) -> float:
        weights = {
            "research_quality": 0.18,
            "consensus_strength": 0.14,
            "engine_health": 0.12,
            "weight_stability": 0.08,
            "performance_attribution": 0.12,
            "cross_engine_agreement": 0.10,
            "runtime_health": 0.08,
            "portfolio_context": 0.07,
            "evidence_completeness": 0.06,
            "risk_control": 0.05,
        }
        return sum(dimensions[k] * weights[k] for k in weights)

    def _research_quality(self, quality_report: Optional[Dict[str, Any]]) -> float:
        if not quality_report:
            return 55.0
        return self._clamp(quality_report.get("research_quality_score"), 55.0)

    def _consensus_strength(self, packet: Dict[str, Any]) -> float:
        consensus = packet.get("consensus", {}) or {}
        summary = packet.get("summary", {}) or {}

        score = self._num(consensus.get("consensus_score_pct") or summary.get("consensus_score_pct"), 50.0)
        agreement = self._num(consensus.get("agreement_pct") or summary.get("agreement_pct"), 50.0)
        certainty = self._num(consensus.get("research_certainty_index") or summary.get("research_certainty_index"), 50.0)

        return self._clamp((score * 0.40) + (agreement * 0.35) + (certainty * 0.25))

    def _engine_health(self, meta_report: Optional[Dict[str, Any]]) -> float:
        if not meta_report:
            return 55.0
        return self._clamp(meta_report.get("overall_health"), 55.0)

    def _weight_stability(self, weight_report: Optional[Dict[str, Any]]) -> float:
        if not weight_report:
            return 55.0

        weights = weight_report.get("optimized_weights", {}) or {}
        deltas = weight_report.get("weight_deltas", {}) or {}

        if not weights:
            return 55.0

        total = sum(float(v) for v in weights.values())
        max_weight = max(float(v) for v in weights.values())
        max_delta = max(abs(float(v)) for v in deltas.values()) if deltas else 0.0

        score = 100.0
        score -= abs(1.0 - total) * 100.0
        score -= max(0.0, max_weight - 0.40) * 100.0
        score -= min(max_delta * 100.0, 25.0)

        return self._clamp(score)

    def _performance_attribution(self, attribution_report: Optional[Dict[str, Any]]) -> float:
        if not attribution_report:
            return 55.0

        attribution = attribution_report.get("attribution", {}) or {}
        alpha = self._num(attribution.get("alpha_added"), 0.0)
        noise = self._num(attribution.get("noise_score"), 0.0)
        positive_count = self._num(attribution.get("positive_support_count"), 0.0)
        negative_count = self._num(attribution.get("negative_support_count"), 0.0)

        score = 60.0
        score += alpha * 0.25
        score -= noise * 0.20
        score += min(positive_count, 8.0) * 4.0
        score -= min(negative_count, 8.0) * 4.0

        return self._clamp(score)

    def _cross_engine_agreement(self, agreement_report: Optional[Dict[str, Any]]) -> float:
        if not agreement_report:
            return 55.0

        diversity = agreement_report.get("consensus_diversity", {}) or {}
        summary = agreement_report.get("summary", {}) or {}

        diversity_score = self._num(diversity.get("diversity_score"), 50.0)
        pair_count = self._num(agreement_report.get("pair_count"), 0.0)
        agreement_pairs = self._num(summary.get("agreement_pairs"), 0.0)
        disagreement_pairs = self._num(summary.get("disagreement_pairs"), 0.0)

        pair_quality = 50.0
        if pair_count > 0:
            pair_quality = (agreement_pairs / pair_count) * 100.0
            pair_quality -= min(disagreement_pairs, 10.0) * 2.0

        return self._clamp((diversity_score * 0.55) + (pair_quality * 0.45))

    def _runtime_health(self, runtime_status: Optional[Dict[str, Any]]) -> float:
        if not runtime_status:
            return 65.0

        health = runtime_status.get("health")
        metrics = runtime_status.get("metrics", {}) or {}
        errors = self._num(metrics.get("errors"), 0.0)

        if health == "healthy":
            score = 100.0
        elif health == "degraded":
            score = 65.0
        else:
            score = 50.0

        score -= min(errors * 8.0, 40.0)
        return self._clamp(score)

    def _portfolio_context(self, portfolio_report: Optional[Dict[str, Any]]) -> float:
        if not portfolio_report:
            return 65.0

        state = (portfolio_report.get("portfolio_state", {}) or {}).get("state")
        risk = portfolio_report.get("risk_summary", {}) or {}
        drift = portfolio_report.get("drift_summary", {}) or {}

        score = 75.0

        if state == "strong_alignment":
            score += 15.0
        elif state == "normal":
            score += 5.0
        elif state == "risk_elevated":
            score -= 10.0
        elif state == "unstable":
            score -= 20.0

        score -= min(self._num(risk.get("high_risk_signals"), 0.0) * 5.0, 25.0)
        counts = drift.get("counts", {}) or {}
        score -= min(self._num(counts.get("side_changed"), 0.0) * 10.0, 30.0)

        return self._clamp(score)

    def _evidence_completeness(self, packet: Dict[str, Any], quality_report: Optional[Dict[str, Any]]) -> float:
        missing = []
        if quality_report:
            missing.extend(quality_report.get("missing_evidence", []) or [])
        else:
            missing.append("Research quality report")

        summary = packet.get("summary", {}) or {}
        if not packet.get("consensus_votes"):
            missing.append("Consensus votes")
        if not packet.get("consensus"):
            missing.append("Consensus object")
        if not summary.get("top_analog"):
            missing.append("Top analog")
        if not summary.get("analog_count"):
            missing.append("Analog count")

        return self._clamp(100.0 - len(set(missing)) * 7.5)

    def _risk_control(self, packet: Dict[str, Any], quality_report: Optional[Dict[str, Any]], portfolio_report: Optional[Dict[str, Any]]) -> float:
        summary = packet.get("summary", {}) or {}
        signals = packet.get("signals", {}) or {}

        risk = str(summary.get("risk_level") or signals.get("risk_level") or "unknown").lower()
        tail = str(summary.get("tail_risk_level") or signals.get("tail_risk_level") or "unknown").lower()

        score = 85.0
        if risk == "high":
            score -= 25.0
        elif risk == "medium":
            score -= 10.0
        elif risk == "low":
            score += 5.0

        if tail == "high":
            score -= 25.0
        elif tail == "medium":
            score -= 10.0
        elif tail == "low":
            score += 5.0

        if quality_report:
            penalties = quality_report.get("penalties", {}) or {}
            score -= self._num(penalties.get("risk_penalty"), 0.0) * 0.5

        if portfolio_report:
            state = (portfolio_report.get("portfolio_state", {}) or {}).get("state")
            if state in {"risk_elevated", "unstable"}:
                score -= 10.0

        return self._clamp(score)

    def _drift_penalty(self, packet: Dict[str, Any], quality_report: Optional[Dict[str, Any]], agreement_report: Optional[Dict[str, Any]]) -> float:
        penalty = 0.0
        if quality_report:
            penalty += self._num((quality_report.get("penalties", {}) or {}).get("drift_penalty"), 0.0) * 0.35

        summary = packet.get("summary", {}) or {}
        outliers = summary.get("outlier_engines") or (packet.get("consensus", {}) or {}).get("outlier_engines") or []
        penalty += len(outliers) * 2.0

        if agreement_report:
            diversity = agreement_report.get("consensus_diversity", {}) or {}
            if diversity.get("diversity_level") == "low":
                penalty += 6.0

        return penalty

    def _runtime_penalty(self, runtime_status: Optional[Dict[str, Any]]) -> float:
        if not runtime_status:
            return 1.5
        if runtime_status.get("health") == "degraded":
            return 8.0
        return 0.0

    def _portfolio_penalty(self, portfolio_report: Optional[Dict[str, Any]]) -> float:
        if not portfolio_report:
            return 0.0
        state = (portfolio_report.get("portfolio_state", {}) or {}).get("state")
        if state == "unstable":
            return 10.0
        if state == "risk_elevated":
            return 5.0
        return 0.0

    def _missing_intelligence_penalty(self, *items: Optional[Dict[str, Any]]) -> float:
        missing = sum(1 for item in items if item is None)
        return min(12.0, missing * 1.5)

    def _missing_inputs(self, *items: Optional[Dict[str, Any]]) -> List[str]:
        names = [
            "quality_report",
            "meta_report",
            "weight_report",
            "attribution_report",
            "agreement_report",
            "runtime_status",
            "portfolio_report",
        ]
        return [name for name, item in zip(names, items) if item is None]

    def _summary(self, score: float, dimensions: Dict[str, float], penalties: Dict[str, float]) -> Dict[str, Any]:
        strongest = max(dimensions.items(), key=lambda kv: kv[1])
        weakest = min(dimensions.items(), key=lambda kv: kv[1])
        total_penalty = sum(penalties.values())

        return {
            "headline": f"Institutional intelligence is {self._readiness_label(score)} ({self._grade(score)}).",
            "strongest_dimension": strongest[0],
            "weakest_dimension": weakest[0],
            "total_penalty": round(total_penalty, 2),
            "interpretation": self._interpretation(score),
        }

    def _interpretation(self, score: float) -> str:
        if score >= 90:
            return "Oracle research is institutionally strong and suitable for high-trust downstream review."
        if score >= 85:
            return "Oracle research is institutionally ready with manageable weaknesses."
        if score >= 75:
            return "Oracle research is useful but should receive additional validation."
        if score >= 65:
            return "Oracle research is developing and should remain watch-only."
        return "Oracle research is weak or incomplete and should not influence execution decisions."

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

    def _readiness_label(self, score: float) -> str:
        if score >= 90:
            return "institutional_strong"
        if score >= 85:
            return "institutional_ready"
        if score >= 75:
            return "validation_required"
        if score >= 65:
            return "watch_only"
        return "not_ready"

    def _clamp(self, value: Any, default: float = 50.0) -> float:
        try:
            v = float(value)
        except Exception:
            v = default
        return max(0.0, min(100.0, v))

    def _num(self, value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except Exception:
            return default


institutional_intelligence_score = InstitutionalIntelligenceScore()
'''

test_code = r'''from qseries_v2.oracle_intelligence.institutional_intelligence_score import institutional_intelligence_score


def test_oi_079_institutional_intelligence_score():
    packet = {
        "market_ticker": "INST-TEST",
        "summary": {
            "market_ticker": "INST-TEST",
            "expected_resolution": "YES",
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
            "consensus_score_pct": 90,
            "agreement_pct": 92,
            "research_certainty_index": 89,
            "research_stability": "high",
            "risk_level": "low",
            "tail_risk_level": "low",
            "analog_count": 35,
            "graph_nodes": 30,
            "top_analog": {"market_ticker": "ANALOG-1", "similarity_pct": 89},
            "outlier_engines": [],
        },
        "signals": {
            "expected_resolution": "YES",
            "expected_probability": 0.88,
            "adjusted_confidence": 86,
            "risk_level": "low",
            "tail_risk_level": "low",
            "final_research_grade": "A",
            "execution_enabled": False,
        },
        "consensus": {
            "consensus_side": "YES",
            "consensus_score_pct": 90,
            "agreement_pct": 92,
            "research_certainty_index": 89,
            "research_stability": "high",
            "outlier_engines": [],
        },
        "consensus_votes": [
            {"engine": "case_reasoning_engine", "side": "YES", "confidence": 90, "weight": 0.24},
            {"engine": "outcome_distribution_engine", "side": "YES", "confidence": 86, "weight": 0.24},
            {"engine": "market_dna_engine", "side": "YES", "confidence": 82, "weight": 0.10},
        ],
    }

    quality = {
        "research_quality_score": 88.27,
        "grade": "A-",
        "institutional_ready": True,
        "missing_evidence": [],
        "penalties": {"drift_penalty": 0.0, "risk_penalty": 0.0},
    }

    meta = {
        "overall_health": 86,
        "research_quality": "strong",
        "best_engine": "case_reasoning_engine",
        "weakest_engine": "analog_retrieval_engine",
    }

    weights = {
        "optimized_weights": {
            "case_reasoning_engine": 0.28,
            "outcome_distribution_engine": 0.24,
            "analog_retrieval_engine": 0.16,
            "adaptive_confidence_engine": 0.14,
            "market_dna_engine": 0.10,
            "knowledge_graph_engine": 0.08,
        },
        "weight_deltas": {
            "case_reasoning_engine": 0.04,
            "outcome_distribution_engine": 0.0,
            "analog_retrieval_engine": -0.02,
            "adaptive_confidence_engine": -0.02,
            "market_dna_engine": 0.0,
            "knowledge_graph_engine": 0.0,
        },
    }

    attribution = {
        "attribution": {
            "alpha_added": 68,
            "noise_score": 8,
            "positive_support_count": 3,
            "negative_support_count": 0,
            "largest_positive_contributor": "case_reasoning_engine",
        }
    }

    agreement = {
        "pair_count": 3,
        "consensus_diversity": {
            "diversity_level": "high",
            "diversity_score": 84,
        },
        "summary": {
            "agreement_pairs": 3,
            "disagreement_pairs": 0,
        },
    }

    runtime = {
        "health": "healthy",
        "metrics": {"errors": 0},
    }

    portfolio = {
        "portfolio_state": {"state": "strong_alignment"},
        "risk_summary": {"high_risk_signals": 0},
        "drift_summary": {"counts": {"side_changed": 0}},
    }

    result = institutional_intelligence_score.score(
        packet=packet,
        quality_report=quality,
        meta_report=meta,
        weight_report=weights,
        attribution_report=attribution,
        agreement_report=agreement,
        runtime_status=runtime,
        portfolio_report=portfolio,
    )

    assert result["status"] == "ok"
    assert result["read_only"] is True
    assert result["q_series_interface"]["execution_enabled"] is False
    assert result["q_series_interface"]["execution_owner"] == "Q Series"
    assert result["institutional_intelligence_score"] >= 80
    assert result["institutional_grade"] in {"A+", "A", "A-", "B+"}
    assert result["deployment_readiness"] in {"institutional_strong", "institutional_ready", "validation_required"}

    status = institutional_intelligence_score.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-079 Institutional Intelligence Score")
    print({
        "score": result["institutional_intelligence_score"],
        "grade": result["institutional_grade"],
        "ready": result["institutional_ready"],
        "summary": result["summary"],
    })


if __name__ == "__main__":
    test_oi_079_institutional_intelligence_score()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .institutional_intelligence_score import institutional_intelligence_score, InstitutionalIntelligenceScore\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-079 INSTALLER")
print(" Institutional Intelligence Score")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-079 installed")
print()
print("Run:")
print("python test_oi_079_institutional_intelligence_score.py")

