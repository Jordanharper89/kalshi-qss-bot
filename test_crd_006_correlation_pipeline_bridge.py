
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
