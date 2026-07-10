from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "liquidity_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "liquidity_discovery_contract.py"
TEST = ROOT / "test_lqd_001_liquidity_discovery_contract.py"
INIT = PKG / "__init__.py"
OI_INIT = ROOT / "qseries_v2" / "oracle_intelligence" / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Tuple


READ_ONLY = True
SCHEMA_VERSION = "LQD-001"
ENGINE_ID = "oracle.discovery.liquidity.contract"


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
class LiquidityDiscoveryOpportunity:
    opportunity_id: str
    market_id: str
    venue: str
    asset: str
    signal_type: str
    direction: str
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
class LiquidityDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    opportunities: Tuple[LiquidityDiscoveryOpportunity, ...] = tuple()
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


def empty_liquidity_discovery_result(
    engine_id: str = "oracle.discovery.liquidity.empty",
) -> LiquidityDiscoveryResult:
    unsigned = LiquidityDiscoveryResult(
        schema_version=SCHEMA_VERSION,
        engine_id=engine_id,
        status="empty",
        opportunities=tuple(),
        read_only=True,
        result_hash="",
    )

    return LiquidityDiscoveryResult(
        schema_version=unsigned.schema_version,
        engine_id=unsigned.engine_id,
        status=unsigned.status,
        opportunities=unsigned.opportunities,
        read_only=True,
        result_hash=_stable_hash(unsigned.canonical()),
    )


def assert_liquidity_contract_read_only(result: LiquidityDiscoveryResult) -> bool:
    if not isinstance(result, LiquidityDiscoveryResult):
        raise TypeError("result must be a LiquidityDiscoveryResult")
    if result.read_only is not True:
        raise AssertionError("liquidity discovery result must be read-only")
    return True


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "LiquidityDiscoveryOpportunity",
    "LiquidityDiscoveryResult",
    "empty_liquidity_discovery_result",
    "assert_liquidity_contract_read_only",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_discovery_contract import (
    LiquidityDiscoveryOpportunity,
    LiquidityDiscoveryResult,
    assert_liquidity_contract_read_only,
    empty_liquidity_discovery_result,
)


def test_liquidity_discovery_contract_empty_result():
    result = empty_liquidity_discovery_result()

    assert result.schema_version == "LQD-001"
    assert result.engine_id == "oracle.discovery.liquidity.empty"
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert assert_liquidity_contract_read_only(result) is True


def test_liquidity_discovery_contract_opportunity_hash():
    opportunity = LiquidityDiscoveryOpportunity(
        opportunity_id="liq-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="liquidity_gap",
        direction="thin_liquidity",
        confidence=0.7,
        magnitude=0.4,
        explanation="Test liquidity gap opportunity.",
        evidence={"spread": 0.08, "depth": 100},
    )

    assert opportunity.opportunity_hash
    assert opportunity.canonical()["opportunity_id"] == "liq-test-001"


def test_liquidity_discovery_contract_result_count():
    opportunity = LiquidityDiscoveryOpportunity(
        opportunity_id="liq-test-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        signal_type="liquidity_gap",
        direction="thin_liquidity",
        confidence=0.7,
        magnitude=0.4,
        explanation="Test liquidity gap opportunity.",
        evidence={"spread": 0.08, "depth": 100},
    )

    result = LiquidityDiscoveryResult(
        schema_version="LQD-001",
        engine_id="oracle.discovery.liquidity.contract.test",
        status="ok",
        opportunities=(opportunity,),
        read_only=True,
        result_hash="test-hash",
    )

    assert result.opportunity_count == 1
    assert result.read_only is True
    assert assert_liquidity_contract_read_only(result) is True


if __name__ == "__main__":
    test_liquidity_discovery_contract_empty_result()
    test_liquidity_discovery_contract_opportunity_hash()
    test_liquidity_discovery_contract_result_count()

    result = empty_liquidity_discovery_result()

    print("[PASS] LQD-001 Liquidity Discovery Contract")
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
from .liquidity_discovery_contract import (
    READ_ONLY,
    SCHEMA_VERSION,
    ENGINE_ID,
    LiquidityDiscoveryOpportunity,
    LiquidityDiscoveryResult,
    empty_liquidity_discovery_result,
    assert_liquidity_contract_read_only,
)
''', encoding="utf-8")

if OI_INIT.exists():
    existing = OI_INIT.read_text(encoding="utf-8")
else:
    existing = ""

if "liquidity_discovery_model" not in existing:
    OI_INIT.write_text(existing.rstrip() + "\n" + "# Liquidity Discovery Model package registered for Phase 1 discovery.\n", encoding="utf-8")

print("========================================")
print(" LQD-001 INSTALLER")
print(" Liquidity Discovery Contract")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {INIT}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {OI_INIT}")
print()
print("[DONE] LQD-001 installed")
print()
print("Run:")
print("py test_lqd_001_liquidity_discovery_contract.py")