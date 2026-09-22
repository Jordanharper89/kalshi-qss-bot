from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

MODULE = r'''"""
OIA-003
Oracle Market Statistics Engine

Read-only deterministic market-statistics analysis over quality-approved Oracle
markets. The engine consumes OIA-002 classifications, preserves the raw corpus,
and computes descriptive trader-facing statistics without producing signals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

from .oracle_corpus_quality_analyzer import (
    ACCEPTED,
    OracleCorpusQualityAnalyzer,
    OracleCorpusQualityReport,
)

SCHEMA_VERSION = "OIA-003"
ENGINE_ID = "OIA-003"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
SIGNALS_ALLOWED = False
RAW_CORPUS_MUTATION_ALLOWED = False


class MarketStatisticsEngineError(RuntimeError):
    pass


class MarketStatisticsConfigurationError(MarketStatisticsEngineError):
    pass


class MarketStatisticsQueryError(MarketStatisticsEngineError):
    pass


class MarketStatisticsInvariantError(MarketStatisticsEngineError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise MarketStatisticsInvariantError(f"{name} must be timezone-aware.")
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


def _decimal(value: Any) -> Optional[Decimal]:
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


def _mean(values: Sequence[Decimal]) -> Optional[Decimal]:
    return None if not values else sum(values, Decimal("0")) / Decimal(len(values))


def _population_stddev(values: Sequence[Decimal]) -> Optional[Decimal]:
    if not values:
        return None
    mean = _mean(values)
    assert mean is not None
    variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
    return Decimal(str(math.sqrt(float(variance))))


def _text(value: Optional[Decimal]) -> Optional[str]:
    return None if value is None else format(value, "f")


@dataclass(frozen=True)
class OracleMarketStatisticsRecord:
    market_id: str
    observation_count: int
    priced_observation_count: int
    first_observed_at: datetime
    latest_observed_at: datetime
    history_duration_seconds: float
    average_update_interval_seconds: float
    price_transition_count: int
    transition_rate: float
    first_price_dollars: Optional[str]
    latest_price_dollars: Optional[str]
    minimum_price_dollars: Optional[str]
    maximum_price_dollars: Optional[str]
    price_range_dollars: Optional[str]
    mean_price_dollars: Optional[str]
    price_stddev_dollars: Optional[str]
    absolute_price_change_dollars: Optional[str]
    average_spread_dollars: Optional[str]
    maximum_spread_dollars: Optional[str]
    latest_volume_fp: Optional[str]
    latest_liquidity_dollars: Optional[str]
    statistics_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleMarketStatisticsReport:
    schema_version: str
    engine_id: str
    analyzed_at: datetime
    quality_report_hash: str
    quality_market_count: int
    accepted_market_count: int
    statistics_market_count: int
    total_observations_analyzed: int
    total_price_transitions: int
    markets: tuple[OracleMarketStatisticsRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    signals_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


STATISTICS_SQL = """
/* oia003:accepted_market_history */
WITH normalized AS (
    SELECT sequence_number, observed_at, persisted_at,
           COALESCE(canonical_observation_json->'raw_observation'->'payload',
                    canonical_observation_json->'payload', '{}'::jsonb) AS payload
    FROM oracle_canonical_observations
    WHERE observation_type = 'market_snapshot'
), identified AS (
    SELECT *, COALESCE(NULLIF(payload->>'source_market_id',''),
                       NULLIF(payload->>'market_id',''),
                       NULLIF(payload->>'source_symbol','')) AS market_id
    FROM normalized
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY market_id ORDER BY sequence_number DESC
    ) AS market_recency_rank
    FROM identified
    WHERE market_id = ANY(%s)
)
SELECT market_id, observed_at, sequence_number,
       payload->>'yes_bid_dollars', payload->>'yes_ask_dollars',
       payload->>'last_price_dollars', payload->>'volume_fp',
       payload->>'liquidity_dollars'
FROM ranked
WHERE market_recency_rank <= %s
ORDER BY market_id ASC, sequence_number ASC
"""


class OracleMarketStatisticsEngine:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    signals_allowed = False
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
            raise MarketStatisticsConfigurationError("connection_factory must be callable.")
        for name, value in (
            ("stale_after_seconds", stale_after_seconds),
            ("minimum_observations", minimum_observations),
            ("market_limit", market_limit),
            ("history_limit_per_market", history_limit_per_market),
        ):
            if int(value) <= 0:
                raise MarketStatisticsConfigurationError(f"{name} must be positive.")
        self._connection_factory = connection_factory
        self._stale_after_seconds = int(stale_after_seconds)
        self._minimum_observations = int(minimum_observations)
        self._market_limit = int(market_limit)
        self._history_limit_per_market = int(history_limit_per_market)

    def analyze(self, *, analyzed_at: Optional[datetime] = None) -> OracleMarketStatisticsReport:
        checked = _aware_utc(analyzed_at or datetime.now(timezone.utc), "analyzed_at")
        quality = OracleCorpusQualityAnalyzer(
            connection_factory=self._connection_factory,
            stale_after_seconds=self._stale_after_seconds,
            minimum_observations=self._minimum_observations,
            market_limit=self._market_limit,
        ).analyze(analyzed_at=checked)
        return self.analyze_quality_report(quality_report=quality, analyzed_at=checked)

    def analyze_quality_report(
        self,
        *,
        quality_report: OracleCorpusQualityReport,
        analyzed_at: Optional[datetime] = None,
    ) -> OracleMarketStatisticsReport:
        checked = _aware_utc(analyzed_at or quality_report.analyzed_at, "analyzed_at")
        accepted_ids = tuple(
            sorted(record.market_id for record in quality_report.markets if record.status == ACCEPTED)
        )
        rows: Sequence[Sequence[Any]] = ()
        if accepted_ids:
            connection = self._connection_factory()
            try:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        STATISTICS_SQL,
                        (list(accepted_ids), self._history_limit_per_market),
                    )
                    rows = cursor.fetchall() or []
                finally:
                    cursor.close()
            except MarketStatisticsEngineError:
                raise
            except Exception as exc:
                raise MarketStatisticsQueryError(
                    "Unable to analyze quality-approved market history."
                ) from exc
            finally:
                connection.close()

        grouped: dict[str, list[Sequence[Any]]] = {market_id: [] for market_id in accepted_ids}
        for row in rows:
            if len(row) < 8:
                raise MarketStatisticsQueryError("Market statistics row violates OIA-003 contract.")
            market_id = str(row[0] or "").strip()
            if market_id in grouped:
                grouped[market_id].append(row)
        records = tuple(
            self._calculate_market(market_id=market_id, rows=grouped[market_id])
            for market_id in accepted_ids
            if grouped[market_id]
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "analyzed_at": checked,
            "quality_report_hash": quality_report.report_hash,
            "quality_market_count": quality_report.market_count,
            "accepted_market_count": len(accepted_ids),
            "statistics_market_count": len(records),
            "total_observations_analyzed": sum(record.observation_count for record in records),
            "total_price_transitions": sum(record.price_transition_count for record in records),
            "markets": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "signals_allowed": False,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleMarketStatisticsReport(**payload, report_hash=stable_hash(payload))

    def _calculate_market(
        self,
        *,
        market_id: str,
        rows: Sequence[Sequence[Any]],
    ) -> OracleMarketStatisticsRecord:
        normalized = sorted(rows, key=lambda row: (int(row[2]), _aware_utc(row[1], "observed_at")))
        observed_times = [_aware_utc(row[1], "observed_at") for row in normalized]
        prices: list[Decimal] = []
        spreads: list[Decimal] = []
        latest_volume: Optional[str] = None
        latest_liquidity: Optional[str] = None
        for row in normalized:
            bid = _decimal(row[3])
            ask = _decimal(row[4])
            last = _decimal(row[5])
            price = last if last is not None else (
                None if bid is None or ask is None else (bid + ask) / Decimal("2")
            )
            if price is not None:
                prices.append(price)
            if bid is not None and ask is not None and ask >= bid:
                spreads.append(ask - bid)
            latest_volume = None if row[6] is None else str(row[6]).strip() or None
            latest_liquidity = None if row[7] is None else str(row[7]).strip() or None

        duration = max(0.0, (observed_times[-1] - observed_times[0]).total_seconds())
        average_interval = 0.0 if len(observed_times) <= 1 else duration / (len(observed_times) - 1)
        transitions = sum(1 for left, right in zip(prices, prices[1:]) if left != right)
        transition_rate = 0.0 if len(prices) <= 1 else transitions / (len(prices) - 1)
        first_price = prices[0] if prices else None
        latest_price = prices[-1] if prices else None
        minimum = min(prices) if prices else None
        maximum = max(prices) if prices else None
        price_range = None if minimum is None or maximum is None else maximum - minimum
        absolute_change = None if first_price is None or latest_price is None else latest_price - first_price
        payload = {
            "market_id": market_id,
            "observation_count": len(normalized),
            "priced_observation_count": len(prices),
            "first_observed_at": observed_times[0],
            "latest_observed_at": observed_times[-1],
            "history_duration_seconds": duration,
            "average_update_interval_seconds": average_interval,
            "price_transition_count": transitions,
            "transition_rate": transition_rate,
            "first_price_dollars": _text(first_price),
            "latest_price_dollars": _text(latest_price),
            "minimum_price_dollars": _text(minimum),
            "maximum_price_dollars": _text(maximum),
            "price_range_dollars": _text(price_range),
            "mean_price_dollars": _text(_mean(prices)),
            "price_stddev_dollars": _text(_population_stddev(prices)),
            "absolute_price_change_dollars": _text(absolute_change),
            "average_spread_dollars": _text(_mean(spreads)),
            "maximum_spread_dollars": _text(max(spreads) if spreads else None),
            "latest_volume_fp": latest_volume,
            "latest_liquidity_dollars": latest_liquidity,
        }
        return OracleMarketStatisticsRecord(**payload, statistics_hash=stable_hash(payload))


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
    raise MarketStatisticsConfigurationError("No PostgreSQL URL found. Configure DATABASE_URL in .env.")


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
        raise MarketStatisticsConfigurationError("Neither psycopg nor psycopg2 is installed.") from exc


def format_report(report: OracleMarketStatisticsReport) -> str:
    lines = [
        "=" * 100,
        " ORACLE INTELLIGENCE ANALYTICS - MARKET STATISTICS ENGINE",
        "=" * 100,
        f"Analyzed (UTC):          {report.analyzed_at.isoformat()}",
        f"Quality markets:         {report.quality_market_count}",
        f"Accepted markets:        {report.accepted_market_count}",
        f"Statistics markets:      {report.statistics_market_count}",
        f"Observations analyzed:   {report.total_observations_analyzed}",
        f"Price transitions:       {report.total_price_transitions}",
        "-" * 100,
        "MARKET                         OBS  TRANS  RANGE     AVG SPRD  CHANGE    AVG UPDATE(s)  LIQUIDITY",
    ]
    for market in report.markets:
        lines.append(
            f"{market.market_id[:30]:30} {market.observation_count:5d} "
            f"{market.price_transition_count:6d} "
            f"{(market.price_range_dollars or '-'):9} "
            f"{(market.average_spread_dollars or '-'):9} "
            f"{(market.absolute_price_change_dollars or '-'):9} "
            f"{market.average_update_interval_seconds:13.1f}  "
            f"{(market.latest_liquidity_dollars or '-'):>10}"
        )
    if not report.markets:
        lines.append("No quality-approved market history was available.")
    lines.extend([
        "-" * 100,
        f"Quality report hash: {report.quality_report_hash}",
        f"Statistics hash:     {report.report_hash}",
        "READ-ONLY: descriptive statistics only; no signals, alerts, trades, or execution.",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze statistics for quality-approved Oracle markets.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--history-limit-per-market", type=int, default=1000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _load_env(Path(args.env_file))
    database_url = resolve_database_url()
    engine = OracleMarketStatisticsEngine(
        connection_factory=lambda: connect_postgresql(database_url),
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
        history_limit_per_market=args.history_limit_per_market,
    )
    report = engine.analyze()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

TEST = r'''from datetime import datetime, timezone

from qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine import (
    ENGINE_ID,
    SCHEMA_VERSION,
    OracleMarketStatisticsEngine,
    format_report,
    stable_hash,
)

NOW = datetime(2026, 7, 20, 4, 0, 0, tzinfo=timezone.utc)


class Cursor:
    def __init__(self, mode):
        self.mode = mode
        self.closed = False

    def execute(self, sql, params=None):
        upper = sql.upper()
        assert "INSERT" not in upper and "UPDATE" not in upper and "DELETE" not in upper
        if self.mode == "quality":
            assert "oia002:market_quality" in sql
            assert params == (50,)
        else:
            assert "oia003:accepted_market_history" in sql
            assert params == (["KXACTIVE"], 100)

    def fetchall(self):
        if self.mode == "quality":
            return [
                ("KXACTIVE", 4, datetime(2026, 7, 20, 3, 59, 50, tzinfo=timezone.utc), "0.40", "0.42", "0.41"),
                ("KXSTALE", 4, datetime(2026, 7, 20, 3, 30, 0, tzinfo=timezone.utc), "0.50", "0.54", "0.52"),
                ("KXCROSS", 4, datetime(2026, 7, 20, 3, 59, 55, tzinfo=timezone.utc), "0.70", "0.60", "0.65"),
            ]
        return [
            ("KXACTIVE", datetime(2026, 7, 20, 3, 57, 0, tzinfo=timezone.utc), 1, "0.38", "0.42", "0.40", "100", "500"),
            ("KXACTIVE", datetime(2026, 7, 20, 3, 58, 0, tzinfo=timezone.utc), 2, "0.39", "0.43", "0.41", "120", "550"),
            ("KXACTIVE", datetime(2026, 7, 20, 3, 59, 0, tzinfo=timezone.utc), 3, "0.40", "0.42", "0.41", "140", "600"),
            ("KXACTIVE", datetime(2026, 7, 20, 4, 0, 0, tzinfo=timezone.utc), 4, "0.43", "0.45", "0.44", "160", "650"),
        ]

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, mode):
        self.cursor_value = Cursor(mode)
        self.closed = False

    def cursor(self):
        return self.cursor_value

    def close(self):
        self.closed = True


