from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_subsystem_integration_gate.py"
TEST = ROOT / "test_crd_009_correlation_subsystem_integration_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .correlation_discovery_contract import (
    empty_correlation_discovery_result,
)
from .correlation_discovery_engine import (
    discover_correlation_opportunities,
)
from .correlation_oos_runtime_gate import (
    validate_correlation_oos_runtime,
)
from .correlation_pipeline_bridge import (
    run_correlation_pipeline,
)
from .correlation_pipeline_gate import (
    validate_correlation_discovery_result,
)
from .correlation_registry_bridge import (
    bridge_correlation_registry,
)
from .correlation_replay_ledger import (
    CorrelationReplayLedgerBuilder,
)
from .correlation_source_adapter import (
    build_correlation_source_snapshot,
)


READ_ONLY = True
SCHEMA_VERSION = "CRD-009"
ENGINE_ID = (
    "oracle.discovery.correlation."
    "subsystem_integration_gate"
)


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }

    if isinstance(value, list):
        return [
            _deep_sort(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            _deep_sort(item)
            for item in value
        )

    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(
        _deep_sort(payload)
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CorrelationSubsystemIntegrationResult:
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
    checks: Dict[str, bool] = field(
        default_factory=dict
    )
    audit: Dict[str, Any] = field(
        default_factory=dict
    )
    read_only: bool = True
    integration_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class CorrelationSubsystemIntegrationGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        strong_correlation_threshold: float = 0.70,
        correlation_break_threshold: float = 0.30,
        return_divergence_threshold: float = 0.04,
        min_sample_size: int = 20,
        max_opportunities: int = 10000,
    ) -> None:
        if int(min_sample_size) < 0:
            raise ValueError(
                "min_sample_size must be non-negative"
            )

        if int(max_opportunities) < 0:
            raise ValueError(
                "max_opportunities must be non-negative"
            )

        self.strong_correlation_threshold = float(
            strong_correlation_threshold
        )
        self.correlation_break_threshold = float(
            correlation_break_threshold
        )
        self.return_divergence_threshold = float(
            return_divergence_threshold
        )
        self.min_sample_size = int(
            min_sample_size
        )
        self.max_opportunities = int(
            max_opportunities
        )

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        source_name: str = "correlation.integration",
        observed_at: Optional[str] = None,
        runtime_context: Optional[
            Mapping[str, Any]
        ] = None,
    ) -> CorrelationSubsystemIntegrationResult:
        raw_list = list(raw_records or [])

        if (
            runtime_context is not None
            and not isinstance(
                runtime_context,
                Mapping,
            )
        ):
            raise TypeError(
                "runtime_context must be a mapping or None"
            )

        context = dict(
            runtime_context
            or {
                "mode": "oos",
                "fold": "integration",
            }
        )

        contract = (
            empty_correlation_discovery_result()
        )

        source_snapshot = (
            build_correlation_source_snapshot(
                raw_records=raw_list,
                source_name=source_name,
                observed_at=observed_at,
            )
        )

        discovery = (
            discover_correlation_opportunities(
                raw_records=raw_list,
                source_name=source_name,
                observed_at=observed_at,
                strong_correlation_threshold=(
                    self
                    .strong_correlation_threshold
                ),
                correlation_break_threshold=(
                    self
                    .correlation_break_threshold
                ),
                return_divergence_threshold=(
                    self
                    .return_divergence_threshold
                ),
                min_sample_size=(
                    self.min_sample_size
                ),
            )
        )

        gate = (
            validate_correlation_discovery_result(
                discovery
            )
        )

        registry = (
            bridge_correlation_registry(gate)
        )

        pipeline = run_correlation_pipeline(
            raw_records=raw_list,
            source_name=source_name,
            observed_at=observed_at,
            strong_correlation_threshold=(
                self.strong_correlation_threshold
            ),
            correlation_break_threshold=(
                self.correlation_break_threshold
            ),
            return_divergence_threshold=(
                self.return_divergence_threshold
            ),
            min_sample_size=self.min_sample_size,
        )

        oos = validate_correlation_oos_runtime(
            pipeline_result=pipeline,
            runtime_context=context,
            require_accepted_pipeline=True,
            max_opportunities=(
                self.max_opportunities
            ),
        )

        ledger_builder = (
            CorrelationReplayLedgerBuilder()
        )

        ledger = ledger_builder.build([oos])
        ledger_validation = (
            ledger_builder.validate(ledger)
        )

        checks = {
            "read_only": all(
                [
                    contract.read_only,
                    source_snapshot.read_only,
                    discovery.read_only,
                    gate.read_only,
                    registry.read_only,
                    pipeline.read_only,
                    oos.read_only,
                    ledger.read_only,
                ]
            ),
            "contract_schema": (
                contract.schema_version
                == "CRD-001"
            ),
            "source_schema": (
                source_snapshot.schema_version
                == "CRD-002"
            ),
            "discovery_schema": (
                discovery.schema_version
                == "CRD-003"
            ),
            "gate_schema": (
                gate.schema_version
                == "CRD-004"
            ),
            "registry_schema": (
                registry.schema_version
                == "CRD-005"
            ),
            "pipeline_schema": (
                pipeline.schema_version
                == "CRD-006"
            ),
            "oos_schema": (
                oos.schema_version
                == "CRD-007"
            ),
            "ledger_schema": (
                ledger.schema_version
                == "CRD-008"
            ),
            "source_count_matches_input": (
                source_snapshot.record_count
                == len(raw_list)
            ),
            "discovery_count_matches_pipeline": (
                discovery.opportunity_count
                == pipeline.opportunity_count
            ),
            "pipeline_count_matches_oos": (
                pipeline.opportunity_count
                == oos.opportunity_count
            ),
            "gate_hash_matches_pipeline": (
                gate.gate_hash
                == pipeline.gate.gate_hash
            ),
            "registry_hash_matches_pipeline": (
                registry.registry_hash
                == (
                    pipeline.registry_entry
                    .registry_hash
                )
            ),
            "discovery_hash_matches_pipeline": (
                discovery.result_hash
                == (
                    pipeline.discovery
                    .result_hash
                )
            ),
            "ledger_has_one_entry": (
                ledger.entry_count == 1
            ),
            "ledger_oos_hash_matches": (
                ledger.entries[0].oos_hash
                == oos.oos_hash
            ),
            "ledger_pipeline_hash_matches": (
                ledger.entries[0].pipeline_hash
                == pipeline.pipeline_hash
            ),
            "ledger_validation_accepted": (
                ledger_validation["accepted"]
                is True
            ),
            "gate_accepted": (
                gate.accepted is True
            ),
            "registry_accepted": (
                registry.accepted is True
            ),
            "pipeline_accepted": (
                pipeline.accepted is True
            ),
            "oos_accepted": (
                oos.accepted is True
            ),
            "execution_disabled": (
                pipeline.audit.get(
                    "execution_capable"
                )
                is False
            ),
            "external_mutation_disabled": (
                pipeline.audit.get(
                    "external_mutation_allowed"
                )
                is False
            ),
            "hashes_present": all(
                [
                    contract.result_hash,
                    source_snapshot.snapshot_hash,
                    discovery.result_hash,
                    gate.gate_hash,
                    registry.registry_hash,
                    pipeline.pipeline_hash,
                    oos.oos_hash,
                    ledger.ledger_hash,
                ]
            ),
        }

        accepted = all(checks.values())

        status = (
            "accepted"
            if accepted
            else "rejected"
        )

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        reason = (
            "correlation subsystem integration "
            "checks passed"
            if accepted
            else "failed checks: "
            + ", ".join(failed_checks)
        )

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "auditable": True,
            "execution_capable": False,
            "external_mutation_allowed": False,
            "subsystem": (
                "correlation_discovery"
            ),
            "source_name": source_name,
            "source_record_count": len(raw_list),
            "runtime_context": _deep_sort(
                context
            ),
            "thresholds": {
                "strong_correlation_threshold": (
                    self
                    .strong_correlation_threshold
                ),
                "correlation_break_threshold": (
                    self
                    .correlation_break_threshold
                ),
                "return_divergence_threshold": (
                    self
                    .return_divergence_threshold
                ),
                "min_sample_size": (
                    self.min_sample_size
                ),
                "max_opportunities": (
                    self.max_opportunities
                ),
            },
            "modules": [
                "CRD-001 contract",
                "CRD-002 source_adapter",
                "CRD-003 discovery_engine",
                "CRD-004 pipeline_gate",
                "CRD-005 registry_bridge",
                "CRD-006 pipeline_bridge",
                "CRD-007 oos_runtime_gate",
                "CRD-008 replay_ledger",
                (
                    "CRD-009 "
                    "subsystem_integration_gate"
                ),
            ],
            "ledger_validation": (
                ledger_validation
            ),
        }

        unsigned = (
            CorrelationSubsystemIntegrationResult(
                schema_version=(
                    self.schema_version
                ),
                engine_id=self.engine_id,
                status=status,
                accepted=accepted,
                reason=reason,
                contract_hash=(
                    contract.result_hash
                ),
                source_snapshot_hash=(
                    source_snapshot
                    .snapshot_hash
                ),
                discovery_result_hash=(
                    discovery.result_hash
                ),
                gate_hash=gate.gate_hash,
                registry_hash=(
                    registry.registry_hash
                ),
                pipeline_hash=(
                    pipeline.pipeline_hash
                ),
                oos_hash=oos.oos_hash,
                replay_ledger_hash=(
                    ledger.ledger_hash
                ),
                opportunity_count=(
                    discovery
                    .opportunity_count
                ),
                checks=checks,
                audit=audit,
                read_only=True,
                integration_hash="",
            )
        )

        return CorrelationSubsystemIntegrationResult(
            schema_version=(
                unsigned.schema_version
            ),
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            contract_hash=(
                unsigned.contract_hash
            ),
            source_snapshot_hash=(
                unsigned.source_snapshot_hash
            ),
            discovery_result_hash=(
                unsigned.discovery_result_hash
            ),
            gate_hash=unsigned.gate_hash,
            registry_hash=(
                unsigned.registry_hash
            ),
            pipeline_hash=(
                unsigned.pipeline_hash
            ),
            oos_hash=unsigned.oos_hash,
            replay_ledger_hash=(
                unsigned.replay_ledger_hash
            ),
            opportunity_count=(
                unsigned.opportunity_count
            ),
            checks=unsigned.checks,
            audit=unsigned.audit,
            read_only=True,
            integration_hash=_stable_hash(
                unsigned.canonical()
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": (
                self.schema_version
            ),
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "full_subsystem_validation",
                "contract_validation",
                "source_adapter_validation",
                "discovery_validation",
                "pipeline_gate_validation",
                "registry_bridge_validation",
                "pipeline_bridge_validation",
                "oos_runtime_validation",
                "replay_ledger_validation",
                "deterministic_integration_hashing",
                "execution_context_rejection",
            ],
            "thresholds": {
                "strong_correlation_threshold": (
                    self
                    .strong_correlation_threshold
                ),
                "correlation_break_threshold": (
                    self
                    .correlation_break_threshold
                ),
                "return_divergence_threshold": (
                    self
                    .return_divergence_threshold
                ),
                "min_sample_size": (
                    self.min_sample_size
                ),
                "max_opportunities": (
                    self.max_opportunities
                ),
            },
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                "mutation-like methods are "
                f"forbidden: {offenders}"
            )

        return True


