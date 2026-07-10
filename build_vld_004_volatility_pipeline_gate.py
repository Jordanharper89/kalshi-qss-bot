from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence" / "volatility_discovery_model"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "volatility_pipeline_gate.py"
TEST = ROOT / "test_vld_004_volatility_pipeline_gate.py"
INIT = PKG / "__init__.py"

MODULE.write_text(r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping

from .volatility_discovery_engine import VolatilityDiscoveryResult


READ_ONLY = True
SCHEMA_VERSION = "VLD-004"
ENGINE_ID = "oracle.discovery.volatility.pipeline_gate"


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
class VolatilityPipelineGateResult:
    schema_version: str
    engine_id: str
    status: str
    accepted: bool
    reason: str
    discovery_result_hash: str
    opportunity_count: int
    checks: Dict[str, bool] = field(default_factory=dict)
    read_only: bool = True
    gate_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))


class VolatilityPipelineGate:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def validate(self, result: VolatilityDiscoveryResult) -> VolatilityPipelineGateResult:
        if not isinstance(result, VolatilityDiscoveryResult):
            raise TypeError("result must be a VolatilityDiscoveryResult")

        checks = {
            "read_only": result.read_only is True,
            "schema_present": bool(result.schema_version),
            "engine_present": bool(result.engine_id),
            "hash_present": bool(result.result_hash),
            "count_matches": result.opportunity_count == len(result.opportunities),
            "valid_status": result.status in {"ok", "empty"},
            "opportunities_have_ids": all(bool(o.opportunity_id) for o in result.opportunities),
            "opportunities_have_hashes": all(bool(o.opportunity_hash) for o in result.opportunities),
            "confidence_in_range": all(0.0 <= o.confidence <= 1.0 for o in result.opportunities),
            "magnitude_non_negative": all(o.magnitude >= 0.0 for o in result.opportunities),
            "signal_types_present": all(bool(o.signal_type) for o in result.opportunities),
            "regimes_present": all(bool(o.regime) for o in result.opportunities),
            "evidence_present": all(isinstance(o.evidence, dict) for o in result.opportunities),
        }

        accepted = all(checks.values())
        status = "accepted" if accepted else "rejected"
        failed = [name for name, passed in checks.items() if not passed]
        reason = "all volatility pipeline checks passed" if accepted else "failed checks: " + ", ".join(failed)

        unsigned = VolatilityPipelineGateResult(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            accepted=accepted,
            reason=reason,
            discovery_result_hash=result.result_hash,
            opportunity_count=result.opportunity_count,
            checks=checks,
            read_only=True,
            gate_hash="",
        )

        return VolatilityPipelineGateResult(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            accepted=unsigned.accepted,
            reason=unsigned.reason,
            discovery_result_hash=unsigned.discovery_result_hash,
            opportunity_count=unsigned.opportunity_count,
            checks=unsigned.checks,
            read_only=True,
            gate_hash=_stable_hash(unsigned.canonical()),
        )

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def validate_volatility_discovery_result(result: VolatilityDiscoveryResult) -> VolatilityPipelineGateResult:
    return VolatilityPipelineGate().validate(result)


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "VolatilityPipelineGate",
    "VolatilityPipelineGateResult",
    "validate_volatility_discovery_result",
]
''', encoding="utf-8")

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_discovery_engine import (
    discover_volatility_opportunities,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_pipeline_gate import (
    VolatilityPipelineGate,
    validate_volatility_discovery_result,
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
    }
]


def test_volatility_pipeline_gate_accepts_valid_result():
    result = discover_volatility_opportunities(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gate = VolatilityPipelineGate()
    assert gate.assert_read_only() is True

    gated = gate.validate(result)

    assert gated.schema_version == "VLD-004"
    assert gated.engine_id == "oracle.discovery.volatility.pipeline_gate"
    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.read_only is True
    assert gated.discovery_result_hash == result.result_hash
    assert gated.opportunity_count == result.opportunity_count
    assert gated.gate_hash
    assert all(gated.checks.values())


def test_volatility_pipeline_gate_accepts_empty_valid_result():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated = validate_volatility_discovery_result(result)

    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.opportunity_count == 0
    assert all(gated.checks.values())


def test_volatility_pipeline_gate_is_replayable():
    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated1 = validate_volatility_discovery_result(result)
    gated2 = validate_volatility_discovery_result(result)

    assert gated1.gate_hash == gated2.gate_hash


if __name__ == "__main__":
    test_volatility_pipeline_gate_accepts_valid_result()
    test_volatility_pipeline_gate_accepts_empty_valid_result()
    test_volatility_pipeline_gate_is_replayable()

    result = discover_volatility_opportunities(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gated = validate_volatility_discovery_result(result)

    print("[PASS] VLD-004 Volatility Pipeline Gate")
    print(
        {
            "schema_version": gated.schema_version,
            "engine_id": gated.engine_id,
            "status": gated.status,
            "accepted": gated.accepted,
            "read_only": gated.read_only,
        }
    )
''', encoding="utf-8")

existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
exports = '''
from .volatility_pipeline_gate import (
    VolatilityPipelineGate,
    VolatilityPipelineGateResult,
    validate_volatility_discovery_result,
)
'''
if "volatility_pipeline_gate" not in existing:
    INIT.write_text(existing.rstrip() + "\n" + exports.lstrip(), encoding="utf-8")

print("========================================")
print(" VLD-004 INSTALLER")
print(" Volatility Pipeline Gate")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] VLD-004 installed")
print()
print("Run:")
print("py test_vld_004_volatility_pipeline_gate.py")