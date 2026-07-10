
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


READ_ONLY = True
SCHEMA_VERSION = "CRD-002"
ENGINE_ID = "oracle.discovery.correlation.source_adapter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _deep_sort(value[k]) for k in sorted(value.keys(), key=str)}
    if isinstance(value, list):
        return [_deep_sort(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_deep_sort(v) for v in value)
    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    return sha256(repr(_deep_sort(payload)).encode("utf-8")).hexdigest()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


@dataclass(frozen=True)
class CorrelationSourceRecord:
    source_id: str
    primary_market_id: str
    related_market_id: str
    venue: str
    observed_at: str
    correlation: float = 0.0
    baseline_correlation: float = 0.0
    recent_correlation: float = 0.0
    correlation_change: float = 0.0
    lag: int = 0
    window: str = "unknown"
    sample_size: int = 0
    primary_return: float = 0.0
    related_return: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def record_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class CorrelationSourceSnapshot:
    schema_version: str
    engine_id: str
    status: str
    source_name: str
    observed_at: str
    record_count: int
    records: Tuple[CorrelationSourceRecord, ...]
    read_only: bool = True
    snapshot_hash: str = ""

    def canonical(self) -> Dict[str, Any]:
        data = asdict(self)
        data["records"] = [r.canonical() for r in self.records]
        return _deep_sort(data)


class CorrelationSourceAdapter:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(self, source_name: str = "correlation.generic") -> None:
        self.source_name = str(source_name or "correlation.generic")

    def normalize_record(self, raw: Mapping[str, Any]) -> CorrelationSourceRecord:
        if not isinstance(raw, Mapping):
            raise TypeError("raw correlation record must be a mapping")

        primary_market_id = _to_str(
            raw.get("primary_market_id", raw.get("primary", raw.get("market_a", raw.get("left_market", ""))))
        )
        related_market_id = _to_str(
            raw.get("related_market_id", raw.get("related", raw.get("market_b", raw.get("right_market", ""))))
        )
        venue = _to_str(raw.get("venue", raw.get("exchange", self.source_name)))

        observed_at = _to_str(raw.get("observed_at", raw.get("timestamp", raw.get("time", ""))))
        if not observed_at:
            observed_at = "1970-01-01T00:00:00+00:00"

        correlation = _to_float(raw.get("correlation", raw.get("corr", 0.0)))
        baseline = _to_float(raw.get("baseline_correlation", raw.get("baseline", raw.get("historical_correlation", 0.0))))
        recent = _to_float(raw.get("recent_correlation", raw.get("recent", correlation)))

        correlation_change = _to_float(raw.get("correlation_change", 0.0))
        if correlation_change == 0.0:
            correlation_change = recent - baseline

        lag = int(_to_float(raw.get("lag", raw.get("lead_lag", 0)), 0.0))
        window = _to_str(raw.get("window", raw.get("lookback", "unknown")))
        sample_size = int(_to_float(raw.get("sample_size", raw.get("n", 0)), 0.0))
        primary_return = _to_float(raw.get("primary_return", raw.get("return_a", raw.get("left_return", 0.0))))
        related_return = _to_float(raw.get("related_return", raw.get("return_b", raw.get("right_return", 0.0))))

        metadata = dict(raw.get("metadata", {})) if isinstance(raw.get("metadata", {}), Mapping) else {}

        identity_payload = {
            "source_name": self.source_name,
            "primary_market_id": primary_market_id,
            "related_market_id": related_market_id,
            "venue": venue,
            "observed_at": observed_at,
            "correlation": correlation,
            "baseline_correlation": baseline,
            "recent_correlation": recent,
            "correlation_change": correlation_change,
            "lag": lag,
            "window": window,
            "sample_size": sample_size,
            "primary_return": primary_return,
            "related_return": related_return,
        }

        source_id = _to_str(raw.get("source_id", ""))
        if not source_id:
            source_id = _stable_hash(identity_payload)

        metadata["raw_hash"] = _stable_hash(dict(raw))

        return CorrelationSourceRecord(
            source_id=source_id,
            primary_market_id=primary_market_id,
            related_market_id=related_market_id,
            venue=venue,
            observed_at=observed_at,
            correlation=correlation,
            baseline_correlation=baseline,
            recent_correlation=recent,
            correlation_change=correlation_change,
            lag=lag,
            window=window,
            sample_size=sample_size,
            primary_return=primary_return,
            related_return=related_return,
            metadata=metadata,
        )

    def snapshot(
        self,
        raw_records: Iterable[Mapping[str, Any]],
        observed_at: Optional[str] = None,
    ) -> CorrelationSourceSnapshot:
        records: List[CorrelationSourceRecord] = [
            self.normalize_record(raw) for raw in list(raw_records or [])
        ]

        records_sorted = tuple(
            sorted(
                records,
                key=lambda r: (
                    r.primary_market_id,
                    r.related_market_id,
                    r.venue,
                    r.window,
                    r.lag,
                    r.observed_at,
                    r.source_id,
                ),
            )
        )

        status = "ok" if records_sorted else "empty"
        snapshot_time = observed_at or (records_sorted[0].observed_at if records_sorted else _utc_now_iso())

        unsigned = CorrelationSourceSnapshot(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            source_name=self.source_name,
            observed_at=snapshot_time,
            record_count=len(records_sorted),
            records=records_sorted,
            read_only=True,
            snapshot_hash="",
        )

        return CorrelationSourceSnapshot(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            record_count=unsigned.record_count,
            records=unsigned.records,
            read_only=True,
            snapshot_hash=_stable_hash(unsigned.canonical()),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "normalize_record",
                "snapshot",
                "deterministic_order_independent_hashing",
                "correlation_normalization",
                "baseline_recent_delta_calculation",
                "lead_lag_metadata",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = ["buy", "sell", "trade", "execute", "order", "sign", "submit", "broadcast"]
        offenders = sorted(word for word in forbidden if word in set(dir(self)))
        if offenders:
            raise AssertionError(f"mutation-like methods are forbidden: {offenders}")
        return True


def build_correlation_source_snapshot(
    raw_records: Iterable[Mapping[str, Any]],
    source_name: str = "correlation.generic",
    observed_at: Optional[str] = None,
) -> CorrelationSourceSnapshot:
    return CorrelationSourceAdapter(source_name=source_name).snapshot(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "CorrelationSourceRecord",
    "CorrelationSourceSnapshot",
    "CorrelationSourceAdapter",
    "build_correlation_source_snapshot",
]
