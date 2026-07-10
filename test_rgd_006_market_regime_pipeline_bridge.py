
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_pipeline_bridge import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimePipelineBridgeResult,
    MarketRegimePipelineStage,
    assert_market_regime_pipeline_bridge_read_only,
    bridge_market_regime_pipeline,
    run_market_regime_pipeline,
    validate_market_regime_pipeline_bridge,
)


OBSERVED_AT = "2026-07-10T00:00:00+00:00"


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


def test_pipeline_bridge_constants():
    assert SCHEMA_VERSION == "RGD-006"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "pipeline_bridge"
    )

    assert READ_ONLY is True


def test_pipeline_bridge_completed():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert isinstance(
        result,
        MarketRegimePipelineBridgeResult,
    )

    assert result.schema_version == "RGD-006"
    assert result.engine_id == ENGINE_ID
    assert result.status == "completed"
    assert result.accepted is True
    assert result.source_record_count == 4
    assert result.opportunity_count == 1
    assert result.registration_count == 1
    assert result.rejection_reasons == tuple()
    assert len(result.stages) == 3
    assert result.read_only is True
    assert result.verify_pipeline_hash() is True

    assert [
        stage.stage_id
        for stage in result.stages
    ] == [
        "discovery",
        "pipeline_gate",
        "registry_bridge",
    ]

    assert all(
        stage.accepted
        for stage in result.stages
    )


def test_pipeline_bridge_empty():
    result = run_market_regime_pipeline(
        source_result=_empty_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.source_record_count == 0
    assert result.opportunity_count == 0
    assert result.registration_count == 1
    assert result.rejection_reasons == tuple()
    assert result.verify_pipeline_hash() is True


def test_pipeline_bridge_rejected():
    result = run_market_regime_pipeline(
        source_result=_invalid_source(),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "rejected"
    assert result.accepted is False

    assert (
        "invalid_source_schema_version"
        in result.rejection_reasons
    )

    assert (
        "pipeline_gate_rejected"
        in result.rejection_reasons
    )

    assert (
        "registry_bridge_rejected"
        in result.rejection_reasons
    )

    assert result.verify_pipeline_hash() is True


def test_pipeline_bridge_hash_chain():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    metadata = dict(
        result.metadata
    )

    discovery_stage = result.stages[0]
    gate_stage = result.stages[1]
    registry_stage = result.stages[2]

    assert discovery_stage.input_hash == (
        metadata["source_hash"]
    )

    assert gate_stage.input_hash == (
        discovery_stage.artifact_hash
    )

    assert registry_stage.input_hash == (
        gate_stage.artifact_hash
    )

    assert discovery_stage.artifact_hash == (
        result.discovery_result.result_hash
    )

    assert gate_stage.artifact_hash == (
        result.gate_result.gate_hash
    )

    assert registry_stage.artifact_hash == (
        result.registry_result.result_hash
    )


def test_pipeline_bridge_deterministic():
    result_1 = (
        bridge_market_regime_pipeline(
            source_result=_valid_source(),
            observed_at=OBSERVED_AT,
        )
    )

    result_2 = (
        bridge_market_regime_pipeline(
            source_result=_valid_source(),
            observed_at=OBSERVED_AT,
        )
    )

    assert result_1 == result_2

    assert result_1.pipeline_hash == (
        result_2.pipeline_hash
    )

    assert (
        result_1.discovery_result
        .result_hash
        == result_2.discovery_result
        .result_hash
    )

    assert (
        result_1.gate_result.gate_hash
        == result_2.gate_result.gate_hash
    )

    assert (
        result_1.registry_result
        .result_hash
        == result_2.registry_result
        .result_hash
    )


def test_pipeline_bridge_input_order_independent():
    source = _valid_source()

    reversed_source = dict(source)

    reversed_source["records"] = tuple(
        reversed(
            source["records"]
        )
    )

    result_1 = run_market_regime_pipeline(
        source_result=source,
        observed_at=OBSERVED_AT,
    )

    result_2 = run_market_regime_pipeline(
        source_result=reversed_source,
        observed_at=OBSERVED_AT,
    )

    assert (
        result_1.discovery_result
        .result_hash
        == result_2.discovery_result
        .result_hash
    )

    assert result_1.opportunity_count == (
        result_2.opportunity_count
    )

    assert result_1.status == result_2.status

    assert (
        result_1.pipeline_hash
        == result_2.pipeline_hash
    )


def test_pipeline_bridge_metadata():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
        metadata={
            "environment": "unit_test",
            "build": "RGD-006",
        },
    )

    metadata = dict(
        result.metadata
    )

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-006"

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


def test_pipeline_bridge_validation():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    validation = (
        validate_market_regime_pipeline_bridge(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_pipeline_bridge_read_only():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    assert (
        assert_market_regime_pipeline_bridge_read_only(
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
            "pipeline result must be "
            "immutable"
        )

    stage = result.stages[0]

    assert isinstance(
        stage,
        MarketRegimePipelineStage,
    )

    try:
        stage.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "pipeline stage must be "
            "immutable"
        )


def test_pipeline_bridge_as_dict():
    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-006"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "completed"
    assert payload["accepted"] is True

    assert payload["opportunity_count"] == 1
    assert payload["registration_count"] == 1

    assert payload["pipeline_hash"] == (
        result.pipeline_hash
    )

    assert len(payload["stages"]) == 3


def test_pipeline_bridge_requires_source():
    try:
        run_market_regime_pipeline(
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
    test_pipeline_bridge_constants()
    test_pipeline_bridge_completed()
    test_pipeline_bridge_empty()
    test_pipeline_bridge_rejected()
    test_pipeline_bridge_hash_chain()
    test_pipeline_bridge_deterministic()
    test_pipeline_bridge_input_order_independent()
    test_pipeline_bridge_metadata()
    test_pipeline_bridge_validation()
    test_pipeline_bridge_read_only()
    test_pipeline_bridge_as_dict()
    test_pipeline_bridge_requires_source()

    result = run_market_regime_pipeline(
        source_result=_valid_source(),
        observed_at=OBSERVED_AT,
    )

    print(
        "[PASS] RGD-006 "
        "Market Regime Pipeline Bridge"
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
            "registrations": (
                result.registration_count
            ),
            "stages": len(
                result.stages
            ),
            "read_only": result.read_only,
        }
    )
