from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "correlation_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "correlation_discovery_contract.py"
TEST = ROOT / "test_crd_001_correlation_discovery_contract.py"
INIT = PKG / "__init__.py"
OI_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Tuple


READ_ONLY = True
SCHEMA_VERSION = "CRD-001"
ENGINE_ID = "oracle.discovery.correlation.contract"


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
class CorrelationDiscoveryOpportunity:
    opportunity_id: str
    primary_market_id: str
    related_market_id: str
    venue: str
    signal_type: str
    relationship: str
    confidence: float
    magnitude: float
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def opportunity_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class CorrelationDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    opportunities: Tuple[CorrelationDiscoveryOpportunity, ...] = tuple()
    read_only: bool = True
    result_hash: str = ""

    @property
    def opportunity_count(self) -> int:
        return len(self.opportunities)

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunity_count"] = self.opportunity_count
        data["opportunities"] = [o.canonical() for o in self.opportunities]
        return _deep_sort(data)


def empty_correlation_discovery_result(
    engine_id: str = "oracle.discovery.correlation.empty",
) -> CorrelationDiscoveryResult:
    unsigned = CorrelationDiscoveryResult(
        schema_version=SCHEMA_VERSION,
        engine_id=engine_id,
        status="empty",
        opportunities=tuple(),
        read_only=True,
        result_hash="",
    )

    return CorrelationDiscoveryResult(
        schema_version=unsigned.schema_version,
        engine_id=unsigned.engine_id,
        status=unsigned.status,
        opportunities=unsigned.opportunities,
        read_only=True,
        result_hash=_stable_hash(unsigned.canonical()),
    )


def assert_correlation_contract_read_only(result: CorrelationDiscoveryResult) -> bool:
    if not isinstance(result, CorrelationDiscoveryResult):
        raise TypeError("result must be a CorrelationDiscoveryResult")
    if result.read_only is not True:
        raise AssertionError("correlation discovery result must be read-only")
    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationDiscoveryOpportunity",
    "CorrelationDiscoveryResult",
    "empty_correlation_discovery_result",
    "assert_correlation_contract_read_only",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_contract import (
    CorrelationDiscoveryOpportunity,
    CorrelationDiscoveryResult,
    assert_correlation_contract_read_only,
    empty_correlation_discovery_result,
)


def test_correlation_discovery_contract_empty_result():
    result = empty_correlation_discovery_result()

    assert result.schema_version == "CRD-001"
    assert result.engine_id == "oracle.discovery.correlation.empty"
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert assert_correlation_contract_read_only(result) is True


def test_correlation_discovery_contract_opportunity_hash():
    opportunity = CorrelationDiscoveryOpportunity(
        opportunity_id="corr-test-001",
        primary_market_id="KXTEST-A",
        related_market_id="KXTEST-B",
        venue="kalshi",
        signal_type="correlation_break",
        relationship="positive_correlation_breakdown",
        confidence=0.72,
        magnitude=0.41,
        explanation="Test correlation breakdown opportunity.",
        evidence={"correlation": 0.82, "recent_correlation": 0.21},
    )

    assert opportunity.opportunity_hash
    assert opportunity.canonical()["opportunity_id"] == "corr-test-001"


def test_correlation_discovery_contract_result_count():
    opportunity = CorrelationDiscoveryOpportunity(
        opportunity_id="corr-test-001",
        primary_market_id="KXTEST-A",
        related_market_id="KXTEST-B",
        venue="kalshi",
        signal_type="correlation_break",
        relationship="positive_correlation_breakdown",
        confidence=0.72,
        magnitude=0.41,
        explanation="Test correlation breakdown opportunity.",
        evidence={"correlation": 0.82, "recent_correlation": 0.21},
    )

    result = CorrelationDiscoveryResult(
        schema_version="CRD-001",
        engine_id="oracle.discovery.correlation.contract.test",
        status="ok",
        opportunities=(opportunity,),
        read_only=True,
        result_hash="test-hash",
    )

    assert result.opportunity_count == 1
    assert result.read_only is True
    assert assert_correlation_contract_read_only(result) is True


if __name__ == "__main__":
    test_correlation_discovery_contract_empty_result()
    test_correlation_discovery_contract_opportunity_hash()
    test_correlation_discovery_contract_result_count()

    result = empty_correlation_discovery_result()

    print("[PASS] CRD-001 Correlation Discovery Contract")
    print(
        {
            "schema_version": result.schema_version,
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": result.opportunity_count,
            "read_only": result.read_only,
        }
    )
''', encoding="utf-8")

INIT.write_text(r'''
from .correlation_discovery_contract import (
    READ_ONLY,
    SCHEMA_VERSION,
    ENGINE_ID,
    CorrelationDiscoveryOpportunity,
    CorrelationDiscoveryResult,
    empty_correlation_discovery_result,
    assert_correlation_contract_read_only,
)
''', encoding="utf-8")

existing = OI_INIT.read_text(encoding="utf-8") if OI_INIT.exists() else ""
if "correlation_discovery_model" not in existing:
    OI_INIT.write_text(existing.rstrip() + "\n" + "# Correlation Discovery Model package registered for Phase 1 discovery.\n", encoding="utf-8")

print("========================================")
print(" CRD-001 INSTALLER")
print(" Correlation Discovery Contract")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {INIT}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {OI_INIT}")
print()
print("[DONE] CRD-001 installed")
print()
print("Run:")
print("py test_crd_001_correlation_discovery_contract.py")