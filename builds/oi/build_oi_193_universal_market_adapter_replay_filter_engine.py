from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"
PKG.mkdir(parents=True, exist_ok=True)

MODULE = PKG / "universal_market_adapter_replay_filter_engine.py"
TEST = ROOT / "test_oi_193_universal_market_adapter_replay_filter_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
"""
OI-193 — Oracle Universal Market Adapter Replay Filter Engine

Read-only replay filtering layer for replay registry/search artifacts.

This engine refines replay search results without mutating registry state,
executing trades, routing orders, submitting orders, or managing positions.
Oracle remains the brain. Q Series remains the hand.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
import json


READ_ONLY_GUARDRAILS = {
    "oracle_read_only": True,
    "executes_trades": False,
    "routes_orders": False,
    "submits_orders": False,
    "manages_positions": False,
    "execution_owner": "Q_SERIES_ONLY",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, Mapping):
            return dict(converted)
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {"value": value}


def _safe_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _field(data: Mapping[str, Any], key: str, default: Any = None) -> Any:
    if key in data:
        return data.get(key)
    telemetry = _safe_dict(data.get("telemetry"))
    if key in telemetry:
        return telemetry.get(key)
    lineage = _safe_dict(data.get("lineage"))
    if key in lineage:
        return lineage.get(key)
    metadata = _safe_dict(data.get("metadata"))
    if key in metadata:
        return metadata.get(key)
    return default


@dataclass(frozen=True)
class ReplayFilterCriteria:
    adapter_id: Optional[str] = None
    market_type: Optional[str] = None
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    market: Optional[str] = None
    manifest_id: Optional[str] = None
    certification_id: Optional[str] = None
    validation_id: Optional[str] = None
    registration_id: Optional[str] = None
    certification_level: Optional[str] = None
    status: Optional[str] = None
    certified: Optional[bool] = None
    passed: Optional[bool] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None
    metadata_contains: Dict[str, Any] = field(default_factory=dict)
    required_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayFilterDecision:
    record_id: str
    included: bool
    reasons: List[str]
    rejected_by: List[str]
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayFilterResult:
    filter_id: str
    created_at: str
    oracle_instance_id: str
    module_id: str
    module_name: str
    input_count: int
    output_count: int
    rejected_count: int
    criteria_hash: str
    result_hash: str
    read_only_guardrails: Dict[str, Any]
    results: List[Any]
    decisions: List[ReplayFilterDecision]
    telemetry: Dict[str, Any]
    explainability: Dict[str, Any]

    @property
    def passed(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data


class UniversalMarketAdapterReplayFilterEngine:
    """
    Filters replay search/registry artifacts using canonical replay metadata.

    The engine is pure and read-only. It returns filtered views and explanatory
    decisions without altering source records.
    """

    module_id = "OI-193"
    module_name = "Oracle Universal Market Adapter Replay Filter Engine"

    def __init__(self, oracle_instance_id: str = "oracle.default") -> None:
        self.oracle_instance_id = oracle_instance_id
        self._history: List[ReplayFilterResult] = []

    def filter_records(
        self,
        records: Iterable[Any],
        criteria: Optional[ReplayFilterCriteria | Mapping[str, Any]] = None,
        *,
        filter_context: Optional[Mapping[str, Any]] = None,
    ) -> ReplayFilterResult:
        criteria_obj = self._criteria(criteria)
        context = _safe_dict(filter_context)
        source_records = list(records or [])

        included: List[Any] = []
        decisions: List[ReplayFilterDecision] = []

        for record in source_records:
            data = _safe_dict(record)
            decision = self._evaluate_record(data, criteria_obj)
            decisions.append(decision)
            if decision.included:
                included.append(record)

        criteria_hash = _hash(criteria_obj.to_dict())
        result_payload = {
            "criteria": criteria_obj.to_dict(),
            "included_ids": [decision.record_id for decision in decisions if decision.included],
            "decisions": [decision.to_dict() for decision in decisions],
            "context": context,
        }
        result_hash = _hash(result_payload)

        result = ReplayFilterResult(
            filter_id="oi193.filter." + result_hash[:24],
            created_at=_utc_now(),
            oracle_instance_id=self.oracle_instance_id,
            module_id=self.module_id,
            module_name=self.module_name,
            input_count=len(source_records),
            output_count=len(included),
            rejected_count=len(source_records) - len(included),
            criteria_hash=criteria_hash,
            result_hash=result_hash,
            read_only_guardrails=dict(READ_ONLY_GUARDRAILS),
            results=included,
            decisions=decisions,
            telemetry={
                "module_id": self.module_id,
                "module_name": self.module_name,
                "oracle_instance_id": self.oracle_instance_id,
                "input_count": len(source_records),
                "output_count": len(included),
                "rejected_count": len(source_records) - len(included),
                "criteria_hash": criteria_hash,
                "result_hash": result_hash,
                "context_hash": _hash(context),
            },
            explainability={
                "purpose": "Refine replay search or registry results using deterministic read-only criteria.",
                "read_only_reason": "Filtering returns a derived view only and does not mutate replay, registry, market, or execution state.",
                "execution_boundary": "Q Series remains the only execution engine.",
                "filter_dimensions": [
                    "adapter_id",
                    "market_type",
                    "exchange",
                    "symbol",
                    "market",
                    "manifest_id",
                    "certification_id",
                    "validation_id",
                    "registration_id",
                    "certification_level",
                    "status",
                    "certified",
                    "passed",
                    "confidence",
                    "created_at",
                    "metadata",
                    "tags",
                ],
                "criteria": criteria_obj.to_dict(),
            },
        )
        self._history.append(result)
        return result

    def chain_filter(
        self,
        prior_result: ReplayFilterResult | Mapping[str, Any],
        criteria: Optional[ReplayFilterCriteria | Mapping[str, Any]] = None,
        *,
        filter_context: Optional[Mapping[str, Any]] = None,
    ) -> ReplayFilterResult:
        data = _safe_dict(prior_result)
        records = data.get("results") or []
        return self.filter_records(records, criteria, filter_context=filter_context)

    def history(self) -> List[ReplayFilterResult]:
        return list(self._history)

    def latest_result(self) -> Optional[ReplayFilterResult]:
        return self._history[-1] if self._history else None

    def telemetry_snapshot(self) -> Dict[str, Any]:
        latest = self.latest_result()
        return {
            "module_id": self.module_id,
            "module_name": self.module_name,
            "oracle_instance_id": self.oracle_instance_id,
            "filter_count": len(self._history),
            "latest_filter_id": latest.filter_id if latest else None,
            "latest_output_count": latest.output_count if latest else None,
            "read_only_guardrails": dict(READ_ONLY_GUARDRAILS),
        }

    def _criteria(self, value: Optional[ReplayFilterCriteria | Mapping[str, Any]]) -> ReplayFilterCriteria:
        if isinstance(value, ReplayFilterCriteria):
            return value
        data = _safe_dict(value)
        known = {field_name for field_name in ReplayFilterCriteria.__dataclass_fields__.keys()}
        return ReplayFilterCriteria(**{key: data.get(key) for key in known if key in data})

    def _evaluate_record(self, data: Dict[str, Any], criteria: ReplayFilterCriteria) -> ReplayFilterDecision:
        reasons: List[str] = []
        rejected_by: List[str] = []

        record_id = str(
            _field(data, "registration_id")
            or _field(data, "replay_id")
            or _field(data, "certification_id")
            or _field(data, "manifest_id")
            or _field(data, "audit_id")
            or _hash(data)[:24]
        )

        def exact(attr: str, expected: Optional[str], field_name: Optional[str] = None) -> None:
            if expected is None:
                return
            actual = _field(data, field_name or attr)
            if _lower(actual) == _lower(expected):
                reasons.append(f"{attr} matched")
            else:
                rejected_by.append(f"{attr} mismatch")

        exact("adapter_id", criteria.adapter_id)
        exact("market_type", criteria.market_type)
        exact("exchange", criteria.exchange)
        exact("symbol", criteria.symbol)
        exact("market", criteria.market)
        exact("manifest_id", criteria.manifest_id)
        exact("certification_id", criteria.certification_id)
        exact("validation_id", criteria.validation_id)
        exact("registration_id", criteria.registration_id)
        exact("certification_level", criteria.certification_level)
        exact("status", criteria.status)

        if criteria.certified is not None:
            actual = bool(_field(data, "certified", False))
            if actual is criteria.certified:
                reasons.append("certified matched")
            else:
                rejected_by.append("certified mismatch")

        if criteria.passed is not None:
            actual = bool(_field(data, "passed", False))
            if actual is criteria.passed:
                reasons.append("passed matched")
            else:
                rejected_by.append("passed mismatch")

        confidence = _field(data, "confidence")
        if confidence is not None:
            try:
                confidence_float = float(confidence)
            except (TypeError, ValueError):
                confidence_float = None
        else:
            confidence_float = None

        if criteria.min_confidence is not None:
            if confidence_float is not None and confidence_float >= float(criteria.min_confidence):
                reasons.append("min_confidence matched")
            else:
                rejected_by.append("below min_confidence")

        if criteria.max_confidence is not None:
            if confidence_float is not None and confidence_float <= float(criteria.max_confidence):
                reasons.append("max_confidence matched")
            else:
                rejected_by.append("above max_confidence")

        created_at = str(_field(data, "created_at") or "")
        if criteria.created_after is not None:
            if created_at >= str(criteria.created_after):
                reasons.append("created_after matched")
            else:
                rejected_by.append("before created_after")

        if criteria.created_before is not None:
            if created_at <= str(criteria.created_before):
                reasons.append("created_before matched")
            else:
                rejected_by.append("after created_before")

        metadata = _safe_dict(data.get("metadata"))
        telemetry = _safe_dict(data.get("telemetry"))
        lineage = _safe_dict(data.get("lineage"))
        combined = {**metadata, **telemetry, **lineage, **data}

        for key, expected in criteria.metadata_contains.items():
            if _lower(combined.get(key)) == _lower(expected):
                reasons.append(f"metadata.{key} matched")
            else:
                rejected_by.append(f"metadata.{key} mismatch")

        if criteria.required_tags:
            record_tags = {str(tag).lower() for tag in _safe_list(_field(data, "tags"))}
            required_tags = {str(tag).lower() for tag in criteria.required_tags}
            missing = sorted(required_tags - record_tags)
            if not missing:
                reasons.append("required_tags matched")
            else:
                rejected_by.append("required_tags missing")

        if not reasons and not rejected_by:
            reasons.append("no criteria supplied; included by default")

        return ReplayFilterDecision(
            record_id=record_id,
            included=not rejected_by,
            reasons=reasons,
            rejected_by=rejected_by,
            evidence={
                "adapter_id": _field(data, "adapter_id"),
                "market_type": _field(data, "market_type"),
                "symbol": _field(data, "symbol"),
                "manifest_id": _field(data, "manifest_id"),
                "certification_id": _field(data, "certification_id"),
                "registration_id": _field(data, "registration_id"),
                "status": _field(data, "status"),
                "certified": _field(data, "certified"),
            },
        )


def create_replay_filter_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayFilterEngine:
    return UniversalMarketAdapterReplayFilterEngine(oracle_instance_id=oracle_instance_id)


def create_universal_market_adapter_replay_filter_engine(oracle_instance_id: str = "oracle.default") -> UniversalMarketAdapterReplayFilterEngine:
    return create_replay_filter_engine(oracle_instance_id)


__all__ = [
    "READ_ONLY_GUARDRAILS",
    "ReplayFilterCriteria",
    "ReplayFilterDecision",
    "ReplayFilterResult",
    "UniversalMarketAdapterReplayFilterEngine",
    "create_replay_filter_engine",
    "create_universal_market_adapter_replay_filter_engine",
]
'''.lstrip()

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_filter_engine import (
    READ_ONLY_GUARDRAILS,
    ReplayFilterCriteria,
    UniversalMarketAdapterReplayFilterEngine,
    create_replay_filter_engine,
)


def test_oi_193_universal_market_adapter_replay_filter_engine():
    engine = create_replay_filter_engine("oracle.test")

    records = [
        {
            "registration_id": "reg-001",
            "certification_id": "cert-001",
            "manifest_id": "man-001",
            "validation_id": "val-001",
            "adapter_id": "adp.kalshi",
            "market_type": "prediction_market",
            "exchange": "kalshi",
            "symbol": "KXTEST",
            "market": "TEST_MARKET",
            "certification_level": "certified",
            "status": "registered",
            "certified": True,
            "passed": True,
            "confidence": 0.92,
            "created_at": "2026-01-01T00:00:00+00:00",
            "tags": ["replay", "gate2"],
            "metadata": {"sector": "macro"},
        },
        {
            "registration_id": "reg-002",
            "certification_id": "cert-002",
            "manifest_id": "man-002",
            "validation_id": "val-002",
            "adapter_id": "adp.polymarket",
            "market_type": "prediction_market",
            "exchange": "polymarket",
            "symbol": "POLYTEST",
            "market": "TEST_MARKET_2",
            "certification_level": "not_certified",
            "status": "rejected",
            "certified": False,
            "passed": False,
            "confidence": 0.41,
            "created_at": "2026-01-02T00:00:00+00:00",
            "tags": ["replay"],
            "metadata": {"sector": "sports"},
        },
        {
            "registration_id": "reg-003",
            "certification_id": "cert-003",
            "manifest_id": "man-003",
            "validation_id": "val-003",
            "adapter_id": "adp.kalshi",
            "market_type": "prediction_market",
            "exchange": "kalshi",
            "symbol": "KXOTHER",
            "market": "OTHER_MARKET",
            "certification_level": "certified_with_warnings",
            "status": "registered",
            "certified": True,
            "passed": True,
            "confidence": 0.74,
            "created_at": "2026-01-03T00:00:00+00:00",
            "tags": ["replay", "warning"],
            "metadata": {"sector": "macro"},
        },
    ]

    result = engine.filter_records(records, ReplayFilterCriteria(adapter_id="adp.kalshi", certified=True))
    assert result.module_id == "OI-193"
    assert result.input_count == 3
    assert result.output_count == 2
    assert result.rejected_count == 1
    assert result.passed is True
    assert result.read_only_guardrails == READ_ONLY_GUARDRAILS
    assert len(result.criteria_hash) == 64
    assert len(result.result_hash) == 64
    assert all(item["adapter_id"] == "adp.kalshi" for item in result.results)

    high_confidence = engine.chain_filter(result, {"min_confidence": 0.9})
    assert high_confidence.output_count == 1
    assert high_confidence.results[0]["registration_id"] == "reg-001"

    metadata_filtered = engine.filter_records(records, {
        "metadata_contains": {"sector": "macro"},
        "required_tags": ["replay"],
    })
    assert metadata_filtered.output_count == 2

    exact = engine.filter_records(records, {"registration_id": "reg-002", "passed": False})
    assert exact.output_count == 1
    assert exact.results[0]["registration_id"] == "reg-002"

    date_filtered = engine.filter_records(records, {
        "created_after": "2026-01-02T00:00:00+00:00",
        "created_before": "2026-01-03T00:00:00+00:00",
    })
    assert date_filtered.output_count == 2

    no_criteria = engine.filter_records(records)
    assert no_criteria.output_count == 3
    assert len(no_criteria.decisions) == 3

    snapshot = engine.telemetry_snapshot()
    assert snapshot["module_id"] == "OI-193"
    assert snapshot["filter_count"] == 6
    assert snapshot["read_only_guardrails"] == READ_ONLY_GUARDRAILS

    direct_engine = UniversalMarketAdapterReplayFilterEngine("oracle.direct")
    assert direct_engine.telemetry_snapshot()["filter_count"] == 0


if __name__ == "__main__":
    test_oi_193_universal_market_adapter_replay_filter_engine()
    print("[PASS] OI-193 Universal Market Adapter Replay Filter Engine")
'''.lstrip()

MODULE.write_text(MODULE_CODE, encoding="utf-8")
TEST.write_text(TEST_CODE, encoding="utf-8")

if INIT.exists():
    init_text = INIT.read_text(encoding="utf-8")
else:
    init_text = ""

import_line = "from .universal_market_adapter_replay_filter_engine import UniversalMarketAdapterReplayFilterEngine, ReplayFilterCriteria, create_replay_filter_engine\n"
if import_line not in init_text:
    init_text += ("\n" if init_text and not init_text.endswith("\n") else "") + import_line

INIT.write_text(init_text, encoding="utf-8")

print("========================================")
print(" OI-193 INSTALLER")
print(" Universal Market Adapter Replay Filter Engine")
print("========================================")
print(f"[OK] Wrote {MODULE}")
print(f"[OK] Wrote {TEST}")
print(f"[OK] Updated {INIT}")
print()
print("[DONE] OI-193 installed")
print()
print("Run:")
print("py test_oi_193_universal_market_adapter_replay_filter_engine.py")
