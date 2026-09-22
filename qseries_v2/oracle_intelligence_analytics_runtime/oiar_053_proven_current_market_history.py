from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import json
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from .oiar_001_production_analytics_snapshot_foundation import SNAPSHOT_TABLE,stable_hash
from .oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status
from .oiar_052_proven_current_canonical_trader_cohort import read_latest_current_trader_cohort
OIAR_053_BUILD_ID="OIAR-053";STAGE="proven_current_market_history"

def materialize_current_market_history(root=None,per_market=250,timeout_ms=20000):
 root=Path(root or Path.cwd()).resolve()
 if not all(_index_status(root)):raise RuntimeError("OIAR-053 requires valid OIAR-003 index")
 cohort=read_latest_current_trader_cohort(root)
 if not cohort:raise RuntimeError("OIAR-053 requires OIAR-052 snapshot")
 ids=[x["market_ticker"] for x in cohort["markets"]]
 sql=f"""SELECT wanted.market_id,h.observed_at,h.sequence_number,
 COALESCE(h.canonical_observation_json->'raw_observation'->'payload',h.canonical_observation_json->'payload','{{}}'::jsonb)->>'yes_bid_dollars',
 COALESCE(h.canonical_observation_json->'raw_observation'->'payload',h.canonical_observation_json->'payload','{{}}'::jsonb)->>'yes_ask_dollars',
 COALESCE(h.canonical_observation_json->'raw_observation'->'payload',h.canonical_observation_json->'payload','{{}}'::jsonb)->>'last_price_dollars',
 COALESCE(h.canonical_observation_json->'raw_observation'->'payload',h.canonical_observation_json->'payload','{{}}'::jsonb)->>'volume_fp',
 COALESCE(h.canonical_observation_json->'raw_observation'->'payload',h.canonical_observation_json->'payload','{{}}'::jsonb)->>'liquidity_dollars'
 FROM unnest(%s::text[]) wanted(market_id) CROSS JOIN LATERAL(
 SELECT observed_at,sequence_number,canonical_observation_json FROM public.oracle_canonical_observations
 WHERE observation_type='market_snapshot' AND ({MARKET_ID_EXPRESSION})=wanted.market_id ORDER BY sequence_number DESC LIMIT %s) h
 ORDER BY wanted.market_id,h.sequence_number ASC"""
 with connect(root,autocommit=False) as c:
  q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'");q.execute(sql,(ids,int(per_market)));rows=q.fetchall() or [];c.rollback()
 grouped={i:[] for i in ids}
 for r in rows:grouped[str(r[0])].append({"observed_at":str(r[1]),"sequence_number":int(r[2]),"yes_bid_dollars":r[3],"yes_ask_dollars":r[4],"last_price_dollars":r[5],"volume_fp":r[6],"liquidity_dollars":r[7]})
 markets=[{"market_ticker":i,"history_rows":len(grouped[i]),"history":grouped[i]} for i in ids if grouped[i]]
 if not markets:raise RuntimeError("OIAR-053 no exact indexed history")
 body={"schema_version":"OIAR-053","stage":STAGE,"source_stage":cohort["stage"],"market_count":len(markets),"source_index":INDEX_NAME,"per_market_limit":int(per_market),"markets":markets,"read_only_source":True,"execution_authority":False}
 h=stable_hash(body);sid="oiar-053-"+h[:32]
 with connect(root,autocommit=False) as c:
  q=c.cursor();q.execute(f"""INSERT INTO public.{SNAPSHOT_TABLE}(snapshot_id,stage,source_schema_version,source_engine_id,generated_at,market_count,payload_json,payload_hash,read_only_source,execution_authority)
  VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,FALSE) ON CONFLICT(snapshot_id) DO NOTHING""",(sid,STAGE,"OIAR-053",OIAR_053_BUILD_ID,datetime.now(timezone.utc),len(markets),json.dumps(body,sort_keys=True,separators=(",",":"),default=str),h));c.commit()
 return body

def read_latest_current_market_history(root=None):
 root=Path(root or Path.cwd()).resolve()
 with connect(root,autocommit=False) as c:
  q=c.cursor();q.execute("SET TRANSACTION READ ONLY");q.execute(f"SELECT payload_json,payload_hash FROM public.{SNAPSHOT_TABLE} WHERE stage=%s ORDER BY generated_at DESC,persisted_at DESC LIMIT 1",(STAGE,));r=q.fetchone();c.rollback()
 if not r:return None
 p,h=r
 if isinstance(p,str):p=json.loads(p)
 if stable_hash(p)!=str(h):raise RuntimeError("OIAR-053 snapshot hash mismatch")
 return p
def physical_probe(root=None):return materialize_current_market_history(root)
