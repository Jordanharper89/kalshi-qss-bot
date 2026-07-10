
from datetime import datetime, timezone

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OraclePredictionResult,
    OracleExplanation,
)
from qseries_v2.integration.oracle_signal_bus import (
    OracleSignalBus,
    create_oracle_signal_bus,
    oracle_signal_bus,
)


def test_int_002_oracle_signal_bus():
    bus = create_oracle_signal_bus()

    assert isinstance(bus, OracleSignalBus)
    assert oracle_signal_bus is create_oracle_signal_bus

    captured_all = []
    captured_market = []

    bus.subscribe_all(lambda signal: captured_all.append(signal))
    bus.subscribe("KXTEST-001", lambda signal: captured_market.append(signal))

    prediction = OraclePredictionResult(
        engine_id="oracle.dummy",
        market_id="KXTEST-001",
        prediction="YES",
        confidence=0.81,
        score=0.22,
        features={"edge": 0.14},
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    explanation = OracleExplanation(
        engine_id="oracle.dummy",
        market_id="KXTEST-001",
        summary="Strong positive signal",
        reasons=["Momentum", "Liquidity"],
        evidence={"sample_count": 5},
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    signal = bus.emit(prediction, explanation)

    assert signal.engine_id == "oracle.dummy"
    assert signal.market_id == "KXTEST-001"
    assert signal.prediction == "YES"
    assert signal.confidence == 0.81
    assert signal.explanation is not None
    assert signal.explanation["summary"] == "Strong positive signal"

    assert len(captured_all) == 1
    assert len(captured_market) == 1

    assert len(bus.list_signals()) == 1
    assert len(bus.list_signals("KXTEST-001")) == 1
    assert bus.latest_signal("KXTEST-001") == signal
    assert bus.latest_signal("UNKNOWN") is None

    health = bus.health()
    assert health["status"] == "ok"
    assert health["signal_count"] == 1

    cleared = bus.clear()
    assert cleared == 1
    assert bus.list_signals() == []

    print("[PASS] INT-002 Oracle Signal Bus")
    print(health)


if __name__ == "__main__":
    test_int_002_oracle_signal_bus()
