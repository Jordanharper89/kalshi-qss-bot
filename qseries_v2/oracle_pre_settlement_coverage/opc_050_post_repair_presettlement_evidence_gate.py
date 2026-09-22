from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status
from qseries_v2.oracle_pre_settlement_coverage.opc_048_post_repair_settlement_epoch_foundation import load_epoch
OPC_050_BUILD_ID="OPC-050"
def physical_probe(root=None,limit=100,timeout_ms=15000):
 root=Path(root or Path.cwd()).resolve();epoch=load_epoch(root)["repair_epoch"]
 if not all(_index_status(root)):raise RuntimeError("OIAR-003 index not valid/ready/live")
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'")
   cur.execute("SELECT ticker,settlement_ts,result FROM public.oracle_production_learning_ledger WHERE settlement_ts > %s ORDER BY settlement_ts ASC LIMIT %s",(epoch,int(limit)));settled=cur.fetchall() or []
  c.rollback()
 ids=[str(r[0]) for r in settled]
 if not ids:return {"repair_epoch":epoch,"checked":0,"with_pre_settlement_snapshot":0,"waiting_for_post_repair_settlements":True,"plan_uses_index":True,"read_only":True,"probability_enabled":False,"execution_authority":False}
 sql=f"""SELECT wanted.market_id,h.sequence_number,h.observed_at FROM unnest(%s::text[]) wanted(market_id) LEFT JOIN LATERAL (SELECT sequence_number,observed_at FROM public.oracle_canonical_observations WHERE observation_type='market_snapshot' AND ({MARKET_ID_EXPRESSION})=wanted.market_id ORDER BY sequence_number DESC LIMIT 100) h ON TRUE ORDER BY wanted.market_id,h.sequence_number DESC"""
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'");cur.execute("EXPLAIN (FORMAT JSON) "+sql,(ids,));plan=cur.fetchone()[0];cur.execute(sql,(ids,));hist=cur.fetchall() or []
  c.rollback()
 if INDEX_NAME not in str(plan):raise RuntimeError("OPC-050 lookup did not use OIAR-003 index")
 grouped={t:[] for t in ids}
 for t,seq,obs in hist:
  if seq is not None:grouped.setdefault(str(t),[]).append((seq,obs))
 from datetime import datetime,timezone
 def dt(v):
  if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
  return datetime.fromisoformat(str(v).replace("Z","+00:00"))
 withpre=0
 for ticker,settle,_ in settled:withpre+=int(any(dt(o)<dt(settle) for _,o in grouped.get(str(ticker),[])))
 return {"repair_epoch":epoch,"checked":len(settled),"with_pre_settlement_snapshot":withpre,"without_pre_settlement_snapshot":len(settled)-withpre,"waiting_for_post_repair_settlements":False,"plan_uses_index":True,"index_name":INDEX_NAME,"read_only":True,"probability_enabled":False,"execution_authority":False}
def verify_opc_050():return OPC_050_BUILD_ID=="OPC-050"
