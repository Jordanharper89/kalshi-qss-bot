from pathlib import Path

TEST = Path.cwd() / "test_oi_195_universal_market_adapter_replay_analytics_engine.py"

TEST.write_text(r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_analytics_engine import create_replay_analytics_engine


def as_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return dict(obj)


def test_oi_195_replay_analytics_engine():
    engine = create_replay_analytics_engine("oracle.test")

    records = [
        {"registration_id": "reg-001", "adapter_id": "adp.kalshi", "certified": True, "confidence": 0.91},
        {"registration_id": "reg-002", "adapter_id": "adp.kalshi", "certified": True, "confidence": 0.74},
        {"registration_id": "reg-003", "adapter_id": "adp.polymarket", "certified": False, "confidence": 0.42},
    ]

    result = engine.analyze(records)
    data = as_dict(result)

    assert data["passed"] is True
    assert data["record_count"] == 3
    assert "telemetry" in data
    assert "explainability" in data
    assert data["read_only_guardrails"]["oracle_read_only"] is True
    assert data["read_only_guardrails"]["execution_owner"] == "Q_SERIES_ONLY"

    summary = engine.summarize(records)
    assert as_dict(summary)["passed"] is True

    assert engine.latest_report() is not None
    assert len(engine.reports()) >= 2


if __name__ == "__main__":
    test_oi_195_replay_analytics_engine()
    print("[PASS] OI-195 Universal Market Adapter Replay Analytics Engine")
'''.lstrip(), encoding="utf-8")

print("[OK] Patched OI-195 ReplayResult test")
print("Run:")
print("py test_oi_195_universal_market_adapter_replay_analytics_engine.py")
print("py run_oracle_replay_smoke_gate_v1.py")