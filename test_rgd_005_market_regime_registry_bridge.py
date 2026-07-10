
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_pipeline_gate import (
    evaluate_market_regime_pipeline,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_registry_bridge import (
    ENGINE_ID,
    READ_ONLY,
    REGISTRY_ENTRY_ID,
    REGISTRY_NAMESPACE,
    SCHEMA_VERSION,
    MarketRegimeRegistryBridgeResult,
    MarketRegimeRegistryDescriptor,
    assert_market_regime_registry_read_only,
    bridge_market_regime_to_registry,
    build_market_regime_registry_descriptor,
    run_market_regime_registry_bridge,
    validate_market_regime_registry_bridge,
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


def _invalid_source():
    source = dict(
        _valid_source()
    )

    source["schema_version"] = "BAD-001"

    return source


def _valid_gate():
    return evaluate_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )


def _empty_gate():
    return evaluate_market_regime_pipeline(
        source_result=_empty_source(),
        observed_at=OBSERVED_AT,
    )


def _rejected_gate():
    return evaluate_market_regime_pipeline(
        source_result=_invalid_source(),
        observed_at=OBSERVED_AT,
    )


def test_registry_bridge_constants():
    assert SCHEMA_VERSION == "RGD-005"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "registry_bridge"
    )

    assert REGISTRY_NAMESPACE == (
        "oracle.discovery.market_regime"
    )

    assert REGISTRY_ENTRY_ID == (
        "oracle.discovery.market_regime."
        "subsystem"
    )

    assert READ_ONLY is True


def test_registry_descriptor():
    descriptor = (
        build_market_regime_registry_descriptor()
    )

    assert isinstance(
        descriptor,
        MarketRegimeRegistryDescriptor,
    )

    assert descriptor.registry_entry_id == (
        REGISTRY_ENTRY_ID
    )

    assert descriptor.namespace == (
        REGISTRY_NAMESPACE
    )

    assert descriptor.subsystem_name == (
        "Market Regime Discovery"
    )

    assert descriptor.contract_schema_version == (
        "RGD-001"
    )

    assert (
        descriptor
        .source_adapter_schema_version
        == "RGD-002"
    )

    assert (
        descriptor
        .discovery_engine_schema_version
        == "RGD-003"
    )

    assert (
        descriptor
        .pipeline_gate_schema_version
        == "RGD-004"
    )

    assert (
        descriptor
        .registry_bridge_schema_version
        == "RGD-005"
    )

    assert descriptor.read_only is True
    assert descriptor.deterministic is True
    assert descriptor.replayable is True
    assert descriptor.explainable is True
    assert descriptor.auditable is True

    assert (
        descriptor.verify_descriptor_hash()
        is True
    )


def test_registry_bridge_registers_valid_gate():
    gate = _valid_gate()

    result = bridge_market_regime_to_registry(
        pipeline_gate_result=gate,
        observed_at=OBSERVED_AT,
    )

    assert isinstance(
        result,
        MarketRegimeRegistryBridgeResult,
    )

    assert result.schema_version == "RGD-005"
    assert result.engine_id == ENGINE_ID
    assert result.status == "registered"
    assert result.accepted is True

    assert result.registry_namespace == (
        REGISTRY_NAMESPACE
    )

    assert result.registration_count == 1

    assert len(result.registrations) == 1

    assert (
        result.registrations[0]
        .registry_entry_id
        == REGISTRY_ENTRY_ID
    )

    assert result.pipeline_gate_status == (
        "accepted"
    )

    assert result.pipeline_gate_hash == (
        gate.gate_hash
    )

    assert result.rejection_reasons == tuple()
    assert result.read_only is True
    assert result.verify_result_hash() is True


def test_registry_bridge_accepts_empty_gate():
    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_empty_gate(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.registration_count == 1
    assert len(result.registrations) == 1
    assert result.pipeline_gate_status == "empty"
    assert result.rejection_reasons == tuple()
    assert result.verify_result_hash() is True


def test_registry_bridge_rejects_rejected_gate():
    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_rejected_gate(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.registration_count == 0
    assert result.registrations == tuple()

    assert (
        "pipeline_gate_rejected"
        in result.rejection_reasons
    )

    assert result.verify_result_hash() is True


def test_registry_bridge_metadata():
    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_valid_gate(),
        observed_at=OBSERVED_AT,
        metadata={
            "environment": "unit_test",
            "build": "RGD-005",
        },
    )

    metadata = dict(
        result.metadata
    )

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-005"

    assert (
        metadata[
            "external_state_mutated"
        ]
        is False
    )

    assert (
        metadata[
            "registry_write_performed"
        ]
        is False
    )

    assert metadata["read_only"] is True


def test_registry_bridge_deterministic():
    gate = _valid_gate()

    result_1 = (
        run_market_regime_registry_bridge(
            pipeline_gate_result=gate,
            observed_at=OBSERVED_AT,
        )
    )

    result_2 = (
        run_market_regime_registry_bridge(
            pipeline_gate_result=gate,
            observed_at=OBSERVED_AT,
        )
    )

    assert result_1 == result_2

    assert result_1.result_hash == (
        result_2.result_hash
    )

    assert (
        result_1.registrations[0]
        .descriptor_hash
        == result_2.registrations[0]
        .descriptor_hash
    )


def test_registry_bridge_validation():
    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_valid_gate(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_registry_bridge(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_registry_bridge_is_read_only():
    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_valid_gate(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_registry_read_only(
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
            "registry result must be "
            "immutable"
        )

    descriptor = result.registrations[0]

    try:
        descriptor.subsystem_name = "mutated"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "registry descriptor must be "
            "immutable"
        )


def test_registry_bridge_as_dict():
    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_valid_gate(),
        observed_at=OBSERVED_AT,
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-005"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "registered"
    assert payload["accepted"] is True

    assert payload["registration_count"] == 1

    assert payload["result_hash"] == (
        result.result_hash
    )

    assert (
        payload["registrations"][0]
        ["descriptor_hash"]
        == result.registrations[0]
        .descriptor_hash
    )


def test_registry_bridge_requires_gate_type():
    try:
        bridge_market_regime_to_registry(
            pipeline_gate_result={
                "status": "accepted",
            },
            observed_at=OBSERVED_AT,
        )
    except TypeError as exc:
        assert str(exc) == (
            "pipeline_gate_result must be a "
            "MarketRegimePipelineGateResult"
        )
    else:
        raise AssertionError(
            "expected pipeline gate type "
            "requirement"
        )


def test_registry_bridge_observed_at_default():
    gate = _valid_gate()

    result = bridge_market_regime_to_registry(
        pipeline_gate_result=gate,
    )

    assert result.observed_at == (
        gate.observed_at
    )


if __name__ == "__main__":
    test_registry_bridge_constants()
    test_registry_descriptor()
    test_registry_bridge_registers_valid_gate()
    test_registry_bridge_accepts_empty_gate()
    test_registry_bridge_rejects_rejected_gate()
    test_registry_bridge_metadata()
    test_registry_bridge_deterministic()
    test_registry_bridge_validation()
    test_registry_bridge_is_read_only()
    test_registry_bridge_as_dict()
    test_registry_bridge_requires_gate_type()
    test_registry_bridge_observed_at_default()

    result = bridge_market_regime_to_registry(
        pipeline_gate_result=_valid_gate(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-005 "
        "Market Regime Registry Bridge"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "registrations": (
                result.registration_count
            ),
            "namespace": (
                result.registry_namespace
            ),
            "gate_status": (
                result.pipeline_gate_status
            ),
            "read_only": result.read_only,
        }
    )
