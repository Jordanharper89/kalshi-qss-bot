from pathlib import Path

ROOT = Path.cwd()
OI_DIR = ROOT / "qseries_v2" / "oracle_intelligence"
ENGINE = OI_DIR / "adaptive_confidence_learning_engine.py"
TEST = ROOT / "test_oi_049_adaptive_confidence_learning_engine.py"
INIT = OI_DIR / "__init__.py"

OI_DIR.mkdir(parents=True, exist_ok=True)

engine_code = r'''"""
OI-049 Adaptive Confidence Learning Engine

Learns how much Oracle should trust its own confidence.

Purpose:
- Measure calibration from historical forecast/outcome memories.
- Compute confidence bucket accuracy.
- Estimate overconfidence / underconfidence drift.
- Produce confidence adjustment guidance for future forecasts.

Read-only:
- No execution.
- No order placement.
- No trade mutation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional
import math

from .oracle_memory_persistence_bridge import (
    oracle_memory_persistence_bridge,
    OracleMemoryPersistenceBridge,
)


class AdaptiveConfidenceLearningEngine:
    module_name = "oi_049_adaptive_confidence_learning_engine"

    def __init__(self, memory_bridge: Optional[OracleMemoryPersistenceBridge] = None) -> None:
        self.memory_bridge = memory_bridge or oracle_memory_persistence_bridge

    def status(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "memory_bridge": self.memory_bridge.status()["status"],
        }

    def learn_confidence(
        self,
        memory_type: Optional[str] = None,
        market_ticker: Optional[str] = None,
        limit: int = 10000,
    ) -> Dict[str, Any]:
        records = self.memory_bridge.recall_persistent(
            memory_type=memory_type,
            market_ticker=market_ticker,
            limit=limit,
        )

        examples = [self._extract_example(r) for r in records]
        examples = [e for e in examples if e is not None]

        buckets = self._bucket_stats(examples)
        overall = self._overall_stats(examples)
        segments = self._segment_stats(examples)
        adjustment = self._confidence_adjustment(overall, buckets)

        return {
            "module": self.module_name,
            "status": "ok",
            "read_only": True,
            "records_scanned": len(records),
            "usable_examples": len(examples),
            "overall": overall,
            "confidence_buckets": buckets,
            "segments": segments,
            "confidence_adjustment": adjustment,
        }

    def adjust_confidence(
        self,
        raw_confidence: float,
        context: Optional[Dict[str, Any]] = None,
        learning_report: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        report = learning_report or self.learn_confidence()
        adjustment = report.get("confidence_adjustment", {})
        drift = float(adjustment.get("recommended_delta", 0.0))

        context = context or {}
        bucket = self._confidence_bucket(raw_confidence)

        bucket_stats = report.get("confidence_buckets", {}).get(bucket)
        bucket_delta = 0.0

        if bucket_stats and bucket_stats.get("count", 0) >= 3:
            bucket_delta = float(bucket_stats.get("accuracy", 0.0) * 100.0 - bucket_stats.get("avg_confidence", raw_confidence))

        total_delta = (drift * 0.60) + (bucket_delta * 0.40)
        adjusted = max(0.0, min(100.0, float(raw_confidence) + total_delta))

        return {
            "status": "ok",
            "read_only": True,
            "raw_confidence": round(float(raw_confidence), 2),
            "adjusted_confidence": round(adjusted, 2),
            "delta": round(adjusted - float(raw_confidence), 2),
            "bucket": bucket,
            "reason": adjustment.get("reason", "No calibration adjustment available."),
            "context": context,
        }

    def _extract_example(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload = record.get("payload", {}) or {}

        forecast = payload.get("forecast", {}) if isinstance(payload.get("forecast"), dict) else {}
        outcome = payload.get("outcome", {}) if isinstance(payload.get("outcome"), dict) else {}

        confidence = (
            forecast.get("confidence")
            or payload.get("confidence")
            or record.get("confidence")
        )

        predicted = (
            forecast.get("predicted_side")
            or forecast.get("expected_resolution")
            or payload.get("predicted_side")
            or payload.get("expected_resolution")
        )

        actual = (
            outcome.get("result")
            or outcome.get("resolved_side")
            or outcome.get("winner")
            or payload.get("result")
            or payload.get("resolved_side")
        )

        probability = (
            forecast.get("probability")
            or forecast.get("yes_probability")
            or payload.get("probability")
            or payload.get("yes_probability")
        )

        if confidence is None or predicted is None or actual is None:
            return None

        predicted = str(predicted).upper()
        actual = str(actual).upper()

        if predicted not in {"YES", "NO"} or actual not in {"YES", "NO"}:
            return None

        confidence = float(confidence)
        confidence_prob = max(0.0, min(1.0, confidence / 100.0))

        if probability is None:
            predicted_yes_prob = confidence_prob if predicted == "YES" else 1.0 - confidence_prob
        else:
            predicted_yes_prob = max(0.0, min(1.0, float(probability)))

        actual_yes = 1.0 if actual == "YES" else 0.0
        correct = predicted == actual

        return {
            "memory_id": record.get("memory_id"),
            "market_ticker": record.get("market_ticker"),
            "confidence": confidence,
            "confidence_prob": confidence_prob,
            "bucket": self._confidence_bucket(confidence),
            "predicted": predicted,
            "actual": actual,
            "correct": correct,
            "predicted_yes_prob": predicted_yes_prob,
            "actual_yes": actual_yes,
            "brier": (predicted_yes_prob - actual_yes) ** 2,
            "category": payload.get("category") or forecast.get("category"),
            "regime": payload.get("regime") or forecast.get("regime"),
            "strategy": payload.get("strategy") or forecast.get("strategy"),
            "pattern_name": payload.get("pattern_name") or forecast.get("pattern_name"),
        }

    def _overall_stats(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not examples:
            return {
                "count": 0,
                "accuracy": None,
                "avg_confidence": None,
                "calibration_drift": None,
                "brier_score": None,
                "log_loss": None,
            }

        accuracy = sum(1 for e in examples if e["correct"]) / len(examples)
        avg_conf = sum(e["confidence"] for e in examples) / len(examples)
        brier = sum(e["brier"] for e in examples) / len(examples)
        log_loss = self._log_loss(examples)

        return {
            "count": len(examples),
            "accuracy": round(accuracy, 4),
            "avg_confidence": round(avg_conf, 2),
            "calibration_drift": round((accuracy * 100.0) - avg_conf, 2),
            "brier_score": round(brier, 4),
            "log_loss": round(log_loss, 4),
        }

    def _bucket_stats(self, examples: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        grouped = defaultdict(list)

        for e in examples:
            grouped[e["bucket"]].append(e)

        output = {}

        for bucket, rows in grouped.items():
            accuracy = sum(1 for e in rows if e["correct"]) / len(rows)
            avg_conf = sum(e["confidence"] for e in rows) / len(rows)
            brier = sum(e["brier"] for e in rows) / len(rows)

            output[bucket] = {
                "count": len(rows),
                "accuracy": round(accuracy, 4),
                "avg_confidence": round(avg_conf, 2),
                "calibration_drift": round((accuracy * 100.0) - avg_conf, 2),
                "brier_score": round(brier, 4),
            }

        return dict(sorted(output.items()))

    def _segment_stats(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "category": self._group_accuracy(examples, "category"),
            "regime": self._group_accuracy(examples, "regime"),
            "strategy": self._group_accuracy(examples, "strategy"),
            "pattern_name": self._group_accuracy(examples, "pattern_name"),
        }

    def _group_accuracy(self, examples: List[Dict[str, Any]], key: str) -> Dict[str, Any]:
        grouped = defaultdict(list)

        for e in examples:
            value = e.get(key)
            if value:
                grouped[str(value)].append(e)

        output = {}

        for value, rows in grouped.items():
            accuracy = sum(1 for e in rows if e["correct"]) / len(rows)
            avg_conf = sum(e["confidence"] for e in rows) / len(rows)

            output[value] = {
                "count": len(rows),
                "accuracy": round(accuracy, 4),
                "avg_confidence": round(avg_conf, 2),
                "calibration_drift": round((accuracy * 100.0) - avg_conf, 2),
            }

        return output

    def _confidence_adjustment(self, overall: Dict[str, Any], buckets: Dict[str, Any]) -> Dict[str, Any]:
        if not overall.get("count"):
            return {
                "recommended_delta": 0.0,
                "direction": "none",
                "reason": "No usable forecast/outcome examples available.",
            }

        drift = float(overall.get("calibration_drift", 0.0))

        if drift <= -10:
            direction = "decrease"
            reason = "Oracle has been materially overconfident versus realized accuracy."
        elif drift >= 10:
            direction = "increase"
            reason = "Oracle has been materially underconfident versus realized accuracy."
        else:
            direction = "hold"
            reason = "Oracle confidence is reasonably calibrated."

        recommended_delta = max(-15.0, min(15.0, drift * 0.50))

        return {
            "recommended_delta": round(recommended_delta, 2),
            "direction": direction,
            "reason": reason,
        }

    def _confidence_bucket(self, confidence: float) -> str:
        c = max(0.0, min(100.0, float(confidence)))
        lower = int(c // 10) * 10
        upper = min(lower + 10, 100)

        if lower == 100:
            return "100"

        return f"{lower}-{upper}"

    def _log_loss(self, examples: List[Dict[str, Any]]) -> float:
        eps = 1e-9
        losses = []

        for e in examples:
            p = max(eps, min(1 - eps, e["predicted_yes_prob"]))
            y = e["actual_yes"]
            losses.append(-(y * math.log(p) + (1 - y) * math.log(1 - p)))

        return sum(losses) / len(losses) if losses else 0.0


adaptive_confidence_learning_engine = AdaptiveConfidenceLearningEngine()
'''

