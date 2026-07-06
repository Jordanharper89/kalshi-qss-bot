from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "oracle_meta_intelligence_engine.py"
TEST = ROOT / "test_oi_074_oracle_meta_intelligence_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-074 Oracle Meta Intelligence Engine

Purpose:
- Evaluate Oracle itself.
- Track subsystem reliability, calibration, drift, contribution, and research value.
- Produce recommended engine weight adjustments for future consensus/intelligence layers.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


DEFAULT_ENGINES = [
    "similarity_engine",
    "case_reasoning_engine",
    "market_dna_engine",
    "analog_retrieval_engine",
    "outcome_distribution_engine",
    "adaptive_confidence_engine",
    "knowledge_graph_engine",
    "consensus_engine",
    "drift_detection_engine",
    "portfolio_intelligence_engine",
]


class OracleMetaIntelligenceEngine:
    module_name = "oi_074_oracle_meta_intelligence_engine"

    def __init__(self) -> None:
        self._engine_history: Dict[str, List[Dict[str, Any]]] = {
            name: [] for name in DEFAULT_ENGINES
        }

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "engines_tracked": len(self._engine_history),
            "records": sum(len(v) for v in self._engine_history.values()),
        }

    def record_engine_result(
        self,
        engine_name: str,
        predicted_side: Optional[str] = None,
        actual_side: Optional[str] = None,
        confidence: Optional[float] = None,
        contribution_score: Optional[float] = None,
        drift_score: Optional[float] = None,
        lead_time_minutes: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        engine_name = str(engine_name)

        if engine_name not in self._engine_history:
            self._engine_history[engine_name] = []

        predicted = self._side(predicted_side)
        actual = self._side(actual_side)
        correct = predicted is not None and actual is not None and predicted == actual

        record = {
            "engine_name": engine_name,
            "predicted_side": predicted,
            "actual_side": actual,
            "correct": correct if predicted and actual else None,
            "confidence": self._num(confidence),
            "contribution_score": self._num(contribution_score, 50.0),
            "drift_score": self._num(drift_score, 0.0),
            "lead_time_minutes": self._num(lead_time_minutes),
            "metadata": metadata or {},
        }

        self._engine_history[engine_name].append(record)

        return {
            "status": "ok",
            "read_only": True,
            "engine_name": engine_name,
            "record": record,
            "records_for_engine": len(self._engine_history[engine_name]),
        }

    def evaluate_engines(self, recent_limit: Optional[int] = None) -> Dict[str, Any]:
        engine_scores = {}

        for engine_name, records in self._engine_history.items():
            rows = records[-recent_limit:] if recent_limit else records
            engine_scores[engine_name] = self._score_engine(engine_name, rows)

        ranked = sorted(
            engine_scores.values(),
            key=lambda r: r["meta_score"],
            reverse=True,
        )

        weight_changes = self._recommended_weight_changes(engine_scores)
        overall = self._overall_health(engine_scores)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "overall_health": overall,
            "research_quality": self._quality_label(overall),
            "best_engine": ranked[0]["engine_name"] if ranked else None,
            "weakest_engine": ranked[-1]["engine_name"] if ranked else None,
            "highest_drift_engine": self._highest_drift(engine_scores),
            "engine_scores": engine_scores,
            "ranked_engines": ranked,
            "recommended_weight_changes": weight_changes,
        }

    def evaluate_from_consensus_votes(
        self,
        consensus_packet: Dict[str, Any],
        actual_side: Optional[str] = None,
    ) -> Dict[str, Any]:
        votes = consensus_packet.get("consensus_votes", []) or []
        recorded = []

        for vote in votes:
            recorded.append(self.record_engine_result(
                engine_name=vote.get("engine", "unknown_engine"),
                predicted_side=vote.get("side"),
                actual_side=actual_side,
                confidence=vote.get("confidence"),
                contribution_score=float(vote.get("weight", 0.0)) * 100.0,
                drift_score=0.0,
                metadata={"source": "consensus_packet"},
            ))

        return {
            "status": "ok",
            "read_only": True,
            "votes_recorded": len(recorded),
            "evaluation": self.evaluate_engines(),
        }

    def _score_engine(self, engine_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {
                "engine_name": engine_name,
                "count": 0,
                "accuracy": None,
                "avg_confidence": None,
                "calibration_gap": None,
                "avg_contribution": 0.0,
                "avg_drift": 0.0,
                "avg_lead_time_minutes": None,
                "meta_score": 50.0,
                "health": "unknown",
            }

        resolved = [r for r in records if r.get("correct") is not None]
        accuracy = (
            sum(1 for r in resolved if r["correct"]) / len(resolved)
            if resolved else None
        )

        confidences = [r["confidence"] for r in records if r.get("confidence") is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else None

        contributions = [r.get("contribution_score", 50.0) for r in records]
        avg_contribution = sum(contributions) / len(contributions) if contributions else 50.0

        drifts = [abs(r.get("drift_score", 0.0) or 0.0) for r in records]
        avg_drift = sum(drifts) / len(drifts) if drifts else 0.0

        leads = [r["lead_time_minutes"] for r in records if r.get("lead_time_minutes") is not None]
        avg_lead = sum(leads) / len(leads) if leads else None

        calibration_gap = None
        if accuracy is not None and avg_conf is not None:
            calibration_gap = (accuracy * 100.0) - avg_conf

        meta_score = self._meta_score(
            accuracy=accuracy,
            avg_confidence=avg_conf,
            calibration_gap=calibration_gap,
            avg_contribution=avg_contribution,
            avg_drift=avg_drift,
            count=len(records),
        )

        return {
            "engine_name": engine_name,
            "count": len(records),
            "accuracy": round(accuracy, 4) if accuracy is not None else None,
            "avg_confidence": round(avg_conf, 2) if avg_conf is not None else None,
            "calibration_gap": round(calibration_gap, 2) if calibration_gap is not None else None,
            "avg_contribution": round(avg_contribution, 2),
            "avg_drift": round(avg_drift, 2),
            "avg_lead_time_minutes": round(avg_lead, 2) if avg_lead is not None else None,
            "meta_score": round(meta_score, 2),
            "health": self._engine_health(meta_score),
        }

    def _meta_score(
        self,
        accuracy: Optional[float],
        avg_confidence: Optional[float],
        calibration_gap: Optional[float],
        avg_contribution: float,
        avg_drift: float,
        count: int,
    ) -> float:
        score = 50.0

        if accuracy is not None:
            score += (accuracy * 100.0 - 50.0) * 0.45

        if calibration_gap is not None:
            score -= min(abs(calibration_gap), 30.0) * 0.35

        score += (avg_contribution - 50.0) * 0.20
        score -= min(avg_drift, 40.0) * 0.30
        score += min(count, 50) * 0.10

        return max(0.0, min(100.0, score))

    def _recommended_weight_changes(self, engine_scores: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        changes = {}

        for name, score in engine_scores.items():
            meta = score.get("meta_score", 50.0)
            drift = score.get("avg_drift", 0.0)

            if meta >= 85 and drift <= 5:
                change = 3.0
            elif meta >= 75:
                change = 1.5
            elif meta <= 45 or drift >= 20:
                change = -3.0
            elif meta <= 60:
                change = -1.5
            else:
                change = 0.0

            changes[name] = round(change, 2)

        return changes

    def _overall_health(self, engine_scores: Dict[str, Dict[str, Any]]) -> float:
        scores = [v.get("meta_score", 50.0) for v in engine_scores.values()]
        if not scores:
            return 50.0
        return round(sum(scores) / len(scores), 2)

    def _highest_drift(self, engine_scores: Dict[str, Dict[str, Any]]) -> Optional[str]:
        if not engine_scores:
            return None
        return max(engine_scores.values(), key=lambda x: x.get("avg_drift", 0.0))["engine_name"]

    def _quality_label(self, health: float) -> str:
        if health >= 90:
            return "institutional"
        if health >= 80:
            return "strong"
        if health >= 70:
            return "good"
        if health >= 60:
            return "developing"
        return "needs_attention"

    def _engine_health(self, score: float) -> str:
        if score >= 85:
            return "excellent"
        if score >= 75:
            return "strong"
        if score >= 60:
            return "stable"
        if score >= 45:
            return "weak"
        return "degraded"

    def _side(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        value = str(value).upper()
        return value if value in {"YES", "NO"} else None

    def _num(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            return float(value)
        except Exception:
            return default


oracle_meta_intelligence_engine = OracleMetaIntelligenceEngine()
'''

test_code = r'''from qseries_v2.oracle_intelligence.oracle_meta_intelligence_engine import OracleMetaIntelligenceEngine


def test_oi_074_oracle_meta_intelligence_engine():
    engine = OracleMetaIntelligenceEngine()

    for i in range(10):
        engine.record_engine_result(
            engine_name="consensus_engine",
            predicted_side="YES",
            actual_side="YES" if i < 9 else "NO",
            confidence=88,
            contribution_score=90,
            drift_score=2,
            lead_time_minutes=15,
        )

    for i in range(10):
        engine.record_engine_result(
            engine_name="analog_retrieval_engine",
            predicted_side="YES",
            actual_side="YES" if i < 6 else "NO",
            confidence=90,
            contribution_score=65,
            drift_score=18,
            lead_time_minutes=9,
        )

    report = engine.evaluate_engines()

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["engine_scores"]["consensus_engine"]["accuracy"] == 0.9
    assert report["engine_scores"]["analog_retrieval_engine"]["accuracy"] == 0.6
    assert report["engine_scores"]["consensus_engine"]["meta_score"] > report["engine_scores"]["analog_retrieval_engine"]["meta_score"]
    assert "recommended_weight_changes" in report

    packet_eval = engine.evaluate_from_consensus_votes(
        {
            "consensus_votes": [
                {"engine": "case_reasoning_engine", "side": "YES", "confidence": 84, "weight": 0.24},
                {"engine": "market_dna_engine", "side": "YES", "confidence": 78, "weight": 0.10},
            ]
        },
        actual_side="YES",
    )

    assert packet_eval["votes_recorded"] == 2

    status = engine.status()
    assert status["status"] == "ok"
    assert status["read_only"] is True

    print("[PASS] OI-074 Oracle Meta Intelligence Engine")
    print({
        "overall_health": report["overall_health"],
        "best_engine": report["best_engine"],
        "highest_drift_engine": report["highest_drift_engine"],
        "quality": report["research_quality"],
    })


if __name__ == "__main__":
    test_oi_074_oracle_meta_intelligence_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .oracle_meta_intelligence_engine import oracle_meta_intelligence_engine, OracleMetaIntelligenceEngine\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-074 INSTALLER")
print(" Oracle Meta Intelligence Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-074 installed")
print()
print("Run:")
print("python test_oi_074_oracle_meta_intelligence_engine.py")