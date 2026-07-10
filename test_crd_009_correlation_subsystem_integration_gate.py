
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_subsystem_integration_gate import (
    CorrelationSubsystemIntegrationGate,
    run_correlation_subsystem_integration_gate,
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


def test_correlation_subsystem_integration_gate_accepts_full_chain():
    gate = CorrelationSubsystemIntegrationGate()

    assert gate.assert_read_only() is True

    result = gate.run(
        RAW,
        source_name=(
            "correlation.integration.test"
        ),
        observed_at=(
            "2026-07-09T00:00:00+00:00"
        ),
        runtime_context={
            "mode": "oos",
            "fold": "integration",
        },
    )

    assert result.schema_version == "CRD-009"
    assert result.engine_id == (
        "oracle.discovery.correlation."
        "subsystem_integration_gate"
    )
    assert result.status == "accepted", (
        result.reason
    )
    assert result.accepted is True
    assert result.read_only is True
    assert result.opportunity_count >= 5
    assert result.integration_hash
    assert all(
        result.checks.values()
    ), result.checks

    assert (
        result.audit["subsystem"]
        == "correlation_discovery"
    )
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
    assert (
        result.audit[
            "ledger_validation"
        ]["accepted"]
        is True
    )


def test_correlation_subsystem_integration_gate_is_replayable_and_order_independent():
    result1 = (
        run_correlation_subsystem_integration_gate(
            RAW,
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "replay",
                "fold": "A",
            },
        )
    )

    result2 = (
        run_correlation_subsystem_integration_gate(
            list(reversed(RAW)),
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "fold": "A",
                "mode": "replay",
            },
        )
    )

    assert (
        result1.integration_hash
        == result2.integration_hash
    )
    assert (
        result1.discovery_result_hash
        == result2.discovery_result_hash
    )
    assert (
        result1.gate_hash
        == result2.gate_hash
    )
    assert (
        result1.registry_hash
        == result2.registry_hash
    )
    assert (
        result1.pipeline_hash
        == result2.pipeline_hash
    )
    assert (
        result1.oos_hash
        == result2.oos_hash
    )
    assert (
        result1.replay_ledger_hash
        == result2.replay_ledger_hash
    )


def test_correlation_subsystem_integration_gate_accepts_empty_chain():
    result = (
        run_correlation_subsystem_integration_gate(
            [],
            source_name=(
                "correlation.integration.empty"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "shadow",
                "fold": "empty",
            },
        )
    )

    assert result.status == "accepted", (
        result.reason
    )
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(
        result.checks.values()
    ), result.checks
    assert result.integration_hash


def test_correlation_subsystem_integration_gate_rejects_execution_context():
    result = (
        run_correlation_subsystem_integration_gate(
            RAW,
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "oos",
                "execute": True,
            },
        )
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert (
        result.checks["oos_accepted"]
        is False
    )
    assert result.read_only is True
    assert result.integration_hash


def test_correlation_subsystem_integration_gate_respects_sample_size():
    result = (
        run_correlation_subsystem_integration_gate(
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
            source_name=(
                "correlation.integration."
                "small_sample"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "oos",
            },
            min_sample_size=20,
        )
    )

    assert result.status == "accepted"
    assert result.accepted is True
    assert result.opportunity_count == 0
    assert result.read_only is True
    assert all(result.checks.values())


def test_correlation_subsystem_integration_gate_rejects_invalid_context_type():
    gate = CorrelationSubsystemIntegrationGate()

    try:
        gate.run(
            RAW,
            source_name=(
                "correlation.integration.test"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context=["oos"],
        )
    except TypeError as exc:
        assert str(exc) == (
            "runtime_context must be a "
            "mapping or None"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid "
            "runtime context"
        )


if __name__ == "__main__":
    test_correlation_subsystem_integration_gate_accepts_full_chain()
    test_correlation_subsystem_integration_gate_is_replayable_and_order_independent()
    test_correlation_subsystem_integration_gate_accepts_empty_chain()
    test_correlation_subsystem_integration_gate_rejects_execution_context()
    test_correlation_subsystem_integration_gate_respects_sample_size()
    test_correlation_subsystem_integration_gate_rejects_invalid_context_type()

    result = (
        run_correlation_subsystem_integration_gate(
            [],
            source_name=(
                "correlation.integration.empty"
            ),
            observed_at=(
                "2026-07-09T00:00:00+00:00"
            ),
            runtime_context={
                "mode": "oos",
                "fold": "integration",
            },
        )
    )

    print(
        "[PASS] CRD-009 "
        "Correlation Subsystem Integration Gate"
    )
    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "opportunities": (
                result.opportunity_count
            ),
            "read_only": result.read_only,
        }
    )
