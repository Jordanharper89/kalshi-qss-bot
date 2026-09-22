from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
execution_authority=False
SQL="SELECT sequence_number, observed_at, canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND observed_at >= to_timestamp(%s) AND observed_at <= to_timestamp(%s) ORDER BY sequence_number ASC"
def read_path_and_witness(ticker,t0,end,root=None,guard_seconds=30.0):
 root=Path(root or Path.cwd());hi=float(end)+max(1.0,float(guard_seconds))
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'")
   q.execute(SQL,(SOURCE,float(t0),hi));raw=q.fetchall() or []
  c.rollback()
 points=[]
 for seq,outer,obj in raw:
  oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
  if p and p["ticker"]==ticker and p["event_epoch"]>float(t0):points.append(dict(p,sequence_number=int(seq)))
 points.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
 path=[x for x in points if x["event_epoch"]<=float(end)]
 witness=next((x for x in points if x["event_epoch"]>=float(end)),None)
 return path,witness
