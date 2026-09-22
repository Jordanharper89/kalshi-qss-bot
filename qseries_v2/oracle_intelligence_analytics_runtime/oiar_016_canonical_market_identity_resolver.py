from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect

OIAR_016_BUILD_ID="OIAR-016"
OIAR_016_REVISION="OIAR_016_CANONICAL_MARKET_IDENTITY_RESOLVER_V1"

@dataclass(frozen=True)
class CanonicalMarketIdentity:
    requested_market_id:str
    resolved:bool
    source_market_id:str|None
    market_title:str|None
    event_ticker:str|None
    source_symbol:str|None
    source_close_time:str|None
    source_expiration_time:str|None
    observed_at:str|None
    source_id:str|None
    identity_reason:str
    read_only:bool=True
    execution_authority:bool=False

def resolve_canonical_market_identity(root=None, market_id=None):
    root=Path(root or Path.cwd()).resolve()
    requested=str(market_id or "").strip().upper()
    if not requested:
        raise ValueError("market_id required")

    sql="""
    SELECT observed_at, source_id, canonical_observation_json
    FROM public.oracle_canonical_observations
    WHERE observation_type='market_snapshot'
      AND (
        COALESCE(canonical_observation_json->'payload'->>'source_market_id','')=%s
        OR COALESCE(canonical_observation_json->'payload'->>'source_symbol','')=%s
        OR COALESCE(canonical_observation_json->'raw_observation'->'payload'->>'source_market_id','')=%s
        OR COALESCE(canonical_observation_json->'raw_observation'->'payload'->>'source_symbol','')=%s
      )
    ORDER BY sequence_number DESC
    LIMIT 1
    """

    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(sql,(requested,requested,requested,requested))
            row=cur.fetchone()
        conn.rollback()

    if row is None:
        return CanonicalMarketIdentity(
            requested,False,None,None,None,None,None,None,None,None,
            "identity_unresolved_no_exact_canonical_match",True,False
        )

    observed_at,source_id,body=row
    if isinstance(body,str):
        body=json.loads(body)
    payload={}
    if isinstance(body,dict):
        payload=body.get("payload") or {}
        if not payload and isinstance(body.get("raw_observation"),dict):
            payload=body["raw_observation"].get("payload") or {}

    source_market_id=str(payload.get("source_market_id") or "").upper() or None
    source_symbol=str(payload.get("source_symbol") or "").upper() or None
    market_title=str(payload.get("market_title") or "").strip() or None
    event_ticker=str(payload.get("event_ticker") or "").upper() or None

    exact=requested in {source_market_id,source_symbol}
    if not exact:
        return CanonicalMarketIdentity(
            requested,False,None,None,None,None,None,None,None,None,
            "identity_unresolved_canonical_row_not_exact",True,False
        )

    return CanonicalMarketIdentity(
        requested,True,source_market_id,market_title,event_ticker,source_symbol,
        str(payload.get("source_close_time") or "") or None,
        str(payload.get("source_expiration_time") or "") or None,
        str(observed_at),
        str(source_id),
        "identity_resolved_exact_canonical_match",
        True,False
    )

def verify_oiar_016(root=None, sample_market_id=None):
    x=resolve_canonical_market_identity(root,sample_market_id)
    return bool(x.resolved and x.market_title and x.source_market_id and x.read_only and not x.execution_authority)
