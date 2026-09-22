from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_predictive_discovery.opd_046_exact_kalshi_future_price_materializer import canonical_point,SOURCE
root=Path.cwd()
SQL="SELECT sequence_number, observed_at, canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=%s ORDER BY sequence_number DESC LIMIT 250"
with connect(root,autocommit=False) as c:
 with c.cursor() as q:
  q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='5000ms'");q.execute(SQL,(SOURCE,));raw=q.fetchall() or []
 c.rollback()
pts=[]
for seq,outer,obj in raw:
 oe=outer.timestamp() if hasattr(outer,"timestamp") else float(outer);p=canonical_point(obj,oe)
 if p:pts.append(dict(p,sequence_number=int(seq),outer_epoch=oe))
if not pts:raise AssertionError("NO_PHYSICAL_KALSHI_CANONICAL_PRICE_POINTS")
pts.sort(key=lambda x:x["sequence_number"])
tickers={x["ticker"] for x in pts};skews=[x["outer_epoch"]-x["event_epoch"] for x in pts]
print("[PHYSICAL_ROWS]",len(raw),"[PRICE_POINTS]",len(pts),"[TICKERS]",len(tickers))
print("[EVENT_STORAGE_SKEW_MIN]",round(min(skews),6),"[MAX]",round(max(skews),6))
print("[LATEST]",pts[-1]["ticker"],pts[-1]["event_epoch"],pts[-1]["price"])
print("[PASS] OPD-052 physical PostgreSQL Kalshi canonical readback certified")
