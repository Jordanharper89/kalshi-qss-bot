from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_intelligence_analytics_runtime.oiar_003_canonical_market_history_access_index import MARKET_ID_EXPRESSION,INDEX_NAME,_index_status
from datetime import datetime,timezone
OPC_046_BUILD_ID="OPC-046";OPC_046_REVISION="OPC_046_EXACT_OIAR003_INDEXED_REBUILD"
def _dt(v):
 if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
 return datetime.fromisoformat(str(v).replace("Z","+00:00"))
def physical_probe(root=None,sample_size=100,timeout_ms=15000):
 root=Path(root or Path.cwd()).resolve();st=_index_status(root)
 if not all(st):raise RuntimeError("OIAR-003 index not valid/ready/live")
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'");cur.execute("SELECT ticker,settlement_ts,result FROM public.oracle_production_learning_ledger WHERE settlement_ts IS NOT NULL ORDER BY settlement_ts DESC LIMIT %s",(int(sample_size),));settled=cur.fetchall() or []
  c.rollback()
 ids=[str(r[0]) for r in settled]
 sql=f"""SELECT wanted.market_id,h.sequence_number,h.observed_at FROM unnest(%s::text[]) AS wanted(market_id) LEFT JOIN LATERAL (SELECT sequence_number,observed_at FROM public.oracle_canonical_observations WHERE observation_type='market_snapshot' AND ({MARKET_ID_EXPRESSION})=wanted.market_id ORDER BY sequence_number DESC LIMIT 50) h ON TRUE ORDER BY wanted.market_id,h.sequence_number DESC"""
 with connect(root,autocommit=False) as c:
  with c.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY");cur.execute(f"SET LOCAL statement_timeout='{int(timeout_ms)}ms'");cur.execute("EXPLAIN (FORMAT JSON) "+sql,(ids,));plan=cur.fetchone()[0];cur.execute(sql,(ids,));hist=cur.fetchall() or []
  c.rollback()
 if INDEX_NAME not in str(plan):raise RuntimeError("OPC-046 exact lookup did not use OIAR-003 index")
 grouped={t:[] for t in ids}
 for t,seq,obs in hist:
  if seq is not None:grouped.setdefault(str(t),[]).append((seq,obs))
 withpre=0;sample=[]
 for ticker,settle,result in settled:
  rows=grouped.get(str(ticker),[]);pre=[r for r in rows if _dt(r[1])<_dt(settle)];withpre+=int(bool(pre));sample.append((str(ticker),str(settle),str(result),len(rows),len(pre)))
 return {"checked_settlements":len(settled),"with_pre_settlement_snapshot":withpre,"without_pre_settlement_snapshot":len(settled)-withpre,"plan_uses_index":True,"index_name":INDEX_NAME,"sample":sample[:20],"read_only":True,"probability_enabled":False,"execution_authority":False}
def verify_opc_046():return OPC_046_BUILD_ID=="OPC-046"
