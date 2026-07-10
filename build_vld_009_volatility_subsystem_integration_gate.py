from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_subsystem_integration_gate.py"
TEST = ROOT / "test_vld_009_volatility_subsystem_integration_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .volatility_discovery_contract import empty_volatility_discovery_result
from .volatility_discovery_engine import discover_volatility_opportunities
from .volatility_oos_runtime_gate import validate_volatility_oos_runtime
from .volatility_pipeline_bridge import run_volatility_pipeline
from .volatility_pipeline_gate import validate_volatility_discovery_result
from .volatility_registry_bridge import bridge_volatility_registry
from .volatility_replay_ledger import VolatilityReplayLedgerBuilder
from .volatility_source_adapter import build_volatility_source_snapshot


READ_ONLY = True
SCHEMA_VERSION = "VLD-009"
ENGINE_ID = "oracle.discovery.volatility.subsystem_integration_gate"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class VolatilitySubsystemIntegrationResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    contract_hash: str
    source_snapshot_hash: str
    discovery_result_hash: str
    gate_hash: str
    registry_hash: str
    pipeline_hash: str
    oos_hash: str
    replay_ledger_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    integration_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class VolatilitySubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "volatility.integration",
        observed_at: Optional[str] = None,
        runtime_context: Optional[Mapping[str, Any]] = None,
    ) -> VolatilitySubsystemIntegrationResult:
        raw_list = list(raw_records or [])
        context = dict(runtime_context or {"mode": "oos", "fold": "integration"})

        contract = empty_volatility_discovery_result()

        source_snapshot = build_volatility_source_snapshot(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
        )

        discovery = discover_volatility_opportunities(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
            expansion_ratio_threshold=1.50,
            contraction_ratio_threshold=0.70,
            iv_rv_gap_threshold=0.10,
            shock_return_threshold=0.05,
            min_volume=0.0,
        )

        gate = validate_volatility_discovery_result(discovery)
        registry = bridge_volatility_registry(gate)

        pipeline = run_volatility_pipeline(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
            expansion_ratio_threshold=1.50,
            contraction_ratio_threshold=0.70,
            iv_rv_gap_threshold=0.10,
            shock_return_threshold=0.05,
            min_volume=0.0,
        )

        oos = validate_volatility_oos_runtime(
            pipeline_result=pipeline,
            runtime_context=context,
        )

        ledger_builder = VolatilityReplayLedgerBuilder()
        ledger = ledger_builder.build([oos])
        ledger_validation = ledger_builder.validate(ledger)

        checks = {
            "read_only": all([
                contract.read_only,
                source_snapshot.read_only,
                discovery.read_only,
                gate.read_only,
                registry.read_only,
                pipeline.read_only,
                oos.read_only,
                ledger.read_only,
            ]),
            "contract_schema": contract.schema_version == "VLD-001",
            "source_schema": source_snapshot.schema_version == "VLD-002",
            "discovery_schema": discovery.schema_version == "VLD-003",
            "gate_schema": gate.schema_version == "VLD-004",
            "registry_schema": registry.schema_version == "VLD-005",
            "pipeline_schema": pipeline.schema_version == "VLD-006",
            "oos_schema": oos.schema_version == "VLD-007",
            "ledger_schema": ledger.schema_version == "VLD-008",
            "discovery_count_matches_pipeline": discovery.opportunity_count == pipeline.opportunity_count,
            "pipeline_count_matches_oos": pipeline.opportunity_count == oos.opportunity_count,
            "ledger_has_one_entry": ledger.entry_count == 1,
            "ledger_validation_accepted": ledger_validation["accepted"] is True,
            "gate_accepted": gate.accepted is True,
            "registry_accepted": registry.accepted is True,
            "pipeline_accepted": pipeline.accepted is True,
            "oos_accepted": oos.accepted is True,
            "hashes_present": all([
                contract.result_hash,
                source_snapshot.snapshot_hash,
                discovery.result_hash,
                gate.gate_hash,
                registry.registry_hash,
                pipeline.pipeline_hash,
                oos.oos_hash,
                ledger.ledger_hash,
            ]),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"
        failed = [name for name, passed in checks.items() if not passed]
        reason = "volatility subsystem integration checks passed" if accepted else "failed checks: " + ", ".join(failed)

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "subsystem": "volatility_discovery",
            "modules": [
                "VLD-001 contract",
                "VLD-002 source_adapter",
                "VLD-003 discovery_engine",
                "VLD-004 pipeline_gate",
                "VLD-005 registry_bridge",
                "VLD-006 pipeline_bridge",
                "VLD-007 oos_runtime_gate",
                "VLD-008 replay_ledger",
                "VLD-009 subsystem_integration_gate",
            ],
            "ledger_validation": ledger_validation,
        }

        unsigned = VolatilitySubsystemIntegrationResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            contract_hash=contract.result_hash,
            source_snapshot_hash=source_snapshot.snapshot_hash,
            discovery_result_hash=discovery.result_hash,
            gate_hash=gate.gate_hash,
            registry_hash=registry.registry_hash,
            pipeline_hash=pipeline.pipeline_hash,
            oos_hash=oos.oos_hash,
            replay_ledger_hash=ledger.ledger_hash,
            opportunity_count=discovery.opportunity_count,
            checks=checks,
            audit=audit,
            read_only=True,
            integration_hash="",
        )

        return VolatilitySubsystemIntegrationResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            contract_hash=unsigned.contract_hash,
            source_snapshot_hash=unsigned.source_snapshot_hash,
            discovery_result_hash=unsigned.discovery_result_hash,
            gate_hash=unsigned.gate_hash,
            registry_hash=unsigned.registry_hash,
            pipeline_hash=unsigned.pipeline_hash,
            oos_hash=unsigned.oos_hash,
            replay_ledger_hash=unsigned.replay_ledger_hash,
            opportunity_count=unsigned.opportunity_count,
            checks=unsigned.checks,
            audit=unsigned.audit,
            read_only=True,
            integration_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def run_volatility_subsystem_integration_gate(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "volatility.integration",
    observed_at: Optional[str] = None,
    runtime_context: Optional[Mapping[str, Any]] = None,
) -> VolatilitySubsystemIntegrationResult:
    return VolatilitySubsystemIntegrationGate().run(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilitySubsystemIntegrationGate",
    "VolatilitySubsystemIntegrationResult",
    "run_volatility_subsystem_integration_gate",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_subsystem_integration_gate import (
    VolatilitySubsystemIntegrationGate,
    run_volatility_subsystem_integration_gate,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.20,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
    {
        "market_id": "KXVOL-CONTRACT",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.10,
        "implied_volatility": 0.24,
        "baseline_volatility": 0.20,
        "price_change": 0.01,
        "volume": 9000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def test_volatility_subsystem_integration_gate_accepts_full_chain():
    gate = VolatilitySubsystemIntegrationGate()
    assert gate.assert_read_only() is True

    result = gate.run(
        RAW,
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    assert result.schema_version == "VLD-009"
    assert result.engine_id == "oracle.discovery.volatility.subsystem_integration_gate"
    assert result.status == "accepted", result.reason
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 4
    assert result.integration_hash
    assert all(result.checks.values()), result.checks
    assert result.audit["subsystem"] == "volatility_discovery"
    assert result.audit["ledger_validation"]["accepted"] is True


def test_volatility_subsystem_integration_gate_is_replayable_and_order_independent():
    r1 = run_volatility_subsystem_integration_gate(
        RAW,
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )
    r2 = run_volatility_subsystem_integration_gate(
        list(reversed(RAW)),
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"fold": "A", "mode": "replay"},
    )

    assert r1.integration_hash == r2.integration_hash
    assert r1.discovery_result_hash == r2.discovery_result_hash
    assert r1.pipeline_hash == r2.pipeline_hash
    assert r1.replay_ledger_hash == r2.replay_ledger_hash


def test_volatility_subsystem_integration_gate_accepts_empty_chain():
    result = run_volatility_subsystem_integration_gate(
        [],
        source_name="volatility.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "shadow", "fold": "empty"},
    )

    assert result.status == "accepted", result.reason
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(result.checks.values()), result.checks


def test_volatility_subsystem_integration_gate_rejects_execution_context():
    result = run_volatility_subsystem_integration_gate(
        RAW,
        source_name="volatility.integration.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.checks["oos_accepted"] is False
    assert result.read_only is True


if __name__ == "__main__":
    test_volatility_subsystem_integration_gate_accepts_full_chain()
    test_volatility_subsystem_integration_gate_is_replayable_and_order_independent()
    test_volatility_subsystem_integration_gate_accepts_empty_chain()
    test_volatility_subsystem_integration_gate_rejects_execution_context()

    result = run_volatility_subsystem_integration_gate(
        [],
        source_name="volatility.integration.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "integration"},
    )

    print("[PASS] VLD-009 Volatility Subsystem Integration Gate")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .volatility_subsystem_integration_gate import (
    VolatilitySubsystemIntegrationGate,
    VolatilitySubsystemIntegrationResult,
    run_volatility_subsystem_integration_gate,
)
'''
if "volatility_subsystem_integration_gate" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-009 INSTALLER")
print(" Volatility Subsystem Integration Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-009 installed")
print()
print("Run:")
print("py test_vld_009_volatility_subsystem_integration_gate.py")