def run_correlation_subsystem_integration_gate(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.integration",
    observed_at: Optional[str] = None,
    runtime_context: Optional[
        Mapping[str, Any]
    ] = None,
    strong_correlation_threshold: float = 0.70,
    correlation_break_threshold: float = 0.30,
    return_divergence_threshold: float = 0.04,
    min_sample_size: int = 20,
    max_opportunities: int = 10000,
) -> CorrelationSubsystemIntegrationResult:
    integration_gate = (
        CorrelationSubsystemIntegrationGate(
            strong_correlation_threshold=(
                strong_correlation_threshold
            ),
            correlation_break_threshold=(
                correlation_break_threshold
            ),
            return_divergence_threshold=(
                return_divergence_threshold
            ),
            min_sample_size=min_sample_size,
            max_opportunities=max_opportunities,
        )
    )

    return integration_gate.run(
        raw_records=raw_records,
        source_name=source_name,
        observed_at=observed_at,
        runtime_context=runtime_context,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationSubsystemIntegrationGate",
    "CorrelationSubsystemIntegrationResult",
    (
        "run_correlation_"
        "subsystem_integration_gate"
    ),
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_subsystem_integration_gate import (
    CorrelationSubsystemIntegrationGate,
    run_correlation_subsystem_integration_gate,
)


RAW = [
    {
        "primary_market_id": "KXTEST-A",
        "related_market_id": "KXTEST-B",
        "venue": "kalshi",
        "correlation": 0.82,
        "baseline_correlation": 0.80,
        "recent_correlation": 0.20,
        "lag": 0,
        "window": "30d",
        "sample_size": 120,
        "primary_return": 0.06,
        "related_return": -0.01,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
    {
        "primary_market_id": "KXTEST-C",
        "related_market_id": "KXTEST-D",
        "venue": "kalshi",
        "correlation": -0.76,
        "baseline_correlation": -0.72,
        "recent_correlation": 0.31,
        "lag": 2,
        "window": "30d",
        "sample_size": 150,
        "primary_return": -0.03,
        "related_return": 0.04,
        "observed_at": (
            "2026-07-09T00:00:00+00:00"
        ),
    },
]


def test_correlation_subsystem_integration_gate_accepts_full_chain():
    gate = CorrelationSubsystemIntegrationGate()

    assert gate.assert_read_only() is True

    result = gate.run(
        RAW,
        source_name=(
            "correlation.integration.test"
        ),
        observed_at=(
            "2026-07-09T00:00:00+00:00"
        ),
        runtime_context={
            "mode": "oos",
            "fold": "integration",
        },
    )

    assert result.schema_version == "CRD-009"
    assert result.engine_id == (
        "oracle.discovery.correlation."
        "subsystem_integration_gate"
    )
    assert result.status == "accepted", (
        result.reason
    )
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 5
    assert result.integration_hash
    assert all(
        result.checks.values()
    ), result.checks

    assert (
        result.audit["subsystem"]
        == "correlation_discovery"
    )
    assert (
        result.audit["execution_capable"]
        is False
    )
    assert (
        result.audit[
            "external_mutation_allowed"
        ]
        is False
    )
    assert (
        result.audit[
            "ledger_validation"
        ]["accepted"]
        is True
    )


def test_correlation_subsystem_integration_gate_is_replayable_and_order_independent():
    result1 = (
        run_correlation_subsystem_integration_gate(
            RAW,
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "replay",
                "fold": "A",
            },
        )
    )

    result2 = (
        run_correlation_subsystem_integration_gate(
            list(reversed(RAW)),
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "fold": "A",
                "mode": "replay",
            },
        )
    )

    assert (
        result1.integration_hash
        == result2.integration_hash
    )
    assert (
        result1.discovery_result_hash
        == result2.discovery_result_hash
    )
    assert (
        result1.gate_hash
        == result2.gate_hash
    )
    assert (
        result1.registry_hash
        == result2.registry_hash
    )
    assert (
        result1.pipeline_hash
        == result2.pipeline_hash
    )
    assert (
        result1.oos_hash
        == result2.oos_hash
    )
    assert (
        result1.replay_ledger_hash
        == result2.replay_ledger_hash
    )


