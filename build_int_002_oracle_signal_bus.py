from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "integration" / "oracle_signal_bus.py"
TEST = ROOT / "test_int_002_oracle_signal_bus.py"

TARGET.parent.mkdir(parents=True, exist_ok=True)

code = r'''
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from qseries_v2.integration.oracle_intelligence_interface_contract import (
    OraclePredictionResult,
    OracleExplanation,
)


@dataclass(frozen=True)
class OracleSignal:
    signal_id: str
    engine_id: str
    market_id: str
    prediction: str
    confidence: float
    score: float
    features: Dict[str, Any]
    explanation: Optional[Dict[str, Any]]
    emitted_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OracleSignalBus:
    """
    INT-002 Oracle Signal Bus.

    Canonical in-memory signal transport between read-only Oracle Intelligence
    engines and downstream Q Series consumers.

    Oracle emits intelligence.
    Q Series consumes and executes separately.
    """

    def __init__(self) -> None:
        self._signals: List[OracleSignal] = []
        self._subscribers: Dict[str, List[Callable[[OracleSignal], None]]] = {}

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def emit(
        self,
        prediction: OraclePredictionResult,
        explanation: Optional[OracleExplanation] = None,
    ) -> OracleSignal:
        signal = OracleSignal(
            signal_id=f"{prediction.engine_id}:{prediction.market_id}:{len(self._signals) + 1}",
            engine_id=prediction.engine_id,
            market_id=prediction.market_id,
            prediction=prediction.prediction,
            confidence=float(prediction.confidence),
            score=float(prediction.score),
            features=dict(prediction.features),
            explanation=explanation.to_dict() if explanation else None,
            emitted_at=self.now_iso(),
        )

        self._signals.append(signal)

        for callback in self._subscribers.get("*", []):
            callback(signal)

        for callback in self._subscribers.get(signal.market_id, []):
            callback(signal)

        return signal

    def subscribe(self, market_id: str, callback: Callable[[OracleSignal], None]) -> None:
        if not market_id:
            raise ValueError("market_id is required")
        if not callable(callback):
            raise ValueError("callback must be callable")

        self._subscribers.setdefault(market_id, []).append(callback)

    def subscribe_all(self, callback: Callable[[OracleSignal], None]) -> None:
        self.subscribe("*", callback)

    def list_signals(self, market_id: Optional[str] = None) -> List[OracleSignal]:
        if market_id is None:
            return list(self._signals)
        return [signal for signal in self._signals if signal.market_id == market_id]

    def latest_signal(self, market_id: str) -> Optional[OracleSignal]:
        matches = self.list_signals(market_id)
        return matches[-1] if matches else None

    def clear(self) -> int:
        count = len(self._signals)
        self._signals.clear()
        return count

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "bus": "oracle_signal_bus",
            "signal_count": len(self._signals),
            "subscriber_channels": sorted(self._subscribers.keys()),
        }


def create_oracle_signal_bus() -> OracleSignalBus:
    return OracleSignalBus()


oracle_signal_bus = create_oracle_signal_bus


__all__ = [
    "OracleSignal",
    "OracleSignalBus",
    "create_oracle_signal_bus",
    "oracle_signal_bus",
]
'''

test_code = r'''
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
'''

TARGET.write_text(code, encoding="utf-8")
TEST.write_text(test_code, encoding="utf-8")

init_path = ROOT / "qseries_v2" / "integration" / "__init__.py"
existing = init_path.read_text(encoding="utf-8") if init_path.exists() else ""

export = (
    "from .oracle_signal_bus import "
    "OracleSignal, OracleSignalBus, create_oracle_signal_bus, oracle_signal_bus\n"
)

if export not in existing:
    init_path.write_text(existing.rstrip() + "\n" + export, encoding="utf-8")

print("========================================")
print(" INT-002 INSTALLER")
print(" Oracle Signal Bus")
print("========================================")
print(f"[OK] Wrote {TARGET}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {init_path}")
print("")
print("[DONE] INT-002 installed")
print("")
print("Run:")
print("py test_int_002_oracle_signal_bus.py")