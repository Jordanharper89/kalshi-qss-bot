from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_certification_registry_filter_engine.py"
TEST = ROOT / "test_oi_205_universal_market_adapter_replay_certification_registry_filter_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
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
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_filter_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryFilterEngine,
    filter_replay_certification_registry,
)


def sample_records():
    return [
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
            "certified": True,
            "certification_level": "strong_certified",
            "status": "certified",
            "intelligence_score": 0.88,
            "signal_count": 3,
            "decision_count": 2,
            "reason_codes": ["READ_ONLY_ORACLE_CERTIFICATION", "STRONG_INTELLIGENCE_SCORE"],
            "explanation": "Strong certified sample.",
        },
        {
            "registry_id": "rec-3",
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
    ]


def test_filters_by_min_score_and_certified():
    result = UniversalMarketAdapterReplayCertificationRegistryFilterEngine().filter(
        {"records": sample_records()},
        min_intelligence_score=0.60,
        certified=True,
    )

    assert result.engine_id == ENGINE_ID
    assert result.status == "ok"
    assert result.input_count == 3
    assert result.filtered_count == 2
    assert result.matches[0].registry_id == "rec-2"
    assert result.matches[1].registry_id == "rec-1"
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_filters_by_required_reason_code():
    result = filter_replay_certification_registry(
        sample_records(),
        required_reason_codes=["WARNING_SIGNALS_PRESENT"],
    )

    assert result.filtered_count == 1
    assert result.matches[0].registry_id == "rec-3"
    assert result.matches[0].status == "review"


def test_filters_by_min_certification_level_and_limit():
    result = filter_replay_certification_registry(
        sample_records(),
        min_certification_level="certified",
        sort_by="certification_level",
        descending=True,
        limit=1,
    )

    assert result.filtered_count == 1
    assert result.matches[0].registry_id == "rec-2"
    assert result.matches[0].certification_level == "strong_certified"


def test_empty_filter_result_is_safe_read_only():
    result = filter_replay_certification_registry(
        sample_records(),
        min_intelligence_score=0.99,
    )

    assert result.status == "empty"
    assert result.filtered_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True


if __name__ == "__main__":
    test_filters_by_min_score_and_certified()
    test_filters_by_required_reason_code()
    test_filters_by_min_certification_level_and_limit()
    test_empty_filter_result_is_safe_read_only()

    print("[PASS] OI-205 Universal Market Adapter Replay Certification Registry Filter Engine")
    print(filter_replay_certification_registry(sample_records(), min_intelligence_score=0.60).to_dict())
'''


def ensure_package() -> None:
    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text("", encoding="utf-8")


def update_init() -> None:
    export_line = (
        "from .universal_market_adapter_replay_certification_registry_filter_engine import "
        "UniversalMarketAdapterReplayCertificationRegistryFilterEngine, "
        "filter_replay_certification_registry\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-205 INSTALLER")
    print(" Universal Market Adapter Replay Certification Registry Filter Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-205 installed")
    print()
    print("Run:")
    print("py test_oi_205_universal_market_adapter_replay_certification_registry_filter_engine.py")


if __name__ == "__main__":
    main()