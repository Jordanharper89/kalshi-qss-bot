from pathlib import Path

ROOT = Path.cwd()
TEST = ROOT / "test_oi_195_universal_market_adapter_replay_analytics_engine.py"

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_analytics_engine import create_replay_analytics_engine


def test_oi_195_replay_analytics_engine():
    engine = create_replay_analytics_engine("oracle.test")

    records = [
        {
            "registration_id": "reg-001",
            "adapter_id": "adp.kalshi",
            "market_type": "prediction_market",
            "certified": True,
            "confidence": 0.91,
            "certification_level": "certified",
        },
        {
            "registration_id": "reg-002",
            "adapter_id": "adp.kalshi",
            "market_type": "prediction_market",
            "certified": True,
            "confidence": 0.74,
            "certification_level": "certified_with_warnings",
        },
        {
            "registration_id": "reg-003",
            "adapter_id": "adp.polymarket",
            "market_type": "prediction_market",
            "certified": False,
            "confidence": 0.42,
            "certification_level": "not_certified",
        },
    ]

    result = engine.analyze(records)

    assert result.passed is True
    assert result.record_count == 3
    assert result.certified_count == 2
    assert result.uncertified_count == 1
    assert result.average_confidence > 0
    assert result.read_only_guardrails["oracle_read_only"] is True
    assert result.read_only_guardrails["execution_owner"] == "Q_SERIES_ONLY"

    summary = engine.summarize(records)
    assert summary.passed is True
    assert summary.record_count == 3

    assert engine.latest_report() is not None
    assert len(engine.reports()) >= 2


if __name__ == "__main__":
    test_oi_195_replay_analytics_engine()
    print("[PASS] OI-195 Universal Market Adapter Replay Analytics Engine")
'''.lstrip(), encoding="utf-8")

print("[OK] Patched OI-195 test file")
print("Run:")
print("py test_oi_195_universal_market_adapter_replay_analytics_engine.py")
print("py run_oracle_replay_smoke_gate_v1.py")