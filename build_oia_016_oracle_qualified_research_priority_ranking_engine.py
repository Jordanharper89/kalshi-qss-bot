from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


MODULE = r'''"""
OIA-016
Oracle Qualified Research Priority Ranking Engine

Consumes the immutable OIA-015 ranking-eligibility report and produces a
deterministic research-only priority ranking for qualified analytical
components.

This module:

- verifies the complete OIA-015 report and decision hash chain;
- admits only OIA-015 eligible decisions into the qualified ranking;
- computes deterministic, policy-versioned research priority scores;
- assigns stable ordinal ranks with explicit tie-breaking;
- preserves immutable source lineage;
- persists content-addressed ranking artifacts atomically.

This module never creates trading signals, alerts, recommendations, execution
instructions, or Q Series handoffs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_forward_shadow_ranking_eligibility_gate import (
    DEFAULT_ELIGIBILITY_DIRECTORY,
    ELIGIBLE,
    stable_hash as eligibility_stable_hash,
)


SCHEMA_VERSION = "OIA-016"
ENGINE_ID = "OIA-016"

RANKING_POLICY_ID = "oracle.qualified-research-priority.v1"

QUALIFIED = "qualified"
NOT_QUALIFIED = "not_qualified"

READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
RANKING_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_RANKING_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_priority_ranking"
)

_QUANT = Decimal("0.00000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_HALF = Decimal("0.5")


class QualifiedResearchPriorityRankingError(RuntimeError):
    """Base OIA-016 error."""


class QualifiedResearchPriorityRankingInvariantError(
    QualifiedResearchPriorityRankingError
):
    """Raised when an immutable upstream or local contract is invalid."""


def _aware_utc(value: datetime, name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchPriorityRankingInvariantError(
            f"{name} must be timezone-aware."
        )
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise QualifiedResearchPriorityRankingInvariantError(
            f"{name} must be a finite decimal."
        ) from exc

    if not result.is_finite():
        raise QualifiedResearchPriorityRankingInvariantError(
            f"{name} must be a finite decimal."
        )
    return result


def _bounded_probability(value: Any, name: str) -> Decimal:
    result = _decimal(value, name)
    if result < _ZERO or result > _ONE:
        raise QualifiedResearchPriorityRankingInvariantError(
            f"{name} must be between zero and one."
        )
    return result


def _non_negative(value: Any, name: str) -> Decimal:
    result = _decimal(value, name)
    if result < _ZERO:
        raise QualifiedResearchPriorityRankingInvariantError(
            f"{name} must be non-negative."
        )
    return result


def _fmt(value: Decimal) -> str:
    return format(
        value.quantize(_QUANT, rounding=ROUND_HALF_EVEN),
        "f",
    )


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    rendered = (
        json.dumps(
            _canonical(payload),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(handle.name)

    try:
        with handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


@dataclass(frozen=True)
class OracleQualifiedResearchPriorityRecord:
    rank: int
    qualification_status: str
    dimension: str
    key: str
    decisive_count: int
    empirical_win_rate: str
    confidence_lower_bound: str
    confidence_upper_bound: str
    calibration_error: str
    brier_score: str
    reliability: str
    resolution: str
    evidence_sufficiency: str
    sample_sufficiency: str
    confidence_edge: str
    calibration_quality: str
    reliability_quality: str
    resolution_quality: str
    sample_strength: str
    priority_score: str
    ranking_policy_id: str
    reason_codes: tuple[str, ...]
    source_eligibility_decision_hash: str
    record_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleQualifiedResearchPriorityRankingReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    eligibility_directory: str
    ranking_directory: str
    ranking_policy_id: str
    source_decision_count: int
    qualified_decision_count: int
    excluded_decision_count: int
    ranking_count: int
    rankings: tuple[OracleQualifiedResearchPriorityRecord, ...]
    excluded_decision_hashes: tuple[str, ...]
    source_eligibility_report_hash: str
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    ranking_artifact_persistence_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleQualifiedResearchPriorityRankingEngine:
    """
    Deterministic research ranking over OIA-015 eligible components.

    Ranking policy v1 weights:

    - 35% confidence lower-bound edge above chance;
    - 20% empirical win-rate edge above chance;
    - 15% calibration quality;
    - 10% reliability quality;
    - 10% resolution quality;
    - 10% sample-strength quality.

    All values are deterministic Decimal calculations. The output is sorted by
    descending priority score, then descending decisive count, then stable
    lexical component identity.
    """

    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    source_mutation_allowed = False
    ranking_artifact_persistence_allowed = True

    def __init__(
        self,
        *,
        eligibility_directory: Path | str = DEFAULT_ELIGIBILITY_DIRECTORY,
        ranking_directory: Path | str = DEFAULT_RANKING_DIRECTORY,
    ) -> None:
        self._eligibility_directory = Path(eligibility_directory)
        self._ranking_directory = Path(ranking_directory)

    def _load_eligibility_report(self) -> dict[str, Any]:
        path = self._eligibility_directory / "current.json"
        if not path.exists():
            raise QualifiedResearchPriorityRankingInvariantError(
                f"OIA-015 current eligibility report is missing: {path}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise QualifiedResearchPriorityRankingInvariantError(
                f"OIA-015 eligibility report is not valid JSON: {path}"
            ) from exc

        report_hash = payload.pop("report_hash", None)

        if (
            payload.get("schema_version") != "OIA-015"
            or payload.get("engine_id") != "OIA-015"
        ):
            raise QualifiedResearchPriorityRankingInvariantError(
                f"Unsupported OIA-015 eligibility report identity: {path}"
            )

        if report_hash != eligibility_stable_hash(payload):
            raise QualifiedResearchPriorityRankingInvariantError(
                f"OIA-015 eligibility report hash verification failed: {path}"
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchPriorityRankingInvariantError(
                "OIA-015 report must preserve read-only corpus semantics."
            )

        forbidden_true_fields = (
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "signals_allowed",
            "trading_recommendations_allowed",
            "source_mutation_allowed",
        )
        for field in forbidden_true_fields:
            if payload.get(field) is not False:
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"OIA-015 safety boundary mismatch: {field}."
                )

        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            raise QualifiedResearchPriorityRankingInvariantError(
                "OIA-015 decisions must be a list."
            )

        expected_count = int(payload.get("matched_component_count", -1))
        if expected_count != len(decisions):
            raise QualifiedResearchPriorityRankingInvariantError(
                "OIA-015 matched component count does not match decisions."
            )

        verified_decisions: list[dict[str, Any]] = []
        seen_identities: set[tuple[str, str]] = set()
        seen_hashes: set[str] = set()

        for index, raw_decision in enumerate(decisions):
            if not isinstance(raw_decision, dict):
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"OIA-015 decision {index} must be an object."
                )

            decision = dict(raw_decision)
            decision_hash = decision.pop("decision_hash", None)

            if decision_hash != eligibility_stable_hash(decision):
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"OIA-015 decision hash verification failed at index {index}."
                )

            identity = (
                str(decision.get("dimension", "")),
                str(decision.get("key", "")),
            )
            if not identity[0] or not identity[1]:
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"OIA-015 decision {index} has an empty identity."
                )
            if identity in seen_identities:
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"Duplicate OIA-015 decision identity: {identity!r}"
                )
            if not isinstance(decision_hash, str) or len(decision_hash) != 64:
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"Invalid OIA-015 decision hash at index {index}."
                )
            if decision_hash in seen_hashes:
                raise QualifiedResearchPriorityRankingInvariantError(
                    f"Duplicate OIA-015 decision hash: {decision_hash}"
                )

            seen_identities.add(identity)
            seen_hashes.add(decision_hash)
            decision["decision_hash"] = decision_hash
            verified_decisions.append(decision)

        calculated_eligible = sum(
            item.get("status") == ELIGIBLE
            for item in verified_decisions
        )
        if calculated_eligible != int(payload.get("eligible_count", -1)):
            raise QualifiedResearchPriorityRankingInvariantError(
                "OIA-015 eligible count does not match verified decisions."
            )

        payload["decisions"] = verified_decisions
        payload["report_hash"] = report_hash
        return payload

    @staticmethod
    def _sample_strength(
        decisive_count: int,
        evidence_sufficiency: str,
        sample_sufficiency: str,
    ) -> Decimal:
        count_strength = min(
            _ONE,
            Decimal(decisive_count) / Decimal("400"),
        )

        evidence_weights = {
            "insufficient": Decimal("0.00"),
            "provisional": Decimal("0.40"),
            "established": Decimal("0.75"),
            "strong": Decimal("1.00"),
        }
        sample_weights = {
            "insufficient": Decimal("0.00"),
            "provisional": Decimal("0.50"),
            "established": Decimal("1.00"),
        }

        evidence_strength = evidence_weights.get(
            evidence_sufficiency,
            Decimal("0.00"),
        )
        sample_sufficiency_strength = sample_weights.get(
            sample_sufficiency,
            Decimal("0.00"),
        )

        return (
            count_strength
            + evidence_strength
            + sample_sufficiency_strength
        ) / Decimal("3")

    @staticmethod
    def _quality_from_error(
        value: Decimal,
        normalization_ceiling: Decimal,
    ) -> Decimal:
        if normalization_ceiling <= _ZERO:
            raise QualifiedResearchPriorityRankingInvariantError(
                "normalization_ceiling must be positive."
            )
        return max(
            _ZERO,
            _ONE - min(_ONE, value / normalization_ceiling),
        )

    def _score_decision(
        self,
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        if decision.get("status") != ELIGIBLE:
            raise QualifiedResearchPriorityRankingInvariantError(
                "Only OIA-015 eligible decisions may be ranked."
            )

        decisive_count = int(decision["decisive_count"])
        if decisive_count < 0:
            raise QualifiedResearchPriorityRankingInvariantError(
                "decisive_count must be non-negative."
            )

        empirical_win_rate = _bounded_probability(
            decision["empirical_win_rate"],
            "empirical_win_rate",
        )
        confidence_lower_bound = _bounded_probability(
            decision["confidence_lower_bound"],
            "confidence_lower_bound",
        )
        confidence_upper_bound = _bounded_probability(
            decision["confidence_upper_bound"],
            "confidence_upper_bound",
        )
        calibration_error = _non_negative(
            decision["calibration_error"],
            "calibration_error",
        )
        brier_score = _non_negative(
            decision["brier_score"],
            "brier_score",
        )
        reliability = _non_negative(
            decision["reliability"],
            "reliability",
        )
        resolution = _non_negative(
            decision["resolution"],
            "resolution",
        )

        if confidence_lower_bound > confidence_upper_bound:
            raise QualifiedResearchPriorityRankingInvariantError(
                "confidence_lower_bound cannot exceed confidence_upper_bound."
            )

        confidence_edge = max(
            _ZERO,
            (confidence_lower_bound - _HALF) / _HALF,
        )
        empirical_edge = max(
            _ZERO,
            (empirical_win_rate - _HALF) / _HALF,
        )

        calibration_quality = self._quality_from_error(
            calibration_error,
            Decimal("0.10"),
        )
        reliability_quality = self._quality_from_error(
            reliability,
            Decimal("0.05"),
        )
        resolution_quality = min(
            _ONE,
            resolution / Decimal("0.10"),
        )
        sample_strength = self._sample_strength(
            decisive_count,
            str(decision["evidence_sufficiency"]),
            str(decision["sample_sufficiency"]),
        )

        priority_score = (
            Decimal("0.35") * confidence_edge
            + Decimal("0.20") * empirical_edge
            + Decimal("0.15") * calibration_quality
            + Decimal("0.10") * reliability_quality
            + Decimal("0.10") * resolution_quality
            + Decimal("0.10") * sample_strength
        ) * Decimal("100")

        reason_codes = (
            "oia_015_eligible",
            "confidence_lower_bound_above_chance",
            "calibration_within_eligibility_policy",
            "reliability_within_eligibility_policy",
            "deterministic_research_priority_scored",
        )

        return {
            "qualification_status": QUALIFIED,
            "dimension": str(decision["dimension"]),
            "key": str(decision["key"]),
            "decisive_count": decisive_count,
            "empirical_win_rate": _fmt(empirical_win_rate),
            "confidence_lower_bound": _fmt(confidence_lower_bound),
            "confidence_upper_bound": _fmt(confidence_upper_bound),
            "calibration_error": _fmt(calibration_error),
            "brier_score": _fmt(brier_score),
            "reliability": _fmt(reliability),
            "resolution": _fmt(resolution),
            "evidence_sufficiency": str(
                decision["evidence_sufficiency"]
            ),
            "sample_sufficiency": str(
                decision["sample_sufficiency"]
            ),
            "confidence_edge": _fmt(confidence_edge),
            "calibration_quality": _fmt(calibration_quality),
            "reliability_quality": _fmt(reliability_quality),
            "resolution_quality": _fmt(resolution_quality),
            "sample_strength": _fmt(sample_strength),
            "priority_score": _fmt(priority_score),
            "ranking_policy_id": RANKING_POLICY_ID,
            "reason_codes": reason_codes,
            "source_eligibility_decision_hash": str(
                decision["decision_hash"]
            ),
        }

    def rank(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchPriorityRankingReport:
        generated_at = _aware_utc(
            generated_at or datetime.now(timezone.utc),
            "generated_at",
        )

        eligibility_report = self._load_eligibility_report()
        source_decisions = eligibility_report["decisions"]

        qualified_decisions = [
            decision
            for decision in source_decisions
            if decision["status"] == ELIGIBLE
        ]
        excluded_decisions = [
            decision
            for decision in source_decisions
            if decision["status"] != ELIGIBLE
        ]

        scored = [
            self._score_decision(decision)
            for decision in qualified_decisions
        ]

        scored.sort(
            key=lambda item: (
                -_decimal(item["priority_score"], "priority_score"),
                -int(item["decisive_count"]),
                str(item["dimension"]),
                str(item["key"]),
                str(item["source_eligibility_decision_hash"]),
            )
        )

        rankings: list[OracleQualifiedResearchPriorityRecord] = []
        for rank, item in enumerate(scored, start=1):
            body = {
                "rank": rank,
                **item,
            }
            rankings.append(
                OracleQualifiedResearchPriorityRecord(
                    **body,
                    record_hash=stable_hash(body),
                )
            )

        excluded_hashes = tuple(
            sorted(
                str(decision["decision_hash"])
                for decision in excluded_decisions
            )
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "eligibility_directory": str(self._eligibility_directory),
            "ranking_directory": str(self._ranking_directory),
            "ranking_policy_id": RANKING_POLICY_ID,
            "source_decision_count": len(source_decisions),
            "qualified_decision_count": len(qualified_decisions),
            "excluded_decision_count": len(excluded_decisions),
            "ranking_count": len(rankings),
            "rankings": tuple(rankings),
            "excluded_decision_hashes": excluded_hashes,
            "source_eligibility_report_hash": str(
                eligibility_report["report_hash"]
            ),
            "read_only_corpus": READ_ONLY_CORPUS,
            "execution_allowed": EXECUTION_ALLOWED,
            "alerts_allowed": ALERTS_ALLOWED,
            "qseries_handoff_allowed": QSERIES_HANDOFF_ALLOWED,
            "signals_allowed": SIGNALS_ALLOWED,
            "trading_recommendations_allowed": (
                TRADING_RECOMMENDATIONS_ALLOWED
            ),
            "source_mutation_allowed": SOURCE_MUTATION_ALLOWED,
            "ranking_artifact_persistence_allowed": (
                RANKING_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }

        report = OracleQualifiedResearchPriorityRankingReport(
            **body,
            report_hash=stable_hash(body),
        )

        if persist:
            payload = dict(report.to_dict())
            _atomic_write(
                self._ranking_directory / "current.json",
                payload,
            )
            _atomic_write(
                self._ranking_directory
                / "reports"
                / f"ranking-{report.report_hash}.json",
                payload,
            )

        return report


def format_report(
    report: OracleQualifiedResearchPriorityRankingReport,
) -> str:
    lines = [
        "=" * 132,
        "ORACLE QUALIFIED RESEARCH PRIORITY RANKING",
        "=" * 132,
        f"Generated at: {report.generated_at.isoformat()}",
        f"Policy:       {report.ranking_policy_id}",
        (
            "Source decisions: "
            f"{report.source_decision_count} | "
            f"qualified={report.qualified_decision_count} | "
            f"excluded={report.excluded_decision_count}"
        ),
        "-" * 132,
        (
            f"{'RANK':>4}  "
            f"{'DIMENSION':34} "
            f"{'KEY':34} "
            f"{'N':>7} "
            f"{'WIN RATE':>10} "
            f"{'LOWER':>10} "
            f"{'SCORE':>12}"
        ),
    ]

    for item in report.rankings:
        lines.append(
            f"{item.rank:>4}  "
            f"{item.dimension[:34]:34} "
            f"{item.key[:34]:34} "
            f"{item.decisive_count:>7} "
            f"{item.empirical_win_rate:>10} "
            f"{item.confidence_lower_bound:>10} "
            f"{item.priority_score:>12}"
        )

    if not report.rankings:
        lines.append(
            "No OIA-015 eligible research components are currently qualified."
        )

    lines.extend(
        [
            "-" * 132,
            f"Report hash: {report.report_hash}",
            (
                "RESEARCH ANALYTICS ONLY — "
                "NO SIGNALS, ALERTS, RECOMMENDATIONS, HANDOFFS, OR EXECUTION"
            ),
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "OIA-016 qualified research priority ranking engine"
        )
    )
    parser.add_argument(
        "--eligibility-directory",
        default=str(DEFAULT_ELIGIBILITY_DIRECTORY),
    )
    parser.add_argument(
        "--ranking-directory",
        default=str(DEFAULT_RANKING_DIRECTORY),
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
    )
    args = parser.parse_args(argv)

    report = OracleQualifiedResearchPriorityRankingEngine(
        eligibility_directory=args.eligibility_directory,
        ranking_directory=args.ranking_directory,
    ).rank(
        persist=not args.no_persist,
    )

    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


TEST = r'''from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from qseries_v2.oracle_intelligence.analytics.oracle_forward_shadow_ranking_eligibility_gate import (
    ELIGIBLE,
    INELIGIBLE,
    PROVISIONAL,
    stable_hash as eligibility_hash,
)
from qseries_v2.oracle_intelligence.analytics.oracle_qualified_research_priority_ranking_engine import (
    ENGINE_ID,
    RANKING_POLICY_ID,
    SCHEMA_VERSION,
    OracleQualifiedResearchPriorityRankingEngine,
    QualifiedResearchPriorityRankingInvariantError,
    format_report,
    stable_hash,
)


