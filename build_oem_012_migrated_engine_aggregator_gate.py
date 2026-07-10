from pathlib import Path

ROOT = Path.cwd()
BASE = ROOT / "qseries_v2"
INTEGRATION = BASE / "integration"

GATE_PATH = INTEGRATION / "oem_012_migrated_engine_aggregator_gate.py"
TEST_PATH = ROOT / "test_oem_012_migrated_engine_aggregator_gate.py"
INIT_PATH = INTEGRATION / "__init__.py"

GATE_CODE = r'''"""
OEM-012 Migrated Engine Aggregator Gate

Validates migrated OEM Oracle engines as a unified prediction source.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


GATE_ID = "oracle.engine_migration.aggregator_gate"
GATE_NAME = "Migrated Engine Aggregator Gate"
GATE_VERSION = "OEM-012"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AggregatedEngineResult:
    engine_id: str
    status: str
    signal_count: int
    prediction_count: int
    read_only: bool
    error: Optional[str] = None


@dataclass
class MigratedAggregatorGateResult:
    gate_id: str
    status: str
    engine_count: int
    passed_count: int
    failed_count: int
    total_signals: int
    total_predictions: int
    engine_results: List[Dict[str, Any]]
    predictions: List[Any]
    telemetry: Dict[str, Any]
    generated_at: str = field(default_factory=_utc_now)


class MigratedEngineAggregatorGate:
    gate_id = GATE_ID
    name = GATE_NAME
    version = GATE_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None):
        self.runtime_paths = runtime_paths

    def run(self) -> MigratedAggregatorGateResult:
        engines = self._load_engines()
        engine_results: List[AggregatedEngineResult] = []
        predictions: List[Any] = []
        total_signals = 0

        for engine in engines:
            engine_id = getattr(engine, "engine_id", "unknown")
            try:
                read_only = bool(getattr(engine, "read_only", False))
                if not read_only:
                    raise AssertionError("engine is not read_only")

                payload = self._payload_for(engine_id)
                analyze_result = engine.analyze(payload)
                signals = getattr(analyze_result, "signals", [])
                if not isinstance(signals, list):
                    signals = []

                engine_predictions = engine.predict(payload)
                if not isinstance(engine_predictions, list):
                    engine_predictions = []

                if len(signals) < 1:
                    raise AssertionError("engine produced no signals")
                if len(engine_predictions) < 1:
                    raise AssertionError("engine produced no predictions")

                total_signals += len(signals)
                predictions.extend(engine_predictions)

                engine_results.append(
                    AggregatedEngineResult(
                        engine_id=engine_id,
                        status="pass",
                        signal_count=len(signals),
                        prediction_count=len(engine_predictions),
                        read_only=True,
                    )
                )

            except Exception as exc:
                engine_results.append(
                    AggregatedEngineResult(
                        engine_id=engine_id,
                        status="fail",
                        signal_count=0,
                        prediction_count=0,
                        read_only=bool(getattr(engine, "read_only", False)),
                        error=str(exc),
                    )
                )

        passed_count = sum(1 for item in engine_results if item.status == "pass")
        failed_count = sum(1 for item in engine_results if item.status == "fail")
        status = "pass" if failed_count == 0 and passed_count == len(engines) and len(predictions) >= len(engines) else "fail"

        return MigratedAggregatorGateResult(
            gate_id=self.gate_id,
            status=status,
            engine_count=len(engines),
            passed_count=passed_count,
            failed_count=failed_count,
            total_signals=total_signals,
            total_predictions=len(predictions),
            engine_results=[item.__dict__ for item in engine_results],
            predictions=predictions,
            telemetry={
                "gate": self.name,
                "version": self.version,
                "read_only": True,
                "aggregation_mode": "migrated_oem_engine_prediction_collection",
                "generated_at": _utc_now(),
            },
        )

    def _load_engines(self) -> List[Any]:
        from qseries_v2.integration.oem_011_oracle_engine_migration_registry_bridge import (
            OracleEngineMigrationRegistryBridge,
        )

        bridge = OracleEngineMigrationRegistryBridge(runtime_paths=self.runtime_paths)
        return bridge.build_all()

    def _payload_for(self, engine_id: str) -> Dict[str, Any]:
        market_id = f"OEM012-{engine_id.upper().replace('.', '-')}-YES"

        payload = {
            "market_id": market_id,
            "confidence": 0.83,
            "edge": 0.39,
            "score": 0.39,
        }

        if engine_id == "oracle.market_relationship":
            payload.update({"related_market_id": "OEM012-RELATED", "relationship_score": 0.39})
        elif engine_id == "oracle.market_influence":
            payload.update({"influence_source": "aggregator_gate", "influence_score": 0.39})
        elif engine_id == "oracle.market_sentiment":
            payload.update({"sentiment_source": "aggregator_gate", "sentiment_score": 0.39})
        elif engine_id == "oracle.discovery":
            payload.update({"discovery_source": "aggregator_gate", "discovery_type": "gate_probe", "discovery_score": 0.39})
        elif engine_id == "oracle.recall_ledger":
            payload.update({"ledger_key": "aggregator_pattern", "recall_score": 0.39, "sample_size": 18})
        elif engine_id == "oracle.query_audit":
            payload.update({"query_id": "aggregator_query", "audit_score": 0.39, "audit_status": "passed"})
        elif engine_id == "oracle.query_resolver":
            payload.update({"query": "aggregator gate query", "resolved_market_id": market_id, "resolver_score": 0.39})

        return payload


def run_gate(runtime_paths: Optional[Any] = None) -> MigratedAggregatorGateResult:
    return MigratedEngineAggregatorGate(runtime_paths=runtime_paths).run()


__all__ = [
    "GATE_ID",
    "GATE_NAME",
    "GATE_VERSION",
    "AggregatedEngineResult",
    "MigratedAggregatorGateResult",
    "MigratedEngineAggregatorGate",
    "run_gate",
]
'''

