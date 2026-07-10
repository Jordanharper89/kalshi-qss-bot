
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_discovery_engine import (
    discover_market_regimes,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_pipeline_gate import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimePipelineGateCheck,
    MarketRegimePipelineGateResult,
    assert_market_regime_pipeline_read_only,
    evaluate_market_regime_pipeline,
    run_market_regime_pipeline_gate,
    validate_market_regime_pipeline_gate,
)


OBSERVED_AT = "2026-07-09T00:00:00+00:00"


def _record(
    signal_id,
    signal_type,
    value,
    source_family,
    reliability=0.90,
    prior_regime="stable",
):
    return {
        "signal_id": signal_id,
        "market_id": "KXREGIME",
        "venue": "kalshi",
        "asset": "binary_event",
        "source_family": source_family,
        "signal_type": signal_type,
        "value": value,
        "reliability": reliability,
        "observed_at": OBSERVED_AT,
        "prior_regime": prior_regime,
        "source_hash": (
            f"source-hash-{signal_id}"
        ),
        "details": {
            "fixture": True,
        },
    }


def _valid_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "ok",
        "records": (
            _record(
                signal_id="volatility-001",
                signal_type="volatility",
                value=0.95,
                reliability=0.95,
                source_family=(
                    "volatility_discovery"
                ),
            ),
            _record(
                signal_id="dispersion-001",
                signal_type="dispersion",
                value=0.90,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _record(
                signal_id="correlation-001",
                signal_type=(
                    "correlation_breakdown"
                ),
                value=0.85,
                source_family=(
                    "correlation_discovery"
                ),
            ),
            _record(
                signal_id="liquidity-001",
                signal_type="liquidity",
                value=-0.50,
                reliability=0.85,
                source_family=(
                    "liquidity_discovery"
                ),
            ),
        ),
        "observed_at": OBSERVED_AT,
        "read_only": True,
    }


def _empty_source():
    return {
        "schema_version": "RGD-002",
        "engine_id": (
            "oracle.discovery.market_regime."
            "source_adapter"
        ),
        "status": "empty",
        "records": tuple(),
        "observed_at": OBSERVED_AT,
        "read_only": True,
    }


def test_pipeline_gate_constants():
    assert SCHEMA_VERSION == "RGD-004"
    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "pipeline_gate"
    )
    assert READ_ONLY is True


def test_pipeline_gate_accepts_valid_pipeline():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert isinstance(
        result,
        MarketRegimePipelineGateResult,
    )

    assert result.schema_version == "RGD-004"
    assert result.engine_id == ENGINE_ID
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.source_status == "ok"
    assert result.source_record_count == 4
    assert result.discovery_status == "ok"
    assert result.opportunity_count == 1
    assert result.rejection_reasons == tuple()
    assert result.read_only is True
    assert result.verify_gate_hash() is True

    assert all(
        check.accepted
        for check in result.checks
    )


def test_pipeline_gate_accepts_empty_pipeline():
    result = evaluate_market_regime_pipeline(
        source_result=_empty_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.source_status == "empty"
    assert result.source_record_count == 0
    assert result.discovery_status == "empty"
    assert result.opportunity_count == 0
    assert result.rejection_reasons == tuple()
    assert result.verify_gate_hash() is True


def test_pipeline_gate_accepts_prebuilt_result():
    source = _valid_source()

    discovery_result = (
        discover_market_regimes(
            source_result=source,
            observed_at=OBSERVED_AT,
        )
    )

    gate_result = (
        evaluate_market_regime_pipeline(
            source_result=source,
            discovery_result=(
                discovery_result
            ),
            observed_at=OBSERVED_AT,
        )
    )

    assert gate_result.accepted is True
    assert gate_result.status == "accepted"

    assert (
        gate_result.discovery_hash
        == discovery_result.result_hash
    )


def test_pipeline_gate_rejects_wrong_source_schema():
    source = dict(
        _valid_source()
    )

    source["schema_version"] = "BAD-001"

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "invalid_source_schema_version"
        in result.rejection_reasons
    )

    check = {
        item.check_id: item
        for item in result.checks
    }["source_schema_version"]

    assert check.accepted is False


def test_pipeline_gate_rejects_wrong_source_engine():
    source = dict(
        _valid_source()
    )

    source["engine_id"] = (
        "oracle.invalid.source"
    )

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "invalid_source_engine_id"
        in result.rejection_reasons
    )


