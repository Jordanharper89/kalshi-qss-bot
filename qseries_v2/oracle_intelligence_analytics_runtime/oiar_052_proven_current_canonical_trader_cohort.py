from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status
from .oiar_051_bounded_recent_canonical_bridge_proof import _recent_active_candidates

OIAR_052_BUILD_ID="OIAR-052"
OIAR_052_REVISION="OIAR_052_PROVEN_CURRENT_CANONICAL_TRADER_COHORT_V1"
STAGE="proven_current_canonical_trader_cohort"

def _p(doc):
    if not isinstance(doc,dict):return {}
    raw=doc.get("raw_observation")
    if isinstance(raw,dict) and isinstance(raw.get("payload"),dict):return raw["payload"]
    p=doc.get("payload");return p if isinstance(p,dict) else {}

def materialize_current_trader_cohort(root=None,limit=100,window=50000,timeout_ms=15000):
    root=Path(root or Path.cwd()).resolve()
    if not all(_index_status(root)):raise RuntimeError("OIAR-052 requires valid OIAR-003 index")
    ceiling,floor,scanned,tickers=_recent_active_candidates(root,window,max(limit*3,250),timeout_ms)
    if not tickers:raise RuntimeError("OIAR-052 no proven ACTIVE OPC candidates")
    sql=f"""SELECT wanted.market_id,h.sequence_number,h.observed_at,h.canonical_observation_json
    FROM unnest(%s::text[]) wanted(market_id)
    CROSS JOIN LATERAL(
      SELECT sequence_number,observed_at,canonical_observation_json
      FROM public.oracle_canonical_observations
      WHERE observation_type='market_snapshot' AND ({MARKET_ID_EXPRESSION})=wanted.market_id
      ORDER BY sequence_number DESC LIMIT 1
    ) h ORDER BY h.sequence_number DESC LIMIT %s"""
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
        q.execute(sql,(list(tickers),int(limit)));rows=q.fetchall() or [];c.rollback()
    markets=[]
    for ticker,seq,obs,doc in rows:
        if isinstance(doc,str):doc=json.loads(doc)
        p=_p(doc)
        markets.append({"market_ticker":str(ticker),"event_ticker":str(p.get("event_ticker") or ""),
          "title":str(p.get("title") or p.get("market_title") or ""), "status":str(p.get("status") or p.get("source_status_filter") or "active").lower(),
          "close_time":p.get("close_time") or p.get("expected_expiration_time") or p.get("expiration_time"),
          "latest_sequence_number":int(seq),"latest_observed_at":str(obs),"source_index":INDEX_NAME})
    if not markets:raise RuntimeError("OIAR-052 produced empty cohort")
    body={"schema_version":"OIAR-052","stage":STAGE,"market_count":len(markets),"sequence_floor":floor,"sequence_ceiling":ceiling,
          "recent_rows_scanned":scanned,"markets":markets,"read_only_source":True,"execution_authority":False}
    h=stable_hash(body);sid="oiar-052-"+h[:32]
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
        VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",
        (sid,STAGE,"OIAR-052",OIAR_052_BUILD_ID,datetime.now(timezone.utc),len(markets),json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()
    return body

def read_latest_current_trader_cohort(root=None):
    root=Path(root or Path.cwd()).resolve()
    with connect(root,autocommit=False) as c:
        q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,));r=q.fetchone();c.rollback()
    if not r:return None
    p,h=r
    if isinstance(p,str):p=json.loads(p)
    if stable_hash(p)!=str(h):raise RuntimeError("OIAR-052 snapshot hash mismatch")
    return p

def physical_probe(root=None):return materialize_current_trader_cohort(root)
