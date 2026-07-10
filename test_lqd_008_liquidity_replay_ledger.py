
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_oos_runtime_gate import (
    run_liquidity_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.liquidity_discovery_model.liquidity_replay_ledger import (
    LiquidityReplayLedgerBuilder,
    build_liquidity_replay_ledger,
    run_liquidity_replay_ledger,
)


RAW = [
    {
        "market_id": "KXTHIN",
        "venue": "kalshi",
        "asset": "binary_event",
        "bid_price": 0.40,
        "ask_price": 0.48,
        "bid_depth": 100,
        "ask_depth": 50,
        "volume_24h": 12000,
        "open_interest": 50000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_liquidity_replay_ledger_builds_valid_ledger():
    result = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "A"},
    )

    builder = LiquidityReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "LQD-008"
    assert ledger.engine_id == "oracle.discovery.liquidity.replay_ledger"
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash
    assert ledger.entries[0].entry_hash
    assert ledger.entries[0].oos_hash == result.oos_hash
    assert ledger.entries[0].pipeline_hash == result.pipeline_hash


def test_liquidity_replay_ledger_replays_exactly():
    result = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )

    builder = LiquidityReplayLedgerBuilder()
    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert replayed.ledger_hash == ledger.ledger_hash
    assert validation["accepted"] is True
    assert validation["checks"]["replay_hash_matches"] is True


def test_liquidity_replay_ledger_handles_rejected_entry():
    rejected = run_liquidity_oos_runtime_gate(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    ledger = build_liquidity_replay_ledger([rejected])

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert ledger.read_only is True


def test_liquidity_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_liquidity_replay_ledger(
        RAW,
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )
    ledger2 = run_liquidity_replay_ledger(
        list(reversed(RAW)),
        source_name="liquidity.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    assert ledger1.ledger_hash == ledger2.ledger_hash


def test_liquidity_replay_ledger_empty():
    ledger = build_liquidity_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash


if __name__ == "__main__":
    test_liquidity_replay_ledger_builds_valid_ledger()
    test_liquidity_replay_ledger_replays_exactly()
    test_liquidity_replay_ledger_handles_rejected_entry()
    test_liquidity_replay_ledger_is_order_independent_for_pipeline_input()
    test_liquidity_replay_ledger_empty()

    ledger = run_liquidity_replay_ledger(
        [],
        source_name="liquidity.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] LQD-008 Liquidity Replay Ledger")
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
