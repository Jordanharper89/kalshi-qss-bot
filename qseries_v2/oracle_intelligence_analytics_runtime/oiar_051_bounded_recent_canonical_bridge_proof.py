from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import (
    INDEX_NAME, MARKET_ID_EXPRESSION, _index_status,
)

OIAR_051_BUILD_ID="OIAR-051"
OIAR_051_REVISION="OIAR_051_BOUNDED_RECENT_CANONICAL_BRIDGE_PROOF_V1"

@dataclass(frozen=True)
class CanonicalBridgeProof:
    sequence_ceiling:int
    sequence_floor:int
    recent_rows_scanned:int
    active_opc_candidates:int
    checked:int
    matched_market_snapshots:int
    exact_ticker_matches:int
    newest_sequence_number:int
    index_name:str
    exact_lookup_uses_index:bool
    read_only:bool=True
    execution_authority:bool=False

def _payload(row):
    if not isinstance(row,dict):
        return {}
    raw=row.get("raw_observation")
    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):
        return raw["payload"]
    p=row.get("payload")
    return p if isinstance(p,dict) else {}

def _recent_active_candidates(root, window=50000, limit=250, timeout_ms=10000):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor()
        q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
        q.execute("SELECT max(sequence_number) FROM public.oracle_canonical_observations")
        ceiling=int((q.fetchone() or [0])[0] or 0)
        if ceiling<=0:
            raise RuntimeError("canonical observation table is empty")
        floor=max(1,ceiling-int(window)+1)
        q.execute("""
            SELECT sequence_number, observation_type, canonical_observation_json
            FROM public.oracle_canonical_observations
            WHERE sequence_number BETWEEN %s AND %s
            ORDER BY sequence_number DESC
        """,(floor,ceiling))
        rows=q.fetchall() or []
        c.rollback()

    found=[]
    seen=set()
    for seq,typ,doc in rows:
        if str(typ)!="market_snapshot":
            continue
        if isinstance(doc,str):
            try: doc=json.loads(doc)
            except Exception: continue
        p=_payload(doc)
        if str(p.get("source_status_filter") or "").strip().lower()!="active":
            continue
        if str(p.get("opc_snapshot") or "").strip().lower()!="true":
            continue
        ticker=str(p.get("source_market_id") or p.get("market_id") or p.get("source_symbol") or "").strip()
        if ticker and ticker not in seen:
            seen.add(ticker); found.append(ticker)
            if len(found)>=int(limit):
                break
    return ceiling,floor,len(rows),tuple(found)

def prove_bounded_recent_canonical_bridge(root=None, window=50000, limit=250, timeout_ms=10000):
    root=Path(root or Path.cwd()).resolve()
    exists,valid,ready,live=_index_status(root)
    if not (exists and valid and ready and live):
        raise RuntimeError("OIAR-003 market identity index is not valid/ready/live")

    ceiling,floor,scanned,tickers=_recent_active_candidates(root,window,limit,timeout_ms)
    if not tickers:
        raise RuntimeError(
            f"OIAR-051 found no ACTIVE OPC market_snapshot candidates in bounded sequence window "
            f"{floor}..{ceiling}"
        )

    sql=f"""
        SELECT wanted.market_id, h.sequence_number
        FROM unnest(%s::text[]) wanted(market_id)
        CROSS JOIN LATERAL (
            SELECT sequence_number
            FROM public.oracle_canonical_observations
            WHERE observation_type='market_snapshot'
              AND ({MARKET_ID_EXPRESSION})=wanted.market_id
            ORDER BY sequence_number DESC
            LIMIT 1
        ) h
    """
    with connect(root,autocommit=False) as c:
        q=c.cursor()
        q.execute("SET TRANSACTION READ ONLY")
        q.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
        q.execute("EXPLAIN (FORMAT JSON) "+sql,(list(tickers),))
        plan=q.fetchone()[0]
        q.execute(sql,(list(tickers),))
        matches=q.fetchall() or []
        c.rollback()

    plan_text=json.dumps(plan,sort_keys=True,default=str)
    returned={str(x[0]) for x in matches}
    exact=len(set(tickers)&returned)

    return CanonicalBridgeProof(
        ceiling,floor,scanned,len(tickers),len(tickers),len(matches),exact,
        max((int(x[1]) for x in matches),default=0),
        INDEX_NAME,INDEX_NAME in plan_text,True,False
    )

def verify_oiar_051_bounded_recent_canonical_bridge_proof(root=None):
    x=prove_bounded_recent_canonical_bridge(root)
    return (
        x.checked>0 and
        x.matched_market_snapshots>0 and
        x.exact_ticker_matches>0 and
        x.exact_ticker_matches==x.matched_market_snapshots and
        x.exact_lookup_uses_index and
        x.read_only and
        not x.execution_authority
    )
