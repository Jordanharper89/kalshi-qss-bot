from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_certification_registry_query_engine.py"
TEST = ROOT / "test_oi_204_universal_market_adapter_replay_certification_registry_query_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
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
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_query_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryQueryEngine,
    query_replay_certification_registry,
)


def sample_registry():
    return {
        "engine_id": "OI-203",
        "records": [
            {
                "registry_id": "rec-1",
                "source_engine_id": "OI-201",
                "certified": True,
                "certification_level": "certified",
                "status": "certified",
                "intelligence_score": 0.64,
                "signal_count": 1,
                "decision_count": 1,
                "reason_codes": ["READ_ONLY_ORACLE_CERTIFICATION", "Q_SERIES_EXECUTION_REQUIRED"],
                "explanation": "Certified sample.",
            },
            {
                "registry_id": "rec-2",
                "source_engine_id": "OI-201",
                "certified": False,
                "certification_level": "review_required",
                "status": "review",
                "intelligence_score": 0.40,
                "signal_count": 1,
                "decision_count": 1,
                "reason_codes": ["WARNING_SIGNALS_PRESENT"],
                "explanation": "Review sample.",
            },
        ],
    }


def test_query_by_registry_id():
    result = UniversalMarketAdapterReplayCertificationRegistryQueryEngine().query(
        sample_registry(),
        registry_id="rec-1",
    )

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 2
    assert result.match_count == 1
    assert result.matches[0].registry_id == "rec-1"
    assert result.matches[0].certified is True
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_query_by_level_and_score_range():
    result = query_replay_certification_registry(
        sample_registry(),
        certification_level="certified",
        min_intelligence_score=0.60,
    )

    assert result.match_count == 1
    assert result.matches[0].registry_id == "rec-1"
    assert result.matches[0].intelligence_score == 0.64


def test_query_by_reason_code_and_limit():
    result = query_replay_certification_registry(
        sample_registry(),
        reason_code="WARNING_SIGNALS_PRESENT",
        limit=1,
    )

    assert result.match_count == 1
    assert result.matches[0].registry_id == "rec-2"
    assert result.matches[0].status == "review"


def test_empty_query_is_safe_read_only():
    result = query_replay_certification_registry(sample_registry(), status="missing")

    assert result.status == "empty"
    assert result.match_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_query_by_registry_id()
    test_query_by_level_and_score_range()
    test_query_by_reason_code_and_limit()
    test_empty_query_is_safe_read_only()

    print("[PASS] OI-204 Universal Market Adapter Replay Certification Registry Query Engine")
    print(query_replay_certification_registry(sample_registry(), certified=True).to_dict())
'''


def ensure_package() -> None:
    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text("", encoding="utf-8")


def update_init() -> None:
    export_line = (
        "from .universal_market_adapter_replay_certification_registry_query_engine import "
        "UniversalMarketAdapterReplayCertificationRegistryQueryEngine, "
        "query_replay_certification_registry\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-204 INSTALLER")
    print(" Universal Market Adapter Replay Certification Registry Query Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-204 installed")
    print()
    print("Run:")
    print("py test_oi_204_universal_market_adapter_replay_certification_registry_query_engine.py")


if __name__ == "__main__":
    main()