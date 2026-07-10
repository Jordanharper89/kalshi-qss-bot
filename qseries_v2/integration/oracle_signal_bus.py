
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
