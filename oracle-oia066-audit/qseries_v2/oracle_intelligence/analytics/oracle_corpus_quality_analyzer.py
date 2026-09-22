"""
OIA-002
Oracle Corpus Quality Analyzer

Read-only deterministic data-quality classification over the canonical Oracle
PostgreSQL corpus. Raw observations are never deleted or changed. Markets are
classified as accepted, quarantined, or rejected with explicit reason codes.
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

SCHEMA_VERSION = "OIA-002"
ENGINE_ID = "OIA-002"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
RAW_CORPUS_MUTATION_ALLOWED = False

ACCEPTED = "accepted"
QUARANTINED = "quarantined"
REJECTED = "rejected"

REASON_STALE_MARKET = "stale_market"
REASON_INSUFFICIENT_HISTORY = "insufficient_history"
REASON_MISSING_PRICE = "missing_price"
REASON_INVALID_PRICE = "invalid_price"
REASON_CROSSED_SPREAD = "crossed_spread"
REASON_MISSING_MARKET_ID = "missing_market_id"


class CorpusQualityAnalyzerError(RuntimeError):
    pass


class CorpusQualityConfigurationError(CorpusQualityAnalyzerError):
    pass


class CorpusQualityQueryError(CorpusQualityAnalyzerError):
    pass


class CorpusQualityInvariantError(CorpusQualityAnalyzerError):
    pass


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CorpusQualityInvariantError(f"{name} must be timezone-aware.")
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


def _safe_int(value: Any, name: str) -> int:
    try:
        result = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise CorpusQualityQueryError(f"{name} must be integer-compatible.") from exc
    if result < 0:
        raise CorpusQualityQueryError(f"{name} cannot be negative.")
    return result


def _price(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


@dataclass(frozen=True)
class OracleMarketQualityRecord:
    market_id: str
    observation_count: int
    latest_persisted_at: datetime
    age_seconds: float
    yes_bid_dollars: Optional[str]
    yes_ask_dollars: Optional[str]
    last_price_dollars: Optional[str]
    status: str
    reason_codes: tuple[str, ...]
    quality_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


@dataclass(frozen=True)
class OracleCorpusQualityReport:
    schema_version: str
    engine_id: str
    analyzed_at: datetime
    market_count: int
    accepted_count: int
    quarantined_count: int
    rejected_count: int
    acceptance_rate: float
    stale_after_seconds: int
    minimum_observations: int
    markets: tuple[OracleMarketQualityRecord, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    raw_corpus_mutation_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))


QUALITY_SQL = """
/* oia002:market_quality */
WITH normalized AS (
    SELECT sequence_number, persisted_at,
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
    SELECT *, ROW_NUMBER() OVER (PARTITION BY market_id ORDER BY sequence_number DESC) AS recency_rank,
           COUNT(*) OVER (PARTITION BY market_id) AS observation_count,
           MAX(persisted_at) OVER (PARTITION BY market_id) AS latest_persisted_at
    FROM identified
)
SELECT COALESCE(market_id, ''), observation_count, latest_persisted_at,
       payload->>'yes_bid_dollars', payload->>'yes_ask_dollars',
       payload->>'last_price_dollars'