NOW = datetime(2026, 7, 21, 4, 0, 0, tzinfo=timezone.utc)


def make_decision(
    *,
    dimension: str,
    key: str,
    status: str,
    decisive_count: int,
    win_rate: str,
    lower: str,
    upper: str,
    calibration_error: str,
    brier_score: str,
    reliability: str,
    resolution: str,
    evidence_sufficiency: str = "strong",
    sample_sufficiency: str = "established",
) -> dict:
    body = {
        "dimension": dimension,
        "key": key,
        "status": status,
        "decisive_count": decisive_count,
        "empirical_win_rate": win_rate,
        "confidence_lower_bound": lower,
        "confidence_upper_bound": upper,
        "calibration_error": calibration_error,
        "brier_score": brier_score,
        "reliability": reliability,
        "resolution": resolution,
        "evidence_sufficiency": evidence_sufficiency,
        "sample_sufficiency": sample_sufficiency,
        "reason_codes": ["test_fixture"],
        "calibration_bucket_hash": "a" * 64,
        "reliability_component_hash": "b" * 64,
        "confidence_component_hash": "c" * 64,
    }
    return {
        **body,
        "decision_hash": eligibility_hash(body),
    }


def write_eligibility_report(
    directory: Path,
    decisions: list[dict],
) -> dict:
    body = {
        "schema_version": "OIA-015",
        "engine_id": "OIA-015",
        "generated_at": NOW,
        "calibration_directory": "calibration",
        "reliability_directory": "reliability",
        "confidence_directory": "confidence",
        "eligibility_directory": str(directory),
        "matched_component_count": len(decisions),
        "eligible_count": sum(
            item["status"] == ELIGIBLE
            for item in decisions
        ),
        "provisional_count": sum(
            item["status"] == PROVISIONAL
            for item in decisions
        ),
        "ineligible_count": sum(
            item["status"] == INELIGIBLE
            for item in decisions
        ),
        "insufficient_evidence_count": 0,
        "decisions": decisions,
        "source_calibration_report_hash": "d" * 64,
        "source_reliability_report_hash": "e" * 64,
        "source_confidence_report_hash": "f" * 64,
        "read_only_corpus": True,
        "execution_allowed": False,
        "alerts_allowed": False,
        "qseries_handoff_allowed": False,
        "signals_allowed": False,
        "trading_recommendations_allowed": False,
        "source_mutation_allowed": False,
        "eligibility_artifact_persistence_allowed": True,
    }
    payload = {
        **body,
        "report_hash": eligibility_hash(body),
    }

    directory.mkdir(parents=True, exist_ok=True)
    (directory / "current.json").write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            default=lambda value: value.isoformat(),
        )
        + "\n",
        encoding="utf-8",
    )
    return payload


