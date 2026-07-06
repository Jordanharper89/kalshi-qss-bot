from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2" / "oracle_intelligence"

MODULE = PKG / "universal_market_adapter_replay_certification_registry_analytics_engine.py"
TEST = ROOT / "test_oi_206_universal_market_adapter_replay_certification_registry_analytics_engine.py"
INIT = PKG / "__init__.py"

MODULE_CODE = r'''
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Mapping, Tuple

ENGINE_ID = "OI-206"
ENGINE_NAME = "Oracle Universal Market Adapter Replay Certification Registry Analytics Engine"
ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ReplayCertificationRegistryAnalyticsFinding:
    finding_id: str
    severity: str
    title: str
    detail: str
    recommendation: str
    reason_codes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        return data


@dataclass(frozen=True)
class ReplayCertificationRegistryAnalyticsResult:
    engine_id: str
    engine_name: str
    engine_version: str
    generated_at: str
    status: str
    input_count: int
    analyzed_count: int
    score_summary: Dict[str, Any]
    level_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    reason_code_distribution: Dict[str, int]
    findings: Tuple[ReplayCertificationRegistryAnalyticsFinding, ...]
    telemetry: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "generated_at": self.generated_at,
            "status": self.status,
            "input_count": self.input_count,
            "analyzed_count": self.analyzed_count,
            "score_summary": dict(self.score_summary),
            "level_distribution": dict(self.level_distribution),
            "status_distribution": dict(self.status_distribution),
            "source_distribution": dict(self.source_distribution),
            "reason_code_distribution": dict(self.reason_code_distribution),
            "findings": [finding.to_dict() for finding in self.findings],
            "telemetry": dict(self.telemetry),
            "explanation": self.explanation,
        }


class UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine:
    def analyze(self, registry_or_filter_result: Any) -> ReplayCertificationRegistryAnalyticsResult:
        generated_at = datetime.now(timezone.utc).isoformat()
        raw_records = self._extract_records(registry_or_filter_result)
        records = [self._normalize(self._to_mapping(item)) for item in raw_records]
        records = [record for record in records if record]

        score_summary = self._score_summary(records)
        level_distribution = self._distribution(records, "certification_level")
        status_distribution = self._distribution(records, "status")
        source_distribution = self._distribution(records, "source_engine_id")
        reason_code_distribution = self._reason_distribution(records)
        findings = self._findings(records, score_summary, level_distribution, status_distribution, reason_code_distribution)

        if not records:
            status = "empty"
        elif any(finding.severity == "warning" for finding in findings):
            status = "review"
        else:
            status = "ok"

        return ReplayCertificationRegistryAnalyticsResult(
            engine_id=ENGINE_ID,
            engine_name=ENGINE_NAME,
            engine_version=ENGINE_VERSION,
            generated_at=generated_at,
            status=status,
            input_count=len(raw_records),
            analyzed_count=len(records),
            score_summary=score_summary,
            level_distribution=level_distribution,
            status_distribution=status_distribution,
            source_distribution=source_distribution,
            reason_code_distribution=reason_code_distribution,
            findings=tuple(findings),
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
                "canonical_input": "ReplayCertificationRegistryResult or ReplayCertificationRegistryFilterResult compatible",
                "canonical_output": "ReplayCertificationRegistryAnalyticsResult",
                "analytics_is_read_only": True,
                "input_count": len(raw_records),
                "analyzed_count": len(records),
                "explainability": True,
                "replayability": True,
            },
            explanation=(
                f"Analyzed {len(records)} replay certification registry record(s). "
                "Oracle analytics are read-only and advisory; Q Series remains the only execution engine."
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
        if not data:
            return {}
        reason_codes = data.get("reason_codes", [])
        if isinstance(reason_codes, str):
            reason_codes = [reason_codes]
        elif not isinstance(reason_codes, Iterable):
            reason_codes = []
        return {
            "registry_id": str(data.get("registry_id", "")),
            "source_engine_id": str(data.get("source_engine_id", data.get("engine_id", "unknown"))),
            "certified": bool(data.get("certified", False)),
            "certification_level": str(data.get("certification_level", "unknown")),
            "status": str(data.get("status", "unknown")),
            "intelligence_score": self._clamp01(self._number(data, "intelligence_score", default=0.0)),
            "signal_count": int(self._number(data, "signal_count", default=0.0)),
            "decision_count": int(self._number(data, "decision_count", default=0.0)),
            "reason_codes": [str(code) for code in reason_codes if str(code).strip()],
        }

    def _score_summary(self, records: List[Mapping[str, Any]]) -> Dict[str, Any]:
        values = [float(record["intelligence_score"]) for record in records]
        if not values:
            return {"count": 0, "min": None, "max": None, "mean": None, "median": None, "spread": None}
        return {
            "count": len(values),
            "min": round(min(values), 6),
            "max": round(max(values), 6),
            "mean": round(mean(values), 6),
            "median": round(median(values), 6),
            "spread": round(max(values) - min(values), 6),
        }

    def _distribution(self, records: List[Mapping[str, Any]], key: str) -> Dict[str, int]:
        output: Dict[str, int] = {}
        for record in records:
            name = str(record.get(key, "unknown"))
            output[name] = output.get(name, 0) + 1
        return dict(sorted(output.items(), key=lambda item: (-item[1], item[0])))

    def _reason_distribution(self, records: List[Mapping[str, Any]]) -> Dict[str, int]:
        output: Dict[str, int] = {}
        for record in records:
            for code in record.get("reason_codes", []):
                output[code] = output.get(code, 0) + 1
        return dict(sorted(output.items(), key=lambda item: (-item[1], item[0])))

    def _findings(
        self,
        records: List[Mapping[str, Any]],
        score_summary: Mapping[str, Any],
        level_distribution: Mapping[str, int],
        status_distribution: Mapping[str, int],
        reason_distribution: Mapping[str, int],
    ) -> List[ReplayCertificationRegistryAnalyticsFinding]:
        findings: List[ReplayCertificationRegistryAnalyticsFinding] = []
        if not records:
            return [
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_EMPTY_REGISTRY_ANALYTICS",
                    severity="info",
                    title="No registry records available for analytics.",
                    detail="The analytics engine received no usable registry or filter records.",
                    recommendation="Confirm OI-203 or OI-205 produced records before registry analytics are requested.",
                    reason_codes=("NO_RECORDS", "READ_ONLY_ANALYTICS"),
                )
            ]

        avg_score = float(score_summary.get("mean") or 0.0)
        certified_count = sum(1 for record in records if record.get("certified") is True)
        certified_pct = (certified_count / len(records)) * 100.0

        if avg_score >= 0.75:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_STRONG_AVERAGE_CERTIFICATION_SCORE",
                    severity="positive",
                    title="Strong average certification score.",
                    detail=f"Average certification intelligence score is {avg_score:.4f}.",
                    recommendation="Promote this registry cohort to downstream read-only Oracle intelligence review.",
                    reason_codes=("STRONG_AVERAGE_SCORE", "ORACLE_REVIEW_CANDIDATE"),
                )
            )
        elif avg_score < 0.50:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_WEAK_AVERAGE_CERTIFICATION_SCORE",
                    severity="warning",
                    title="Weak average certification score.",
                    detail=f"Average certification intelligence score is {avg_score:.4f}.",
                    recommendation="Hold this registry cohort for additional replay review.",
                    reason_codes=("WEAK_AVERAGE_SCORE", "REQUIRES_REVIEW"),
                )
            )

        if certified_pct >= 50.0:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_CERTIFIED_COHORT_MAJORITY",
                    severity="positive",
                    title="Certified records are the majority of the cohort.",
                    detail=f"{certified_pct:.2f}% of analyzed registry records are certified.",
                    recommendation="Continue monitoring certification quality and reason-code coverage.",
                    reason_codes=("CERTIFIED_MAJORITY",),
                )
            )
        else:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_CERTIFIED_COHORT_MINORITY",
                    severity="warning",
                    title="Certified records are not the majority of the cohort.",
                    detail=f"{certified_pct:.2f}% of analyzed registry records are certified.",
                    recommendation="Review rejected or review-required registry records before downstream promotion.",
                    reason_codes=("CERTIFIED_MINORITY",),
                )
            )

        if "review" in status_distribution:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_REVIEW_STATUS_PRESENT",
                    severity="info",
                    title="Review-status registry records are present.",
                    detail=f"{status_distribution['review']} registry record(s) require review.",
                    recommendation="Route review records to downstream read-only Oracle inspection.",
                    reason_codes=("REVIEW_STATUS_PRESENT",),
                )
            )

        if not reason_distribution:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_REASON_CODE_GAP",
                    severity="warning",
                    title="Reason-code coverage gap.",
                    detail="No reason codes were found in the analyzed registry cohort.",
                    recommendation="Require upstream certification reason codes before registry promotion.",
                    reason_codes=("REASON_CODE_GAP", "EXPLAINABILITY_GAP"),
                )
            )

        if not findings:
            findings.append(
                ReplayCertificationRegistryAnalyticsFinding(
                    finding_id="OI206_STABLE_REGISTRY_ANALYTICS_BASELINE",
                    severity="info",
                    title="Stable registry analytics baseline.",
                    detail="No severe registry analytics issues were detected.",
                    recommendation="Continue read-only replay certification registry monitoring.",
                    reason_codes=("STABLE_BASELINE",),
                )
            )
        return findings

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


def analyze_replay_certification_registry(payload: Any) -> ReplayCertificationRegistryAnalyticsResult:
    return UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine().analyze(payload)


__all__ = [
    "ENGINE_ID",
    "ENGINE_NAME",
    "ENGINE_VERSION",
    "ReplayCertificationRegistryAnalyticsFinding",
    "ReplayCertificationRegistryAnalyticsResult",
    "UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine",
    "analyze_replay_certification_registry",
]
'''

