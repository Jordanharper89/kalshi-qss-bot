"""
OIA-001
Oracle Live Corpus Inspector

Read-only first analytics boundary over the canonical Oracle PostgreSQL corpus.
It reports corpus size, time coverage, collection rate, market coverage, freshness,
and basic trader-facing market activity without generating signals or authorizing
execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence

SCHEMA_VERSION = "OIA-001"
ENGINE_ID = "OIA-001"
READ_ONLY = True
EXECUTION_ALLOWED = False
ALERTS_ALLOWED = False
QSERIES_HANDOFF_ALLOWED = False
TRADE_AUTHORIZATION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False
FUNDS_MOVED = False
PORTFOLIO_MUTATED = False

class LiveCorpusInspectorError(RuntimeError): pass
class LiveCorpusConfigurationError(LiveCorpusInspectorError): pass
class LiveCorpusQueryError(LiveCorpusInspectorError): pass
class LiveCorpusInvariantError(LiveCorpusInspectorError): pass

def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise LiveCorpusInvariantError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)

def _iso(value: Optional[datetime]) -> Optional[str]:
    return None if value is None else _aware_utc(value, "datetime").isoformat()

def _canonical(value: Any) -> Any:
    if is_dataclass(value): return _canonical(asdict(value))
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [_canonical(v) for v in value]
    if isinstance(value, datetime): return _iso(value)
    return value

def stable_hash(value: Any) -> str:
    encoded=json.dumps(_canonical(value),sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()

def _freeze(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(value))

def _safe_int(value: Any, name: str) -> int:
    try: result=int(value or 0)
    except (TypeError,ValueError) as exc: raise LiveCorpusQueryError(f"{name} must be integer-compatible.") from exc
    if result < 0: raise LiveCorpusQueryError(f"{name} cannot be negative.")
    return result

def _safe_float(value: Any, name: str) -> float:
    try: result=float(value or 0.0)
    except (TypeError,ValueError) as exc: raise LiveCorpusQueryError(f"{name} must be numeric.") from exc
    if result < 0: raise LiveCorpusQueryError(f"{name} cannot be negative.")
    return result

@dataclass(frozen=True)
class OracleCorpusMarketSummary:
    market_id: str
    observation_count: int
    first_observed_at: datetime
    latest_observed_at: datetime
    latest_persisted_at: datetime
    latest_yes_bid_dollars: Optional[str]
    latest_yes_ask_dollars: Optional[str]
    latest_last_price_dollars: Optional[str]
    latest_volume_fp: Optional[str]
    latest_liquidity_dollars: Optional[str]
    source_expiration_time: Optional[str]
    age_seconds: float
    stale: bool

@dataclass(frozen=True)
class OracleLiveCorpusReport:
    schema_version: str
    engine_id: str
    inspected_at: datetime
    observation_count: int
    market_count: int
    source_count: int
    acquisition_batch_count: int
    oldest_observed_at: Optional[datetime]
    newest_observed_at: Optional[datetime]
    newest_persisted_at: Optional[datetime]
    corpus_duration_seconds: float
    observations_per_hour: float
    stale_after_seconds: int
    stale_market_count: int
    active_market_count: int
    markets: tuple[OracleCorpusMarketSummary, ...]
    read_only: bool
    execution_allowed: bool
    alerts_allowed: bool
    qseries_handoff_allowed: bool
    report_hash: str

    def to_dict(self) -> Mapping[str, Any]:
        return _freeze(_canonical(asdict(self)))

SUMMARY_SQL = """
/* oia001:corpus_summary */
SELECT COUNT(*), COUNT(DISTINCT source_id), COUNT(DISTINCT acquisition_batch_id),
       MIN(observed_at), MAX(observed_at), MAX(persisted_at)
