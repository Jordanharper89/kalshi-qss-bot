
from __future__ import annotations
from pathlib import Path
import json,time
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_004_indexed_current_cohort_analytics_materializer import ANALYTICS_STAGE

OIAR_021_BUILD_ID="OIAR-021"
IDENTITY_STAGE="trader_identity"

def materialize_snapshot_native_identity(root=None,statement_timeout_ms=10000):
    root=Path(root or Path.cwd()).resolve();started=time.monotonic()
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute(f"SELECT snapshot_id,payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(ANALYTICS_STAGE,))
            row=cur.fetchone()
        conn.rollback()
    if row is None:raise RuntimeError("OIAR-021 requires OIAR-004 snapshot")
    analytics_id,analytics,ph=row
    if isinstance(analytics,str):analytics=json.loads(analytics)
    if stable_hash(analytics)!=str(ph):raise RuntimeError("analytics hash mismatch")
    ids=[str(x.get("market_id") or "").upper().strip() for x in analytics.get("markets",[]) if isinstance(x,dict) and str(x.get("market_id") or "").strip()]
    if not ids:raise RuntimeError("analytics snapshot has no markets")
    sql="""WITH requested(market_id,ord) AS (SELECT * FROM unnest(%s::text[]) WITH ORDINALITY)
    SELECT r.market_id,q.observed_at,q.source_id,q.payload FROM requested r
    LEFT JOIN LATERAL (
      SELECT o.observed_at,o.source_id,COALESCE(o.canonical_observation_json->'payload',o.canonical_observation_json->'raw_observation'->'payload','{}'::jsonb) payload
      FROM public.oracle_canonical_observations o
      WHERE o.observation_type='market_snapshot'
        AND COALESCE(o.canonical_observation_json->'payload'->>'source_market_id',o.canonical_observation_json->'raw_observation'->'payload'->>'source_market_id',o.canonical_observation_json->'payload'->>'source_symbol',o.canonical_observation_json->'raw_observation'->'payload'->>'source_symbol')=r.market_id
      ORDER BY o.sequence_number DESC LIMIT 1
    ) q ON TRUE ORDER BY r.ord"""
    with connect(root,autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {int(statement_timeout_ms)}")
            cur.execute(sql,(ids,));rows=cur.fetchall()
        conn.rollback()
    markets=[];resolved=0
    for market_id,observed_at,source_id,payload in rows:
        payload=payload or {};sm=str(payload.get("source_market_id") or "").upper() or None;ss=str(payload.get("source_symbol") or "").upper() or None
        exact=market_id in {sm,ss};title=str(payload.get("market_title") or "").strip() or None;ok=bool(exact and title)
        resolved+=int(ok)
        markets.append({"market_id":market_id,"resolved":ok,"market_title":title if ok else None,"event_ticker":str(payload.get("event_ticker") or "").upper() or None if ok else None,"source_market_id":sm if ok else None,"identity_reason":"exact_canonical_match" if ok else "identity_unresolved_no_exact_snapshot_match"})
    body={"stage":IDENTITY_STAGE,"analytics_snapshot_id":str(analytics_id),"learner_state_hash":str(analytics.get("learner_state_hash") or ""),"market_count":len(markets),"resolved_count":resolved,"unresolved_count":len(markets)-resolved,"markets":markets,"read_only":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-021-"+h[:32]
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(f"INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,market_count,payload_json,payload_hash,generated_at,persisted_at) VALUES(%s,%s,%s,%s::jsonb,%s,clock_timestamp(),clock_timestamp()) ON CONFLICT(snapshot_id) DO NOTHING",(sid,IDENTITY_STAGE,len(markets),json.dumps(body,sort_keys=True),h))
    return {"snapshot_id":sid,"market_count":len(markets),"resolved_count":resolved,"unresolved_count":len(markets)-resolved,"elapsed_seconds":time.monotonic()-started}
