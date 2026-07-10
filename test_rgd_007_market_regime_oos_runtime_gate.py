
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_oos_runtime_gate import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimeOOSCheck,
    MarketRegimeOOSRuntimeGateResult,
    MarketRegimeOOSWindow,
    assert_market_regime_oos_runtime_read_only,
    evaluate_market_regime_oos_runtime,
    run_market_regime_oos_runtime_gate,
    validate_market_regime_oos_runtime_gate,
)


TRAINING_END = "2026-07-01T23:59:59+00:00"
EVALUATION_START = "2026-07-02T00:00:00+00:00"
EVALUATION_END = "2026-07-10T23:59:59+00:00"
OBSERVED_AT = "2026-07-10T20:00:00+00:00"


def _window():
    return MarketRegimeOOSWindow(
        training_end=TRAINING_END,
        evaluation_start=EVALUATION_START,
        evaluation_end=EVALUATION_END,
    )


def _record(
    signal_id,
    signal_type,
    value,
    source_family,
    observed_at=OBSERVED_AT,
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
        "observed_at": observed_at,
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


def test_oos_constants():
    assert SCHEMA_VERSION == "RGD-007"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "oos_runtime_gate"
    )

    assert READ_ONLY is True


def test_oos_window_validation():
    window = _window()

    assert window.training_end == TRAINING_END

    assert (
        window.evaluation_start
        == EVALUATION_START
    )

    assert (
        window.evaluation_end
        == EVALUATION_END
    )

    try:
        MarketRegimeOOSWindow(
            training_end=EVALUATION_START,
            evaluation_start=(
                EVALUATION_START
            ),
            evaluation_end=EVALUATION_END,
        )
    except ValueError as exc:
        assert str(exc) == (
            "training_end must be before "
            "evaluation_start"
        )
    else:
        raise AssertionError(
            "expected invalid OOS window"
        )


def test_oos_accepts_valid_runtime():
    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert isinstance(
        result,
        MarketRegimeOOSRuntimeGateResult,
    )

    assert result.schema_version == "RGD-007"
    assert result.engine_id == ENGINE_ID
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.source_record_count == 4
    assert result.in_window_record_count == 4
    assert result.pre_window_record_count == 0
    assert result.post_window_record_count == 0
    assert (
        result.invalid_timestamp_record_count
        == 0
    )
    assert result.rejection_reasons == tuple()
    assert result.pipeline_result.accepted is True
    assert result.pipeline_result.status == (
        "completed"
    )
    assert result.read_only is True
    assert result.verify_result_hash() is True

    assert all(
        check.accepted
        for check in result.checks
    )


