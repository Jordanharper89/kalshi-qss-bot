
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_oos_runtime_gate import (
    CorrelationOOSRuntimeGate,
    run_correlation_oos_runtime_gate,
    validate_correlation_oos_runtime,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_pipeline_bridge import (
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


def _build_pipeline():
    return run_correlation_pipeline(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )


def test_correlation_oos_runtime_gate_accepts_valid_pipeline():
    pipeline = _build_pipeline()

    gate = CorrelationOOSRuntimeGate()
    assert gate.assert_read_only() is True

    result = gate.validate(
        pipeline,
        runtime_context={
            "mode": "oos",
            "fold": "test-fold-001",
        },
    )

    assert result.schema_version == "CRD-007"
    assert (
        result.engine_id
        == (
            "oracle.discovery.correlation."
            "oos_runtime_gate"
        )
    )
    assert result.status == "accepted"
    assert result.accepted is True
    assert result.read_only is True
    assert (
        result.pipeline_hash
        == pipeline.pipeline_hash
    )
    assert (
        result.opportunity_count
        == pipeline.opportunity_count
    )
    assert result.checks["runtime_mode_valid"] is True
    assert (
        result.checks["no_execution_context"]
        is True
    )
    assert result.oos_hash


def test_correlation_oos_runtime_gate_rejects_execution_context():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "oos",
            "execute": True,
        },
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["no_execution_context"]
        is False
    )
    assert result.read_only is True
    assert result.oos_hash


def test_correlation_oos_runtime_gate_rejects_nested_execution_context():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "shadow",
            "request": {
                "submit_order": True,
            },
        },
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["no_execution_context"]
        is False
    )


def test_correlation_oos_runtime_gate_rejects_invalid_mode():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "live_execution",
        },
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["runtime_mode_valid"]
        is False
    )


def test_correlation_oos_runtime_gate_is_replayable():
    result1 = run_correlation_oos_runtime_gate(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "replay",
            "fold": "A",
        },
    )

    result2 = run_correlation_oos_runtime_gate(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "fold": "A",
            "mode": "replay",
        },
    )

    assert result1.oos_hash == result2.oos_hash
    assert result1.checks == result2.checks
    assert (
        result1.pipeline_hash
        == result2.pipeline_hash
    )


def test_correlation_oos_runtime_gate_accepts_empty_pipeline():
    result = run_correlation_oos_runtime_gate(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "shadow",
        },
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert result.oos_hash


def test_correlation_oos_runtime_gate_enforces_opportunity_limit():
    pipeline = _build_pipeline()

    result = validate_correlation_oos_runtime(
        pipeline,
        runtime_context={
            "mode": "oos",
        },
        max_opportunities=0,
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks[
            "opportunity_count_within_limit"
        ]
        is False
    )


def test_correlation_oos_runtime_gate_rejects_wrong_types():
    gate = CorrelationOOSRuntimeGate()

    try:
        gate.validate(
            {"status": "accepted"},
            runtime_context={"mode": "oos"},
        )
    except TypeError as exc:
        assert str(exc) == (
            "pipeline_result must be a "
            "CorrelationPipelineBridgeResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid pipeline type"
        )

    pipeline = _build_pipeline()

    try:
        gate.validate(
            pipeline,
            runtime_context=["oos"],
        )
    except TypeError as exc:
        assert str(exc) == (
            "runtime_context must be a mapping or None"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid context type"
        )


if __name__ == "__main__":
    test_correlation_oos_runtime_gate_accepts_valid_pipeline()
    test_correlation_oos_runtime_gate_rejects_execution_context()
    test_correlation_oos_runtime_gate_rejects_nested_execution_context()
    test_correlation_oos_runtime_gate_rejects_invalid_mode()
    test_correlation_oos_runtime_gate_is_replayable()
    test_correlation_oos_runtime_gate_accepts_empty_pipeline()
    test_correlation_oos_runtime_gate_enforces_opportunity_limit()
    test_correlation_oos_runtime_gate_rejects_wrong_types()

    result = run_correlation_oos_runtime_gate(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
        },
    )

    print(
        "[PASS] CRD-007 "
        "Correlation OOS Runtime Gate"
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