test_code = r'''from pathlib import Path

from qseries_v2.oracle_intelligence.oracle_memory_engine import OracleMemoryEngine
from qseries_v2.oracle_intelligence.oracle_persistent_memory_store import OraclePersistentMemoryStore
from qseries_v2.oracle_intelligence.oracle_memory_persistence_bridge import OracleMemoryPersistenceBridge
from qseries_v2.oracle_intelligence.adaptive_confidence_learning_engine import AdaptiveConfidenceLearningEngine


def test_oi_049_adaptive_confidence_learning_engine():
    test_db = Path("qseries_v2") / "data" / "test_adaptive_confidence.sqlite3"

    if test_db.exists():
        test_db.unlink()

    memory_engine = OracleMemoryEngine()
    store = OraclePersistentMemoryStore(test_db)
    bridge = OracleMemoryPersistenceBridge(memory_engine, store)
    learner = AdaptiveConfidenceLearningEngine(bridge)

    for i in range(8):
        bridge.remember_and_persist(
            memory_type="forecast",
            market_ticker=f"CAL-YES-{i}",
            title=f"Calibration correct YES {i}",
            summary="Forecast resolved correctly.",
            confidence=85,
            importance=80,
            tags=["calibration", "correct"],
            source_module="test_oi_049",
            payload={
                "category": "crypto",
                "regime": "trend",
                "strategy": "momentum",
                "pattern_name": "strong_momentum",
                "forecast": {
                    "predicted_side": "YES",
                    "confidence": 85,
                    "probability": 0.85,
                },
                "outcome": {
                    "result": "YES",
                },
            },
        )

    for i in range(2):
        bridge.remember_and_persist(
            memory_type="forecast",
            market_ticker=f"CAL-WRONG-{i}",
            title=f"Calibration wrong YES {i}",
            summary="Forecast resolved incorrectly.",
            confidence=90,
            importance=70,
            tags=["calibration", "wrong"],
            source_module="test_oi_049",
            payload={
                "category": "crypto",
                "regime": "trend",
                "strategy": "momentum",
                "pattern_name": "strong_momentum",
                "forecast": {
                    "predicted_side": "YES",
                    "confidence": 90,
                    "probability": 0.90,
                },
                "outcome": {
                    "result": "NO",
                },
            },
        )

    report = learner.learn_confidence(memory_type="forecast")

    assert report["status"] == "ok"
    assert report["read_only"] is True
    assert report["usable_examples"] == 10
    assert report["overall"]["accuracy"] == 0.8
    assert report["overall"]["brier_score"] is not None
    assert "80-90" in report["confidence_buckets"] or "90-100" in report["confidence_buckets"]
    assert "crypto" in report["segments"]["category"]

    adjusted = learner.adjust_confidence(90, learning_report=report)

    assert adjusted["status"] == "ok"
    assert adjusted["read_only"] is True
    assert adjusted["adjusted_confidence"] <= 90

    status = learner.status()
    assert status["status"] == "ok"

    print("[PASS] OI-049 Adaptive Confidence Learning Engine")
    print({
        "overall": report["overall"],
        "confidence_adjustment": report["confidence_adjustment"],
        "adjusted": adjusted,
    })


if __name__ == "__main__":
    test_oi_049_adaptive_confidence_learning_engine()
'''

ENGINE.write_text(engine_code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_text = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
export_line = "from .adaptive_confidence_learning_engine import adaptive_confidence_learning_engine, AdaptiveConfidenceLearningEngine\n"

if export_line not in init_text:
    init_text += "\n" + export_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-049 INSTALLER")
print(" Adaptive Confidence Learning Engine")
print("========================================")
print(f"[OK] Wrote {ENGINE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-049 installed")
print()
print("Run:")
print("python test_oi_049_adaptive_confidence_learning_engine.py")