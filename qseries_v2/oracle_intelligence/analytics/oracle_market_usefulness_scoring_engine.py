"""
OIA-005
Oracle Market Usefulness Scoring Engine

Read-only deterministic scoring over OIA-004 canonical market features.
The engine measures whether accumulated market data is useful for later trader
research. It does not create opportunities, signals, alerts, or execution input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

from .oracle_market_feature_extraction_engine import (
    OracleCanonicalMarketFeatureExtractionEngine,
    OracleCanonicalMarketFeatureRecord,
    OracleCanonicalMarketFeatureReport,
)

SCHEMA_VERSION = "OIA-005"
ENGINE_ID = "OIA-005"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
OPPORTUNITIES_ALLOWED = False
RAW_CORPUS_MUTATION_ALLOWED = False

USEFUL = "useful"
WATCHLIST = "watchlist"
NOT_USEFUL = "not_useful"


class MarketUsefulnessError(RuntimeError):
    pass


class MarketUsefulnessConfigurationError(MarketUsefulnessError):
    pass


class MarketUsefulnessInvariantError(MarketUsefulnessError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise MarketUsefulnessInvariantError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, datetime):
        return _aware_utc(value, "datetime").isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))


def _decimal(value: Optional[str], default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return Decimal(default)
    return result if result.is_finite() else Decimal(default)


def _clamp(value: Decimal, low: Decimal = Decimal("0"), high: Decimal = Decimal("1")) -> Decimal:
    return max(low, min(high, value))


def _component(value: Decimal, target: Decimal) -> Decimal:
    if target <= 0:
        raise MarketUsefulnessConfigurationError("Scoring targets must be positive.")
    return _clamp(value / target)


def _inverse_component(value: Decimal, maximum: Decimal) -> Decimal:
    if maximum <= 0:
        raise MarketUsefulnessConfigurationError("Scoring maximums must be positive.")
    return _clamp(Decimal("1") - (value / maximum))


def _score_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


@dataclass(frozen=True)
class OracleMarketUsefulnessRecord:
    market_id: str
    classification: str
    usefulness_score: str
    data_depth_score: str
    activity_score: str
    movement_score: str
    spread_score: str
    liquidity_score: str
    observation_count: int
    observations_per_hour: float
    transitions_per_hour: float
    transition_rate: float
    normalized_volatility_ratio: Optional[str]
    movement_efficiency_ratio: Optional[str]
    spread_to_price_ratio: Optional[str]
    latest_volume_fp: Optional[str]
    latest_liquidity_dollars: Optional[str]
    reason_codes: tuple[str, ...]
    feature_hash: str
    usefulness_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleMarketUsefulnessReport:
    schema_version: str
    engine_id: str
    scored_at: datetime
    feature_report_hash: str
    feature_market_count: int
    scored_market_count: int
    useful_market_count: int
    watchlist_market_count: int
    not_useful_market_count: int
    average_usefulness_score: str
    markets: tuple[OracleMarketUsefulnessRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    opportunities_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleMarketUsefulnessScoringEngine:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    opportunities_allowed = False
    raw_corpus_mutation_allowed = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        stale_after_seconds: int = 300,
        minimum_observations: int = 3,
        market_limit: int = 1000,
        history_limit_per_market: int = 1000,
        useful_threshold: Decimal | str = "70",
        watchlist_threshold: Decimal | str = "45",
    ) -> None:
        if not callable(connection_factory):
            raise MarketUsefulnessConfigurationError("connection_factory must be callable.")
        for name, value in (("stale_after_seconds", stale_after_seconds), ("minimum_observations", minimum_observations), ("market_limit", market_limit), ("history_limit_per_market", history_limit_per_market)):
            if int(value) <= 0:
                raise MarketUsefulnessConfigurationError(f"{name} must be positive.")
        self._useful_threshold = _decimal(str(useful_threshold))
        self._watchlist_threshold = _decimal(str(watchlist_threshold))
        if not (Decimal("0") <= self._watchlist_threshold < self._useful_threshold <= Decimal("100")):
            raise MarketUsefulnessConfigurationError("Thresholds must satisfy 0 <= watchlist < useful <= 100.")
        self._connection_factory = connection_factory
        self._stale_after_seconds = int(stale_after_seconds)
        self._minimum_observations = int(minimum_observations)
        self._market_limit = int(market_limit)
        self._history_limit_per_market = int(history_limit_per_market)

    def score(self, *, scored_at: Optional[datetime] = None) -> OracleMarketUsefulnessReport:
        checked = _aware_utc(scored_at or datetime.now(timezone.utc), "scored_at")
        feature_report = OracleCanonicalMarketFeatureExtractionEngine(
            connection_factory=self._connection_factory,
            stale_after_seconds=self._stale_after_seconds,
            minimum_observations=self._minimum_observations,
            market_limit=self._market_limit,
            history_limit_per_market=self._history_limit_per_market,
        ).extract(extracted_at=checked)
        return self.score_feature_report(feature_report=feature_report, scored_at=checked)

    def score_feature_report(self, *, feature_report: OracleCanonicalMarketFeatureReport, scored_at: Optional[datetime] = None) -> OracleMarketUsefulnessReport:
        checked = _aware_utc(scored_at or feature_report.extracted_at, "scored_at")
        records = tuple(self._score_market(item) for item in sorted(feature_report.markets, key=lambda x: x.market_id))
        useful = sum(item.classification == USEFUL for item in records)
        watchlist = sum(item.classification == WATCHLIST for item in records)
        not_useful = sum(item.classification == NOT_USEFUL for item in records)
        average = Decimal("0") if not records else sum((_decimal(item.usefulness_score) for item in records), Decimal("0")) / Decimal(len(records))
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "scored_at": checked,
            "feature_report_hash": feature_report.report_hash,
            "feature_market_count": feature_report.feature_market_count,
            "scored_market_count": len(records),
            "useful_market_count": useful,
            "watchlist_market_count": watchlist,
            "not_useful_market_count": not_useful,
            "average_usefulness_score": _score_text(average),
            "markets": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "opportunities_allowed": False,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleMarketUsefulnessReport(**payload, report_hash=stable_hash(payload))

    def _score_market(self, feature: OracleCanonicalMarketFeatureRecord) -> OracleMarketUsefulnessRecord:
        depth = _component(Decimal(feature.observation_count), Decimal("60"))
        activity = (_component(Decimal(str(feature.observations_per_hour)), Decimal("60")) + _component(Decimal(str(feature.transitions_per_hour)), Decimal("12"))) / Decimal("2")
        volatility = _decimal(feature.normalized_volatility_ratio)
        efficiency = _decimal(feature.movement_efficiency_ratio)
        movement = (_component(volatility, Decimal("0.08")) + _component(efficiency, Decimal("0.60"))) / Decimal("2")
        spread_ratio = _decimal(feature.spread_to_price_ratio, "1")
        spread = _inverse_component(spread_ratio, Decimal("0.20"))
        volume = _decimal(feature.latest_volume_fp)
        liquidity = _decimal(feature.latest_liquidity_dollars)
        liquidity_component = (_component(volume, Decimal("1000")) + _component(liquidity, Decimal("5000"))) / Decimal("2")
        total = (depth * Decimal("20") + activity * Decimal("20") + movement * Decimal("25") + spread * Decimal("20") + liquidity_component * Decimal("15"))
        reasons = []
        if depth < Decimal("0.50"): reasons.append("shallow_history")
        if activity < Decimal("0.35"): reasons.append("low_update_activity")
        if movement < Decimal("0.25"): reasons.append("low_information_movement")
        if spread < Decimal("0.40"): reasons.append("wide_spread")
        if liquidity_component < Decimal("0.25"): reasons.append("low_liquidity")
        if total >= self._useful_threshold:
            classification = USEFUL
            if not reasons: reasons.append("meets_usefulness_policy")
        elif total >= self._watchlist_threshold:
            classification = WATCHLIST
            if not reasons: reasons.append("borderline_usefulness")
        else:
            classification = NOT_USEFUL
            if not reasons: reasons.append("below_usefulness_threshold")
        payload = {
            "market_id": feature.market_id,
            "classification": classification,
            "usefulness_score": _score_text(total),
            "data_depth_score": _score_text(depth * Decimal("100")),
            "activity_score": _score_text(activity * Decimal("100")),
            "movement_score": _score_text(movement * Decimal("100")),
            "spread_score": _score_text(spread * Decimal("100")),
            "liquidity_score": _score_text(liquidity_component * Decimal("100")),
            "observation_count": feature.observation_count,
            "observations_per_hour": feature.observations_per_hour,
            "transitions_per_hour": feature.transitions_per_hour,
            "transition_rate": feature.transition_rate,
            "normalized_volatility_ratio": feature.normalized_volatility_ratio,
            "movement_efficiency_ratio": feature.movement_efficiency_ratio,
            "spread_to_price_ratio": feature.spread_to_price_ratio,
            "latest_volume_fp": feature.latest_volume_fp,
            "latest_liquidity_dollars": feature.latest_liquidity_dollars,
            "reason_codes": tuple(sorted(set(reasons))),
            "feature_hash": feature.feature_hash,
        }
        return OracleMarketUsefulnessRecord(**payload, usefulness_hash=stable_hash(payload))


def _load_env(path: Path) -> None:
    if not path.exists(): return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def resolve_database_url() -> str:
    value = os.getenv("ORACLE_POSTGRESQL_URL") or os.getenv("DATABASE_URL")
    if not value:
        raise MarketUsefulnessConfigurationError("Set ORACLE_POSTGRESQL_URL or DATABASE_URL.")
    return value


def connect_postgresql(database_url: str) -> Any:
    try:
        import psycopg
        return psycopg.connect(database_url)
    except ImportError:
        try:
            import psycopg2
            return psycopg2.connect(database_url)
        except ImportError as exc:
            raise MarketUsefulnessConfigurationError("Install psycopg or psycopg2.") from exc


def format_report(report: OracleMarketUsefulnessReport) -> str:
    lines = [
        "=" * 112,
        "ORACLE MARKET USEFULNESS SCORECARD",
        "=" * 112,
        f"Scored at: {report.scored_at.isoformat()}",
        f"Markets: {report.scored_market_count} | useful={report.useful_market_count} | watchlist={report.watchlist_market_count} | not_useful={report.not_useful_market_count}",
        f"Average usefulness score: {report.average_usefulness_score}",
        "-" * 112,
        f"{'MARKET':30} {'STATE':12} {'TOTAL':>7} {'DEPTH':>7} {'ACTIVE':>7} {'MOVE':>7} {'SPREAD':>7} {'LIQ':>7} REASONS",
    ]
    for market in sorted(report.markets, key=lambda item: (-float(item.usefulness_score), item.market_id)):
        lines.append(f"{market.market_id[:30]:30} {market.classification:12} {market.usefulness_score:>7} {market.data_depth_score:>7} {market.activity_score:>7} {market.movement_score:>7} {market.spread_score:>7} {market.liquidity_score:>7} {','.join(market.reason_codes)}")
    if not report.markets: lines.append("No quality-approved feature records were available for scoring.")
    lines.extend(["-" * 112, f"Feature report hash:    {report.feature_report_hash}", f"Usefulness report hash: {report.report_hash}", "READ-ONLY: usefulness measurement only; no opportunities, signals, alerts, Q Series handoff, or execution."])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Score Oracle markets for research usefulness.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--useful-threshold", default="70")
    parser.add_argument("--watchlist-threshold", default="45")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _load_env(Path(args.env_file))
    engine = OracleMarketUsefulnessScoringEngine(connection_factory=lambda: connect_postgresql(resolve_database_url()), stale_after_seconds=args.stale_after_seconds, minimum_observations=args.minimum_observations, market_limit=args.market_limit, history_limit_per_market=args.history_limit_per_market, useful_threshold=args.useful_threshold, watchlist_threshold=args.watchlist_threshold)
    report = engine.score()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
