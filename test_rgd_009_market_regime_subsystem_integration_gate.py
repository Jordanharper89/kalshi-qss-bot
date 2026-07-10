
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_oos_runtime_gate import (
    MarketRegimeOOSWindow,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_subsystem_integration_gate import (
    ENGINE_ID,
    EXPECTED_MODULES,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimeIntegrationCheck,
    MarketRegimeSubsystemIntegrationResult,
    assert_market_regime_subsystem_read_only,
    run_market_regime_subsystem_integration_gate,
    validate_market_regime_subsystem_integration_gate,
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


def test_integration_constants():
    assert SCHEMA_VERSION == "RGD-009"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "subsystem_integration_gate"
    )

    assert EXPECTED_MODULES == (
        "RGD-001",
        "RGD-002",
        "RGD-003",
        "RGD-004",
        "RGD-005",
        "RGD-006",
        "RGD-007",
        "RGD-008",
        "RGD-009",
    )

    assert READ_ONLY is True


def test_integration_gate_passes():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert isinstance(
        result,
        MarketRegimeSubsystemIntegrationResult,
    )

    assert result.schema_version == "RGD-009"
    assert result.engine_id == ENGINE_ID
    assert result.status == "passed"
    assert result.accepted is True
    assert result.modules == EXPECTED_MODULES
    assert result.failed_check_count == 0
    assert result.passed_check_count == len(
        result.checks
    )
    assert result.rejection_reasons == tuple()
    assert result.discovery_hash
    assert result.gate_hash
    assert result.registry_hash
    assert result.pipeline_hash
    assert result.oos_hash
    assert result.replay_ledger_hash
    assert result.integration_hash
    assert result.verify_integration_hash() is True
    assert result.read_only is True

    assert all(
        check.accepted
        for check in result.checks
    )


def test_integration_gate_empty():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_empty_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.failed_check_count == 0
    assert result.rejection_reasons == tuple()
    assert result.verify_integration_hash() is True


def test_integration_gate_check_set():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    check_ids = {
        check.check_id
        for check in result.checks
    }

    assert check_ids == {
        "artifact_hash_chain",
        "discovery_contract",
        "oos_determinism",
        "oos_runtime_gate",
        "pipeline_bridge",
        "pipeline_determinism",
        "pipeline_gate",
        "registry_bridge",
        "replay_ledger",
        "replay_reproduction",
        "subsystem_read_only",
    }


def test_integration_gate_accepts_context_specific_pipeline_hashes():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result.status == "passed"
    assert result.accepted is True

    check_map = {
        check.check_id: check
        for check in result.checks
    }

    assert (
        check_map["artifact_hash_chain"]
        .accepted
        is True
    )


def test_integration_gate_deterministic():
    result_1 = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    result_2 = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result_1 == result_2

    assert (
        result_1.integration_hash
        == result_2.integration_hash
    )

    assert (
        result_1.pipeline_hash
        == result_2.pipeline_hash
    )

    assert (
        result_1.oos_hash
        == result_2.oos_hash
    )

    assert (
        result_1.replay_ledger_hash
        == result_2.replay_ledger_hash
    )


def test_integration_gate_input_order_independent():
    source = _valid_source()

    reversed_source = dict(source)

    reversed_source["records"] = tuple(
        reversed(
            source["records"]
        )
    )

    result_1 = (
        run_market_regime_subsystem_integration_gate(
            source_result=source,
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    result_2 = (
        run_market_regime_subsystem_integration_gate(
            source_result=reversed_source,
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result_1.status == result_2.status

    assert (
        result_1.discovery_hash
        == result_2.discovery_hash
    )

    assert (
        result_1.pipeline_hash
        == result_2.pipeline_hash
    )


def test_integration_gate_metadata():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
            metadata={
                "environment": "unit_test",
                "build": "RGD-009",
            },
        )
    )

    metadata = dict(
        result.metadata
    )

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-009"

    assert metadata["module_count"] == 9

    assert (
        metadata[
            "external_state_mutated"
        ]
        is False
    )

    assert (
        metadata[
            "order_placement_performed"
        ]
        is False
    )

    assert (
        metadata[
            "transaction_signed"
        ]
        is False
    )

    assert metadata["read_only"] is True


def test_integration_gate_validation():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    validation = (
        validate_market_regime_subsystem_integration_gate(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_integration_gate_read_only():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    assert (
        assert_market_regime_subsystem_read_only(
            result
        )
        is True
    )

    try:
        result.status = "failed"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "integration result must be "
            "immutable"
        )

    check = result.checks[0]

    assert isinstance(
        check,
        MarketRegimeIntegrationCheck,
    )

    try:
        check.accepted = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "integration check must be "
            "immutable"
        )


def test_integration_gate_as_dict():
    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-009"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "passed"
    assert payload["accepted"] is True
    assert payload["modules"] == (
        EXPECTED_MODULES
    )

    assert payload["integration_hash"] == (
        result.integration_hash
    )

    assert len(payload["checks"]) == len(
        result.checks
    )


def test_integration_gate_requires_inputs():
    try:
        run_market_regime_subsystem_integration_gate(
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
        run_market_regime_subsystem_integration_gate(
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
            "expected window requirement"
        )


if __name__ == "__main__":
    test_integration_constants()
    test_integration_gate_passes()
    test_integration_gate_empty()
    test_integration_gate_check_set()
    test_integration_gate_accepts_context_specific_pipeline_hashes()
    test_integration_gate_deterministic()
    test_integration_gate_input_order_independent()
    test_integration_gate_metadata()
    test_integration_gate_validation()
    test_integration_gate_read_only()
    test_integration_gate_as_dict()
    test_integration_gate_requires_inputs()

    result = (
        run_market_regime_subsystem_integration_gate(
            source_result=_valid_source(),
            window=_window(),
            observed_at=OBSERVED_AT,
        )
    )

    if result.accepted is not True:
        print(
            "[DIAGNOSTIC] Failed checks:",
            [
                check.check_id
                for check in result.checks
                if not check.accepted
            ],
        )

    print(
        "[PASS] RGD-009 "
        "Market Regime Subsystem "
        "Integration Gate"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "modules": len(
                result.modules
            ),
            "checks": len(
                result.checks
            ),
            "passed_checks": (
                result.passed_check_count
            ),
            "failed_checks": (
                result.failed_check_count
            ),
            "read_only": result.read_only,
        }
    )
