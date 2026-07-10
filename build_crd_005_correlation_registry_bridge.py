from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_registry_bridge.py"
TEST = ROOT / "test_crd_005_correlation_registry_bridge.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping

from .correlation_pipeline_gate import CorrelationPipelineGateResult


READ_ONLY = True
SCHEMA_VERSION = "CRD-005"
ENGINE_ID = "oracle.discovery.correlation.registry_bridge"


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }
    if isinstance(value, list):
        return [_deep_sort(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(item) for item in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(_deep_sort(payload)).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CorrelationRegistryEntry:
    schema_version: str
    engine_id: str
    family: str
    bridge_status: str
    accepted: bool
    registry_key: str
    source_gate_hash: str
    source_result_hash: str
    opportunity_count: int
    capabilities: Dict[str, Any] = field(default_factory=dict)
    read_only: bool = True
    registry_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class CorrelationRegistryBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        family: str = "correlation_discovery",
    ) -> None:
        self.family = str(
            family or "correlation_discovery"
        )

    def bridge(
        self,
        gate_result: CorrelationPipelineGateResult,
    ) -> CorrelationRegistryEntry:
        if not isinstance(
            gate_result,
            CorrelationPipelineGateResult,
        ):
            raise TypeError(
                "gate_result must be a "
                "CorrelationPipelineGateResult"
            )

        registry_key = _stable_hash(
            {
                "family": self.family,
                "source_gate_hash": gate_result.gate_hash,
                "source_result_hash": (
                    gate_result.discovery_result_hash
                ),
                "source_schema_version": (
                    gate_result.schema_version
                ),
                "source_engine_id": gate_result.engine_id,
            }
        )

        capabilities = {
            "family": self.family,
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "auditable": True,
            "execution_capable": False,
            "external_mutation_allowed": False,
            "source_schema_version": (
                gate_result.schema_version
            ),
            "source_engine_id": gate_result.engine_id,
            "source_status": gate_result.status,
            "source_accepted": gate_result.accepted,
            "checks": dict(gate_result.checks),
            "supported_signals": [
                "correlation_break",
                "correlation_sign_flip",
                "return_divergence",
                "lead_lag_relationship",
                "correlation_decay",
            ],
        }

        bridge_status = (
            "registered"
            if gate_result.accepted
            else "rejected"
        )

        unsigned = CorrelationRegistryEntry(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            family=self.family,
            bridge_status=bridge_status,
            accepted=gate_result.accepted,
            registry_key=registry_key,
            source_gate_hash=gate_result.gate_hash,
            source_result_hash=(
                gate_result.discovery_result_hash
            ),
            opportunity_count=(
                gate_result.opportunity_count
            ),
            capabilities=capabilities,
            read_only=True,
            registry_hash="",
        )

        return CorrelationRegistryEntry(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            family=unsigned.family,
            bridge_status=unsigned.bridge_status,
            accepted=unsigned.accepted,
            registry_key=unsigned.registry_key,
            source_gate_hash=unsigned.source_gate_hash,
            source_result_hash=unsigned.source_result_hash,
            opportunity_count=unsigned.opportunity_count,
            capabilities=unsigned.capabilities,
            read_only=True,
            registry_hash=_stable_hash(
                unsigned.canonical()
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "family": self.family,
            "read_only": True,
            "supports": [
                "accepted_gate_registration",
                "rejected_gate_registration",
                "deterministic_registry_keys",
                "deterministic_registry_hashes",
                "capability_manifest_generation",
            ],
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
                f"mutation-like methods are forbidden: "
                f"{offenders}"
            )

        return True


def bridge_correlation_registry(
    gate_result: CorrelationPipelineGateResult,
) -> CorrelationRegistryEntry:
    return CorrelationRegistryBridge().bridge(
        gate_result
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationRegistryBridge",
    "CorrelationRegistryEntry",
    "bridge_correlation_registry",
]
''', encoding="utf-8")

TEST.write_text(r'''
from dataclasses import replace

from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_engine import (
    discover_correlation_opportunities,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_pipeline_gate import (
    validate_correlation_discovery_result,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_registry_bridge import (
    CorrelationRegistryBridge,
    bridge_correlation_registry,
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


def _build_gate():
    discovery = discover_correlation_opportunities(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    return validate_correlation_discovery_result(
        discovery
    )


def test_correlation_registry_bridge_registers_valid_gate():
    gate = _build_gate()
    bridge = CorrelationRegistryBridge()

    assert bridge.assert_read_only() is True

    entry = bridge.bridge(gate)

    assert entry.schema_version == "CRD-005"
    assert (
        entry.engine_id
        == "oracle.discovery.correlation.registry_bridge"
    )
    assert entry.family == "correlation_discovery"
    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.read_only is True
    assert entry.source_gate_hash == gate.gate_hash
    assert (
        entry.source_result_hash
        == gate.discovery_result_hash
    )
    assert (
        entry.opportunity_count
        == gate.opportunity_count
    )
    assert entry.registry_key
    assert entry.registry_hash

    assert (
        entry.capabilities["deterministic"]
        is True
    )
    assert (
        entry.capabilities["replayable"]
        is True
    )
    assert (
        entry.capabilities["immutable"]
        is True
    )
    assert (
        entry.capabilities["read_only"]
        is True
    )
    assert (
        entry.capabilities["execution_capable"]
        is False
    )
    assert (
        entry.capabilities[
            "external_mutation_allowed"
        ]
        is False
    )


def test_correlation_registry_bridge_is_replayable():
    gate = _build_gate()

    entry1 = bridge_correlation_registry(gate)
    entry2 = bridge_correlation_registry(gate)

    assert (
        entry1.registry_key
        == entry2.registry_key
    )
    assert (
        entry1.registry_hash
        == entry2.registry_hash
    )
    assert (
        entry1.capabilities
        == entry2.capabilities
    )


def test_correlation_registry_bridge_accepts_empty_valid_gate():
    discovery = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_correlation_discovery_result(
        discovery
    )
    entry = bridge_correlation_registry(gate)

    assert entry.bridge_status == "registered"
    assert entry.accepted is True
    assert entry.opportunity_count == 0
    assert entry.read_only is True
    assert entry.registry_key
    assert entry.registry_hash


def test_correlation_registry_bridge_records_rejected_gate():
    gate = _build_gate()

    rejected_gate = replace(
        gate,
        status="rejected",
        accepted=False,
        reason="test rejection",
    )

    entry = bridge_correlation_registry(
        rejected_gate
    )

    assert entry.bridge_status == "rejected"
    assert entry.accepted is False
    assert entry.read_only is True
    assert entry.registry_key
    assert entry.registry_hash
    assert (
        entry.capabilities["source_accepted"]
        is False
    )


def test_correlation_registry_bridge_rejects_wrong_type():
    bridge = CorrelationRegistryBridge()

    try:
        bridge.bridge({"accepted": True})
    except TypeError as exc:
        assert str(exc) == (
            "gate_result must be a "
            "CorrelationPipelineGateResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid gate type"
        )


if __name__ == "__main__":
    test_correlation_registry_bridge_registers_valid_gate()
    test_correlation_registry_bridge_is_replayable()
    test_correlation_registry_bridge_accepts_empty_valid_gate()
    test_correlation_registry_bridge_records_rejected_gate()
    test_correlation_registry_bridge_rejects_wrong_type()

    discovery = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gate = validate_correlation_discovery_result(
        discovery
    )
    entry = bridge_correlation_registry(gate)

    print(
        "[PASS] CRD-005 "
        "Correlation Registry Bridge"
    )
    print(
        {
            "schema_version": entry.schema_version,
            "engine_id": entry.engine_id,
            "bridge_status": entry.bridge_status,
            "accepted": entry.accepted,
            "opportunities": (
                entry.opportunity_count
            ),
            "read_only": entry.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(
    encoding="utf-8"
) if INIT.exists() else ""

exports = '''
from .correlation_registry_bridge import (
    CorrelationRegistryBridge,
    CorrelationRegistryEntry,
    bridge_correlation_registry,
)
'''

if "correlation_registry_bridge" not in existing:
    INIT.write_text(
        existing.rstrip() + "\n" + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" CRD-005 INSTALLER")
print(" Correlation Registry Bridge")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] CRD-005 installed")
print()
print("Run:")
print("py test_crd_005_correlation_registry_bridge.py")