
from dataclasses import FrozenInstanceError

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_oos_runtime_gate import (
    MarketRegimeOOSWindow,
)

from qseries_v2.oracle_intelligence.market_regime_discovery_model.market_regime_replay_ledger import (
    ENGINE_ID,
    READ_ONLY,
    SCHEMA_VERSION,
    MarketRegimeReplayEntry,
    MarketRegimeReplayLedgerResult,
    assert_market_regime_replay_ledger_read_only,
    build_market_regime_replay_entry,
    build_market_regime_replay_ledger,
    replay_market_regime_entry,
    validate_market_regime_replay_ledger,
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


def _second_source():
    source = _valid_source()

    source["records"] = tuple(
        {
            **record,
            "signal_id": (
                f"{record['signal_id']}-second"
            ),
            "source_hash": (
                f"{record['source_hash']}-second"
            ),
            "value": (
                float(record["value"]) * 0.95
            ),
        }
        for record in source["records"]
    )

    return source


def _rejected_source():
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

    return source


def test_replay_ledger_constants():
    assert SCHEMA_VERSION == "RGD-008"

    assert ENGINE_ID == (
        "oracle.discovery.market_regime."
        "replay_ledger"
    )

    assert READ_ONLY is True


def test_replay_ledger_records_single_run():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert isinstance(
        result,
        MarketRegimeReplayLedgerResult,
    )

    assert result.schema_version == "RGD-008"
    assert result.engine_id == ENGINE_ID
    assert result.status == "recorded"
    assert result.accepted is True
    assert result.entry_count == 1
    assert len(result.entries) == 1
    assert result.head_hash == (
        result.entries[0].entry_hash
    )
    assert result.rejection_reasons == tuple()
    assert result.verify_ledger_hash() is True
    assert result.verify_chain() is True
    assert result.read_only is True

    entry = result.entries[0]

    assert isinstance(
        entry,
        MarketRegimeReplayEntry,
    )

    assert entry.sequence == 1
    assert entry.previous_entry_hash == ""
    assert entry.status == "accepted"
    assert entry.accepted is True
    assert entry.source_record_count == 4
    assert entry.in_window_record_count == 4
    assert entry.opportunity_count == 1
    assert entry.pipeline_status == "completed"
    assert entry.verify_entry_hash() is True


def test_replay_ledger_records_chain():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
            (
                _second_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert result.status == "recorded"
    assert result.accepted is True
    assert result.entry_count == 2

    first = result.entries[0]
    second = result.entries[1]

    assert first.sequence == 1
    assert second.sequence == 2

    assert (
        second.previous_entry_hash
        == first.entry_hash
    )

    assert result.head_hash == (
        second.entry_hash
    )

    assert result.verify_chain() is True


def test_replay_ledger_empty():
    result = build_market_regime_replay_ledger(
        replay_runs=tuple(),
    )

    assert result.status == "empty"
    assert result.accepted is True
    assert result.entry_count == 0
    assert result.entries == tuple()
    assert result.head_hash == ""
    assert result.rejection_reasons == tuple()
    assert result.verify_ledger_hash() is True
    assert result.verify_chain() is True


def test_replay_ledger_rejected_runtime():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _rejected_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert result.status == "rejected"
    assert result.accepted is False
    assert result.entry_count == 1

    assert (
        "runtime_rejected"
        in result.rejection_reasons
    )

    assert result.entries[0].accepted is False
    assert result.verify_chain() is True


def test_replay_entry_reproduces():
    ledger = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    replay = replay_market_regime_entry(
        entry=ledger.entries[0],
        source_result=_valid_source(),
        window=_window(),
    )

    assert replay["accepted"] is True

    assert all(
        replay["checks"].values()
    )

    assert (
        replay["runtime_result"].result_hash
        == ledger.entries[0].runtime_hash
    )


def test_replay_entry_detects_source_change():
    ledger = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    replay = replay_market_regime_entry(
        entry=ledger.entries[0],
        source_result=_second_source(),
        window=_window(),
    )

    assert replay["accepted"] is False

    assert (
        replay["checks"][
            "source_hash_match"
        ]
        is False
    )


def test_replay_ledger_deterministic():
    runs = (
        (
            _valid_source(),
            _window(),
            OBSERVED_AT,
        ),
        (
            _second_source(),
            _window(),
            OBSERVED_AT,
        ),
    )

    result_1 = (
        build_market_regime_replay_ledger(
            replay_runs=runs,
        )
    )

    result_2 = (
        build_market_regime_replay_ledger(
            replay_runs=runs,
        )
    )

    assert result_1 == result_2

    assert result_1.ledger_hash == (
        result_2.ledger_hash
    )

    assert result_1.head_hash == (
        result_2.head_hash
    )

    assert (
        result_1.entries[0].entry_hash
        == result_2.entries[0].entry_hash
    )


def test_replay_ledger_metadata():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
        metadata={
            "environment": "unit_test",
            "build": "RGD-008",
        },
    )

    metadata = dict(result.metadata)

    assert metadata["environment"] == (
        "unit_test"
    )

    assert metadata["build"] == "RGD-008"

    assert (
        metadata[
            "external_state_mutated"
        ]
        is False
    )

    assert (
        metadata[
            "persistent_write_performed"
        ]
        is False
    )

    assert metadata["read_only"] is True


def test_replay_ledger_validation():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    validation = (
        validate_market_regime_replay_ledger(
            result
        )
    )

    assert validation["accepted"] is True

    assert all(
        validation["checks"].values()
    )


def test_replay_ledger_read_only():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    assert (
        assert_market_regime_replay_ledger_read_only(
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
            "replay ledger must be immutable"
        )

    entry = result.entries[0]

    try:
        entry.status = "rejected"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError(
            "replay entry must be immutable"
        )


def test_replay_ledger_as_dict():
    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    payload = result.as_dict()

    assert payload["schema_version"] == (
        "RGD-008"
    )

    assert payload["engine_id"] == ENGINE_ID
    assert payload["status"] == "recorded"
    assert payload["accepted"] is True
    assert payload["entry_count"] == 1

    assert payload["ledger_hash"] == (
        result.ledger_hash
    )

    assert (
        payload["entries"][0]["entry_hash"]
        == result.entries[0].entry_hash
    )


def test_replay_ledger_requires_valid_run_tuple():
    try:
        build_market_regime_replay_ledger(
            replay_runs=(
                (_valid_source(),),
            ),
        )
    except TypeError as exc:
        assert str(exc) == (
            "each replay run must be a "
            "(source_result, window, "
            "observed_at) tuple"
        )
    else:
        raise AssertionError(
            "expected replay tuple validation"
        )


if __name__ == "__main__":
    test_replay_ledger_constants()
    test_replay_ledger_records_single_run()
    test_replay_ledger_records_chain()
    test_replay_ledger_empty()
    test_replay_ledger_rejected_runtime()
    test_replay_entry_reproduces()
    test_replay_entry_detects_source_change()
    test_replay_ledger_deterministic()
    test_replay_ledger_metadata()
    test_replay_ledger_validation()
    test_replay_ledger_read_only()
    test_replay_ledger_as_dict()
    test_replay_ledger_requires_valid_run_tuple()

    result = build_market_regime_replay_ledger(
        replay_runs=(
            (
                _valid_source(),
                _window(),
                OBSERVED_AT,
            ),
            (
                _second_source(),
                _window(),
                OBSERVED_AT,
            ),
        ),
    )

    print(
        "[PASS] RGD-008 "
        "Market Regime Replay Ledger"
    )

    print(
        {
            "schema_version": (
                result.schema_version
            ),
            "engine_id": result.engine_id,
            "status": result.status,
            "accepted": result.accepted,
            "entries": result.entry_count,
            "chain_valid": (
                result.verify_chain()
            ),
            "head_hash": (
                result.head_hash[:16]
                if result.head_hash
                else ""
            ),
            "read_only": result.read_only,
        }
    )
