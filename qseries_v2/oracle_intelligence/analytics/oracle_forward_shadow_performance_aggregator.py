"""
OIA-011
Oracle Forward Shadow Performance Aggregator

Reads immutable OIA-010 fixed-horizon outcome artifacts and produces deterministic
research-performance summaries. It never changes outcome artifacts, OIA-009 ledger
entries, canonical PostgreSQL observations, Q Series state, orders, funds, or portfolios.
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
from statistics import median
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Optional

from .oracle_forward_shadow_outcome_evaluator import (
    DEFAULT_OUTCOME_DIRECTORY,
    FLAT,
    GRADED,
    LOSS,
    WIN,
    stable_hash as outcome_stable_hash,
)

SCHEMA_VERSION = "OIA-011"
ENGINE_ID = "OIA-011"
READ_ONLY_CORPUS = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
TRADING_RECOMMENDATIONS_ALLOWED = False
SOURCE_OUTCOME_MUTATION_ALLOWED = False
PERFORMANCE_ARTIFACT_PERSISTENCE_ALLOWED = True
DEFAULT_PERFORMANCE_DIRECTORY = Path("runtime") / "oracle_intelligence" / "forward_shadow_performance"
AGGREGATION_DIMENSIONS = ("overall", "horizon", "market_horizon", "family_horizon", "direction_horizon")
_QUANT = Decimal("0.00000001")


class ForwardShadowPerformanceError(RuntimeError):
    pass


class ForwardShadowPerformanceInvariantError(ForwardShadowPerformanceError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ForwardShadowPerformanceInvariantError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def stable_hash(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ForwardShadowPerformanceInvariantError(f"{name} must be a finite decimal.") from exc
    if not result.is_finite():
        raise ForwardShadowPerformanceInvariantError(f"{name} must be a finite decimal.")
    return result


def _ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.00000000"
    return format((Decimal(numerator) / Decimal(denominator)).quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _mean(values: list[Decimal]) -> str:
    if not values:
        return "0.00000000"
    return format((sum(values, Decimal("0")) / Decimal(len(values))).quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _median(values: list[Decimal]) -> str:
    if not values:
        return "0.00000000"
    return format(Decimal(str(median(values))).quantize(_QUANT, rounding=ROUND_HALF_EVEN), "f")


def _atomic_json_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(_canonical(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", delete=False, dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class OracleForwardShadowPerformanceBucket:
    dimension: str
    key: str
    graded_count: int
    win_count: int
    loss_count: int
    flat_count: int
    decisive_count: int
    win_rate: str
    loss_rate: str
    flat_rate: str
    mean_directional_return: str
    median_directional_return: str
    positive_return_rate: str
    bucket_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleForwardShadowPerformanceReport:
    schema_version: str
    engine_id: str
    generated_at: datetime
    source_outcome_directory: str
    performance_directory: str
    source_artifact_count: int
    verified_graded_outcome_count: int
    duplicate_outcome_count: int
    bucket_count: int
    buckets: tuple[OracleForwardShadowPerformanceBucket, ...]
    source_outcome_hashes: tuple[str, ...]
    read_only_corpus: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    trading_recommendations_allowed: bool
    source_outcome_mutation_allowed: bool
    performance_artifact_persistence_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleForwardShadowPerformanceAggregator:
    read_only_corpus = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    trading_recommendations_allowed = False
    source_outcome_mutation_allowed = False
    performance_artifact_persistence_allowed = True

    def __init__(self, *, outcome_directory: Path | str = DEFAULT_OUTCOME_DIRECTORY, performance_directory: Path | str = DEFAULT_PERFORMANCE_DIRECTORY) -> None:
        self._outcome_directory = Path(outcome_directory)
        self._performance_directory = Path(performance_directory)

    def _load_outcomes(self) -> tuple[list[Mapping[str, Any]], int, int]:
        root = self._outcome_directory / "outcomes"
        files = sorted(root.glob("*/*.json")) if root.exists() else []
        outcomes: list[Mapping[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        duplicates = 0
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != "OIA-010" or payload.get("engine_id") != "OIA-010":
                raise ForwardShadowPerformanceInvariantError(f"Unexpected outcome contract: {path}")
            supplied = str(payload.get("outcome_hash", ""))
            body = dict(payload)
            body.pop("outcome_hash", None)
            if len(supplied) != 64 or supplied != outcome_stable_hash(body):
                raise ForwardShadowPerformanceInvariantError(f"Outcome hash verification failed: {path}")
            if payload.get("status") != GRADED:
                continue
            grade = payload.get("grade")
            if grade not in {WIN, LOSS, FLAT}:
                raise ForwardShadowPerformanceInvariantError(f"Invalid grade in {path}")
            key = (str(payload.get("evaluation_id", "")), int(payload.get("horizon_seconds", 0)))
            if not key[0] or key[1] <= 0:
                raise ForwardShadowPerformanceInvariantError(f"Invalid evaluation identity in {path}")
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            _decimal(payload.get("directional_return"), "directional_return")
            outcomes.append(payload)
        return outcomes, len(files), duplicates

    @staticmethod
    def _keys(payload: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
        horizon = str(int(payload["horizon_seconds"]))
        market = str(payload.get("market_id", ""))
        family = str(payload.get("candidate_family", ""))
        direction = str(payload.get("research_direction", ""))
        return (
            ("overall", "all"),
            ("horizon", horizon),
            ("market_horizon", f"{market}|{horizon}"),
            ("family_horizon", f"{family}|{horizon}"),
            ("direction_horizon", f"{direction}|{horizon}"),
        )

    def aggregate(self, *, generated_at: Optional[datetime] = None, persist: bool = True) -> OracleForwardShadowPerformanceReport:
        anchor = _aware_utc(generated_at or datetime.now(timezone.utc), "generated_at")
        outcomes, artifact_count, duplicates = self._load_outcomes()
        groups: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
        for outcome in outcomes:
            for key in self._keys(outcome):
                groups.setdefault(key, []).append(outcome)
        buckets: list[OracleForwardShadowPerformanceBucket] = []
        for (dimension, key), items in sorted(groups.items()):
            grades = [str(item["grade"]) for item in items]
            returns = [_decimal(item["directional_return"], "directional_return") for item in items]
            wins = grades.count(WIN); losses = grades.count(LOSS); flats = grades.count(FLAT)
            decisive = wins + losses
            positive = sum(1 for value in returns if value > 0)
            body = {
                "dimension": dimension,
                "key": key,
                "graded_count": len(items),
                "win_count": wins,
                "loss_count": losses,
                "flat_count": flats,
                "decisive_count": decisive,
                "win_rate": _ratio(wins, decisive),
                "loss_rate": _ratio(losses, decisive),
                "flat_rate": _ratio(flats, len(items)),
                "mean_directional_return": _mean(returns),
                "median_directional_return": _median(returns),
                "positive_return_rate": _ratio(positive, len(items)),
            }
            buckets.append(OracleForwardShadowPerformanceBucket(**body, bucket_hash=stable_hash(body)))
        body = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "generated_at": anchor,
            "source_outcome_directory": str(self._outcome_directory),
            "performance_directory": str(self._performance_directory),
            "source_artifact_count": artifact_count,
            "verified_graded_outcome_count": len(outcomes),
            "duplicate_outcome_count": duplicates,
            "bucket_count": len(buckets),
            "buckets": tuple(buckets),
            "source_outcome_hashes": tuple(sorted(str(item["outcome_hash"]) for item in outcomes)),
            "read_only_corpus": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "trading_recommendations_allowed": False,
            "source_outcome_mutation_allowed": False,
            "performance_artifact_persistence_allowed": True,
        }
        report = OracleForwardShadowPerformanceReport(**body, report_hash=stable_hash(body))
        if persist:
            _atomic_json_write(self._performance_directory / "current.json", report.to_dict())
            history = self._performance_directory / "reports" / f"performance-{anchor.strftime('%Y%m%dT%H%M%S%fZ')}-{report.report_hash[:16]}.json"
            _atomic_json_write(history, report.to_dict())
        return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate immutable OIA-010 forward-shadow outcomes.")
    parser.add_argument("--outcome-directory", default=str(DEFAULT_OUTCOME_DIRECTORY))
    parser.add_argument("--performance-directory", default=str(DEFAULT_PERFORMANCE_DIRECTORY))
    parser.add_argument("--no-persist", action="store_true")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    report = OracleForwardShadowPerformanceAggregator(outcome_directory=args.outcome_directory, performance_directory=args.performance_directory).aggregate(persist=not args.no_persist)
    print("========================================")
    print(" OIA-011 FORWARD SHADOW PERFORMANCE")
    print("========================================")
    print(f"[OK] Verified graded outcomes: {report.verified_graded_outcome_count}")
    print(f"[OK] Performance buckets: {report.bucket_count}")
    print(f"[OK] Report hash: {report.report_hash}")
    print("[PASS] OIA-011 performance aggregation completed read-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
