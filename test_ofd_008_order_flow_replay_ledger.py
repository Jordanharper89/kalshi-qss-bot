
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_oos_runtime_gate import (
    run_order_flow_oos_runtime_gate,
)
from qseries_v2.oracle_intelligence.order_flow_discovery_model.order_flow_replay_ledger import (
    OrderFlowReplayLedgerBuilder,
    build_order_flow_replay_ledger,
    run_order_flow_replay_ledger,
)


RAW = [
    {
        "market_id": "KXTEST-YES",
        "venue": "kalshi",
        "instrument": "binary_event",
        "bid_size": 85,
        "ask_size": 15,
        "bid_price": 0.42,
        "ask_price": 0.45,
        "last_price": 0.43,
        "volume": 2500,
        "open_interest": 7000,
        "observed_at": "2026-07-09T00:00:00+00:00",
    }
]


def test_order_flow_replay_ledger_builds_valid_ledger():
    result = run_order_flow_oos_runtime_gate(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "fold": "A"},
    )

    builder = OrderFlowReplayLedgerBuilder()
    assert builder.assert_read_only() is True

    ledger = builder.build([result])

    assert ledger.schema_version == "OFD-008"
    assert ledger.engine_id == "oracle.discovery.order_flow.replay_ledger"
    assert ledger.status == "accepted"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 1
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash
    assert ledger.entries[0].entry_hash
    assert ledger.entries[0].oos_hash == result.oos_hash
    assert ledger.entries[0].pipeline_hash == result.pipeline_hash


def test_order_flow_replay_ledger_replays_exactly():
    result = run_order_flow_oos_runtime_gate(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "replay", "fold": "A"},
    )

    builder = OrderFlowReplayLedgerBuilder()
    ledger = builder.build([result])
    replayed = builder.replay(ledger)
    validation = builder.validate(ledger)

    assert replayed.ledger_hash == ledger.ledger_hash
    assert validation["accepted"] is True
    assert validation["checks"]["replay_hash_matches"] is True


def test_order_flow_replay_ledger_handles_rejected_entry():
    rejected = run_order_flow_oos_runtime_gate(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos", "execute": True},
    )

    ledger = build_order_flow_replay_ledger([rejected])

    assert ledger.status == "rejected"
    assert ledger.entry_count == 1
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 1
    assert ledger.entries[0].accepted is False
    assert ledger.read_only is True


def test_order_flow_replay_ledger_is_order_independent_for_pipeline_input():
    ledger1 = run_order_flow_replay_ledger(
        RAW,
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )
    ledger2 = run_order_flow_replay_ledger(
        list(reversed(RAW)),
        source_name="order_flow.test",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    assert ledger1.ledger_hash == ledger2.ledger_hash


def test_order_flow_replay_ledger_empty():
    ledger = build_order_flow_replay_ledger([])

    assert ledger.status == "empty"
    assert ledger.entry_count == 0
    assert ledger.accepted_count == 0
    assert ledger.rejected_count == 0
    assert ledger.read_only is True
    assert ledger.ledger_hash


if __name__ == "__main__":
    test_order_flow_replay_ledger_builds_valid_ledger()
    test_order_flow_replay_ledger_replays_exactly()
    test_order_flow_replay_ledger_handles_rejected_entry()
    test_order_flow_replay_ledger_is_order_independent_for_pipeline_input()
    test_order_flow_replay_ledger_empty()

    ledger = run_order_flow_replay_ledger(
        [],
        source_name="order_flow.empty",
        observed_at="2026-07-09T00:00:00+00:00",
        runtime_context={"mode": "oos"},
    )

    print("[PASS] OFD-008 Order Flow Replay Ledger")
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