def run_test():
    modes = iter(("quality", "statistics"))
    connections = []

    def factory():
        connection = Connection(next(modes))
        connections.append(connection)
        return connection

    engine = OracleMarketStatisticsEngine(
        connection_factory=factory,
        stale_after_seconds=300,
        minimum_observations=3,
        market_limit=50,
        history_limit_per_market=100,
    )
    report = engine.analyze(analyzed_at=NOW)
    assert report.schema_version == SCHEMA_VERSION == "OIA-003"
    assert report.engine_id == ENGINE_ID == "OIA-003"
    assert report.quality_market_count == 3
    assert report.accepted_market_count == 1
    assert report.statistics_market_count == 1
    assert report.total_observations_analyzed == 4
    assert report.total_price_transitions == 2
    market = report.markets[0]
    assert market.market_id == "KXACTIVE"
    assert market.observation_count == 4
    assert market.priced_observation_count == 4
    assert market.history_duration_seconds == 180.0
    assert market.average_update_interval_seconds == 60.0
    assert market.price_transition_count == 2
    assert round(market.transition_rate, 6) == round(2 / 3, 6)
    assert market.first_price_dollars == "0.40"
    assert market.latest_price_dollars == "0.44"
    assert market.minimum_price_dollars == "0.40"
    assert market.maximum_price_dollars == "0.44"
    assert market.price_range_dollars == "0.04"
    assert market.absolute_price_change_dollars == "0.04"
    assert market.average_spread_dollars == "0.03"
    assert market.maximum_spread_dollars == "0.04"
    assert market.latest_volume_fp == "160"
    assert market.latest_liquidity_dollars == "650"
    market_payload = dict(market.to_dict())
    market_hash = market_payload.pop("statistics_hash")
    assert market_hash == stable_hash(market_payload)
    report_payload = dict(report.to_dict())
    report_hash = report_payload.pop("report_hash")
    assert report_hash == stable_hash(report_payload)
    assert report.read_only is True
    assert report.signals_allowed is False
    assert report.raw_corpus_mutation_allowed is False
    rendered = format_report(report)
    assert "KXACTIVE" in rendered and "Price transitions:" in rendered
    assert all(connection.closed for connection in connections)
    assert all(connection.cursor_value.closed for connection in connections)
    print("[PASS] OIA-003 Oracle Market Statistics Engine")