TEST_CODE = r'''
from qseries_v2.oracle_intelligence.universal_market_adapter_replay_certification_registry_analytics_engine import (
    ENGINE_ID,
    UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine,
    analyze_replay_certification_registry,
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
        },
    ]


def test_analyzes_registry_records():
    result = UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine().analyze(
        {"records": sample_records()}
    )

    assert result.engine_id == ENGINE_ID
    assert result.input_count == 3
    assert result.analyzed_count == 3
    assert result.score_summary["mean"] == 0.64
    assert result.level_distribution["certified"] == 1
    assert result.level_distribution["strong_certified"] == 1
    assert result.status_distribution["review"] == 1
    assert result.reason_code_distribution["READ_ONLY_ORACLE_CERTIFICATION"] == 2
    assert result.telemetry["read_only"] is True
    assert result.telemetry["execution_owner"] == "Q Series"
    assert result.telemetry["does_not_execute"] is True


def test_analyzes_filter_matches_payload():
    result = analyze_replay_certification_registry({"matches": sample_records()[:2]})

    assert result.status == "ok"
    assert result.input_count == 2
    assert result.analyzed_count == 2
    assert result.score_summary["mean"] == 0.76
    assert any(f.finding_id == "OI206_STRONG_AVERAGE_CERTIFICATION_SCORE" for f in result.findings)


def test_empty_input_is_safe_read_only():
    result = analyze_replay_certification_registry([])

    assert result.status == "empty"
    assert result.input_count == 0
    assert result.analyzed_count == 0
    assert result.telemetry["read_only"] is True
    assert result.telemetry["does_not_route_orders"] is True
    assert result.telemetry["does_not_manage_positions"] is True
    assert result.findings[0].finding_id == "OI206_EMPTY_REGISTRY_ANALYTICS"


if __name__ == "__main__":
    test_analyzes_registry_records()
    test_analyzes_filter_matches_payload()
    test_empty_input_is_safe_read_only()

    print("[PASS] OI-206 Universal Market Adapter Replay Certification Registry Analytics Engine")
    print(analyze_replay_certification_registry({"records": sample_records()}).to_dict())
'''


def ensure_package() -> None:
    PKG.mkdir(parents=True, exist_ok=True)
    if not INIT.exists():
        INIT.write_text("", encoding="utf-8")


def update_init() -> None:
    export_line = (
        "from .universal_market_adapter_replay_certification_registry_analytics_engine import "
        "UniversalMarketAdapterReplayCertificationRegistryAnalyticsEngine, "
        "analyze_replay_certification_registry\n"
    )

    existing = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if export_line not in existing:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        existing += export_line
        INIT.write_text(existing, encoding="utf-8")


def main() -> None:
    print("========================================")
    print(" OI-206 INSTALLER")
    print(" Universal Market Adapter Replay Certification Registry Analytics Engine")
    print("========================================")

    ensure_package()

    MODULE.write_text(MODULE_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {MODULE}")

    TEST.write_text(TEST_CODE.strip() + "\n", encoding="utf-8")
    print(f"[OK] Wrote {TEST}")

    update_init()
    print(f"[OK] Updated {INIT}")

    print()
    print("[DONE] OI-206 installed")
    print()
    print("Run:")
    print("py test_oi_206_universal_market_adapter_replay_certification_registry_analytics_engine.py")


if __name__ == "__main__":
    main()