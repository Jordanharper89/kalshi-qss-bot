"""
OI-204 — Oracle Universal Market Adapter Replay Certification Registry Query Engine

Read-only Oracle Intelligence component.

Queries replay certification registry records produced by OI-203.
This engine never mutates registry records and never executes trades.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


ENGINE_ID = "OI-204"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Certification Registry Query Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReplayCertificationRegistryQueryMatch:
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
class ReplayCertificationRegistryQueryResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    query: Dict[str, Any]
    input_count: int
    match_count: int
    matches: Tuple[ReplayCertificationRegistryQueryMatch, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "query": dict(self.query),
            "input_count": self.input_count,
            "match_count": self.match_count,
            "matches": [match.to_dict() for match in self.matches],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayCertificationRegistryQueryEngine:
    """
    Read-only query engine for OI-203 registry outputs.

    Supported query fields:
        registry_id
        source_engine_id
        status
        certification_level
        certified
        min_intelligence_score
        max_intelligence_score
        reason_code
        limit
    """

    def query(
        self,
        registry: Any,
        *,
        registry_id: Optional[str] = None,
        source_engine_id: Optional[str] = None,
        status: Optional[str] = None,
        certification_level: Optional[str] = None,
        certified: Optional[bool] = None,
        min_intelligence_score: Optional[float] = None,
        max_intelligence_score: Optional[float] = None,
        reason_code: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ReplayCertificationRegistryQueryResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        records = self._extract_records(registry)

        query_spec = {
            "registry_id": registry_id,
            "source_engine_id": source_engine_id,
            "status": status,
            "certification_level": certification_level,
            "certified": certified,
            "min_intelligence_score": min_intelligence_score,
            "max_intelligence_score": max_intelligence_score,
            "reason_code": reason_code,
            "limit": limit,
        }

        matches: List[ReplayCertificationRegistryQueryMatch] = []
        for record in records:
            data = self._to_mapping(record)
            if not data:
                continue
            normalized = self._normalize(data)
            if self._matches(
                normalized,
                registry_id=registry_id,
                source_engine_id=source_engine_id,
                status=status,
                certification_level=certification_level,
                certified=certified,
                min_intelligence_score=min_intelligence_score,
                max_intelligence_score=max_intelligence_score,
                reason_code=reason_code,
            ):
                matches.append(self._to_match(normalized))

        if limit is not None:
            matches = matches[: max(0, int(limit))]

        result_status = "ok" if matches else "empty"

        return ReplayCertificationRegistryQueryResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=result_status,
            query=query_spec,
            input_count=len(records),
            match_count=len(matches),
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
                "canonical_input": "ReplayCertificationRegistryResult compatible",
                "canonical_output": "ReplayCertificationRegistryQueryResult",
                "query_is_read_only": True,
                "input_count": len(records),
                "match_count": len(matches),
                "explainability": True,
                "replayability": True,
            },
            explanation=(
                f"Read-only registry query scanned {len(records)} record(s) and returned "
                f"{len(matches)} match(es). Oracle query output is advisory only; Q Series "
                "remains the only execution engine."
            ),
        )

    def _extract_records(self, registry: Any) -> List[Any]:
        if registry is None:
            return []
        if isinstance(registry, Mapping):
            if "records" in registry:
                return list(registry.get("records") or [])
            return [registry]
        if hasattr(registry, "records"):
            raw = getattr(registry, "records")
            if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
                return list(raw)
        if isinstance(registry, Iterable) and not isinstance(registry, (str, bytes)):
            return list(registry)
        return [registry]

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
            "certification_level": str(data.get("certification_level", "")),
            "status": str(data.get("status", "")),
            "intelligence_score": self._clamp01(self._number(data, "intelligence_score", default=0.0)),
            "signal_count": int(self._number(data, "signal_count", default=0.0)),
            "decision_count": int(self._number(data, "decision_count", default=0.0)),
            "reason_codes": [str(code) for code in reason_codes if str(code).strip()],
            "explanation": str(data.get("explanation", "")),
            "source": dict(data),
        }

    def _matches(
        self,
        record: Mapping[str, Any],
        *,
        registry_id: Optional[str],
        source_engine_id: Optional[str],
        status: Optional[str],
        certification_level: Optional[str],
        certified: Optional[bool],
        min_intelligence_score: Optional[float],
        max_intelligence_score: Optional[float],
        reason_code: Optional[str],
    ) -> bool:
        if registry_id is not None and record["registry_id"] != registry_id:
            return False
        if source_engine_id is not None and record["source_engine_id"] != source_engine_id:
            return False
        if status is not None and record["status"] != status:
            return False
        if certification_level is not None and record["certification_level"] != certification_level:
            return False
        if certified is not None and record["certified"] is not bool(certified):
            return False
        if min_intelligence_score is not None and record["intelligence_score"] < float(min_intelligence_score):
            return False
        if max_intelligence_score is not None and record["intelligence_score"] > float(max_intelligence_score):
            return False
        if reason_code is not None and reason_code not in record["reason_codes"]:
            return False
        return True

    def _to_match(self, record: Mapping[str, Any]) -> ReplayCertificationRegistryQueryMatch:
        return ReplayCertificationRegistryQueryMatch(
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


def query_replay_certification_registry(registry: Any, **filters: Any) -> ReplayCertificationRegistryQueryResult:
    return UniversalMarketAdapterReplayCertificationRegistryQueryEngine().query(registry, **filters)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayCertificationRegistryQueryMatch",
    "ReplayCertificationRegistryQueryResult",
    "UniversalMarketAdapterReplayCertificationRegistryQueryEngine",
    "query_replay_certification_registry",
]