FROM oracle_canonical_observations
"""

MARKETS_SQL = """
/* oia001:market_summary */
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
    SELECT *, ROW_NUMBER() OVER (PARTITION BY market_id ORDER BY sequence_number DESC) AS recency_rank,
           COUNT(*) OVER (PARTITION BY market_id) AS observation_count,
           MIN(observed_at) OVER (PARTITION BY market_id) AS first_observed_at,
           MAX(observed_at) OVER (PARTITION BY market_id) AS latest_observed_at,
           MAX(persisted_at) OVER (PARTITION BY market_id) AS latest_persisted_at
    FROM identified WHERE market_id IS NOT NULL
)
SELECT market_id, observation_count, first_observed_at, latest_observed_at,
       latest_persisted_at, payload->>'yes_bid_dollars', payload->>'yes_ask_dollars',
       payload->>'last_price_dollars', payload->>'volume_fp',
       payload->>'liquidity_dollars', payload->>'source_expiration_time'
FROM ranked WHERE recency_rank = 1
ORDER BY observation_count DESC, market_id ASC
LIMIT %s
"""

class OracleLiveCorpusInspector:
    read_only=True
    execution_allowed=False
    alerts_allowed=False
    qseries_handoff_allowed=False

    def __init__(self, *, connection_factory: Callable[[], Any], stale_after_seconds: int=300, market_limit: int=100):
        if not callable(connection_factory): raise LiveCorpusConfigurationError("connection_factory must be callable.")
        if int(stale_after_seconds) <= 0: raise LiveCorpusConfigurationError("stale_after_seconds must be positive.")
        if int(market_limit) <= 0: raise LiveCorpusConfigurationError("market_limit must be positive.")
        self._connection_factory=connection_factory
        self._stale_after_seconds=int(stale_after_seconds)
        self._market_limit=int(market_limit)

    def inspect(self, *, inspected_at: Optional[datetime]=None) -> OracleLiveCorpusReport:
        checked=_aware_utc(inspected_at or datetime.now(timezone.utc), "inspected_at")
        connection=self._connection_factory()
        try:
            cursor=connection.cursor()
            try:
                cursor.execute(SUMMARY_SQL)
                summary=cursor.fetchone()
                if summary is None: raise LiveCorpusQueryError("Corpus summary query returned no row.")
                cursor.execute(MARKETS_SQL, (self._market_limit,))
                rows=cursor.fetchall() or []
            finally:
                cursor.close()
        except LiveCorpusInspectorError: raise
        except Exception as exc: raise LiveCorpusQueryError("Unable to inspect canonical PostgreSQL corpus.") from exc
        finally:
            connection.close()

        observation_count=_safe_int(summary[0],"observation_count")
        source_count=_safe_int(summary[1],"source_count")
        batch_count=_safe_int(summary[2],"acquisition_batch_count")
        oldest=summary[3]; newest=summary[4]; persisted=summary[5]
        if oldest is not None: oldest=_aware_utc(oldest,"oldest_observed_at")
        if newest is not None: newest=_aware_utc(newest,"newest_observed_at")
        if persisted is not None: persisted=_aware_utc(persisted,"newest_persisted_at")
        duration=0.0 if oldest is None or newest is None else max(0.0,(newest-oldest).total_seconds())
        rate=0.0 if observation_count == 0 else (float(observation_count) if duration <= 0 else observation_count/(duration/3600.0))
        markets=[]
        for row in rows:
            first=_aware_utc(row[2],"market.first_observed_at")
            latest=_aware_utc(row[3],"market.latest_observed_at")
            latest_persisted=_aware_utc(row[4],"market.latest_persisted_at")
            age=max(0.0,(checked-latest_persisted).total_seconds())
            markets.append(OracleCorpusMarketSummary(
                market_id=str(row[0]), observation_count=_safe_int(row[1],"market.observation_count"),
                first_observed_at=first, latest_observed_at=latest, latest_persisted_at=latest_persisted,
                latest_yes_bid_dollars=None if row[5] is None else str(row[5]),
                latest_yes_ask_dollars=None if row[6] is None else str(row[6]),
                latest_last_price_dollars=None if row[7] is None else str(row[7]),
                latest_volume_fp=None if row[8] is None else str(row[8]),
                latest_liquidity_dollars=None if row[9] is None else str(row[9]),
                source_expiration_time=None if row[10] is None else str(row[10]),
                age_seconds=age, stale=age > self._stale_after_seconds,
            ))
        market_count=len(markets); stale=sum(1 for m in markets if m.stale)
        payload={
            "schema_version":SCHEMA_VERSION,"engine_id":ENGINE_ID,"inspected_at":checked,
            "observation_count":observation_count,"market_count":market_count,"source_count":source_count,
            "acquisition_batch_count":batch_count,"oldest_observed_at":oldest,"newest_observed_at":newest,
            "newest_persisted_at":persisted,"corpus_duration_seconds":duration,
            "observations_per_hour":rate,"stale_after_seconds":self._stale_after_seconds,
            "stale_market_count":stale,"active_market_count":market_count-stale,"markets":tuple(markets),
            "read_only":True,"execution_allowed":False,"alerts_allowed":False,"qseries_handoff_allowed":False,
        }
        return OracleLiveCorpusReport(**payload,report_hash=stable_hash(payload))

def _load_env(path: Path) -> None:
    if not path.exists(): return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line=raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key,value=line.split("=",1); key=key.strip(); value=value.strip()
        if len(value)>=2 and value[0]==value[-1] and value[0] in "\"'": value=value[1:-1]
        if key: os.environ.setdefault(key,value)

def resolve_database_url() -> str:
    for key in ("DATABASE_URL","POSTGRES_URL","POSTGRESQL_URL","ORACLE_DATABASE_URL"):
        value=os.getenv(key)
        if value and value.strip(): return value.strip()
    raise LiveCorpusConfigurationError("No PostgreSQL URL found. Configure DATABASE_URL in .env.")

def connect_postgresql(database_url: str) -> Any:
    try:
        import psycopg
        return psycopg.connect(database_url)
    except ImportError: pass
    try:
        import psycopg2
        return psycopg2.connect(database_url)
    except ImportError as exc: raise LiveCorpusConfigurationError("Neither psycopg nor psycopg2 is installed.") from exc

def format_report(report: OracleLiveCorpusReport) -> str:
    lines=["="*72," ORACLE INTELLIGENCE ANALYTICS - LIVE CORPUS INSPECTOR","="*72,
           f"Inspected (UTC):        {report.inspected_at.isoformat()}",
           f"Observations:           {report.observation_count}",f"Markets returned:       {report.market_count}",
           f"Sources:                {report.source_count}",f"Acquisition batches:    {report.acquisition_batch_count}",
           f"Oldest observation:     {_iso(report.oldest_observed_at) or 'none'}",
           f"Newest observation:     {_iso(report.newest_observed_at) or 'none'}",
           f"Newest persistence:     {_iso(report.newest_persisted_at) or 'none'}",
           f"Corpus duration hours:  {report.corpus_duration_seconds/3600.0:.2f}",
           f"Observations/hour:      {report.observations_per_hour:.2f}",
           f"Active markets:         {report.active_market_count}",f"Stale markets:          {report.stale_market_count}","-"*72]
    if not report.markets: lines.append("No market snapshots were found.")
    else:
        lines.append("MARKET                               OBS   AGE(s)  BID     ASK     LAST    LIQUIDITY")
        for m in report.markets:
            lines.append(f"{m.market_id[:35]:35} {m.observation_count:5d} {m.age_seconds:8.0f}  {(m.latest_yes_bid_dollars or '-'):7} {(m.latest_yes_ask_dollars or '-'):7} {(m.latest_last_price_dollars or '-'):7} {(m.latest_liquidity_dollars or '-'):>10}")
    lines.extend(["-"*72,f"Report hash: {report.report_hash}","READ-ONLY: no alerts, trades, orders, funds, or portfolio mutation."])
    return "\n".join(lines)

def main(argv: Optional[Sequence[str]]=None) -> int:
    parser=argparse.ArgumentParser(description="Inspect Oracle's canonical live PostgreSQL corpus.")
    parser.add_argument("--env-file",default=".env")
    parser.add_argument("--stale-after-seconds",type=int,default=300)
    parser.add_argument("--market-limit",type=int,default=100)
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args(argv)
    _load_env(Path(args.env_file))
    url=resolve_database_url()
    inspector=OracleLiveCorpusInspector(connection_factory=lambda: connect_postgresql(url),stale_after_seconds=args.stale_after_seconds,market_limit=args.market_limit)
    report=inspector.inspect()
    print(json.dumps(dict(report.to_dict()),indent=2,sort_keys=True) if args.json else format_report(report))
    return 0

if __name__ == "__main__": raise SystemExit(main())
