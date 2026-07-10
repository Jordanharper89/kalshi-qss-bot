from pathlib import Path

ROOT = Path.cwd()
PKG = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "market_regime_discovery_model"
)
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "market_regime_discovery_contract.py"
TEST = ROOT / "test_rgd_001_market_regime_discovery_contract.py"
INIT = PKG / "__init__.py"
OI_INIT = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "__init__.py"
)

MODULE.write_text(
r'''
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Mapping, Tuple


READ_ONLY = True
SCHEMA_VERSION = "RGD-001"
ENGINE_ID = "oracle.discovery.market_regime.contract"

ALLOWED_REGIMES = frozenset(
    {
        "unknown",
        "stable",
        "trending",
        "mean_reverting",
        "volatile",
        "illiquid",
        "dislocated",
        "event_driven",
        "risk_on",
        "risk_off",
        "transition",
    }
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


def _validate_probability(
    value: float,
    field_name: str,
) -> float:
    normalized = float(value)

    if not 0.0 <= normalized <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0.0 and 1.0"
        )

    return normalized


@dataclass(frozen=True)
class MarketRegimeEvidence:
    evidence_id: str
    source_family: str
    signal_type: str
    contribution: float
    source_hash: str
    details: Dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not str(self.evidence_id).strip():
            raise ValueError(
                "evidence_id must not be empty"
            )

        if not str(self.source_family).strip():
            raise ValueError(
                "source_family must not be empty"
            )

        if not str(self.signal_type).strip():
            raise ValueError(
                "signal_type must not be empty"
            )

        if not str(self.source_hash).strip():
            raise ValueError(
                "source_hash must not be empty"
            )

        _validate_probability(
            self.contribution,
            "contribution",
        )

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def evidence_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class MarketRegimeOpportunity:
    opportunity_id: str
    market_id: str
    venue: str
    asset: str
    prior_regime: str
    current_regime: str
    transition_type: str
    confidence: float
    magnitude: float
    observed_at: str
    explanation: str
    evidence: Tuple[
        MarketRegimeEvidence,
        ...,
    ] = tuple()

    def __post_init__(self) -> None:
        if not str(self.opportunity_id).strip():
            raise ValueError(
                "opportunity_id must not be empty"
            )

        if not str(self.market_id).strip():
            raise ValueError(
                "market_id must not be empty"
            )

        if not str(self.venue).strip():
            raise ValueError(
                "venue must not be empty"
            )

        if not str(self.asset).strip():
            raise ValueError(
                "asset must not be empty"
            )

        if self.prior_regime not in ALLOWED_REGIMES:
            raise ValueError(
                "prior_regime is not supported"
            )

        if self.current_regime not in ALLOWED_REGIMES:
            raise ValueError(
                "current_regime is not supported"
            )

        if not str(self.transition_type).strip():
            raise ValueError(
                "transition_type must not be empty"
            )

        _validate_probability(
            self.confidence,
            "confidence",
        )
        _validate_probability(
            self.magnitude,
            "magnitude",
        )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if not str(self.explanation).strip():
            raise ValueError(
                "explanation must not be empty"
            )

        evidence_ids = [
            item.evidence_id
            for item in self.evidence
        ]

        if len(evidence_ids) != len(
            set(evidence_ids)
        ):
            raise ValueError(
                "evidence identifiers must be unique"
            )

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["evidence"] = [
            item.canonical()
            for item in self.evidence
        ]
        return _deep_sort(data)

    @property
    def opportunity_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class MarketRegimeDiscoveryResult:
    schema_version: str
    engine_id: str
    status: str
    observed_at: str
    opportunities: Tuple[
        MarketRegimeOpportunity,
        ...,
    ] = tuple()
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    read_only: bool = True
    result_hash: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"schema_version must be {SCHEMA_VERSION}"
            )

        if not str(self.engine_id).strip():
            raise ValueError(
                "engine_id must not be empty"
            )

        if self.status not in {
            "ok",
            "empty",
            "rejected",
        }:
            raise ValueError(
                "status must be ok, empty, or rejected"
            )

        if not str(self.observed_at).strip():
            raise ValueError(
                "observed_at must not be empty"
            )

        if self.read_only is not True:
            raise ValueError(
                "market regime results must be read-only"
            )

        if (
            self.status == "empty"
            and self.opportunities
        ):
            raise ValueError(
                "empty results cannot contain opportunities"
            )

        if (
            self.status == "ok"
            and not self.opportunities
        ):
            raise ValueError(
                "ok results must contain opportunities"
            )

        opportunity_ids = [
            item.opportunity_id
            for item in self.opportunities
        ]

        if len(opportunity_ids) != len(
            set(opportunity_ids)
        ):
            raise ValueError(
                "opportunity identifiers must be unique"
            )

    @property
    def opportunity_count(self) -> int:
        return len(self.opportunities)

    def canonical(
        self,
        include_result_hash: bool = True,
    ) -> Dict[str, Any]:
        data = asdict(self)
        data["opportunity_count"] = (
            self.opportunity_count
        )
        data["opportunities"] = [
            item.canonical()
            for item in self.opportunities
        ]

        if not include_result_hash:
            data["result_hash"] = ""

        return _deep_sort(data)

    def expected_result_hash(self) -> str:
        return _stable_hash(
            self.canonical(
                include_result_hash=False
            )
        )

    def verify_result_hash(self) -> bool:
        return (
            bool(self.result_hash)
            and self.result_hash
            == self.expected_result_hash()
        )


def build_market_regime_discovery_result(
    engine_id: str,
    observed_at: str,
    opportunities: Tuple[
        MarketRegimeOpportunity,
        ...,
    ] = tuple(),
    metadata: Mapping[str, Any] | None = None,
    status: str | None = None,
) -> MarketRegimeDiscoveryResult:
    ordered_opportunities = tuple(
        sorted(
            tuple(opportunities or tuple()),
            key=lambda item: (
                item.market_id,
                item.venue,
                item.asset,
                item.current_regime,
                item.transition_type,
                item.opportunity_id,
            ),
        )
    )

    resolved_status = status or (
        "ok"
        if ordered_opportunities
        else "empty"
    )

    unsigned = MarketRegimeDiscoveryResult(
        schema_version=SCHEMA_VERSION,
        engine_id=str(engine_id),
        status=resolved_status,
        observed_at=str(observed_at),
        opportunities=ordered_opportunities,
        metadata=dict(metadata or {}),
        read_only=True,
        result_hash="",
    )

    return MarketRegimeDiscoveryResult(
        schema_version=unsigned.schema_version,
        engine_id=unsigned.engine_id,
        status=unsigned.status,
        observed_at=unsigned.observed_at,
        opportunities=unsigned.opportunities,
        metadata=unsigned.metadata,
        read_only=True,
        result_hash=(
            unsigned.expected_result_hash()
        ),
    )


def empty_market_regime_discovery_result(
    engine_id: str = (
        "oracle.discovery.market_regime.empty"
    ),
    observed_at: str = (
        "1970-01-01T00:00:00+00:00"
    ),
) -> MarketRegimeDiscoveryResult:
    return build_market_regime_discovery_result(
        engine_id=engine_id,
        observed_at=observed_at,
        opportunities=tuple(),
        metadata={
            "reason": "no regime opportunities",
        },
        status="empty",
    )


def assert_market_regime_contract_read_only(
    result: MarketRegimeDiscoveryResult,
) -> bool:
    if not isinstance(
        result,
        MarketRegimeDiscoveryResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeDiscoveryResult"
        )

    if result.read_only is not True:
        raise AssertionError(
            "market regime discovery result "
            "must be read-only"
        )

    return True


def validate_market_regime_discovery_result(
    result: MarketRegimeDiscoveryResult,
) -> Dict[str, Any]:
    if not isinstance(
        result,
        MarketRegimeDiscoveryResult,
    ):
        raise TypeError(
            "result must be a "
            "MarketRegimeDiscoveryResult"
        )

    checks = {
        "schema_version": (
            result.schema_version
            == SCHEMA_VERSION
        ),
        "engine_id_present": bool(
            result.engine_id
        ),
        "valid_status": (
            result.status
            in {
                "ok",
                "empty",
                "rejected",
            }
        ),
        "observed_at_present": bool(
            result.observed_at
        ),
        "read_only": (
            result.read_only is True
        ),
        "count_matches": (
            result.opportunity_count
            == len(result.opportunities)
        ),
        "status_consistent": (
            (
                result.status == "ok"
                and result.opportunity_count > 0
            )
            or (
                result.status == "empty"
                and result.opportunity_count == 0
            )
            or result.status == "rejected"
        ),
        "opportunity_hashes_present": all(
            bool(item.opportunity_hash)
            for item in result.opportunities
        ),
        "confidence_in_range": all(
            0.0 <= item.confidence <= 1.0
            for item in result.opportunities
        ),
        "magnitude_in_range": all(
            0.0 <= item.magnitude <= 1.0
            for item in result.opportunities
        ),
        "regimes_supported": all(
            item.prior_regime in ALLOWED_REGIMES
            and item.current_regime
            in ALLOWED_REGIMES
            for item in result.opportunities
        ),
        "result_hash_valid": (
            result.verify_result_hash()
        ),
    }

    return {
        "accepted": all(checks.values()),
        "checks": checks,
        "schema_version": (
            result.schema_version
        ),
        "engine_id": result.engine_id,
        "status": result.status,
        "opportunity_count": (
            result.opportunity_count
        ),
        "result_hash": result.result_hash,
        "read_only": result.read_only,
    }


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "ALLOWED_REGIMES",
    "MarketRegimeEvidence",
    "MarketRegimeOpportunity",
    "MarketRegimeDiscoveryResult",
    "build_market_regime_discovery_result",
    "empty_market_regime_discovery_result",
    "assert_market_regime_contract_read_only",
    "validate_market_regime_discovery_result",
]
''',
    encoding="utf-8",
)

