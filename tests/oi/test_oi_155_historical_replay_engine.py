from qseries_v2.oracle_intelligence.historical_replay_engine import (
    oracle_historical_replay_engine,
)


def test_replay_builds_read_only_frames_from_memory_index():
    memory_index = {
        "memory_index_batch_id": "idx-001",
        "records": [
            {
                "source_id": "stocks-low",
                "source_type": "memory_index_record",
                "market": "STOCKS",
                "index_score": 79.0,
                "memory_tier": "validated_memory_index",
            },
            {
                "source_id": "crypto-high",
                "source_type": "memory_index_record",
                "market": "CRYPTO",
                "index_score": 96.0,
                "memory_tier": "institutional_memory_index",
            },
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index)

    assert replay["read_only"] is True
    assert replay["execution_allowed"] is False
    assert replay["execution_owner"] == "Q Series"
    assert replay["replay_status"] == "replay_complete"
    assert replay["frame_count"] == 2
    assert replay["frames"][0]["source_id"] == "crypto-high"
    assert replay["frames"][0]["read_only"] is True
    assert replay["frames"][0]["execution_allowed"] is False
    assert replay["top_market"] == "CRYPTO"


def test_replay_source_order_mode():
    memory_index = {
        "memory_index_batch_id": "idx-002",
        "records": [
            {"source_id": "first", "market": "WEATHER", "index_score": 60},
            {"source_id": "second", "market": "CRYPTO", "index_score": 99},
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index, replay_mode="source_order")

    assert replay["replay_mode"] == "source_order"
    assert replay["frames"][0]["source_id"] == "first"
    assert replay["frames"][1]["source_id"] == "second"


def test_replay_score_asc_mode():
    memory_index = {
        "memory_index_batch_id": "idx-003",
        "records": [
            {"source_id": "high", "market": "CRYPTO", "index_score": 95},
            {"source_id": "low", "market": "FOREX", "index_score": 65},
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index, replay_mode="score_asc")

    assert replay["frames"][0]["source_id"] == "low"
    assert replay["frames"][1]["source_id"] == "high"


def test_explain_frame():
    memory_index = {
        "memory_index_batch_id": "idx-004",
        "records": [
            {"source_id": "crypto-alpha", "market": "CRYPTO", "index_score": 94},
        ],
    }

    replay = oracle_historical_replay_engine.replay(memory_index)
    explanation = oracle_historical_replay_engine.explain_frame(replay, "crypto-alpha")

    assert explanation["found"] is True
    assert explanation["read_only"] is True
    assert explanation["execution_allowed"] is False
    assert explanation["frame"]["source_id"] == "crypto-alpha"
    assert "Q Series owns execution" in explanation["explanation"]


def test_empty_replay():
    replay = oracle_historical_replay_engine.replay({"memory_index_batch_id": "empty", "records": []})

    assert replay["replay_status"] == "empty_replay"
    assert replay["frame_count"] == 0
    assert replay["frames"] == []
    assert replay["summary"]["read_only"] is True


if __name__ == "__main__":
    test_replay_builds_read_only_frames_from_memory_index()
    test_replay_source_order_mode()
    test_replay_score_asc_mode()
    test_explain_frame()
    test_empty_replay()
    print("[PASS] OI-155 Oracle Historical Replay Engine")
