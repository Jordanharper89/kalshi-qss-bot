from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_pipeline_bridge.py"
TEST = ROOT / "test_crd_006_correlation_pipeline_bridge.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, Mapping, Optional

from .correlation_discovery_engine import (
    CorrelationDiscoveryEngine,
    CorrelationDiscoveryResult,
)
from .correlation_pipeline_gate import (
    CorrelationPipelineGate,
    CorrelationPipelineGateResult,
)
from .correlation_registry_bridge import (
    CorrelationRegistryBridge,
    CorrelationRegistryEntry,
)


READ_ONLY = True
SCHEMA_VERSION = "CRD-006"
ENGINE_ID = "oracle.discovery.correlation.pipeline_bridge"


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
class CorrelationPipelineBridgeResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    source_name: str
    observed_at: str
    discovery: CorrelationDiscoveryResult
    gate: CorrelationPipelineGateResult
    registry_entry: CorrelationRegistryEntry
    opportunity_count: int
    read_only: bool = True
    pipeline_hash: str = ""
    audit: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class CorrelationPipelineBridge:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "correlation.generic",
        strong_correlation_threshold: float = 0.70,
        correlation_break_threshold: float = 0.30,
        return_divergence_threshold: float = 0.04,
        min_sample_size: int = 20,
    ) -> None:
        self.source_name = str(
            source_name or "correlation.generic"
        )

        self.discovery_engine = CorrelationDiscoveryEngine(
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
        )

        self.pipeline_gate = CorrelationPipelineGate()
        self.registry_bridge = CorrelationRegistryBridge()

    def run(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> CorrelationPipelineBridgeResult:
        raw_list = list(raw_records or [])

        discovery = self.discovery_engine.discover_from_raw(
            raw_records=raw_list,
            source_name=self.source_name,
            observed_at=observed_at,
        )

        gate = self.pipeline_gate.validate(discovery)
        registry_entry = self.registry_bridge.bridge(gate)

        accepted = (
            gate.accepted
            and registry_entry.accepted
        )

        status = (
            "accepted"
            if accepted
            else "rejected"
        )

        audit = {
            "read_only": True,
            "deterministic": True,
            "replayable": True,
            "immutable": True,
            "execution_capable": False,
            "external_mutation_allowed": False,
            "pipeline_steps": [
                "source_adapter",
                "discovery_engine",
                "pipeline_gate",
                "registry_bridge",
            ],
            "source_name": self.source_name,
            "source_record_count": len(raw_list),
            "discovery_result_hash": (
                discovery.result_hash
            ),
            "gate_hash": gate.gate_hash,
            "registry_hash": (
                registry_entry.registry_hash
            ),
        }

        unsigned = CorrelationPipelineBridgeResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            source_name=self.source_name,
            observed_at=discovery.observed_at,
            discovery=discovery,
            gate=gate,
            registry_entry=registry_entry,
            opportunity_count=(
                discovery.opportunity_count
            ),
            read_only=True,
            pipeline_hash="",
            audit=audit,
        )

        return CorrelationPipelineBridgeResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            discovery=unsigned.discovery,
            gate=unsigned.gate,
            registry_entry=unsigned.registry_entry,
            opportunity_count=(
                unsigned.opportunity_count
            ),
            read_only=True,
            pipeline_hash=_stable_hash(
                unsigned.canonical()
            ),
            audit=unsigned.audit,
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "source_normalization",
                "correlation_discovery",
                "pipeline_validation",
                "registry_bridging",
                "deterministic_pipeline_hashing",
                "order_independent_processing",
                "empty_pipeline_processing",
            ],
            "thresholds": {
                "strong_correlation_threshold": (
                    self.discovery_engine
                    .strong_correlation_threshold
                ),
                "correlation_break_threshold": (
                    self.discovery_engine
                    .correlation_break_threshold
                ),
                "return_divergence_threshold": (
                    self.discovery_engine
                    .return_divergence_threshold
                ),
                "min_sample_size": (
                    self.discovery_engine
                    .min_sample_size
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
                f"mutation-like methods are forbidden: "
                f"{offenders}"
            )

        self.discovery_engine.assert_read_only()
        self.pipeline_gate.assert_read_only()
        self.registry_bridge.assert_read_only()

        return True


def run_correlation_pipeline(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.generic",
    observed_at: Optional[str] = None,
    strong_correlation_threshold: float = 0.70,
    correlation_break_threshold: float = 0.30,
    return_divergence_threshold: float = 0.04,
    min_sample_size: int = 20,
) -> CorrelationPipelineBridgeResult:
    bridge = CorrelationPipelineBridge(
        source_name=source_name,
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
    )

    return bridge.run(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationPipelineBridge",
    "CorrelationPipelineBridgeResult",
    "run_correlation_pipeline",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_pipeline_bridge import (
    CorrelationPipelineBridge,
    run_correlation_pipeline,
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


def test_correlation_pipeline_bridge_runs_full_pipeline():
    bridge = CorrelationPipelineBridge(
        source_name="correlation.test",
    )

    assert bridge.assert_read_only() is True

    result = bridge.run(
        RAW,
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.schema_version == "CRD-006"
    assert (
        result.engine_id
        == "oracle.discovery.correlation.pipeline_bridge"
    )
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 5

    assert (
        result.discovery.schema_version
        == "CRD-003"
    )
    assert result.gate.schema_version == "CRD-004"
    assert (
        result.registry_entry.schema_version
        == "CRD-005"
    )

    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.pipeline_hash

    assert result.audit["read_only"] is True
    assert result.audit["deterministic"] is True
    assert result.audit["replayable"] is True
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

    assert result.audit["pipeline_steps"] == [
        "source_adapter",
        "discovery_engine",
        "pipeline_gate",
        "registry_bridge",
    ]


def test_correlation_pipeline_bridge_is_replayable():
    result1 = run_correlation_pipeline(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    result2 = run_correlation_pipeline(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert (
        result1.pipeline_hash
        == result2.pipeline_hash
    )
    assert (
        result1.discovery.result_hash
        == result2.discovery.result_hash
    )
    assert (
        result1.gate.gate_hash
        == result2.gate.gate_hash
    )
    assert (
        result1.registry_entry.registry_hash
        == result2.registry_entry.registry_hash
    )


def test_correlation_pipeline_bridge_is_order_independent():
    result1 = run_correlation_pipeline(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    result2 = run_correlation_pipeline(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert (
        result1.pipeline_hash
        == result2.pipeline_hash
    )
    assert (
        result1.discovery.result_hash
        == result2.discovery.result_hash
    )
    assert (
        result1.gate.gate_hash
        == result2.gate.gate_hash
    )
    assert (
        result1.registry_entry.registry_hash
        == result2.registry_entry.registry_hash
    )


def test_correlation_pipeline_bridge_accepts_empty_pipeline():
    result = run_correlation_pipeline(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.discovery.status == "empty"
    assert result.gate.accepted is True
    assert result.registry_entry.accepted is True
    assert result.read_only is True
    assert result.pipeline_hash


def test_correlation_pipeline_bridge_respects_sample_threshold():
    result = run_correlation_pipeline(
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
        source_name="correlation.small_sample",
        observed_at="2026-07-09T00:00:00+00:00",
        min_sample_size=20,
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.discovery.status == "empty"
    assert result.read_only is True


if __name__ == "__main__":
    test_correlation_pipeline_bridge_runs_full_pipeline()
    test_correlation_pipeline_bridge_is_replayable()
    test_correlation_pipeline_bridge_is_order_independent()
    test_correlation_pipeline_bridge_accepts_empty_pipeline()
    test_correlation_pipeline_bridge_respects_sample_threshold()

    result = run_correlation_pipeline(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    print(
        "[PASS] CRD-006 "
        "Correlation Pipeline Bridge"
    )
    print(
        {
            "schema_version": result.schema_version,
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
from .correlation_pipeline_bridge import (
    CorrelationPipelineBridge,
    CorrelationPipelineBridgeResult,
    run_correlation_pipeline,
)
'''

if "correlation_pipeline_bridge" not in existing:
    INIT.write_text(
        existing.rstrip() + "\n" + exports.lstrip(),
        encoding="utf-8",
    )

print("========================================")
print(" CRD-006 INSTALLER")
print(" Correlation Pipeline Bridge")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] CRD-006 installed")
print()
print("Run:")
print("py test_crd_006_correlation_pipeline_bridge.py")