def test_oos_accepts_empty_runtime():
    result = evaluate_market_regime_oos_runtime(
        source_result=_empty_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.source_record_count == 0
    assert result.in_window_record_count == 0
    assert (
        result.invalid_timestamp_record_count
        == 0
    )
    assert result.pipeline_result.status == (
        "empty"
    )
    assert result.verify_result_hash() is True


def test_oos_rejects_training_leakage():
    source = _valid_source()

    source["records"] = (
        *source["records"],
        _record(
            signal_id="training-record",
            signal_type="volatility",
            value=0.50,
            source_family=(
                "volatility_discovery"
            ),
            observed_at=(
                "2026-06-30T12:00:00+00:00"
            ),
        ),
    )

    result = evaluate_market_regime_oos_runtime(
        source_result=source,
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.pre_window_record_count == 1

    assert (
        "training_data_leakage"
        in result.rejection_reasons
    )


def test_oos_rejects_future_leakage():
    source = _valid_source()

    source["records"] = (
        *source["records"],
        _record(
            signal_id="future-record",
            signal_type="volatility",
            value=0.50,
            source_family=(
                "volatility_discovery"
            ),
            observed_at=(
                "2026-07-11T12:00:00+00:00"
            ),
        ),
    )

    result = evaluate_market_regime_oos_runtime(
        source_result=source,
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.post_window_record_count == 1

    assert (
        "future_data_leakage"
        in result.rejection_reasons
    )


def test_oos_rejects_invalid_timestamp():
    source = _valid_source()

    source["records"] = (
        *source["records"],
        _record(
            signal_id="bad-time-record",
            signal_type="volatility",
            value=0.50,
            source_family=(
                "volatility_discovery"
            ),
            observed_at="not-a-timestamp",
        ),
    )

    result = evaluate_market_regime_oos_runtime(
        source_result=source,
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.invalid_timestamp_record_count
        == 1
    )

    assert (
        "invalid_record_timestamp"
        in result.rejection_reasons
    )


def test_oos_rejects_late_runtime():
    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=(
            "2026-07-11T00:00:00+00:00"
        ),
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "runtime_after_evaluation_end"
        in result.rejection_reasons
    )


def test_oos_deterministic():
    result_1 = (
        run_market_regime_oos_runtime_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    result_2 = (
        run_market_regime_oos_runtime_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result_1 == result_2

    assert result_1.result_hash == (
        result_2.result_hash
    )

    assert (
        result_1.pipeline_result
        .pipeline_hash
        == result_2.pipeline_result
        .pipeline_hash
    )


def test_oos_input_order_independent():
    source = _valid_source()

    reversed_source = dict(source)

    reversed_source["records"] = tuple(
        reversed(source["records"])
    )

    result_1 = evaluate_market_regime_oos_runtime(
        source_result=source,
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    result_2 = evaluate_market_regime_oos_runtime(
        source_result=reversed_source,
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert (
        result_1.pipeline_result
        .discovery_result.result_hash
        == result_2.pipeline_result
        .discovery_result.result_hash
    )

    assert result_1.status == result_2.status

    assert (
        result_1.in_window_record_count
        == result_2.in_window_record_count
    )


def test_oos_metadata():
    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
        metadata={
            "environment": "unit_test",
            "build": "RGD-007",
        },
    )

    metadata = dict(result.metadata)

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-007"

    assert (
        metadata[
            "external_state_mutated"
        ]
        is False
    )

    assert (
        metadata[
            "training_data_consumed"
        ]
        is False
    )

    assert (
        metadata[
            "future_data_consumed"
        ]
        is False
    )

    assert metadata["read_only"] is True


def test_oos_validation():
    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_oos_runtime_gate(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_oos_read_only():
    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_oos_runtime_read_only(
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
            "OOS result must be immutable"
        )

    check = result.checks[0]

    assert isinstance(
        check,
        MarketRegimeOOSCheck,
    )

    try:
        check.accepted = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "OOS check must be immutable"
        )


def test_oos_as_dict():
    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-007"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "accepted"
    assert payload["accepted"] is True

    assert (
        payload["in_window_record_count"]
        == 4
    )

    assert (
        payload[
            "invalid_timestamp_record_count"
        ]
        == 0
    )

    assert payload["result_hash"] == (
        result.result_hash
    )


def test_oos_requires_source_and_window():
    try:
        evaluate_market_regime_oos_runtime(
            source_result=None,
            window=_window(),
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

    try:
        evaluate_market_regime_oos_runtime(
            source_result=_valid_source(),
            window={
                "training_end": TRAINING_END,
            },
            observed_at=OBSERVED_AT,
        )
    except TypeError as exc:
        assert str(exc) == (
            "window must be a "
            "MarketRegimeOOSWindow"
        )
    else:
        raise AssertionError(
            "expected window type requirement"
        )


if __name__ == "__main__":
    test_oos_constants()
    test_oos_window_validation()
    test_oos_accepts_valid_runtime()
    test_oos_accepts_empty_runtime()
    test_oos_rejects_training_leakage()
    test_oos_rejects_future_leakage()
    test_oos_rejects_invalid_timestamp()
    test_oos_rejects_late_runtime()
    test_oos_deterministic()
    test_oos_input_order_independent()
    test_oos_metadata()
    test_oos_validation()
    test_oos_read_only()
    test_oos_as_dict()
    test_oos_requires_source_and_window()

    result = evaluate_market_regime_oos_runtime(
        source_result=_valid_source(),
        window=_window(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-007 "
        "Market Regime OOS Runtime Gate"
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
            "in_window_records": (
                result.in_window_record_count
            ),
            "invalid_timestamps": (
                result.invalid_timestamp_record_count
            ),
            "pipeline_status": (
                result.pipeline_result.status
            ),
            "checks": len(result.checks),
            "read_only": result.read_only,
        }
    )
