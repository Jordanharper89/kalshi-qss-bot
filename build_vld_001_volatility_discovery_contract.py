from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_discovery_contract.py"
TEST = ROOT / "test_vld_001_volatility_discovery_contract.py"
INIT = PKG / "__init__.py"
OI_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Tuple


READ_ONLY = True
SCHEMA_VERSION = "VLD-001"
ENGINE_ID = "oracle.discovery.volatility.contract"


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
class VolatilityDiscoveryOpportunity:
    opportunity_id: str
    market_id: str
    venue: str
    asset: str
    signal_type: str
    regime: str
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
class VolatilityDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    opportunities: Tuple[VolatilityDiscoveryOpportunity, ...] = tuple()
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


def empty_volatility_discovery_result(
    engine_id: str = "oracle.discovery.volatility.empty",
) -> VolatilityDiscoveryResult:
    unsigned = VolatilityDiscoveryResult(
        schema_version=SCHEMA_VERSION,
        engine_id=engine_id,
        status="empty",
        opportunities=tuple(),
        read_only=True,
        result_hash="",
    )

    return VolatilityDiscoveryResult(
        schema_version=unsigned.schema_version,
        engine_id=unsigned.engine_id,
        status=unsigned.status,
        opportunities=unsigned.opportunities,
        read_only=True,
        result_hash=_stable_hash(unsigned.canonical()),
    )


def assert_volatility_contract_read_only(result: VolatilityDiscoveryResult) -> bool:
    if not isinstance(result, VolatilityDiscoveryResult):
        raise TypeError("result must be a VolatilityDiscoveryResult")
    if result.read_only is not True:
        raise AssertionError("volatility discovery result must be read-only")
    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilityDiscoveryOpportunity",
    "VolatilityDiscoveryResult",
    "empty_volatility_discovery_result",
    "assert_volatility_contract_read_only",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_contract import (
    VolatilityDiscoveryOpportunity,
    VolatilityDiscoveryResult,
    assert_volatility_contract_read_only,
    empty_volatility_discovery_result,
)


def test_volatility_discovery_contract_empty_result():
    result = empty_volatility_discovery_result()

    assert result.schema_version == "VLD-001"
    assert result.engine_id == "oracle.discovery.volatility.empty"
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert assert_volatility_contract_read_only(result) is True


def test_volatility_discovery_contract_opportunity_hash():
    opportunity = VolatilityDiscoveryOpportunity(
        opportunity_id="vol-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="volatility_regime_shift",
        regime="expanding",
        confidence=0.75,
        magnitude=0.42,
        explanation="Test volatility regime shift opportunity.",
        evidence={"realized_volatility": 0.31, "baseline_volatility": 0.18},
    )

    assert opportunity.opportunity_hash
    assert opportunity.canonical()["opportunity_id"] == "vol-test-001"


def test_volatility_discovery_contract_result_count():
    opportunity = VolatilityDiscoveryOpportunity(
        opportunity_id="vol-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="volatility_regime_shift",
        regime="expanding",
        confidence=0.75,
        magnitude=0.42,
        explanation="Test volatility regime shift opportunity.",
        evidence={"realized_volatility": 0.31, "baseline_volatility": 0.18},
    )

    result = VolatilityDiscoveryResult(
        schema_version="VLD-001",
        engine_id="oracle.discovery.volatility.contract.test",
        status="ok",
        opportunities=(opportunity,),
        read_only=True,
        result_hash="test-hash",
    )

    assert result.opportunity_count == 1
    assert result.read_only is True
    assert assert_volatility_contract_read_only(result) is True


if __name__ == "__main__":
    test_volatility_discovery_contract_empty_result()
    test_volatility_discovery_contract_opportunity_hash()
    test_volatility_discovery_contract_result_count()

    result = empty_volatility_discovery_result()

    print("[PASS] VLD-001 Volatility Discovery Contract")
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
from .volatility_discovery_contract import (
    READ_ONLY,
    SCHEMA_VERSION,
    ENGINE_ID,
    VolatilityDiscoveryOpportunity,
    VolatilityDiscoveryResult,
    empty_volatility_discovery_result,
    assert_volatility_contract_read_only,
)
''', encoding="utf-8")

existing = OI_INIT.read_text(encoding="utf-8") if OI_INIT.exists() else ""
if "volatility_discovery_model" not in existing:
    OI_INIT.write_text(existing.rstrip() + "\n" + "# Volatility Discovery Model package registered for Phase 1 discovery.\n", encoding="utf-8")

print("========================================")
print(" VLD-001 INSTALLER")
print(" Volatility Discovery Contract")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {INIT}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {OI_INIT}")
print()
print("[DONE] VLD-001 installed")
print()
print("Run:")
print("py test_vld_001_volatility_discovery_contract.py")