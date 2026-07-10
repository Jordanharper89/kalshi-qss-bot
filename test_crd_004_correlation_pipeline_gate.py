
from dataclasses import replace

from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_discovery_engine import (
    discover_correlation_opportunities,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_pipeline_gate import (
    CorrelationPipelineGate,
    validate_correlation_discovery_result,
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
        "observed_at": "2026-07-09T00:00:00+00:00",
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
        "observed_at": "2026-07-09T00:00:00+00:00",
    },
]


def _build_result():
    return discover_correlation_opportunities(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
    )


def test_correlation_pipeline_gate_accepts_valid_result():
    result = _build_result()

    gate = CorrelationPipelineGate()
    assert gate.assert_read_only() is True

    gated = gate.validate(result)

    assert gated.schema_version == "CRD-004"
    assert (
        gated.engine_id
        == "oracle.discovery.correlation.pipeline_gate"
    )
    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.read_only is True
    assert (
        gated.discovery_result_hash
        == result.result_hash
    )
    assert (
        gated.opportunity_count
        == result.opportunity_count
    )
    assert gated.gate_hash
    assert all(gated.checks.values())


def test_correlation_pipeline_gate_accepts_empty_result():
    result = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )

    gated = validate_correlation_discovery_result(result)

    assert gated.status == "accepted"
    assert gated.accepted is True
    assert gated.opportunity_count == 0
    assert gated.read_only is True
    assert all(gated.checks.values())


def test_correlation_pipeline_gate_rejects_missing_hash():
    result = _build_result()
    invalid = replace(result, result_hash="")

    gated = validate_correlation_discovery_result(invalid)

    assert gated.status == "rejected"
    assert gated.accepted is False
    assert gated.checks["hash_present"] is False
    assert gated.read_only is True
    assert gated.gate_hash


def test_correlation_pipeline_gate_rejects_inconsistent_status():
    result = _build_result()
    invalid = replace(result, status="empty")

    gated = validate_correlation_discovery_result(invalid)

    assert gated.status == "rejected"
    assert gated.accepted is False
    assert (
        gated.checks["empty_status_consistent"]
        is False
    )


def test_correlation_pipeline_gate_is_replayable():
    result = _build_result()

    gated1 = validate_correlation_discovery_result(
        result
    )
    gated2 = validate_correlation_discovery_result(
        result
    )

    assert gated1.gate_hash == gated2.gate_hash
    assert gated1.checks == gated2.checks
    assert gated1.reason == gated2.reason


def test_correlation_pipeline_gate_rejects_wrong_type():
    gate = CorrelationPipelineGate()

    try:
        gate.validate({"status": "ok"})
    except TypeError as exc:
        assert (
            str(exc)
            == "result must be a CorrelationDiscoveryResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid result type"
        )


if __name__ == "__main__":
    test_correlation_pipeline_gate_accepts_valid_result()
    test_correlation_pipeline_gate_accepts_empty_result()
    test_correlation_pipeline_gate_rejects_missing_hash()
    test_correlation_pipeline_gate_rejects_inconsistent_status()
    test_correlation_pipeline_gate_is_replayable()
    test_correlation_pipeline_gate_rejects_wrong_type()

    result = discover_correlation_opportunities(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
    )
    gated = validate_correlation_discovery_result(
        result
    )

    print("[PASS] CRD-004 Correlation Pipeline Gate")
    print(
        {
            "schema_version": gated.schema_version,
            "engine_id": gated.engine_id,
            "status": gated.status,
            "accepted": gated.accepted,
            "opportunities": gated.opportunity_count,
            "read_only": gated.read_only,
        }
    )
