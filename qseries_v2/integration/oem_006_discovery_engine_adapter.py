"""
OEM-006 Discovery Engine Adapter

Canonical Oracle adapter for the existing Oracle Intelligence Discovery Engine.

Oracle remains read-only.
Q Series remains execution-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


ENGINE_ID = "oracle.discovery"
ENGINE_NAME = "Discovery Engine Adapter"
ENGINE_VERSION = "OEM-006"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_contracts():
    try:
        from qseries_v2.integration.oracle_intelligence_interface_contract import (
            OracleIntelligenceEngineContract,
            OracleEngineResult,
        )
        return OracleIntelligenceEngineContract, OracleEngineResult
    except Exception:
        class OracleIntelligenceEngineContract:
            pass

        @dataclass
        class OracleEngineResult:
            engine_id: str
            status: str
            signals: List[Dict[str, Any]] = field(default_factory=list)
            telemetry: Dict[str, Any] = field(default_factory=dict)
            errors: List[str] = field(default_factory=list)
            generated_at: str = field(default_factory=_utc_now)

        return OracleIntelligenceEngineContract, OracleEngineResult


def _load_prediction_contract():
    try:
        from qseries_v2.integration.canonical_prediction_contract import CanonicalPrediction
        return CanonicalPrediction
    except Exception:
        @dataclass
        class CanonicalPrediction:
            prediction_id: str
            engine_id: str
            market_id: str
            side: str
            confidence: float
            edge: float
            reason: str
            source_signals: List[Dict[str, Any]] = field(default_factory=list)
            metadata: Dict[str, Any] = field(default_factory=dict)
            created_at: str = field(default_factory=_utc_now)

        return CanonicalPrediction


OracleIntelligenceEngineContract, OracleEngineResult = _load_contracts()
CanonicalPrediction = _load_prediction_contract()


class DiscoveryEngineAdapter(OracleIntelligenceEngineContract):
    engine_id = ENGINE_ID
    name = ENGINE_NAME
    version = ENGINE_VERSION
    read_only = True

    def __init__(self, runtime_paths: Optional[Any] = None, engine: Optional[Any] = None):
        self.runtime_paths = runtime_paths
        self.engine = engine or self._build_underlying_engine(runtime_paths)

    def health(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "status": "ok",
            "details": {
                "ready": True,
                "read_only": True,
                "adapter": self.name,
                "version": self.version,
                "underlying_engine_loaded": self.engine is not None,
            },
            "checked_at": _utc_now(),
        }

    def analyze(self, payload: Optional[Dict[str, Any]] = None, **kwargs: Any) -> OracleEngineResult:
        payload = _safe_dict(payload)
        if kwargs:
            payload = {**payload, **kwargs}

        telemetry = {
            "engine_id": self.engine_id,
            "adapter_version": self.version,
            "read_only": True,
            "input_keys": sorted(payload.keys()),
            "generated_at": _utc_now(),
        }

        errors: List[str] = []
        raw_output = None

        try:
            raw_output = self._run_underlying_engine(payload)
        except Exception as exc:
            errors.append(f"underlying_engine_error: {exc}")

        signals = self._normalize_signals(payload, raw_output)
        telemetry["signal_count"] = len(signals)

        status = "ok" if signals and not errors else "degraded" if signals else "empty"

        return OracleEngineResult(
            engine_id=self.engine_id,
            status=status,
            signals=signals,
            telemetry=telemetry,
            errors=errors,
            generated_at=_utc_now(),
        )

    def predict(self, payload: Optional[Dict[str, Any]] = None, **kwargs: Any) -> List[Any]:
        result = self.analyze(payload, **kwargs)
        predictions: List[Any] = []

        for signal in result.signals:
            market_id = str(
                signal.get("market_id")
                or signal.get("ticker")
                or signal.get("symbol")
                or signal.get("id")
                or "unknown_market"
            )

            edge = _safe_float(signal.get("edge"), _safe_float(signal.get("discovery_score"), 0.0))
            confidence = max(0.0, min(1.0, _safe_float(signal.get("confidence"), 0.5)))
            side = str(signal.get("side") or self._side_from_edge(edge)).upper()

            reason = str(
                signal.get("reason")
                or signal.get("explanation")
                or "Discovery signal converted through OEM-006 canonical adapter."
            )

            predictions.append(
                self._make_prediction(
                    prediction_id=f"pred_{self.engine_id}_{uuid4().hex[:12]}",
                    engine_id=self.engine_id,
                    market_id=market_id,
                    side=side,
                    confidence=confidence,
                    edge=edge,
                    reason=reason,
                    source_signals=[signal],
                    metadata={
                        "adapter": self.name,
                        "version": self.version,
                        "read_only": True,
                        "discovery_type": signal.get("discovery_type"),
                        "discovery_source": signal.get("discovery_source"),
                    },
                    created_at=_utc_now(),
                )
            )

        return predictions

    def run(self, payload: Optional[Dict[str, Any]] = None, **kwargs: Any) -> OracleEngineResult:
        return self.analyze(payload, **kwargs)

    def _build_underlying_engine(self, runtime_paths: Optional[Any]) -> Optional[Any]:
        candidates = [
            ("qseries_v2.oracle_intelligence.discovery_engine", "DiscoveryEngine"),
            ("qseries_v2.oracle_intelligence.oracle_discovery_engine", "OracleDiscoveryEngine"),
            ("qseries_v2.oracle_intelligence.market_discovery_engine", "MarketDiscoveryEngine"),
        ]

        for module_name, class_name in candidates:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
            except Exception:
                continue

            try:
                return cls(runtime_paths=runtime_paths)
            except TypeError:
                try:
                    return cls(runtime_paths)
                except TypeError:
                    try:
                        return cls()
                    except Exception:
                        continue
            except Exception:
                continue

        return None

    def _run_underlying_engine(self, payload: Dict[str, Any]) -> Any:
        if self.engine is None:
            return None

        for method_name in ("analyze", "run", "scan", "evaluate", "discover", "resolve"):
            method = getattr(self.engine, method_name, None)
            if callable(method):
                try:
                    return method(payload)
                except TypeError:
                    return method()

        return None

    def _normalize_signals(self, payload: Dict[str, Any], raw_output: Any) -> List[Dict[str, Any]]:
        raw_signals = self._extract_raw_signals(raw_output)

        if not raw_signals:
            raw_signals = self._signals_from_payload(payload)

        normalized: List[Dict[str, Any]] = []

        for item in raw_signals:
            item = _safe_dict(item)
            if not item:
                continue

            market_id = str(
                item.get("market_id")
                or item.get("ticker")
                or item.get("symbol")
                or item.get("id")
                or payload.get("market_id")
                or "unknown_market"
            )

            score = _safe_float(
                item.get("discovery_score"),
                _safe_float(item.get("score"), _safe_float(item.get("edge"), 0.0)),
            )

            confidence = item.get("confidence")
            if confidence is None:
                confidence = min(1.0, max(0.0, abs(score)))

            normalized.append(
                {
                    "signal_id": item.get("signal_id") or f"sig_{self.engine_id}_{uuid4().hex[:12]}",
                    "engine_id": self.engine_id,
                    "market_id": market_id,
                    "discovery_source": item.get("discovery_source") or item.get("source") or "unknown",
                    "discovery_type": item.get("discovery_type") or item.get("type") or "market_discovery",
                    "discovery_score": score,
                    "edge": _safe_float(item.get("edge"), score),
                    "confidence": max(0.0, min(1.0, _safe_float(confidence, 0.5))),
                    "side": str(item.get("side") or self._side_from_edge(score)).upper(),
                    "reason": item.get("reason")
                    or item.get("explanation")
                    or f"Discovery signal detected for {market_id}.",
                    "raw": item,
                    "created_at": _utc_now(),
                }
            )

        return normalized

    def _extract_raw_signals(self, raw_output: Any) -> List[Dict[str, Any]]:
        if raw_output is None:
            return []

        if isinstance(raw_output, list):
            return [x for x in raw_output if isinstance(x, dict)]

        if isinstance(raw_output, dict):
            for key in ("signals", "discoveries", "discovery", "results", "items", "data", "markets"):
                value = raw_output.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
                if isinstance(value, dict):
                    return [value]
            return [raw_output]

        if hasattr(raw_output, "signals"):
            value = getattr(raw_output, "signals")
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]

        return []

    def _signals_from_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        markets = payload.get("markets")
        if isinstance(markets, list) and markets:
            return [
                {
                    "market_id": item.get("market_id") or item.get("ticker") or item.get("id"),
                    "discovery_source": item.get("discovery_source") or item.get("source"),
                    "discovery_type": item.get("discovery_type") or item.get("type"),
                    "discovery_score": item.get("discovery_score", item.get("edge", item.get("score", 0.0))),
                    "confidence": item.get("confidence", 0.5),
                    "reason": "Fallback payload-derived discovery signal.",
                }
                for item in markets
                if isinstance(item, dict)
            ]

        if payload.get("market_id"):
            return [
                {
                    "market_id": payload.get("market_id"),
                    "discovery_source": payload.get("discovery_source"),
                    "discovery_type": payload.get("discovery_type"),
                    "discovery_score": payload.get("discovery_score", payload.get("edge", payload.get("score", 0.0))),
                    "confidence": payload.get("confidence", 0.5),
                    "reason": "Fallback payload-derived discovery signal.",
                }
            ]

        return []

    def _side_from_edge(self, edge: float) -> str:
        if edge > 0:
            return "YES"
        if edge < 0:
            return "NO"
        return "HOLD"

    def _make_prediction(self, **kwargs: Any) -> Any:
        try:
            return CanonicalPrediction(**kwargs)
        except TypeError:
            filtered = {
                "prediction_id": kwargs["prediction_id"],
                "engine_id": kwargs["engine_id"],
                "market_id": kwargs["market_id"],
                "side": kwargs["side"],
                "confidence": kwargs["confidence"],
                "edge": kwargs["edge"],
                "reason": kwargs["reason"],
            }
            try:
                return CanonicalPrediction(**filtered)
            except Exception:
                return kwargs


def build_engine(runtime_paths: Optional[Any] = None) -> DiscoveryEngineAdapter:
    return DiscoveryEngineAdapter(runtime_paths=runtime_paths)


def register_with_runtime(runtime: Any, runtime_paths: Optional[Any] = None) -> DiscoveryEngineAdapter:
    engine = build_engine(runtime_paths=runtime_paths)

    for method_name in ("register_engine", "register", "add_engine"):
        method = getattr(runtime, method_name, None)
        if callable(method):
            method(engine)
            return engine

    registry = getattr(runtime, "registry", None)
    if registry is not None:
        for method_name in ("register_engine", "register", "add_engine"):
            method = getattr(registry, method_name, None)
            if callable(method):
                method(engine)
                return engine

    raise AttributeError("Runtime does not expose a supported engine registration method.")


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "DiscoveryEngineAdapter",
    "build_engine",
    "register_with_runtime",
]