def test_pipeline_gate_rejects_mutable_source():
    source = dict(
        _valid_source()
    )

    source["read_only"] = False

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "source_not_read_only"
        in result.rejection_reasons
    )


def test_pipeline_gate_rejects_duplicate_records():
    source = dict(
        _valid_source()
    )

    record = _record(
        signal_id="duplicate-001",
        signal_type="volatility",
        value=0.90,
        source_family=(
            "volatility_discovery"
        ),
    )

    source["records"] = (
        record,
        record,
    )

    try:
        evaluate_market_regime_pipeline(
            source_result=source,
            observed_at=OBSERVED_AT,
        )
    except ValueError as exc:
        assert str(exc) == (
            "signal identifiers must be unique"
        )
    else:
        raise AssertionError(
            "expected duplicate source "
            "records to be rejected"
        )


def test_pipeline_gate_detects_inconsistent_empty_source():
    source = dict(
        _valid_source()
    )

    source["status"] = "empty"

    result = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    assert result.accepted is False
    assert result.status == "rejected"

    assert (
        "inconsistent_empty_source"
        in result.rejection_reasons
    )


def test_pipeline_gate_is_deterministic():
    result_1 = run_market_regime_pipeline_gate(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    result_2 = run_market_regime_pipeline_gate(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert result_1 == result_2

    assert (
        result_1.gate_hash
        == result_2.gate_hash
    )

    assert (
        result_1.source_hash
        == result_2.source_hash
    )

    assert (
        result_1.discovery_hash
        == result_2.discovery_hash
    )


def test_pipeline_gate_input_order_independent():
    source = _valid_source()

    reversed_source = dict(source)

    reversed_source["records"] = tuple(
        reversed(
            source["records"]
        )
    )

    result_1 = evaluate_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    result_2 = evaluate_market_regime_pipeline(
        source_result=reversed_source,
        observed_at=OBSERVED_AT,
    )

    assert (
        result_1.discovery_hash
        == result_2.discovery_hash
    )

    assert (
        result_1.status
        == result_2.status
    )

    assert (
        result_1.opportunity_count
        == result_2.opportunity_count
    )

    assert (
        result_1.source_hash
        == result_2.source_hash
    )

    assert (
        result_1.gate_hash
        == result_2.gate_hash
    )

    assert result_1 == result_2


def test_pipeline_gate_validation():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_pipeline_gate(
            result
        )
    )

    assert validation["accepted"] is True
    assert all(
        validation["checks"].values()
    )


def test_pipeline_gate_read_only():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_pipeline_read_only(
            result
        )
        is True
    )

    try:
        result.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "gate result must be immutable"
        )

    check = result.checks[0]

    assert isinstance(
        check,
        MarketRegimePipelineGateCheck,
    )

    try:
        check.accepted = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "gate check must be immutable"
        )


def test_pipeline_gate_as_dict():
    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-004"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["accepted"] is True
    assert payload["read_only"] is True

    assert payload["gate_hash"] == (
        result.gate_hash
    )

    assert len(payload["checks"]) == len(
        result.checks
    )


def test_pipeline_gate_requires_source():
    try:
        evaluate_market_regime_pipeline(
            source_result=None,
            observed_at=OBSERVED_AT,
        )
    except TypeError as exc:
        assert str(exc) == (
            "source_result must not be None"
        )
    else:
        raise AssertionError(
            "expected source requirement"
        )


if __name__ == "__main__":
    test_pipeline_gate_constants()
    test_pipeline_gate_accepts_valid_pipeline()
    test_pipeline_gate_accepts_empty_pipeline()
    test_pipeline_gate_accepts_prebuilt_result()
    test_pipeline_gate_rejects_wrong_source_schema()
    test_pipeline_gate_rejects_wrong_source_engine()
    test_pipeline_gate_rejects_mutable_source()
    test_pipeline_gate_rejects_duplicate_records()
    test_pipeline_gate_detects_inconsistent_empty_source()
    test_pipeline_gate_is_deterministic()
    test_pipeline_gate_input_order_independent()
    test_pipeline_gate_validation()
    test_pipeline_gate_read_only()
    test_pipeline_gate_as_dict()
    test_pipeline_gate_requires_source()

    result = evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-004 "
        "Market Regime Pipeline Gate"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "source_records": (
                result.source_record_count
            ),
            "opportunities": (
                result.opportunity_count
            ),
            "checks": len(
                result.checks
            ),
            "read_only": result.read_only,
        }
    )
