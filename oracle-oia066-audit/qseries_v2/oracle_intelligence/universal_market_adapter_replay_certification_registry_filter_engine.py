from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

ENGINE_ID = "OI-205"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Certification Registry Filter Engine"
ENGINE_VERSION = "1.0.1"

LEVEL_RANK = {
    "strong_certified": 4,
    "certified": 3,
    "review_required": 2,
    "rejected": 1,
    "unknown": 0,
}


@dataclass(frozen=True)
class ReplayCertificationRegistryFilterMatch:
    registry_id: str
    source_engine_id: str
    certified: bool
    certification_level: str
    status: str
    intelligence_score: float
    signal_count: int
    decision_count: int
    reason_codes: Tuple[str, ...] = field(default_factory=tuple)
    explanation: str = ""
    source: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        return data


@dataclass(frozen=True)
class ReplayCertificationRegistryFilterResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    filter_spec: Dict[str, Any]
    input_count: int
    filtered_count: int
    matches: Tuple[ReplayCertificationRegistryFilterMatch, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "filter_spec": dict(self.filter_spec),
            "input_count": self.input_count,
            "filtered_count": self.filtered_count,
            "matches": [match.to_dict() for match in self.matches],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayCertificationRegistryFilterEngine:
    def filter(
        self,
        registry_or_query_result: Any,
        *,
        min_intelligence_score: Optional[float] = None,
        max_intelligence_score: Optional[float] = None,
        min_signal_count: Optional[int] = None,
        min_decision_count: Optional[int] = None,
        required_reason_codes: Optional[Iterable[str]] = None,
        source_engine_id: Optional[str] = None,
        status: Optional[str] = None,
        certification_level: Optional[str] = None,
        min_certification_level: Optional[str] = None,
        certified: Optional[bool] = None,
        sort_by: str = "intelligence_score",
        descending: bool = True,
        limit: Optional[int] = None,
    ) -> ReplayCertificationRegistryFilterResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        records = self._extract_records(registry_or_query_result)
        required_codes = [str(code) for code in (required_reason_codes or [])]

        filter_spec = {
            "min_intelligence_score": min_intelligence_score,
            "max_intelligence_score": max_intelligence_score,
            "min_signal_count": min_signal_count,
            "min_decision_count": min_decision_count,
            "required_reason_codes": required_codes,
            "source_engine_id": source_engine_id,
            "status": status,
            "certification_level": certification_level,
            "min_certification_level": min_certification_level,
            "certified": certified,
            "sort_by": sort_by,
            "descending": descending,
            "limit": limit,
        }

        matches: List[ReplayCertificationRegistryFilterMatch] = []
        for item in records:
            data = self._to_mapping(item)
            if not data:
                continue
            normalized = self._normalize(data)
            if self._passes(
                normalized,
                min_intelligence_score=min_intelligence_score,
                max_intelligence_score=max_intelligence_score,
                min_signal_count=min_signal_count,
                min_decision_count=min_decision_count,
                required_reason_codes=required_codes,
                source_engine_id=source_engine_id,
                status=status,
                certification_level=certification_level,
                min_certification_level=min_certification_level,
                certified=certified,
            ):
                matches.append(self._to_match(normalized))

        matches = self._sort(matches, sort_by=sort_by, descending=descending)

        if limit is not None:
            matches = matches[: max(0, int(limit))]

        return ReplayCertificationRegistryFilterResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status="ok" if matches else "empty",
            filter_spec=filter_spec,
            input_count=len(records),
            filtered_count=len(matches),
            matches=tuple(matches),
            telemetry={
                "engine_id": ENGINE_ID,
                "engine_name": ENGINE_NAME,
                "engine_version": ENGINE_VERSION,
                "read_only": True,
                "oracle_role": "brain",
                "execution_owner": "Q Series",
                "does_not_execute": True,
                "does_not_route_orders": True,
                "does_not_manage_positions": True,
                "canonical_input": "ReplayCertificationRegistryResult or ReplayCertificationRegistryQueryResult compatible",
                "canonical_output": "ReplayCertificationRegistryFilterResult",
                "filter_is_read_only": True,
                "input_count": len(records),
                "filtered_count": len(matches),
                "explainability": True,
                "replayability": True,
            },
            explanation=(
                f"Read-only registry filter scanned {len(records)} record(s) and retained "
                f"{len(matches)} match(es). Oracle output is advisory only; Q Series remains "
                "the only execution engine."
            ),
        )

    def _extract_records(self, payload: Any) -> List[Any]:
        if payload is None:
            return []
        if isinstance(payload, Mapping):
            if "matches" in payload:
                return list(payload.get("matches") or [])
            if "records" in payload:
                return list(payload.get("records") or [])
            return [payload]
        if hasattr(payload, "matches"):
            raw = getattr(payload, "matches")
            if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
                return list(raw)
        if hasattr(payload, "records"):
            raw = getattr(payload, "records")
            if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
                return list(raw)
        if isinstance(payload, Iterable) and not isinstance(payload, (str, bytes)):
            return list(payload)
        return [payload]

    def _normalize(self, data: Mapping[str, Any]) -> Dict[str, Any]:
        reason_codes = data.get("reason_codes", [])
        if isinstance(reason_codes, str):
            reason_codes = [reason_codes]
        elif not isinstance(reason_codes, Iterable):
            reason_codes = []

        return {
            "registry_id": str(data.get("registry_id", "")),
            "source_engine_id": str(data.get("source_engine_id", data.get("engine_id", ""))),
            "certified": bool(data.get("certified", False)),
            "certification_level": str(data.get("certification_level", "unknown")),
            "status": str(data.get("status", "unknown")),
            "intelligence_score": self._clamp01(self._number(data, "intelligence_score", default=0.0)),
            "signal_count": int(self._number(data, "signal_count", default=0.0)),
            "decision_count": int(self._number(data, "decision_count", default=0.0)),
            "reason_codes": [str(code) for code in reason_codes if str(code).strip()],
            "explanation": str(data.get("explanation", "")),
            "source": dict(data),
        }

    def _passes(
        self,
        record: Mapping[str, Any],
        *,
        min_intelligence_score: Optional[float],
        max_intelligence_score: Optional[float],
        min_signal_count: Optional[int],
        min_decision_count: Optional[int],
        required_reason_codes: List[str],
        source_engine_id: Optional[str],
        status: Optional[str],
        certification_level: Optional[str],
        min_certification_level: Optional[str],
        certified: Optional[bool],
    ) -> bool:
        if min_intelligence_score is not None and record["intelligence_score"] < float(min_intelligence_score):
            return False
        if max_intelligence_score is not None and record["intelligence_score"] > float(max_intelligence_score):
            return False
        if min_signal_count is not None and record["signal_count"] < int(min_signal_count):
            return False
        if min_decision_count is not None and record["decision_count"] < int(min_decision_count):
            return False
        if source_engine_id is not None and record["source_engine_id"] != source_engine_id:
            return False
        if status is not None and record["status"] != status:
            return False
        if certification_level is not None and record["certification_level"] != certification_level:
            return False
        if certified is not None and record["certified"] is not bool(certified):
            return False
        if min_certification_level is not None:
            if LEVEL_RANK.get(record["certification_level"], 0) < LEVEL_RANK.get(min_certification_level, 0):
                return False
        for code in required_reason_codes:
            if code not in record["reason_codes"]:
                return False
        return True

    def _sort(
        self,
        matches: List[ReplayCertificationRegistryFilterMatch],
        *,
        sort_by: str,
        descending: bool,
    ) -> List[ReplayCertificationRegistryFilterMatch]:
        if sort_by == "certification_level":
            return sorted(
                matches,
                key=lambda item: (LEVEL_RANK.get(item.certification_level, 0), item.registry_id),
                reverse=descending,
            )
        if sort_by == "registry_id":
            return sorted(matches, key=lambda item: item.registry_id, reverse=descending)
        return sorted(
            matches,
            key=lambda item: (item.intelligence_score, item.registry_id),
            reverse=descending,
        )

    def _to_match(self, record: Mapping[str, Any]) -> ReplayCertificationRegistryFilterMatch:
        return ReplayCertificationRegistryFilterMatch(
            registry_id=record["registry_id"],
            source_engine_id=record["source_engine_id"],
            certified=record["certified"],
            certification_level=record["certification_level"],
            status=record["status"],
            intelligence_score=record["intelligence_score"],
            signal_count=record["signal_count"],
            decision_count=record["decision_count"],
            reason_codes=tuple(record["reason_codes"]),
            explanation=record["explanation"],
            source=dict(record["source"]),
        )

    def _to_mapping(self, item: Any) -> Dict[str, Any]:
        if item is None:
            return {}
        if isinstance(item, Mapping):
            return dict(item)
        if hasattr(item, "to_dict") and callable(item.to_dict):
            mapped = item.to_dict()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        if hasattr(item, "__dict__"):
            return dict(vars(item))
        return {}

    def _number(self, data: Mapping[str, Any], key: str, *, default: float = 0.0) -> float:
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return float(default)

    def _clamp01(self, value: float) -> float:
        value = float(value)
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return max(0.0, min(1.0, value))


def filter_replay_certification_registry(payload: Any, **filters: Any) -> ReplayCertificationRegistryFilterResult:
    return UniversalMarketAdapterReplayCertificationRegistryFilterEngine().filter(payload, **filters)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayCertificationRegistryFilterMatch",
    "ReplayCertificationRegistryFilterResult",
    "UniversalMarketAdapterReplayCertificationRegistryFilterEngine",
    "filter_replay_certification_registry",
]