FROM ranked
WHERE recency_rank = 1
ORDER BY COALESCE(market_id, '') ASC
LIMIT %s
"""


class OracleCorpusQualityAnalyzer:
    read_only = True
    execution_allowed = False
    alerts_allowed = False
    qseries_handoff_allowed = False
    raw_corpus_mutation_allowed = False

    def __init__(
        self,
        *,
        connection_factory: Callable[[], Any],
        stale_after_seconds: int = 300,
        minimum_observations: int = 3,
        market_limit: int = 1000,
    ) -> None:
        if not callable(connection_factory):
            raise CorpusQualityConfigurationError("connection_factory must be callable.")
        if int(stale_after_seconds) <= 0:
            raise CorpusQualityConfigurationError("stale_after_seconds must be positive.")
        if int(minimum_observations) <= 0:
            raise CorpusQualityConfigurationError("minimum_observations must be positive.")
        if int(market_limit) <= 0:
            raise CorpusQualityConfigurationError("market_limit must be positive.")
        self._connection_factory = connection_factory
        self._stale_after_seconds = int(stale_after_seconds)
        self._minimum_observations = int(minimum_observations)
        self._market_limit = int(market_limit)

    def analyze(self, *, analyzed_at: Optional[datetime] = None) -> OracleCorpusQualityReport:
        checked = _aware_utc(analyzed_at or datetime.now(timezone.utc), "analyzed_at")
        connection = self._connection_factory()
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(QUALITY_SQL, (self._market_limit,))
                rows = cursor.fetchall() or []
            finally:
                cursor.close()
        except CorpusQualityAnalyzerError:
            raise
        except Exception as exc:
            raise CorpusQualityQueryError("Unable to analyze canonical PostgreSQL corpus quality.") from exc
        finally:
            connection.close()

        records = tuple(self._classify_row(row=row, analyzed_at=checked) for row in rows)
        accepted = sum(1 for record in records if record.status == ACCEPTED)
        quarantined = sum(1 for record in records if record.status == QUARANTINED)
        rejected = sum(1 for record in records if record.status == REJECTED)
        count = len(records)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "engine_id": ENGINE_ID,
            "analyzed_at": checked,
            "market_count": count,
            "accepted_count": accepted,
            "quarantined_count": quarantined,
            "rejected_count": rejected,
            "acceptance_rate": 0.0 if count == 0 else accepted / count,
            "stale_after_seconds": self._stale_after_seconds,
            "minimum_observations": self._minimum_observations,
            "markets": records,
            "read_only": True,
            "execution_allowed": False,
            "alerts_allowed": False,
            "qseries_handoff_allowed": False,
            "raw_corpus_mutation_allowed": False,
        }
        return OracleCorpusQualityReport(**payload, report_hash=stable_hash(payload))

    def _classify_row(self, *, row: Sequence[Any], analyzed_at: datetime) -> OracleMarketQualityRecord:
        if len(row) < 6:
            raise CorpusQualityQueryError("Market quality row does not satisfy OIA-002 contract.")
        market_id = str(row[0] or "").strip()
        observation_count = _safe_int(row[1], "market.observation_count")
        persisted_at = _aware_utc(row[2], "market.latest_persisted_at")
        age_seconds = max(0.0, (analyzed_at - persisted_at).total_seconds())
        bid_text = None if row[3] is None else str(row[3]).strip() or None
        ask_text = None if row[4] is None else str(row[4]).strip() or None
        last_text = None if row[5] is None else str(row[5]).strip() or None
        bid = _price(bid_text)
        ask = _price(ask_text)
        last = _price(last_text)

        hard_reasons: list[str] = []
        soft_reasons: list[str] = []
        if not market_id:
            hard_reasons.append(REASON_MISSING_MARKET_ID)
        supplied_prices = (bid_text, ask_text, last_text)
        parsed_prices = (bid, ask, last)
        if all(value is None for value in supplied_prices):
            hard_reasons.append(REASON_MISSING_PRICE)
        elif any(text is not None and parsed is None for text, parsed in zip(supplied_prices, parsed_prices)):
            hard_reasons.append(REASON_INVALID_PRICE)
        elif any(value is not None and (value < Decimal("0") or value > Decimal("1")) for value in parsed_prices):
            hard_reasons.append(REASON_INVALID_PRICE)
        if bid is not None and ask is not None and bid > ask:
            hard_reasons.append(REASON_CROSSED_SPREAD)
        if age_seconds > self._stale_after_seconds:
            soft_reasons.append(REASON_STALE_MARKET)
        if observation_count < self._minimum_observations:
            soft_reasons.append(REASON_INSUFFICIENT_HISTORY)

        reasons = tuple(sorted(set(hard_reasons + soft_reasons)))
        status = REJECTED if hard_reasons else (QUARANTINED if soft_reasons else ACCEPTED)
        payload = {
            "market_id": market_id,
            "observation_count": observation_count,
            "latest_persisted_at": persisted_at,
            "age_seconds": age_seconds,
            "yes_bid_dollars": bid_text,
            "yes_ask_dollars": ask_text,
            "last_price_dollars": last_text,
            "status": status,
            "reason_codes": reasons,
        }
        return OracleMarketQualityRecord(**payload, quality_hash=stable_hash(payload))


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def resolve_database_url() -> str:
    for key in ("DATABASE_URL", "POSTGRES_URL", "POSTGRESQL_URL", "ORACLE_DATABASE_URL"):
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    raise CorpusQualityConfigurationError("No PostgreSQL URL found. Configure DATABASE_URL in .env.")


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
        raise CorpusQualityConfigurationError("Neither psycopg nor psycopg2 is installed.") from exc


def format_report(report: OracleCorpusQualityReport) -> str:
    lines = [
        "=" * 78,
        " ORACLE INTELLIGENCE ANALYTICS - CORPUS QUALITY ANALYZER",
        "=" * 78,
        f"Analyzed (UTC):         {report.analyzed_at.isoformat()}",
        f"Markets analyzed:       {report.market_count}",
        f"Accepted:               {report.accepted_count}",
        f"Quarantined:            {report.quarantined_count}",
        f"Rejected:               {report.rejected_count}",
        f"Acceptance rate:        {report.acceptance_rate:.2%}",
        f"Stale threshold:        {report.stale_after_seconds}s",
        f"Minimum observations:   {report.minimum_observations}",
        "-" * 78,
        "STATUS       MARKET                              OBS   AGE(s)  REASONS",
    ]
    for market in report.markets:
        reasons = ",".join(market.reason_codes) or "none"
        lines.append(
            f"{market.status[:12]:12} {market.market_id[:35]:35} "
            f"{market.observation_count:5d} {market.age_seconds:8.0f}  {reasons}"
        )
    if not report.markets:
        lines.append("No market snapshots were found.")
    lines.extend([
        "-" * 78,
        f"Report hash: {report.report_hash}",
        "READ-ONLY: raw observations are preserved; no alerts, trades, or execution.",
    ])
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify Oracle corpus market quality.")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--stale-after-seconds", type=int, default=300)
    parser.add_argument("--minimum-observations", type=int, default=3)
    parser.add_argument("--market-limit", type=int, default=1000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    _load_env(Path(args.env_file))
    database_url = resolve_database_url()
    analyzer = OracleCorpusQualityAnalyzer(
        connection_factory=lambda: connect_postgresql(database_url),
        stale_after_seconds=args.stale_after_seconds,
        minimum_observations=args.minimum_observations,
        market_limit=args.market_limit,
    )
    report = analyzer.analyze()
    print(json.dumps(dict(report.to_dict()), indent=2, sort_keys=True) if args.json else format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
