from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
execution_authority=False
SQL="SELECT sequence_number, observed_at, canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s AND observed_at >= to_timestamp(%s) AND observed_at <= to_timestamp(%s) ORDER BY sequence_number ASC"
def read_post_t(ticker,t0,end,root=None):
 root=Path(root or Path.cwd())
 with connect(root,autocommit=False) as c:
  with c.cursor() as q:
   q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'");q.execute(SQL,(SOURCE,float(t0),float(end)));raw=q.fetchall() or []
  c.rollback()
 rows=[]
 for seq,outer,obj in raw:
  oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
  if p and p["ticker"]==ticker and float(t0)<p["event_epoch"]<=float(end):rows.append(dict(p,sequence_number=int(seq)))
 rows.sort(key=lambda x:(x["event_epoch"],x["sequence_number"]))
 return rows