TEST_CODE = r'''from qseries_v2.integration.oem_012_migrated_engine_aggregator_gate import (
    GATE_ID,
    MigratedEngineAggregatorGate,
    run_gate,
)


def test_oem_012_gate_runs():
    result = run_gate()

    assert result.gate_id == GATE_ID
    assert result.status == "pass"
    assert result.engine_count == 7
    assert result.passed_count == 7
    assert result.failed_count == 0


def test_oem_012_predictions_are_aggregated():
    result = run_gate()

    assert result.total_signals >= 7
    assert result.total_predictions >= 7
    assert len(result.predictions) >= 7


def test_oem_012_all_engines_are_read_only():
    result = run_gate()

    for item in result.engine_results:
        assert item["status"] == "pass"
        assert item["read_only"] is True


def test_oem_012_gate_class_shape():
    gate = MigratedEngineAggregatorGate()
    result = gate.run()

    assert gate.read_only is True
    assert result.telemetry["read_only"] is True
    assert result.telemetry["aggregation_mode"] == "migrated_oem_engine_prediction_collection"


if __name__ == "__main__":
    test_oem_012_gate_runs()
    test_oem_012_predictions_are_aggregated()
    test_oem_012_all_engines_are_read_only()
    test_oem_012_gate_class_shape()

    result = run_gate()

    print("[PASS] OEM-012 Migrated Engine Aggregator Gate")
    print(
        {
            "gate_id": result.gate_id,
            "status": result.status,
            "engine_count": result.engine_count,
            "passed_count": result.passed_count,
            "failed_count": result.failed_count,
            "total_signals": result.total_signals,
            "total_predictions": result.total_predictions,
        }
    )
'''

def ensure_dirs():
    INTEGRATION.mkdir(parents=True, exist_ok=True)


def update_init():
    INIT_PATH.touch(exist_ok=True)
    text = INIT_PATH.read_text(encoding="utf-8")

    line = (
        "from .oem_012_migrated_engine_aggregator_gate import "
        "MigratedEngineAggregatorGate, run_gate as run_migrated_engine_aggregator_gate"
    )

    exports = [
        '"MigratedEngineAggregatorGate"',
        '"run_migrated_engine_aggregator_gate"',
    ]

    if line not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"

    if "__all__" not in text:
        text += "\n__all__ = []\n"

    for item in exports:
        if item not in text:
            text = text.replace("__all__ = [", f"__all__ = [\n    {item},")

    INIT_PATH.write_text(text, encoding="utf-8")


def main():
    print("=" * 40)
    print(" OEM-012 INSTALLER")
    print(" Migrated Engine Aggregator Gate")
    print("=" * 40)

    ensure_dirs()

    GATE_PATH.write_text(GATE_CODE, encoding="utf-8")
    print(f"[OK] Wrote {GATE_PATH}")

    TEST_PATH.write_text(TEST_CODE, encoding="utf-8")
    print(f"[OK] Wrote {TEST_PATH}")

    update_init()
    print(f"[OK] Updated {INIT_PATH}")

    print("\n[DONE] OEM-012 installed")
    print("\nRun:")
    print("py test_oem_012_migrated_engine_aggregator_gate.py")


if __name__ == "__main__":
    main()