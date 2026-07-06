from pathlib import Path

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
