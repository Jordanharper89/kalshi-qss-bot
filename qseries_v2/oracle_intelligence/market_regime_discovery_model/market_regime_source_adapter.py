
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


READ_ONLY = True
SCHEMA_VERSION = "RGD-002"
ENGINE_ID = "oracle.discovery.market_regime.source_adapter"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deep_sort(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _deep_sort(value[key])
            for key in sorted(value.keys(), key=str)
        }

    if isinstance(value, list):
        return [
            _deep_sort(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            _deep_sort(item)
            for item in value
        )

    return value


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = repr(
        _deep_sort(payload)
    ).encode("utf-8")

    return sha256(encoded).hexdigest()


def _to_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None:
            return default

        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(
    value: Any,
    default: int = 0,
) -> int:
    try:
        if value is None:
            return default

        return int(value)
    except (TypeError, ValueError):
        return default


def _to_str(
    value: Any,
    default: str = "",
) -> str:
    if value is None:
        return default

    return str(value)


def _clamp(
    value: float,
    low: float = 0.0,
    high: float = 1.0,
) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class MarketRegimeSourceRecord:
    source_id: str
    market_id: str
    venue: str
    asset: str
    observed_at: str
    source_family: str
    signal_type: str
    signal_direction: str
    confidence: float
    magnitude: float
    prior_regime: str = "unknown"
    candidate_regime: str = "unknown"
    transition_type: str = "unknown"
    source_hash: str = ""
    sequence: int = 0
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def canonical(self) -> Dict[str, Any]:
        return _deep_sort(asdict(self))

    @property
    def record_hash(self) -> str:
        return _stable_hash(self.canonical())


@dataclass(frozen=True)
class MarketRegimeSourceSnapshot:
    schema_version: str
    engine_id: str
    status: str
    source_name: str
    observed_at: str
    record_count: int
    family_count: int
    market_count: int
    records: Tuple[
        MarketRegimeSourceRecord,
        ...,
    ]
    read_only: bool = True
    snapshot_hash: str = ""

    def canonical(
        self,
        include_snapshot_hash: bool = True,
    ) -> Dict[str, Any]:
        data = asdict(self)
        data["records"] = [
            record.canonical()
            for record in self.records
        ]

        if not include_snapshot_hash:
            data["snapshot_hash"] = ""

        return _deep_sort(data)

    def expected_snapshot_hash(self) -> str:
        return _stable_hash(
            self.canonical(
                include_snapshot_hash=False
            )
        )

    def verify_snapshot_hash(self) -> bool:
        return (
            bool(self.snapshot_hash)
            and self.snapshot_hash
            == self.expected_snapshot_hash()
        )


class MarketRegimeSourceAdapter:
    schema_version = SCHEMA_VERSION
    engine_id = ENGINE_ID
    read_only = READ_ONLY

    def __init__(
        self,
        source_name: str = "market_regime.generic",
    ) -> None:
        self.source_name = str(
            source_name
            or "market_regime.generic"
        )

    def normalize_record(
        self,
        raw: Mapping[str, Any],
    ) -> MarketRegimeSourceRecord:
        if not isinstance(raw, Mapping):
            raise TypeError(
                "raw market regime record "
                "must be a mapping"
            )

        market_id = _to_str(
            raw.get(
                "market_id",
                raw.get(
                    "market",
                    raw.get(
                        "symbol",
                        raw.get("instrument_id", ""),
                    ),
                ),
            )
        )

        venue = _to_str(
            raw.get(
                "venue",
                raw.get(
                    "exchange",
                    raw.get("source_venue", self.source_name),
                ),
            )
        )

        asset = _to_str(
            raw.get(
                "asset",
                raw.get(
                    "instrument",
                    raw.get("symbol", market_id),
                ),
            )
        )

        observed_at = _to_str(
            raw.get(
                "observed_at",
                raw.get(
                    "timestamp",
                    raw.get("time", ""),
                ),
            )
        )

        if not observed_at:
            observed_at = (
                "1970-01-01T00:00:00+00:00"
            )

        source_family = _to_str(
            raw.get(
                "source_family",
                raw.get(
                    "family",
                    raw.get(
                        "discovery_family",
                        "unknown",
                    ),
                ),
            )
        )

        signal_type = _to_str(
            raw.get(
                "signal_type",
                raw.get(
                    "signal",
                    raw.get("event_type", "unknown"),
                ),
            )
        )

        signal_direction = _to_str(
            raw.get(
                "signal_direction",
                raw.get(
                    "direction",
                    raw.get(
                        "relationship",
                        raw.get("regime", "unknown"),
                    ),
                ),
            )
        )

        confidence = _clamp(
            _to_float(
                raw.get(
                    "confidence",
                    raw.get("score", 0.0),
                )
            )
        )

        magnitude = _clamp(
            abs(
                _to_float(
                    raw.get(
                        "magnitude",
                        raw.get(
                            "strength",
                            raw.get("severity", 0.0),
                        ),
                    )
                )
            )
        )

        prior_regime = _to_str(
            raw.get(
                "prior_regime",
                raw.get(
                    "previous_regime",
                    "unknown",
                ),
            )
        )

        candidate_regime = _to_str(
            raw.get(
                "candidate_regime",
                raw.get(
                    "current_regime",
                    raw.get(
                        "target_regime",
                        raw.get("regime", "unknown"),
                    ),
                ),
            )
        )

        transition_type = _to_str(
            raw.get(
                "transition_type",
                raw.get(
                    "transition",
                    "unknown",
                ),
            )
        )

        sequence = _to_int(
            raw.get(
                "sequence",
                raw.get("index", 0),
            )
        )

        source_hash = _to_str(
            raw.get(
                "source_hash",
                raw.get(
                    "result_hash",
                    raw.get(
                        "record_hash",
                        raw.get("event_hash", ""),
                    ),
                ),
            )
        )

        metadata = (
            dict(raw.get("metadata", {}))
            if isinstance(
                raw.get("metadata", {}),
                Mapping,
            )
            else {}
        )

        metadata.update(
            {
                "normalized_by": self.engine_id,
                "source_name": self.source_name,
                "raw_hash": _stable_hash(
                    dict(raw)
                ),
            }
        )

        identity_payload = {
            "source_name": self.source_name,
            "market_id": market_id,
            "venue": venue,
            "asset": asset,
            "observed_at": observed_at,
            "source_family": source_family,
            "signal_type": signal_type,
            "signal_direction": signal_direction,
            "confidence": confidence,
            "magnitude": magnitude,
            "prior_regime": prior_regime,
            "candidate_regime": candidate_regime,
            "transition_type": transition_type,
            "source_hash": source_hash,
            "sequence": sequence,
        }

        source_id = _to_str(
            raw.get("source_id", "")
        )

        if not source_id:
            source_id = _stable_hash(
                identity_payload
            )

        if not source_hash:
            source_hash = _stable_hash(
                {
                    "source_family": source_family,
                    "signal_type": signal_type,
                    "market_id": market_id,
                    "observed_at": observed_at,
                    "raw_hash": metadata["raw_hash"],
                }
            )

        return MarketRegimeSourceRecord(
            source_id=source_id,
            market_id=market_id,
            venue=venue,
            asset=asset,
            observed_at=observed_at,
            source_family=source_family,
            signal_type=signal_type,
            signal_direction=signal_direction,
            confidence=confidence,
            magnitude=magnitude,
            prior_regime=prior_regime,
            candidate_regime=candidate_regime,
            transition_type=transition_type,
            source_hash=source_hash,
            sequence=sequence,
            metadata=metadata,
        )

    def snapshot(
        self,
        raw_records: Iterable[
            Mapping[str, Any]
        ],
        observed_at: Optional[str] = None,
    ) -> MarketRegimeSourceSnapshot:
        records: List[
            MarketRegimeSourceRecord
        ] = [
            self.normalize_record(raw)
            for raw in list(raw_records or [])
        ]

        ordered_records = tuple(
            sorted(
                records,
                key=lambda record: (
                    record.market_id,
                    record.venue,
                    record.asset,
                    record.source_family,
                    record.signal_type,
                    record.observed_at,
                    record.sequence,
                    record.source_id,
                ),
            )
        )

        status = (
            "ok"
            if ordered_records
            else "empty"
        )

        snapshot_time = (
            observed_at
            or (
                ordered_records[0].observed_at
                if ordered_records
                else _utc_now_iso()
            )
        )

        family_count = len(
            {
                record.source_family
                for record in ordered_records
            }
        )

        market_count = len(
            {
                (
                    record.market_id,
                    record.venue,
                    record.asset,
                )
                for record in ordered_records
            }
        )

        unsigned = MarketRegimeSourceSnapshot(
            schema_version=self.schema_version,
            engine_id=self.engine_id,
            status=status,
            source_name=self.source_name,
            observed_at=str(snapshot_time),
            record_count=len(ordered_records),
            family_count=family_count,
            market_count=market_count,
            records=ordered_records,
            read_only=True,
            snapshot_hash="",
        )

        return MarketRegimeSourceSnapshot(
            schema_version=unsigned.schema_version,
            engine_id=unsigned.engine_id,
            status=unsigned.status,
            source_name=unsigned.source_name,
            observed_at=unsigned.observed_at,
            record_count=unsigned.record_count,
            family_count=unsigned.family_count,
            market_count=unsigned.market_count,
            records=unsigned.records,
            read_only=True,
            snapshot_hash=(
                unsigned.expected_snapshot_hash()
            ),
        )

    def capabilities(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "engine_id": self.engine_id,
            "read_only": True,
            "supports": [
                "normalize_record",
                "snapshot",
                "multi_family_signal_normalization",
                "regime_candidate_normalization",
                "transition_normalization",
                "deterministic_order_independent_hashing",
                "source_provenance_hashing",
                "immutable_snapshot_generation",
            ],
        }

    def assert_read_only(self) -> bool:
        forbidden = [
            "buy",
            "sell",
            "trade",
            "execute",
            "order",
            "sign",
            "submit",
            "broadcast",
        ]

        offenders = sorted(
            word
            for word in forbidden
            if word in set(dir(self))
        )

        if offenders:
            raise AssertionError(
                "mutation-like methods are "
                f"forbidden: {offenders}"
            )

        return True


def build_market_regime_source_snapshot(
    raw_records: Iterable[
        Mapping[str, Any]
    ],
    source_name: str = "market_regime.generic",
    observed_at: Optional[str] = None,
) -> MarketRegimeSourceSnapshot:
    return MarketRegimeSourceAdapter(
        source_name=source_name
    ).snapshot(
        raw_records=raw_records,
        observed_at=observed_at,
    )


__all__ = [
    "READ_ONLY",
    "SCHEMA_VERSION",
    "ENGINE_ID",
    "MarketRegimeSourceRecord",
    "MarketRegimeSourceSnapshot",
    "MarketRegimeSourceAdapter",
    "build_market_regime_source_snapshot",
]
