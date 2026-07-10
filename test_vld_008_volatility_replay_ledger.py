
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_oos_runtime_gate import (
    run_volatility_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.volatility_discovery_model.volatility_replay_ledger import (
    VolatilityReplayLedgerBuilder,
    build_volatility_replay_ledger,
    run_volatility_replay_ledger,
)


RAW = [
    {
        "market_id": "KXVOL-EXPAND",
        "venue": "kalshi",
        "asset": "binary_event",
        "realized_volatility": 0.42,
        "implied_volatility": 0.20,
        "baseline_volatility": 0.20,
        "price_change": 0.08,
        "volume": 12000,
        "window": "1d",
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_volatility_replay_ledger_builds_valid_ledger():
    result = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "A"},
    )

    builder = VolatilityReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "VLD-008"
    assert ledger.engine_id == "oracle.discovery.volatility.replay_ledger"
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash
    assert ledger.entries[0].entry_hash
    assert ledger.entries[0].oos_hash == result.oos_hash
    assert ledger.entries[0].pipeline_hash == result.pipeline_hash


def test_volatility_replay_ledger_replays_exactly():
    result = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )

    builder = VolatilityReplayLedgerBuilder()
    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert replayed.ledger_hash == ledger.ledger_hash
    assert validation["accepted"] is True
    assert validation["checks"]["replay_hash_matches"] is True


def test_volatility_replay_ledger_handles_rejected_entry():
    rejected = run_volatility_oos_runtime_gate(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    ledger = build_volatility_replay_ledger([rejected])

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert ledger.read_only is True


def test_volatility_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_volatility_replay_ledger(
        RAW,
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )
    ledger2 = run_volatility_replay_ledger(
        list(reversed(RAW)),
        source_name="volatility.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    assert ledger1.ledger_hash == ledger2.ledger_hash


def test_volatility_replay_ledger_empty():
    ledger = build_volatility_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash


if __name__ == "__main__":
    test_volatility_replay_ledger_builds_valid_ledger()
    test_volatility_replay_ledger_replays_exactly()
    test_volatility_replay_ledger_handles_rejected_entry()
    test_volatility_replay_ledger_is_order_independent_for_pipeline_input()
    test_volatility_replay_ledger_empty()

    ledger = run_volatility_replay_ledger(
        [],
        source_name="volatility.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] VLD-008 Volatility Replay Ledger")
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
