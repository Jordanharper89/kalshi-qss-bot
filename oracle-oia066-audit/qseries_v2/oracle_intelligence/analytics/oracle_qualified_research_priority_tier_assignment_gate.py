"""
OIA-017
Oracle Qualified Research Priority Tier Assignment Gate

Consumes the immutable OIA-016 qualified research priority ranking report and
assigns deterministic research-priority tiers.

The gate:

- verifies the complete OIA-016 report and record hash chain;
- preserves the exact OIA-016 ordinal ranking;
- assigns policy-versioned Tier 1, Tier 2, or Tier 3 classifications;
- keeps all non-ranked components outside the tier system;
- emits immutable, content-addressed research-tier artifacts;
- remains permanently separated from alerts, recommendations, handoffs,
  execution, orders, funds, and portfolio mutation.

OIA-017 is a research scheduling classification boundary only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .oracle_qualified_research_priority_ranking_engine import (
    DEFAULT_RANKING_DIRECTORY,
    QUALIFIED,
    RANKING_POLICY_ID,
    stable_hash as ranking_stable_hash,
)


SCHEMA_VERSION = "OIA-017"
ENGINE_ID = "OIA-017"

TIER_POLICY_ID = "oracle.qualified-research-priority-tier.v1"

TIER_1 = "tier_1"
TIER_2 = "tier_2"
TIER_3 = "tier_3"
UNASSIGNED = "unassigned"

ADMITTED = "admitted"
DENIED = "denied"

TIER_1_MINIMUM_SCORE = Decimal("70.00000000")
TIER_2_MINIMUM_SCORE = Decimal("50.00000000")
TIER_3_MINIMUM_SCORE = Decimal("0.00000000")

READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
TIER_ARTIFACT_PERSISTENCE_ALLOWED = True

DEFAULT_TIER_DIRECTORY = (
    Path("runtime")
    / "oracle_intelligence"
    / "qualified_research_priority_tiers"
)


class QualifiedResearchPriorityTierError(RuntimeError):
    """Base OIA-017 error."""


class QualifiedResearchPriorityTierInvariantError(
    QualifiedResearchPriorityTierError
):
    """Raised when an immutable source or local invariant fails."""


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise QualifiedResearchPriorityTierInvariantError(
            f"{field_name} must be timezone-aware."
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


def _decimal(value: Any, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise QualifiedResearchPriorityTierInvariantError(
            f"{field_name} must be a finite decimal."
        ) from exc

    if not result.is_finite():
        raise QualifiedResearchPriorityTierInvariantError(
            f"{field_name} must be a finite decimal."
        )

    return result


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
class OracleQualifiedResearchPriorityTierRecord:
    rank: int
    dimension: str
    key: str
    qualification_status: str
    tier_status: str
    tier: str
    priority_score: str
    decisive_count: int
    empirical_win_rate: str
    confidence_lower_bound: str
    calibration_quality: str
    reliability_quality: str
    resolution_quality: str
    sample_strength: str
    ranking_policy_id: str
    tier_policy_id: str
    reason_codes: tuple[str, ...]
    source_eligibility_decision_hash: str
    source_ranking_record_hash: str
    tier_record_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleQualifiedResearchPriorityTierReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    ranking_directory: str
    tier_directory: str
    ranking_policy_id: str
    tier_policy_id: str
    source_ranking_count: int
    admitted_count: int
    denied_count: int
    tier_1_count: int
    tier_2_count: int
    tier_3_count: int
    records: tuple[OracleQualifiedResearchPriorityTierRecord, ...]
    source_ranking_report_hash: str
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_mutation_allowed: bool
    tier_artifact_persistence_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleQualifiedResearchPriorityTierAssignmentGate:
    """
    Deterministically classifies verified OIA-016 ranking records.

    Tier policy v1:

    - Tier 1: priority score >= 70
    - Tier 2: priority score >= 50 and < 70
    - Tier 3: priority score >= 0 and < 50

    Every valid OIA-016 ranking record must already be qualified. OIA-017 does
    not override, recalculate, or weaken OIA-016 eligibility or ranking.
    """

    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    source_mutation_allowed = False
    tier_artifact_persistence_allowed = True

    def __init__(
        self,
        *,
        ranking_directory: Path | str = DEFAULT_RANKING_DIRECTORY,
        tier_directory: Path | str = DEFAULT_TIER_DIRECTORY,
    ) -> None:
        self._ranking_directory = Path(ranking_directory)
        self._tier_directory = Path(tier_directory)

    def _load_ranking_report(self) -> dict[str, Any]:
        current_path = self._ranking_directory / "current.json"

        if not current_path.exists():
            raise QualifiedResearchPriorityTierInvariantError(
                f"OIA-016 current ranking report is missing: {current_path}"
            )

        try:
            payload = json.loads(
                current_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise QualifiedResearchPriorityTierInvariantError(
                f"OIA-016 ranking report is not valid JSON: {current_path}"
            ) from exc

        if not isinstance(payload, dict):
            raise QualifiedResearchPriorityTierInvariantError(
                "OIA-016 ranking report must be a JSON object."
            )

        report_hash = payload.pop("report_hash", None)

        if payload.get("schema_version") != "OIA-016":
            raise QualifiedResearchPriorityTierInvariantError(
                "Unsupported OIA-016 schema version."
            )

        if payload.get("engine_id") != "OIA-016":
            raise QualifiedResearchPriorityTierInvariantError(
                "Unsupported OIA-016 engine identity."
            )

        if payload.get("ranking_policy_id") != RANKING_POLICY_ID:
            raise QualifiedResearchPriorityTierInvariantError(
                "OIA-016 ranking policy identity mismatch."
            )

        if report_hash != ranking_stable_hash(payload):
            raise QualifiedResearchPriorityTierInvariantError(
                "OIA-016 ranking report hash verification failed."
            )

        if payload.get("read_only_corpus") is not True:
            raise QualifiedResearchPriorityTierInvariantError(
                "OIA-016 read-only corpus invariant failed."
            )

        forbidden_true_fields = (
            "execution_allowed",
            "alerts_allowed",
            "qseries_handoff_allowed",
            "signals_allowed",
            "trading_recommendations_allowed",
            "source_mutation_allowed",
        )

        for field_name in forbidden_true_fields:
            if payload.get(field_name) is not False:
                raise QualifiedResearchPriorityTierInvariantError(
                    f"OIA-016 safety boundary mismatch: {field_name}."
                )

        rankings = payload.get("rankings")

        if not isinstance(rankings, list):
            raise QualifiedResearchPriorityTierInvariantError(
                "OIA-016 rankings must be a list."
            )

        expected_count = int(payload.get("ranking_count", -1))

        if expected_count != len(rankings):
            raise QualifiedResearchPriorityTierInvariantError(
                "OIA-016 ranking count does not match ranking records."
            )

        qualified_count = int(
            payload.get("qualified_decision_count", -1)
        )

        if qualified_count != len(rankings):
            raise QualifiedResearchPriorityTierInvariantError(
                "Every OIA-016 qualified decision must have one ranking."
            )

        verified_records: list[dict[str, Any]] = []
        seen_ranks: set[int] = set()
        seen_identities: set[tuple[str, str]] = set()
        seen_record_hashes: set[str] = set()

        previous_score: Decimal | None = None

        for index, raw_record in enumerate(rankings, start=1):
            if not isinstance(raw_record, dict):
                raise QualifiedResearchPriorityTierInvariantError(
                    f"OIA-016 ranking record {index} must be an object."
                )

            record = dict(raw_record)
            record_hash = record.pop("record_hash", None)

            if record_hash != ranking_stable_hash(record):
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 ranking record hash verification failed "
                    f"at index {index}."
                )

            rank = int(record.get("rank", -1))

            if rank != index:
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 ranks must be contiguous and ordered "
                    "starting at one."
                )

            if rank in seen_ranks:
                raise QualifiedResearchPriorityTierInvariantError(
                    f"Duplicate OIA-016 rank: {rank}"
                )

            identity = (
                str(record.get("dimension", "")),
                str(record.get("key", "")),
            )

            if not identity[0] or not identity[1]:
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 ranking identity cannot be empty."
                )

            if identity in seen_identities:
                raise QualifiedResearchPriorityTierInvariantError(
                    f"Duplicate OIA-016 ranking identity: {identity!r}"
                )

            if record.get("qualification_status") != QUALIFIED:
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 ranked records must be qualified."
                )

            if record.get("ranking_policy_id") != RANKING_POLICY_ID:
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 record ranking policy mismatch."
                )

            if (
                not isinstance(record_hash, str)
                or len(record_hash) != 64
            ):
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 ranking record hash is malformed."
                )

            if record_hash in seen_record_hashes:
                raise QualifiedResearchPriorityTierInvariantError(
                    f"Duplicate OIA-016 record hash: {record_hash}"
                )

            score = _decimal(
                record.get("priority_score"),
                "priority_score",
            )

            if score < Decimal("0") or score > Decimal("100"):
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 priority score must be between 0 and 100."
                )

            if previous_score is not None and score > previous_score:
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 rankings are not ordered by descending score."
                )

            decisive_count = int(record.get("decisive_count", -1))

            if decisive_count < 0:
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 decisive count must be non-negative."
                )

            source_decision_hash = record.get(
                "source_eligibility_decision_hash"
            )

            if (
                not isinstance(source_decision_hash, str)
                or len(source_decision_hash) != 64
            ):
                raise QualifiedResearchPriorityTierInvariantError(
                    "OIA-016 source eligibility decision hash is malformed."
                )

            seen_ranks.add(rank)
            seen_identities.add(identity)
            seen_record_hashes.add(record_hash)
            previous_score = score

            record["record_hash"] = record_hash
            verified_records.append(record)

        payload["rankings"] = verified_records
        payload["report_hash"] = report_hash
        return payload

    @staticmethod
    def _assign_tier(priority_score: Decimal) -> tuple[str, str]:
        if priority_score >= TIER_1_MINIMUM_SCORE:
            return TIER_1, ADMITTED

        if priority_score >= TIER_2_MINIMUM_SCORE:
            return TIER_2, ADMITTED

        if priority_score >= TIER_3_MINIMUM_SCORE:
            return TIER_3, ADMITTED

        return UNASSIGNED, DENIED

    @staticmethod
    def _reason_codes(tier: str) -> tuple[str, ...]:
        common = (
            "oia_016_qualified_ranking_verified",
            "source_rank_preserved",
            "deterministic_tier_policy_applied",
            "research_classification_only",
        )

        if tier == TIER_1:
            return common + (
                "priority_score_meets_tier_1_threshold",
            )

        if tier == TIER_2:
            return common + (
                "priority_score_meets_tier_2_threshold",
            )

        if tier == TIER_3:
            return common + (
                "priority_score_meets_tier_3_threshold",
            )

        return common + (
            "priority_score_outside_admission_policy",
        )

    def evaluate(
        self,
        *,
        generated_at: datetime | None = None,
        persist: bool = True,
    ) -> OracleQualifiedResearchPriorityTierReport:
        generated_at = _aware_utc(
            generated_at or datetime.now(timezone.utc),
            "generated_at",
        )

        source_report = self._load_ranking_report()
        source_rankings = source_report["rankings"]

        records: list[OracleQualifiedResearchPriorityTierRecord] = []

        for source_record in source_rankings:
            score = _decimal(
                source_record["priority_score"],
                "priority_score",
            )
            tier, tier_status = self._assign_tier(score)

            body = {
                "rank": int(source_record["rank"]),
                "dimension": str(source_record["dimension"]),
                "key": str(source_record["key"]),
                "qualification_status": str(
                    source_record["qualification_status"]
                ),
                "tier_status": tier_status,
                "tier": tier,
                "priority_score": str(
                    source_record["priority_score"]
                ),
                "decisive_count": int(
                    source_record["decisive_count"]
                ),
                "empirical_win_rate": str(
                    source_record["empirical_win_rate"]
                ),
                "confidence_lower_bound": str(
                    source_record["confidence_lower_bound"]
                ),
                "calibration_quality": str(
                    source_record["calibration_quality"]
                ),
                "reliability_quality": str(
                    source_record["reliability_quality"]
                ),
                "resolution_quality": str(
                    source_record["resolution_quality"]
                ),
                "sample_strength": str(
                    source_record["sample_strength"]
                ),
                "ranking_policy_id": str(
                    source_record["ranking_policy_id"]
                ),
                "tier_policy_id": TIER_POLICY_ID,
                "reason_codes": self._reason_codes(tier),
                "source_eligibility_decision_hash": str(
                    source_record[
                        "source_eligibility_decision_hash"
                    ]
                ),
                "source_ranking_record_hash": str(
                    source_record["record_hash"]
                ),
            }

            records.append(
                OracleQualifiedResearchPriorityTierRecord(
                    **body,
                    tier_record_hash=stable_hash(body),
                )
            )

        admitted_count = sum(
            record.tier_status == ADMITTED
            for record in records
        )
        denied_count = sum(
            record.tier_status == DENIED
            for record in records
        )
        tier_1_count = sum(
            record.tier == TIER_1
            for record in records
        )
        tier_2_count = sum(
            record.tier == TIER_2
            for record in records
        )
        tier_3_count = sum(
            record.tier == TIER_3
            for record in records
        )

        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": generated_at,
            "ranking_directory": str(self._ranking_directory),
            "tier_directory": str(self._tier_directory),
            "ranking_policy_id": RANKING_POLICY_ID,
            "tier_policy_id": TIER_POLICY_ID,
            "source_ranking_count": len(source_rankings),
            "admitted_count": admitted_count,
            "denied_count": denied_count,
            "tier_1_count": tier_1_count,
            "tier_2_count": tier_2_count,
            "tier_3_count": tier_3_count,
            "records": tuple(records),
            "source_ranking_report_hash": str(
                source_report["report_hash"]
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
            "tier_artifact_persistence_allowed": (
                TIER_ARTIFACT_PERSISTENCE_ALLOWED
            ),
        }

        report = OracleQualifiedResearchPriorityTierReport(
            **body,
            report_hash=stable_hash(body),
        )

        if persist:
            payload = dict(report.to_dict())

            _atomic_write(
                self._tier_directory / "current.json",
                payload,
            )

            _atomic_write(
                self._tier_directory
                / "reports"
                / f"tier-report-{report.report_hash}.json",
                payload,
            )

        return report


def format_report(
    report: OracleQualifiedResearchPriorityTierReport,
) -> str:
    lines = [
        "=" * 140,
        "ORACLE QUALIFIED RESEARCH PRIORITY TIER ASSIGNMENT",
        "=" * 140,
        f"Generated at:  {report.generated_at.isoformat()}",
        f"Ranking policy:{report.ranking_policy_id}",
        f"Tier policy:   {report.tier_policy_id}",
        (
            "Records: "
            f"{report.source_ranking_count} | "
            f"admitted={report.admitted_count} | "
            f"denied={report.denied_count} | "
            f"tier_1={report.tier_1_count} | "
            f"tier_2={report.tier_2_count} | "
            f"tier_3={report.tier_3_count}"
        ),
        "-" * 140,
        (
            f"{'RANK':>4}  "
            f"{'TIER':10} "
            f"{'STATUS':10} "
            f"{'DIMENSION':34} "
            f"{'KEY':34} "
            f"{'N':>7} "
            f"{'SCORE':>12}"
        ),
    ]

    for record in report.records:
        lines.append(
            f"{record.rank:>4}  "
            f"{record.tier:10} "
            f"{record.tier_status:10} "
            f"{record.dimension[:34]:34} "
            f"{record.key[:34]:34} "
            f"{record.decisive_count:>7} "
            f"{record.priority_score:>12}"
        )

    if not report.records:
        lines.append(
            "No verified OIA-016 ranking records are currently available."
        )

    lines.extend(
        [
            "-" * 140,
            f"Report hash: {report.report_hash}",
            (
                "RESEARCH CLASSIFICATION ONLY — "
                "NO SIGNALS, ALERTS, RECOMMENDATIONS, HANDOFFS, "
                "ORDERS, FUNDS MOVEMENT, OR EXECUTION"
            ),
        ]
    )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "OIA-017 qualified research priority tier assignment gate"
        )
    )
    parser.add_argument(
        "--ranking-directory",
        default=str(DEFAULT_RANKING_DIRECTORY),
    )
    parser.add_argument(
        "--tier-directory",
        default=str(DEFAULT_TIER_DIRECTORY),
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
    )
    args = parser.parse_args(argv)

    report = OracleQualifiedResearchPriorityTierAssignmentGate(
        ranking_directory=args.ranking_directory,
        tier_directory=args.tier_directory,
    ).evaluate(
        persist=not args.no_persist,
    )

    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
