
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_oos_runtime_gate import (
    run_correlation_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.correlation_discovery_model.correlation_replay_ledger import (
    CorrelationReplayLedgerBuilder,
    build_correlation_replay_ledger,
    run_correlation_replay_ledger,
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


def _accepted_result():
    return run_correlation_oos_runtime_gate(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
            "fold": "A",
        },
    )


def _rejected_result():
    return run_correlation_oos_runtime_gate(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
            "execute": True,
        },
    )


def test_correlation_replay_ledger_builds_valid_ledger():
    result = _accepted_result()

    builder = CorrelationReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "CRD-008"
    assert (
        ledger.engine_id
        == (
            "oracle.discovery.correlation."
            "replay_ledger"
        )
    )
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash

    entry = ledger.entries[0]

    assert entry.sequence == 0
    assert entry.accepted is True
    assert entry.status == "accepted"
    assert entry.entry_hash
    assert entry.oos_hash == result.oos_hash
    assert (
        entry.pipeline_hash
        == result.pipeline_hash
    )
    assert (
        entry.opportunity_count
        == result.opportunity_count
    )
    assert entry.read_only is True


def test_correlation_replay_ledger_replays_exactly():
    result = _accepted_result()
    builder = CorrelationReplayLedgerBuilder()

    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert (
        replayed.ledger_hash
        == ledger.ledger_hash
    )
    assert (
        replayed.entries[0].entry_hash
        == ledger.entries[0].entry_hash
    )
    assert validation["accepted"] is True
    assert (
        validation["checks"][
            "replay_hash_matches"
        ]
        is True
    )


def test_correlation_replay_ledger_handles_rejected_entry():
    rejected = _rejected_result()

    ledger = build_correlation_replay_ledger(
        [rejected]
    )

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert (
        ledger.entries[0].status
        == "rejected"
    )
    assert ledger.read_only is True
    assert ledger.ledger_hash


def test_correlation_replay_ledger_handles_mixed_entries():
    accepted = _accepted_result()
    rejected = _rejected_result()

    builder = CorrelationReplayLedgerBuilder()
    ledger = builder.build(
        [accepted, rejected]
    )

    assert ledger.status == "mixed"
    assert ledger.entry_count == 2
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 1
    assert [
        entry.sequence
        for entry in ledger.entries
    ] == [0, 1]

    validation = builder.validate(ledger)
    assert validation["accepted"] is True


def test_correlation_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_correlation_replay_ledger(
        RAW,
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "replay",
            "fold": "A",
        },
    )

    ledger2 = run_correlation_replay_ledger(
        list(reversed(RAW)),
        source_name="correlation.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "fold": "A",
            "mode": "replay",
        },
    )

    assert (
        ledger1.ledger_hash
        == ledger2.ledger_hash
    )
    assert (
        ledger1.entries[0].entry_hash
        == ledger2.entries[0].entry_hash
    )


def test_correlation_replay_ledger_empty():
    ledger = build_correlation_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.entries == tuple()
    assert ledger.read_only is True
    assert ledger.ledger_hash

    validation = (
        CorrelationReplayLedgerBuilder()
        .validate(ledger)
    )
    assert validation["accepted"] is True


def test_correlation_replay_ledger_rejects_invalid_inputs():
    builder = CorrelationReplayLedgerBuilder()

    try:
        builder.entry_from_oos_result(
            {"accepted": True}
        )
    except TypeError as exc:
        assert str(exc) == (
            "result must be a "
            "CorrelationOOSRuntimeGateResult"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid result"
        )

    try:
        builder.entry_from_oos_result(
            _accepted_result(),
            sequence=-1,
        )
    except ValueError as exc:
        assert str(exc) == (
            "sequence must be non-negative"
        )
    else:
        raise AssertionError(
            "expected ValueError for negative sequence"
        )

    try:
        builder.replay({"entries": []})
    except TypeError as exc:
        assert str(exc) == (
            "ledger must be a "
            "CorrelationReplayLedger"
        )
    else:
        raise AssertionError(
            "expected TypeError for invalid ledger"
        )


if __name__ == "__main__":
    test_correlation_replay_ledger_builds_valid_ledger()
    test_correlation_replay_ledger_replays_exactly()
    test_correlation_replay_ledger_handles_rejected_entry()
    test_correlation_replay_ledger_handles_mixed_entries()
    test_correlation_replay_ledger_is_order_independent_for_pipeline_input()
    test_correlation_replay_ledger_empty()
    test_correlation_replay_ledger_rejects_invalid_inputs()

    ledger = run_correlation_replay_ledger(
        [],
        source_name="correlation.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={
            "mode": "oos",
        },
    )

    print(
        "[PASS] CRD-008 "
        "Correlation Replay Ledger"
    )
    print(
        {
            "schema_version": ledger.schema_version,
            "engine_id": ledger.engine_id,
            "status": ledger.status,
            "entries": ledger.entry_count,
            "accepted": ledger.accepted_count,
            "rejected": ledger.rejected_count,
            "read_only": ledger.read_only,
        }
    )
