"""
OIA-004
Oracle Canonical Market Feature Extraction Engine

Read-only deterministic feature extraction over OIA-003 market statistics.
The engine converts descriptive market history into canonical trader-research
features without ranking markets, producing signals, publishing alerts, or
allowing execution.
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

from .oracle_market_statistics_engine import (
    OracleMarketStatisticsEngine,
    OracleMarketStatisticsRecord,
    OracleMarketStatisticsReport,
)

SCHEMA_VERSION = "OIA-004"
ENGINE_ID = "OIA-004"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
RANKING_ALLOWED = False
RAW_CORPUS_MUTATION_ALLOWED = False


class MarketFeatureExtractionError(RuntimeError):
    pass


class MarketFeatureConfigurationError(MarketFeatureExtractionError):
    pass


class MarketFeatureInvariantError(MarketFeatureExtractionError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise MarketFeatureInvariantError(f"{name} must be timezone-aware.")
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


def _decimal(value: Optional[str]) -> Optional[Decimal]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        result = Decimal(text)
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _text(value: Optional[Decimal]) -> Optional[str]:
    return None if value is None else format(value, "f")


def _ratio(numerator: Optional[Decimal], denominator: Optional[Decimal]) -> Optional[Decimal]:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


@dataclass(frozen=True)
class OracleCanonicalMarketFeatureRecord:
    market_id: str
    observation_count: int
    priced_observation_count: int
    history_duration_seconds: float
    observations_per_hour: float
    average_update_interval_seconds: float
    price_transition_count: int
    transitions_per_hour: float
    transition_rate: float
    latest_price_dollars: Optional[str]
    price_range_dollars: Optional[str]
    price_stddev_dollars: Optional[str]
    directional_change_dollars: Optional[str]
    absolute_movement_dollars: Optional[str]
    directional_change_ratio: Optional[str]
    normalized_volatility_ratio: Optional[str]
    movement_efficiency_ratio: Optional[str]
    average_spread_dollars: Optional[str]
    maximum_spread_dollars: Optional[str]
    spread_to_price_ratio: Optional[str]
    latest_volume_fp: Optional[str]
    latest_liquidity_dollars: Optional[str]
    feature_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCanonicalMarketFeatureReport:
    schema_version: str
    engine_id: str
    extracted_at: datetime
    statistics_report_hash: str
    statistics_market_count: int
    feature_market_count: int
    total_observations_represented: int
    total_price_transitions_represented: int
    markets: tuple[OracleCanonicalMarketFeatureRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    ranking_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


class OracleCanonicalMarketFeatureExtractionEngine:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
    ranking_allowed = False
    raw_corpus_mutation_allowed = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        stale_after_seconds: int = 300,
        minimum_observations: int = 3,
        market_limit: int = 1000,
        history_limit_per_market: int = 1000,
    ) -> None:
        if not callable(connection_factory):
            raise MarketFeatureConfigurationError("connection_factory must be callable.")
        for name, value in (
            ("stale_after_seconds", stale_after_seconds),
            ("minimum_observations", minimum_observations),
            ("market_limit", market_limit),
            ("history_limit_per_market", history_limit_per_market),
        ):
            if int(value) <= 0:
                raise MarketFeatureConfigurationError(f"{name} must be positive.")
        self._connection_factory = connection_factory
        self._stale_after_seconds = int(stale_after_seconds)
        self._minimum_observations = int(minimum_observations)
        self._market_limit = int(market_limit)
        self._history_limit_per_market = int(history_limit_per_market)

    def extract(self, *, extracted_at: Optional[datetime] = None) -> OracleCanonicalMarketFeatureReport:
        checked = _aware_utc(extracted_at or datetime.now(timezone.utc), "extracted_at")
        statistics = OracleMarketStatisticsEngine(
            connection_factory=self._connection_factory,
            stale_after_seconds=self._stale_after_seconds,
            minimum_observations=self._minimum_observations,
            market_limit=self._market_limit,
            history_limit_per_market=self._history_limit_per_market,
        ).analyze(analyzed_at=checked)
        return self.extract_statistics_report(statistics_report=statistics, extracted_at=checked)

    def extract_statistics_report(
        self,
        *,
        statistics_report: OracleMarketStatisticsReport,
        extracted_at: Optional[datetime] = None,
    ) -> OracleCanonicalMarketFeatureReport:
        checked = _aware_utc(extracted_at or statistics_report.analyzed_at, "extracted_at")
        records = tuple(
            self._extract_market(record)
            for record in sorted(statistics_report.markets, key=lambda item: item.market_id)
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "extracted_at": checked,
            "statistics_report_hash": statistics_report.report_hash,
            "statistics_market_count": statistics_report.statistics_market_count,
            "feature_market_count": len(records),
            "total_observations_represented": sum(item.observation_count for item in records),
            "total_price_transitions_represented": sum(item.price_transition_count for item in records),
            "markets": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "ranking_allowed": False,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleCanonicalMarketFeatureReport(**payload, report_hash=stable_hash(payload))

    def _extract_market(
        self,
        record: OracleMarketStatisticsRecord,
    ) -> OracleCanonicalMarketFeatureRecord:
        if record.observation_count <= 0:
            raise MarketFeatureInvariantError("Market statistics observation_count must be positive.")
        duration_hours = Decimal(str(record.history_duration_seconds)) / Decimal("3600")
        observations_per_hour = (
            float(Decimal(record.observation_count) / duration_hours)
            if duration_hours > 0 else float(record.observation_count)
        )
        transitions_per_hour = (
            float(Decimal(record.price_transition_count) / duration_hours)
            if duration_hours > 0 else float(record.price_transition_count)
        )
        latest_price = _decimal(record.latest_price_dollars)
        price_range = _decimal(record.price_range_dollars)
        price_stddev = _decimal(record.price_stddev_dollars)
        directional_change = _decimal(record.absolute_price_change_dollars)
        absolute_movement = None if directional_change is None else abs(directional_change)
        average_spread = _decimal(record.average_spread_dollars)
        maximum_spread = _decimal(record.maximum_spread_dollars)
        directional_change_ratio = _ratio(directional_change, latest_price)
        normalized_volatility_ratio = _ratio(price_stddev, latest_price)
        movement_efficiency_ratio = _ratio(absolute_movement, price_range)
        spread_to_price_ratio = _ratio(average_spread, latest_price)
        payload = {
            "market_id": record.market_id,
            "observation_count": record.observation_count,
            "priced_observation_count": record.priced_observation_count,
            "history_duration_seconds": record.history_duration_seconds,
            "observations_per_hour": observations_per_hour,
            "average_update_interval_seconds": record.average_update_interval_seconds,
            "price_transition_count": record.price_transition_count,
            "transitions_per_hour": transitions_per_hour,
            "transition_rate": record.transition_rate,
            "latest_price_dollars": record.latest_price_dollars,
            "price_range_dollars": record.price_range_dollars,
            "price_stddev_dollars": record.price_stddev_dollars,
            "directional_change_dollars": record.absolute_price_change_dollars,
            "absolute_movement_dollars": _text(absolute_movement),
            "directional_change_ratio": _text(directional_change_ratio),
            "normalized_volatility_ratio": _text(normalized_volatility_ratio),
            "movement_efficiency_ratio": _text(movement_efficiency_ratio),
            "average_spread_dollars": record.average_spread_dollars,
            "maximum_spread_dollars": record.maximum_spread_dollars,
            "spread_to_price_ratio": _text(spread_to_price_ratio),
            "latest_volume_fp": record.latest_volume_fp,
            "latest_liquidity_dollars": record.latest_liquidity_dollars,
        }
        return OracleCanonicalMarketFeatureRecord(**payload, feature_hash=stable_hash(payload))


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def resolve_database_url() -> str:
    for key in ("DATABASE_URL", "POSTGRES_URL", "POSTGRESQL_URL", "ORACLE_DATABASE_URL"):
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    raise MarketFeatureConfigurationError("No PostgreSQL URL found. Configure DATABASE_URL in .env.")


def connect_postgresql(database_url: str) -> Any:
    try:
        import psycopg
        return psycopg.connect(database_url)
    except ImportError:
        pass
    try:
        import psycopg2
        return psycopg2.connect(database_url)
    except ImportError as exc:
        raise MarketFeatureConfigurationError("Neither psycopg nor psycopg2 is installed.") from exc


def format_report(report: OracleCanonicalMarketFeatureReport) -> str:
    lines = [
        "=" * 112,
        " ORACLE INTELLIGENCE ANALYTICS - CANONICAL MARKET FEATURE EXTRACTION",
        "=" * 112,
        f"Extracted (UTC):         {report.extracted_at.isoformat()}",
        f"Statistics markets:      {report.statistics_market_count}",
        f"Feature markets:         {report.feature_market_count}",
        f"Observations represented:{report.total_observations_represented:>12}",
        f"Transitions represented: {report.total_price_transitions_represented}",
        "-" * 112,
        "MARKET                         OBS/H   TRANS/H  VOL RATIO  SPRD RATIO  MOVE EFF  DIR CHANGE  LIQUIDITY",
    ]
    for market in report.markets:
        lines.append(
            f"{market.market_id[:30]:30} "
            f"{market.observations_per_hour:7.2f} "
            f"{market.transitions_per_hour:9.2f} "
            f"{(market.normalized_volatility_ratio or '-'):10} "
            f"{(market.spread_to_price_ratio or '-'):11} "
            f"{(market.movement_efficiency_ratio or '-'):9} "
            f"{(market.directional_change_dollars or '-'):11} "
            f"{(market.latest_liquidity_dollars or '-'):>10}"
        )
    if not report.markets:
        lines.append("No quality-approved market statistics were available for feature extraction.")
    lines.extend([
        "-" * 112,
        f"Statistics report hash: {report.statistics_report_hash}",
        f"Feature report hash:    {report.report_hash}",
        "READ-ONLY: canonical research features only; no ranking, signals, alerts, trades, or execution.",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract canonical features from quality-approved Oracle markets.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _load_env(Path(args.env_file))
    database_url = resolve_database_url()
    engine = OracleCanonicalMarketFeatureExtractionEngine(
        connection_factory=lambda: connect_postgresql(database_url),
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
        history_limit_per_market=args.history_limit_per_market,
    )
    report = engine.extract()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