def run_test() -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        eligibility_directory = root / "eligibility"
        ranking_directory = root / "ranking"

        strongest = make_decision(
            dimension="candidate_family_horizon",
            key="momentum|300",
            status=ELIGIBLE,
            decisive_count=600,
            win_rate="0.70000000",
            lower="0.66000000",
            upper="0.73800000",
            calibration_error="0.01000000",
            brier_score="0.21000000",
            reliability="0.00500000",
            resolution="0.05000000",
        )
        second = make_decision(
            dimension="candidate_family_horizon",
            key="reversion|900",
            status=ELIGIBLE,
            decisive_count=420,
            win_rate="0.64000000",
            lower="0.59000000",
            upper="0.68600000",
            calibration_error="0.03000000",
            brier_score="0.23000000",
            reliability="0.02000000",
            resolution="0.03000000",
        )
        provisional = make_decision(
            dimension="horizon",
            key="3600",
            status=PROVISIONAL,
            decisive_count=90,
            win_rate="0.60000000",
            lower="0.49000000",
            upper="0.70000000",
            calibration_error="0.02000000",
            brier_score="0.24000000",
            reliability="0.02000000",
            resolution="0.02000000",
            evidence_sufficiency="provisional",
            sample_sufficiency="provisional",
        )
        ineligible = make_decision(
            dimension="research_direction_horizon",
            key="no|300",
            status=INELIGIBLE,
            decisive_count=500,
            win_rate="0.42000000",
            lower="0.38000000",
            upper="0.46300000",
            calibration_error="0.12000000",
            brier_score="0.27000000",
            reliability="0.06000000",
            resolution="0.00000000",
        )

        source_report = write_eligibility_report(
            eligibility_directory,
            [
                second,
                ineligible,
                strongest,
                provisional,
            ],
        )

        engine = OracleQualifiedResearchPriorityRankingEngine(
            eligibility_directory=eligibility_directory,
            ranking_directory=ranking_directory,
        )

        report = engine.rank(
            generated_at=NOW,
            persist=True,
        )

        assert report.schema_version == SCHEMA_VERSION == "OIA-016"
        assert report.engine_id == ENGINE_ID == "OIA-016"
        assert report.ranking_policy_id == RANKING_POLICY_ID

        assert report.source_decision_count == 4
        assert report.qualified_decision_count == 2
        assert report.excluded_decision_count == 2
        assert report.ranking_count == 2

        assert report.rankings[0].rank == 1
        assert report.rankings[0].key == "momentum|300"
        assert report.rankings[1].rank == 2
        assert report.rankings[1].key == "reversion|900"

        assert (
            float(report.rankings[0].priority_score)
            > float(report.rankings[1].priority_score)
        )

        assert (
            report.rankings[0].source_eligibility_decision_hash
            == strongest["decision_hash"]
        )
        assert (
            report.rankings[1].source_eligibility_decision_hash
            == second["decision_hash"]
        )

        assert set(report.excluded_decision_hashes) == {
            provisional["decision_hash"],
            ineligible["decision_hash"],
        }

        for item in report.rankings:
            payload = dict(item.to_dict())
            digest = payload.pop("record_hash")
            assert digest == stable_hash(payload)

        report_payload = dict(report.to_dict())
        report_digest = report_payload.pop("report_hash")
        assert report_digest == stable_hash(report_payload)

        assert (
            report.source_eligibility_report_hash
            == source_report["report_hash"]
        )

        assert report.read_only_corpus
        assert not report.execution_allowed
        assert not report.alerts_allowed
        assert not report.qseries_handoff_allowed
        assert not report.signals_allowed
        assert not report.trading_recommendations_allowed
        assert not report.source_mutation_allowed
        assert report.ranking_artifact_persistence_allowed

        current_path = ranking_directory / "current.json"
        immutable_path = (
            ranking_directory
            / "reports"
            / f"ranking-{report.report_hash}.json"
        )
        assert current_path.exists()
        assert immutable_path.exists()

        first_current = current_path.read_bytes()
        first_immutable = immutable_path.read_bytes()

        replay = engine.rank(
            generated_at=NOW,
            persist=True,
        )
        assert replay.report_hash == report.report_hash
        assert current_path.read_bytes() == first_current
        assert immutable_path.read_bytes() == first_immutable

        rendered = format_report(report)
        assert "ORACLE QUALIFIED RESEARCH PRIORITY RANKING" in rendered
        assert "momentum|300" in rendered
        assert "NO SIGNALS" in rendered

        tampered = json.loads(
            (
                eligibility_directory / "current.json"
            ).read_text(encoding="utf-8")
        )
        tampered["eligible_count"] = 999
        (
            eligibility_directory / "current.json"
        ).write_text(
            json.dumps(tampered, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            engine.rank(
                generated_at=NOW,
                persist=False,
            )
        except QualifiedResearchPriorityRankingInvariantError:
            pass
        else:
            raise AssertionError(
                "Tampered OIA-015 report was not rejected."
            )

    print(
        "[PASS] OIA-016 Oracle Qualified Research "
        "Priority Ranking Engine"
    )


if __name__ == "__main__":
    run_test()
'''


INIT_BLOCK = r'''
from .oracle_qualified_research_priority_ranking_engine import (
    NOT_QUALIFIED,
    QUALIFIED,
    RANKING_POLICY_ID,
    OracleQualifiedResearchPriorityRankingEngine,
    OracleQualifiedResearchPriorityRankingReport,
    OracleQualifiedResearchPriorityRecord,
)
'''


INIT_EXPORTS = (
    "NOT_QUALIFIED",
    "QUALIFIED",
    "RANKING_POLICY_ID",
    "OracleQualifiedResearchPriorityRankingEngine",
    "OracleQualifiedResearchPriorityRankingReport",
    "OracleQualifiedResearchPriorityRecord",
)


def write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def update_package_init(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            f"[FAIL] Analytics package initializer is missing: {path}"
        )

    original = path.read_text(encoding="utf-8")
    updated = original

    import_marker = (
        "from .oracle_qualified_research_priority_ranking_engine import"
    )

    if import_marker not in updated:
        updated = updated.rstrip() + "\n\n" + INIT_BLOCK.strip() + "\n"

    if "__all__" in updated:
        missing_exports = [
            name
            for name in INIT_EXPORTS
            if f'"{name}"' not in updated
        ]

        if missing_exports:
            export_lines = "\n".join(
                f'    "{name}",'
                for name in missing_exports
            )
            updated = (
                updated.rstrip()
                + "\n\n__all__ = [\n"
                + export_lines
                + "\n] + __all__\n"
            )

    if updated != original:
        path.write_text(
            updated,
            encoding="utf-8",
            newline="\n",
        )
        print(f"[OK] PACKAGE EXPORT UPDATE: {path.resolve()}")
    else:
        print(f"[OK] PACKAGE EXPORTS ALREADY PRESENT: {path.resolve()}")


def verify_dependency(path: Path) -> None:
    if not path.exists():
        raise SystemExit(
            "[FAIL] OIA-015 production module is missing. "
            "Install and pass OIA-015 first."
        )

    text = path.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIA-015"',
        'ENGINE_ID = "OIA-015"',
        'ELIGIBLE = "eligible"',
        "class OracleForwardShadowRankingEligibilityDecision:",
        "class OracleForwardShadowRankingEligibilityReport:",
        "class OracleForwardShadowRankingEligibilityGate:",
        "decision_hash",
        "report_hash",
        "eligibility_artifact_persistence_allowed",
        "execution_allowed",
        "qseries_handoff_allowed",
    )

    missing = [
        token
        for token in required
        if token not in text
    ]
    if missing:
        raise SystemExit(
            "[FAIL] Actual OIA-015 dependency contract mismatch: "
            f"{missing}"
        )


def main() -> int:
    root = Path.cwd()

    dependency = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "analytics"
        / "oracle_forward_shadow_ranking_eligibility_gate.py"
    )
    verify_dependency(dependency)

    print("========================================")
    print(" OIA-016 INSTALLER")
    print(" QUALIFIED RESEARCH PRIORITY RANKING")
    print(" ELIGIBILITY / QUALITY / CONFIDENCE")
    print("========================================")
    print("[OK] Actual OIA-015 eligibility contract verified")

    package = (
        root
        / "qseries_v2"
        / "oracle_intelligence"
        / "analytics"
    )
    package.mkdir(parents=True, exist_ok=True)

    module_path = (
        package
        / "oracle_qualified_research_priority_ranking_engine.py"
    )
    test_path = (
        root
        / "test_oia_016_oracle_qualified_research_priority_ranking_engine.py"
    )
    init_path = package / "__init__.py"

    write_full(module_path, MODULE)
    write_full(test_path, TEST)
    update_package_init(init_path)

    ast.parse(
        MODULE,
        filename=str(module_path),
    )
    ast.parse(
        TEST,
        filename=str(test_path),
    )
    ast.parse(
        init_path.read_text(encoding="utf-8"),
        filename=str(init_path),
    )

    print(
        "[OK] OIA-016 production, package, and test syntax verified"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(test_path),
        ],
        cwd=root,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("[OK] OIA-016 test executed successfully")
    print(
        "[DONE] OIA-016 Oracle Qualified Research "
        "Priority Ranking Engine installed"
    )
    print()
    print("Run the live research ranking with:")
    print(
        "python -m "
        "qseries_v2.oracle_intelligence.analytics."
        "oracle_qualified_research_priority_ranking_engine"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())