if __name__ == "__main__":
    run_test()
'''

INIT = r'''"""Oracle Intelligence Analytics subsystem."""

from .oracle_live_corpus_inspector import (
    OracleCorpusMarketSummary,
    OracleLiveCorpusInspector,
    OracleLiveCorpusReport,
)
from .oracle_corpus_quality_analyzer import (
    ACCEPTED,
    QUARANTINED,
    REJECTED,
    OracleCorpusQualityAnalyzer,
    OracleCorpusQualityReport,
    OracleMarketQualityRecord,
)
from .oracle_market_statistics_engine import (
    OracleMarketStatisticsEngine,
    OracleMarketStatisticsRecord,
    OracleMarketStatisticsReport,
)

__all__ = [
    "ACCEPTED",
    "QUARANTINED",
    "REJECTED",
    "OracleCorpusMarketSummary",
    "OracleLiveCorpusInspector",
    "OracleLiveCorpusReport",
    "OracleCorpusQualityAnalyzer",
    "OracleCorpusQualityReport",
    "OracleMarketQualityRecord",
    "OracleMarketStatisticsEngine",
    "OracleMarketStatisticsRecord",
    "OracleMarketStatisticsReport",
]
'''


def write_full(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"[OK] FULL REPLACEMENT: {path.resolve()}")


def main() -> int:
    print("========================================")
    print(" OIA-003 INSTALLER")
    print(" ORACLE MARKET STATISTICS ENGINE")
    print(" QUALITY-APPROVED DESCRIPTIVE ANALYTICS")
    print("========================================")
    root = Path.cwd()
    dependency = root / "qseries_v2/oracle_intelligence/analytics/oracle_corpus_quality_analyzer.py"
    if not dependency.exists():
        raise SystemExit("[FAIL] OIA-002 Corpus Quality Analyzer not found. Run from repository root.")
    text = dependency.read_text(encoding="utf-8")
    required = (
        'SCHEMA_VERSION = "OIA-002"',
        "class OracleCorpusQualityAnalyzer",
        "class OracleCorpusQualityReport",
        'ACCEPTED = "accepted"',
        "RAW_CORPUS_MUTATION_ALLOWED = False",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"[FAIL] Actual OIA-002 contract mismatch: {missing}")
    print("[OK] Actual OIA-002 corpus quality contract verified")

    package = root / "qseries_v2/oracle_intelligence/analytics"
    module_path = package / "oracle_market_statistics_engine.py"
    init_path = package / "__init__.py"
    test_path = root / "test_oia_003_oracle_market_statistics_engine.py"
    write_full(module_path, MODULE)
    write_full(init_path, INIT)
    write_full(test_path, TEST)
    ast.parse(MODULE)
    ast.parse(INIT)
    ast.parse(TEST)
    print("[OK] OIA-003 production, package, and test syntax verified")
    result = subprocess.run([sys.executable, str(test_path)], cwd=root, check=False)
    if result.returncode != 0:
        raise SystemExit(f"[FAIL] OIA-003 test failed with exit code {result.returncode}")
    print("[OK] OIA-003 test executed successfully")
    print("[DONE] OIA-003 Oracle Market Statistics Engine installed")
    print("\nAnalyze quality-approved live markets with:")
    print("python -m qseries_v2.oracle_intelligence.analytics.oracle_market_statistics_engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