def test_correlation_subsystem_integration_gate_accepts_empty_chain():
    result = (
        run_correlation_subsystem_integration_gate(
            [],
            source_name=(
                "correlation.integration.empty"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "shadow",
                "fold": "empty",
            },
        )
    )

    assert result.status == "accepted", (
        result.reason
    )
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(
        result.checks.values()
    ), result.checks
    assert result.integration_hash


def test_correlation_subsystem_integration_gate_rejects_execution_context():
    result = (
        run_correlation_subsystem_integration_gate(
            RAW,
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "oos",
                "execute": True,
            },
        )
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["oos_accepted"]
        is False
    )
    assert result.read_only is True
    assert result.integration_hash


def test_correlation_subsystem_integration_gate_respects_sample_size():
    result = (
        run_correlation_subsystem_integration_gate(
            [
                {
                    "primary_market_id": "A",
                    "related_market_id": "B",
                    "venue": "demo",
                    "correlation": 0.90,
                    "baseline_correlation": 0.90,
                    "recent_correlation": -0.20,
                    "lag": 1,
                    "window": "7d",
                    "sample_size": 5,
                    "primary_return": 0.10,
                    "related_return": -0.10,
                    "observed_at": (
                        "2026-07-09T00:00:00+00:00"
                    ),
                }
            ],
            source_name=(
                "correlation.integration."
                "small_sample"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "oos",
            },
            min_sample_size=20,
        )
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(result.checks.values())


def test_correlation_subsystem_integration_gate_rejects_invalid_context_type():
    gate = CorrelationSubsystemIntegrationGate()

    try:
        gate.run(
            RAW,
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context=["oos"],
        )
    except TypeError as exc:
        assert str(exc) == (
            "runtime_context must be a "
            "mapping or None"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid "
            "runtime context"
        )


if __name__ == "__main__":
    test_correlation_subsystem_integration_gate_accepts_full_chain()
    test_correlation_subsystem_integration_gate_is_replayable_and_order_independent()
    test_correlation_subsystem_integration_gate_accepts_empty_chain()
    test_correlation_subsystem_integration_gate_rejects_execution_context()
    test_correlation_subsystem_integration_gate_respects_sample_size()
    test_correlation_subsystem_integration_gate_rejects_invalid_context_type()

    result = (
        run_correlation_subsystem_integration_gate(
            [],
            source_name=(
                "correlation.integration.empty"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "oos",
                "fold": "integration",
            },
        )
    )

    print(
        "[PASS] CRD-009 "
        "Correlation Subsystem Integration Gate"
    )
    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": (
                result.opportunity_count
            ),
            "read_only": result.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(
    encoding="utf-8"
) if INIT.exists() else ""

exports = '''
from .correlation_subsystem_integration_gate import (
    CorrelationSubsystemIntegrationGate,
    CorrelationSubsystemIntegrationResult,
    run_correlation_subsystem_integration_gate,
)
'''

if (
    "correlation_subsystem_integration_gate"
    not in existing
):
    INIT.write_text(
        existing.rstrip()
        + "\n"
        + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" CRD-009 INSTALLER")
print(" Correlation Subsystem Integration Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] CRD-009 installed")
print()
print("Run:")
print(
    "py "
    "test_crd_009_correlation_"
    "subsystem_integration_gate.py"
)