TEST.write_text(
r'''
from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_discovery_contract import (
    ALLOWED_REGIMES,
    MarketRegimeDiscoveryResult,
    MarketRegimeEvidence,
    MarketRegimeOpportunity,
    assert_market_regime_contract_read_only,
    build_market_regime_discovery_result,
    empty_market_regime_discovery_result,
    validate_market_regime_discovery_result,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"


def _build_evidence():
    return MarketRegimeEvidence(
        evidence_id="evidence-volatility-001",
        source_family="volatility_discovery",
        signal_type="volatility_expansion",
        contribution=0.80,
        source_hash="source-hash-volatility-001",
        details={
            "realized_volatility": 0.42,
            "baseline_volatility": 0.20,
        },
    )


def _build_opportunity():
    return MarketRegimeOpportunity(
        opportunity_id="regime-opportunity-001",
        market_id="KXTEST",
        venue="kalshi",
        asset="binary_event",
        prior_regime="stable",
        current_regime="volatile",
        transition_type=(
            "stable_to_volatile"
        ),
        confidence=0.84,
        magnitude=0.71,
        observed_at=OBSERVED_AT,
        explanation=(
            "Volatility expansion and liquidity "
            "deterioration indicate a regime transition."
        ),
        evidence=(
            _build_evidence(),
        ),
    )


def test_market_regime_contract_empty_result():
    result = (
        empty_market_regime_discovery_result(
            observed_at=OBSERVED_AT,
        )
    )

    assert result.schema_version == "RGD-001"
    assert result.engine_id == (
        "oracle.discovery.market_regime.empty"
    )
    assert result.status == "empty"
    assert result.opportunity_count == 0
    assert result.opportunities == tuple()
    assert result.read_only is True
    assert result.result_hash
    assert result.verify_result_hash() is True
    assert (
        assert_market_regime_contract_read_only(
            result
        )
        is True
    )


def test_market_regime_contract_builds_valid_result():
    opportunity = _build_opportunity()

    result = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(opportunity,),
            metadata={
                "scenario": (
                    "volatility_transition"
                ),
            },
        )
    )

    assert result.status == "ok"
    assert result.opportunity_count == 1
    assert result.read_only is True
    assert result.result_hash
    assert result.verify_result_hash() is True
    assert (
        result.opportunities[0]
        .opportunity_hash
    )
    assert (
        result.opportunities[0]
        .evidence[0]
        .evidence_hash
    )


def test_market_regime_contract_is_replayable():
    opportunity = _build_opportunity()

    result1 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(opportunity,),
            metadata={
                "source": "deterministic",
            },
        )
    )

    result2 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(opportunity,),
            metadata={
                "source": "deterministic",
            },
        )
    )

    assert (
        result1.result_hash
        == result2.result_hash
    )
    assert (
        result1.opportunities[0]
        .opportunity_hash
        == result2.opportunities[0]
        .opportunity_hash
    )


def test_market_regime_contract_orders_opportunities():
    first = MarketRegimeOpportunity(
        opportunity_id="opportunity-b",
        market_id="MARKET-B",
        venue="kalshi",
        asset="binary_event",
        prior_regime="stable",
        current_regime="trending",
        transition_type="trend_emergence",
        confidence=0.70,
        magnitude=0.50,
        observed_at=OBSERVED_AT,
        explanation="Trend regime detected.",
        evidence=tuple(),
    )

    second = MarketRegimeOpportunity(
        opportunity_id="opportunity-a",
        market_id="MARKET-A",
        venue="kalshi",
        asset="binary_event",
        prior_regime="stable",
        current_regime="volatile",
        transition_type=(
            "volatility_expansion"
        ),
        confidence=0.75,
        magnitude=0.60,
        observed_at=OBSERVED_AT,
        explanation=(
            "Volatile regime detected."
        ),
        evidence=tuple(),
    )

    result1 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.order_test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(first, second),
        )
    )

    result2 = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.order_test"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(second, first),
        )
    )

    assert [
        item.market_id
        for item in result1.opportunities
    ] == [
        "MARKET-A",
        "MARKET-B",
    ]

    assert (
        result1.result_hash
        == result2.result_hash
    )


def test_market_regime_contract_validation():
    result = (
        build_market_regime_discovery_result(
            engine_id=(
                "oracle.discovery."
                "market_regime.validation"
            ),
            observed_at=OBSERVED_AT,
            opportunities=(
                _build_opportunity(),
            ),
        )
    )

    validation = (
        validate_market_regime_discovery_result(
            result
        )
    )

    assert validation["accepted"] is True
    assert all(
        validation["checks"].values()
    )
    assert (
        validation["opportunity_count"]
        == 1
    )
    assert validation["read_only"] is True


def test_market_regime_contract_rejects_invalid_regime():
    try:
        MarketRegimeOpportunity(
            opportunity_id="invalid-regime",
            market_id="KXTEST",
            venue="kalshi",
            asset="binary_event",
            prior_regime="stable",
            current_regime="unsupported_regime",
            transition_type="invalid",
            confidence=0.50,
            magnitude=0.50,
            observed_at=OBSERVED_AT,
            explanation="Invalid test.",
            evidence=tuple(),
        )
    except ValueError as exc:
        assert str(exc) == (
            "current_regime is not supported"
        )
    else:
        raise AssertionError(
            "expected invalid regime rejection"
        )


def test_market_regime_contract_rejects_mutable_result():
    try:
        MarketRegimeDiscoveryResult(
            schema_version="RGD-001",
            engine_id=(
                "oracle.discovery."
                "market_regime.invalid"
            ),
            status="empty",
            observed_at=OBSERVED_AT,
            opportunities=tuple(),
            metadata={},
            read_only=False,
            result_hash="",
        )
    except ValueError as exc:
        assert str(exc) == (
            "market regime results "
            "must be read-only"
        )
    else:
        raise AssertionError(
            "expected mutable result rejection"
        )


def test_market_regime_contract_allowed_regimes():
    required = {
        "unknown",
        "stable",
        "trending",
        "mean_reverting",
        "volatile",
        "illiquid",
        "dislocated",
        "event_driven",
        "risk_on",
        "risk_off",
        "transition",
    }

    assert required == set(
        ALLOWED_REGIMES
    )


if __name__ == "__main__":
    test_market_regime_contract_empty_result()
    test_market_regime_contract_builds_valid_result()
    test_market_regime_contract_is_replayable()
    test_market_regime_contract_orders_opportunities()
    test_market_regime_contract_validation()
    test_market_regime_contract_rejects_invalid_regime()
    test_market_regime_contract_rejects_mutable_result()
    test_market_regime_contract_allowed_regimes()

    result = (
        empty_market_regime_discovery_result(
            observed_at=OBSERVED_AT,
        )
    )

    print(
        "[PASS] RGD-001 "
        "Market Regime Discovery Contract"
    )
    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "opportunities": (
                result.opportunity_count
            ),
            "read_only": result.read_only,
        }
    )
''',
    encoding="utf-8",
)

INIT.write_text(
r'''
from .market_regime_discovery_contract import (
    ALLOWED_REGIMES,
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimeDiscoveryResult,
    MarketRegimeEvidence,
    MarketRegimeOpportunity,
    assert_market_regime_contract_read_only,
    build_market_regime_discovery_result,
    empty_market_regime_discovery_result,
    validate_market_regime_discovery_result,
)
''',
    encoding="utf-8",
)

existing = (
    OI_INIT.read_text(encoding="utf-8")
    if OI_INIT.exists()
    else ""
)

registration = (
    "# Market Regime Discovery Model package "
    "registered for Phase 1 discovery."
)

if registration not in existing:
    OI_INIT.write_text(
        existing.rstrip()
        + "\n"
        + registration
        + "\n",
        encoding="utf-8",
    )

print("========================================")
print(" RGD-001 INSTALLER")
print(" Market Regime Discovery Contract")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {INIT}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {OI_INIT}")
print()
print("[DONE] RGD-001 installed")
print()
print("Run:")
print(
    "py "
    "test_rgd_001_market_regime_"
    "discovery_contract.py"
)