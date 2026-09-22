from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
execution_authority=False
SQL="SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND sequence_number>%s ORDER BY sequence_number ASC LIMIT %s"
def read_until_witness(ticker,t0,end,root=None,after_sequence=0,batch_size=2000,max_batches=8):
 root=Path(root or Path.cwd());seq=int(after_sequence);path=[];witness=None
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
   for _ in range(int(max_batches)):
    q.execute(SQL,(SOURCE,seq,int(batch_size)));rows=q.fetchall() or []
    if not rows:break
    for sn,outer,obj in rows:
     seq=max(seq,int(sn));oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
     if not p:continue
     ep=float(p["event_epoch"])
     if p["ticker"]==ticker and float(t0)<ep<=float(end):path.append(dict(p,sequence_number=int(sn)))
     if ep>=float(end):
      witness={"event_epoch":ep,"sequence_number":int(sn),"ticker":p.get("ticker"),"coverage_scope":"KALSHI_SOURCE_HIGHWATER"}
      break
    if witness:break
  c.rollback()
 path.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
 return path,witness,seq
